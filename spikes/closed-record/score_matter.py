#!/usr/bin/env python3
# File: score_matter.py
# Purpose: Score a free-prose answer to a closed-record matter against its sealed key.
# Project: sparkbench | Date: 2026-08-12
#
# Overview: The E10 scorer reads markdown table rows; professional answers are prose, so matching
# works differently here. Numeric values are matched on WHOLE TOKENS after normalising separators
# and currency, because "9,100" naively tokenises to ["9", "100"] and a bare "100" would satisfy a
# different proposition. Free-text values are matched as substrings, which is why check_keys.py
# refuses any key whose free-text values overlap.
#
# The contradiction rule is the part worth reading. A trap counts against an answer ONLY when the
# proposition it displaces was not also answered correctly. A model that writes "the EUR 18,000
# fixed fee is not in issue here" has done exactly the right thing with a distractor, and scoring
# that as an error would punish the behaviour the traps exist to reward. This is the same
# distinction the E10 key drew between a trap asserted as data and a trap discussed in prose.
# Schema: schema/key.yaml. Gate: check_keys.py.

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from check_keys import is_numeric, normalise

# A number as a model writes it: digits, optional thousands separators, optional decimals.
NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")

# The heading every matter now requires. Matched loosely on the line because models vary the
# markup ("## Final answer", "**Final Answer**", "FINAL ANSWER:") while keeping the words.
FINAL_ANSWER_RE = re.compile(
    r"^[^\w]*final answer[^\w]*$", re.IGNORECASE | re.MULTILINE
)


def final_answer_block(answer: str) -> tuple[str, bool]:
    """The model's stated answer, and whether it actually supplied one.

    Element matching reads ONLY this block. Measured 2026-08-12, matching anywhere in the answer
    credited Mistral-Small-24B with the correct non-chargeable figure because EUR 1,680 appeared
    in its working, while the figure it actually gave was EUR 1,960. That is the same defect this
    repo recorded against a third-party grader eight days earlier, where numbers in reasoning
    prose satisfied an assertion for an answer that contained no table.

    Falls back to the whole answer when no block is present, and says so, because silently
    scoring one thing as if it were the other is the failure being fixed.
    """
    matches = list(FINAL_ANSWER_RE.finditer(answer))
    if not matches:
        return answer, False
    return answer[matches[-1].end() :], True


def numeric_tokens(text: str) -> set[str]:
    """Every number in the text, in comparison form.

    Matching on this SET rather than on substrings is what keeps "100" from being found inside
    "9,100" - the separator is stripped only after the token boundary has been established.
    """
    return {normalise(m.group()) for m in NUMBER_RE.finditer(text)}


def value_present(value: str, answer: str, tokens: set[str]) -> bool:
    if is_numeric(value):
        return normalise(value) in tokens
    return normalise(value) in normalise(answer)


def score_answer(answer: str, key: dict, truncated: bool | None = None) -> dict:
    """Mark every proposition hit or miss, and record which traps displaced which answer.

    `truncated` is passed in from the measured delivery status where one exists. It does not
    change any verdict - a miss on a truncated answer is not attributable to the model, and the
    caveat has to travel with the coverage figure rather than silently adjust it.
    """
    stated, has_block = final_answer_block(answer)
    stated_tokens = numeric_tokens(stated)

    elements: dict[int, str] = {}
    for el in key["required"]:
        hit = any(value_present(v, stated, stated_tokens) for v in el["values"])
        elements[el["id"]] = "hit" if hit else "miss"

    # Traps read the STATED answer too. A trap value appearing in working is a rejected
    # candidate, which is the behaviour the traps exist to reward - the same reason a distractor
    # quoted alongside the right answer is not a contradiction.
    contradictions = []
    for trap in key.get("traps", []):
        if not value_present(trap["value"], stated, stated_tokens):
            continue
        displaced = trap["displaces"]
        # Present alongside the correct answer means the model discussed the distractor and
        # rejected it, which is the behaviour being tested for, not a failure.
        if elements.get(displaced) == "hit":
            continue
        contradictions.append(
            {"value": trap["value"], "displaces": displaced, "why": trap["why"]}
        )

    hits = sum(1 for v in elements.values() if v == "hit")
    total = len(key["required"])
    return {
        "matter": key["matter"],
        "elements": elements,
        "hits": hits,
        "total": total,
        "coverage": f"{hits}/{total}",
        "contradictions": contradictions,
        "truncated": truncated,
        "truncation_source": "measured" if truncated is not None else "not supplied",
        "coverage_is_lower_bound": bool(truncated),
        "answer_chars": len(answer),
        "stated_answer_chars": len(stated),
        # False means the model ignored the required final-answer block and the whole answer was
        # scored instead. That reading over-credits, so it travels with the score.
        "final_answer_block": has_block,
    }


def load_key(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"key not found: {p}; "
            f"hint: each matter directory holds matter.md and key.yaml - see "
            f"spikes/closed-record/matters/"
        )
    return yaml.safe_load(p.read_text())


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score a matter answer against its sealed key.",
        epilog="Example: python3 score_matter.py --key matters/m01-scope-variation/key.yaml "
        "--answer ans.txt",
    )
    ap.add_argument("--key", required=True)
    ap.add_argument(
        "--answer", required=True, help="file containing the model's answer"
    )
    args = ap.parse_args()
    key = load_key(args.key)
    answer = Path(args.answer).read_text()
    print(json.dumps(score_answer(answer, key), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
