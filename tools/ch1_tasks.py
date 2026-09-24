#!/usr/bin/env python3
# File: tools/ch1_tasks.py
# Purpose: The C-H1 coding suite - real sparkbench commits as tasks, with the ORIGINAL tests held out as ground truth.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: F33 is the constraint this file is built around. The Qwen3-30B
# workhorse topped the ten-model document matrix (93.3% / 87.5%) and then
# scored ZERO on both real-repository coding tasks - 85 tool calls of thrash,
# zero test runs - while Qwen3-Coder-30B passed in 129s. F36 adds the other
# half: the synthetic fixtures in spikes/coding-screen are EASY (a frontier
# model clears each in under 50s) and do not discriminate between strong arms.
# So a C-H1 suite built from hand-authored fixtures would measure nothing.
#
# THE TASKS ARE REAL COMMITS FROM THIS REPOSITORY. Each task reverts one source
# file to its state BEFORE a real commit and asks the model to restore the
# behaviour. The commit's own test file is the ground truth, and the agent never
# sees it - it is removed from the sandbox before the run and injected after.
#
# WHY GROUND TRUTH FROM HISTORY RATHER THAN FROM ME. A test I author for the
# occasion encodes my idea of the solution, and I have already read the answer.
# The commit's test was written by whoever did the work, to check the work,
# before any of this existed. It is also dated after the models' knowledge
# cutoff, so no arm can have memorised it.
#
# THE GATE BELOW IS NOT OPTIONAL. A task only counts if its held-out test PASSES
# at the commit and FAILS after the revert. Without both halves a "task" can be
# one whose test never exercised the change at all, which would score every arm
# correct and discriminate nothing - the L3-hard ceiling (F91) reached by
# accident. validate_task() refuses such a task rather than reporting it.

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent

# Sandboxes are deliberately NOT under /tmp. The C04 task's own test asserts
# that the check script it resolves is the repo copy and not a temporary one -
# `assert "/tmp/" not in str(w.CHECK)` - so a /tmp worktree failed a valid test
# for a reason that had nothing to do with the model. Measured 2026-08-19; the
# fix is to move the ruler, not to drop the test.
SANDBOX_ROOT = Path.home() / ".cache" / "sparkbench-ch1"


@dataclass
class Task:
    """One C-H1 task. `prompt` states the PROBLEM, never the implementation."""

    id: str
    tier: str  # "interactive" | "substantial"
    kind: str  # bugfix | feature | refactor
    commit: str  # the real commit whose behaviour is to be restored
    revert: list[str]  # source paths reset to the commit's PARENT
    heldout: list[str]  # test paths removed from the sandbox, injected at grading
    prompt: str
    budget_s: int
    notes: str = ""
    validation: dict[str, Any] = field(default_factory=dict)


def _sandbox_root() -> Path:
    """Where working copies live. Created on demand; never under /tmp (see above)."""
    SANDBOX_ROOT.mkdir(parents=True, exist_ok=True)
    return SANDBOX_ROOT


def _git(args: list[str], cwd: Path, check: bool = True) -> str:
    r = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, timeout=300
    )
    if check and r.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {cwd}: {r.stderr.strip()}\n"
            f"hint: is the commit present in this clone, and is the path tracked at it?"
        )
    return r.stdout


def file_exists_at(commit: str, path: str) -> bool:
    """Was this path tracked at that commit? A `feature` task's file was not."""
    r = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{path}"],
        cwd=str(REPO),
        capture_output=True,
        timeout=60,
    )
    return r.returncode == 0


def run_pytest(cwd: Path, targets: list[str], timeout: float = 600.0) -> dict[str, Any]:
    """Run pytest on named targets. A crash or a timeout is a RESULT, not an exception."""
    cmd = [sys.executable, "-m", "pytest", "-q", "--no-header", *targets]
    try:
        r = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return {
            "returncode": None,
            "timed_out": True,
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "tail": f"timed out after {timeout}s",
        }
    out = r.stdout + r.stderr
    passed = failed = errors = 0
    for line in out.splitlines():
        if " passed" in line or " failed" in line or " error" in line:
            for tok, name in ((" passed", "p"), (" failed", "f"), (" error", "e")):
                if tok in line:
                    parts = line.replace("=", " ").split()
                    for i, w in enumerate(parts):
                        if w.startswith(tok.strip()) and i:
                            try:
                                n = int(parts[i - 1])
                            except ValueError:
                                continue
                            if name == "p":
                                passed = max(passed, n)
                            elif name == "f":
                                failed = max(failed, n)
                            else:
                                errors = max(errors, n)
    return {
        "returncode": r.returncode,
        "timed_out": False,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "tail": out[-1500:],
    }


def make_sandbox(task: Task, dest: Path | None = None) -> Path:
    """A working copy at the task's STARTING state: commit, minus the fix, minus its tests."""
    dest = dest or Path(tempfile.mkdtemp(prefix=f"ch1-{task.id}-", dir=_sandbox_root()))
    if dest.exists():
        shutil.rmtree(dest)
    _git(["worktree", "add", "--detach", str(dest), task.commit], REPO)
    for path in task.revert:
        if file_exists_at(f"{task.commit}^", path):
            _git(["checkout", f"{task.commit}^", "--", path], dest)
        else:
            # The commit CREATED this file - the starting state has no file.
            (dest / path).unlink(missing_ok=True)
    _git(
        ["reset"], dest, check=False
    )  # unstage, so `git diff` reads naturally for the agent
    for path in task.heldout:
        (dest / path).unlink(missing_ok=True)
    return dest


def drop_sandbox(dest: Path) -> None:
    _git(["worktree", "remove", "--force", str(dest)], REPO, check=False)
    shutil.rmtree(dest, ignore_errors=True)


def inject_heldout(sandbox: Path, task: Task) -> None:
    """Put the ground-truth tests in place for grading, from the commit itself."""
    for path in task.heldout:
        blob = subprocess.run(
            ["git", "show", f"{task.commit}:{path}"],
            cwd=str(REPO),
            capture_output=True,
            timeout=120,
        )
        if blob.returncode != 0:
            raise RuntimeError(
                f"held-out test {path} not found at {task.commit}\n"
                f"hint: check the path is tracked at that commit"
            )
        target = sandbox / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob.stdout)


# The two modules with pre-existing fastapi collection errors are excluded
# everywhere, so a task is never charged for them.
_PREEXISTING_COLLECTION_ERRORS = (
    "tests/test_auth_sidecar.py",
    "tests/test_kokoro_gateway.py",
)


def _rest_of_suite(task: Task) -> list[str]:
    """pytest targets for the REGRESSION check: everything but the held-out tests."""
    return [
        "tests/",
        *[f"--ignore={p}" for p in _PREEXISTING_COLLECTION_ERRORS],
        *[f"--ignore={h}" for h in task.heldout],
    ]


def validate_task(task: Task) -> dict[str, Any]:
    """The gate: the held-out test must PASS at the commit and FAIL after the revert.

    Both halves are required. A test that passes in both states does not
    exercise the change and would make every arm look correct - a ceiling
    reached by accident (F91). A test that fails in both is a broken task.
    """
    result: dict[str, Any] = {"id": task.id, "commit": task.commit}

    # Half 1 - the test passes at the real commit.
    at_commit = Path(
        tempfile.mkdtemp(prefix=f"ch1-val-{task.id}-", dir=_sandbox_root())
    )
    shutil.rmtree(at_commit)
    _git(["worktree", "add", "--detach", str(at_commit), task.commit], REPO)
    try:
        r_after = run_pytest(at_commit, task.heldout)
    finally:
        drop_sandbox(at_commit)
    result["at_commit"] = {
        k: r_after[k] for k in ("passed", "failed", "errors", "timed_out")
    }

    # Half 2 - the same test fails once the fix is reverted.
    sb = make_sandbox(task)
    try:
        inject_heldout(sb, task)
        r_before = run_pytest(sb, task.heldout)
    finally:
        drop_sandbox(sb)
    result["after_revert"] = {
        k: r_before[k] for k in ("passed", "failed", "errors", "timed_out")
    }
    result["revert_tail"] = r_before["tail"][-600:]

    passes_at_commit = (
        r_after["passed"] > 0
        and r_after["failed"] == 0
        and r_after["errors"] == 0
        and not r_after["timed_out"]
    )
    fails_after_revert = r_before["failed"] > 0 or r_before["errors"] > 0
    result["passes_at_commit"] = passes_at_commit
    result["fails_after_revert"] = fails_after_revert
    result["usable"] = bool(passes_at_commit and fails_after_revert)
    if not result["usable"]:
        result["why_not"] = (
            "held-out test does not pass at the commit"
            if not passes_at_commit
            else "held-out test still passes after the revert - it does not "
            "exercise the change, so every arm would score correct"
        )
    result["discriminating_failures"] = r_before["failed"] + r_before["errors"]

    # The rest of the suite already fails in these historical worktrees - 11
    # cells at several of the commits used here, from modules unrelated to any
    # task. Comparing a run against ZERO would score every arm as having caused
    # a regression. Measure the baseline instead, on the same starting state the
    # arms get, and define a regression as a rise above it.
    sb2 = make_sandbox(task)
    try:
        base = run_pytest(sb2, _rest_of_suite(task), timeout=900)
    finally:
        drop_sandbox(sb2)
    result["regression_baseline"] = {
        "failed": base["failed"],
        "errors": base["errors"],
        "passed": base["passed"],
        "timed_out": base["timed_out"],
    }
    return result


def diff_tests_wrapper(sandbox: Path, pristine: Path) -> tuple[list[str], list[str]]:
    """(deleted, modified) test files in `sandbox`, measured against `pristine`.

    A separate name because the guard's diff_tests takes a hash snapshot and the
    runner has a clean worktree to compare against instead - same question,
    different evidence to hand.
    """
    from ch1_sandbox_guard import diff_tests, snapshot_tests as _snap

    return diff_tests(sandbox, _snap(pristine))


TASKS: list[Task] = [
    Task(
        id="C01",
        tier="interactive",
        kind="bugfix",
        commit="f776249",
        revert=["tools/score_aabr.py"],
        heldout=["tests/test_score_aabr.py"],
        budget_s=30,
        prompt=(
            "tools/score_aabr.py grades model answers to the AABR instrument.\n\n"
            "It is marking CORRECT answers as wrong on the unanswerable items - the "
            "ones whose expected outcome is that the model should decline to answer "
            "because the source material does not settle the question.\n\n"
            "A reply that correctly declines can be phrased many ways, and the scorer "
            "must also be able to say 'I cannot decide this mechanically' rather than "
            "being forced into a wrong verdict.\n\n"
            "Fix the scoring so correct declines are credited. Do not change what "
            "counts as a correct answer on the other item types."
        ),
        notes="Small, real, and the failure mode is a false NEGATIVE - the hardest kind to notice.",
    ),
    Task(
        id="C02",
        tier="interactive",
        kind="bugfix",
        commit="916b207",
        revert=["tools/aabr_items.py"],
        heldout=["tests/test_aabr_items.py"],
        budget_s=30,
        prompt=(
            "tools/aabr_items.py loads the AABR item bank and refuses items whose "
            "stated ground truth cannot be reproduced by executing their own "
            "derivation chain.\n\n"
            "The gate is rejecting valid items. It currently demands that the item's "
            "answer key be the LAST step of the derivation, but a legitimate item can "
            "produce its key at any point in the chain and then carry on to state a "
            "related figure.\n\n"
            "Fix the gate so an item is accepted when its key is produced ANYWHERE in "
            "the chain, without weakening it into accepting items whose key the chain "
            "never produces at all."
        ),
        notes="A gate that is wrong in the SAFE direction - it refuses good items.",
    ),
    Task(
        id="C03",
        tier="interactive",
        kind="bugfix",
        commit="bbe651c",
        revert=["tools/webdav_push.py"],
        heldout=["tests/test_webdav_push.py"],
        budget_s=30,
        prompt=(
            "tools/webdav_push.py uploads files to WebDAV storage.\n\n"
            "Its password handling is wrong: it reads the credential from the "
            "environment only, and silently proceeds when that is empty. An empty "
            "credential reaching the server produces a 401 that names nothing, which "
            "has already cost a debugging session.\n\n"
            "Make the credential lookup correct and make the failure loud rather than "
            "silent."
        ),
        notes="Credential handling - the fleet rule is fatal-not-fallback.",
    ),
    Task(
        id="C04",
        tier="substantial",
        kind="refactor",
        commit="f751532",
        revert=["tools/sparkmax_watch_notify.py"],
        heldout=["tests/test_sparkmax_watch_notify.py"],
        budget_s=300,
        prompt=(
            "tools/sparkmax_watch_notify.py runs on a 15-minute timer, checks whether "
            "sparkmax is deadlocked, and sends a message when something is wrong.\n\n"
            "It has a noise problem. When the box is powered off or rebooting the check "
            "cannot run at all, and the tool alerts UNREACHABLE on every single tick - "
            "96 messages a day saying only 'could not look'. A channel muted for that "
            "noise is the same channel the real power-cycle alert arrives on.\n\n"
            "Change it so that:\n"
            "  - UNREACHABLE is suppressed until it has been unreachable 3 consecutive "
            "times, and then sent ONCE per outage rather than on every tick;\n"
            "  - the DEADLOCKED, UNKNOWN and SUSPICIOUS verdicts still alert on every "
            "tick - a deadlock does not self-resolve;\n"
            "  - a recovery message is only sent for a problem that was actually "
            "reported, so a blip that cleared before the threshold announces nothing;\n"
            "  - a FAILED send does not count as having alerted, or a broken message "
            "transport would turn into permanent silence about a wedged box.\n\n"
            "The state file must be redirectable by a caller rather than fixed at "
            "import time."
        ),
        notes="The real one. A state machine with four interacting rules, 102 lines changed.",
    ),
    Task(
        id="C05",
        tier="substantial",
        kind="bugfix",
        commit="82b7455",
        revert=["tools/aabr_items.py"],
        heldout=["tests/test_aabr_items.py"],
        budget_s=300,
        prompt=(
            "tools/aabr_items.py loads a bank of evaluation items and verifies each "
            "one's stated ground truth by executing the item's own derivation chain "
            "through tools/date_calc.py.\n\n"
            "The gate has two bugs that only appear on real items:\n"
            "  - items whose kind is not a date calculation are being put through the "
            "date machinery and rejected, when what should be checked is only that "
            "their declared steps are coherent;\n"
            "  - the chain's intermediate values are not being threaded correctly, so a "
            "later step cannot refer to an earlier one.\n\n"
            "Fix both so a valid item bank loads, and keep the gate strict: an item "
            "whose ground truth the chain does NOT produce must still be refused."
        ),
        notes="Two bugs, one file, discovered on real contact - the shape of ordinary work.",
    ),
    Task(
        id="C06",
        tier="substantial",
        kind="feature",
        commit="8e905bc",
        revert=["tools/gateway/preflight.py"],
        heldout=["tests/test_preflight.py"],
        budget_s=300,
        prompt=(
            "Write tools/gateway/preflight.py.\n\n"
            "The LAN gateway swaps between large local models blue/green: the new "
            "llama-server is started before the old one is stopped, so for a window "
            "BOTH models are resident. On a 128 GB machine a 59 GiB model plus a 17 GiB "
            "model plus KV cache does not fit, and the failure mode is not a clean error "
            "- it is an amdgpu deadlock that needs a physical power cycle.\n\n"
            "Provide a memory pre-check that decides, BEFORE the swap starts, whether "
            "the incoming model can be loaded alongside the outgoing one. It must read "
            "the actual available memory rather than assume it, size the incoming model "
            "from its GGUF files on disk, apply headroom, and refuse rather than "
            "guessing when it cannot read a figure it needs."
        ),
        notes="A whole module from a spec. The revert deletes the file.",
    ),
]

TASKS_BY_ID = {t.id: t for t in TASKS}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate the C-H1 task suite: each held-out test must pass at "
        "its commit and fail after the revert.",
        epilog="example: python3 tools/ch1_tasks.py --validate --out results/raw/ch1-validation.json",
    )
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--only", default=None, help="comma-separated task ids")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    tasks = TASKS
    if args.only:
        want = {s.strip() for s in args.only.split(",")}
        tasks = [t for t in TASKS if t.id in want]
        missing = want - {t.id for t in tasks}
        if missing:
            raise SystemExit(
                f"unknown task ids: {sorted(missing)}\n"
                f"hint: known ids are {sorted(TASKS_BY_ID)}"
            )

    if not args.validate:
        for t in tasks:
            print(f"{t.id}  {t.tier:12s} {t.kind:8s} {t.commit}  budget {t.budget_s}s")
            print(f"      revert  {t.revert}")
            print(f"      heldout {t.heldout}")
        return 0

    results = []
    for i, t in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] validating {t.id} ({t.commit}) ...", flush=True)
        try:
            r = validate_task(t)
        except Exception as exc:  # noqa: BLE001 - a broken task is a RESULT of validation
            r = {
                "id": t.id,
                "commit": t.commit,
                "usable": False,
                "why_not": f"{type(exc).__name__}: {exc}",
            }
        results.append(r)
        mark = "USABLE" if r["usable"] else "REJECTED"
        extra = "" if r["usable"] else f" - {r.get('why_not', '')}"
        print(f"      {mark}{extra}", flush=True)

    usable = [r for r in results if r["usable"]]
    print(f"\n=== {len(usable)}/{len(results)} tasks usable ===")
    for r in results:
        if not r["usable"]:
            print(f"  REJECTED {r['id']}: {r.get('why_not', '')}")
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(
            json.dumps(
                {"validated": results, "usable_ids": [r["id"] for r in usable]},
                indent=2,
            )
        )
        print(f"written: {args.out}")
    return 0 if usable else 1


if __name__ == "__main__":
    sys.exit(main())
