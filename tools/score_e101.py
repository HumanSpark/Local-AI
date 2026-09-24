#!/usr/bin/env python3
# File: score_e101.py
# Purpose: Score E101's five cells against its six pre-registered predictions.
# Project: sparkbench | Date: 2026-09-04
#
# Overview: Reads results/raw/e101/*.json, pools replicate seeds within a cell,
# and prints the cell table plus a verdict per prediction. Written BEFORE the
# cells finished so the scoring rule could not be shaped by the numbers.
#
# The predictions, verbatim from the E101 registration:
#   P1 cell4 truncated >= 6 of 18
#   P2 cell5.truncated - cell4.truncated <= -3            (DISCRIMINATING)
#   P3 (cell2 - cell4) more negative than (cell5 - cell4) (HEADLINE)
#   P4 cell1 normalize_path and roman_roundtrip both pass
#   P5 mean max_ngram_rep over truncated >= 3x over pass, pooled cells 2-5
#   P6 transport_failed and no_code both 0 across all runs

from __future__ import annotations

import argparse
import json
from pathlib import Path

CELLS = {
    "c1": "greedy, medium effort (control)",
    "c2": "sampled min-p 0.00, medium effort",
    "c3": "sampled min-p 0.05, medium effort",
    "c4": "sampled min-p 0.00, xhigh effort  (THEIR CONFIG)",
    "c5": "sampled min-p 0.05, xhigh effort  (THEIR FIX)",
}


def load(indir: Path) -> dict[str, list[dict]]:
    """Group every run file under its cell prefix. Missing cell = loud, not empty."""
    cells: dict[str, list[dict]] = {c: [] for c in CELLS}
    files = sorted(indir.glob("*.json"))
    if not files:
        raise SystemExit(
            f"no run files in {indir}. hint: E101 writes one JSON per invocation; "
            f"an empty directory means the cells never ran, which is not a result."
        )
    for f in files:
        prefix = f.name.split("-", 1)[0]
        if prefix not in cells:
            raise SystemExit(
                f"{f.name} does not belong to a registered cell {sorted(CELLS)}. "
                f"hint: an unregistered arm must not be pooled into a scored one."
            )
        cells[prefix].append(json.loads(f.read_text()))
    missing = [c for c, v in cells.items() if not v]
    if missing:
        raise SystemExit(
            f"cells with no data: {missing}. Scoring a partial experiment against "
            f"predictions written for the whole one reports the SHORTFALL as a "
            f"result. hint: wait for the runs, or score explicitly with --partial."
        )
    return cells


def items(runs: list[dict]) -> list[dict]:
    return [r for run in runs for r in run["results"]]


def count(runs: list[dict], outcome: str) -> int:
    return sum(1 for r in items(runs) if r["outcome"] == outcome)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", default="results/raw/e101")
    ap.add_argument("--partial", action="store_true",
                    help="score whatever cells exist. The output is labelled "
                         "PARTIAL and no prediction verdict is authoritative.")
    a = ap.parse_args()
    indir = Path(a.indir)
    try:
        cells = load(indir)
    except SystemExit:
        if not a.partial:
            raise
        cells = {c: [] for c in CELLS}
        for f in sorted(indir.glob("*.json")):
            cells.setdefault(f.name.split("-", 1)[0], []).append(json.loads(f.read_text()))

    print(f"{'cell':4s} {'n':>4s} {'pass':>5s} {'trunc':>6s} {'fail':>5s} "
          f"{'nocode':>7s} {'transp':>7s} {'medtok':>7s}  description")
    stats = {}
    for c, desc in CELLS.items():
        runs = cells.get(c) or []
        it = items(runs)
        toks = sorted(r["completion_tokens"] for r in it
                      if r.get("completion_tokens") is not None)
        med = toks[len(toks) // 2] if toks else 0
        stats[c] = {
            "n": len(it), "pass": count(runs, "pass"), "trunc": count(runs, "truncated"),
            "fail": count(runs, "fail"), "no_code": count(runs, "no_code"),
            "transport_failed": count(runs, "transport_failed"), "med_tokens": med,
        }
        s = stats[c]
        print(f"{c:4s} {s['n']:4d} {s['pass']:5d} {s['trunc']:6d} {s['fail']:5d} "
              f"{s['no_code']:7d} {s['transport_failed']:7d} {med:7d}  {desc}")

    print()
    verdicts = []

    def verdict(n, text, ok, detail, needs=()):
        """A prediction whose cells have NO DATA is unscored, never FALSIFIED.

        Printing FALSIFIED against an empty cell is a false signal that reads
        exactly like a real result - 'cell4 truncated = 0 of 0' satisfies no
        threshold, so every comparison trivially fails. An absent measurement
        and a measurement that came back negative are different facts.
        """
        empty = [c for c in needs if stats.get(c, {}).get("n", 0) == 0]
        if empty:
            verdicts.append((n, "NO DATA"))
            print(f"P{n} {'NO DATA':10s} {text}\n     cells not yet run: {empty}")
            return
        mark = "HELD" if ok else "FALSIFIED"
        verdicts.append((n, mark))
        print(f"P{n} {mark:10s} {text}\n     {detail}")

    c4t, c5t, c2t = stats["c4"]["trunc"], stats["c5"]["trunc"], stats["c2"]["trunc"]
    verdict(1, "their config runs away >= 6 of 18",
            c4t >= 6, f"cell4 truncated = {c4t} of {stats['c4']['n']}", needs=("c4",))
    verdict(2, "min-p reduces non-termination by >= 3 at xhigh",
            (c5t - c4t) <= -3, f"cell5 - cell4 = {c5t - c4t} ({c5t} vs {c4t})",
            needs=("c4", "c5"))
    effort_delta, minp_delta = c2t - c4t, c5t - c4t
    verdict(3, "reasoning effort dominates the sampler",
            effort_delta < minp_delta,
            f"effort (c2-c4) = {effort_delta}; min-p (c5-c4) = {minp_delta}; "
            f"effort wins = {effort_delta < minp_delta}", needs=("c2", "c4", "c5"))

    c1 = {r["id"]: r["outcome"] for r in items(cells.get("c1") or [])}
    tgt = ["normalize_path", "roman_roundtrip"]
    verdict(4, "F71 reproduces on the greedy control",
            all(c1.get(t) == "pass" for t in tgt),
            "; ".join(f"{t}={c1.get(t, 'MISSING')}" for t in tgt), needs=("c1",))

    pooled = items([r for c in ("c2", "c3", "c4", "c5") for r in (cells.get(c) or [])])

    def mean_rep(outcome):
        v = [r["repetition"]["max_ngram_rep"] for r in pooled
             if r["outcome"] == outcome and r.get("repetition")]
        return sum(v) / len(v) if v else 0.0

    mt, mp = mean_rep("truncated"), mean_rep("pass")
    verdict(5, "repetition meter tracks non-termination",
            mp > 0 and mt >= 3 * mp,
            f"mean max_ngram_rep: truncated={mt:.1f}, pass={mp:.1f}, "
            f"ratio={(mt / mp if mp else float('inf')):.2f}",
            needs=("c2", "c3", "c4", "c5"))

    tot_bad = sum(stats[c]["transport_failed"] + stats[c]["no_code"] for c in CELLS)
    verdict(6, "harness holds (transport_failed + no_code = 0)",
            tot_bad == 0, f"total = {tot_bad}")

    nd = sum(1 for _, m in verdicts if m == "NO DATA")
    print(f"\nheld {sum(1 for _, m in verdicts if m == 'HELD')} of "
          f"{len(verdicts) - nd} scorable"
          + (f"; {nd} UNSCORED (cells not yet run)" if nd else ""))
    if a.partial:
        print("PARTIAL RUN - no verdict above is authoritative.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
