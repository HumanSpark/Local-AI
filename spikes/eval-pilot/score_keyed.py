#!/usr/bin/env python3
# File: score_keyed.py
# Purpose: Score a model answer against a ground-truth key, so a single answer can be
#          measured without an opponent.
# Project: sparkbench | Date: 2026-08-11 (v2 2026-08-20)
#
# Overview: Pairwise judging cannot score one model (there is always an opponent) and
# cannot tell "both right" from "both wrong the same way". Keyed scoring can: a key
# element either appears in the answer or it does not. extract_rows() pulls markdown
# table rows out of free-form output; score_answer() marks each required element
# hit/miss/contradicted against SETS of acceptable surface forms, and records two
# contradiction classes separately - trap values (present in the source but not
# measurements) and wrong-depth values (real measurements, wrong condition).
# Key format + derivation: keys/e10-full-table.yaml.
# Plan: docs/plans/2026-08-11-benchmark-instrumentation-uplift.md task 3.
#
# v2 FIXES THE F95 TYPOGRAPHY DEFECT, PROSPECTIVELY. v1 compared aliases with a
# plain lowercased substring test, so a model writing "Qwen3-14B" with U+2011
# NON-BREAKING HYPHEN named a model this scorer could not see, and a value
# written "6,223" or "6 223" (NARROW NO-BREAK SPACE) extracted as two numbers
# rather than one. tools/score_kw_eval.py met that defect for real on
# 2026-08-20 and one arm's score moved 11/24 -> 18/24 on re-scoring the SAME
# completions. This file had the identical exposure and had simply not yet met
# a model that writes that way.
#
# NO BANKED RESULT WAS REGENERATED OR SILENTLY RESTATED. Every figure in
# results/keyed-vs-pairwise.md and results/closed-record*.md was produced by v1
# and still says v1. Re-scoring anything with v2 must record which version
# produced which number - score_answer() returns `scorer_version` for exactly
# that. The v1 -> v2 re-score of the stored E10 answers is recorded in
# results/keyed-vs-pairwise.md.

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from typography import TYPOGRAPHY_VERSION, fold, fold_digit_groups  # noqa: E402

#   v1  2026-08-11  ASCII-exact alias matching, comma-splitting number extraction
#   v2  2026-08-20  F95 typography fold applied to the answer before rows are
#                   extracted, to aliases before they are compared, and to digit
#                   group separators before numbers are read.
SCORER_VERSION = "keyed-v2-2026-08-20"

# A markdown table row: leading pipe, at least two cells. Separator rows (|---|) are
# dropped by the caller, not here, so the pattern stays readable.
ROW_RE = re.compile(r"^\s*\|(?P<cells>.+)\|\s*$")
NUM_RE = re.compile(r"\d+\.\d+|\d+")


def extract_rows(answer: str) -> list[tuple[str, str]]:
    """Return (model_text, value_text) for each markdown table row in the answer.

    Free-form output is the normal case here - models wrap tables in reasoning prose,
    and two of the five real E10 answers contain no table at all. That returns [] and
    scores as zero coverage rather than raising: an answer with no table is a real
    result about the model, not a malformed input.
    """
    rows: list[tuple[str, str]] = []
    for line in fold(answer).splitlines():
        m = ROW_RE.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.group("cells").split("|")]
        if len(cells) < 2:
            continue
        if set("".join(cells)) <= set("-: "):  # separator row
            continue
        model, value = cells[0], cells[1]
        if not model or model.lower() in {"model", "name"}:  # header
            continue
        rows.append((model, value))
    return rows


def _numbers(text: str) -> set[str]:
    """Numbers in the text, with digit-group separators folded first.

    v1 read "6,223" as {"6", "223"} and "6 223" (NARROW NO-BREAK SPACE) the
    same way, so a correct value written the way a model actually writes it
    never matched a key value of "6223".
    """
    return set(NUM_RE.findall(fold_digit_groups(fold(text))))


def looks_truncated(answer: str) -> bool:
    """True when the answer stops mid-token rather than finishing.

    This is a HEURISTIC and a weak one. Prefer the measured verdict from
    delivery.classify_delivery(), which reads the server's own token counts, and pass it
    in as score_answer(truncated=...).

    Measured 2026-08-12 across the 136 stored pilot answers, the original punctuation-only
    rule fired 114 times against 24 real ceiling hits. It called a bare "4096" truncated
    because a number does not end in a full stop. A short answer carrying no sentence
    structure is not evidence of anything, so it is no longer treated as evidence.
    """
    tail = fold(answer).rstrip()
    if not tail:
        return True
    if tail.endswith((".", "!", "?", "|", "`", ")", '"', "'")):
        return False
    # A bare value or short phrase is a complete answer to a short question. Only prose long
    # enough to have sentence structure can be judged mid-token by its last character.
    return len(tail.split()) >= 6


def score_answer(answer: str, key: dict, truncated: bool | None = None) -> dict:
    """Mark every required element hit/miss/contradicted and collect contradictions.

    An element is a HIT when any accepted model alias and any accepted value share a
    row. It is CONTRADICTED when an alias appears with some other number - a confident
    wrong value is a different failure from silence and must not collapse into "miss".

    `truncated` (auto-detected when not given) does NOT change any element verdict -
    it is reported alongside them, because a miss on a truncated answer is not
    attributable to the model and any coverage figure derived from one is a lower
    bound, not a measurement.
    """
    rows = extract_rows(answer)
    elements: dict[int, str] = {}
    for el in key["required"]:
        verdict = "miss"
        for model_text, value_text in rows:
            low = fold(model_text).lower()
            if not any(fold(a).lower() in low for a in el["aliases"]):
                continue
            nums = _numbers(value_text)
            if any(v in nums for v in el["values"]):
                verdict = "hit"
                break
            if nums:  # named the model, asserted a different number
                verdict = "contradicted"
        elements[el["id"]] = verdict

    # Contradictions are only counted when asserted AS TABLE DATA. A model that
    # discusses a trap value in prose to explain why it excluded it has done the
    # right thing, and scoring that as an error would punish the correct behaviour.
    row_numbers: set[str] = set()
    for _, value_text in rows:
        row_numbers |= _numbers(value_text)
    contradictions = [
        {"kind": "trap", "value": t["value"], "why": t["why"]}
        for t in key.get("traps", [])
        if t["value"] in row_numbers
    ]
    contradictions += [
        {"kind": "wrong_depth", "value": v, "why": "depth-8192 measurement reported as depth-0"}
        for v in key.get("wrong_depth", [])
        if v in row_numbers
    ]

    hits = sum(1 for v in elements.values() if v == "hit")
    total = len(key["required"])
    # A measured verdict and a guess about punctuation are not the same kind of claim, and a
    # score that cannot tell them apart invites the second to be read as the first. That is how
    # the E10 truncation finding came to attribute all five answers to one mechanism.
    if truncated is None:
        trunc = looks_truncated(answer)
        source = "heuristic"
    else:
        trunc = truncated
        source = "measured"
    return {
        "scorer_version": SCORER_VERSION,
        "typography_version": TYPOGRAPHY_VERSION,
        "elements": elements,
        "hits": hits,
        "total": total,
        "coverage": f"{hits}/{total}",
        "contradictions": contradictions,
        "rows_found": len(rows),
        "truncated": trunc,
        "truncation_source": source,
        "coverage_is_lower_bound": trunc,
    }


def load_key(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"key file not found: {p}; "
            f"hint: keys live in spikes/eval-pilot/keys/ - see e10-full-table.yaml"
        )
    return yaml.safe_load(p.read_text())


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score an answer against a ground-truth key.",
        epilog="Example: python3 score_keyed.py --key keys/e10-full-table.yaml --answer ans.md",
    )
    ap.add_argument("--key", required=True, help="key YAML (see keys/)")
    ap.add_argument("--answer", required=True, help="file containing the model answer")
    args = ap.parse_args()
    key = load_key(args.key)
    answer = Path(args.answer).read_text()
    print(json.dumps(score_answer(answer, key), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
