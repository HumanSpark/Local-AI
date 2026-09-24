#!/usr/bin/env python3
# File: validate_ps_eval_l4.py
# Purpose: Prove the L4 graders separate, every named trap is reachable, and no key collides with a figure in the pack.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: A grader is an unmeasured instrument until it is driven with
# answers whose outcome is known in advance. This drives grade_answer_l4 with
# six synthetic respondents, each with a REQUIRED SIGNATURE - a perfect one,
# and five that fail in exactly one named way each. If a respondent designed
# to produce `off_by_calendar` produces `wrong` instead, the trap is not
# reachable and the tier's headline number would be silently zero.
#
# It also carries the check E48 taught, which is the one no score can reveal:
# an answer key that coincides with a figure printed in the pack lets a model
# that reads a number straight off the page grade as `correct`. That is not a
# hypothetical here - the insurance shortfall was 1,000,000 - 500,000 =
# 500,000 in the first draft, exactly the subcontract's own cover figure, and
# this check is what would have caught it.
#
# Run: python3 tools/validate_ps_eval_l4.py   (exit 0 = every signature holds)

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "ps-eval"))

from corpus_l4 import build_pack_l4  # noqa: E402
from questions_l4 import (  # noqa: E402
    BREACH_HOLIDAY_TRAP,
    BREACH_WEEKEND_TRAP,
    CATEGORIES_L4,
    DSR_SEQUENTIAL_TRAP,
    FEES_TO_TERMINATION,
    FIRST_ANNIVERSARY,
    INTEREST,
    LIMITATION_FROM_DISCOVERY,
    NOTICE_PLAIN,
    QUESTIONS_L4,
    SUB_INSURANCE_ACTUAL,
    SUB_INSURANCE_GAP,
    SUB_INSURANCE_REQUIRED,
    SUB_INSURANCE_WRONG_BASIS,
    SUB_RECORDS_ACTUAL_YEARS,
    SUB_RECORDS_REQUIRED_YEARS,
    SUB_RECORDS_SHORTFALL_YEARS,
    _dates,
    grade_answer_l4,
)


def _fmt(value) -> str:
    """A date as a professional would write it; anything else as-is."""
    return value.strftime("%d %B %Y") if hasattr(value, "strftime") else str(value)


def _answer(q: dict, respondent: str) -> str | None:
    """What `respondent` answers question `q`.

    Each branch is a deliberate, single failure mode. `perfect` returns the
    key; every other respondent returns the named trap where the question
    defines one and the correct answer where it does not, so the signature
    counts below isolate one outcome at a time.
    """
    spec = q["expect"]
    kind = spec["kind"]
    correct = (_fmt(spec["want"]) if kind == "date"
               else spec["want"] if kind in ("yes_no", "choice")
               else str(spec["values"][0]) if kind == "numeric"
               else "The pack does not state this.")

    if respondent == "perfect":
        return correct

    if respondent == "calendar_blind":
        # Right method, wrong count - never suspends a clock, never rolls a
        # month back, never notices a rate change mid-period.
        traps = spec.get("off_by_calendar")
        return _fmt(traps[0]) if traps else correct

    if respondent == "wrong_start":
        # Counts perfectly, from the wrong event.
        traps = spec.get("wrong_trigger")
        return _fmt(traps[0]) if traps else correct

    if respondent == "fault_finder":
        # Primed to find something wrong with the contract. Answers YES to
        # every yes/no question; correct elsewhere. This is the respondent the
        # `defect_absent` category exists to catch.
        return "YES" if kind == "yes_no" else correct

    if respondent == "quotes_the_page":
        # Reads a figure off the page instead of computing a difference.
        traps = spec.get("partial")
        return str(traps[0]) if traps else correct

    if respondent == "unformatted":
        # Never emits a parseable ANSWER line at all.
        return None

    raise ValueError(
        f"unknown respondent {respondent!r}. "
        f"hint: add a branch here or fix the signature table"
    )


# Each respondent's REQUIRED signature: the outcome counts it must produce.
# Only the outcomes that define the respondent are asserted; the rest are
# free, because pinning every cell would make the table a copy of the
# implementation rather than a check on it.
SIGNATURES: dict[str, dict[str, int]] = {
    "perfect":         {"correct": len(QUESTIONS_L4)},
    "calendar_blind":  {"off_by_calendar": 8},
    "wrong_start":     {"wrong_trigger": 3},
    "fault_finder":    {"wrong": 2},
    "quotes_the_page": {"partial": 3},
    "unformatted":     {"format_error": len(QUESTIONS_L4)},
}


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def eq(label: str, got, want) -> None:
        checks.append((f"{label}: {want!r} (got {got!r})", got == want))

    pack = build_pack_l4()

    # ---- the tier's own shape --------------------------------------------
    eq("questions", len(QUESTIONS_L4), 15)
    eq("ids are unique", len({q["id"] for q in QUESTIONS_L4}), 15)
    eq("every category is used",
       sorted({q["category"] for q in QUESTIONS_L4}), sorted(CATEGORIES_L4))
    eq("defect_absent has TWO items, so a coin toss cannot pass it",
       sum(1 for q in QUESTIONS_L4 if q["category"] == "defect_absent"), 2)
    # F60's claim is that walked periods are what discriminate, so the tier
    # has to be mostly walks or it is not a test of the theory.
    walkers = sum(1 for q in QUESTIONS_L4
                  if q["expect"].get("off_by_calendar") or q["expect"].get("wrong_trigger"))
    eq("questions carrying a walked-period trap", walkers, 9)

    # ---- respondent signatures -------------------------------------------
    for name, signature in SIGNATURES.items():
        counts = Counter(grade_answer_l4(q, _answer(q, name)) for q in QUESTIONS_L4)
        for outcome, want in signature.items():
            eq(f"{name} produces {outcome}", counts[outcome], want)

    # ---- no trap may equal its own question's answer ----------------------
    # Added with the 2026-08-17 off-by-one traps. A trap list is generated now
    # rather than typed, and a generated trap that lands on the key would grade
    # a CORRECT answer as a named failure - the inverse of the collision below
    # and just as invisible.
    self_collisions: list[str] = []
    for q in QUESTIONS_L4:
        spec = q["expect"]
        key = spec.get("want") if spec["kind"] == "date" else None
        keys = [key] if key is not None else list(spec.get("values", ()))
        for label in ("off_by_calendar", "wrong_trigger", "partial"):
            for trap in spec.get(label, ()):
                if trap in keys:
                    self_collisions.append(f"{q['id']} {label} {trap}")
    eq("traps that collide with their own answer", self_collisions, [])

    # ---- E48's collision check -------------------------------------------
    # Every number printed in the pack, and every date. A key that appears in
    # the pack verbatim can be answered by copying rather than computing.
    pack_numbers = {
        float(m.replace(",", ""))
        for m in re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", pack)
    }
    pack_dates = set(_dates(pack))
    collisions: list[str] = []
    for q in QUESTIONS_L4:
        spec = q["expect"]
        if spec["kind"] == "numeric":
            for value in spec["values"]:
                # Small integers (a count of years, a clause number) are
                # meant to appear in the pack; only a computed FIGURE that
                # can be copied is a collision.
                if value >= 1000 and float(value) in pack_numbers:
                    collisions.append(f"{q['id']} numeric {value}")
        elif spec["kind"] == "date":
            if spec["want"] in pack_dates:
                collisions.append(f"{q['id']} date {spec['want']}")
    eq("answer keys that can be copied straight off the pack", collisions, [])

    # The sweep above exempts values below 1,000, because a clause number or a
    # count of years is MEANT to appear in the pack. That exemption is exactly
    # where the second collision hid, so the two difference questions are
    # asserted individually: a key that equals either operand is answerable by
    # copying, and no score would ever reveal it.
    eq("records shortfall differs from both operands",
       SUB_RECORDS_SHORTFALL_YEARS not in (SUB_RECORDS_REQUIRED_YEARS,
                                           SUB_RECORDS_ACTUAL_YEARS), True)
    eq("insurance shortfall differs from both operands",
       SUB_INSURANCE_GAP not in (SUB_INSURANCE_REQUIRED, SUB_INSURANCE_ACTUAL), True)
    eq("records shortfall is 6 - 2", SUB_RECORDS_SHORTFALL_YEARS, 4)

    # ---- the traps that matter most are distinct from each other ----------
    eq("insurance gap and wrong-basis gap differ",
       SUB_INSURANCE_GAP != SUB_INSURANCE_WRONG_BASIS, True)
    eq("N1 and N2 have different answers",
       NOTICE_PLAIN != FIRST_ANNIVERSARY, True)
    eq("breach traps are distinct days",
       len({BREACH_WEEKEND_TRAP.date(), BREACH_HOLIDAY_TRAP.date()}), 2)
    eq("the extension trap differs from the key", DSR_SEQUENTIAL_TRAP.day, 28)
    eq("interest-only is a partial, not the key", INTEREST != FEES_TO_TERMINATION, True)
    eq("limitation-from-discovery is a different year",
       LIMITATION_FROM_DISCOVERY.year, 2029)

    bad = [c for c, ok in checks if not ok]
    for c, ok in checks:
        print(("  ok    " if ok else "  WRONG ") + c)
    print(f"\npack: {len(pack):,} chars")
    print(f"{len(checks) - len(bad)}/{len(checks)} checks pass")
    if bad:
        print("\nA grader signature does not hold. Fix the QUESTIONS or the GRADER, "
              "not this file, unless the signature itself was wrong.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
