#!/usr/bin/env python3
# File: tools/score_capped_atlas_arm.py
# Purpose: Server-side scoring for any Atlas DFlash arm (E150 M5, E151 M6, later ones) against M3p and M1p on the same first N turns, with acceptance split by first turn against later turns.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: Reuses score_e149's parsers (per-turn "Done" lines, verify lines). Prints the server-side comparison E149 used,
# the acceptance table by 4K bucket, and the same table split by first-turn-of-conversation against later turns using the
# turn order of E148 M3p's per-turn.json (the harness issues the same 206 turns in the same order for every arm). Verdicts
# are left to the experiment's results file; this prints the fields the preregs name.
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_e149 import RAW, acceptance, clean, server_turns  # noqa: E402

VERIFY = re.compile(r"accepted=(\d+)/(\d+) \(\d+%\) seq_len=(\d+)")
DONE = re.compile(r"mtp_accept_debug: Done: (\d+) tokens")


def steps_by_turn(serverlog: Path) -> list[list[tuple[int, int]]]:
    turns: list[list[tuple[int, int]]] = []
    cur: list[tuple[int, int]] = []
    for line in clean(serverlog).splitlines():
        m = VERIFY.search(line)
        if m:
            cur.append((int(m.group(1)), int(m.group(3))))
            continue
        if DONE.search(line):
            turns.append(cur)
            cur = []
    return turns


def split_table(serverlog: Path, limit: int | None = None, label: str = "") -> None:
    order = [
        (r["conversation_id"], r["turn"])
        for r in json.loads((RAW / "e148" / "M3p" / "per-turn.json").read_text())
    ]
    turns = steps_by_turn(serverlog)
    if limit is not None:
        turns = turns[
            :limit
        ]  # the comparator restricted to the same first N turns as the capped arm
    by: dict[tuple[str, int], list[int]] = collections.defaultdict(lambda: [0, 0])
    for (_conv, turn), steps in zip(order, turns):
        key = "first" if turn == 1 else "later"
        for a, s in steps:
            b = min(s // 4096, 3)
            by[(key, b)][0] += 1
            by[(key, b)][1] += a
    print(
        f"acceptance by first-turn against later turns{label} ({len(turns)} turns matched to E148's order):"
    )
    for k in sorted(by):
        c, a = by[k]
        hi = "12288+" if k[1] == 3 else f"{k[1] * 4096}-{k[1] * 4096 + 4095}"
        print(
            f"  {k[0]:5s} turns, context {hi:>12}: steps {c:>5}, accepted/step {a / c:.3f}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Server-side scoring for a capped Atlas DFlash arm.",
        epilog="example:\n  tools/score_capped_atlas_arm.py results/raw/e150/M5",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("arm_dir", type=Path)
    args = ap.parse_args()
    log = args.arm_dir / "server.serverlog"
    t = server_turns(log)
    n = len(t)
    print(
        f"=== {args.arm_dir.name}: {n} turns; server-side comparison on the same first {n} turns ==="
    )

    def line(name: str, r: list[dict]) -> None:
        print(
            f"  {name}: tok_step {sum(x['tok_step'] for x in r) / n:.3f}, p1 {sum(x['p1'] for x in r) / n:.3f}, "
            f"decode {sum(x['decode_tps'] for x in r) / n:.2f} tok/s, TTFT {sum(x['ttft_ms'] for x in r) / n:.0f} ms, "
            f"est {sum(x['est_ms'] for x in r) / n:.0f} ms/turn"
        )

    line(args.arm_dir.name, t)
    for name, p in (("M3p", RAW / "e148" / "M3p"), ("M1p", RAW / "e146" / "M1p")):
        c = server_turns(p / "server.serverlog")[:n]
        line(name, c)
        same = sum(1 for a, b in zip(t, c) if a["tokens"] == b["tokens"])
        print(
            f"    {args.arm_dir.name}/{name} est ratio {sum(x['est_ms'] for x in t) / sum(x['est_ms'] for x in c):.3f}; "
            f"identical output token counts {same}/{n}"
        )
    acc_all, acc_long, nsteps = acceptance(log)
    print(
        f"acceptance: {acc_all:.3f} tokens per step over {nsteps} logged steps; 12,288-28,671 bucket {acc_long:.3f}"
    )
    split_table(log)
    split_table(
        RAW / "e148" / "M3p" / "server.serverlog",
        limit=n,
        label=", M3p on the same first turns",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
