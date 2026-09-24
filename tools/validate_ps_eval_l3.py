#!/usr/bin/env python3
# File: validate_ps_eval_l3.py
# Purpose: Prove the L3 tier changes ONLY the pack size, and that wrong-document retrieval is detectable.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: L3's entire claim is that it differs from L2 in one variable - how
# much text the answer is buried in. If the questions, the expected values or
# the graders have drifted, a score drop between L2 and L3 cannot be
# attributed to scale and the tier is worthless. Most of this file exists to
# assert that non-drift mechanically rather than by inspection.
#
# It also drives the new `wrong_document` outcome with a respondent that
# answers every question from the WRONG contract, which is the failure this
# tier was built to detect and the one a generic `wrong` would hide.
#
# Run: python3 tools/validate_ps_eval_l3.py   (exit 0 = L3 is sound)

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "ps-eval"))
from corpus import build_pack  # noqa: E402
from corpus_l2 import build_pack_l2  # noqa: E402
from corpus_l3 import DISTRACTOR_FIGURES, DISTRACTORS, build_pack_l3  # noqa: E402
from questions_l2 import QUESTIONS_L2  # noqa: E402
from questions_l3 import FIGURE_KIND, QUESTIONS_L3, grade_answer_l3  # noqa: E402
from questions import parse_response  # noqa: E402

L1_CHARS, L1_SHA = 10_741, "eb5630b5f7378476"
L2_CHARS = 13_221

# Correct answers, identical to L2's by construction.
PERFECT = {
    "D1": "EUR 42,000", "D2": "EUR 500,000", "D3": "EUR 51,000",
    "V1": "24 months", "V2": "YES",
    "P1": "6 months", "P2": "2 business days",
    "M1": "EUR 378,000", "M2": "EUR 445,500", "M3": "24.5",
    "N1": "(d)", "Z1": "The pack does not specify.",
}


def main() -> int:
    problems: list[str] = []

    # --- the earlier tiers must not have moved -----------------------------
    l1, l2 = build_pack(), build_pack_l2()
    d1 = hashlib.sha256(l1.encode()).hexdigest()
    print(f"L1 {len(l1):>6,} chars sha {d1[:16]} | L2 {len(l2):>6,} chars")
    if len(l1) != L1_CHARS or not d1.startswith(L1_SHA):
        problems.append("L1 pack changed - completed arms no longer compare")
    if len(l2) != L2_CHARS:
        problems.append(f"L2 pack changed: {len(l2)} chars, expected {L2_CHARS}")

    print(f"\nL3 size sweep ({len(DISTRACTORS)} distractor agreements available):")
    for n in (0, 2, 4, 6, 9):
        p = build_pack_l3(n)
        print(f"   n={n}: {len(p):>7,} chars  ~{len(p)//4:>6,} tokens")
    if build_pack_l3(0) != l2:
        problems.append(
            "build_pack_l3(0) differs from the L2 pack - the zero-distractor case must "
            "BE L2, or the sweep's baseline is a different instrument"
        )

    # --- the one-variable claim -------------------------------------------
    if len(QUESTIONS_L3) != len(QUESTIONS_L2):
        problems.append(f"question count differs: L2 {len(QUESTIONS_L2)}, L3 {len(QUESTIONS_L3)}")
    l2_by_id = {q["id"]: q for q in QUESTIONS_L2}
    drifted = []
    for q in QUESTIONS_L3:
        base = l2_by_id[q["id"]]
        if q["expect"].get("values") != base["expect"].get("values"):
            drifted.append((q["id"], base["expect"].get("values"), q["expect"].get("values")))
        if q["category"] != base["category"]:
            drifted.append((q["id"], base["category"], q["category"]))
    print(f"\nexpected values identical to L2: {'yes' if not drifted else drifted}")
    if drifted:
        problems.append(f"L3 answers drifted from L2 - a score drop could not be attributed "
                        f"to scale: {drifted}")

    # --- every question must name its scope --------------------------------
    # In a pack of ten services agreements an unscoped question has no single
    # right answer. This is E38 AMENDMENT 1's lesson applied before the fact.
    unscoped = [q["id"] for q in QUESTIONS_L3
                if "calderwood" not in q["question"].lower()
                and q["id"] != "N1"]  # N1's five options carry their own scope
    print(f"questions naming their agreement: {len(QUESTIONS_L3) - len(unscoped)}"
          f"/{len(QUESTIONS_L3)} (N1 exempt by design)")
    if unscoped:
        problems.append(f"unscoped questions in a multi-agreement pack: {unscoped}")

    # --- graders ------------------------------------------------------------
    def score(overrides: dict) -> dict[str, int]:
        tally: dict[str, int] = {}
        for q in QUESTIONS_L3:
            ans = overrides.get(q["id"], PERFECT[q["id"]])
            parsed, _ = parse_response(f"ANSWER: {ans}\nCITATION: x")
            o = grade_answer_l3(q, parsed)
            tally[o] = tally.get(o, 0) + 1
        return tally

    perfect = score({})
    print(f"\n  PERFECT        {perfect}")
    if perfect.get("correct") != len(QUESTIONS_L3):
        problems.append(f"PERFECT scored {perfect.get('correct', 0)}/{len(QUESTIONS_L3)}")

    # Answers every numeric question from a distractor contract.
    wrong_doc = {qid: str(DISTRACTOR_FIGURES[kind][0])
                 for qid, kind in FIGURE_KIND.items() if kind}
    wd = score(wrong_doc)
    print(f"  WRONG_DOCUMENT {wd}")
    if wd.get("wrong_document") != len(wrong_doc):
        problems.append(
            f"WRONG_DOCUMENT produced {wd.get('wrong_document', 0)} wrong_document "
            f"outcomes, expected {len(wrong_doc)} - retrieval from the wrong contract "
            f"is the failure this tier exists to detect and it is not being named"
        )

    prose = {q["id"]: "the answer is somewhere in the pack" for q in QUESTIONS_L3}
    print(f"  VAGUE          {score(prose)}")

    # --- disjointness, restated rather than trusted ------------------------
    real = {"retainer": {42_000, 46_500, 51_000}, "cap": {500_000, 1_250_000},
            "notice": {90, 120}, "retention": {6, 12, 24}, "response": {1, 2}}
    clashes = {k: sorted(set(v) & real[k]) for k, v in DISTRACTOR_FIGURES.items()
               if set(v) & real[k]}
    print(f"\n  distractor/real figure clashes: {clashes or 'none'}")
    if clashes:
        problems.append(f"distractor figures collide with real ones: {clashes} - a "
                        f"wrong-document answer would score as correct")

    print()
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("L3 sound: one variable changed, answers identical to L2, every question "
          "scoped, wrong-document retrieval detectable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
