#!/usr/bin/env python3
# File: tools/score_e154.py
# Purpose: Score E154 arms from results/e154/raw/<arm>/<task>.json against the pre-registered fields and P1-P7.
# Project: sparkbench | Date: 2026-11-04
#
# Overview: Loads every task file per arm (a task file that is missing counts as NOT RUN, never as a fail), computes the
# prereg's scored fields - pass_count, wall_median_s (over all tasks run), cost_usd (sum of usage.cost_usd, amendment 1) -
# plus reported-only fields (turns, malformed calls, statuses, length stops), prints a per-arm table and a per-task matrix,
# and evaluates P1-P7 exactly as worded in results/e154-prereg.md. A prediction whose arms did not all run is UNSCORED.
# --json writes the same numbers for the results file.

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ARMS = ["S", "H", "Q", "QN", "T27", "TL"]


def load_bank(bank: Path) -> list[str]:
    return [json.loads(line)["id"] for line in bank.read_text().splitlines() if line.strip()]


def load_arm(raw: Path, arm: str, task_ids: list[str]) -> dict[str, dict] | None:
    d = raw / arm
    if not d.is_dir():
        return None
    out = {}
    for t in task_ids:
        f = d / f"{t}.json"
        if f.exists() and f.stat().st_size:
            out[t] = json.loads(f.read_text())
    return out


def summarise(tasks: dict[str, dict], n_bank: int) -> dict:
    walls = [r["wall_time"] for r in tasks.values()]
    # Arms whose transcripts trip the pre-commit secret gate are stored stripped (full copy under
    # results/e154/transcripts/, gitignored) with length_stops precomputed; S keeps its transcript inline.
    length_stops = sum(
        r["length_stops"] if "transcript" not in r
        else sum(1 for e in r["transcript"] if e.get("finish_reason") == "length")
        for r in tasks.values()
    )
    statuses: dict[str, int] = {}
    for r in tasks.values():
        statuses[r["status"]] = statuses.get(r["status"], 0) + 1
    return {
        "run": len(tasks),
        "not_run": n_bank - len(tasks),
        "pass_count": sum(1 for r in tasks.values() if r["status"] == "pass"),
        "wall_median_s": round(statistics.median(walls), 1) if walls else None,
        "cost_usd": round(sum(r["usage"]["cost_usd"] for r in tasks.values()), 4),
        "turns_median": statistics.median([r["turns"] for r in tasks.values()]) if tasks else None,
        "malformed_calls": sum(r.get("malformed_calls", 0) for r in tasks.values()),
        "length_stops": length_stops,
        "statuses": statuses,
    }


def predictions(s: dict[str, dict]) -> list[tuple[str, str, str]]:
    """(id, verdict, evidence). Verdict HELD / FALSIFIED / UNSCORED (an arm it names did not complete the bank)."""

    def full(*arms: str) -> bool:
        return all(a in s and s[a]["not_run"] == 0 for a in arms)

    out = []

    def add(pid: str, arms: tuple[str, ...], ok_fn, evidence_fn) -> None:
        if not full(*arms):
            out.append((pid, "UNSCORED", f"needs complete arms {', '.join(arms)}"))
        else:
            out.append((pid, "HELD" if ok_fn() else "FALSIFIED", evidence_fn()))

    add("P1", ("S",), lambda: s["S"]["pass_count"] >= 11, lambda: f"S.pass_count={s['S']['pass_count']} (>= 11)")
    locals_full = [a for a in ("H", "T27", "TL") if full(a)]
    if full("S") and locals_full:
        best = max(locals_full, key=lambda a: s[a]["pass_count"])
        note = "" if len(locals_full) == 3 else f" (only {', '.join(locals_full)} complete)"
        ok = s[best]["pass_count"] >= s["S"]["pass_count"] - 3
        out.append(
            ("P2", "HELD" if ok else "FALSIFIED",
             f"best local {best}={s[best]['pass_count']} vs S-3={s['S']['pass_count'] - 3}{note}")
        )
    else:
        out.append(("P2", "UNSCORED", "needs S and at least one of H, T27, TL complete"))
    add("P3", ("Q", "H"), lambda: s["Q"]["pass_count"] < s["H"]["pass_count"],
        lambda: f"Q={s['Q']['pass_count']} < H={s['H']['pass_count']}")
    add("P4", ("T27", "Q"), lambda: s["T27"]["pass_count"] >= s["Q"]["pass_count"],
        lambda: f"T27={s['T27']['pass_count']} >= Q={s['Q']['pass_count']}")
    add("P5", ("H", "S"), lambda: s["H"]["wall_median_s"] <= 2 * s["S"]["wall_median_s"],
        lambda: f"H.wall_median_s={s['H']['wall_median_s']} vs 2xS={2 * s['S']['wall_median_s']}")
    add("P6", ("S",), lambda: s["S"]["cost_usd"] <= 10.0, lambda: f"S.cost_usd={s['S']['cost_usd']} (<= 10.00)")
    add("P8", ("QN", "Q"), lambda: s["QN"]["pass_count"] >= s["Q"]["pass_count"],
        lambda: f"QN={s['QN']['pass_count']} >= Q={s['Q']['pass_count']}")
    matches = [
        a for a in ("H", "Q", "QN", "T27", "TL")
        if full(a, "S")
        and s[a]["pass_count"] >= s["S"]["pass_count"] - 2
        and s[a]["wall_median_s"] <= 2 * s["S"]["wall_median_s"]
    ]
    if full("S") and any(full(a) for a in ("H", "Q", "QN", "T27", "TL")):
        out.append(("P7", "HELD" if matches else "FALSIFIED", f"arms matching Sonnet: {matches or 'none'}"))
    else:
        out.append(("P7", "UNSCORED", "needs S and at least one local arm complete"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score E154 arms against the pre-registered fields and P1-P7.",
        epilog="Example: tools/score_e154.py --json results/e154/score.json",
    )
    ap.add_argument("--raw", default="results/e154/raw")
    ap.add_argument("--bank", default="results/e154/bank.jsonl")
    ap.add_argument("--json", default=None, help="also write the scores as JSON")
    args = ap.parse_args()

    task_ids = load_bank(Path(args.bank))
    per_task: dict[str, dict[str, dict]] = {}
    summary: dict[str, dict] = {}
    for arm in ARMS:
        tasks = load_arm(Path(args.raw), arm, task_ids)
        if tasks is None:
            continue
        per_task[arm] = tasks
        summary[arm] = summarise(tasks, len(task_ids))

    print(f"{'arm':4} {'run':>4} {'pass':>5} {'wall_med_s':>10} {'turns_med':>9} {'cost_usd':>9} {'malformed':>9} {'length':>6}  statuses")
    for arm, x in summary.items():
        print(
            f"{arm:4} {x['run']:>4} {x['pass_count']:>5} {x['wall_median_s']!s:>10} {x['turns_median']!s:>9} "
            f"{x['cost_usd']:>9} {x['malformed_calls']:>9} {x['length_stops']:>6}  {x['statuses']}"
        )
    print()
    print(f"{'task':36} " + " ".join(f"{a:>5}" for a in per_task))
    for t in task_ids:
        cells = []
        for a in per_task:
            r = per_task[a].get(t)
            cells.append(f"{'-' if r is None else ('P' if r['status'] == 'pass' else r['status'][:5]):>5}")
        print(f"{t:36} " + " ".join(cells))
    print()
    preds = predictions(summary)
    for pid, verdict, ev in preds:
        print(f"{pid}: {verdict:9} {ev}")
    if args.json:
        Path(args.json).write_text(
            json.dumps({"summary": summary, "predictions": [dict(zip(("id", "verdict", "evidence"), p)) for p in preds]}, indent=1)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
