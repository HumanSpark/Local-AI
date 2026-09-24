#!/usr/bin/env python3
# File: regrade_multiturn.py
# Purpose: Re-grade a finished multi-turn run from its STORED answers, so a grader repair costs no GPU and no new model output.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: A multi-turn run records every answer string it received. When the
# GRADER is repaired, the honest thing to re-derive is the outcome, not the
# answer - re-running the models would change two things at once and make the
# repair unattributable. E54b established this pattern: across all three arms
# not one answer string differed, and every outcome change was a byte-identical
# answer re-graded by a newly added trap.
#
# WHAT THIS TOOL WILL NOT DO. It refuses to rewrite the input file. A regrade
# writes a NEW file and prints every cell that moved, so the original outcome
# stays on disk and the diff is reviewable. A tool that silently improved a
# result in place is a tool nobody can audit.
#
# It also re-derives the turn specs from the conversation SCRIPT rather than
# from anything stored in the run, so a spec that has drifted since the run is
# caught as a mismatch instead of being quietly applied.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))
from grade_multiturn import grade_multiturn  # noqa: E402
from run_multiturn_eval import load_conversation  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Re-grade a multi-turn run from its stored answers.",
        epilog="example: python3 tools/regrade_multiturn.py "
               "results/raw/e57-20260819-workhorse-ab.json --out-suffix .regraded",
    )
    ap.add_argument("runs", nargs="+", help="one or more run JSONs")
    ap.add_argument("--out-suffix", default=".regraded",
                    help="written alongside each input; the input is never modified")
    ap.add_argument("--conversation", default=None,
                    help="script name for runs that predate the `conversation` "
                         "field (E55). Never inferred - the wrong key would "
                         "regrade a run against a different experiment.")
    ap.add_argument("--in-place", action="store_true",
                    help="overwrite the input. Use ONLY once the regrade has been "
                         "reviewed and the reason is recorded in results/")
    args = ap.parse_args()

    total_moved = 0
    for path_s in args.runs:
        path = Path(path_s)
        run = json.loads(path.read_text())
        # E55's runs predate the `conversation` field, which arrived with E56's
        # second script. Guessing which script produced a run would regrade it
        # against the wrong answer key and report the mismatch as a model
        # result, so the name must be SUPPLIED for those files rather than
        # inferred.
        if "conversation" not in run:
            if not args.conversation:
                raise SystemExit(
                    f"{path.name} has no `conversation` field - it predates "
                    f"that field (E55, 2026-08-17). "
                    f"hint: pass --conversation l4 for an E55 run; do not "
                    f"regrade a run whose script you cannot name"
                )
            run["conversation"] = args.conversation
        conv = load_conversation(run["conversation"])
        by_id = {t["id"]: t for t in conv.TURNS}

        moved: list[str] = []
        for rec in run["results"]:
            if not rec["graded"]:
                continue
            turn = by_id.get(rec["id"])
            if turn is None or "expect" not in turn:
                raise ValueError(
                    f"{path.name}: turn {rec['id']} is graded in the run but is "
                    f"not a graded turn in conversation {run['conversation']!r}. "
                    f"hint: the script changed since the run - regrade against "
                    f"the script that produced it, or do not regrade at all"
                )
            # A truncated turn produced no answer to grade; leave it alone
            # rather than inventing an outcome for a turn that never finished.
            if rec["outcome"] == "truncated":
                continue
            was = rec["outcome"]
            now = grade_multiturn(turn, rec["answer"])
            if now != was:
                moved.append(f"{rec['id']:5} {rec.get('probe', ''):8} "
                             f"{was:16} -> {now:16} {str(rec['answer'])[:34]}")
                rec["outcome"] = now
                rec["outcome_before_regrade"] = was

        graded = [r for r in run["results"] if r["graded"]]
        run["correct"] = sum(1 for r in graded if r["outcome"] == "correct")
        for label in ("accepted_false", "stale_answer", "over_revised",
                      "wrong_document"):
            run[label] = sum(1 for r in graded if r["outcome"] == label)
        counts: dict[str, int] = {}
        by_probe: dict[str, dict[str, int]] = {}
        for r in graded:
            counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
            b = by_probe.setdefault(r["probe"], {"correct": 0, "total": 0})
            b["total"] += 1
            b["correct"] += 1 if r["outcome"] == "correct" else 0
        run["outcome_counts"], run["by_probe"] = counts, by_probe
        run["regraded"] = True

        out = path if args.in_place else path.with_suffix(path.suffix + args.out_suffix)
        out.write_text(json.dumps(run, indent=2))
        total_moved += len(moved)
        print(f"{path.name}: {len(moved)} cell(s) moved, "
              f"correct {run['correct']}/{len(graded)} -> {out.name}")
        for line in moved:
            print(f"    {line}")

    print(f"\n{total_moved} cell(s) moved across {len(args.runs)} run(s). "
          f"Every answer string is unchanged - only the LABEL was re-derived.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
