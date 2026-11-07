#!/usr/bin/env python3
# File: analyse_thinking_matrix.py
# Purpose: Resolve the E42 thinking-level matrix against the decision rule declared before the run.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: E42 sweeps four reasoning levels (off, low, medium, xhigh) across
# three task types (knowledge, writing, coding). This reads the result JSONs
# and applies the rule registered in E42 AMENDMENT 2, which was written before
# any data existed:
#
#   For each task type, the RECOMMENDED level is the one with the lowest
#   median per-item latency whose score is within 1 item of the best score
#   achieved by any level on that task type. Ties go to the lower level.
#
# The 1-item band is a DESIGNED tolerance declared up front, not one invented
# after seeing a gap. Local runs at temperature 0 are deterministic (F59), so a
# 1-item difference is real; the band expresses a routing judgement, that one
# item is not worth a multiple of the wall time. Two or more items disqualifies
# a level outright.
#
# It also reports the two operating modes the owner asked for:
#   BATCH       the best score any level reaches, latency disregarded
#   INTERACTIVE the best score reachable with median latency under 30s, and
#               separately under 10s
#
# Nothing here decides anything the registration did not already decide. If
# the rule and my reading of the table disagree, the rule wins.

from __future__ import annotations

import json
import sys
from pathlib import Path

LEVELS = ["off", "low", "medium", "xhigh"]
ROWS = {
    "knowledge": "e42-20260815-know-{lvl}.json",
    "writing": "e42-20260815-write-{lvl}.json",
    "coding": "e42-20260815-code-{lvl}.json",
}
RAW = Path(__file__).resolve().parent.parent / "results" / "raw"

# Each task type reports its score under a different key, because they measure
# different things. Named explicitly rather than guessed - F65's lesson is that
# a pre-registration naming a CONCEPT instead of a FIELD is not falsifiable,
# and the same applies to the code that resolves it.
SCORE_FIELD = {
    "knowledge": ("correct", "total"),
    "writing": ("correct", "total"),
    "coding": ("passed", "total"),
}


def load(row: str, lvl: str) -> dict | None:
    p = RAW / ROWS[row].format(lvl=lvl)
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    sk, tk = SCORE_FIELD[row]
    if sk not in d:
        raise KeyError(
            f"{p.name} has no {sk!r} field. hint: SCORE_FIELD names the field per task "
            f"type; fix it there rather than guessing at the call site"
        )
    lat = d.get("latency") or {}
    return {
        "level": lvl, "score": d[sk], "total": d[tk],
        "wall_s": d.get("wall_s"),
        "median_s": lat.get("median_s"), "p95_s": lat.get("p95_s"),
        "under_10s": lat.get("under_10s"), "under_30s": lat.get("under_30s"),
        "n": lat.get("n"),
        "by": d.get("by_category") or d.get("by_tier") or d.get("by_kind") or {},
        "outcomes": d.get("outcome_counts", {}),
    }


def recommend(cells: list[dict]) -> tuple[dict | None, str]:
    """The rule from E42 AMENDMENT 2, applied literally."""
    scored = [c for c in cells if c["median_s"] is not None]
    if not scored:
        return None, "no cell has latency data"
    best = max(c["score"] for c in scored)
    eligible = [c for c in scored if c["score"] >= best - 1]
    eligible.sort(key=lambda c: (c["median_s"], LEVELS.index(c["level"])))
    pick = eligible[0]
    return pick, (f"best={best}, within-1 band admits "
                  f"{[c['level'] for c in eligible]}, lowest median latency wins")


def main() -> int:
    any_data = False
    print("E42 - thinking-level matrix, resolved against the rule registered "
          "in AMENDMENT 2\n")
    for row in ROWS:
        cells = [c for c in (load(row, lvl) for lvl in LEVELS) if c]
        if not cells:
            print(f"{row.upper():10s}  (no results yet)\n")
            continue
        any_data = True
        print(f"{row.upper()}")
        print(f"  {'level':7s} {'score':>8s} {'wall':>9s} {'median':>9s} "
              f"{'p95':>8s} {'<10s':>6s} {'<30s':>6s}")
        for c in cells:
            print(f"  {c['level']:7s} {str(c['score']) + '/' + str(c['total']):>8s} "
                  f"{c['wall_s']:>8.1f}s {str(c['median_s']):>8s}s "
                  f"{str(c['p95_s']):>7s}s {str(c['under_10s']):>6s} "
                  f"{str(c['under_30s']):>6s}")

        batch = max(cells, key=lambda c: (c["score"], -(c["median_s"] or 1e9)))
        inter30 = [c for c in cells if (c["median_s"] or 1e9) < 30]
        inter10 = [c for c in cells if (c["median_s"] or 1e9) < 10]
        pick, why = recommend(cells)
        print(f"  BATCH        best {batch['score']}/{batch['total']} at {batch['level']}")
        for bar, group in ((30, inter30), (10, inter10)):
            if group:
                b = max(group, key=lambda c: c["score"])
                print(f"  INTERACTIVE  best {b['score']}/{b['total']} at {b['level']} "
                      f"(median {b['median_s']}s, under {bar}s)")
            else:
                print(f"  INTERACTIVE  no level has median latency under {bar}s")
        if pick:
            print(f"  RECOMMENDED  {pick['level']}  ({why})")
        # The writing row's "clean" count requires passing EVERY dimension at
        # once, so a draft that invents nothing, keeps every unfavourable
        # finding and breaks no style rule still scores zero if it runs six
        # words long. Reporting only the total would say "2/7" about a set of
        # drafts whose sole defect is length, which inverts the finding.
        if row == "writing":
            print("  dimensions (a 'clean' draft passes all of them at once):")
            for c in cells:
                oc = c["outcomes"]
                print(f"    {c['level']:7s} clean {c['score']}/{c['total']}  "
                      f"fabricated {oc.get('fabricated', 0)}  "
                      f"dropped_negative {oc.get('dropped_negative', 0)}  "
                      f"style {oc.get('style_violation', 0)}  "
                      f"length {oc.get('length_violation', 0)}  "
                      f"truncated {oc.get('truncated', 0)}")

        # Where the score went, which is the part a total hides.
        for c in cells:
            if c["by"]:
                short = {k: f"{v['correct']}/{v['total']}" if "correct" in v
                         else f"{v.get('pass')}/{v['total']}" for k, v in c["by"].items()}
                print(f"    {c['level']:7s} {short}")
        print()

    if not any_data:
        print("No E42 results on disk yet.")
        return 1
    print("Reminder: the writing row's score counts fully-clean drafts only and "
          "says nothing about prose quality; the judgement rules the style canon "
          "lists as ungated are not measured here.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
