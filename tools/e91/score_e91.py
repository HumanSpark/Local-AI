#!/usr/bin/env python3
# File: score_e91.py
# Purpose: Score E91 against its pre-registered predictions, and REFUSE a verdict if the rulers moved.
# Project: sparkbench | Date: 2026-08-31
#
# Overview: Reads results/raw/e91/*.json and scores predictions 1-6 from
# results/e91-prereg.md by the FIELD each one named. The important behaviour is
# the gate: predictions 3 and 4 are ruler checks on the two control arms, and if
# either fails this scorer prints NO VERDICT for the challenger rather than
# reporting arm C against frozen F74/F80 figures measured on a different build.
# A scorer that reports a comparison it cannot justify is the "vacuous success"
# failure class - a result that looks like a measurement and is not one.

from __future__ import annotations

import json
import sys
from pathlib import Path

RAW = Path("/home/agent-spark/sparkbench/results/raw/e91")

# F80's WALKED-period categories: the eight items that require counting across a
# calendar, against seven static-analysis ones. `fee_basis` belongs here and was
# missing from the first version of this file, which would have scored every arm
# out of 7 and compared it against F80's "/8" figures - two rulers, silently.
#
# Confirmed arithmetically against arm A rather than assumed: the workhorse
# scored 0 across these eight and 6 of the seven static items, for 6/15 total,
# which reproduces F80's published 0/8, 6/7 and 6/15 exactly.
COUNTED = ("statutory_period", "breach_clock", "interest_calc", "notice_period",
           "fee_basis")


def load(label: str, tier: str) -> dict | None:
    p = RAW / f"e91-{label}-{tier}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def counted_score(d: dict) -> tuple[int, int]:
    """Summed correct/total over the counted-period categories. Absent
    categories contribute nothing rather than raising - an arm that died
    part-way should read as a low score with a visible total, not a crash."""
    bc = d.get("by_category", {})
    c = sum(bc.get(k, {}).get("correct", 0) for k in COUNTED)
    t = sum(bc.get(k, {}).get("total", 0) for k in COUNTED)
    return c, t


def empty_answers(d: dict) -> int:
    return sum(1 for r in d.get("results", []) if not (r.get("answer") or r.get("content") or "").strip())


def main() -> int:
    arms = {
        "A": ("A-workhorse", "workhorse Qwen3-30B-A3B"),
        "B": ("B-qwen38-low", "Qwen3.8-27B @ low"),
        "C": ("C-flashnext-low", "Flash-Next @ low"),
        "D": ("D-flashnext-medium", "Flash-Next @ medium"),
    }

    print("=== E91: arms present ===")
    data: dict[str, dict[str, dict]] = {}
    for key, (label, desc) in arms.items():
        data[key] = {}
        for tier in ("l4", "l3"):
            d = load(label, tier)
            if d:
                data[key][tier] = d
                print(f"  {key} {desc:28s} {tier}: {d['correct']}/{d['total']} correct, "
                      f"over_claims {d.get('over_claims')}, wall {d.get('wall_s')}s")
            else:
                print(f"  {key} {desc:28s} {tier}: ABSENT")

    print("\n=== ruler checks (predictions 3 and 4) - these gate everything ===")
    gate_ok = True

    a4 = data.get("A", {}).get("l4")
    if a4:
        c, t = counted_score(a4)
        p3 = c <= 1
        gate_ok &= p3
        print(f"  P3 workhorse counted-period {c}/{t} (F80 measured 0/8; band 0-1): "
              f"{'HOLDS' if p3 else 'FALSIFIED'}")
    else:
        gate_ok = False
        print("  P3 UNSCORED - arm A l4 absent")

    b4 = data.get("B", {}).get("l4")
    if b4:
        c, t = counted_score(b4)
        p4 = 6 <= c <= 8
        gate_ok &= p4
        print(f"  P4 Qwen3.8-27B counted-period {c}/{t} (F80 measured 7/8; band 6-8): "
              f"{'HOLDS' if p4 else 'FALSIFIED'}")
    else:
        gate_ok = False
        print("  P4 UNSCORED - arm B l4 absent")

    print("\n=== challenger (predictions 1, 2, 5, 6) ===")
    c4 = data.get("C", {}).get("l4")
    c3 = data.get("C", {}).get("l3")

    if c4:
        c, t = counted_score(c4)
        print(f"  P1 Flash-Next counted-period {c}/{t} (>= 7 to move the guide): "
              f"{'HOLDS' if c >= 7 else 'FALSIFIED'}")
        print(f"  P5 over_claims {c4.get('over_claims')} (<= 1): "
              f"{'HOLDS' if (c4.get('over_claims') or 0) <= 1 else 'FALSIFIED'}")
        empties = empty_answers(c4)
        fmt = c4.get("outcome_counts", {}).get("format_error", 0)
        print(f"  P6 empty answers {empties}, format_error {fmt} (both 0): "
              f"{'HOLDS' if empties == 0 and fmt == 0 else 'FALSIFIED'}")
    else:
        print("  P1/P5/P6 UNSCORED - arm C l4 absent")

    if c3:
        print(f"  P2 Flash-Next l3 {c3['correct']}/{c3['total']} (>= 10): "
              f"{'HOLDS' if c3['correct'] >= 10 else 'FALSIFIED'}")
    else:
        print("  P2 UNSCORED - arm C l3 absent")

    print("\n=== VERDICT ===")
    if not gate_ok:
        print("  NO VERDICT. A ruler check failed or could not be scored, so the build")
        print("  moved the instrument and NO Flash-Next figure here may be compared")
        print("  against F74 or F80. Report the ruler, not the challenger.")
        return 1

    if not (c4 and c3):
        print("  NO VERDICT - controls are sound but the challenger did not complete.")
        return 1

    cc, ct = counted_score(c4)
    ac, _ = counted_score(a4)
    bc_, _ = counted_score(b4)
    print(f"  Controls reproduced (workhorse {ac}/8, Qwen3.8-27B {bc_}/8), so the")
    print(f"  comparison is same-build and legitimate.")
    if cc >= 7 and c3["correct"] >= 10:
        print(f"  Flash-Next MATCHES OR BEATS the incumbent ({cc}/8 counted, "
              f"{c3['correct']}/{c3['total']} l3).")
        print("  -> the routing guide may need a Flash-Next row. Cost: the whole box.")
    elif cc <= ac:
        print(f"  Flash-Next ({cc}/8) is at or below the WORKHORSE ({ac}/8) on its own")
        print("  strongest axis. Second falsifier fired: not a production candidate here.")
    else:
        print(f"  Flash-Next ({cc}/8 counted, {c3['correct']}/{c3['total']} l3) is between")
        print(f"  the workhorse and the incumbent. It does not justify taking the whole box.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
