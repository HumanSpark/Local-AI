#!/usr/bin/env python3
# File: tools/energy_per_answer.py
# Purpose: Energy per task and per correct answer for a coding-bank run, with a fridge-freezer comparison, from records we already keep.
# Project: sparkbench | Date: 2026-11-25
#
# Overview: Owner 2026-11-25 ("yeah do it ... compare it with a typical fridge"), after the Intelligence per Watt
# scouting (scouting/intelligence-per-watt/REPORT.md). Reads the harness's per-task records (wall_time, passed) for
# one arm, multiplies time by a stated power, and reports energy per task and per correct answer, as chip power and as
# a wall-power range. Power is an INPUT, never inferred: pass the measured chip (package) power for that engine, e.g.
# Halogen 87.0 W on code (E153). Wall draw is chip power plus 10-25 W (claim C-POWER-DRAW-P1). It is an UPPER estimate
# per task: the whole task time is counted at generating power, though the GPU idles while tests and tools run.
# Fridge: a fridge-freezer averages 390 kWh a year (BRE for BEIS, Cold Appliances Field Trial, 2017, Table 6;
# 998 appliances in 766 homes), i.e. 44.5 W around the clock. No GPU, no network.
from __future__ import annotations

import argparse
import glob
import json
import statistics
import sys
from pathlib import Path

FRIDGE_KWH_YEAR = 390.0  # fridge-freezer, BRE/BEIS Cold Appliances Field Trial 2017, Table 6
FRIDGE_W = FRIDGE_KWH_YEAR * 1000 / (365 * 24)  # = 44.5 W average
WALL_EXTRA_W = (10.0, 25.0)  # chip-to-wall overhead range, C-POWER-DRAW-P1 (used only without --wall-w)
# Measured wall power, 2026-11-22 12:47-15:10Z: Tapo P304M socket 4 (benchhost), sparkfleet power log on lanhost,
# 102 readings during a sustained coding run (Hy4-Flash on Strata, E171): median 121.4 W, range 119.2-125.1 W.


def load(pattern: str) -> list[dict]:
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"no records match {pattern!r}; hint: point at results/<exp>/raw/<ARM>/*.json")
    rows = []
    for f in files:
        d = json.loads(Path(f).read_text())
        if d.get("wall_time") is None or "passed" not in d:
            raise ValueError(f"{f} lacks wall_time or passed; hint: only finished harness task records count")
        rows.append(d)
    return rows


def report(label: str, rows: list[dict], chip_w: float, wall_w: float | None = None) -> dict:
    wh = [r["wall_time"] * chip_w / 3600 for r in rows]
    total, solved = sum(wh), sum(1 for r in rows if r["passed"])
    if wall_w:
        wall_lo = wall_hi = wall_w / chip_w
    else:
        wall_lo, wall_hi = ((chip_w + x) / chip_w for x in WALL_EXTRA_W)
    med = statistics.median(wh)
    out = {
        "label": label, "tasks": len(rows), "solved": solved, "chip_w": chip_w,
        "median_wh_per_task_chip": round(med, 1),
        "median_wh_per_task_wall": [round(med * wall_lo, 1), round(med * wall_hi, 1)],
        "wh_per_correct_answer_chip": round(total / solved, 1) if solved else None,
        "fridge_minutes_per_task_wall": [round(med * wall_lo / FRIDGE_W * 60), round(med * wall_hi / FRIDGE_W * 60)],
        "wall_w": wall_w,
        "box_vs_fridge_while_working": ([round(wall_w / FRIDGE_W, 1)] * 2 if wall_w
                                        else [round((chip_w + x) / FRIDGE_W, 1) for x in WALL_EXTRA_W]),
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Energy per task and per correct answer, with a fridge-freezer comparison.",
                                 epilog="example: tools/energy_per_answer.py 'results/e154/raw/H/*.json' --chip-w 87.0 "
                                        "--label 'production, 15 everyday fixes'")
    ap.add_argument("records", help="glob of per-task harness records for ONE arm")
    ap.add_argument("--chip-w", type=float, required=True, help="measured chip (package) power while generating, watts")
    ap.add_argument("--label", required=True, help="plain label for the run")
    ap.add_argument("--wall-w", type=float, default=None,
                    help="measured wall power while working (e.g. 121.4 from the Tapo log); else chip + 10-25 W")
    a = ap.parse_args()
    r = report(a.label, load(a.records), a.chip_w, a.wall_w)
    print(json.dumps(r))
    lo, hi = r["fridge_minutes_per_task_wall"]
    print(f"{a.label}: {r['solved']}/{r['tasks']} solved; a typical task used about {r['median_wh_per_task_wall'][0]}-"
          f"{r['median_wh_per_task_wall'][1]} Wh at the wall, what a fridge-freezer uses in {lo}-{hi} min; while working "
          f"the box draws as much as {r['box_vs_fridge_while_working'][0]}-{r['box_vs_fridge_while_working'][1]} "
          f"fridge-freezers.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
