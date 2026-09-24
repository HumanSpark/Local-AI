#!/usr/bin/env python3
# File: compare_positions.py
# Purpose: Compare the SAME matters scored across runs that differ only in request order.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: F70 established that a byte-identical prompt gives a byte-different
# answer depending on how many requests preceded it, because llama-server reuses
# the KV prefix and differently-chunked prefill accumulates floating point
# differently. That is a reproducibility result. E51 asks the commercial
# question instead: does the ADVICE change?
#
# The comparison is deliberately stricter than "same score". Two runs can both
# score a matter 4/5 while missing DIFFERENT elements, which is the same number
# and different advice - the failure a score-only check would wave through. So
# agreement here requires the missed-element SET to match, not just its size.
#
# Traps are compared too. A trap reproduced at one position and not another
# would be the worst version of this result, because traps are the specific
# wrong answers the corpus was built to catch.
#
# Run: python3 compare_positions.py <scored.json> <scored.json> [...]
#      (each input is `score_run.py --run X --json` output)

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_scored(path: Path) -> tuple[str, dict[str, dict]]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. hint: produce it with "
            f"score_run.py --run <run.json> --json > {path}"
        )
    d = json.loads(path.read_text())
    by_matter: dict[str, dict] = {}
    for r in d["rows"]:
        # rep 0 only: E51 runs one rep per position, and silently averaging
        # reps would hide the very variation being measured.
        if int(r["rep"]) != 0:
            continue
        by_matter[r["matter"]] = r
    if not by_matter:
        raise ValueError(f"{path} has no rep-0 rows. hint: was the run empty?")
    return d["label"], by_matter


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compare matters across runs that differ only in request order.",
        epilog="example: python3 compare_positions.py a.json b.json c.json",
    )
    ap.add_argument("scored", nargs="+", type=Path,
                    help="two or more score_run.py --json outputs")
    args = ap.parse_args()
    if len(args.scored) < 2:
        raise SystemExit("need at least two scored runs to compare")

    runs = [load_scored(p) for p in args.scored]
    labels = [lbl for lbl, _ in runs]
    common = sorted(set.intersection(*[set(m) for _, m in runs]))
    if not common:
        raise ValueError(
            f"no matters common to all of {labels}. "
            f"hint: the runs must cover the same matter set"
        )

    print(f"comparing {len(common)} matters across {len(runs)} runs: {', '.join(labels)}\n")
    hdr = f"{'matter':32}" + "".join(f"{lbl[:14]:>16}" for lbl in labels) + "  verdict"
    print(hdr)
    print("-" * len(hdr))

    score_stable = missed_stable = traps_stable = 0
    disagreements = []
    for m in common:
        rows = [by[m] for _, by in runs]
        scores = [f"{r['hits']}/{r['of']}" for r in rows]
        missed = [tuple(sorted(r["missed"])) for r in rows]
        traps = [tuple(sorted(r["traps"])) for r in rows]
        same_score = len(set(scores)) == 1
        same_missed = len(set(missed)) == 1
        same_traps = len(set(traps)) == 1
        score_stable += same_score
        missed_stable += same_missed
        traps_stable += same_traps
        if same_score and same_missed and same_traps:
            verdict = "stable"
        elif same_score and not same_missed:
            # The case a score-only check would have passed.
            verdict = f"SAME SCORE, DIFFERENT ELEMENTS {missed}"
            disagreements.append((m, verdict))
        else:
            verdict = f"CHANGED {scores}" + ("" if same_traps else f" TRAPS {traps}")
            disagreements.append((m, verdict))
        print(f"{m:32}" + "".join(f"{s:>16}" for s in scores) + f"  {verdict}")

    n = len(common)
    print(f"\nscore identical at every position : {score_stable}/{n}")
    print(f"missed-element SET identical      : {missed_stable}/{n}")
    print(f"traps identical                   : {traps_stable}/{n}")
    totals = [sum(by[m]["hits"] for m in common) for _, by in runs]
    of = sum(runs[0][1][m]["of"] for m in common)
    print("run totals                        : " + ", ".join(f"{t}/{of}" for t in totals))

    if disagreements:
        print("\nDISAGREEMENTS - advice changed with request position:")
        for m, v in disagreements:
            print(f"  {m}: {v}")
        return 1
    print("\nAll matters stable across every request position tested.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
