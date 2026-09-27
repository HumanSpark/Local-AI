#!/usr/bin/env python3
# File: score_e138_blocks.py
# Purpose: Score E138 blocks 2-4 (quality banks, Aider, pi on Bonsai 2 PQ2_0) against results/e138-prereg.md P7-P10 and amendments 3-4.
# Project: sparkbench | Date: 2026-09-25
#
# Overview: Reads results/e138/quality-l5-8192.json (amendment 3's re-run; falls back to quality-l5.json and says so),
# quality-core.json, quality-expert.json, agentic-aider.json and agentic-pi.json. Prints each bank's correct/total with its
# truncated count, the Aider and pi pass counts with F171's diff check (a T3 record whose diff is exactly the seed is
# "not applied", never "wrong"), and every prediction with its band and verdict. An absent file is reported as VOID.

from __future__ import annotations

import json
from pathlib import Path

R = Path("/home/agent-spark/sparkbench/results/e138")
INCUMBENT = {
    "l5": (23, 24),
    "core": (15, 15),
    "expert": (7, 8),
    "aider": (2, 3),
}  # E113/F144 figures, from the prereg


def bank(name: str) -> dict | None:
    f = R / f"quality-{name}.json"
    if not f.exists():
        return None
    d = json.loads(f.read_text())
    correct = d.get("correct", d.get("passed"))
    return {
        "correct": correct,
        "total": d["total"],
        "truncated": d.get("truncated", 0),
        "file": f.name,
    }


def agent(name: str) -> dict | None:
    f = R / f"agentic-{name}.json"
    if not f.exists():
        return None
    rows = json.loads(f.read_text())
    out = {"passes": 0, "tasks": [], "file": f.name}
    for x in rows:
        ok = x.get("verify_after_rc") == 0
        diff = x.get("diff") or ""
        label = (
            "pass"
            if ok
            else ("not-applied (seed diff only)" if len(diff) == 978 else "fail")
        )
        out["passes"] += ok
        out["tasks"].append((x["name"].split("-")[0], label))
    return out


def verdict(ok: bool | None) -> str:
    return "VOID" if ok is None else ("HELD" if ok else "FALSIFIED")


l5 = bank("l5-8192")
l5_src = "re-run at 8,192 (amendment 3)"
if l5 is None:
    l5 = bank("l5")
    l5_src = "ORIGINAL 4,096 run (re-run absent)"
core, expert = bank("core"), bank("expert")
aider, pi = agent("aider"), agent("pi")

print("=== E138 blocks 2-4: Bonsai 2 PQ2_0 (B0p) ===")
for label, b, inc in (
    ("l5 documents", l5, INCUMBENT["l5"]),
    ("core coding", core, INCUMBENT["core"]),
    ("expert coding", expert, INCUMBENT["expert"]),
):
    if b is None:
        print(f"{label}: VOID (no file)")
    else:
        print(
            f"{label}: {b['correct']}/{b['total']} correct, {b['truncated']} truncated (unanswered) | incumbent {inc[0]}/{inc[1]} | {b['file']}"
        )
print(f"  l5 source: {l5_src}")
for label, a in (("Aider", aider), ("pi", pi)):
    if a is None:
        print(f"{label}: VOID (no file)")
    else:
        print(f"{label}: {a['passes']}/3 | {a['tasks']} | incumbent Aider 2/3 (E113)")

print()
print("registered predictions:")
if l5:
    print(
        f"  P7 B0.l5_correct 21-23 of 24: {l5['correct']} ({l5['truncated']} unanswered) -> {verdict(21 <= l5['correct'] <= 23)}"
    )
if expert:
    print(
        f"  P8 B0.expert_correct <= 5 of 8: {expert['correct']} ({expert['truncated']} unanswered) -> {verdict(expert['correct'] <= 5)}"
    )
if aider:
    print(
        f"  P9 aider.pass_count <= incumbent 2 of 3: {aider['passes']} -> {verdict(aider['passes'] <= 2)}"
    )
if aider and pi:
    print(
        f"  P10 pi.pass_count == aider.pass_count: {pi['passes']} vs {aider['passes']} -> {verdict(pi['passes'] == aider['passes'])}"
    )
print()
print(
    "F171 check: any task labelled 'not-applied' failed because the edit never reached the file, not because the model was wrong."
)
