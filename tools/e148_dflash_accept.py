#!/usr/bin/env python3
# File: tools/e148_dflash_accept.py
# Purpose: Summarise Atlas's DFlash acceptance from an arm's server log - overall and by 4K context bucket.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: Atlas logs one line per DFlash verify step, "DFLASH K=γ verify: γ=15 accepted=a/g (p%) seq_len=n".
# This reads those lines (ANSI stripped), and prints the step count, accepted tokens, mean accepted per step,
# the histogram of accepted counts, and the mean accepted per step by 4,096-token seq_len bucket. It is the
# source of the acceptance table in results/e146-results.md's E148 section. Only the logged steps are counted;
# it does not claim every step is logged.
from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

LINE = re.compile(r"accepted=(\d+)/(\d+) \((\d+)%\) seq_len=(\d+)")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="DFlash acceptance from an Atlas server log.",
        epilog="example:\n  tools/e148_dflash_accept.py results/raw/e148/M3p/server.serverlog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("serverlog", type=Path)
    args = ap.parse_args()
    text = ANSI.sub("", args.serverlog.read_text(errors="replace"))
    steps = [tuple(map(int, m.groups())) for m in LINE.finditer(text)]
    if not steps:
        raise SystemExit(
            f"no DFlash verify lines in {args.serverlog}. hint: the arm did not run DFlash, or the log format changed"
        )
    acc = [a for a, _g, _p, _s in steps]
    n = len(acc)
    print(
        f"verify steps logged {n}, accepted tokens {sum(acc)}, mean accepted/step {sum(acc) / n:.3f}"
    )
    print("accepted histogram", sorted(collections.Counter(acc).items()))
    byb: dict[int, list[int]] = collections.defaultdict(lambda: [0, 0])
    for a, _g, _p, s in steps:
        b = s // 4096 * 4096
        byb[b][0] += 1
        byb[b][1] += a
    for b in sorted(byb):
        c, a = byb[b]
        print(f"seq_len {b:>6}-{b + 4095:<6} steps {c:>6} accepted/step {a / c:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
