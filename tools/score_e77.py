#!/usr/bin/env python3
# File: tools/score_e77.py
# Purpose: Score E77 - the correct-to-wrong rate between an f16 KV baseline and each quantised arm, plus byte identity of the answers.
# Project: sparkbench | Date: 2026-08-28
#
# Overview: E77's primary metric is correct_to_wrong, NOT mean accuracy. Two
# arms can both score 21/24 and disagree on four items, and averaging hides
# exactly the failure this experiment exists to find. So this pairs the runs
# item by item against the f16 baseline and reports the flips in both
# directions, because a quantised arm that GAINS an item has told us the bank is
# noisy rather than that compression helps.
#
# needs_judge is carried separately and never folded into either flip count. An
# item the mechanical scorer cannot settle is not evidence of a break, and
# collapsing it into one would manufacture the finding.
#
# It also reports BYTE IDENTITY of the answer strings, which is a far more
# sensitive detector than the verdict. The idea and the argument for it come
# from tools/diff_run_answers.py (E59/F84): a score is too coarse to answer
# "does this serving flag change what the model SAYS", and two runs can agree on
# every verdict while disagreeing on every word.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_kw_eval import SCORER_VERSION, score_file  # noqa: E402

ANALYSIS_VERSION = "e77-agg-v1-2026-08-28"


def _name(verdict: bool | None) -> str:
    """score_kw_eval encodes the verdict as bool | None. Name it for reporting."""
    return {True: "correct", False: "wrong", None: "needs_judge"}[verdict]


def rows_by_id(path: Path) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Score one run and index its per-item rows by item id.

    Raises rather than returning a sentinel: a missing run file means the arm
    did not produce evidence, and a caller that quietly scored three arms as
    four would report a comparison that never happened.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"E77 arm file missing: {path}\n"
            f"hint: instrument A writes results/raw/e77-a-<kv>-<pack>.json; "
            f"an arm whose server never became healthy is DECLARED, not scored"
        )
    summary = score_file(path)
    idx = {r["id"]: r for r in summary["rows"]}
    if len(idx) != len(summary["rows"]):
        raise ValueError(
            f"duplicate item ids in {path}\n"
            f"hint: the bank must yield one row per id; a duplicate means the "
            f"runner wrote an item twice and the pairing below would be wrong"
        )
    return idx, summary


def answers_by_id(path: Path) -> dict[str, str]:
    d = json.loads(path.read_text())
    return {r["id"]: r["answer"] for r in d["records"]}


def compare(base: Path, cand: Path) -> dict[str, Any]:
    b_rows, b_sum = rows_by_id(base)
    c_rows, c_sum = rows_by_id(cand)

    shared = sorted(set(b_rows) & set(c_rows))
    if set(b_rows) != set(c_rows):
        raise ValueError(
            f"item sets differ between {base.name} and {cand.name}\n"
            f"hint: both arms must run the same bank on the same pack, or the "
            f"flip counts compare different questions"
        )

    b_ans, c_ans = answers_by_id(base), answers_by_id(cand)

    ctw, wtc, judge_moves, identical = [], [], [], 0
    for i in shared:
        bv, cv = b_rows[i]["verdict"], c_rows[i]["verdict"]
        if b_ans[i] == c_ans[i]:
            identical += 1
        # score_kw_eval's verdict domain is bool | None: True correct, False
        # wrong, None needs_judge. It is NOT a string, and comparing it to
        # "correct"/"wrong" silently yields zero flips forever - which is how the
        # first version of this file reported a clean zero on every arm.
        if bv is True and cv is False:
            ctw.append(i)
        elif bv is False and cv is True:
            wtc.append(i)
        elif bv is not cv and (bv is None or cv is None):
            judge_moves.append({"id": i, "from": _name(bv), "to": _name(cv)})

    return {
        "baseline": base.name,
        "candidate": cand.name,
        "n": len(shared),
        "baseline_correct": b_sum["correct"],
        "candidate_correct": c_sum["correct"],
        "correct_to_wrong": len(ctw),
        "correct_to_wrong_ids": ctw,
        "wrong_to_correct": len(wtc),
        "wrong_to_correct_ids": wtc,
        "verdict_moves_involving_needs_judge": judge_moves,
        "answers_byte_identical": identical,
        "answers_differing": len(shared) - identical,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E77: correct-to-wrong between an f16 KV baseline and each quantised arm.",
        epilog="example: python3 tools/score_e77.py --baseline-kv f16 "
        "--arms q8_0 q5_1 q4_0 --packs s m --out results/raw/e77-scores.json",
    )
    ap.add_argument("--raw-dir", default="results/raw")
    ap.add_argument("--prefix", default="e77-a", help="e77-a for instrument A")
    ap.add_argument("--baseline-kv", default="f16")
    ap.add_argument("--arms", nargs="+", default=["q8_0", "q5_1", "q4_0"])
    ap.add_argument("--packs", nargs="+", default=["s", "m"])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    raw = Path(args.raw_dir)
    out: dict[str, Any] = {
        "analysis_version": ANALYSIS_VERSION,
        "scorer_version": SCORER_VERSION,
        "comparisons": [],
    }

    for pack in args.packs:
        base = raw / f"{args.prefix}-{args.baseline_kv}-{pack}.json"
        for kv in args.arms:
            cmp_ = compare(base, raw / f"{args.prefix}-{kv}-{pack}.json")
            cmp_["pack"], cmp_["kv"] = pack, kv
            out["comparisons"].append(cmp_)
            print(
                f"pack {pack} | {args.baseline_kv} -> {kv:5s} | "
                f"correct {cmp_['baseline_correct']} -> {cmp_['candidate_correct']} | "
                f"correct_to_wrong {cmp_['correct_to_wrong']} "
                f"{cmp_['correct_to_wrong_ids'] or ''} | "
                f"wrong_to_correct {cmp_['wrong_to_correct']} "
                f"{cmp_['wrong_to_correct_ids'] or ''} | "
                f"byte-identical {cmp_['answers_byte_identical']}/{cmp_['n']}"
            )
            for m in cmp_["verdict_moves_involving_needs_judge"]:
                print(f"    needs_judge move: {m['id']} {m['from']} -> {m['to']}")

    totals = {
        kv: sum(c["correct_to_wrong"] for c in out["comparisons"] if c["kv"] == kv)
        for kv in args.arms
    }
    out["correct_to_wrong_totals_across_packs"] = totals
    print(f"\ncorrect_to_wrong summed over packs: {totals}")

    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
        print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
