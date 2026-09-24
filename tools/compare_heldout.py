#!/usr/bin/env python3
# File: compare_heldout.py
# Purpose: Join E57's two crossover runs into the shallow-versus-deep table that neither run can report on its own.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: E57 asks each question exactly once per run, so the pair that IS
# the measurement is split across two runs: set A is shallow in the `ab` run
# and deep in the `ba` run, set B the other way round. A single run's JSON
# therefore contains half of every pair and no summary at all - which is
# deliberate, and is why this tool exists rather than the runner reporting it.
#
# The join is on the recorded `probe` field, never on the order name. If a
# question turns up shallow in both runs, or deep in both, that is a broken
# crossover and this tool REFUSES rather than averaging two shallow cells into
# something that looks like a result.
#
# THE THIRD POSITION IS FREE AND IS PRINTED WHEN OFFERED. All ten questions
# have a standalone score from E54b, where they were asked with no conversation
# at all. Passing --standalone adds that column, which turns a two-point
# comparison into three: no conversation, shallow conversation, deep
# conversation. It is a WEAKER control than the crossover - E54b is a different
# run on a different day and the question text differs by E57's scope preamble
# - so it is printed as context and never as the headline.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))
from conversation_heldout import HELD_OUT_IDS, SET_A  # noqa: E402


def load_run(path: str) -> dict:
    d = json.loads(Path(path).read_text())
    if not d["conversation"].startswith("heldout-"):
        raise ValueError(
            f"{path} is a {d['conversation']!r} run, not a held-out one. "
            f"hint: E57 comparisons need two runs of --conversation heldout-ab "
            f"and heldout-ba"
        )
    return d


def cells(run: dict) -> dict[str, dict]:
    """Question id -> its record, for the shallow and deep turns only."""
    return {r["id"]: r for r in run["results"]
            if r["probe"] in ("shallow", "deep")}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Join E57's two crossover runs into one shallow-vs-deep table.",
        epilog="example: python3 tools/compare_heldout.py --ab results/raw/e57-x-ab.json "
               "--ba results/raw/e57-x-ba.json --standalone results/raw/e54b-x.json "
               "--out results/raw/e57-x-paired.json",
    )
    ap.add_argument("--ab", required=True, help="the heldout-ab run")
    ap.add_argument("--ba", required=True, help="the heldout-ba run")
    ap.add_argument("--standalone", default=None,
                    help="an E54b L4 run for the same model, for the "
                         "no-conversation column")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    ab, ba = load_run(args.ab), load_run(args.ba)
    if ab["conversation"] == ba["conversation"]:
        raise ValueError(
            f"both runs are {ab['conversation']!r}, so no question has a pair. "
            f"hint: --ab wants the heldout-ab run and --ba the heldout-ba one"
        )
    if ab["model"] != ba["model"]:
        raise ValueError(
            f"the two runs are different models ({ab['model']} vs {ba['model']}). "
            f"hint: the crossover compares a model with ITSELF at two depths"
        )
    for field in ("ctx", "max_tokens", "thinking", "server_extra"):
        if ab[field] != ba[field]:
            raise ValueError(
                f"the two runs differ in {field}: {ab[field]!r} vs {ba[field]!r}. "
                f"hint: depth must be the only variable; re-run the odd one out"
            )

    a_cells, b_cells = cells(ab), cells(ba)
    standalone = {}
    if args.standalone:
        s = json.loads(Path(args.standalone).read_text())
        # The L4 runner names its per-question list `results`, same as the
        # multi-turn runner. Indexed by hand rather than searched, so a file
        # with a different shape fails here instead of silently contributing
        # an empty standalone column that reads as "no data".
        standalone = {q["id"]: q["outcome"] for q in s["results"]}

    rows = []
    for qid in HELD_OUT_IDS:
        a, b = a_cells.get(qid), b_cells.get(qid)
        if not (a and b):
            raise ValueError(
                f"{qid} is missing from one of the runs "
                f"(ab={bool(a)}, ba={bool(b)}). "
                f"hint: a run that ended early cannot be paired - re-run it"
            )
        pair = {a["probe"]: a, b["probe"]: b}
        if set(pair) != {"shallow", "deep"}:
            raise ValueError(
                f"{qid} is {a['probe']} in both runs - the crossover is broken. "
                f"hint: check conversation_heldout.SET_A/SET_B and re-validate"
            )
        sh, dp = pair["shallow"], pair["deep"]
        rows.append({
            "id": qid,
            "set": "A" if qid in SET_A else "B",
            "standalone": standalone.get(qid),
            "shallow": sh["outcome"], "deep": dp["outcome"],
            "shallow_answer": sh["answer"], "deep_answer": dp["answer"],
            "shallow_history_tokens": sh["history_tokens"],
            "deep_history_tokens": dp["history_tokens"],
            "identical_answer": sh["answer"] == dp["answer"],
            "held": sh["outcome"] == dp["outcome"],
            "degraded": sh["outcome"] == "correct" and dp["outcome"] != "correct",
            "improved": sh["outcome"] != "correct" and dp["outcome"] == "correct",
        })

    # `recent` is reported separately and is the disambiguator: a model that
    # fails the deep questions but answers these has not lost the conversation,
    # it has lost the OLD part of it.
    recent = [{"id": r["id"], "run": name, "outcome": r["outcome"]}
              for name, run in (("ab", ab), ("ba", ba))
              for r in run["results"] if r["probe"] == "recent"]

    summary = {
        "model": ab["model"], "thinking": ab["thinking"],
        "ctx": ab["ctx"], "max_tokens": ab["max_tokens"],
        "ab_label": ab["label"], "ba_label": ba["label"],
        "standalone_label": (json.loads(Path(args.standalone).read_text())["label"]
                             if args.standalone else None),
        "shallow_correct": sum(1 for r in rows if r["shallow"] == "correct"),
        "deep_correct": sum(1 for r in rows if r["deep"] == "correct"),
        "total": len(rows),
        "degraded": [r["id"] for r in rows if r["degraded"]],
        "improved": [r["id"] for r in rows if r["improved"]],
        "identical_answer": sum(1 for r in rows if r["identical_answer"]),
        "wrong_document_deep": [r["id"] for r in rows if r["deep"] == "wrong_document"],
        "recent_correct": sum(1 for r in recent if r["outcome"] == "correct"),
        "recent_total": len(recent),
        "deep_history_tokens": max(r["deep_history_tokens"] for r in rows),
        "rows": rows, "recent": recent,
    }

    head = f"{'q':4} {'set':3} "
    if standalone:
        head += f"{'standalone':>14} "
    head += f"{'shallow':>14} {'deep':>14}   depth"
    print(head)
    for r in rows:
        line = f"{r['id']:4} {r['set']:3} "
        if standalone:
            line += f"{str(r['standalone']):>14} "
        flag = ("DEGRADED" if r["degraded"] else
                "improved" if r["improved"] else "held")
        line += (f"{r['shallow']:>14} {r['deep']:>14}   "
                 f"{r['deep_history_tokens']:,} {flag}")
        print(line)

    print(f"\nshallow {summary['shallow_correct']}/{summary['total']}  ->  "
          f"deep {summary['deep_correct']}/{summary['total']}   at "
          f"{summary['deep_history_tokens']:,} of {summary['ctx']:,} tokens "
          f"({summary['deep_history_tokens'] / summary['ctx'] * 100:.1f}%)")
    print(f"degraded: {summary['degraded'] or 'none'}   "
          f"improved: {summary['improved'] or 'none'}")
    print(f"answer byte-identical shallow and deep: "
          f"{summary['identical_answer']}/{summary['total']} "
          f"(NOT expected here - these are different runs, so this is a "
          f"determinism observation, not the measurement)")
    print(f"wrong_document at depth: {summary['wrong_document_deep'] or 'none'}")
    print(f"recent probes: {summary['recent_correct']}/{summary['recent_total']}")

    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2))
        print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
