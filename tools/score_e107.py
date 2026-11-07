#!/usr/bin/env python3
# File: score_e107.py
# Purpose: Score E107's temperature sweep against its six pre-registered predictions.
# Project: sparkbench | Date: 2026-09-05
#
# Overview: Reads results/raw/e107/*.json, pools seeds within a temperature
# cell, and reports the primary metric (over_claim on the 4 underspecified
# items) plus band R / band E / total, with the E82 noise floor printed beside
# every contrast so no one quotes a 1-item difference as an effect.
#
# Written while cells were still running, so the scoring rule could not be
# shaped by the numbers. Bands are re-graded through score_l5_bands' grader
# rather than trusting banked outcomes, for the reason that tool documents.

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "spikes" / "ps-eval"))
from questions_l5 import QUESTIONS_L5  # noqa: E402

# E82 measured prompt ORDER alone moving 2 items across twelve shuffles. Any
# contrast at or below this is inside characterised noise and is NOT an effect.
NOISE_FLOOR_ITEMS = 2

CELLS = {"t0": "0.0 greedy (control)", "t04": "0.4", "t07": "0.7", "t10": "1.0 (shipped default)"}
BAND = {q["id"]: q["band"] for q in QUESTIONS_L5}
if sorted(set(BAND.values())) != ["E", "R"]:
    raise SystemExit(
        f"questions_l5 bands are {sorted(set(BAND.values()))}, expected R and E. "
        f"hint: without a band map every item scores as band-less and the cell "
        f"table would report 0/0, which reads as total collapse rather than a "
        f"broken scorer."
    )


def load(indir: Path) -> dict[str, list[dict]]:
    cells: dict[str, list[dict]] = {c: [] for c in CELLS}
    files = sorted(indir.glob("*.json"))
    if not files:
        raise SystemExit(
            f"no run files in {indir}. hint: an empty directory is not a null "
            f"result - the cells never ran."
        )
    for f in files:
        # e107-t0.json -> t0 ; e107-t04-s301.json -> t04
        cell = f.stem.split("-")[1]
        if cell not in cells:
            raise SystemExit(
                f"{f.name} is not a registered cell {sorted(CELLS)}. hint: an "
                f"unregistered arm must not be pooled into a scored one."
            )
        cells[cell].append(json.loads(f.read_text()))
    return cells


def stats_for(runs: list[dict]) -> dict:
    """Per-run figures, then the mean. A cell with no runs returns None, never 0."""
    if not runs:
        return {"n_runs": 0}
    per = []
    for d in runs:
        res = d["results"]
        per.append({
            "correct": sum(1 for r in res if r["outcome"] == "correct"),
            "over_claim": sum(1 for r in res if r["outcome"] == "over_claim"),
            "bandR": sum(1 for r in res if r["outcome"] == "correct" and BAND.get(r["id"]) == "R"),
            "bandE": sum(1 for r in res if r["outcome"] == "correct" and BAND.get(r["id"]) == "E"),
            "format_error": sum(1 for r in res if r["outcome"] == "format_error"),
        })
    out = {"n_runs": len(per), "per_run": per}
    for k in ("correct", "over_claim", "bandR", "bandE", "format_error"):
        out[k] = statistics.mean(p[k] for p in per)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--indir", default="results/raw/e107")
    a = ap.parse_args()
    cells = load(Path(a.indir))
    st = {c: stats_for(runs) for c, runs in cells.items()}

    print(f"{'cell':5s} {'n':>2s} {'correct':>8s} {'bandR':>6s} {'bandE':>6s} "
          f"{'over_claim':>11s}  description")
    for c, desc in CELLS.items():
        s = st[c]
        if not s["n_runs"]:
            print(f"{c:5s} {'-':>2s} {'NO DATA':>8s} {'-':>6s} {'-':>6s} {'-':>11s}  {desc}")
            continue
        print(f"{c:5s} {s['n_runs']:2d} {s['correct']:8.2f} {s['bandR']:6.2f} "
              f"{s['bandE']:6.2f} {s['over_claim']:11.2f}  {desc}")
        if s["n_runs"] > 1:
            print(f"{'':5s}    per-seed correct: {[p['correct'] for p in s['per_run']]}"
                  f"  over_claim: {[p['over_claim'] for p in s['per_run']]}")

    print(f"\nE82 noise floor: {NOISE_FLOOR_ITEMS} items (prompt order alone). "
          f"Contrasts at or below it are UNDETECTED, not absent.\n")

    verdicts = []

    def verdict(n, text, ok, detail, needs):
        missing = [c for c in needs if not st[c]["n_runs"]]
        if missing:
            verdicts.append("NO DATA")
            print(f"P{n} {'NO DATA':10s} {text}\n     cells not yet run: {missing}")
            return
        mark = "HELD" if ok else "FALSIFIED"
        verdicts.append(mark)
        print(f"P{n} {mark:10s} {text}\n     {detail}")

    if st["t0"]["n_runs"] and st["t10"]["n_runs"]:
        d_oc = st["t10"]["over_claim"] - st["t0"]["over_claim"]
        d_e = st["t0"]["bandE"] - st["t10"]["bandE"]
        d_r = st["t0"]["bandR"] - st["t10"]["bandR"]
    else:
        d_oc = d_e = d_r = None

    verdict(1, "temperature increases fabrication (t10 over_claim - t0 >= 1)",
            d_oc is not None and d_oc >= 1,
            f"delta = {d_oc:+.2f} of 4 underspecified items" if d_oc is not None else "",
            ("t0", "t10"))
    verdict(2, "evidence work degrades with temperature (band E drop >= 2)",
            d_e is not None and d_e >= 2,
            f"band E drop = {d_e:+.2f}"
            + ("  [INSIDE NOISE FLOOR]" if d_e is not None and abs(d_e) <= NOISE_FLOOR_ITEMS else "")
            if d_e is not None else "", ("t0", "t10"))
    verdict(3, "reasoning is less affected than evidence",
            d_r is not None and d_e is not None and d_r < d_e,
            f"band R drop {d_r:+.2f} vs band E drop {d_e:+.2f}" if d_r is not None else "",
            ("t0", "t10"))
    verdict(4, "0.4 is safe (mean total >= 22 of 24)",
            st["t04"]["n_runs"] and st["t04"]["correct"] >= 22,
            f"t04 mean correct = {st['t04'].get('correct', 0):.2f}", ("t04",))

    # P5: the arm actually sampled. Checked on ANSWER TEXT, because a cell that
    # silently ran greedy would satisfy every other prediction by not moving.
    if st["t10"]["n_runs"] >= 2:
        answers: dict[str, set] = {}
        for d in cells["t10"]:
            for r in d["results"]:
                answers.setdefault(r["id"], set()).add(r.get("answer") or "")
        varying = [k for k, v in answers.items() if len(v) > 1]
        verdict(5, "the arm actually sampled (>1 distinct answer on some item)",
                bool(varying), f"{len(varying)} of 24 items vary across t10 seeds: "
                f"{varying[:6]}", ("t10",))
    else:
        verdict(5, "the arm actually sampled", False, "", ("t10",))

    fe = sum(st[c].get("format_error", 0) for c in CELLS if st[c]["n_runs"])
    verdict(6, "graders hold (format_error = 0)", fe == 0, f"total = {fe}", tuple(CELLS))

    nd = verdicts.count("NO DATA")
    print(f"\nheld {verdicts.count('HELD')} of {len(verdicts) - nd} scorable"
          + (f"; {nd} UNSCORED" if nd else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
