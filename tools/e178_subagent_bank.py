#!/usr/bin/env python3
# File: tools/e178_subagent_bank.py
# Purpose: E178 - prepare hard-bank task trees for Claude Code subagents and grade them with the bank's own tests.
# Project: sparkbench | Date: 2026-11-25
#
# Overview: results/e178-prereg.md. `prepare ARM TASK` materialises the task's base commit as a fresh one-commit repo
# (coding_harness.materialise_at, so the fix commit is not reachable), writes the visible test files and the
# .graded_tests.sh runner exactly as the harness does for visible-test tasks, and prints the tree path and the task
# prompt. `verify ARM TASK [--wall-s N] [--turns N]` rewrites the test files over the tree (the agent may have
# edited them), runs the task's verify_cmd with a timeout, and writes results/e178/raw/ARM/TASK.json with the same
# status/passed/verify fields the harness writes, plus the diff size. Host verify (the repos are the owner's own
# trusted code); the harness verifies inside podman. Tasks come from var/e167-tasks/ (the E167 hard bank).
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from coding_harness import VISIBLE_RUNNER, materialise_at, read_test_files  # noqa: E402

TASKS = ROOT / "var/e167-tasks"
TREES = ROOT / "var/e178"
RAW = ROOT / "results/e178/raw"


def spec(task: str) -> dict:
    f = TASKS / f"{task}.json"
    if not f.is_file():
        raise FileNotFoundError(f"no task {task} in {TASKS}; hint: ids are the file stems there")
    s = json.loads(f.read_text())
    s["test_files"] = read_test_files(s["repo"], s["fix_sha"], s["test_paths"])
    return s


def tree(arm: str, task: str) -> Path:
    return TREES / arm / task


def prepare(arm: str, task: str) -> None:
    s = spec(task)
    t = tree(arm, task)
    if t.exists():
        raise FileExistsError(f"{t} exists; hint: one attempt per task - do not reuse a tree")
    materialise_at(s["repo"], s["base_sha"], t)
    for rel, content in {**s["test_files"], VISIBLE_RUNNER: s["verify_cmd"] + "\n"}.items():
        (t / rel).parent.mkdir(parents=True, exist_ok=True)
        (t / rel).write_text(content)
    print(json.dumps({"tree": str(t), "prompt": s["prompt"]}))


def verify(arm: str, task: str, wall_s: float | None, turns: int | None) -> None:
    s = spec(task)
    t = tree(arm, task)
    if not t.is_dir():
        raise FileNotFoundError(f"{t} missing; hint: run prepare first")
    for rel, content in s["test_files"].items():  # graded tests are the bank's, whatever the agent did to its copy
        (t / rel).write_text(content)
    # intent-to-add so files the agent created count in the diff (a plain diff only sees tracked files)
    subprocess.run(["git", "-C", str(t), "add", "-A", "--intent-to-add"], capture_output=True, timeout=60)
    diff = subprocess.run(["git", "-C", str(t), "diff", "--stat", "HEAD", "--", ".", f":!{VISIBLE_RUNNER}"]
                          + [f":!{p}" for p in s["test_paths"]], capture_output=True, text=True, timeout=60).stdout
    t0 = time.time()
    try:
        r = subprocess.run(s["verify_cmd"], shell=True, cwd=t, capture_output=True, text=True, timeout=600)
        rc, out = r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired as e:
        rc, out = 124, f"verify timed out after 600 s: {e}"
    rec = {"task": task, "arm": arm, "status": "pass" if rc == 0 else "fail", "passed": rc == 0,
           "verify": {"after_rc": rc, "after_tail": out[-4000:], "verify_s": round(time.time() - t0, 1)},
           "diff_stat": diff.strip().splitlines()[-1] if diff.strip() else "no changes",
           "wall_time": wall_s, "turns": turns, "scaffold": "Claude Code subagent (Agent tool)", "isolation": "host"}
    (RAW / arm).mkdir(parents=True, exist_ok=True)
    (RAW / arm / f"{task}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(f"[e178] {arm} {task}: {rec['status']} (rc {rc}; {rec['diff_stat']})")


def main() -> int:
    ap = argparse.ArgumentParser(description="E178: hard-bank trees for Claude Code subagents, and their grading.",
                                 epilog="example: tools/e178_subagent_bank.py prepare sonnet clearmail-3d41463d0")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "verify"):
        p = sub.add_parser(name)
        p.add_argument("arm", choices=["sonnet", "opus", "fable"])
        p.add_argument("task")
        if name == "verify":
            p.add_argument("--wall-s", type=float)
            p.add_argument("--turns", type=int)
    a = ap.parse_args()
    if a.cmd == "prepare":
        prepare(a.arm, a.task)
    else:
        verify(a.arm, a.task, a.wall_s, a.turns)
    return 0


if __name__ == "__main__":
    sys.exit(main())
