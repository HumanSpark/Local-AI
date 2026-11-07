#!/usr/bin/env python3
# File: validate_ps_eval.py
# Purpose: Prove the PS-eval graders score a perfect answer set correctly AND catch each named failure mode.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: The PS eval replaces an LLM judge with string and numeric
# matching, which only helps if the matcher itself is right. This drives the
# graders with four synthetic respondents whose behaviour is known in advance:
#
#   PERFECT      every answer correct and correctly cited      -> 20/20
#   STALE        reads the base contract, ignores both         -> supersession
#                amendments                                       items land as
#                                                                 `stale_value`
#   OVER_CLAIMER invents a plausible figure for anything it    -> unanswerable
#                cannot find                                      items land as
#                                                                 `over_claim`
#   PROSE        correct content, ignores the output format    -> `format_error`
#
# If any of those four fails to produce its signature, the grader is not
# measuring what the report will claim it measures.
#
# Run: python3 tools/validate_ps_eval.py   (exit 0 = graders are sound)

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "ps-eval"))
from corpus import DOCUMENTS, build_pack, distractors  # noqa: E402
from questions import (  # noqa: E402
    NUM_RE,
    QUESTIONS,
    grade_answer,
    grade_citation,
    parse_response,
)

# The known-correct answer and citation for every question.
PERFECT: dict[str, tuple[str, str]] = {
    "R1": ("EUR 500,000", "MSA-2024 clause 4.1"),
    "R2": ("30 days", "MSA-2024 clause 2.3"),
    "R3": ("The Chief Financial Officer", "MSA-2024 clause 7.2"),
    "R4": ("5% of the monthly retainer", "MSA-2024 clause 6.3"),
    "R5": ("48 hours", "MSA-2024 clause 5.4"),
    "S1": ("EUR 46,500", "AMD-1 paragraph 1 (replacing clause 2.1)"),
    "S2": ("120 days", "AMD-2 paragraph 2 (replacing clause 3.2)"),
    "S3": ("EUR 1,250,000", "AMD-2 paragraph 1 (replacing clause 4.1)"),
    "S4": ("12 months", "AMD-2 paragraph 3 (replacing clause 5.2)"),
    "C1": ("EUR 32,960,000", "FIN-SUMMARY"),
    "C2": ("19.2%", "FIN-SUMMARY"),
    "C3": ("14.1%", "FIN-SUMMARY"),
    "C4": ("19.6%", "FIN-SUMMARY"),
    "X1": ("NO - the policy requires deletion within 6 months, the Agreement permits 12 months",
           "POL-3.1 P-4.2 and AMD-2 clause 5.2"),
    "X2": ("NO - the board minutes note 21.4% but the summary gives 19.6%",
           "BM-EXTRACTS 6.1 and FIN-SUMMARY"),
    "X3": ("NO - the policy requires 1 business day, the Agreement allows 2 business days",
           "POL-3.1 P-2.3 and MSA-2024 clause 6.1"),
    "U1": ("NOT_IN_PACK", "NONE"),
    "U2": ("NOT_IN_PACK", "NONE"),
    "U3": ("NOT_IN_PACK", "NONE"),
    "U4": ("NOT_IN_PACK", "NONE"),
}

# Reads only the base contract - the classic retrieval failure.
STALE_OVERRIDES = {
    "S1": ("EUR 42,000", "MSA-2024 clause 2.1"),
    "S2": ("90 days", "MSA-2024 clause 3.2"),
    "S3": ("EUR 500,000", "MSA-2024 clause 4.1"),
    "S4": ("24 months", "MSA-2024 clause 5.2"),
}

# Spots every conflict but never quantifies it - the right judgement,
# under-reported. Must NOT be scored the same as missing the conflict.
PARTIAL_OVERRIDES = {
    "X1": ("NO", "POL-3.1 P-4.2 and AMD-2 clause 5.2"),
    "X2": ("NO", "BM-EXTRACTS 6.1 and FIN-SUMMARY"),
    "X3": ("NO", "POL-3.1 P-2.3 and MSA-2024 clause 6.1"),
}

# Misses the conflicts entirely - the genuinely wrong answer.
MISSED_CONFLICT_OVERRIDES = {
    "X1": ("YES, they agree", "POL-3.1 P-4.2"),
    "X2": ("YES, both give 21.4%", "BM-EXTRACTS 6.1"),
    "X3": ("YES, both require 1 business day", "POL-3.1 P-2.3"),
}

# Invents something plausible rather than declining.
OVER_CLAIM_OVERRIDES = {
    "U1": ("EUR 5,000,000", "MSA-2024 clause 4.1"),
    "U2": ("Aer Data Services Ltd and Kinsale Analytics", "MSA-2024 clause 5.3"),
    "U3": ("412 employees", "BM-EXTRACTS"),
    "U4": ("EUR 2,280 per day", "MSA-2024 clause 2.2"),
}


def respond(answer: str, citation: str) -> str:
    return f"ANSWER: {answer}\nCITATION: {citation}"


def score(overrides: dict, formatted: bool = True) -> dict[str, int]:
    tally: dict[str, int] = {}
    for q in QUESTIONS:
        answer, citation = overrides.get(q["id"], PERFECT[q["id"]])
        text = respond(answer, citation) if formatted else f"{answer} (see {citation})"
        parsed_answer, parsed_citation = parse_response(text)
        outcome = grade_answer(q, parsed_answer)
        tally[outcome] = tally.get(outcome, 0) + 1
        if formatted and overrides is PERFECT_EMPTY and not grade_citation(q, parsed_citation):
            tally["bad_citation"] = tally.get("bad_citation", 0) + 1
    return tally


PERFECT_EMPTY: dict = {}


def main() -> int:
    problems: list[str] = []

    pack = build_pack()
    print(f"corpus: {len(DOCUMENTS)} documents, {len(pack):,} chars, ~{len(pack)//4:,} tokens")
    print(f"questions: {len(QUESTIONS)}\n")

    # every question must have a perfect answer written for it
    missing = [q["id"] for q in QUESTIONS if q["id"] not in PERFECT]
    if missing:
        problems.append(f"no reference answer for: {missing}")

    perfect = score(PERFECT_EMPTY)
    print(f"  PERFECT      {perfect}")
    if perfect.get("correct") != len(QUESTIONS):
        problems.append(
            f"PERFECT respondent scored {perfect.get('correct', 0)}/{len(QUESTIONS)} - "
            f"the grader rejects known-correct answers: {perfect}"
        )

    # citations, graded separately
    bad_cites = [
        q["id"] for q in QUESTIONS
        if not grade_citation(q, parse_response(respond(*PERFECT[q["id"]]))[1])
    ]
    print(f"  citations    {len(QUESTIONS) - len(bad_cites)}/{len(QUESTIONS)} valid")
    if bad_cites:
        problems.append(f"grader rejects known-correct citations for: {bad_cites}")

    stale = score(STALE_OVERRIDES)
    print(f"  STALE        {stale}")
    if stale.get("stale_value") != len(STALE_OVERRIDES):
        problems.append(
            f"STALE respondent produced {stale.get('stale_value', 0)} stale_value outcomes, "
            f"expected {len(STALE_OVERRIDES)} - supersession failures are not being detected"
        )

    over = score(OVER_CLAIM_OVERRIDES)
    print(f"  OVER_CLAIMER {over}")
    if over.get("over_claim") != len(OVER_CLAIM_OVERRIDES):
        problems.append(
            f"OVER_CLAIMER produced {over.get('over_claim', 0)} over_claim outcomes, expected "
            f"{len(OVER_CLAIM_OVERRIDES)} - the headline liability metric does not work"
        )

    part = score(PARTIAL_OVERRIDES)
    print(f"  PARTIAL      {part}")
    if part.get("partial") != len(PARTIAL_OVERRIDES):
        problems.append(
            f"PARTIAL respondent produced {part.get('partial', 0)} partial outcomes, expected "
            f"{len(PARTIAL_OVERRIDES)} - a detected-but-unquantified conflict is being scored "
            f"as if the conflict was missed"
        )

    missed = score(MISSED_CONFLICT_OVERRIDES)
    print(f"  MISSED_CONF  {missed}")
    if missed.get("wrong") != len(MISSED_CONFLICT_OVERRIDES):
        problems.append(
            f"MISSED_CONFLICT respondent produced {missed.get('wrong', 0)} wrong outcomes, "
            f"expected {len(MISSED_CONFLICT_OVERRIDES)} - missing a conflict must score worse "
            f"than under-reporting one"
        )

    prose = score(PERFECT_EMPTY, formatted=False)
    print(f"  PROSE        {prose}")
    if prose.get("format_error") != len(QUESTIONS):
        problems.append(
            f"PROSE respondent produced {prose.get('format_error', 0)} format_error outcomes, "
            f"expected {len(QUESTIONS)} - unformatted output is being scored as content"
        )

    # DISTRACTORS must answer nothing. A distractor that happens to contain an
    # expected value would silently make a long-pack run wrong in a way no
    # score would reveal, so this is checked mechanically rather than by eye.
    noise = "\n".join(distractors(12))
    noise_numbers = {float(n.replace(",", "")) for n in NUM_RE.findall(noise)}
    leaks = []
    for q in QUESTIONS:
        spec = q["expect"]
        for value in list(spec.get("values", [])) + [
            v for group in spec.get("values_all", []) for v in group
        ]:
            if value in noise_numbers:
                leaks.append((q["id"], value))
    print(f"  distractors  12 documents, {len(noise):,} chars, "
          f"{len(noise_numbers)} distinct numbers, {len(leaks)} bare-value collisions")
    if leaks:
        # NOT counted as a problem, and the reason matters. A bare `2` in a
        # distractor's "ARTICLE II" is not an answer to anything: grading reads
        # the MODEL's answer text, never the pack. Small integers are
        # unavoidable in realistic contracts, so a numeric-disjointness test is
        # the wrong instrument - the real risk is a SEMANTIC collision, another
        # agreement that also specifies a response time or a retention period.
        # Until that check exists, distractor mode stays unvalidated and unrun.
        print(f"               collisions: {leaks}")
        print("               -> DISTRACTOR MODE IS NOT VALIDATED. Do not run a "
              "long-pack arm until a semantic collision check exists.")
    # and the base pack must stay byte-stable, or arms already run stop comparing
    if build_pack(0) != build_pack():
        problems.append("build_pack(0) differs from build_pack() - default pack is unstable")

    # a safe decline on an answerable item must be `wrong`, never `over_claim`
    decline = grade_answer(QUESTIONS[0], "NOT_IN_PACK")
    print(f"  safe-decline on an answerable item -> {decline}")
    if decline != "wrong":
        problems.append(f"safe decline graded as {decline!r}, expected 'wrong'")

    print()
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("CORE graders sound: perfect set scores 20/20, and each failure mode is detected")
    print("distractor mode: built, NOT validated - see the note above")
    return 0


if __name__ == "__main__":
    sys.exit(main())
