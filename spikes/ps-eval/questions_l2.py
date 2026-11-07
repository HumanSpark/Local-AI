# File: questions_l2.py
# Purpose: Level-2 questions and graders - the harder tier, still graded without an LLM judge.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: Twelve questions over the L2 pack (corpus_l2.build_pack_l2), in
# six categories, every one graded by string or numeric matching. Written
# because Qwen3.8-27B-Q4_K_M scored 20/20 on L1 and a ceiling cannot rank
# anything.
#
# L1 REWARDED A HEURISTIC AND THIS TIER TESTS WHETHER THAT IS ALL THE MODEL
# HAS. Every L1 supersession item was solved by "use the most recent
# amendment". Three L2 categories punish exactly that move:
#
#   date_effective  the amendment exists but is not yet in force on the date
#                   asked about, so the OLDER figure is correct
#   revocation      the newest amendment restores an older value by revoking
#                   a paragraph of the previous one
#   precedence      a scoped precedence rule resolves one conflict and must
#                   NOT be applied to another outside its scope
#
# The outcome vocabulary is extended for the same reason it exists at all
# (F20): a wrong answer whose SHAPE is diagnostic must not be folded into a
# generic `wrong`. Two are added here.
#
#   premature       used an amendment before its stated effective date. This
#                   is the exact inverse of `stale_value` and a model can be
#                   bad at one and good at the other, so they are counted
#                   apart.
#   over_applied    applied the precedence rule outside the scope the side
#                   letter draws. In practice this is the more expensive of
#                   the two precedence errors - it produces a confident
#                   answer that contradicts the contract - so it is named.
#
# WHAT THIS TIER IS NOT. It is not longer (the L2 pack is ~3.3K tokens
# against L1's ~2.7K) and it is not more obscure. The difficulty is in the
# reasoning the question demands, not in retrieval load or trick wording.
# Length is E35's question and must not be conflated with this one.

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_l2 import (  # noqa: E402
    LIABILITY_CAP_SCHEDULE,
    RETAINER_SCHEDULE,
    RETENTION_SCHEDULE,
    retainer_total,
    value_on,
)
from questions import (  # noqa: E402
    NOT_IN_PACK_FORMS,
    _matches,
    _normalise_token,
    _numbers,
    parse_response,  # noqa: F401  - re-exported so the runner imports one module
)

CATEGORIES_L2 = [
    "date_effective", "revocation", "precedence",
    "multihop", "exhaustive", "underspecified",
]

# Phrasings that count as declining to answer. The capability under test is
# whether the model refuses to invent, not whether it happens to produce the
# literal token NOT_IN_PACK, so this is deliberately generous.
DECLINE_PATTERNS = [
    "not specified", "does not specify", "not stated", "does not state",
    "silent", "not addressed", "does not say", "cannot be determined",
    "not determinable", "no provision", "not in pack", "not_in_pack",
    "does not deal", "unspecified",
]


def _is_decline(answer: str) -> bool:
    if _normalise_token(answer) in NOT_IN_PACK_FORMS:
        return True
    low = (answer or "").lower()
    return any(p in low for p in DECLINE_PATTERNS)


QUESTIONS_L2: list[dict] = [
    # ---------------------------------------------------------------- dates
    {
        "id": "D1",
        "category": "date_effective",
        "question": (
            "What monthly retainer was payable for services delivered in September 2024? "
            "Give the amount in EUR."
        ),
        "cite_doc": ["MSA-2024"],
        "cite_clause": ["2.1"],
        # AMD-1 raises the retainer but only WITH EFFECT FROM 1 January 2025.
        # A model that has learned "apply the amendment" answers 46,500.
        "expect": {"kind": "numeric", "values": [value_on(RETAINER_SCHEDULE, "2024-09-15")],
                   "tol_rel": 0.001, "premature": [46_500]},
    },
    {
        "id": "D2",
        "category": "date_effective",
        "question": (
            "What was the Supplier's aggregate liability cap as at 31 March 2025? "
            "Give the amount in EUR."
        ),
        "cite_doc": ["MSA-2024"],
        "cite_clause": ["4.1"],
        # AMD-2 is dated 30 June 2025 and states no effective date, so it
        # cannot govern a question about March.
        "expect": {"kind": "numeric",
                   "values": [value_on(LIABILITY_CAP_SCHEDULE, "2025-03-31")],
                   "tol_rel": 0.001, "premature": [1_250_000, 1.25]},
    },
    {
        "id": "D3",
        "category": "date_effective",
        "question": (
            "What monthly retainer is payable for services delivered in May 2026? "
            "Give the amount in EUR."
        ),
        "cite_doc": ["AMD-3"],
        "cite_clause": ["2", "2.1"],
        # The mirror of D1: here the future-dated amendment HAS come into
        # force, so a model that treats all effective dates as noise and a
        # model that ignores AMD-3 both miss it, in opposite directions.
        "expect": {"kind": "numeric", "values": [value_on(RETAINER_SCHEDULE, "2026-05-01")],
                   "tol_rel": 0.001, "stale": [46_500]},
    },
    # ----------------------------------------------------------- revocation
    {
        "id": "V1",
        "category": "revocation",
        "question": (
            "Under the Agreement as amended, and disregarding the Client's internal "
            "policy, for how many months may the Supplier retain Client personal data "
            "following a termination occurring in February 2026?"
        ),
        "cite_doc": ["AMD-3", "MSA-2024"],
        "cite_clause": ["1", "5.2"],
        # AMD-3 revokes AMD-2 paragraph 3 and reinstates 24. "Most recent
        # amendment wins" gives 24 here only if the model reads what the most
        # recent amendment actually DOES; reading only AMD-2 gives 12.
        #
        # E38 AMENDMENT 1: the original wording did not scope this to the
        # Agreement, so 6 - the Policy period, which SIDE-1 makes prevail on
        # data matters - was a defensible answer and the cloud arm gave it.
        # Adding SIDE-1 for the P1/P2 questions silently changed the correct
        # answer to a question already in the set, and no grader could catch
        # that because the synthetic respondents answer what I intended.
        # 6 is now a NAMED trap: after an explicit instruction to disregard
        # the Policy, answering 6 is carrying the precedence rule past its
        # scope, which is `over_applied` and not generic wrongness.
        "expect": {"kind": "numeric", "values": [value_on(RETENTION_SCHEDULE, "2026-02-01")],
                   "tol_rel": 0.001, "stale": [12], "over_applied": [6]},
    },
    {
        "id": "V2",
        "category": "revocation",
        "question": (
            "Under clause 4.2 as amended, is 'loss of profit' still excluded? "
            "Answer YES or NO."
        ),
        "cite_doc": ["AMD-3", "MSA-2024"],
        "cite_clause": ["3", "4.2"],
        # AMD-3 deletes only the words "or loss of anticipated savings".
        # A model that treats every amendment as a wholesale clause
        # replacement gets this wrong.
        "expect": {"kind": "yes_no", "want": "yes"},
    },
    # ----------------------------------------------------------- precedence
    {
        "id": "P1",
        "category": "precedence",
        "question": (
            "A termination occurs in February 2026. Within what period must the Supplier "
            "delete Client personal data? Give the period that actually governs."
        ),
        "cite_doc": ["SIDE-1", "POL-3.1"],
        "cite_clause": ["1", "P-4.2"],
        # The Policy (6 months) is stricter than the Agreement as amended
        # (24 months) and SIDE-1 paragraph 1 makes the Policy prevail on data
        # matters. Answering 24 means the precedence rule was not applied.
        "expect": {"kind": "numeric", "values": [6], "tol_rel": 0.001,
                   "precedence_missed": [24]},
    },
    {
        "id": "P2",
        "category": "precedence",
        "question": (
            "Within how many business days must the Supplier respond to a query the Client "
            "has classified as critical? Give the period that actually governs."
        ),
        "cite_doc": ["SIDE-1", "MSA-2024"],
        "cite_clause": ["2", "6.1"],
        # SIDE-1 paragraph 2 confines the Policy's precedence to data matters
        # and says the Agreement continues to prevail on service levels, so
        # the answer is the Agreement's 2 days. Answering 1 is the model
        # carrying the precedence rule past its stated scope - the expensive
        # error, and invisible to L1.
        "expect": {"kind": "numeric", "values": [2], "tol_rel": 0.001,
                   "over_applied": [1]},
    },
    # ------------------------------------------------------------- multihop
    {
        "id": "M1",
        "category": "multihop",
        "question": (
            "What is the total retainer invoiced for the calendar year 2024? The Agreement "
            "commenced on 1 April 2024. Give the amount in EUR."
        ),
        "cite_doc": ["MSA-2024"],
        "cite_clause": ["2.1", "3.1"],
        # Nine months at 42,000. Requires the commencement date as well as the
        # rate, and requires knowing AMD-1 does not bite until January 2025.
        "expect": {"kind": "numeric",
                   "values": [retainer_total("2024-04-01", "2024-12-01")],
                   "tol_rel": 0.001, "premature": [retainer_total("2024-04-01", "2024-12-01")
                                                   - 42_000 * 9 + 46_500 * 9]},
    },
    {
        "id": "M2",
        "category": "multihop",
        "question": (
            "What is the total retainer payable from 1 January 2026 to the end of the "
            "Engagement Period? Give the amount in EUR."
        ),
        "cite_doc": ["AMD-1", "AMD-3"],
        "cite_clause": ["2", "1.2", "2.1"],
        # Three hops: the Engagement Period END comes from AMD-1 paragraph 2
        # (extended to 30 September 2026), the rate change from AMD-3
        # paragraph 2 (1 April 2026), and the split is 3 months at 46,500
        # plus 6 at 51,000.
        "expect": {"kind": "numeric",
                   "values": [retainer_total("2026-01-01", "2026-09-01")],
                   "tol_rel": 0.001,
                   # the trap is using the ORIGINAL end date of 31 March 2026
                   "stale": [retainer_total("2026-01-01", "2026-03-01")]},
    },
    {
        "id": "M3",
        "category": "multihop",
        "question": (
            "Expressed as a multiple of the monthly retainer in force in May 2026, how "
            "large is the Supplier's aggregate liability cap? Give the multiple to one "
            "decimal place."
        ),
        "cite_doc": ["AMD-2", "AMD-3"],
        "cite_clause": ["1", "2", "4.1", "2.1"],
        "expect": {"kind": "numeric",
                   "values": [1_250_000 / value_on(RETAINER_SCHEDULE, "2026-05-01")],
                   "tol_abs": 0.06},
    },
    # ------------------------------------------------------------ exhaustive
    {
        "id": "N1",
        "category": "exhaustive",
        "question": (
            "Exactly one of the following five obligations does NOT appear anywhere in the "
            "pack. Which one? Answer with its letter.\n"
            "(a) Notify the Client of a personal data breach within 48 hours of becoming aware.\n"
            "(b) Deliver the monthly reporting pack by the 10th calendar day of the "
            "following month.\n"
            "(c) Provide a named escalation contact.\n"
            "(d) Maintain professional indemnity insurance of at least EUR 5 million.\n"
            "(e) Confirm deletion of personal data in writing to the Data Protection Officer."
        ),
        "cite_doc": [],
        "cite_clause": [],
        # (a) MSA 5.4, (b) MSA 6.2, (c) POL P-2.2, (e) POL P-4.3. Insurance
        # appears nowhere. Answering requires checking all five rather than
        # finding one - the negative form is what makes it expensive.
        "expect": {"kind": "choice", "want": "d",
                   "aliases": ["insurance", "indemnity"]},
    },
    # --------------------------------------------------------- underspecified
    {
        "id": "Z1",
        "category": "underspecified",
        "question": (
            "Is VAT chargeable on a service credit issued under clause 6.3?"
        ),
        "cite_doc": [],
        "cite_clause": [],
        # The Agreement states fees are exclusive of VAT and says nothing at
        # all about the VAT treatment of credits. The topic is in the pack;
        # the attribute is not. This is a harder decline than L1's
        # unanswerable items, where the whole subject was absent - here there
        # is adjacent text that makes a confident answer feel supported.
        "expect": {"kind": "underspecified"},
    },
]


def grade_answer_l2(question: dict, answer: str | None) -> str:
    """correct | partial | wrong | stale_value | premature | over_applied |
    precedence_missed | over_claim | format_error."""
    if answer is None:
        return "format_error"
    spec = question["expect"]
    kind = spec["kind"]

    if kind == "underspecified":
        return "correct" if _is_decline(answer) else "over_claim"

    # Declining an answerable item is wrong, but it is the SAFE direction of
    # wrong and must never be counted as an over-claim.
    if _is_decline(answer):
        return "wrong"

    if kind == "yes_no":
        low = (answer or "").lower()
        said_yes = bool(re.search(r"\byes\b", low))
        said_no = bool(re.search(r"\bno\b|\bnot\b", low))
        if said_yes and not said_no:
            return "correct" if spec["want"] == "yes" else "wrong"
        if said_no and not said_yes:
            return "correct" if spec["want"] == "no" else "wrong"
        return "wrong"

    if kind == "choice":
        low = (answer or "").lower()
        if re.search(rf"\(?\b{re.escape(spec['want'])}\b\)?", low):
            return "correct"
        if any(alias in low for alias in spec.get("aliases", [])):
            return "correct"
        return "wrong"

    if kind == "numeric":
        found = _numbers(answer)
        tol_rel, tol_abs = spec.get("tol_rel", 0.0), spec.get("tol_abs", 0.0)
        if _matches(found, spec["values"], tol_rel, tol_abs):
            return "correct"
        # Ordered most-specific first: each of these is a NAMED failure whose
        # shape says what the model did wrong, and folding any into `wrong`
        # would lose the diagnostic the tier exists to produce.
        for label in ("premature", "over_applied", "precedence_missed", "stale"):
            targets = spec.get(label)
            if targets and _matches(found, targets, tol_rel, tol_abs):
                return "stale_value" if label == "stale" else label
        return "wrong"

    raise ValueError(
        f"unknown expect kind {kind!r} for L2 question {question['id']}. "
        f"hint: add a branch to grade_answer_l2 or fix the question spec"
    )
