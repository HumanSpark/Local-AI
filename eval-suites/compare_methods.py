#!/usr/bin/env python3
# File: compare_methods.py
# Purpose: Measure how often keyed scoring and blind pairwise judging disagree on the same answers.
# Project: sparkbench | Date: 2026-08-11
#
# Overview: The disagreement rate IS the finding. If the two methods agree, pairwise judging is
# cheap and defensible and we keep using it; if they diverge, we have measured what an LLM
# judge's verdict is worth against checkable ground truth. keyed_verdict() ranks by element
# coverage with contradictions as the tiebreak; judge_verdict() folds a pairing's two label
# orders into one verdict and returns "position_dependent" when they disagree - that pairing is
# then excluded from the denominator and reported separately, never counted as agreement.
# Plan: docs/plans/2026-08-11-benchmark-instrumentation-uplift.md task 3.

from __future__ import annotations

import argparse
import glob
import itertools
import json
import sys
from pathlib import Path

from score_keyed import load_key, score_answer


def keyed_verdict(label_a: str, score_a: dict, label_b: str, score_b: dict) -> str:
    """Rank two answers by element coverage, breaking ties on fewer contradictions."""
    if score_a["hits"] != score_b["hits"]:
        return label_a if score_a["hits"] > score_b["hits"] else label_b
    ca, cb = len(score_a["contradictions"]), len(score_b["contradictions"])
    if ca != cb:
        return label_a if ca < cb else label_b
    return "tie"


def judge_verdict(records: list[dict], pair: tuple[str, str]) -> str:
    """Fold both label orders of one pairing into a single verdict.

    Both orders agreeing is the only case that yields a usable verdict. When they
    disagree the judge is responding to slot position rather than content, which is a
    property of the judge - reporting a winner there would launder a coin flip.
    """
    got = [r["winner"] for r in records if tuple(r["pair"]) == pair]
    if len(got) != 2:
        raise ValueError(
            f"expected 2 order records for pairing {pair}, found {len(got)}; "
            f"hint: judge_pairwise.py writes one record per label order - re-run it"
        )
    return got[0] if got[0] == got[1] else "position_dependent"


def agreement(rows: list[dict]) -> dict:
    """Agreement between the two methods, with the denominator it was computed over."""
    excluded = [r for r in rows if r["judge"] == "position_dependent"]
    comparable = [r for r in rows if r["judge"] != "position_dependent"]
    agree = [r for r in comparable if r["keyed"] == r["judge"]]
    disagree = [r for r in comparable if r["keyed"] != r["judge"]]
    n = len(comparable)
    return {
        "compared": n,
        "agree": len(agree),
        "disagree": len(disagree),
        "excluded_position_dependent": len(excluded),
        "disagreement_rate": f"{len(disagree)}/{n}" if n else "0/0 - nothing comparable",
        "disagreeing_pairs": [r["pair"] for r in disagree],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compare keyed scoring against blind pairwise judging on the same answers.",
        epilog="Example: python3 compare_methods.py --key keys/e10-full-table.yaml "
               "--pairwise ../../results/eval-pilot/e10-pairwise-material-outcome.json",
    )
    ap.add_argument("--key", default="keys/e10-full-table.yaml")
    ap.add_argument("--results-glob", default="../../results/eval-pilot/e10-*.json")
    ap.add_argument("--pairwise", required=True, help="output of judge_pairwise.py")
    ap.add_argument("--out", help="optional JSON report path")
    args = ap.parse_args()

    key = load_key(args.key)
    scores: dict[str, dict] = {}
    for f in sorted(glob.glob(args.results_glob)):
        label = Path(f).stem.replace("e10-", "")
        d = json.loads(Path(f).read_text())
        scores[label] = score_answer(str(d["results"]["results"][0]["response"]["output"]), key)

    pw = json.loads(Path(args.pairwise).read_text())
    records = pw["records"]

    print("Keyed scores (element coverage against the answer key):")
    for label in sorted(scores):
        s = scores[label]
        bad = [c["value"] for c in s["contradictions"]]
        flag = "  TRUNCATED - coverage is a LOWER BOUND" if s["truncated"] else ""
        print(f"  {label:18s} {s['coverage']:>5s}  rows={s['rows_found']:2d}  "
              f"contradictions={bad}{flag}")
    if all(s["truncated"] for s in scores.values()):
        print("\n  !! EVERY answer is truncated. Coverage differences here may reflect a\n"
              "     harness ceiling rather than model capability, and no capability claim\n"
              "     should be built on this substrate without a re-run. Which ceiling is\n"
              "     not decidable from the answers - run spikes/eval-pilot/audit_ceiling.py,\n"
              "     because the context window and max_tokens need different fixes.")

    rows = []
    for a, b in itertools.combinations(sorted(scores), 2):
        rows.append({"pair": [a, b],
                     "keyed": keyed_verdict(a, scores[a], b, scores[b]),
                     "judge": judge_verdict(records, (a, b))})

    print("\nPer-pairing verdicts:")
    for r in rows:
        flag = "" if r["keyed"] == r["judge"] else "   <-- DISAGREE"
        if r["judge"] == "position_dependent":
            flag = "   <-- judge flipped with slot order"
        print(f"  {r['pair'][0]:18s} vs {r['pair'][1]:18s} "
              f"keyed={r['keyed']:18s} judge={r['judge']:18s}{flag}")

    result = agreement(rows)
    print(f"\nDisagreement rate: {result['disagreement_rate']} "
          f"({result['agree']} agree, {result['disagree']} disagree, "
          f"{result['excluded_position_dependent']} excluded as position-dependent)")

    if args.out:
        Path(args.out).write_text(json.dumps(
            {"scores": scores, "rows": rows, "agreement": result}, indent=1))
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
