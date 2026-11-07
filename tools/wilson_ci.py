#!/usr/bin/env python3
# File: wilson_ci.py
# Purpose: Calculate Wilson score confidence intervals for proportions (95%, two-tailed)
# Project: sparkbench | Date: 2026-07-11
#
# Overview: Given k passes out of n trials, compute 95% confidence interval
# using Wilson score interval (more accurate than normal approximation,
# especially for extreme proportions like 0/n or n/n).
# Output: "p% (CI lower-upper)" format for report tables.
#
#   v1  2026-07-11  Wilson for 0 < k < n, and a DIFFERENT estimator for k == 0
#                   and k == n: the exact one-sided bound 1 - alpha**(1/n).
#                   The function was named wilson_ci_95 and documented
#                   "two-tailed", so a zero-count bound read as a Wilson bound
#                   and was not one. Two estimators for one quantity is the
#                   like-for-like failure, and it produced three inconsistent
#                   published figures - see the CLOSE-OUT CORRECTION in
#                   results/experiments.md (2026-08-20).
#   v2  2026-08-20  Wilson everywhere, including k == 0 and k == n, so the name
#                   describes the value. The exact one-sided bound remains
#                   available as exact_upper_bound_one_sided(), named for what
#                   it is, and is the RIGHT tool when a one-sided ceiling on a
#                   never-observed fault is what is wanted - it is simply not
#                   interchangeable with a two-sided interval.

from __future__ import annotations

import argparse
import math
import sys


def wilson_ci_95(passed: int, total: int) -> tuple[float, float]:
    """
    Calculate Wilson score 95% confidence interval for a proportion.

    Args:
        passed: number of successes
        total: number of trials

    Returns:
        (lower_bound, upper_bound) as proportions in [0, 1]

    Raises:
        ValueError: if passed < 0, total <= 0, or passed > total
    """
    if not isinstance(passed, int) or not isinstance(total, int):
        raise TypeError("passed and total must be integers")

    if passed < 0:
        raise ValueError(f"passed must be >= 0, got {passed}")

    if total <= 0:
        raise ValueError(f"total must be > 0, got {total}")

    if passed > total:
        raise ValueError(f"passed ({passed}) cannot exceed total ({total})")

    # Edge cases
    if total == 0:
        raise ValueError("total must be > 0")

    # v2: no special case. The Wilson formula is well behaved at both extremes -
    # at p_hat = 0 it gives exactly (0, z^2/(n + z^2)) - and special-casing them
    # with a different estimator is what made a zero-count "Wilson" bound not a
    # Wilson bound. See the version note in the header.
    # Wilson score interval formula (Agresti & Coull, 1998)
    z = 1.96  # 95% confidence, two-tailed (0.025 in each tail)

    p_hat = passed / total
    n = total

    denominator = 1 + (z**2) / n
    center = (p_hat + (z**2) / (2 * n)) / denominator
    margin = (
        z * math.sqrt((p_hat * (1 - p_hat) / n) + (z**2 / (4 * n**2))) / denominator
    )

    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)

    return lower, upper


ESTIMATOR_VERSION = "wilson-v2-2026-08-20"


def exact_upper_bound_one_sided(total: int, alpha: float = 0.05) -> float:
    """The exact one-sided upper confidence bound when ZERO events were observed.

    `1 - alpha**(1/n)` - the Clopper-Pearson one-sided bound, and the "rule of
    three" approximation's exact form. It is the right answer to "we saw no
    failures in n trials; how bad could the rate still be?", and it is NOT a
    Wilson interval: for 0 of 125 it gives 2.37% where two-sided Wilson gives
    2.98%. Quote one or the other, say which, and never mix them across
    experiments that are compared with each other.
    """
    if total <= 0:
        raise ValueError(
            f"total must be > 0, got {total}; "
            f"hint: a bound on a rate needs trials to bound it with"
        )
    if not 0 < alpha < 1:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")
    return 1 - alpha ** (1 / total)


def format_ci(passed: int, total: int, as_percent: bool = True) -> str:
    """
    Format as "p% (CI lower-upper)" or "p (CI lower-upper)".

    Args:
        passed: number of successes
        total: number of trials
        as_percent: if True, format as percentages; else as proportions

    Returns:
        formatted string like "84.9% (CI 82.7-86.8)"
    """
    if total == 0:
        raise ValueError("total must be > 0")

    p = passed / total
    lower, upper = wilson_ci_95(passed, total)

    if as_percent:
        p_str = f"{100 * p:.1f}%"
        ci_str = f"CI {100 * lower:.1f}-{100 * upper:.1f}"
    else:
        p_str = f"{p:.4f}"
        ci_str = f"CI {lower:.4f}-{upper:.4f}"

    return f"{p_str} ({ci_str})"


def main():
    parser = argparse.ArgumentParser(
        description="Calculate Wilson 95% confidence intervals for proportions",
        epilog="""
Examples:
  %(prog)s 25 30        # 25/30 with CI
  %(prog)s 0 10         # 0/10 (all failed)
  %(prog)s 10 10        # 10/10 (all passed)
  %(prog)s --batch 25 30 14 24 28 30  # Multiple: 25/30, 14/24, 28/30
        """,
    )
    parser.add_argument(
        "passed",
        nargs="?",
        type=int,
        help="Number of passed tests",
    )
    parser.add_argument(
        "total",
        nargs="?",
        type=int,
        help="Total number of tests",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Batch mode: all arguments are passed/total pairs",
    )
    parser.add_argument(
        "--proportion",
        action="store_true",
        help="Output as decimal proportion instead of percentage",
    )
    args = parser.parse_args()

    if args.batch:
        # Parse all args as passed/total pairs
        all_args = sys.argv[2:]  # skip script name and --batch
        if len(all_args) % 2 != 0:
            print(
                "Error: batch mode requires even number of arguments (passed/total pairs)",
                file=sys.stderr,
            )
            sys.exit(1)

        for i in range(0, len(all_args), 2):
            try:
                passed = int(all_args[i])
                total = int(all_args[i + 1])
                result = format_ci(passed, total, as_percent=not args.proportion)
                print(result)
            except ValueError as e:
                print(
                    f"Error parsing {all_args[i]}/{all_args[i + 1]}: {e}",
                    file=sys.stderr,
                )
                sys.exit(1)
    else:
        if args.passed is None or args.total is None:
            parser.print_help()
            sys.exit(1)

        try:
            result = format_ci(args.passed, args.total, as_percent=not args.proportion)
            print(result)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
