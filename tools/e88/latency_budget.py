#!/usr/bin/env python3
# File: latency_budget.py
# Purpose: E88 - turn the measured curves into an allocated latency budget.
# Project: sparkbench | Date: 2026-08-29
#
# Overview: Fits nothing and invents nothing. Reads the measured context-tax
# points and, for a given payload composition, INTERPOLATES between the two
# bracketing measurements to attribute first-turn wall time to each component.
# Interpolation is linear in prompt tokens against measured TTFT, and any request
# outside the measured range is reported as EXTRAPOLATED rather than silently
# quoted - the measured envelope is stated so a reader can see which it is.
from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys


def load_curve(path: pathlib.Path) -> list[tuple[int, float]]:
    rows = json.loads(path.read_text())
    by_size: dict[int, list[float]] = {}
    for r in rows:
        by_size.setdefault(r["actual_prompt_tokens"], []).append(r["ttft_s"])
    return sorted((n, statistics.median(v)) for n, v in by_size.items())


def ttft_at(curve: list[tuple[int, float]], n: int) -> tuple[float, str]:
    """Median TTFT at n prompt tokens, by linear interpolation between the two
    bracketing MEASURED points. Never silently extrapolates."""
    if not curve:
        raise ValueError(
            "empty context curve. hint: run tools/e88/ctx_tax.py first and pass "
            "its --out file here"
        )
    lo, hi = curve[0][0], curve[-1][0]
    if n <= lo:
        return curve[0][1] * n / lo, "EXTRAPOLATED below measured range"
    if n >= hi:
        return curve[-1][1] * n / hi, "EXTRAPOLATED above measured range"
    for (n0, t0), (n1, t1) in zip(curve, curve[1:]):
        if n0 <= n <= n1:
            frac = (n - n0) / (n1 - n0)
            return t0 + frac * (t1 - t0), "interpolated between measured points"
    raise AssertionError("bracketing failed despite range check")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E88: allocate first-turn latency across payload components.",
        epilog="example: latency_budget.py --curve results/raw/e88/ctx-tax.json",
    )
    ap.add_argument("--curve", type=pathlib.Path, required=True)
    ap.add_argument("--json-out", type=pathlib.Path, default=None)
    args = ap.parse_args()

    curve = load_curve(args.curve)
    print("## Measured context curve (median TTFT)\n")
    print("| prompt tokens | TTFT s |")
    print("|---:|---:|")
    for n, t in curve:
        print(f"| {n:,} | {t:.2f} |")
    print(f"\nmeasured envelope: {curve[0][0]:,} - {curve[-1][0]:,} tokens\n")

    # Measured composition of the real 28-tool Claude Code capture (Phase C).
    components = [
        ("tool schemas (28 tools, client floor)", 19206),
        ("injected CLAUDE.md + rules + memory", 15694),
        ("SessionStart hook (superpowers)", 2873),
        ("system prompt", 1500),
        ("the actual user turn", 2),
    ]
    total = sum(c for _, c in components)
    t_total, how = ttft_at(curve, total)

    print("## First-turn latency budget, Claude Code at its floor\n")
    print("| component | tokens | share | marginal TTFT cost s |")
    print("|---|---:|---:|---:|")
    running = 0
    rows = []
    for label, n in components:
        t_before, _ = ttft_at(curve, running) if running else (0.0, "")
        running += n
        t_after, _ = ttft_at(curve, running)
        cost = t_after - t_before
        rows.append(
            {"component": label, "tokens": n, "marginal_ttft_s": round(cost, 2)}
        )
        print(f"| {label} | {n:,} | {100 * n / total:.1f}% | {cost:.1f} |")
    print(f"| **total** | **{total:,}** | **100%** | **{t_total:.1f}** |")
    print(f"\nattribution method: {how}")

    # What a light client costs at the same measured curve (F105: aider = 761).
    t_aider, how_a = ttft_at(curve, 761)
    print("\n## Client comparison at the SAME measured curve\n")
    print("| client | first-turn prompt tokens | TTFT s |")
    print("|---|---:|---:|")
    print(
        f"| Claude Code (28-tool floor, measured capture) | {total:,} | {t_total:.1f} |"
    )
    print(f"| aider (F105 banked) | 761 | {t_aider:.2f} |")
    print(
        f"\nratio: **{total / 761:.0f}x the prompt, {t_total / t_aider:.0f}x the wait**"
    )
    print(f"aider point is {how_a}")

    if args.json_out:
        args.json_out.write_text(
            json.dumps(
                {
                    "curve": [{"tokens": n, "ttft_s": t} for n, t in curve],
                    "components": rows,
                    "total_tokens": total,
                    "total_ttft_s": round(t_total, 2),
                    "aider_tokens": 761,
                    "aider_ttft_s": round(t_aider, 3),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
