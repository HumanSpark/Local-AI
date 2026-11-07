#!/usr/bin/env python3
# File: tools/coding_harness.py
# Purpose: Coding-model screening harness (minimal OpenAI-compatible agent loop)
# Project: sparkbench | Date: 2026-07-12
#
# Overview: Minimal MVP agent loop for coding task evaluation. Connects to
# local llama-server endpoint, provides file/bash/search tools, captures
# transcript and scoring.
#
# Isolation (E156, 2026-11-05, F182): with --isolate podman every agent shell command and every verify runs inside a
# per-task rootless podman container that sees ONLY the host's /usr and /etc (read-only), the user's Python
# site-packages (read-only) and the task tree (read-write), with no network. The vault (/opt/vault), home
# directories, /tmp and the harness's environment are absent. Default "none" keeps E154's behaviour.

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import shlex
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    # capability-bypass: sparkbench compares raw providers; that IS the product
    from openai import OpenAI
except ImportError:
    print("Error: OpenAI library not found. Install with: pip install openai", file=sys.stderr)
    sys.exit(1)


logger = logging.getLogger(__name__)

# Isolation image: only its loader is used - /usr and /etc come from the host, read-only (see Overview).
ISOLATION_IMAGE = "docker.io/library/python:3.12-slim"

# File operations on the agent's tree, run INSIDE the isolation container. Host-side resolve-then-open raced with a
# background process the agent left running (swap a file for a symlink between check and use - security review
# 2026-11-05); inside the container a symlink can only reach the task tree or the read-only host /usr and /etc.
# stdin: {"op": read|edit|write, "root", "path", ["old", "new"] | ["content"]}. Exit 3 escape, 4 missing, 5 old absent.
FILE_OP = r"""
import json, os, sys
a = json.load(sys.stdin)
root = os.path.realpath(a["root"])
t = os.path.realpath(os.path.join(root, a["path"]))
if os.path.commonpath([root, t]) != root:
    sys.exit(3)
if a["op"] != "write" and not os.path.isfile(t):
    sys.exit(4)
if a["op"] == "read":
    sys.stdout.write(open(t).read())
elif a["op"] == "edit":
    c = open(t).read()
    if a["old"] not in c:
        sys.exit(5)
    open(t, "w").write(c.replace(a["old"], a["new"], 1))
else:
    os.makedirs(os.path.dirname(t), exist_ok=True)
    open(t, "w").write(a["content"])
"""

# Tool results returned to the model. The old 1,000-char cut showed ~25 lines of
# any file, which made real-repo tasks a test of the harness (E154, 2026-11-04).
MAX_TOOL_CHARS = 20000


def cap_tool_output(text: str, limit: int = MAX_TOOL_CHARS) -> str:
    """Cap a tool result, telling the model how much it did not see."""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n[... {len(text) - limit} characters truncated; narrow the command or read a range ...]"


class BudgetExceeded(RuntimeError):
    """The next paid call could cross the USD ceiling."""


class CostLedger:
    """Append-only JSONL spend record shared by every task of a paid arm.

    The file, not the process, holds the total, so a crash or a restart
    cannot reset the spend against the ceiling.
    """

    def __init__(self, path: str | Path, ceiling_usd: float, reserve_usd: float = 1.0) -> None:
        self.path = Path(path)
        self.ceiling_usd = ceiling_usd
        # Headroom for one more call: the check runs BEFORE a call whose cost is unknown.
        self.reserve_usd = reserve_usd

    def spent(self) -> float:
        if not self.path.exists():
            return 0.0
        total = 0.0
        for line in self.path.read_text().splitlines():
            if line.strip():
                total += float(json.loads(line)["cost_usd"])
        return total

    def check(self) -> None:
        spent = self.spent()
        if spent + self.reserve_usd > self.ceiling_usd:
            raise BudgetExceeded(
                f"spent ${spent:.4f} + reserve ${self.reserve_usd:.2f} > ceiling ${self.ceiling_usd:.2f}. "
                f"hint: the arm stops here by design; raise the ceiling only with the owner's word ({self.path})"
            )

    def record(self, task_id: str, cost_usd: float, usage: dict[str, Any]) -> None:
        entry = {"ts": datetime.now().isoformat(), "task": task_id, "cost_usd": cost_usd, **usage}
        with self.path.open("a") as fh:
            fh.write(json.dumps(entry) + "\n")


def _usage_numbers(usage: Any) -> dict[str, Any]:
    """Pull token counts (and provider cost, if any) from an OpenAI-style usage object."""
    if usage is None:
        return {"prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0, "cost": None}
    details = getattr(usage, "completion_tokens_details", None)
    reasoning = getattr(details, "reasoning_tokens", None) if details is not None else None
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "reasoning_tokens": reasoning or 0,
        "cost": getattr(usage, "cost", None),
    }


def with_cache_breakpoint(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Copy of messages with an Anthropic cache_control marker on the last text message.

    One moving breakpoint is the documented multi-turn pattern: each call
    reads the previous call's cached prefix and writes a longer one. The
    history itself stays plain, so only one marker is ever sent.
    """
    out = [dict(m) for m in messages]
    for m in reversed(out):
        if isinstance(m.get("content"), str) and m["content"]:
            m["content"] = [{"type": "text", "text": m["content"], "cache_control": {"type": "ephemeral"}}]
            break
    return out


def resolve_api_key(spec: str) -> str:
    """Return the key for `--api-key`; `env:VAR` reads VAR and REMOVES it from os.environ.

    The agent's bash tool and the verify command are subprocesses that inherit this
    environment: a model running `env` would otherwise send the key to the provider and
    into the committed transcripts (security review, 2026-11-04).
    """
    if not spec.startswith("env:"):
        return spec
    var = spec[4:]
    value = os.environ.pop(var, "")
    if not value:
        raise ValueError(f"--api-key env:{var} is unset or empty; hint: export it from vault_get.py first")
    return value


def read_test_files(repo: str | Path, sha: str, paths: list[str]) -> dict[str, str]:
    """Contents of `paths` at commit `sha`; a missing path raises (the bank would be wrong)."""
    return {
        p: subprocess.run(
            ["git", "-C", str(repo), "show", f"{sha}:{p}"], check=True, capture_output=True, text=True, timeout=60
        ).stdout
        for p in paths
    }


def materialise_at(repo: str | Path, sha: str, dest: Path) -> None:
    """Write the tree at `sha` into `dest` as a fresh one-commit repo.

    No clone: a clone carries every later commit, including the fix the
    agent is asked to reproduce.
    """
    dest.mkdir(parents=True, exist_ok=True)
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", sha], check=True, capture_output=True, timeout=300
    ).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True, timeout=300)
    for args in (
        ["init", "-q"],
        ["config", "user.email", "harness@sparkbench.invalid"],
        ["config", "user.name", "harness"],
        ["add", "-A"],
        ["commit", "-qm", "base", "--no-verify"],
    ):
        subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True, timeout=120)


class SandboxedCodeEnvironment:
    """Manages a sandboxed fixture repo for model interaction."""

    def __init__(
        self,
        fixture_path: str | Path,
        setup_cmd: Optional[str] = None,
        base_sha: Optional[str] = None,
        isolate: str = "podman",
    ):
        """Initialize sandbox from fixture.

        Args:
            fixture_path: Path to fixture git repo
            setup_cmd: optional shell command run in the sandbox after
                cloning (environment bootstrap: venv, dependency install).
                A non-zero exit raises - an unrunnable environment is an
                ENVIRONMENT failure recorded before any model turn, never
                attributed to the model (real-project lesson, 2026-07-12).
        """
        self.fixture_path = Path(fixture_path)
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Fixture not found: {fixture_path}")

        # Create temporary sandbox
        self.sandbox_dir = Path(tempfile.mkdtemp(prefix="coding-screen-"))
        logger.info(f"Created sandbox at {self.sandbox_dir}")

        if base_sha:
            # E154 real-repo task: history-free snapshot of the fix's parent.
            materialise_at(self.fixture_path, base_sha, self.sandbox_dir)
        else:
            subprocess.run(
                ["git", "clone", str(self.fixture_path), str(self.sandbox_dir)],
                check=True,
                capture_output=True,
            )

        # Record initial HEAD so committed model work is diffable (lesson 6)
        self.initial_sha = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=str(self.sandbox_dir),
            capture_output=True, text=True,
        ).stdout.strip() or "HEAD"

        if setup_cmd:
            logger.info(f"Running environment setup: {setup_cmd}")
            r = subprocess.run(
                setup_cmd, shell=True, cwd=str(self.sandbox_dir),
                capture_output=True, text=True, timeout=900,
            )
            if r.returncode != 0:
                raise RuntimeError(
                    f"Environment setup failed (rc={r.returncode}): "
                    f"{r.stderr[-500:]} (hint: fix the setup command or the "
                    f"project's requirements before running models)"
                )
            logger.info("Environment setup complete")

        self.container: Optional[str] = None
        if isolate == "podman":
            self.container = self._start_container()
        elif isolate != "none":
            raise ValueError(f"unknown isolate mode {isolate!r}; hint: use 'none' or 'podman'")

    def _start_container(self) -> str:
        """Start the per-task isolation container (see file Overview); returns its name."""
        name = f"e156-sb-{self.sandbox_dir.name}"
        site = subprocess.run(
            [sys.executable, "-c", "import site; print(site.getusersitepackages())"],
            capture_output=True, text=True, check=True, timeout=30,
        ).stdout.strip()
        sb = str(self.sandbox_dir.resolve())
        argv = [
            "podman", "run", "-d", "--rm", "--name", name, "--userns=keep-id", "--network=none",
            "--memory=32g", "--pids-limit=4096",
            "-v", "/usr:/usr:ro", "-v", "/etc:/etc:ro", "-v", f"{site}:{site}:ro", "-v", f"{sb}:{sb}:rw",
            "-w", sb, "-e", "HOME=/tmp/home", "-e", f"PYTHONUSERBASE={Path(site).parents[2]}",
            ISOLATION_IMAGE, "sleep", "infinity",
        ]
        # Playwright's browser binaries (no secrets): rendering tests (sparkforge) need them; HOME moves, so name the path.
        pw = Path.home() / ".cache" / "ms-playwright"
        if pw.is_dir():
            argv[-3:-3] = ["-v", f"{pw}:{pw}:ro", "-e", f"PLAYWRIGHT_BROWSERS_PATH={pw}"]
        r = subprocess.run(argv, capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(
                f"isolation container failed to start (rc={r.returncode}): {r.stderr[-500:]} "
                f"(hint: check rootless podman and that {ISOLATION_IMAGE} is pulled)"
            )
        subprocess.run(["podman", "exec", name, "mkdir", "-p", "/tmp/home"], check=True, timeout=60)
        logger.info(f"Isolation container {name} started over {sb}")
        return name

    def file_op(self, op: str, path: str, **kw: str) -> str:
        """read / edit / write one file of the tree inside the container (see FILE_OP)."""
        if self.container is None:
            raise RuntimeError("file_op needs the isolation container; hint: construct with isolate='podman'")
        root = str(self.sandbox_dir.resolve())
        r = subprocess.run(
            ["podman", "exec", "-i", "-w", root, self.container, "python3", "-c", FILE_OP],
            input=json.dumps({"op": op, "root": root, "path": path, **kw}),
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 3:
            raise ValueError(f"Path escape attempted: {path}")
        if r.returncode == 4:
            raise FileNotFoundError(f"File not found: {path}")
        if r.returncode == 5:
            raise ValueError(f"old_string not found in {path}")
        if r.returncode != 0:
            raise RuntimeError(f"{op} {path} failed in the container (rc={r.returncode}): {r.stderr[-300:]} "
                               f"(hint: is the file text, and is the container still running?)")
        return r.stdout

    def fresh_container(self) -> None:
        """Replace the container over the same tree: kills anything the agent left running before verify."""
        if self.container is None:
            return
        subprocess.run(["podman", "rm", "-f", "-t", "0", self.container], capture_output=True, timeout=120)
        self.container = self._start_container()

    def run_shell(self, cmd: str, cwd: Path, timeout: int) -> subprocess.CompletedProcess:
        """Run an untrusted shell command (agent bash, verify) - inside the container when isolated."""
        if self.container is None:
            return subprocess.run(cmd, shell=True, cwd=str(cwd), capture_output=True, text=True, timeout=timeout)
        # The inner timeout kills the command inside the container; the outer one bounds the podman client.
        argv = ["podman", "exec", "-w", str(cwd), self.container, "timeout", "-k", "5", str(timeout), "bash", "-c", cmd]
        return subprocess.run(argv, capture_output=True, text=True, timeout=timeout + 60)

    def cleanup(self):
        """Remove the isolation container (if any), then the sandbox directory."""
        if getattr(self, "container", None):
            subprocess.run(["podman", "rm", "-f", "-t", "0", self.container], capture_output=True, timeout=120)
            self.container = None
        if self.sandbox_dir.exists():
            shutil.rmtree(self.sandbox_dir)
            logger.info(f"Cleaned up sandbox {self.sandbox_dir}")

    def read_file(self, path: str) -> str:
        """Read file from sandbox.

        Args:
            path: Relative path within sandbox

        Returns:
            File contents as string

        Raises:
            ValueError: If path tries to escape sandbox
        """
        if self.container is not None:
            return self.file_op("read", path)
        # Validate path doesn't escape sandbox
        target = (self.sandbox_dir / path).resolve()
        if not target.is_relative_to(self.sandbox_dir.resolve()):
            raise ValueError(f"Path escape attempted: {path}")

        if not target.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return target.read_text()

    def edit_file(self, path: str, old: str, new: str) -> str:
        """Edit file by replacing old_string with new_string.

        Args:
            path: Relative path within sandbox
            old: String to replace
            new: Replacement string

        Returns:
            "OK" on success

        Raises:
            ValueError: If path escapes sandbox or old_string not found
        """
        if self.container is not None:
            self.file_op("edit", path, old=old, new=new)
            return "OK"
        # Validate path
        target = (self.sandbox_dir / path).resolve()
        if not target.is_relative_to(self.sandbox_dir.resolve()):
            raise ValueError(f"Path escape attempted: {path}")

        if not target.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Read current content
        content = target.read_text()

        # Find and replace
        if old not in content:
            raise ValueError(f"old_string not found in {path}")

        new_content = content.replace(old, new, 1)
        target.write_text(new_content)
        return "OK"

    def bash(self, cmd: str, cwd: Optional[str] = None) -> dict[str, Any]:
        """Execute bash command in sandbox.

        Args:
            cmd: Command to run
            cwd: Relative working directory (default: sandbox root)

        Returns:
            Dict with 'stdout', 'stderr', 'returncode'
        """
        # Determine cwd
        work_dir = self.sandbox_dir / cwd if cwd else self.sandbox_dir

        # Validate cwd doesn't escape
        if not work_dir.resolve().is_relative_to(self.sandbox_dir.resolve()):
            return {
                "stdout": "",
                "stderr": "Error: cwd escape attempted",
                "returncode": 1,
            }

        # Run command
        result = self.run_shell(cmd, work_dir, 300)  # 5 min timeout per command

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    def search(self, pattern: str, directory: str = ".") -> str:
        """Grep for pattern in directory.

        Args:
            pattern: Regex pattern to search for
            directory: Relative directory (default: ".")

        Returns:
            Grep output as string
        """
        search_dir = self.sandbox_dir / directory
        # The directory comes from the model: "../../opt/vault" would grep the host (security review 2026-11-05).
        if not search_dir.resolve().is_relative_to(self.sandbox_dir.resolve()):
            return f"Error: directory escapes the sandbox: {directory}"
        if not search_dir.exists():
            return f"Error: directory not found: {directory}"
        if self.container is not None:
            cmd = f"grep -r -n -- {shlex.quote(pattern)} {shlex.quote(str(search_dir))}"
            out = self.run_shell(cmd, self.sandbox_dir, 30).stdout
            return out if out else "(no matches)"

        try:
            result = subprocess.run(
                ["grep", "-r", "-n", "--", pattern, str(search_dir)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.stdout if result.stdout else "(no matches)"
        except Exception as e:
            return f"Error during search: {e}"

    def get_diff(self) -> str:
        """Get all changes since initial clone - COMMITTED and uncommitted.

        Lesson 6 (real-project phase): a model that commits its work (e.g.
        a git merge) is invisible to a working-tree-only diff; the v3/v5
        sparky runs reported "(no changes)" for real merges. Diff against
        the initial HEAD instead, plus any uncommitted changes.
        """
        if not hasattr(self, "initial_sha"):
            self.initial_sha = "HEAD"
        # After the agent runs, .git/config is the agent's: host git would execute a planted core.fsmonitor or
        # diff driver ON THE HOST (security review 2026-11-05). Isolated runs diff inside the container; both
        # forms refuse external diff and textconv drivers.
        git = "git -c core.fsmonitor=false -c core.hooksPath=/dev/null --no-pager diff --no-ext-diff --no-textconv"
        committed = self.run_shell(f"{git} {self.initial_sha}..HEAD", self.sandbox_dir, 120).stdout
        working = self.run_shell(git, self.sandbox_dir, 120).stdout
        out = ""
        if committed:
            out += f"### committed since {self.initial_sha[:12]}\n{committed}"
        if working:
            out += f"\n### uncommitted working tree\n{working}"
        return out if out else "(no changes)"


class CodingHarness:
    """Agent loop harness for coding task evaluation."""

    def __init__(
        self,
        model_path: str,
        endpoint: str = "http://127.0.0.1:8100/v1",
        timeout: int = 1200,  # 20 minutes
        max_iterations: int = 200,
        api_key: str = "mock",
        resend_reasoning: bool = True,
        extra_body: Optional[dict[str, Any]] = None,
        ledger: Optional[CostLedger] = None,
        prompt_cache: bool = False,
        sampling: Optional[dict[str, float]] = None,
    ):
        """Initialize harness.

        Args:
            model_path: Path to GGUF model file or model identifier
            endpoint: OpenAI-compatible endpoint URL
            timeout: Maximum wall-clock seconds per task
            max_iterations: Maximum tool-use iterations before giving up
            api_key: API key for the endpoint ("mock" for local llama-server;
                a real key when pointing --endpoint at a frontier provider like
                OpenRouter for the local-vs-frontier comparison)
        """
        self.model_path = model_path
        self.endpoint = endpoint
        self.timeout = timeout
        self.max_iterations = max_iterations
        self.setup_cmd: Optional[str] = None
        # "podman" (E156+, F182) or "none" (E154 and earlier, explicit opt-in only); set by --isolate.
        self.isolate = "podman"
        # Qwen3.8's template keeps reasoning for assistant turns after the last
        # user message ONLY if the client sends it back; dropping it blinds the
        # model to its own plan between tool calls (E154 design, 2026-11-04).
        self.resend_reasoning = resend_reasoning
        self.extra_body = extra_body
        # A ledger means a PAID endpoint: every response must report its cost.
        self.ledger = ledger
        # Anthropic via OpenRouter caches only at explicit markers; without
        # them every agent turn re-bills the whole history (probe 2026-11-04:
        # cached_tokens=0).
        self.prompt_cache = prompt_cache
        # None keeps the legacy greedy setting. E154 passes each model's vendor
        # sampling: greedy + thinking loops on Qwen, and Anthropic requires
        # temperature 1 with extended thinking.
        self.sampling = sampling
        self.task_id = "adhoc"
        self.status: Optional[str] = None

        # OpenAI client
        self.client = OpenAI(api_key=api_key, base_url=endpoint)

        # Transcript
        self.transcript = []
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def run_task(self, fixture_path: str, task_prompt: str) -> dict[str, Any]:
        """Run a coding task with the model.

        Args:
            fixture_path: Path to fixture repo
            task_prompt: Initial task prompt (from README or provided)

        Returns:
            Dict with task results: score, transcript, diff, timing
        """
        # Validate fixture
        fixture = Path(fixture_path)
        if not fixture.exists():
            return {
                "score": 0,
                "error": f"Fixture not found: {fixture_path}",
                "transcript": [],
                "diff": "",
                "wall_time": 0,
            }

        # Setup sandbox
        try:
            env = SandboxedCodeEnvironment(fixture_path, setup_cmd=getattr(self, 'setup_cmd', None))
        except Exception as e:
            return {
                "score": 0,
                "error": f"Sandbox setup failed: {e}",
                "transcript": [],
                "diff": "",
                "wall_time": 0,
            }

        self.start_time = time.time()
        try:
            result = self._agent_loop(env, task_prompt)
            result["score"] = self._score_task(env)
            return result
        finally:
            env.cleanup()
            self.end_time = time.time()

    def run_task_spec(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Run one E154 bank task: fail-before check, agent run, hidden-test verify.

        spec keys (all required except setup_cmd/verify_timeout): id, repo,
        base_sha, prompt, verify_cmd, and either test_files {path: content}
        or test_paths [path] + fix_sha (read with git show).
        Pass = verify_cmd exits 0 after the agent, having exited non-zero
        before it. The verify output is never shown to the model.
        """
        self.task_id = spec["id"]
        if "test_files" not in spec:
            # Bank form: paths only, read from the fix commit. Keeps fixture text out of
            # the bank file (the secret-scan hook matched test data, 2026-11-04).
            spec = {**spec, "test_files": read_test_files(spec["repo"], spec["fix_sha"], spec["test_paths"])}
        self.transcript = []
        self.status = None
        setup_cmd = spec.get("setup_cmd")
        verify_timeout = int(spec.get("verify_timeout", 600))

        # Fail-before runs in its own sandbox so the hidden test files, and
        # anything running them leaves behind, never reach the agent's tree.
        before_env = SandboxedCodeEnvironment(
            spec["repo"], setup_cmd=setup_cmd, base_sha=spec["base_sha"], isolate=self.isolate
        )
        try:
            before_rc, _ = self._verify(before_env, spec["test_files"], spec["verify_cmd"], verify_timeout)
        finally:
            before_env.cleanup()
        if before_rc == 0:
            return {
                "task": self.task_id,
                "status": "invalid-precondition",
                "passed": False,
                "verify": {"before_rc": before_rc, "after_rc": None},
                "error": "verify passes before the agent runs; hint: the task's tests do not exercise the change",
            }

        env = SandboxedCodeEnvironment(
            spec["repo"], setup_cmd=setup_cmd, base_sha=spec["base_sha"], isolate=self.isolate
        )
        self.start_time = time.time()
        try:
            result = self._agent_loop(env, spec["prompt"])
            diff = result["diff"]
            after_rc, after_out = self._verify(env, spec["test_files"], spec["verify_cmd"], verify_timeout)
        finally:
            env.cleanup()
            self.end_time = time.time()

        passed = after_rc == 0
        result.update(
            {
                "task": self.task_id,
                "status": self.status or ("pass" if passed else "fail"),
                "passed": passed if self.status is None else False,
                "verify": {"before_rc": before_rc, "after_rc": after_rc, "after_tail": after_out[-4000:]},
                "diff": diff,
                "wall_time": self.end_time - self.start_time,
                "isolation": self.isolate,
            }
        )
        return result

    @staticmethod
    def _verify(
        env: SandboxedCodeEnvironment, test_files: dict[str, str], verify_cmd: str, timeout: int
    ) -> tuple[int, str]:
        """Write the hidden tests over the tree and run verify; the exit code is the verdict."""
        root = env.sandbox_dir.resolve()
        # getattr: e154_build_bank's gold check passes a bare tree object with no container (host verify, trusted code).
        if getattr(env, "container", None) is not None:
            # Fresh container first: nothing the agent started may touch the hidden tests or the verify run.
            env.fresh_container()
            for rel, content in test_files.items():
                env.file_op("write", rel, content=content)
            r = env.run_shell(verify_cmd, root, timeout)
            return r.returncode, r.stdout + r.stderr
        for rel, content in test_files.items():
            target = (root / rel).resolve()
            if not target.is_relative_to(root):
                raise ValueError(f"test file escapes sandbox: {rel}; hint: bank entries must use repo-relative paths")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        r = env.run_shell(verify_cmd, root, timeout)
        return r.returncode, r.stdout + r.stderr

    def _agent_loop(self, env: SandboxedCodeEnvironment, initial_prompt: str) -> dict[str, Any]:
        """Run the agentic loop.

        Args:
            env: Sandbox environment
            initial_prompt: Initial task prompt

        Returns:
            Task result dict
        """
        messages = [{"role": "user", "content": initial_prompt}]
        tool_calls_made = 0
        malformed_calls = 0
        recoverable_errors = 0
        failed_cycles = 0
        last_action: Optional[str] = None
        turns = 0
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0, "cost_usd": 0.0, "calls": 0}

        for iteration in range(self.max_iterations):
            # Check timeout
            if time.time() - self.start_time > self.timeout:
                self.transcript.append({
                    "type": "timeout",
                    "reason": "Exceeded 20-minute budget",
                    "iteration": iteration
                })
                break

            if self.ledger is not None:
                try:
                    self.ledger.check()
                except BudgetExceeded as e:
                    self.status = "budget-exhausted"
                    self.transcript.append({"type": "budget", "reason": str(e), "iteration": iteration})
                    break

            # Call model
            kwargs: dict[str, Any] = {"temperature": 0.0, "top_p": 1.0}
            extra = dict(self.extra_body or {})
            if self.sampling is not None:
                kwargs = {k: v for k, v in self.sampling.items() if k in ("temperature", "top_p")}
                # top_k / min_p are not OpenAI parameters; llama.cpp-family servers read them from the body.
                extra.update({k: v for k, v in self.sampling.items() if k not in ("temperature", "top_p")})
            if extra:
                kwargs["extra_body"] = extra
            try:
                response = self.client.chat.completions.create(
                    model=self.model_path,
                    messages=with_cache_breakpoint(messages) if self.prompt_cache else messages,
                    tools=self._get_tools(),
                    tool_choice="auto",
                    **kwargs,
                )
            except Exception as e:
                self.transcript.append({
                    "type": "error",
                    "error": str(e),
                    "iteration": iteration
                })
                break

            # Extract content and tool calls from response
            if not response.choices:
                self.transcript.append({
                    "type": "error",
                    "error": "No choices in response",
                    "iteration": iteration
                })
                break

            turns += 1
            u = _usage_numbers(getattr(response, "usage", None))
            if self.ledger is not None:
                if u["cost"] is None:
                    raise RuntimeError(
                        "paid endpoint returned no usage cost; hint: send extra_body "
                        '{"usage": {"include": true}} to OpenRouter, or run without --usd-ceiling for a local arm'
                    )
                self.ledger.record(self.task_id, float(u["cost"]), {k: u[k] for k in ("prompt_tokens", "completion_tokens", "reasoning_tokens")})
            usage["prompt_tokens"] += u["prompt_tokens"]
            usage["completion_tokens"] += u["completion_tokens"]
            usage["reasoning_tokens"] += u["reasoning_tokens"]
            usage["cost_usd"] += float(u["cost"] or 0.0)
            usage["calls"] += 1

            choice = response.choices[0]
            response_content = choice.message.content if choice.message.content else ""
            response_tool_calls = choice.message.tool_calls if hasattr(choice.message, "tool_calls") and choice.message.tool_calls else None
            finish_reason = choice.finish_reason

            # Log model response
            self.transcript.append({
                "type": "model_response",
                "content": response_content if response_content else "(no text)",
                "finish_reason": finish_reason,
                "iteration": iteration,
            })

            # Check if model is done (stop_reason can be "stop", "tool_calls", "length", etc.)
            if finish_reason not in ["tool_calls"] or not response_tool_calls:
                self.transcript.append({
                    "type": "done",
                    "reason": "Model indicated completion",
                    "iteration": iteration
                })
                break

            # Process tool calls
            if not response_tool_calls:
                # No tool calls but not stopped; loop again
                continue

            # Append the assistant turn WITH its tool_calls structure (the
            # protocol requires it; dropping it caused '2+ assistant
            # messages' 400s), then execute each tool exactly ONCE and
            # append its result (success or error text) as a role:"tool"
            # message. The previous design executed every tool twice (once
            # for scoring, once for history) - double-applied edits then
            # legitimately failed on the second pass.
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": response_content or None,
                "tool_calls": [
                    {"id": tc.id, "type": "function",
                     "function": {"name": tc.function.name,
                                  "arguments": tc.function.arguments}}
                    for tc in response_tool_calls
                ],
            }
            if self.resend_reasoning:
                # llama.cpp-family servers use reasoning_content; OpenRouter
                # uses reasoning + reasoning_details (needed to keep Anthropic
                # thinking intact across tool turns). Send back what came.
                for field in ("reasoning_content", "reasoning", "reasoning_details"):
                    val = getattr(choice.message, field, None)
                    if val:
                        assistant_msg[field] = val
            messages.append(assistant_msg)

            has_valid_call = False
            for tool_call in response_tool_calls:
                tool_calls_made += 1

                try:
                    # Execute tool (ONCE)
                    result = self._execute_tool(env, tool_call)
                    has_valid_call = True
                    failed_cycles = 0

                    # Track action
                    last_action = tool_call.function.name

                    # Log to transcript
                    self.transcript.append({
                        "type": "tool_call",
                        "tool": tool_call.function.name,
                        "args": tool_call.function.arguments,
                        "result": result[:500] if isinstance(result, str) else str(result)[:500],
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": cap_tool_output(str(result)),
                    })

                except Exception as e:
                    # Round-1 correction: a tool that RAISES on legitimate
                    # grounds (old_string not found, missing file, failed
                    # command) is a RECOVERABLE tool error, not a malformed
                    # call - the error text goes back to the model as the
                    # tool result so it can retry. "Malformed" is reserved
                    # for protocol/JSON-parse failures (counted where the
                    # arguments are parsed). Terminate only on a genuinely
                    # unproductive error loop.
                    recoverable_errors += 1
                    result = f"TOOL ERROR: {e}"
                    self.transcript.append({
                        "type": "tool_error",
                        "tool": tool_call.function.name,
                        "error": str(e),
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": cap_tool_output(result),
                    })
                    if recoverable_errors >= 6:
                        self.transcript.append({
                            "type": "terminated",
                            "reason": "6+ recoverable tool errors (unproductive loop)",
                        })
                        break

            # Check for repeated failures
            if not has_valid_call:
                failed_cycles += 1
                if failed_cycles >= 3:
                    self.transcript.append({
                        "type": "terminated",
                        "reason": "3+ failed cycles without valid action",
                    })
                    break

            # (assistant + tool messages are appended in the single
            # execution loop above - the former duplicate-execution block
            # here is removed; see Round 1 / real-project corrections.)

        return {
            "transcript": self.transcript,
            "turns": turns,
            "usage": usage,
            "diff": env.get_diff(),
            "wall_time": time.time() - self.start_time,
            "tool_calls": tool_calls_made,
            "malformed_calls": malformed_calls,
            "last_action": last_action,
        }

    def _execute_tool(self, env: SandboxedCodeEnvironment, tool_call: Any) -> str:
        """Execute a single tool call.

        Args:
            env: Sandbox environment
            tool_call: Tool call from model

        Returns:
            Tool result as string

        Raises:
            Exception: If tool execution fails
        """
        tool_name = tool_call.function.name

        # Parse arguments (may be JSON string)
        args_str = tool_call.function.arguments
        if isinstance(args_str, str):
            try:
                args = json.loads(args_str)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON arguments: {e}")
        else:
            args = args_str

        # Execute tool
        if tool_name == "read_file":
            path = args.get("path")
            if not path:
                raise ValueError("read_file: missing 'path' argument")
            return env.read_file(path)

        elif tool_name == "edit_file":
            path = args.get("path")
            old = args.get("old")
            new = args.get("new")
            if not path or old is None or new is None:
                raise ValueError("edit_file: missing required arguments (path, old, new)")
            return env.edit_file(path, old, new)

        elif tool_name == "bash":
            cmd = args.get("cmd")
            cwd = args.get("cwd")
            if not cmd:
                raise ValueError("bash: missing 'cmd' argument")
            result = env.bash(cmd, cwd)
            return json.dumps(result)

        elif tool_name == "search":
            pattern = args.get("pattern")
            directory = args.get("directory", ".")
            if not pattern:
                raise ValueError("search: missing 'pattern' argument")
            return env.search(pattern, directory)

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _get_tools(self) -> list[dict[str, Any]]:
        """Get tool definitions for model.

        Returns:
            List of tool definitions in OpenAI format
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read file contents",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to file in sandbox"
                            }
                        },
                        "required": ["path"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "edit_file",
                    "description": "Edit file by replacing old string with new string",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Relative path to file"
                            },
                            "old": {
                                "type": "string",
                                "description": "String to replace"
                            },
                            "new": {
                                "type": "string",
                                "description": "Replacement string"
                            },
                        },
                        "required": ["path", "old", "new"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "bash",
                    "description": "Execute bash command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cmd": {
                                "type": "string",
                                "description": "Command to execute"
                            },
                            "cwd": {
                                "type": "string",
                                "description": "Working directory (relative to sandbox)"
                            },
                        },
                        "required": ["cmd"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "search",
                    "description": "Search for patterns in files (grep)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Regex pattern to search for"
                            },
                            "directory": {
                                "type": "string",
                                "description": "Directory to search in (default: .)"
                            },
                        },
                        "required": ["pattern"],
                    },
                },
            },
        ]

    def _score_task(self, env: SandboxedCodeEnvironment) -> int:
        """Score the task based on test results.

        Args:
            env: Sandbox environment

        Returns:
            Score 0-3 based on test pass/fail status
        """
        # Run pytest with python3
        # The exit code is the verdict. The old form ran `pytest || true`, so
        # returncode was always 0 and "1 failed, 2 passed" scored 3 (E154 audit).
        result = env.bash("python3 -m pytest -q 2>&1")
        return 3 if result["returncode"] == 0 else 0


def build_parser() -> argparse.ArgumentParser:
    """CLI parser, separate from main() so tests can check its defaults."""
    parser = argparse.ArgumentParser(
        description="Coding-model screening harness"
    )
    parser.add_argument(
        "model_path",
        help="Path to GGUF model file or model identifier",
    )
    parser.add_argument(
        "fixture_path",
        nargs="?",
        default=None,
        help="Path to fixture repository (legacy mode; omit with --task)",
    )
    parser.add_argument(
        "--task",
        default=None,
        help="E154 bank task JSON (id, repo, base_sha, prompt, test_files, verify_cmd); "
             "scored by verify exit code, fail-before checked",
    )
    parser.add_argument(
        "--usd-ceiling",
        type=float,
        default=None,
        help="Hard spend ceiling for a PAID endpoint; requires --ledger. Every response must report cost",
    )
    parser.add_argument(
        "--ledger",
        default=None,
        help="JSONL spend ledger shared by all tasks of the arm (the total survives restarts)",
    )
    parser.add_argument(
        "--isolate",
        choices=["none", "podman"],
        default="podman",
        help="Run agent shell commands and verify in a per-task rootless podman container with no vault, home, "
        "/tmp or network (F182). Default podman since 2026-11-07; 'none' runs agent commands ON THE HOST "
        "(E154 behaviour) and must be asked for",
    )
    parser.add_argument(
        "--extra-body",
        default=None,
        help='JSON merged into each request, e.g. \'{"usage":{"include":true},"reasoning":{"max_tokens":8000}}\'',
    )
    parser.add_argument(
        "--sampling",
        default=None,
        help='JSON sampling, e.g. \'{"temperature":0.8,"top_p":0.95,"top_k":40,"min_p":0.05}\' (default: greedy)',
    )
    parser.add_argument(
        "--prompt-cache",
        action="store_true",
        help="Mark the last message with Anthropic cache_control (OpenRouter Claude arms)",
    )
    parser.add_argument(
        "--no-resend-reasoning",
        action="store_true",
        help="Do not send reasoning back on assistant turns (default: resend within the task)",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Task prompt (if not provided, read from README.md)",
    )
    parser.add_argument(
        "--endpoint",
        default="http://127.0.0.1:8100/v1",
        help="OpenAI-compatible endpoint URL",
    )
    parser.add_argument(
        "--api-key",
        default="mock",
        help="API key for the endpoint (\"mock\" for local; a real key for a "
             "frontier provider like OpenRouter). Prefix with 'env:' to read a "
             "named env var, e.g. --api-key env:OPENROUTER_API_KEY",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1200,
        help="Timeout in seconds (default: 1200 = 20 min)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output JSON file (default: stdout)",
    )
    parser.add_argument(
        "--setup-cmd",
        default=None,
        help="Shell command run in the sandbox after clone (env bootstrap)",
    )

    return parser


def main():
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    if (args.usd_ceiling is None) != (args.ledger is None):
        parser.error("--usd-ceiling and --ledger go together")
    if args.task is None and args.fixture_path is None:
        parser.error("give a fixture_path or --task")

    # Read prompt if not provided
    if args.task is None and args.prompt is None:
        readme_path = Path(args.fixture_path) / "README.md"
        if readme_path.exists():
            args.prompt = readme_path.read_text()
        else:
            print("Error: no prompt provided and no README.md found", file=sys.stderr)
            sys.exit(1)

    # Resolve api-key (support env: prefix so keys never land in argv/process list)
    api_key = args.api_key
    try:
        api_key = resolve_api_key(api_key)
    except ValueError as e:
        parser.error(str(e))

    # Run task
    harness = CodingHarness(
        model_path=args.model_path,
        endpoint=args.endpoint,
        timeout=args.timeout,
        api_key=api_key,
        resend_reasoning=not args.no_resend_reasoning,
        extra_body=json.loads(args.extra_body) if args.extra_body else None,
        ledger=CostLedger(args.ledger, args.usd_ceiling) if args.ledger else None,
        prompt_cache=args.prompt_cache,
        sampling=json.loads(args.sampling) if args.sampling else None,
    )
    harness.setup_cmd = args.setup_cmd
    harness.isolate = args.isolate

    if args.task:
        result = harness.run_task_spec(json.loads(Path(args.task).read_text()))
    else:
        result = harness.run_task(args.fixture_path, args.prompt)

    # Output result
    output = json.dumps(result, indent=2, default=str)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Results written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
