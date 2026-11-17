#!/usr/bin/env python3
# File: tools/score_e164.py
# Purpose: Score E164 (Qwen4 Max) against results/e164-prereg.md: E160 suite fields, drafting nets, spend.
# Project: sparkbench | Date: 2026-11-17
#
# Overview: Suites go through score_e160.arm_fields UNCHANGED, pointed at results/e164/raw. kw-eval was not run
# (prereg), so kw_scored is replaced by an empty stand-in and every kw field is dropped from the output rather than
# reported as zero. KFL and KX come from E160's banked raw files through the same function. Drafting: net per pair
# from results/e164/drafting/judge-grok-4.7.json under E162's rule (decided = both orders agree). Spend sums the
# proxy ledger, the drafting record and the judge record, all provider-reported. Writes results/e164/score.json.

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/home/bench/sparkbench")
sys.path.insert(0, str(ROOT / "tools"))
import score_e160  # noqa: E402

OUT = ROOT / "results/e164"
KW_KEYS = ("kw", "kw_n", "kw_judge", "over_claim_kw", "unanswerable_kw_n")


def suite_fields(arm: str, raw: Path, has_kw: bool) -> dict:
    score_e160.RAW = raw
    orig = score_e160.kw_scored
    if not has_kw:
        score_e160.kw_scored = lambda _arm: {
            "correct": None,
            "n": 0,
            "needs_judge": None,
            "rows": [],
        }
    try:
        f = score_e160.arm_fields(arm)
    finally:
        score_e160.kw_scored = orig
    f.pop("tok")
    f.pop("wall")
    if not has_kw:
        for k in KW_KEYS:
            f.pop(k)
    return f


def nets(judge: dict) -> dict:
    out = {}
    for other in ("L", "C", "G"):
        recs = [r for r in judge["records"] if {r["x"], r["y"]} == {"Q", other}]
        if len(recs) != 10:
            raise ValueError(
                f"Q v {other}: {len(recs)} records, expected 10. hint: judging incomplete"
            )
        q = sum(
            (r["outcome"] == "x" and r["x"] == "Q")
            or (r["outcome"] == "y" and r["y"] == "Q")
            for r in recs
        )
        o = sum(
            (r["outcome"] == "x" and r["x"] == other)
            or (r["outcome"] == "y" and r["y"] == other)
            for r in recs
        )
        out[f"Q_over_{other}"] = {
            "q_wins": q,
            "other_wins": o,
            "undecided": 10 - q - o,
            "net": q - o,
        }
    return out


def main() -> int:
    ledger = [
        json.loads(line) for line in (OUT / "raw/ledger.jsonl").read_text().splitlines()
    ]
    judge = json.loads((OUT / "drafting/judge-grok-4.7.json").read_text())
    drafts = json.loads((OUT / "drafting/drafts-Q.json").read_text())
    spend = {
        "suites_proxy": round(sum(r["cost_usd"] for r in ledger), 4),
        "drafting": drafts["spend"]["usd_provider_reported"],
        "judge": judge["spend"]["usd_provider_reported"],
    }
    spend["total"] = round(sum(spend.values()), 4)
    rec = {
        "Q": suite_fields("Q", OUT / "raw", has_kw=False),
        "KFL": suite_fields("KFL", ROOT / "results/e160/raw", has_kw=True),
        "KX": suite_fields("KX", ROOT / "results/e160/raw", has_kw=True),
        "drafting_nets_grok": nets(judge),
        "spend_usd": spend,
        "suite_calls": len(ledger),
        "suite_tokens": {
            "prompt": sum(r["prompt_tokens"] for r in ledger),
            "completion": sum(r["completion_tokens"] for r in ledger),
            "reasoning": sum(r["reasoning_tokens"] or 0 for r in ledger),
        },
        "finish_reasons": {
            k: sum(r["finish_reason"] == k for r in ledger)
            for k in {r["finish_reason"] for r in ledger}
        },
    }
    (OUT / "score.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps(rec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
