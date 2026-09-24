#!/usr/bin/env python3
# File: prefill_curve.py
# Purpose: Compare llama-server prefill throughput between runs at MATCHED depth.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: On 2026-08-17 a published claim that a serving-flag change made
# prefill "2.7x faster" was wrong. llama-server's `prompt processing ... tokens
# per second` is a CUMULATIVE AVERAGE that declines as depth grows, so dividing
# one run's rate by another's compares two different depths unless the n_tokens
# happen to match. The correct figure was 2.51x, and only at the deepest point
# both runs reached.
#
# This exists so that comparison is computed rather than eyeballed. It parses
# the progress lines, aligns two runs on shared n_tokens values, and reports the
# ratio as a curve rather than a single number - because the ratio is not
# constant, and a single number hides that it is 0.97x when shallow and 2.51x
# when deep.
#
# It also derives the INSTANTANEOUS rate, which the log does not print. The
# cumulative average understates how bad the tail is: at 210k tokens one run
# showed 66 tok/s cumulative and 27.8 tok/s instantaneous.
#
# Run:
#   python3 tools/prefill_curve.py <serverlog>                  # one curve
#   python3 tools/prefill_curve.py <baseline> <candidate>       # matched-depth compare

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PROGRESS = re.compile(
    r"prompt processing, n_tokens = *(\d+), progress = [\d.]+, "
    r"t = ([\d.]+) s / ([\d.]+) tokens per second"
)


def parse(path: Path) -> list[tuple[int, float, float]]:
    """(n_tokens, elapsed_s, cumulative_tok_s) for each progress line.

    Reads bytes and decodes with replacement: these logs are written with -v and
    routinely contain partial UTF-8 sequences from interleaved output, which
    would otherwise raise part-way through a multi-megabyte file.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. hint: serverlogs are gitignored, so this "
            f"only works on a run whose log is still on disk"
        )
    text = path.read_bytes().decode("utf-8", "replace")
    pts = [(int(n), float(t), float(r)) for n, t, r in PROGRESS.findall(text)]
    if not pts:
        raise ValueError(
            f"no prefill progress lines in {path}. hint: the server must run "
            f"with -v, and the run must have reached prompt processing"
        )
    return pts


def instantaneous(pts: list[tuple[int, float, float]], window: int = 5) -> list[tuple[int, float]]:
    """Rate over the preceding `window` samples, which the log never prints."""
    out = []
    for i in range(window, len(pts)):
        dn = pts[i][0] - pts[i - window][0]
        dt = pts[i][1] - pts[i - window][1]
        if dt > 0:
            out.append((pts[i][0], dn / dt))
    return out


def show_one(path: Path) -> None:
    pts = parse(path)
    inst = dict(instantaneous(pts))
    print(f"\n{path.name}: {len(pts)} samples, "
          f"{pts[0][0]:,} -> {pts[-1][0]:,} tokens in {pts[-1][1]:,.0f}s")
    print(f"{'n_tokens':>10} {'elapsed':>9} {'cumulative':>11} {'instant':>9}")
    step = max(1, len(pts) // 12)
    for n, t, r in pts[::step] + [pts[-1]]:
        i = inst.get(n)
        print(f"{n:>10,} {t:>8.0f}s {r:>10.2f} {(f'{i:>8.1f}' if i else '        -')}")


def compare(base: Path, cand: Path) -> int:
    bp, cp = parse(base), parse(cand)
    bd = {n: (t, r) for n, t, r in bp}
    cd = {n: (t, r) for n, t, r in cp}
    common = sorted(set(bd) & set(cd))
    if not common:
        raise ValueError(
            f"no shared n_tokens between {base.name} and {cand.name}, so no "
            f"like-for-like comparison exists. hint: the runs must share a "
            f"prompt prefix and both reach a common depth"
        )
    print(f"\nbaseline : {base.name}")
    print(f"candidate: {cand.name}")
    print(f"{len(common)} matched depths, {common[0]:,} to {common[-1]:,} tokens\n")
    print(f"{'n_tokens':>10} {'base tok/s':>11} {'cand tok/s':>11} {'ratio':>8} "
          f"{'base sec':>10} {'cand sec':>10}")
    step = max(1, len(common) // 10)
    for n in common[::step] + [common[-1]]:
        bt, br = bd[n]
        ct, cr = cd[n]
        print(f"{n:>10,} {br:>11.2f} {cr:>11.2f} {cr / br:>7.2f}x "
              f"{bt:>9.1f}s {ct:>9.1f}s")
    n = common[-1]
    bt, br = bd[n]
    ct, cr = cd[n]
    print(f"\nAt the deepest matched depth ({n:,} tokens): {cr / br:.2f}x the throughput, "
          f"{bt / ct:.2f}x less wall clock.")
    ratios = [cd[n][1] / bd[n][1] for n in common]
    print(f"Ratio is NOT constant: {min(ratios):.2f}x to {max(ratios):.2f}x across the "
          f"matched range. Quote the curve, or quote a ratio WITH its depth.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compare llama-server prefill throughput at matched depth.",
        epilog="example: python3 tools/prefill_curve.py "
               "results/raw/e48-20260816-l3-n59.serverlog "
               "results/raw/e48b-20260817-l3-n59-ub128.serverlog",
    )
    ap.add_argument("logs", nargs="+", type=Path,
                    help="one serverlog for a curve, or two for a matched-depth compare")
    args = ap.parse_args()
    if len(args.logs) == 1:
        show_one(args.logs[0])
        return 0
    if len(args.logs) == 2:
        return compare(args.logs[0], args.logs[1])
    raise SystemExit("pass one serverlog for a curve, or exactly two to compare")


if __name__ == "__main__":
    sys.exit(main())
