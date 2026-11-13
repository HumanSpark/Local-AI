# File: tools/judge_writing_pairwise.py
# Purpose: Blind pairwise judging of writing-eval drafts from two or more arms by a frontier model that is not a contestant.
# Project: sparkbench | Date: 2026-11-13
#
# Overview: For each writing task and each pair of arms, the judge sees the task prompt (the brief, the source facts
# and the house style) and two drafts labelled A and B, with no arm names. Every pair is judged in BOTH orders, which
# cancels position bias and yields a consistency figure. A pair counts as a win only when both orders agree; a split
# verdict is a tie. Verdicts are parsed from the first line and kept raw when unrecognised, never coerced. Calls go
# through tools/cloud_client.chat (OpenRouter key from the vault, spend ceiling enforced). Output: one JSON with every
# raw verdict plus per-arm win/tie/loss counts. E160 prereg: results/e160-prereg.md.
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cloud_client import CloudBudget, chat  # noqa: E402

RUBRIC = """You are reviewing two drafts written for the same brief by a professional-services firm.
Judge which draft a demanding client-facing editor would rather send, considering, in order:
1. Accuracy: every figure and fact matches the source; nothing invented, nothing material left out.
2. Fitness for the reader: it answers what the brief asks, at the right length and register.
3. Clarity and structure: easy to read once, logically ordered, no padding.
4. House style as stated in the brief.
Length alone is not quality. Do not reward a draft for being longer."""

VERDICTS = {"A IS BETTER": "A", "B IS BETTER": "B", "TIE": "tie"}

CLOSING = (
    "# YOUR TASK\nCompare DRAFT A and DRAFT B against the BRIEF. Do not write a draft yourself.\n"
    "Your FIRST line must be exactly one of: A IS BETTER / B IS BETTER / TIE\n"
    "Then give at most three sentences of reasons."
)


def build_prompt(brief: str, a: str, b: str) -> str:
    return f"{RUBRIC}\n\n# BRIEF (reference)\n{brief}\n\n# DRAFT A\n{a}\n\n# DRAFT B\n{b}\n\n{CLOSING}\n"


def parse_verdict(text: str) -> str:
    """First non-empty line mapped to A / B / tie, or 'unparsed' (kept, never guessed)."""
    for line in text.splitlines():
        head = line.strip().strip("#*_ .").upper()
        if head:
            return VERDICTS.get(head, "unparsed")
    return "unparsed"


def combine(v_ab: str, v_ba: str) -> str:
    """Order AB then BA (the second call shows arm 2 as A). Returns 'x', 'y' or 'tie' for arms (x, y)."""
    x_first = {"A": "x", "B": "y", "tie": "tie"}.get(v_ab)
    x_second = {"A": "y", "B": "x", "tie": "tie"}.get(v_ba)
    if x_first is None or x_second is None:
        return "unparsed"
    return x_first if x_first == x_second else "tie"


def load_drafts(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text())
    drafts = {}
    for r in data["results"]:
        if not r.get("output"):
            raise KeyError(
                f"{path}: task {r['id']} has no draft (outcome {r['outcome']}). "
                f"hint: a transport-failed or missing draft cannot be judged; rerun that task first"
            )
        drafts[r["id"]] = r["output"]
    return drafts


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        epilog="example: tools/judge_writing_pairwise.py --arm KFL=results/e160/raw/KFL/writing.json "
        "--arm KM=results/e160/raw/KM/writing.json --out results/e160/writing-judge.json",
    )
    ap.add_argument(
        "--arm",
        action="append",
        required=True,
        help="LABEL=path to a run_writing_eval.py result",
    )
    ap.add_argument(
        "--judge",
        default="anthropic/claude-opus-5.5",
        help="OpenRouter model id (not a contestant)",
    )
    ap.add_argument("--usd-ceiling", type=float, default=10.0)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--dry-run", action="store_true", help="build every prompt, call nothing"
    )
    args = ap.parse_args()

    sys.path.insert(
        0, str(Path(__file__).resolve().parent.parent / "spikes" / "writing-eval")
    )
    from tasks import TASKS  # noqa: PLC0415 - path set just above

    briefs = {t["id"]: t["prompt"] for t in TASKS}
    arms = dict(a.split("=", 1) for a in args.arm)
    drafts = {label: load_drafts(Path(p)) for label, p in arms.items()}
    budget = CloudBudget(usd_ceiling=args.usd_ceiling)
    records, tally = [], {label: {"win": 0, "tie": 0, "loss": 0} for label in arms}
    pairs = list(itertools.combinations(sorted(arms), 2))
    n = len(pairs) * len(briefs) * 2
    print(
        f"{len(briefs)} tasks x {len(pairs)} pairs x 2 orders = {n} judge calls ({args.judge})"
    )
    done = 0
    for tid, brief in briefs.items():
        for x, y in pairs:
            verdicts = []
            for first, second in ((x, y), (y, x)):
                prompt = build_prompt(brief, drafts[first][tid], drafts[second][tid])
                if args.dry_run:
                    verdicts.append(("tie", "(dry run)"))
                    continue
                r = chat(
                    args.judge,
                    [{"role": "user", "content": prompt}],
                    budget,
                    provider="openrouter",
                    temperature=0,
                    max_tokens=4000,  # Opus 5.5 spends reasoning tokens first; 400 left empty content (2026-11-13)
                    timeout=300,
                    retries=6,
                )
                verdicts.append((parse_verdict(r["content"]), r["content"]))
                done += 1
                print(
                    f"  [{done}/{n}] {tid} {first} vs {second}: {verdicts[-1][0]}",
                    flush=True,
                )
            outcome = combine(verdicts[0][0], verdicts[1][0])
            if outcome == "x":
                tally[x]["win"] += 1
                tally[y]["loss"] += 1
            elif outcome == "y":
                tally[y]["win"] += 1
                tally[x]["loss"] += 1
            elif outcome == "tie":
                tally[x]["tie"] += 1
                tally[y]["tie"] += 1
            records.append(
                {
                    "task": tid,
                    "x": x,
                    "y": y,
                    "outcome": outcome,
                    "verdict_xy": verdicts[0][0],
                    "verdict_yx": verdicts[1][0],
                    "raw_xy": verdicts[0][1],
                    "raw_yx": verdicts[1][1],
                }
            )
    consistent = sum(
        r["verdict_xy"] != "unparsed" and r["outcome"] != "tie" for r in records
    )
    out = {
        "judge": args.judge,
        "arms": arms,
        "tally": tally,
        "pairs_decided": consistent,
        "pairs_total": len(records),
        "unparsed": sum(r["outcome"] == "unparsed" for r in records),
        "records": records,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(json.dumps(tally, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
