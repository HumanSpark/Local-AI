#!/usr/bin/env python3
# File: tools/score_e163.py
# Purpose: Score E163 (Loom LM, llama.cpp LC, Halogen HS) against results/e163-prereg.md P1-P8.
# Project: sparkbench | Date: 2026-11-16
#
# Overview: Speed fields come from results/e163/raw/<arm>/speed.json (tools/e163_speed.py medians). Quality fields reuse
# tools/score_e160.arm_fields unchanged, pointed at results/e163/raw, so every suite is graded exactly as E160 graded it.
# Production's E160 arm KFL (community template + low) is printed as a reference column and not scored against.
# Writes results/e163/score.json. A missing file or field raises: an absent suite must not score as zero.
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results/e163/raw"
sys.path.insert(0, str(ROOT / "tools"))
import score_e160  # noqa: E402

AMD_P32K = 1196.0  # loom-fun package card, prefill tok/s at 32K, measured 2026-11-13
SUITES = [
    ("l5", "L5 hard document Q&A"),
    ("pr1", "pr1 refuse/comply"),
    ("kw", "kw-eval real documents"),
    ("writing", "writing grader"),
    ("mt-l4", "conversation l4"),
    ("mt-long", "conversation long"),
    ("h6", "H6 dates with tool"),
    ("tooluse", "tool use (tasks passed)"),
]


def speed(arm: str) -> dict:
    return json.loads((RAW / arm / "speed.json").read_text())["summary"]


def main() -> int:
    S = {a: speed(a) for a in ("LM", "LC", "HS")}
    Q = {}
    for arm, raw in (("LM", RAW), ("HS", RAW), ("KFL", ROOT / "results/e160/raw")):
        score_e160.RAW = raw
        Q[arm] = score_e160.arm_fields(arm)
    pf = {a: S[a]["P32K"]["prefill_tps"] for a in S}
    dec = {a: S[a]["D1500"]["decode_tps"] for a in S}
    lm, hs = Q["LM"], Q["HS"]
    per_suite = {k: (lm[k], hs[k]) for k, _ in SUITES if k != "tooluse"}
    P = {
        "P1": (pf["LM"] >= 1.5 * pf["LC"], round(pf["LM"] / pf["LC"], 2)),
        "P2": (
            abs(pf["LM"] - AMD_P32K) / AMD_P32K <= 0.15,
            round(pf["LM"] / AMD_P32K - 1, 3),
        ),
        "P3": (dec["LM"] >= 1.1 * dec["LC"], round(dec["LM"] / dec["LC"], 2)),
        "P4": (pf["LM"] <= 1.0 * pf["HS"], round(pf["LM"] / pf["HS"], 2)),
        "P5": (dec["LM"] <= 0.7 * dec["HS"], round(dec["LM"] / dec["HS"], 2)),
        "P6": (
            all(a >= b - 1 for a, b in per_suite.values()),
            {k: v for k, v in per_suite.items() if v[0] < v[1] - 1}
            or "none below HS - 1",
        ),
        "P7": (
            lm["tooluse"] >= hs["tooluse"] - 1 and lm["leaks"] == 0,
            [lm["tooluse"], hs["tooluse"], lm["leaks"]],
        ),
    }
    out = {
        "speed": S,
        "quality": {
            a: {k: Q[a][k] for k, _ in SUITES}
            | {f"{k}_n": Q[a].get(f"{k}_n") for k, _ in SUITES}
            | {
                "leaks": Q[a]["leaks"],
                "missed_flag": Q[a]["missed_flag"],
                "over_claim_l5": Q[a]["over_claim_l5"],
                "over_claim_kw": Q[a]["over_claim_kw"],
                "tok_median": Q[a]["tok_median"],
                "wall_median": Q[a]["wall_median"],
                "l5_lost": Q[a]["l5_lost"],
            }
            for a in Q
        },
        "predictions": {k: {"held": v[0], "value": v[1]} for k, v in P.items()},
    }
    (ROOT / "results/e163/score.json").write_text(
        json.dumps(out, indent=1, default=str)
    )
    print(f"{'speed (median)':26} {'LM':>8} {'LC':>8} {'HS':>8}")
    for p, key in (
        ("P8K", "prefill_tps"),
        ("P32K", "prefill_tps"),
        ("D1500", "decode_tps"),
        ("P32K", "decode_tps"),
    ):
        print(
            f"{p + ' ' + key:26} "
            + " ".join(f"{S[a][p][key]:>8}" for a in ("LM", "LC", "HS"))
        )
    print(f"\n{'suite':28} {'LM':>7} {'HS':>7} {'KFL ref':>8}")
    for k, name in SUITES:
        n = Q["LM"].get(f"{k}_n", 7)
        print(
            f"{name:28} {Q['LM'][k]:>4}/{n:<2} {Q['HS'][k]:>4}/{n:<2} {Q['KFL'][k]:>5}/{n:<2}"
        )
    print(
        f"tool-call leaks: LM {lm['leaks']} HS {hs['leaks']}; tokens median LM {lm['tok_median']} HS {hs['tok_median']}"
    )
    for k, v in out["predictions"].items():
        print(k, "HELD" if v["held"] else "FAILED", v["value"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
