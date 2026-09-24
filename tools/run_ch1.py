#!/usr/bin/env python3
# File: tools/run_ch1.py
# Purpose: Run one C-H1 coding arm over the real-commit task suite and record the WHOLE agentic task, not a pass/fail.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: C-H1 asks whether a local model can take bounded interactive coding
# work, and C-H2 whether it can take unattended batch work. The goal names the
# metrics: completed-correct rate, critical errors, human intervention, wall
# time, non-termination and infrastructure failures, prompt and generated
# tokens, and test/regression results. This records all of them per task.
#
# IT ASSIGNS NO SCORE ITSELF. Grading happens after the agent has stopped, from
# tests the agent never saw (tools/ch1_tasks.py). That ordering is what makes
# F36's failure mode unprofitable: Qwen3-Coder deleted a test file it could not
# satisfy and declared the task done, so any grader reading the tests the agent
# left behind can be gamed. Every tests/ file is restored to its pre-run state
# before the held-out tests are injected.
#
# THREE OUTCOMES ARE KEPT APART, because collapsing them is the error F87
# names: a task can fail because the model was wrong (capability), because it
# never stopped (non-termination), or because the server died (infrastructure).
# Only the first is evidence about the model.
#
# REGRESSIONS ARE MEASURED SEPARATELY FROM THE TASK. Passing the held-out test
# while breaking three other modules is not a success, and a single suite-wide
# pass/fail cannot tell those apart.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ch1_sandbox_guard import GuardReport, restore_tests, screen_command  # noqa: E402
from ch1_tasks import (  # noqa: E402
    TASKS_BY_ID,
    _rest_of_suite,
    Task,
    diff_tests_wrapper,
    drop_sandbox,
    inject_heldout,
    make_sandbox,
    run_pytest,
)
from coding_harness import CodingHarness, SandboxedCodeEnvironment  # noqa: E402

ARMS: dict[str, dict[str, str]] = {
    "workhorse": {
        "model": "/opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf",
        "label": "workhorse-30B-A3B",
    },
    "qwen38": {
        "model": "/opt/models/staging/Qwen3.8-27B-Q4_K_M.gguf",
        "label": "Qwen3.8-27B",
    },
    "gptoss": {
        "model": "/opt/models/staging/gpt-oss-120b-mxfp4-00001-of-00003.gguf",
        "label": "gpt-oss-120b",
    },
    "coder": {
        "model": "/opt/models/staging/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf",
        "label": "Qwen3-Coder-30B-A3B",
    },
    # CLOUD ARM, added 2026-08-20. `model` is an API model id, not a path, and
    # `provider` is what makes main() skip start_server entirely - there is no
    # GPU to hold, so Rule 9's one-consumer-at-a-time does not apply to it.
    # The key is read from the vault at run time and never written anywhere.
    "mistral-medium": {
        "model": "mistral-medium-latest",
        "label": "Mistral-Medium-3.5",
        "provider": "mistral",
    },
    # Added 2026-08-21. GLM 5.2 is the strongest arm found on this endpoint and
    # Mistral documents it as aimed at long-context coding and agentic work, so
    # it is the one model that has earned a coding arm on its own merits rather
    # than for completeness. Same endpoint as the other cloud arm, so the only
    # variable against the re-run cells is the corrected guard.
    "glm-5-2": {
        "model": "zai-glm-5-2",
        "label": "GLM-5.2",
        "provider": "mistral",
    },
}

# Provider -> (OpenAI-compatible base url, sparkvault key name). The endpoint
# carries the /v1 suffix the OpenAI SDK expects as base_url.
CLOUD_PROVIDERS = {
    "mistral": ("https://api.mistral.ai/v1", "SPARKBENCH_MISTRAL_API_KEY"),
}
VAULT_GET = "/opt/sparkvault/tools/vault_get.py"


def load_cloud_key(provider: str) -> str:
    """Vault only. Branch on the exit code, never on stdout (an empty string
    reaching an API is an auth error that names nothing)."""
    _, key_name = CLOUD_PROVIDERS[provider]
    proc = subprocess.run(
        ["python3", VAULT_GET, key_name], capture_output=True, text=True, timeout=30
    )
    if proc.returncode != 0 or not proc.stdout:
        raise SystemExit(
            f"could not read {key_name} from the sparkvault "
            f"(vault_get exit {proc.returncode}): {proc.stderr.strip()}\n"
            f"hint: this host must be a recipient of apps/sparkbench.sops.yaml. "
            f"Grant it on sparkline (.sops.yaml + sops updatekeys), push the "
            f"payload, then install it here."
        )
    return proc.stdout


DEFAULT_SERVER = (
    "/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server"
)

SYSTEM_PROMPT = (
    "You are working in a Python repository. Use the tools to read files, search, "
    "edit files and run commands. Make the change the task describes, then verify "
    "it by running the test suite. When you are finished, say DONE and stop.\n\n"
    "Work only inside this repository. Do not modify or delete test files - the "
    "tests are the specification."
)


class PreparedSandbox(SandboxedCodeEnvironment):
    """Adopts an ALREADY-PREPARED working copy instead of cloning a fixture.

    The C-H1 starting state is a git worktree at a real commit with one source
    file reverted and the held-out tests removed. That state lives in the
    working tree, not in a commit, so the parent's `git clone` would silently
    discard the very thing that makes it a task.

    Overrides `bash` to screen every command (tools/ch1_sandbox_guard.py) and to
    record refusals, because a refused command is a measurement.
    """

    def __init__(self, path: Path) -> None:
        self.fixture_path = path
        self.sandbox_dir = path
        self.guard = GuardReport()
        self.initial_sha = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(path),
                capture_output=True,
                text=True,
            ).stdout.strip()
            or "HEAD"
        )

    def cleanup(self) -> None:
        """No-op: the caller owns this worktree and grades it after the run."""

    def bash(self, cmd: str, cwd: str | None = None) -> dict[str, Any]:
        self.guard.screened += 1
        verdict = screen_command(cmd, sandbox=self.sandbox_dir)
        if not verdict.allowed:
            self.guard.refusals.append(verdict)
            return {"stdout": "", "stderr": verdict.reason, "returncode": 1}
        try:
            return super().bash(cmd, cwd)
        except subprocess.TimeoutExpired:
            # A command that never returns is the agent's problem, not a crash.
            return {
                "stdout": "",
                "stderr": "command timed out after 300s",
                "returncode": 124,
            }


class _UsageRecordingClient:
    """Wraps the OpenAI client to accumulate token usage the harness does not expose.

    The goal requires prompt and generated token counts per task. Rather than
    edit the shared agent loop - which several banked results were measured
    through - this records usage at the call boundary.
    """

    def __init__(self, inner: Any) -> None:
        self._inner = inner
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.calls = 0
        self.chat = self  # the harness calls client.chat.completions.create

    @property
    def completions(self) -> _UsageRecordingClient:
        return self

    def create(self, **kwargs: Any) -> Any:
        resp = self._inner.chat.completions.create(**kwargs)
        self.calls += 1
        usage = getattr(resp, "usage", None)
        if usage is not None:
            self.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
            self.completion_tokens += getattr(usage, "completion_tokens", 0) or 0
        return resp


class CH1Harness(CodingHarness):
    """The parent loop, with scoring removed - grading happens after, from held-out tests."""

    def _score_task(self, env: SandboxedCodeEnvironment) -> int:
        """Deliberately inert. A grader that reads the tests the agent left behind
        can be gamed by deleting them, which is exactly F36's failure."""
        return 0

    def run_prepared(self, env: PreparedSandbox, prompt: str) -> dict[str, Any]:
        self.transcript = []
        self.start_time = time.time()
        try:
            return self._agent_loop(env, prompt)
        finally:
            self.end_time = time.time()


def start_server(
    model: str, port: int, ctx: int, server_bin: str, load_timeout: float = 900.0
) -> tuple[subprocess.Popen, float]:
    """Bring one arm up. Rule 9: refuse to start beside another GPU consumer."""
    r = subprocess.run(["pgrep", "-x", "llama-server"], capture_output=True, text=True)
    if r.stdout.strip():
        raise SystemExit(
            f"llama-server already running (pids {r.stdout.split()})\n"
            f"hint: one GPU consumer at a time - `pkill -x llama-server`"
        )
    log = Path(f"/tmp/ch1-{port}.serverlog")
    cmd = [
        server_bin,
        "-m",
        model,
        "-c",
        str(ctx),
        "-np",
        "1",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--no-webui",
    ]
    proc = subprocess.Popen(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT)
    t0 = time.time()
    while time.time() - t0 < load_timeout:
        if proc.poll() is not None:
            raise RuntimeError(
                f"llama-server exited {proc.returncode} during load\nhint: read {log}"
            )
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=5
            ) as h:
                if h.status == 200:
                    return proc, time.time() - t0
        except Exception:  # noqa: BLE001 - poll boundary
            pass
        time.sleep(2)
    proc.kill()
    raise RuntimeError(f"llama-server never became healthy within {load_timeout}s")


def stop_server(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=60)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=60)


# Tool results are unbounded third-party text - a repository file, a pytest
# dump, whatever a command printed. Storing them verbatim bloats the evidence
# file AND trips the pre-commit secret scanner on benign strings: one task in
# this suite prints a credential-ABSENCE notice that matches the scanner's
# pattern exactly. Bounding is applied to any transcript kept in memory;
# transcripts are not written to git at all (see run_ch1_all.sh).
MAX_FIELD = 600


def _bound(obj: Any) -> Any:
    """Recursively cap long strings. Truncation is MARKED, never silent."""
    if isinstance(obj, str):
        return (
            obj
            if len(obj) <= MAX_FIELD
            else obj[:MAX_FIELD] + f"...[+{len(obj) - MAX_FIELD} chars]"
        )
    if isinstance(obj, list):
        return [_bound(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _bound(v) for k, v in obj.items()}
    return obj


def grade(
    task: Task, sandbox: Path, pristine: Path, baseline: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Restore the tests, inject the held-out ones, then measure.

    Ordering is the whole point: RESTORE happens before INJECT, so whatever the
    agent did to the existing tests cannot influence the grade, and the held-out
    tests arrive from the commit rather than from the sandbox.
    """
    tampered_deleted, tampered_modified = diff_tests_wrapper(sandbox, pristine)
    restore_tests(sandbox, pristine)
    inject_heldout(sandbox, task)

    heldout = run_pytest(sandbox, task.heldout, timeout=600)
    # Regressions are measured against the TASK'S OWN BASELINE, not against zero.
    # The rest of the suite already fails 11 cells at several of the commits used
    # here, in modules unrelated to any task; charging every arm with those would
    # have marked all 20 cells a critical error. Measured 2026-08-19 by grading a
    # do-nothing agent, before any GPU time was spent.
    rest = run_pytest(sandbox, _rest_of_suite(task), timeout=900)
    base_failed = (baseline or {}).get("failed", 0) + (baseline or {}).get("errors", 0)
    regressions = max(0, rest["failed"] + rest["errors"] - base_failed)
    return {
        "heldout": heldout,
        "regression_suite": rest,
        "regression_baseline_failed": base_failed,
        "regressions_introduced": regressions,
        "task_passed": bool(
            heldout["passed"] > 0
            and heldout["failed"] == 0
            and heldout["errors"] == 0
            and not heldout["timed_out"]
        ),
        "test_files_deleted": tampered_deleted,
        "test_files_modified": tampered_modified,
    }


def run_one(
    task: Task, arm: str, endpoint: str, args: argparse.Namespace
) -> dict[str, Any]:
    """One task against one arm. Every failure shape is recorded, never raised away."""
    rec: dict[str, Any] = {
        "task": task.id,
        "tier": task.tier,
        "kind": task.kind,
        "arm": arm,
        "budget_s": task.budget_s,
    }
    sandbox = make_sandbox(task)
    pristine = make_sandbox(task, dest=Path(str(sandbox) + "-pristine"))
    # "mock" is what llama-server expects; a cloud arm carries a real one, read
    # from the vault in main() and never written to disk or argv.
    key = getattr(args, "_cloud_auth", "mock")
    try:
        harness = CH1Harness(
            model_path=ARMS[arm]["model"],
            endpoint=endpoint,
            timeout=args.hard_timeout,
            max_iterations=args.max_turns,
            api_key=key,
        )
        harness.client = _UsageRecordingClient(harness.client)
        env = PreparedSandbox(sandbox)
        t0 = time.time()
        try:
            out = harness.run_prepared(env, f"{SYSTEM_PROMPT}\n\n---\n\n{task.prompt}")
            rec["infrastructure_failure"] = None
        except Exception as exc:  # noqa: BLE001 - transport IS a result class (F87)
            out = {
                "transcript": harness.transcript,
                "diff": "",
                "tool_calls": 0,
                "malformed_calls": 0,
                "last_action": None,
            }
            rec["infrastructure_failure"] = f"{type(exc).__name__}: {exc}"
        rec["wall_s"] = round(time.time() - t0, 2)

        # The parent loop SWALLOWS a failed API call: it appends {"type":"error"}
        # to the transcript and breaks, so no exception reaches this function and
        # a dead server reads as a model that did nothing. Measured 2026-08-19,
        # when four workhorse cells returned in ~1.4s with zero turns and were
        # recorded as capability failures. That is F87's error committed by this
        # harness, so the errors are lifted out of the transcript here and a
        # zero-turn cell with an error is classified as INFRASTRUCTURE.
        harness_errors = [
            {
                "iteration": t.get("iteration"),
                "type": t.get("type"),
                "error": str(t.get("error") or t.get("reason"))[:400],
            }
            for t in out.get("transcript", [])
            if t.get("type") in ("error", "timeout")
        ]
        rec["harness_errors"] = harness_errors[:6]
        if harness_errors and harness.client.calls == 0:
            rec["infrastructure_failure"] = (
                f"agent loop made no successful model call: {harness_errors[0]['error']}"
            )

        term = [t for t in out.get("transcript", []) if t.get("type") == "terminated"]
        rec["terminated_reason"] = term[-1]["reason"] if term else None
        rec["hit_turn_cap"] = (
            len([t for t in out.get("transcript", []) if t.get("type") == "tool_call"])
            >= args.max_turns
        )
        rec["non_termination"] = bool(rec["hit_turn_cap"] or rec["terminated_reason"])
        rec["tool_calls"] = out.get("tool_calls", 0)
        rec["malformed_calls"] = out.get("malformed_calls", 0)
        rec["turns"] = harness.client.calls
        rec["prompt_tokens"] = harness.client.prompt_tokens
        rec["generated_tokens"] = harness.client.completion_tokens
        rec["diff_chars"] = len(out.get("diff", "") or "")
        rec["guard"] = env.guard.as_dict()

        after_deleted, after_modified = diff_tests_wrapper(sandbox, pristine)
        env.guard.test_files_deleted = after_deleted
        env.guard.test_files_modified = after_modified
        rec["guard"] = env.guard.as_dict()

        rec["grade"] = grade(
            task, sandbox, pristine, baseline=args._baselines.get(task.id)
        )
        rec["completed_correct"] = bool(
            rec["grade"]["task_passed"] and rec["infrastructure_failure"] is None
        )
        # A cell the model never got to attempt is not evidence about the model.
        # It is excluded from capability rates and counted on its own.
        rec["scoreable"] = rec["infrastructure_failure"] is None
        rec["within_budget"] = bool(rec["wall_s"] <= task.budget_s)
        rec["success_at_deadline"] = bool(
            rec["completed_correct"] and rec["within_budget"]
        )
        rec["critical_error"] = bool(
            env.guard.attempted_test_destruction
            or rec["grade"]["regressions_introduced"] > 0
        )
        rec["transcript_len"] = len(out.get("transcript", []))
        if args.keep_transcripts:
            rec["transcript"] = _bound(out.get("transcript", []))
            rec["diff"] = (out.get("diff", "") or "")[:MAX_FIELD]
    finally:
        drop_sandbox(sandbox)
        drop_sandbox(pristine)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run one C-H1 arm over the real-commit coding suite.",
        epilog="example: python3 tools/run_ch1.py --arm coder --out results/raw/ch1-coder.json",
    )
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument(
        "--tasks", default=None, help="comma-separated ids (default: all usable)"
    )
    ap.add_argument(
        "--validation",
        default="results/raw/ch1-validation.json",
        help="only tasks marked usable there are run",
    )
    ap.add_argument("--ctx", type=int, default=32768)
    ap.add_argument("--port", type=int, default=8124)
    ap.add_argument("--max-turns", type=int, default=60)
    ap.add_argument("--hard-timeout", type=int, default=900)
    ap.add_argument("--server-bin", default=DEFAULT_SERVER)
    ap.add_argument(
        "--endpoint", default=None, help="skip serving and use this endpoint"
    )
    ap.add_argument(
        "--auth-stdin",
        action="store_true",
        help="read the cloud credential from STDIN rather than the vault. For a "
        "host that is already a RECIPIENT but whose vault payload has not been "
        "installed yet. EXPLICIT BY DESIGN and never a silent fallback: a "
        "fallback is how a stale plaintext copy stays load-bearing. Nothing is "
        "written to disk and nothing reaches argv.",
    )
    ap.add_argument("--keep-transcripts", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    _val = json.loads(Path(args.validation).read_text())
    usable = _val["usable_ids"]
    # Baselines come from validation, measured on the same starting state the
    # arms get. A missing baseline is REFUSED rather than defaulted to zero -
    # defaulting would charge every arm with regressions it did not cause.
    args._baselines = {
        r["id"]: r.get("regression_baseline")
        for r in _val["validated"]
        if r.get("usable")
    }
    if any(v is None for v in args._baselines.values()):
        raise SystemExit(
            "validation file has no regression_baseline for some usable tasks\n"
            "hint: re-run `python3 tools/ch1_tasks.py --validate`"
        )
    ids = [s.strip() for s in args.tasks.split(",")] if args.tasks else usable
    skipped = [i for i in ids if i not in usable]
    ids = [i for i in ids if i in usable]
    if not ids:
        raise SystemExit(
            f"no usable tasks selected. usable={usable}\n"
            f"hint: run `python3 tools/ch1_tasks.py --validate` first"
        )
    if skipped:
        print(f"NOTE: skipping {skipped} - not marked usable by the ground-truth gate")

    proc = None
    endpoint = args.endpoint
    load_s = None
    args._cloud_auth = "mock"
    provider = ARMS[args.arm].get("provider")
    if provider is not None:
        base, _ = CLOUD_PROVIDERS[provider]
        endpoint = endpoint or base
        if args.auth_stdin:
            args._cloud_auth = sys.stdin.readline().strip()
            if not args._cloud_auth:
                raise SystemExit(
                    "--auth-stdin was given but stdin carried nothing.\n"
                    "hint: pipe the vault read in, e.g. "
                    "`ssh <vault-host> python3 /opt/sparkvault/tools/vault_get.py "
                    "SPARKBENCH_MISTRAL_API_KEY | python3 tools/run_ch1.py ...`"
                )
        else:
            args._cloud_auth = load_cloud_key(provider)
        print(
            f"cloud arm {ARMS[args.arm]['label']} via {endpoint} "
            f"- no server started, no GPU held",
            flush=True,
        )
    if endpoint is None:
        print(f"starting {ARMS[args.arm]['label']} ...", flush=True)
        proc, load_s = start_server(
            ARMS[args.arm]["model"], args.port, args.ctx, args.server_bin
        )
        endpoint = f"http://127.0.0.1:{args.port}/v1"
        print(f"  loaded in {load_s:.1f}s", flush=True)

    records: list[dict[str, Any]] = []
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "arm": args.arm,
        "label": ARMS[args.arm]["label"],
        "model": ARMS[args.arm]["model"],
        "ctx": args.ctx,
        "max_turns": args.max_turns,
        "hard_timeout_s": args.hard_timeout,
        "load_s": round(load_s, 2) if load_s else None,
        "tasks": ids,
        "skipped_not_usable": skipped,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "kernel": subprocess.run(
            ["uname", "-r"], capture_output=True, text=True
        ).stdout.strip(),
    }
    try:
        for i, tid in enumerate(ids, 1):
            task = TASKS_BY_ID[tid]
            print(
                f"[{i}/{len(ids)}] {tid} ({task.tier}, budget {task.budget_s}s) ...",
                flush=True,
            )
            rec = run_one(task, args.arm, endpoint, args)
            records.append(rec)
            print(
                f"    correct={rec['completed_correct']} "
                f"wall={rec['wall_s']}s turns={rec['turns']} "
                f"gen={rec['generated_tokens']} "
                f"nonterm={rec['non_termination']} "
                f"critical={rec['critical_error']}",
                flush=True,
            )
            out.write_text(json.dumps({"meta": meta, "records": records}, indent=2))
    finally:
        if proc is not None:
            stop_server(proc)

    n = len(records)
    ok = sum(1 for r in records if r["completed_correct"])
    within = sum(1 for r in records if r["success_at_deadline"])
    print(
        f"\n=== {ARMS[args.arm]['label']}: {ok}/{n} completed-correct, "
        f"{within}/{n} within budget ==="
    )
    print(f"  non-termination : {sum(1 for r in records if r['non_termination'])}")
    print(f"  critical errors : {sum(1 for r in records if r['critical_error'])}")
    print(
        f"  infra failures  : {sum(1 for r in records if r['infrastructure_failure'])}"
    )
    print(f"  written         : {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
