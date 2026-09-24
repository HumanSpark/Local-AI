#!/usr/bin/env python3
# File: analyse_e32.py
# Purpose: Summarise the E32 concurrency sweep JSONs into a comparison table.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: Reads results/raw/e32-<stamp>-<arm>-np<N>.json and prints scaling
# per arm relative to that arm's own slots=1. Reports BOTH aggregate_gen_tps
# (total delivered tokens / wall, so it charges TTFT and queueing) and
# mean_stream_gen_tps x streams (steady-state generation capacity). The two
# answer different questions and quoting only one is how a concurrency claim
# gets overstated. Carries the under_sampled flag through to the table
# instead of dropping it - a weakly-sampled point must not read as solid.

from __future__ import annotations

import json
import sys
from pathlib import Path

RAW = Path("/home/agent-spark/sparkbench/results/raw")


def main() -> int:
    stamp = sys.argv[1] if len(sys.argv) > 1 else None
    files = sorted(RAW.glob(f"e32-{stamp or '*'}-*-np*.json"))
    if not files:
        print("no E32 result files found", file=sys.stderr)
        return 1
    arms: dict[str, dict[int, dict]] = {}
    for f in files:
        d = json.load(open(f))
        s = d["summary"]
        arm = d["label"].replace("e32-", "").rsplit("-np", 1)[0]
        arms.setdefault(arm, {})[s["streams"]] = s

    for arm, by_slots in arms.items():
        base = by_slots.get(1)
        print(f"\n=== {arm} ===")
        print(f"{'slots':>5} {'agg t/s':>9} {'x(agg)':>7} {'per-stream':>11} "
              f"{'capacity':>9} {'x(cap)':>7} {'ttft p50 ms':>12} {'ok':>4} {'sampling':>10}")
        for slots in sorted(by_slots):
            s = by_slots[slots]
            agg = s["aggregate_gen_tps"]
            per = s["mean_stream_gen_tps"]
            cap = round(per * slots, 2)
            xa = f"{agg / base['aggregate_gen_tps']:.2f}x" if base else "-"
            xc = f"{cap / (base['mean_stream_gen_tps'] * 1):.2f}x" if base else "-"
            flag = "UNDER" if s.get("under_sampled") else "ok"
            print(f"{slots:>5} {agg:>9} {xa:>7} {per:>11} {cap:>9} {xc:>7} "
                  f"{s['ttft_ms_p50']:>12} {s['requests_ok']:>4} {flag:>10}")
    print("\nagg = delivered tokens / wall (charges TTFT + queueing)")
    print("capacity = mean per-stream rate x streams (steady-state generation)")
    print("UNDER = harness flagged under_sampled; too few requests per stream to trust")
    return 0


if __name__ == "__main__":
    sys.exit(main())
