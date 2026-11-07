# File: run_ps_eval_subagent.py
# Purpose: run a ps-eval tier through Claude Code subagents instead of HTTP, and grade it with the repo's own grader.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: two subcommands. `prompts` emits the tier's prompts EXACTLY as
# run_ps_eval.py builds them, for pasting one-per-subagent into the Agent tool;
# `grade` takes the collected answers back and scores them through the same
# parse_response + grade + grade_citation path the HTTP runner uses. Nothing
# about prompting or correctness is re-implemented, because a bespoke grader
# would make this arm incomparable with the arms it exists to be compared to.
#
# WHY THIS EXISTS AT ALL: E65 needed a frontier comparator and no working cloud
# credential exists (the vaulted OpenRouter key returns 401 "User not found").
# This transport costs no API credit. It also CANNOT pin a model version - the
# Agent tool's enum is sonnet/opus/haiku/fable and resolves to the running
# session's model - so every result it writes carries a harness_caveats block
# saying so. A reader who mistakes this for an API measurement would be wrong,
# and Rule 8 / F39 make that the runner's problem to prevent, not the reader's.
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))

from run_ps_eval import PROMPT_TEMPLATE, TIERS, parse_response  # noqa: E402
from questions import grade_citation  # noqa: E402

CAVEATS = [
    "MODEL VERSION IS NOT PINNED. The Agent tool's model enum is "
    "sonnet/opus/haiku/fable and resolves to the running Claude Code session's "
    "model. It cannot select a specific Opus release, so this arm cannot answer "
    "a question about one and must not be labelled as if it did.",
    "NO TOKEN ACCOUNTING. The transport exposes no prompt_tokens, "
    "completion_tokens or reasoning_chars, so F90's output-volume rule cannot "
    "be applied to this arm.",
    "WALL TIME IS NOT A LATENCY MEASUREMENT. It includes subagent scheduling and "
    "orchestration, is measured under concurrency, and has no serving config "
    "behind it. Recorded for completeness only.",
    "REASONING CONFIG UNDECLARED AND UNCONTROLLED - the opposite of what Rule 8 "
    "/ F39 require of a serving config.",
    "Contamination guard: the answer keys live in spikes/ps-eval/questions_*.py "
    "and subagents have repo tool access. tool_uses is recorded per question; a "
    "non-zero value anywhere invalidates the run.",
]


def build(tier_name: str, distractors: int | None) -> tuple[str, list[dict]]:
    tier = TIERS[tier_name]
    pack = tier["pack"](distractors) if tier_name == "l3" else tier["pack"]()
    return pack, tier["questions"]


def cmd_prompts(args: argparse.Namespace) -> int:
    pack, questions = build(args.tier, args.distractors)
    if args.expect_pack_chars is not None and len(pack) != args.expect_pack_chars:
        raise SystemExit(
            f"pack is {len(pack)} chars, expected {args.expect_pack_chars}. "
            f"hint: the corpus changed since the run being matched - the arms are "
            f"no longer comparable, reconcile before proceeding"
        )
    out = [
        {
            "id": q["id"],
            "category": q["category"],
            "prompt": PROMPT_TEMPLATE.format(pack=pack, question=q["question"]),
        }
        for q in questions
    ]
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"pack {len(pack)} chars; {len(out)} prompts -> {args.out}", file=sys.stderr)
    return 0


def cmd_grade(args: argparse.Namespace) -> int:
    pack, question_list = build(args.tier, args.distractors)
    questions = {q["id"]: q for q in question_list}
    grade = TIERS[args.tier]["grade"]

    results = []
    for rec in json.loads(Path(args.answers).read_text()):
        q = questions[rec["id"]]
        answer, citation = parse_response(rec["raw"])
        results.append(
            {
                "id": q["id"],
                "category": q["category"],
                "outcome": grade(q, answer),
                "citation_ok": grade_citation(q, citation),
                "citation": citation,
                "answer": answer,
                "finish_reason": "stop",
                "completion_tokens": None,
                "prompt_tokens": None,
                "reasoning_chars": None,
                "subagent_tokens": rec["subagent_tokens"],
                "tool_uses": rec["tool_uses"],
                "wall_s": round(rec["duration_ms"] / 1000, 2),
            }
        )

    by_cat: dict[str, dict[str, int]] = {}
    counts: dict[str, int] = {}
    for r in results:
        c = by_cat.setdefault(r["category"], {"correct": 0, "total": 0})
        c["total"] += 1
        c["correct"] += r["outcome"] == "correct"
        counts[r["outcome"]] = counts.get(r["outcome"], 0) + 1
    walls = [r["wall_s"] for r in results]

    summary = {
        "label": args.label,
        "tier": args.tier,
        "distractors": args.distractors,
        "provider": "claude-code-subagent",
        "model": args.model_label,
        "requested_model_alias": args.model_alias,
        "harness": "Claude Code Agent tool, subagent_type=general-purpose, one "
        "fresh context-free subagent per question, no wrapper around "
        "the prompt",
        "prompt_identical_to": args.prompt_identical_to,
        "pack_chars": len(pack),
        "harness_caveats": CAVEATS,
        "correct": sum(1 for r in results if r["outcome"] == "correct"),
        "total": len(results),
        "citation_valid": sum(1 for r in results if r["citation_ok"]),
        "by_category": by_cat,
        "outcome_counts": counts,
        "latency_note": "orchestration wall time, not model latency",
        "wall_s": {
            "median": round(statistics.median(walls), 2),
            "min": min(walls),
            "max": max(walls),
        },
        "total_tool_uses": sum(r["tool_uses"] for r in results),
        "results": results,
    }
    Path(args.out).write_text(json.dumps(summary, indent=2))
    print(
        f"score {summary['correct']}/{summary['total']}   "
        f"citations {summary['citation_valid']}/{summary['total']}   "
        f"tool_uses total {summary['total_tool_uses']}"
    )
    for r in results:
        print(
            f" {'  ' if r['outcome'] == 'correct' else '<-'} {r['id']:3s} "
            f"{r['category']:16s} {r['outcome']:17s} "
            f"cite={'ok' if r['citation_ok'] else 'no'}  {str(r['answer'])[:44]}"
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run a ps-eval tier through Claude Code subagents and grade it "
        "with the repo's own grader.",
        epilog="examples:\n"
        "  %(prog)s prompts --tier l3 --distractors 0 --expect-pack-chars 13221 --out /tmp/p.json\n"
        "  %(prog)s grade --tier l3 --distractors 0 --answers /tmp/a.json \\\n"
        "      --label e65-opus-subagent-l3n0 --out results/raw/e65-...json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser(
        "prompts", help="emit the tier's prompts for pasting into subagents"
    )
    p.add_argument("--tier", default="l3", choices=sorted(TIERS))
    p.add_argument("--distractors", type=int, default=None)
    p.add_argument(
        "--expect-pack-chars",
        type=int,
        default=None,
        help="abort unless the pack matches this size - guards comparability "
        "against a banked run",
    )
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_prompts)

    g = sub.add_parser("grade", help="grade collected subagent answers")
    g.add_argument("--tier", default="l3", choices=sorted(TIERS))
    g.add_argument("--distractors", type=int, default=None)
    g.add_argument(
        "--answers",
        required=True,
        help="JSON list of {id, raw, subagent_tokens, tool_uses, duration_ms}",
    )
    g.add_argument("--label", required=True)
    g.add_argument(
        "--model-alias", default="opus", help="the alias passed to the Agent tool"
    )
    g.add_argument(
        "--model-label", default="opus (Claude Code session model - NOT version-pinned)"
    )
    g.add_argument(
        "--prompt-identical-to",
        default=None,
        help="path of the banked run whose prompts these match",
    )
    g.add_argument("--out", required=True)
    g.set_defaults(func=cmd_grade)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
