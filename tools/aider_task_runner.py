# File: tools/aider_task_runner.py
# Purpose: Run real coding tasks through Aider against the production llama-server in clean
#          disposable git worktrees, and record what actually happened.
# Project: sparkbench | Date: 2026-08-30
#
# Overview: Each task is a JSON spec naming a base ref, an optional seed script, the files to
# put in Aider's chat, the instruction, and a VERIFY command that must FAIL before and PASS
# after. The runner cuts a throwaway worktree, records the before-verdict, runs Aider once
# under a wall-clock timer, records the after-verdict and the diff, and writes one JSON result
# row per task. Latency is read from tools/aider_probe.py's JSONL - measured on the wire, not
# inferred from Aider's own output.
#
# Data flow: task spec -> git worktree add -> seed -> verify(before) -> aider -> verify(after)
#            -> diff + files touched -> probe rows for this window -> results JSON.
# Dependencies: git, aider (user-level), a running tools/aider_probe.py, a serving llama-server.
#
# --agent pi (added 2026-09-22, E138) runs the same specs through the pi coding agent instead:
# same worktree, seed, verify and diff, only the agent command differs. pi reads its endpoint
# from ~/.pi/agent/models.json (provider/model passed as --pi-provider/--pi-model). pi has no
# read-only file mode, so a read_files entry it edits is scored `fail-readonly-violation`
# rather than trusted - a TDD task must not pass by rewriting its own test.
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Aider's own bookkeeping, never part of the task's diff.
AIDER_ARTEFACTS = frozenset(
    {
        "aider-run.log",
        ".gitignore",
        ".aider.chat.history.md",
        ".aider.input.history",
        ".aider.tags.cache.v4/",
        ".aider.tags.cache.v3/",
    }
)


class TaskError(RuntimeError):
    """Raised when a task cannot be set up or run. Always carries a hint."""


def _run(
    cmd: list[str],
    cwd: Path | None = None,
    timeout: float = 600.0,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    # stdin closed: pi -p waits on an open stdin and never exits (measured 2026-09-22)
    return subprocess.run(
        cmd,
        cwd=cwd,
        timeout=timeout,
        capture_output=True,
        text=True,
        env=env,
        check=False,
        stdin=subprocess.DEVNULL,
    )


def _sh(
    script: str, cwd: Path, timeout: float = 900.0
) -> subprocess.CompletedProcess[str]:
    """Run a task's seed or verify script.

    `pipefail` is forced on. Without it a verify ending in `| tail` reports tail's
    exit status, so a failing command scores as a pass - which is exactly how the
    first E90 run scored every task 'invalid-precondition'.
    """
    return subprocess.run(
        ["bash", "-o", "pipefail", "-c", script],
        cwd=cwd,
        timeout=timeout,
        capture_output=True,
        text=True,
        check=False,
    )


def make_worktree(repo: Path, base: str, dest: Path) -> None:
    """Create a clean detached worktree at dest. Disposable by construction."""
    if dest.exists():
        raise TaskError(
            f"worktree destination already exists: {dest}. "
            f"hint: pass a fresh --workdir, or remove it with "
            f"'git -C {repo} worktree remove --force {dest}'"
        )
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = _run(["git", "-C", str(repo), "worktree", "add", "--detach", str(dest), base])
    if r.returncode != 0:
        raise TaskError(
            f"git worktree add failed (rc={r.returncode}) for base {base!r}: "
            f"{r.stderr.strip()}. hint: check that ref exists in {repo}"
        )


def drop_worktree(repo: Path, dest: Path) -> None:
    _run(
        ["git", "-C", str(repo), "worktree", "remove", "--force", str(dest)],
        timeout=120,
    )


def read_probe_window(probe_log: Path, skip_lines: int) -> list[dict[str, Any]]:
    """Chat-completion rows appended to the probe log after `skip_lines`.

    An empty list is a real, expected outcome - it means Aider never called the
    model - so the caller reports it rather than this raising.
    """
    if not probe_log.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in probe_log.read_text(encoding="utf-8").splitlines()[skip_lines:]:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue  # a partially flushed final line is expected while the proxy runs
        if str(row.get("path", "")).endswith("/chat/completions"):
            rows.append(row)
    return rows


def _tokens(row: dict[str, Any], counted: str, reported: str) -> int:
    value = row.get(counted)
    if value is None:
        value = row.get(reported)
    return int(value or 0)


def summarise_requests(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "n_requests": 0,
            "note": "no /v1/chat/completions request reached the probe",
        }
    first = rows[0]
    return {
        "n_requests": len(rows),
        "first_turn_ttfb_s": first.get("ttfb_s"),
        "first_turn_wall_s": first.get("wall_s"),
        "first_turn_prompt_tokens": _tokens(first, "prompt_n", "prompt_tokens"),
        "first_turn_prompt_ms": first.get("prompt_ms"),
        "total_prompt_tokens": sum(
            _tokens(r, "prompt_n", "prompt_tokens") for r in rows
        ),
        "total_completion_tokens": sum(
            _tokens(r, "predicted_n", "completion_tokens") for r in rows
        ),
        "ttfb_all_s": [r.get("ttfb_s") for r in rows],
    }


def classify(
    verify_before_rc: int, verify_after_rc: int, edit_applied: bool = True
) -> str:
    """A task only counts as passed if its verify FAILED first and PASSES now.

    A verify that already passed before Aider ran proves nothing about the model,
    so it is reported as 'invalid-precondition' rather than folded into a pass.
    """
    if verify_before_rc == 0:
        return "invalid-precondition"
    if verify_after_rc == 0:
        return "pass"
    # A failing verify with NO applied edit is the harness not writing the model's fix to the file
    # (F171: 21 of 24 T3 attempts, F174: pi passed where Aider's edit never landed). It is a
    # different outcome from a wrong edit and must never be counted as one.
    return "fail" if edit_applied else "fail-not-applied"


def run_task(
    spec: dict[str, Any],
    repo: Path,
    workdir: Path,
    probe_log: Path,
    base_url: str,
    model: str,
    aider_extra: list[str],
    timeout: float,
    agent: str = "aider",
) -> dict[str, Any]:
    name = spec["name"]
    dest = workdir / name
    result: dict[str, Any] = {
        "name": name,
        "kind": spec["kind"],
        "instruction": spec["instruction"],
        "files_given": spec.get("files", []),
        "read_only_files": spec.get("read_files", []),
        "verify_cmd": spec["verify"],
    }

    skip = 0
    if probe_log.exists():
        skip = len(probe_log.read_text(encoding="utf-8").splitlines())

    make_worktree(repo, spec.get("base", "HEAD"), dest)
    try:
        if spec.get("seed"):
            seeded = _sh(spec["seed"], dest, timeout=300)
            result["seed_rc"] = seeded.returncode
            if seeded.returncode != 0:
                raise TaskError(
                    f"seed script failed for task {name!r} (rc={seeded.returncode}): "
                    f"{seeded.stderr[-800:]}. "
                    f"hint: the seed must leave the worktree in the pre-fix state"
                )

        # The seed's own diff, captured with the same pathspec as the final one, so "did the agent
        # change anything" is diff inequality rather than a length heuristic (F171).
        exclude = [f":(exclude){n.rstrip('/')}" for n in sorted(AIDER_ARTEFACTS)]
        _run(["git", "-C", str(dest), "add", "-A", "-N", "--", "."], timeout=120)
        seed_diff = _run(
            ["git", "-C", str(dest), "diff", "HEAD", "--", ".", *exclude], timeout=120
        ).stdout
        result["seed_diff_chars"] = len(seed_diff)

        before = _sh(spec["verify"], dest, timeout=900)
        result["verify_before_rc"] = before.returncode
        result["verify_before_tail"] = (before.stdout + before.stderr).strip()[-600:]

        env = dict(os.environ)
        env["OPENAI_API_BASE"] = base_url
        env["OPENAI_API_KEY"] = env.get("SPARKROUTER_KEY", "sk-local-noauth")

        # read_files go in as --read: visible to the model, not editable. A TDD task must not
        # be able to make its own test pass by rewriting the test.
        read_args: list[str] = []
        for path in spec.get("read_files", []):
            read_args += ["--read", path]

        if agent == "pi":
            provider, _, pi_model = model.partition("/")
            message = spec["instruction"]
            if spec.get("files"):
                message += "\n\nFiles to edit: " + ", ".join(spec["files"]) + "."
            if spec.get("read_files"):
                message += (
                    "\nRead-only (do NOT modify): "
                    + ", ".join(spec["read_files"])
                    + "."
                )
            # --no-context-files: the worktree's CLAUDE.md/AGENTS.md are sparkbench's own agent
            # instructions, and Aider never sees them either.
            cmd = [
                "pi",
                "-p",
                "--provider",
                provider,
                "--model",
                pi_model,
                "--no-session",
                "--offline",
                "--no-context-files",
                *aider_extra,
                message,
            ]
        else:
            cmd = [
                "aider",
                "--model",
                model,
                "--yes",
                "--no-auto-commits",
                "--no-analytics",
                "--no-check-update",
                "--no-show-model-warnings",
                "--no-gitignore",
                "--no-show-release-notes",
                *read_args,
                *aider_extra,
                "--message",
                spec["instruction"],
                *spec.get("files", []),
            ]
        result["agent"] = agent
        result["aider_cmd"] = " ".join(cmd)

        t0 = time.monotonic()
        proc = _run(cmd, cwd=dest, timeout=timeout, env=env)
        result["aider_rc"] = proc.returncode
        result["aider_wall_s"] = round(time.monotonic() - t0, 2)
        (dest / "aider-run.log").write_text(
            proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8"
        )
        result["aider_tail"] = proc.stdout.strip()[-1500:]

        after = _sh(spec["verify"], dest, timeout=900)
        result["verify_after_rc"] = after.returncode
        result["verify_after_tail"] = (after.stdout + after.stderr).strip()[-600:]

        # Intent-to-add first: a task whose whole output is a NEW file shows an empty
        # `git diff` otherwise, which lost T2's implementation on the first E90 run.
        _run(["git", "-C", str(dest), "add", "-A", "-N", "--", "."], timeout=120)
        # EXCLUDE Aider's own bookkeeping from the diff, not just from
        # files_touched. aider-run.log is written INTO the worktree before this
        # runs, so without the exclusion it lands in `git diff` ahead of the
        # task's own files and, at a 20,000-character cap, crowds them out
        # entirely: E113's T3 failed and its actual edit was not in the record
        # (2026-09-06). The diff is the evidence for WHY a task failed; a run
        # log is not evidence and it is already kept beside the results.
        result["diff_stat"] = _run(
            ["git", "-C", str(dest), "diff", "--stat", "HEAD", "--", ".", *exclude],
            timeout=120,
        ).stdout.strip()
        diff_full = _run(
            ["git", "-C", str(dest), "diff", "HEAD", "--", ".", *exclude], timeout=120
        ).stdout
        result["diff"] = diff_full[:20000]
        result["edit_applied"] = diff_full != seed_diff
        # A silently clipped diff reads as a complete one. Say so in the record.
        if len(diff_full) > 20000:
            result["diff_truncated_chars"] = len(diff_full) - 20000
        # The FINAL contents of every file the task was allowed to edit, so a
        # failure can be attributed after the disposable worktree is gone.
        finals: dict[str, str] = {}
        for rel in spec.get("files", []):
            fp = dest / rel
            finals[rel] = (
                fp.read_text(encoding="utf-8", errors="replace")[:20000]
                if fp.exists()
                else "<<file does not exist after the run>>"
            )
        result["final_files"] = finals
        porcelain = _run(
            ["git", "-C", str(dest), "status", "--porcelain"], timeout=120
        ).stdout
        result["files_touched"] = sorted(
            line[3:]
            for line in porcelain.splitlines()
            if line[3:] not in AIDER_ARTEFACTS
        )

        result.update(summarise_requests(read_probe_window(probe_log, skip)))
        result["outcome"] = classify(
            result["verify_before_rc"],
            result["verify_after_rc"],
            edit_applied=result.get("edit_applied", True),
        )
        edited_ro = sorted(
            set(spec.get("read_files", [])) & set(result["files_touched"])
        )
        if edited_ro:
            result["read_only_edited"] = edited_ro
            if result["outcome"] == "pass":
                result["outcome"] = "fail-readonly-violation"
    finally:
        log = dest / "aider-run.log"
        if log.exists():
            shutil.copy2(log, workdir / f"{name}-aider.log")
        if spec.get("keep_worktree"):
            result["worktree_kept"] = str(dest)
        else:
            drop_worktree(repo, dest)
    return result


def check_preconditions(specs: list[dict[str, Any]], repo: Path, workdir: Path) -> int:
    """Seed each task in a fresh worktree and run its verify - no model involved.

    A task's verify must FAIL before the model runs, or the task proves nothing
    and `classify` reports invalid-precondition. These specs rot silently: the
    work they describe gets DONE and committed, and from then on HEAD already
    satisfies the verify. T2 and T3 rotted exactly that way and were only
    noticed because E109 scored 0/3 (2026-09-05), which reads as a broken
    harness rather than a stale bank.

    Returns 0 when every precondition is valid, 1 otherwise, so it can gate a
    run instead of only reporting on one.
    """
    bad = 0
    for spec in specs:
        name = spec["name"]
        dest = workdir / f"precheck-{name}"
        make_worktree(repo, spec.get("base", "HEAD"), dest)
        try:
            if spec.get("seed"):
                seeded = _sh(spec["seed"], dest, timeout=300)
                if seeded.returncode != 0:
                    print(
                        f"{name}: SEED FAILED rc={seeded.returncode} "
                        f"{seeded.stderr.strip()[-200:]}",
                        flush=True,
                    )
                    bad += 1
                    continue
            before = _sh(spec["verify"], dest, timeout=900)
            if before.returncode == 0:
                print(
                    f"{name}: INVALID - verify PASSES before the model runs "
                    f"(rc=0). The work this task describes is already in the "
                    f"tree; the seed must undo it.",
                    flush=True,
                )
                bad += 1
            else:
                print(
                    f"{name}: valid - verify fails first (rc={before.returncode})",
                    flush=True,
                )
        finally:
            drop_worktree(repo, dest)
    print()
    if bad:
        print(
            f"{bad}/{len(specs)} task(s) have an invalid precondition. "
            f"A run against these would score 0 and read as a harness fault."
        )
        return 1
    print(f"all {len(specs)} preconditions valid.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Run real coding tasks through Aider against the production "
        "llama-server in clean disposable git worktrees.",
        epilog="example:\n"
        "  python3 tools/aider_task_runner.py \\\n"
        "      --tasks tools/aider-tasks.json --workdir /tmp/aider-runs \\\n"
        "      --probe-log /tmp/probe.jsonl --out results/raw/e90/tasks.json \\\n"
        "      --model openai/$(python3 -c 'import json,urllib.request as u; "
        'print(json.load(u.urlopen("http://127.0.0.1:8400/v1/models"))["data"][0]["id"])\')',
    )
    parser.add_argument(
        "--tasks", required=True, help="JSON file holding a list of task specs"
    )
    parser.add_argument(
        "--repo",
        default=str(Path(__file__).resolve().parent.parent),
        help="repository the worktrees are cut from (default: this repo)",
    )
    parser.add_argument(
        "--workdir", required=True, help="directory to create worktrees under"
    )
    parser.add_argument(
        "--probe-log", help="JSONL written by a running tools/aider_probe.py"
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8499/v1",
        help="OpenAI-compatible endpoint Aider calls (default: the probe)",
    )
    parser.add_argument(
        "--model", help="Aider model string, e.g. openai/<id from /v1/models>"
    )
    parser.add_argument("--out", help="where to write the results JSON")
    parser.add_argument(
        "--timeout",
        type=float,
        default=1800.0,
        help="per-task Aider timeout in seconds (default: 1800)",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=None,
        help="run only the named task (repeatable)",
    )
    parser.add_argument(
        "--agent",
        default="aider",
        choices=["aider", "pi"],
        help="coding agent to drive (default aider). For pi, --model is "
        "<provider>/<model> from ~/.pi/agent/models.json",
    )
    parser.add_argument(
        "--aider-arg",
        action="append",
        default=[],
        help="extra argument passed through to aider (repeatable)",
    )
    parser.add_argument(
        "--check-preconditions",
        action="store_true",
        help="seed each task in a worktree, run its verify and report "
        "whether it FAILS first, then stop. No model is called, so "
        "this needs neither --model nor --probe-log. Run it before "
        "believing a 0/N result: these specs rot when the work they "
        "describe gets committed",
    )
    args = parser.parse_args(argv)

    specs = json.loads(Path(args.tasks).read_text(encoding="utf-8"))
    if args.only:
        wanted = set(args.only)
        known = [s["name"] for s in specs]
        missing = wanted - set(known)
        if missing:
            raise TaskError(
                f"no task named {sorted(missing)} in {args.tasks}. "
                f"hint: names present are {known}"
            )
        specs = [s for s in specs if s["name"] in wanted]

    repo = Path(args.repo).resolve()
    workdir = Path(args.workdir).resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    if args.check_preconditions:
        return check_preconditions(specs, repo, workdir)

    missing = [
        f
        for f, v in (
            ("--model", args.model),
            ("--probe-log", args.probe_log),
            ("--out", args.out),
        )
        if not v
    ]
    if missing:
        raise TaskError(
            f"missing required argument(s) {missing} for a real run. "
            f"hint: they are optional only with --check-preconditions"
        )
    probe_log = Path(args.probe_log).resolve()
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for i, spec in enumerate(specs, 1):
        print(
            f"[{i}/{len(specs)}] {spec['name']} ({spec['kind']}) - starting", flush=True
        )
        started = time.monotonic()
        try:
            row = run_task(
                spec,
                repo,
                workdir,
                probe_log,
                args.base_url,
                args.model,
                args.aider_arg,
                args.timeout,
                agent=args.agent,
            )
        except subprocess.TimeoutExpired as exc:
            row = {
                "name": spec["name"],
                "kind": spec["kind"],
                "outcome": "timeout",
                "error": f"aider timed out after {exc.timeout}s",
            }
            drop_worktree(repo, workdir / spec["name"])
        print(
            f"[{i}/{len(specs)}] {spec['name']} -> {row.get('outcome')} "
            f"in {time.monotonic() - started:.1f}s "
            f"(first-turn TTFB {row.get('first_turn_ttfb_s')}s, "
            f"{row.get('n_requests')} requests, "
            f"files {row.get('files_touched')})",
            flush=True,
        )
        results.append(row)
        out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    passed = sum(1 for r in results if r.get("outcome") == "pass")
    print(f"\n{passed}/{len(results)} passed. wrote {out_path}", flush=True)
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
