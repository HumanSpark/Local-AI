#!/usr/bin/env python3
# File: tools/score_l5_bands.py
# Purpose: Score L5 runs by BAND, because the tier's total is the least informative number it produces.
# Project: sparkbench | Date: 2026-08-28
#
# Overview: L5 splits its difficulty into a reasoning-limited band and an
# evidence-limited band on purpose, and E78's headline prediction is about the
# DIFFERENCE between the two bands' separations. A total conflates them: an arm
# can move ten points on reasoning and none on evidence and the total reports
# one number that describes neither.
#
# It re-grades from the stored answers rather than trusting the outcome banked
# at run time. That is deliberate. The workhorse pilot was graded before E05's
# count alias was fixed, so its banked outcome for that item says `partial`
# where the current grader says `correct`, and a comparison that mixed the two
# grader versions would be measuring the grader.

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "spikes" / "ps-eval"))

from questions_l5 import QUESTIONS_L5, grade_answer_l5  # noqa: E402

ANALYSIS_VERSION = "l5-bands-v1-2026-08-28"
ITEMS = {q["id"]: q for q in QUESTIONS_L5}


def score_run(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    per_band: dict[str, Counter] = {"R": Counter(), "E": Counter()}
    correct: Counter = Counter()
    relabelled: list[str] = []
    rows = []

    # Outcomes the RUNNER determined from transport or finish_reason, which
    # re-grading cannot see and must not overwrite. A truncated answer is
    # stored as None, and grading None returns `format_error` - which would
    # report a model that ran out of its token budget as one that produced an
    # unusable answer shape. Those need different fixes and E78's decision rule
    # sends a format_error to a grader audit, so conflating them would send the
    # audit after the wrong thing. Found by that audit, on the 8B's R10 and R12,
    # where finish_reason was `length` at 4,096 tokens after 14,968 characters
    # of reasoning.
    RUNNER_OWNED = {"truncated", "transport_failed"}

    for r in data["results"]:
        item = ITEMS[r["id"]]
        if r["outcome"] in RUNNER_OWNED:
            verdict = r["outcome"]
        else:
            verdict = grade_answer_l5(item, r["answer"])
        if verdict != r["outcome"]:
            relabelled.append(
                f"{r['id']}: banked {r['outcome']} -> re-graded {verdict}"
            )
        per_band[item["band"]][verdict] += 1
        if verdict == "correct":
            correct[item["band"]] += 1
        rows.append(
            {
                "id": r["id"],
                "band": item["band"],
                "difficulty": item["difficulty"],
                "category": item["category"],
                "banked_outcome": r["outcome"],
                "verdict": verdict,
            }
        )

    return {
        "label": data["label"],
        "model": data["model"],
        "total_correct": correct["R"] + correct["E"],
        "band_R_correct": correct["R"],
        "band_E_correct": correct["E"],
        "band_R_outcomes": dict(per_band["R"]),
        "band_E_outcomes": dict(per_band["E"]),
        "regraded_since_run": relabelled,
        "rule9_breach_acknowledged": data["rule9_breach_acknowledged"],
        "kernel": data["kernel"],
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score L5 runs by band and report the between-arm separation per band.",
        epilog="example: python3 tools/score_l5_bands.py results/raw/l5-*.json "
        "--out results/raw/e78-scores.json",
    )
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    runs = [score_run(Path(f)) for f in args.files]
    runs.sort(key=lambda r: r["total_correct"])

    print(f"{'arm':16s} {'total':>7s} {'band R':>8s} {'band E':>8s}")
    for r in runs:
        print(
            f"{r['label']:16s} {r['total_correct']:>4d}/24 {r['band_R_correct']:>6d}/12 "
            f"{r['band_E_correct']:>6d}/12"
        )
        for note in r["regraded_since_run"]:
            print(f"    re-graded: {note}")

    spread = {
        "band_R": max(r["band_R_correct"] for r in runs)
        - min(r["band_R_correct"] for r in runs),
        "band_E": max(r["band_E_correct"] for r in runs)
        - min(r["band_E_correct"] for r in runs),
    }
    print(
        f"\nseparation across arms: band R {spread['band_R']} points, "
        f"band E {spread['band_E']} points"
    )

    out = {"analysis_version": ANALYSIS_VERSION, "separation": spread, "runs": runs}
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
        print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
