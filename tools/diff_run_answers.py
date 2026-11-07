#!/usr/bin/env python3
# File: diff_run_answers.py
# Purpose: Compare two runs of the SAME conversation under two serving configs, on the answer STRINGS rather than on the score.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: Rule 8 says a benchmark measures a CONFIG, and that claiming a
# config difference MATTERS needs measuring too. The usual way that gets done is
# by comparing scores, and a score is far too coarse an instrument for the
# question this tool exists for: does turning on speculative decoding change
# what the model SAYS?
#
# A score cannot answer that. Two runs can both be 13/13 while disagreeing on
# every word, and speculative decoding is supposed to be mathematically exact -
# so the honest test is not "did accuracy hold" but "is the output the same
# string". This compares answer text, then outcome, then tokens, then wall time,
# and reports the first three separately from the fourth because a throughput
# win that changes answers is not a throughput win.
#
# THE PROBE THIS WAS BUILT FOR. E57's Qwen3.8-27B produced ten of ten
# byte-identical answers across two separate runs and two separate server
# processes. That is an unusually strong determinism baseline, and it makes the
# model a sensitive detector: re-run the same conversation with one serving flag
# changed, and any divergence is attributable to the flag rather than to
# sampling noise, because the noise floor was measured at zero.
#
# IT REFUSES A COMPARISON THAT IS NOT ONE VARIABLE. Model, conversation, ctx,
# max_tokens and thinking must all match; only `server_extra` may differ. A diff
# across two models is not a config comparison, and averaging it into one would
# produce a number about nothing.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Everything that must be IDENTICAL for the diff to mean anything. server_extra
# is deliberately absent: it is the variable under test.
MUST_MATCH = ("model", "conversation", "ctx", "max_tokens", "thinking")


def load(path: str) -> dict:
    return json.loads(Path(path).read_text())


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Diff two runs of one conversation under two serving configs.",
        epilog="example: python3 tools/diff_run_answers.py "
               "--baseline results/raw/e57-20260819-qwen38-ab.json "
               "--candidate results/raw/e57mtp-20260819-qwen38-ab.json",
    )
    ap.add_argument("--baseline", required=True, help="the run whose config is known-good")
    ap.add_argument("--candidate", required=True, help="the run with the flag under test")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    base, cand = load(args.baseline), load(args.candidate)

    for field in MUST_MATCH:
        if base[field] != cand[field]:
            raise SystemExit(
                f"refusing to diff: {field} differs "
                f"({base[field]!r} vs {cand[field]!r}). "
                f"hint: this tool isolates ONE serving flag; only server_extra "
                f"may differ between the two runs"
            )
    if base["server_extra"] == cand["server_extra"]:
        raise SystemExit(
            f"refusing to diff: both runs used server_extra "
            f"{base['server_extra']!r}, so there is no config difference to "
            f"attribute anything to. hint: pass the run that carries the flag "
            f"under test as --candidate"
        )

    b_by = {r["id"]: r for r in base["results"]}
    c_by = {r["id"]: r for r in cand["results"]}
    missing = sorted(set(b_by) ^ set(c_by))
    if missing:
        raise SystemExit(
            f"refusing to diff: turn ids differ between the runs ({missing}). "
            f"hint: a run that ended early cannot be compared - re-run it"
        )

    rows = []
    for tid, b in b_by.items():
        if not b["graded"]:
            continue
        c = c_by[tid]
        # The run JSON stores the PARSED answer, not the raw completion, so
        # answer-identity alone is a weaker determinism test than it looks: two
        # completions can differ in their reasoning or their trailing prose and
        # still yield the same one-line ANSWER. completion_tokens and
        # reasoning_chars are the available proxies for the whole string, and
        # they are strong ones - a diverged completion almost never lands on the
        # identical token count. `strict_identical` requires all four to match
        # and is what the graduation gate should be read against.
        strict = (b["answer"] == c["answer"]
                  and b["citation"] == c["citation"]
                  and b["completion_tokens"] == c["completion_tokens"]
                  and b["reasoning_chars"] == c["reasoning_chars"])
        rows.append({
            "id": tid, "probe": b["probe"],
            "answer_identical": b["answer"] == c["answer"],
            "strict_identical": strict,
            "baseline_citation": b["citation"], "candidate_citation": c["citation"],
            "baseline_reasoning_chars": b["reasoning_chars"],
            "candidate_reasoning_chars": c["reasoning_chars"],
            "baseline_answer": b["answer"], "candidate_answer": c["answer"],
            "baseline_outcome": b["outcome"], "candidate_outcome": c["outcome"],
            "outcome_changed": b["outcome"] != c["outcome"],
            "baseline_gen": b["completion_tokens"], "candidate_gen": c["completion_tokens"],
            "baseline_wall_s": b["wall_s"], "candidate_wall_s": c["wall_s"],
        })

    identical = sum(1 for r in rows if r["answer_identical"])
    strict = sum(1 for r in rows if r["strict_identical"])
    changed = [r for r in rows if r["outcome_changed"]]
    b_wall, c_wall = base["wall_s"], cand["wall_s"]

    print(f"baseline  {base['label']:26} server_extra={base['server_extra']!r}")
    print(f"candidate {cand['label']:26} server_extra={cand['server_extra']!r}")
    print(f"model     {base['model']}")
    print(f"\n{'turn':6} {'probe':9} {'same?':6} {'outcome':>30} {'gen tok':>16} {'wall s':>16}")
    for r in rows:
        same = "yes" if r["answer_identical"] else "NO"
        oc = (f"{r['baseline_outcome']} -> {r['candidate_outcome']}"
              if r["outcome_changed"] else r["baseline_outcome"])
        print(f"{r['id']:6} {r['probe']:9} {same:6} {oc:>30} "
              f"{r['baseline_gen']:>7,}/{r['candidate_gen']:<8,} "
              f"{r['baseline_wall_s']:>7.1f}/{r['candidate_wall_s']:<8.1f}")

    print(f"\nANSWER STRINGS IDENTICAL: {identical}/{len(rows)}")
    print(f"STRICT IDENTICAL (answer + citation + gen tokens + reasoning chars): "
          f"{strict}/{len(rows)}")
    print(f"outcomes changed: {[r['id'] for r in changed] or 'none'}")
    print(f"baseline correct {base['correct']}/{base['total']}  ->  "
          f"candidate {cand['correct']}/{cand['total']}")
    speedup = b_wall / c_wall if c_wall else 0
    print(f"wall time: {b_wall:,.1f}s -> {c_wall:,.1f}s  ({speedup:.2f}x)")

    if strict == len(rows):
        print("\nEXACT: answer, citation, generated-token count and reasoning length "
              "all unchanged on\nevery cell. The flag did not alter what the model "
              "said, so any wall-time change is free.")
    elif identical == len(rows):
        print(f"\nANSWERS HELD, COMPLETIONS MOVED: every parsed answer is unchanged, "
              f"but {len(rows) - strict} cell(s)\ndiffer in token count or reasoning "
              f"length - so the full completion was NOT identical.\nThe graded result "
              f"survives; the determinism property does not. Report both.")
    else:
        print(f"\nDIVERGENT: {len(rows) - identical} answer(s) changed. Whatever the "
              "wall time did, this flag\nis not output-preserving on this model - "
              "report the divergence before the speed.")

    summary = {
        "baseline_label": base["label"], "candidate_label": cand["label"],
        "baseline_server_extra": base["server_extra"],
        "candidate_server_extra": cand["server_extra"],
        "model": base["model"], "graded_turns": len(rows),
        "answers_identical": identical,
        "strict_identical": strict,
        "exact": strict == len(rows),
        "outcomes_changed": [r["id"] for r in changed],
        "baseline_correct": base["correct"], "candidate_correct": cand["correct"],
        "baseline_wall_s": b_wall, "candidate_wall_s": c_wall,
        "speedup": round(speedup, 3),
        "rows": rows,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(summary, indent=2))
        print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
