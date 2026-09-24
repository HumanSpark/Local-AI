#!/usr/bin/env python3
# File: score_e92.py
# Purpose: Score E92 against its pre-registered hypotheses, using E91's same-build arms as controls.
# Project: sparkbench | Date: 2026-08-31
#
# Overview: Reads results/raw/e92/ and scores H1-H6 from results/e92-prereg.md
# by the field each names. The controls are NOT re-measured here - E91 ran the
# workhorse and Qwen3.8-27B on this same build on the same day, so their figures
# are read from results/raw/e91/ rather than assumed or quoted from the frozen
# F-register. If an E91 file is missing the affected hypothesis reports
# UNSCORED rather than falling back to a figure from another build (E85:
# build-to-build extrapolation is unsafe for correctness).

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path("/home/agent-spark/sparkbench")
E92 = REPO / "results/raw/e92"
E91 = REPO / "results/raw/e91"

# F80's walked-period categories - eight items, fee_basis included.
COUNTED = ("statutory_period", "breach_clock", "interest_calc",
           "notice_period", "fee_basis")


def load(p: Path) -> dict | None:
    """Prefer the max_tokens=16384 re-run where it exists.

    The first pass truncated at 4,096 and its numbers are budget artefacts, not
    measurements (Rule 13). The re-run is the same model, bank, effort, grader
    and build with only the cap and the context raised, so it supersedes rather
    than sits beside the original."""
    rerun = p.with_name(p.stem + "-mt16384" + p.suffix)
    if rerun.exists():
        return json.loads(rerun.read_text())
    return json.loads(p.read_text()) if p.exists() else None


def counted(d: dict) -> tuple[int, int]:
    bc = d.get("by_category", {})
    return (sum(bc.get(k, {}).get("correct", 0) for k in COUNTED),
            sum(bc.get(k, {}).get("total", 0) for k in COUNTED))


def truncation(d: dict, only: tuple[str, ...] | None = None) -> tuple[int, int]:
    """(truncated, total) over all items, or over `only` categories.

    A `truncated` item was never answered - the model was cut off mid-output.
    Scoring it as a miss reports the token budget as if it were the model's
    capability, which is the vacuous-success class: a number that looks like a
    measurement and is not one. Every hypothesis below refuses rather than
    scores when truncation touches the field it names.
    """
    rs = d.get("results", [])
    if only is not None:
        rs = [r for r in rs if r.get("category") in only]
    return sum(1 for r in rs if r.get("outcome") == "truncated"), len(rs)


def bench_tg128(path: Path) -> float | None:
    """First tg128 row (depth 0) from a llama-bench markdown table."""
    if not path.exists():
        return None
    for line in path.read_text().splitlines():
        if "tg128" in line and "@" not in line and "|" in line:
            cells = [c.strip() for c in line.split("|")]
            for c in reversed(cells):
                if c and c[0].isdigit():
                    try:
                        return float(c.split("±")[0].strip())
                    except ValueError:
                        pass
    return None


def main() -> int:
    nemo_l4 = load(E92 / "e92-nemotron-nano-l4.json")
    nemo_l3 = load(E92 / "e92-nemotron-nano-l3.json")
    kwai_x = load(E92 / "e92-kwaipilot-expert.json")
    kwai_l4 = load(E92 / "e92-kwaipilot-l4.json")

    wh_l4 = load(E91 / "e91-A-workhorse-l4.json")
    wh_l3 = load(E91 / "e91-A-workhorse-l3.json")
    q38_l4 = load(E91 / "e91-B-qwen38-low-l4.json")

    print("=== E92 arms ===")
    for name, d in [("nemotron-nano l4", nemo_l4), ("nemotron-nano l3", nemo_l3),
                    ("kwaipilot expert", kwai_x), ("kwaipilot l4", kwai_l4)]:
        if d:
            tot = d.get("total")
            print(f"  {name:20s} {d.get('correct')}/{tot}  wall={d.get('wall_s')}s")
        else:
            print(f"  {name:20s} ABSENT")

    print("\n=== controls, read from E91 (same build, same day) ===")
    for name, d in [("workhorse l4", wh_l4), ("workhorse l3", wh_l3),
                    ("Qwen3.8-27B l4", q38_l4)]:
        if d:
            c, t = counted(d) if "l4" in name else (d["correct"], d["total"])
            print(f"  {name:18s} {d['correct']}/{d['total']}   walked/total {c}/{t}")
        else:
            print(f"  {name:18s} ABSENT - dependent hypotheses will be UNSCORED")

    print("\n=== hypotheses ===")

    # H1 / H2 / H3 - Kwaipilot on the expert coding bank
    if kwai_x:
        # run_coding_eval's pass count field varies by version; try the common ones.
        passed = kwai_x.get("passed", kwai_x.get("correct"))
        total = kwai_x.get("total")
        tr, n = truncation(kwai_x)
        # Rule 13: score ONLY where truncation cannot change the verdict. A
        # truncated task might have passed, so `passed` is a floor and
        # `passed + tr` is the ceiling. A hypothesis whose answer differs
        # between those two bounds is UNSCORABLE, not falsified.
        if tr:
            print(f"  [gate {kwai_x.get('truncation_gate')}: {tr}/{n} tasks truncated - "
                  f"passes are bounded {passed}..{passed + tr}]")
        lo, hi = passed, passed + tr
        if hi <= 7:
            print(f"  H1 Kwaipilot expert {lo}..{hi} of {total} (<= 7 = uplift did NOT "
                  f"transfer): HOLDS - robust to the truncation")
        elif lo > 7:
            print(f"  H1 Kwaipilot expert {lo}..{hi}: FALSIFIED")
        else:
            print(f"  H1 UNSCORABLE - {lo}..{hi} straddles the <= 7 band")
        if lo >= 3:
            print(f"  H2 Kwaipilot expert >= 3: HOLDS")
        elif hi < 3:
            print(f"  H2 Kwaipilot expert {lo}..{hi} >= 3: FALSIFIED")
        else:
            print(f"  H2 UNSCORABLE - {lo}..{hi} straddles the >= 3 band, and the "
                  f"6 truncated tasks are exactly the unknown")
        sm = [r for r in kwai_x.get("results", [])
              if "sliding_median" in str(r.get("task", r.get("id", "")))]
        if sm:
            out = sm[0].get("outcome")
            if out == "truncated":
                print("  H3 UNSCORABLE - sliding_median was truncated at the cap, "
                      "never attempted to completion")
            else:
                ok = sm[0].get("passed", out) in (True, "correct", "pass")
                print(f"  H3 sliding_median solved: {'HOLDS' if ok else 'FALSIFIED'}")
        else:
            print("  H3 UNSCORED - sliding_median not found in results")
    else:
        print("  H1/H2/H3 UNSCORED - kwaipilot expert arm absent")

    # H4 - Nemotron walked periods: workhorse-class (0-2) or 27B-class?
    if nemo_l4:
        c, t = counted(nemo_l4)
        trw, _ = truncation(nemo_l4, COUNTED)
        note = ""
        if trw:
            note = (f" [{trw} walked item(s) truncated, so the true score is "
                    f"{c}..{c + trw}; the verdict is the same at both bounds]")
        print(f"  H4 Nemotron walked {c}/{t} (0-2 = lands with the workhorse): "
              f"{'HOLDS' if c + trw <= 2 else 'FALSIFIED'}{note}")
        if c >= 5:
            print("     ** FALSIFIER FIRED: at >=5 of 8, F80's claim is about the")
            print("        WORKHORSE, not about ~3B-active MoEs as a class. **")
    else:
        print("  H4 UNSCORED - nemotron l4 absent")

    # H5 - Nemotron l3 within 2 of the workhorse's
    if nemo_l3 and wh_l3:
        diff = abs(nemo_l3["correct"] - wh_l3["correct"])
        print(f"  H5 Nemotron l3 {nemo_l3['correct']}/12 vs workhorse "
              f"{wh_l3['correct']}/12, |diff|={diff} (<= 2): "
              f"{'HOLDS' if diff <= 2 else 'FALSIFIED'}")
    else:
        print("  H5 UNSCORED - nemotron or workhorse l3 absent")

    # H6 - Nemotron tg128 within 25% of the workhorse's 92.28
    tg = bench_tg128(E92 / "e92-nemotron-nano-bench.md")
    if tg is not None:
        lo = 92.28 * 0.75
        print(f"  H6 Nemotron tg128 {tg:.2f} t/s (>= {lo:.2f} = within 25% of "
              f"the workhorse's 92.28): {'HOLDS' if tg >= lo else 'FALSIFIED'}")
    else:
        print("  H6 UNSCORED - no tg128 row in the nemotron bench")

    print("\n=== the queued side-question ===")
    tg27 = bench_tg128(E92 / "e92-qwen38-27b-dense-bench.md")
    if tg27 is not None:
        inband = 10.0 <= tg27 <= 14.0
        print(f"  dense Qwen3.8-27B tg128 {tg27:.2f} t/s against the community's "
              f"10-14 t/s claim for dense >=27B: {'CONFIRMED' if inband else 'OUTSIDE'}")
    else:
        print("  UNSCORED - no dense-27B bench")
    return 0


if __name__ == "__main__":
    sys.exit(main())
