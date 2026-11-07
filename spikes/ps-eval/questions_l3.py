# File: questions_l3.py
# Purpose: The L2 questions, rescoped to name their agreement, plus the wrong_document outcome.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: L3 changes exactly ONE variable against L2 - the size of the pack.
# The questions, the reasoning they demand and the correct answers are
# identical. Every question is derived from QUESTIONS_L2 here rather than
# retyped, so the two tiers cannot drift apart: if an L2 answer is amended,
# L3 inherits the amendment automatically.
#
# TWO THINGS ARE ADDED, AND ONLY TWO.
#
# 1. SCOPE. Each question names the agreement and its parties. In L2 the pack
#    held one services agreement, so "the Agreement" was unambiguous. In L3 it
#    holds ten, all with their own liability caps and retention periods, and
#    an unscoped question stops having a single right answer. This is E38
#    AMENDMENT 1's lesson applied BEFORE the fact: V1 was ambiguous because a
#    document added for other questions changed what it could mean, and nine
#    added documents do that to every question at once.
#
# 2. `wrong_document` - a NEW outcome, and the signature failure of this tier.
#    Distractor figures are drawn from ranges disjoint from the real pack
#    (asserted at import in corpus_l3), so an answer of 275,000 is not merely
#    wrong: it is the liability cap from the Harbourgate agreement, and it
#    says the model retrieved fluently from the wrong contract. That is the
#    error a firm actually makes with a folder of similar agreements, and
#    folding it into a generic `wrong` would hide the one thing this tier
#    exists to measure.

from __future__ import annotations

import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_l3 import DISTRACTOR_FIGURES  # noqa: E402
from questions_l2 import CATEGORIES_L2, QUESTIONS_L2, _is_decline  # noqa: E402
from questions import _matches, _numbers  # noqa: E402

CATEGORIES_L3 = list(CATEGORIES_L2)

# The agreement every question refers to, named the way a professional would
# name it in a file note.
SCOPE = ("the Master Services Agreement dated 1 March 2024 between Northwind "
         "Logistics Limited and Calderwood Advisory LLP, as amended")

# Which distractor figure family could be confused with each question's
# answer. Stated explicitly per question rather than inferred: a wrong guess
# here would attach the wrong trap and mislabel a failure, and there are only
# twelve of them.
FIGURE_KIND: dict[str, str | None] = {
    "D1": "retainer", "D2": "cap", "D3": "retainer",
    "V1": "retention", "V2": None,
    "P1": "retention", "P2": "response",
    "M1": "retainer", "M2": "retainer", "M3": "cap",
    "N1": None, "Z1": None,
}

# How each question is rescoped. The reasoning is untouched; only the noun
# phrase identifying the agreement changes.
RESCOPE: dict[str, str] = {
    "D1": (f"Under {SCOPE}, what monthly retainer was payable to Calderwood "
           "Advisory for services delivered in September 2024? Give the amount in EUR."),
    "D2": (f"Under {SCOPE}, what was Calderwood Advisory's aggregate liability cap "
           "as at 31 March 2025? Give the amount in EUR."),
    "D3": (f"Under {SCOPE}, what monthly retainer is payable to Calderwood Advisory "
           "for services delivered in May 2026? Give the amount in EUR."),
    "V1": (f"Under {SCOPE}, and disregarding the Client's internal policy, for how "
           "many months may Calderwood Advisory retain Client personal data following "
           "a termination occurring in February 2026?"),
    "V2": (f"Under clause 4.2 of {SCOPE}, is 'loss of profit' still excluded? "
           "Answer YES or NO."),
    "P1": ("A termination of the Calderwood Advisory engagement occurs in February "
           "2026. Within what period must Calderwood Advisory delete Client personal "
           "data? Give the period that actually governs."),
    "P2": ("Within how many business days must Calderwood Advisory respond to a query "
           "the Client has classified as critical? Give the period that actually "
           "governs."),
    "M1": (f"Under {SCOPE}, what is the total retainer invoiced to the Client by "
           "Calderwood Advisory for the calendar year 2024? That engagement commenced "
           "on 1 April 2024. Give the amount in EUR."),
    "M2": (f"Under {SCOPE}, what is the total retainer payable to Calderwood Advisory "
           "from 1 January 2026 to the end of the Engagement Period? Give the amount "
           "in EUR."),
    "M3": ("Expressed as a multiple of the monthly retainer payable to Calderwood "
           "Advisory in May 2026, how large is Calderwood Advisory's aggregate "
           "liability cap? Give the multiple to one decimal place."),
    "N1": None,  # already self-contained; the five options name their own scope
    "Z1": ("Under the Calderwood Advisory engagement, is VAT chargeable on a service "
           "credit issued under clause 6.3?"),
}


def _build() -> list[dict]:
    out = []
    for q in QUESTIONS_L2:
        n = copy.deepcopy(q)
        rescoped = RESCOPE.get(q["id"])
        if rescoped:
            n["question"] = rescoped
        kind = FIGURE_KIND[q["id"]]
        if kind and n["expect"]["kind"] == "numeric":
            n["expect"]["wrong_document"] = list(DISTRACTOR_FIGURES[kind])
        out.append(n)
    return out


QUESTIONS_L3: list[dict] = _build()


def grade_answer_l3(question: dict, answer: str | None) -> str:
    """As grade_answer_l2, plus `wrong_document`.

    `wrong_document` is checked FIRST among the traps because it is the most
    diagnostic: it does not say the model reasoned badly, it says the model
    reasoned correctly over the wrong contract. The distractor ranges are
    disjoint from the real figures (asserted in corpus_l3), so a hit here is
    unambiguous.
    """
    if answer is None:
        return "format_error"
    spec = question["expect"]
    kind = spec["kind"]

    if kind == "underspecified":
        return "correct" if _is_decline(answer) else "over_claim"
    if _is_decline(answer):
        return "wrong"

    if kind != "numeric":
        # yes_no and choice are unchanged by the pack size; reuse L2's logic.
        from questions_l2 import grade_answer_l2  # noqa: PLC0415 - avoids a cycle
        return grade_answer_l2(question, answer)

    found = _numbers(answer)
    tol_rel, tol_abs = spec.get("tol_rel", 0.0), spec.get("tol_abs", 0.0)
    if _matches(found, spec["values"], tol_rel, tol_abs):
        return "correct"
    for label in ("wrong_document", "premature", "over_applied",
                  "precedence_missed", "stale"):
        targets = spec.get(label)
        if targets and _matches(found, targets, tol_rel, tol_abs):
            return "stale_value" if label == "stale" else label
    return "wrong"
