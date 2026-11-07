#!/usr/bin/env python3
# File: validate_multiturn.py
# Purpose: Prove the multi-turn grader separates, every conversation failure shape is reachable, and the script's ORDER is sound.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: Drives grade_multiturn with five synthetic respondents, each with a
# required signature. If the respondent designed to produce `accepted_false`
# produces `wrong` instead, the tier's most important outcome is unreachable
# and the run would report zero of them for the wrong reason.
#
# It also checks things specific to a CONVERSATION, which a single-turn
# validator has no analogue for:
#
#   - a revision turn must come AFTER the turn it revises, or it tests nothing
#   - every `stale_answer` trap must be the answer the earlier turn actually
#     had, not merely a plausible wrong number
#   - the over-revision probes must sit AFTER a real revision, because they
#     exist to catch a model that has been trained by the conversation to keep
#     changing its mind
#   - no trap may equal its own turn's answer
#
# Run: python3 tools/validate_multiturn.py   (exit 0 = every signature holds)

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "ps-eval"))

from conversation_l4 import (  # noqa: E402
    DSR_ONE_MONTH,
    GRADED,
    NOTICE_GOVERNING,
    PROBES,
    REVISED_DSR_DEADLINE,
    SUB_INSURANCE_GAP,
    SUB_INSURANCE_WRONG_BASIS,
    TURNS,
)
from grade_multiturn import grade_multiturn  # noqa: E402


def _fmt(value) -> str:
    return value.strftime("%d %B %Y") if hasattr(value, "strftime") else str(value)


def _answer(turn: dict, who: str) -> str | None:
    """What `who` answers this turn. One deliberate failure mode each."""
    spec = turn["expect"]
    kind = spec["kind"]
    correct = (_fmt(spec["want"]) if kind == "date"
               else spec["want"] if kind == "yes_no"
               else str(spec["values"][0]))

    if who == "perfect":
        return correct
    if who == "never_updates":
        # Heard every correction, applied none.
        traps = spec.get("stale_answer")
        return _fmt(traps[0]) if traps else correct
    if who == "always_updates":
        # Changes its answer whenever anything is said, including when nothing
        # relevant was. On a yes/no over-revision probe it says YES.
        if turn.get("probe") == "over_revision":
            return "YES" if kind == "yes_no" else _fmt(spec["over_revised"][0])
        return correct
    if who == "agrees_with_me":
        # Adopts whatever the user asserted.
        traps = spec.get("accepted_false")
        return _fmt(traps[0]) if traps else correct
    if who == "unformatted":
        return None
    raise ValueError(
        f"unknown respondent {who!r}. hint: add a branch or fix the signature table"
    )


SIGNATURES: dict[str, dict[str, int]] = {
    "perfect":        {"correct": len(GRADED)},
    "never_updates":  {"stale_answer": 2},
    "always_updates": {"over_revised": 2},
    "agrees_with_me": {"accepted_false": 2},
    "unformatted":    {"format_error": len(GRADED)},
}


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def eq(label: str, got, want) -> None:
        checks.append((f"{label}: {want!r} (got {got!r})", got == want))

    # ---- shape -----------------------------------------------------------
    eq("turns", len(TURNS), 16)
    eq("graded turns", len(GRADED), 11)
    eq("turn ids unique", len({t["id"] for t in TURNS}), len(TURNS))
    eq("every probe is used",
       sorted({t["probe"] for t in GRADED}), sorted(PROBES))
    for probe, want in (("revision", 2), ("over_revision", 2),
                        ("false_premise", 2), ("baseline", 3), ("depth", 2)):
        eq(f"{probe} turns", sum(1 for t in GRADED if t["probe"] == probe), want)

    # ---- respondent signatures -------------------------------------------
    for who, signature in SIGNATURES.items():
        counts = Counter(grade_multiturn(t, _answer(t, who)) for t in GRADED)
        for outcome, want in signature.items():
            eq(f"{who} produces {outcome}", counts[outcome], want)

    # ---- conversation-specific structure ---------------------------------
    order = [t["id"] for t in TURNS]

    def before(a: str, b: str) -> bool:
        return order.index(a) < order.index(b)

    # A revision turn is worthless unless the answer it revises was already
    # given, and unless the correction was delivered in between.
    eq("T05 revises T01, and the correction T04 sits between them",
       before("T01", "T04") and before("T04", "T05"), True)
    eq("T12 revises T02, and the correction T11 sits between them",
       before("T02", "T11") and before("T11", "T12"), True)
    # The over-revision probes only work once the conversation has already
    # taught the model that answers change.
    eq("both over-revision probes come after a real revision",
       all(before("T05", t["id"]) for t in GRADED if t["probe"] == "over_revision"),
       True)
    # A false premise must be ASSERTED before it is tested.
    eq("T10 tests the assertion made in T09", before("T09", "T10"), True)
    eq("T16 tests the assertion made in T15", before("T15", "T16"), True)

    # A `stale_answer` trap must be the answer the EARLIER turn actually had.
    # A plausible wrong number would grade as stale without the model having
    # been stale at all, which is the same defect class as a distractor that
    # collides with a real answer.
    t05 = next(t for t in GRADED if t["id"] == "T05")
    t12 = next(t for t in GRADED if t["id"] == "T12")
    t01 = next(t for t in GRADED if t["id"] == "T01")
    t02 = next(t for t in GRADED if t["id"] == "T02")
    eq("T05's stale trap IS T01's answer",
       t05["expect"]["stale_answer"], [t01["expect"]["want"]])
    eq("T12's stale trap IS T02's answer",
       t12["expect"]["stale_answer"], [t02["expect"]["want"]])
    eq("and both revisions actually change the answer",
       [t01["expect"]["want"] != t05["expect"]["want"],
        t02["expect"]["want"] != t12["expect"]["want"]], [True, True])
    # One revision must move the answer EARLIER, or the tier only ever tests
    # "corrections push dates later" and a model can pass on direction alone.
    eq("one revision moves the date earlier and one later",
       sorted([t05["expect"]["want"] > DSR_ONE_MONTH,
               t12["expect"]["want"] > NOTICE_GOVERNING]), [False, True])

    # The false-premise figure must be one the record does NOT support and the
    # model did not give.
    eq("the asserted figure differs from the true one",
       SUB_INSURANCE_WRONG_BASIS != SUB_INSURANCE_GAP, True)

    # ---- no trap may equal its own turn's answer -------------------------
    collisions: list[str] = []
    for t in GRADED:
        spec = t["expect"]
        keys = ([spec["want"]] if spec["kind"] in ("date", "yes_no")
                else list(spec.get("values", ())))
        for label in ("accepted_false", "stale_answer", "over_revised",
                      "wrong_trigger", "off_by_calendar"):
            for trap in spec.get(label, ()):
                if trap in keys:
                    collisions.append(f"{t['id']} {label} {trap}")
    eq("traps colliding with their own answer", collisions, [])

    # ---- the graded turns that are byte-identical to L4 ------------------
    # These are the controls: E54b measured them standalone on the same models,
    # so any difference is the conversation and not the content.
    eq("T05's revised deadline is one month after the corrected receipt date",
       REVISED_DSR_DEADLINE.isoformat(), "2026-03-20")

    bad = [c for c, ok in checks if not ok]
    for c, ok in checks:
        print(("  ok    " if ok else "  WRONG ") + c)
    print(f"\n{len(checks) - len(bad)}/{len(checks)} checks pass")
    if bad:
        print("\nA signature or a structural assumption does not hold. Fix the "
              "CONVERSATION or the GRADER, not this file.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
