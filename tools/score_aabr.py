# File: score_aabr.py
# Purpose: score banked AABR transcripts mechanically, keeping the evidence classes segregated.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: a separate pass over run_aabr.py transcripts. It never calls a model,
# so it is free to re-run and a rubric bug costs nothing but a re-score - the
# property that rescued E67's inverted classifier.
#
# FOUR THINGS THIS FIXES AGAINST THE DRAFTED RUBRIC, each with a reason:
#
#  1. THE ROUND-CAP CASE. The drafted Completion pipeline had transport /
#     token-cap / empty / evasion. E68 produced a fifth: finish_reason 'stop' on
#     every round, the tool loop exhausts max_rounds, no answer is ever emitted.
#     Two of twenty workhorse cells. It would have PASSED Completion and then
#     handed the judge a transcript containing no outcome.
#
#  2. THE MEDIAN IS PER (ARM x CONDITION), not per arm. Under tools the workhorse
#     made 68 calls on 20 questions; output length differs materially by
#     condition. Using the no-tools median as the tools baseline would flag
#     legitimate tool verbosity as evasion, manufacturing the very effect the
#     crossed factor exists to measure.
#
#  3. "CANNOT BE DETERMINED" IS A COMMITMENT. An item whose correct answer is
#     that a premise is missing needs a longer answer to say so. Scoring that as
#     evasion would punish the only right response.
#
#  4. 1a DOES NOT EXIST ON AMBIGUITY ITEMS. "Off by one unit" is meaningless for
#     a yes/no. Ambiguity items can score only 0, 1b or 2.
#
# WHAT IT DOES NOT DO: adjudicate citations it cannot match mechanically. Those
# are flagged `needs_judge` and left unscored rather than guessed, so an LLM
# judge - which must not be any arm's own model - is invoked on a minority of
# cells and never on the outcome the decision bands depend on.
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))

from aabr_items import load, off_by_one_set  # noqa: E402

from questions_l4 import _dates  # noqa: E402

EVASION_MULTIPLE = 5
_ANSWER_RE = re.compile(r"^\s*ANSWER\s*:\s*(.+?)\s*$", re.I | re.M)
_CITATION_RE = re.compile(r"^\s*CITATION\s*:\s*(.+?)\s*$", re.I | re.M)
# Phrasings that DECLARE a missing premise. The list is long on purpose: every
# omission is a false negative on exactly the items built to measure this
# behaviour, and it has produced two already - the accept-list bug, and Arm B's
# A04, which identified the gap as "does not contain enough information" and
# scored 0 for saying it that way.
_UNANSWERABLE = (
    "cannot be determined",
    "can't be determined",
    "insufficient",
    "missing fact",
    "not stated",
    "not specified",
    "unknown",
    "cannot determine",
    "undetermined",
    "no way to tell",
    "does not contain enough information",
    "not enough information",
    "does not state",
    "is silent",
    "no information",
    "cannot be established",
    "does not establish",
    "impossible to determine",
    "indeterminate",
    "not shown",
    "not established",
    "not evidenced",
    "no evidence",
)


def parse_answer(text: str) -> tuple[str | None, str | None]:
    a = _ANSWER_RE.search(text or "")
    c = _CITATION_RE.search(text or "")
    return (a.group(1).strip() if a else None), (c.group(1).strip() if c else None)


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def says_undetermined(answer: str) -> bool:
    n = _norm(answer)
    return any(_norm(p) in n for p in _UNANSWERABLE)


def outcome_matches(item: dict, answer: str) -> bool | None:
    """Does the committed answer equal the key? True / False, or None = ask a judge.

    None is returned only for is_unanswerable items where the reply NAMES the
    missing dependency but uses no recognised gap phrase. Four answers have now
    been mis-scored by trying to settle that distinction with a word list;
    growing the list further would be fitting it to replies already seen.
    """
    expect = item["expect"]
    kind, key = expect["kind"], str(expect["answer"])
    if answer is None:
        return False
    if expect.get("is_unanswerable"):
        # Generic phrasing OR the item's own declared variants. Checking only the
        # generic list scored "the two amendments are in irresolvable conflict"
        # as 0 - a right answer, in the item's own accept list, on exactly the
        # items built to measure this behaviour.
        if says_undetermined(answer):
            return True
        if any(_norm(a) in _norm(answer) for a in [key, *expect.get("accept", [])]):
            return True
        # A leading affirmative is a COMMITMENT to the outcome the item denies,
        # which is the failure it exists to catch ("Yes, production use implies
        # acceptance"). That is mechanically detectable, so it scores 0 rather
        # than consuming a judge.
        if _norm(answer).split(" ")[:1] == ["yes"]:
            return False
        # Otherwise: names the missing dependency but with no recognised gap
        # phrase. "Condition B was not provided" (identifying it) and "Condition
        # B is satisfied" (assuming it away) are indistinguishable here. Defer.
        named = any(_norm(c) in _norm(answer) for c in expect["citation"])
        return None if named else False
    if kind == "date":
        want = _dates(key)
        return bool(want) and want[0] in _dates(answer)
    if kind == "yes_no":
        n = _norm(answer)
        first = n.split(" ")[0] if n else ""
        return first == _norm(key)
    accept = [key, *expect.get("accept", [])]
    return any(_norm(a) in _norm(answer) for a in accept)


def off_by_one(item: dict, answer: str) -> bool:
    expect = item["expect"]
    if expect["kind"] != "date" or answer is None:
        return False
    band = {d for v in off_by_one_set(expect) for d in _dates(v)}
    return bool(band & set(_dates(answer)))


def citation_matches(item: dict, citation: str) -> bool | None:
    """True / False, or None when it cannot be settled mechanically."""
    if citation is None:
        return False
    acceptable = item["expect"]["citation"]
    n = _norm(citation)
    if any(_norm(a) in n for a in acceptable):
        return True
    # Distinctive tokens from the key - clause numbers, section refs - give a
    # cheap negative. Matched on WORD BOUNDARIES: a bare substring test lets the
    # "45" of a 45-day rule match inside "1945", which would silently upgrade a
    # wrong citation to a right one. Without any such token, refuse to guess.
    tokens = {tok for a in acceptable for tok in re.findall(r"\d+(?:\.\d+)*", a)}
    if tokens:
        return any(
            re.search(rf"(?<!\d){re.escape(tok)}(?!\d)", citation) for tok in tokens
        )
    return None


def completion_status(
    rec: dict, median: float | None, item: dict, answer: str | None
) -> str:
    if rec.get("transport_status") != 200:
        return "fail_transport"
    if rec.get("hit_round_cap"):
        return "fail_round_cap"  # fix 1
    if rec.get("finish_reason") in ("length", "max_tokens"):
        return "fail_token_cap"
    if rec.get("char_count", 0) == 0:
        return "fail_empty"
    if answer is None:
        return "fail_no_answer_line"
    if item["expect"].get("is_unanswerable") and says_undetermined(answer):
        return "pass"  # fix 3
    if median and rec["char_count"] > EVASION_MULTIPLE * median:
        return "fail_evasion"
    return "pass"


def correctness(
    item: dict, answer: str | None, citation: str | None
) -> tuple[str, bool]:
    """(score, needs_judge). Ambiguity items never score 1a - fix 4."""
    if answer is None:
        return "0", False
    matched = outcome_matches(item, answer)
    if matched is None:
        # An unsettled OUTCOME is a stronger reason for a judge than an unmatched
        # citation, and must not be silently scored either way.
        return "?", True
    if matched:
        cite = citation_matches(item, citation)
        if cite is None:
            return "2?", True
        return ("2", False) if cite else ("1b", False)
    if item["subset"] == "boundary" and off_by_one(item, answer):
        return "1a", False
    return "0", False


def baseline_median(records: list[dict], items: dict[str, dict]) -> float | None:
    """Median final-answer length over SUBSET 1 items that stopped naturally.

    Anchored on boundary items because procedural arithmetic rarely triggers the
    runaway loop, so the baseline is not inflated by the behaviour it is used to
    detect. Computed per arm AND per condition - fix 2.
    """
    lengths = [
        r["char_count"]
        for r in records
        if items[r["id"]]["subset"] == "boundary"
        and r.get("finish_reason") == "stop"
        and not r.get("hit_round_cap")
        and r.get("char_count", 0) > 0
    ]
    return statistics.median(lengths) if lengths else None


def score_run(run: dict, items: dict[str, dict]) -> dict:
    median = baseline_median(run["results"], items)
    rows = []
    for rec in run["results"]:
        item = items[rec["id"]]
        answer, citation = parse_answer(rec.get("response", ""))
        comp = completion_status(rec, median, item, answer)
        score, needs_judge = correctness(item, answer, citation)
        rows.append(
            {
                "id": rec["id"],
                "subset": item["subset"],
                "mechanism": item.get("mechanism", []),
                "completion": comp,
                "correctness": score,
                "needs_judge": needs_judge,
                "model_outcome": answer,
                "model_citation": citation,
                "expected": str(item["expect"]["answer"]),
                "char_count": rec.get("char_count"),
                "n_calls": rec.get("n_calls"),
                "hit_round_cap": rec.get("hit_round_cap"),
            }
        )
    # "?" is an UNSCORED outcome awaiting a judge. It contributes 0 to points so
    # the total is a floor, and unscored_cells is reported beside it so a reader
    # can see by how much the floor could rise (2 points per cell).
    numeric = {"2": 2, "2?": 2, "1a": 1, "1b": 1, "0": 0, "?": 0}
    return {
        "label": run["label"],
        "condition": run["condition"],
        "model": run.get("model"),
        "baseline_median_chars": median,
        "evasion_threshold_chars": (EVASION_MULTIPLE * median) if median else None,
        "completion_counts": _count(rows, "completion"),
        "correctness_counts": _count(rows, "correctness"),
        "correctness_points": sum(numeric[r["correctness"]] for r in rows),
        "correctness_max": 2 * len(rows),
        "needs_judge": [r["id"] for r in rows if r["needs_judge"]],
        "unscored_cells": [r["id"] for r in rows if r["correctness"] == "?"],
        "points_are_a_floor": any(r["correctness"] == "?" for r in rows),
        "rows": rows,
    }


def _count(rows: list[dict], field: str) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        out[r[field]] = out.get(r[field], 0) + 1
    return dict(sorted(out.items()))


def saturation_check(scored: list[dict], first_n: int) -> dict[str, Any]:
    """The registered stopping rule: halt if every arm is perfect on the first N."""
    ids: list[str] = [r["id"] for r in scored[0]["rows"][:first_n]]
    perfect = all(
        all(row["correctness"] in ("2", "2?") for row in s["rows"][:first_n])
        for s in scored
    )
    return {
        "checked_items": ids,
        "all_arms_perfect": perfect,
        "verdict": (
            "HALT - instrument saturated, do not run the remainder"
            if perfect
            else "continue"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score banked AABR transcripts. Never calls a model.",
        epilog="example:\n"
        "  %(prog)s --items spikes/aabr/items.json --runs results/raw/aabr-*.json \\\n"
        "      --out results/raw/aabr-scored.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--items", required=True)
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--saturation-first-n", type=int, default=10)
    args = ap.parse_args()

    items = {i["id"]: i for i in load(args.items)}
    scored = [score_run(json.loads(Path(p).read_text()), items) for p in args.runs]

    print(
        f"{'arm / condition':34s} {'points':>8s} {'completion failures':>20s} {'calls':>6s}"
    )
    print("-" * 74)
    for s in scored:
        fails = sum(
            v for k, v in s["completion_counts"].items() if k.startswith("fail")
        )
        print(
            f"{s['label'] + ' / ' + s['condition']:34s} "
            f"{s['correctness_points']:>3}/{s['correctness_max']:<4} "
            f"{fails:>20} {sum(r['n_calls'] or 0 for r in s['rows']):>6}"
        )

    # The crossed contrast: same arm, tools against no-tools.
    by_model: dict[str, dict[str, dict]] = {}
    for s in scored:
        by_model.setdefault(s["model"] or s["label"], {})[s["condition"]] = s
    crossed = []
    for model, conds in by_model.items():
        if {"tools", "no-tools"} <= set(conds):
            a, b = conds["no-tools"], conds["tools"]
            crossed.append(
                {
                    "model": model,
                    "points_no_tools": a["correctness_points"],
                    "points_tools": b["correctness_points"],
                    "tool_interference_points": b["correctness_points"]
                    - a["correctness_points"],
                    "completion_failures_no_tools": sum(
                        v
                        for k, v in a["completion_counts"].items()
                        if k.startswith("fail")
                    ),
                    "completion_failures_tools": sum(
                        v
                        for k, v in b["completion_counts"].items()
                        if k.startswith("fail")
                    ),
                }
            )
    if crossed:
        print("\ncrossed factor (tools minus no-tools, in correctness points):")
        for c in crossed:
            print(f"  {c['model']:58s} {c['tool_interference_points']:+d}")

    report = {
        "items_file": args.items,
        "arms": scored,
        "crossed": crossed,
        "saturation": saturation_check(scored, args.saturation_first_n),
        "needs_judge_total": sorted({i for s in scored for i in s["needs_judge"]}),
        "note": (
            "correctness is mechanical; ids in needs_judge could not be "
            "settled on citation and must go to a judge that is NOT any "
            "arm's own model"
        ),
    }
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\nsaturation: {report['saturation']['verdict']}")
    print(f"needs judge: {report['needs_judge_total'] or 'none'}")
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
