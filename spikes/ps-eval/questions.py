# File: questions.py
# Purpose: The PS-eval question set plus its objective graders - no LLM judge anywhere.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: Twenty questions over the engagement pack in corpus.py, in five
# categories, each with an exactly checkable expected answer and an expected
# citation. Grading is string and numeric matching, which is the whole point:
# every other knowledge-work result in results/ depends on a frontier model as
# judge, so the ruler is itself an unmeasured instrument. Here there is no
# ruler to doubt.
#
# THE MODEL IS REQUIRED TO ANSWER IN A FIXED TWO-LINE FORM:
#
#   ANSWER: <value, or NOT_IN_PACK>
#   CITATION: <document id and clause, or NONE>
#
# Format compliance is a real capability for this use case - a firm cannot
# consume free prose - but a model that fails to emit the form is recorded as
# `format_error` and NOT as a wrong answer. That distinction is F20's lesson
# applied here: a mechanical failure silently scored as a capability failure
# is how a benchmark lies.
#
# DIAGNOSTIC OUTCOMES, not just pass/fail. A supersession item answered with
# the pre-amendment figure is recorded as `stale_value`, because "used the
# superseded number" is a specific and expensive real-world failure that
# deserves its own count rather than being folded into "wrong". Likewise an
# unanswerable item answered with anything at all is `over_claim`.

from __future__ import annotations

import re

# --------------------------------------------------------------------------
# QUESTIONS
# --------------------------------------------------------------------------
# expect kinds:
#   numeric      - any number in ANSWER matches one of `values` within tol
#   text         - ANSWER contains one of `any_of` (case-insensitive)
#   not_in_pack  - ANSWER is exactly NOT_IN_PACK
#   conflict     - ANSWER signals disagreement AND names both figures

QUESTIONS: list[dict] = [
    # ---------------- RETRIEVAL: stated once, cite it ----------------
    {
        "id": "R1",
        "category": "retrieval",
        "question": "Under the Master Services Agreement AS ORIGINALLY EXECUTED on 1 March 2024, "
                    "and ignoring any later amendment, what was the Supplier's aggregate "
                    "liability cap?",
        "expect": {"kind": "numeric", "values": [500000, 0.5], "tol_rel": 0.001},
        "cite_doc": ["MSA-2024"], "cite_clause": ["4.1"],
    },
    {
        "id": "R2",
        "category": "retrieval",
        "question": "Within how many days of receipt are the Supplier's invoices payable?",
        "expect": {"kind": "numeric", "values": [30], "tol_rel": 0.001},
        "cite_doc": ["MSA-2024"], "cite_clause": ["2.3"],
    },
    {
        "id": "R3",
        "category": "retrieval",
        "question": "Who is the Client's authorised representative for the purposes of change "
                    "control?",
        "expect": {"kind": "text", "any_of": ["chief financial officer", "cfo"]},
        "cite_doc": ["MSA-2024"], "cite_clause": ["7.2"],
    },
    {
        "id": "R4",
        "category": "retrieval",
        "question": "If the Supplier misses the monthly reporting deadline in three consecutive "
                    "months, what service credit is the Client entitled to?",
        "expect": {"kind": "numeric", "values": [5], "tol_rel": 0.001},
        "cite_doc": ["MSA-2024"], "cite_clause": ["6.3"],
    },
    {
        "id": "R5",
        "category": "retrieval",
        "question": "Within how many hours must the Supplier notify the Client of a personal "
                    "data breach?",
        "expect": {"kind": "numeric", "values": [48], "tol_rel": 0.001},
        "cite_doc": ["MSA-2024"], "cite_clause": ["5.4"],
    },

    # ---------------- SUPERSESSION: an amendment changed it ----------------
    {
        "id": "S1",
        "category": "supersession",
        "question": "What monthly retainer is payable by the Client with effect from "
                    "1 January 2025?",
        "expect": {"kind": "numeric", "values": [46500], "tol_rel": 0.001, "stale": [42000]},
        "cite_doc": ["AMD-1"], "cite_clause": ["1", "2.1"],
    },
    {
        "id": "S2",
        "category": "supersession",
        "question": "As at 1 August 2025, how many days written notice must a party give to "
                    "terminate the Agreement for convenience?",
        "expect": {"kind": "numeric", "values": [120], "tol_rel": 0.001, "stale": [90]},
        "cite_doc": ["AMD-2"], "cite_clause": ["2", "3.2"],
    },
    {
        "id": "S3",
        "category": "supersession",
        "question": "What is the Supplier's aggregate liability cap under the Agreement as "
                    "currently amended?",
        "expect": {"kind": "numeric", "values": [1250000, 1.25], "tol_rel": 0.001,
                   "stale": [500000, 0.5]},
        "cite_doc": ["AMD-2"], "cite_clause": ["1", "4.1"],
    },
    {
        "id": "S4",
        "category": "supersession",
        "question": "For how many months following termination may the Supplier retain Client "
                    "personal data, under the Agreement as currently amended?",
        "expect": {"kind": "numeric", "values": [12], "tol_rel": 0.001, "stale": [24]},
        "cite_doc": ["AMD-2"], "cite_clause": ["3", "5.2"],
    },

    # ---------------- COMPUTATION: arithmetic over the table ----------------
    {
        "id": "C1",
        "category": "computation",
        "question": "What was total revenue for FY2024 (the four calendar quarters of 2024)? "
                    "Give the figure in euro.",
        "expect": {"kind": "numeric", "values": [32960000, 32.96], "tol_rel": 0.001},
        "cite_doc": ["FIN-SUMMARY"], "cite_clause": [],
    },
    {
        "id": "C2",
        "category": "computation",
        "question": "What was the gross margin percentage for FY2024, to one decimal place? "
                    "Gross margin is gross profit divided by revenue.",
        "expect": {"kind": "numeric", "values": [19.1748], "tol_abs": 0.06},
        "cite_doc": ["FIN-SUMMARY"], "cite_clause": [],
    },
    {
        "id": "C3",
        "category": "computation",
        "question": "By what percentage did revenue grow in 2025 Q2 compared with 2024 Q2? "
                    "Give the answer to one decimal place.",
        "expect": {"kind": "numeric", "values": [14.0794], "tol_abs": 0.06},
        "cite_doc": ["FIN-SUMMARY"], "cite_clause": [],
    },
    {
        "id": "C4",
        "category": "computation",
        "question": "What was the gross margin percentage for the six months ended 30 June 2025, "
                    "to one decimal place, calculated from the financial summary?",
        "expect": {"kind": "numeric", "values": [19.5699], "tol_abs": 0.06},
        "cite_doc": ["FIN-SUMMARY"], "cite_clause": [],
    },

    # ---------------- CONFLICT: two documents disagree ----------------
    {
        "id": "X1",
        "category": "conflict",
        "question": "Does the data deletion requirement in the internal policy agree with the "
                    "retention period in the Agreement as currently amended? Answer YES or NO, "
                    "and if NO state both periods in months.",
        "expect": {"kind": "conflict", "disagree": True,
                   "values_all": [[6], [12]], "tol_rel": 0.001},
        "cite_doc": ["POL-3.1", "AMD-2"], "cite_clause": ["P-4.2", "5.2", "3"],
    },
    {
        "id": "X2",
        "category": "conflict",
        "question": "Does the gross margin for the six months ended 30 June 2025 noted in the "
                    "board minutes agree with the figure calculated from the financial summary? "
                    "Answer YES or NO, and if NO state both percentages.",
        "expect": {"kind": "conflict", "disagree": True,
                   "values_all": [[21.4], [19.5699]], "tol_abs": 0.06},
        "cite_doc": ["BM-EXTRACTS", "FIN-SUMMARY"], "cite_clause": ["6.1"],
    },
    {
        "id": "X3",
        "category": "conflict",
        "question": "Does the supplier response time required by the internal policy for "
                    "critical queries agree with the service level in the Agreement? Answer YES "
                    "or NO, and if NO state both response times in business days.",
        "expect": {"kind": "conflict", "disagree": True,
                   "values_all": [[1], [2]], "tol_rel": 0.001},
        "cite_doc": ["POL-3.1", "MSA-2024"], "cite_clause": ["P-2.3", "6.1"],
    },

    # ---------------- UNANSWERABLE: the pack does not say ----------------
    {
        "id": "U1",
        "category": "unanswerable",
        "question": "What is the limit of the Supplier's professional indemnity insurance?",
        "expect": {"kind": "not_in_pack"},
        "cite_doc": [], "cite_clause": [],
    },
    {
        "id": "U2",
        "category": "unanswerable",
        "question": "Which sub-processors has the Client approved in writing?",
        "expect": {"kind": "not_in_pack"},
        "cite_doc": [], "cite_clause": [],
    },
    {
        "id": "U3",
        "category": "unanswerable",
        "question": "What was Northwind Logistics' total headcount at 31 December 2024?",
        "expect": {"kind": "not_in_pack"},
        "cite_doc": [], "cite_clause": [],
    },
    {
        "id": "U4",
        "category": "unanswerable",
        "question": "What day rate does the Supplier charge for expert witness work?",
        "expect": {"kind": "not_in_pack"},
        "cite_doc": [], "cite_clause": [],
    },
]

# --------------------------------------------------------------------------
# GRADING
# --------------------------------------------------------------------------

ANSWER_RE = re.compile(r"^\s*ANSWER\s*:\s*(.*?)\s*$", re.IGNORECASE | re.MULTILINE)
CITATION_RE = re.compile(r"^\s*CITATION\s*:\s*(.*?)\s*$", re.IGNORECASE | re.MULTILINE)
NUM_RE = re.compile(r"-?\d[\d,]*\.?\d*")

NOT_IN_PACK_FORMS = {
    "notinpack", "not_in_pack", "notinthepack", "none", "nonestated",
    "notstated", "notspecified", "notavailable",
}


def parse_response(text: str) -> tuple[str | None, str | None]:
    """Pull the ANSWER and CITATION fields out of a model response.

    Takes the LAST match of each: reasoning models frequently rehearse the
    template mid-thought before committing to it, and the final statement is
    the one the model is standing behind.
    """
    answers = ANSWER_RE.findall(text or "")
    citations = CITATION_RE.findall(text or "")
    return (answers[-1] if answers else None, citations[-1] if citations else None)


def _numbers(text: str) -> list[float]:
    out = []
    for raw in NUM_RE.findall(text or ""):
        try:
            out.append(float(raw.replace(",", "")))
        except ValueError:
            continue
    return out


def _matches(found: list[float], targets: list[float], tol_rel: float = 0.0,
             tol_abs: float = 0.0) -> bool:
    for value in found:
        for target in targets:
            if tol_abs and abs(value - target) <= tol_abs:
                return True
            if tol_rel and abs(value - target) <= abs(target) * tol_rel:
                return True
            if not tol_abs and not tol_rel and value == target:
                return True
    return False


def _normalise_token(text: str) -> str:
    return re.sub(r"[^a-z]", "", (text or "").lower())


def grade_citation(question: dict, citation: str | None) -> bool:
    """A citation is valid when it names an expected document, and - where the
    question has clause-level ground truth - an expected clause."""
    if not question["cite_doc"]:
        return citation is not None and _normalise_token(citation) in NOT_IN_PACK_FORMS
    if not citation:
        return False
    low = citation.lower()
    if not any(doc.lower() in low for doc in question["cite_doc"]):
        return False
    if not question["cite_clause"]:
        return True
    return any(clause.lower() in low for clause in question["cite_clause"])


def grade_answer(question: dict, answer: str | None) -> str:
    """Return one of: correct | partial | wrong | stale_value | over_claim | format_error."""
    if answer is None:
        return "format_error"
    spec = question["expect"]
    kind = spec["kind"]
    normalised = _normalise_token(answer)

    if kind == "not_in_pack":
        return "correct" if normalised in NOT_IN_PACK_FORMS else "over_claim"

    # A model that says NOT_IN_PACK on an answerable item is wrong, but it is
    # the SAFE direction of wrong and is not an over-claim.
    if normalised in NOT_IN_PACK_FORMS:
        return "wrong"

    found = _numbers(answer)
    if kind == "numeric":
        if _matches(found, spec["values"], spec.get("tol_rel", 0.0), spec.get("tol_abs", 0.0)):
            return "correct"
        if spec.get("stale") and _matches(found, spec["stale"],
                                          spec.get("tol_rel", 0.0), spec.get("tol_abs", 0.0)):
            return "stale_value"
        return "wrong"

    if kind == "text":
        low = (answer or "").lower()
        return "correct" if any(opt in low for opt in spec["any_of"]) else "wrong"

    if kind == "conflict":
        says_no = bool(re.search(r"\bno\b|disagree|conflict|inconsist", answer, re.IGNORECASE))
        if not says_no:
            return "wrong"
        # Detecting the conflict and quantifying it are different capabilities.
        # A bare "NO" is the right JUDGEMENT under-reported, and folding it into
        # `wrong` alongside a model that missed the conflict entirely would
        # destroy the distinction the category exists to measure - the same
        # reason `stale_value` and `format_error` are not folded into `wrong`.
        for group in spec["values_all"]:
            if not _matches(found, group, spec.get("tol_rel", 0.0), spec.get("tol_abs", 0.0)):
                return "partial"
        return "correct"

    raise ValueError(
        f"unknown expect kind {kind!r} for question {question['id']}. "
        f"hint: add a branch to grade_answer or fix the question spec"
    )


CATEGORIES = ["retrieval", "supersession", "computation", "conflict", "unanswerable"]
