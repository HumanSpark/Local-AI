#!/usr/bin/env python3
# File: validate_ps_eval_l2.py
# Purpose: Prove the L2 graders score a perfect answer set correctly AND catch each named L2 failure mode.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: The L2 tier adds two outcomes (`premature`, `over_applied`) and
# one more (`precedence_missed`) on top of the L1 vocabulary, and every one
# of them is a claim that the grader can tell a specific reasoning error
# apart from generic wrongness. That claim has to be tested before any model
# is scored, or the tier reports failure modes it cannot actually detect.
#
# Seven synthetic respondents, each with a known signature:
#
#   PERFECT       every answer right                    -> 12/12 correct
#   PREMATURE     applies amendments ignoring their     -> 3 `premature`
#                 effective dates
#   HEURISTIC     "the latest amendment always wins",   -> 1 stale_value +
#                 blind to revocation and partial          1 wrong
#                 supersession
#   PREC_BLIND    never applies the precedence rule     -> 1 precedence_missed
#   OVER_APPLIER  applies it outside its stated scope   -> 1 over_applied
#   FABRICATOR    answers the underspecified item       -> 1 over_claim
#   PROSE         right content, ignores the format     -> 12 format_error
#
# It also asserts the thing most likely to break silently: that the L1 pack
# is still byte-identical. Seven completed cloud arms are scored against it.
#
# Run: python3 tools/validate_ps_eval_l2.py   (exit 0 = L2 graders are sound)

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "ps-eval"))
from corpus import build_pack  # noqa: E402
from corpus_l2 import DOCUMENTS_L2, build_pack_l2  # noqa: E402
from questions_l2 import QUESTIONS_L2, grade_answer_l2  # noqa: E402
from questions import grade_citation, parse_response  # noqa: E402

# The L1 pack as measured and committed on 2026-08-15, before L2 existed.
L1_SHA256_PREFIX = "eb5630b5f7378476"
L1_CHARS = 10_741

PERFECT: dict[str, str] = {
    "D1": "EUR 42,000",
    "D2": "EUR 500,000",
    "D3": "EUR 51,000",
    "V1": "24 months",
    "V2": "YES",
    "P1": "6 months",
    "P2": "2 business days",
    "M1": "EUR 378,000",
    "M2": "EUR 445,500",
    "M3": "24.5",
    "N1": "(d)",
    "Z1": "The pack does not specify the VAT treatment of service credits.",
}

# Applies every amendment the moment it sees it, effective dates be damned.
PREMATURE_OVERRIDES = {
    "D1": "EUR 46,500",
    "D2": "EUR 1,250,000",
    "M1": "EUR 418,500",
}

# "The most recent amendment wins" - the rule L1 rewarded.
HEURISTIC_OVERRIDES = {
    "V1": "12 months",
    "V2": "NO, clause 4.2 was replaced",
}

PREC_BLIND_OVERRIDES = {"P1": "24 months"}
OVER_APPLIER_OVERRIDES = {"P2": "1 business day"}
FABRICATOR_OVERRIDES = {"Z1": "Yes, VAT at 23% is chargeable on the service credit."}


def respond(answer: str) -> str:
    return f"ANSWER: {answer}\nCITATION: see pack"


def score(overrides: dict, formatted: bool = True) -> dict[str, int]:
    tally: dict[str, int] = {}
    for q in QUESTIONS_L2:
        answer = overrides.get(q["id"], PERFECT[q["id"]])
        text = respond(answer) if formatted else f"{answer} (see the pack)"
        parsed, _ = parse_response(text)
        outcome = grade_answer_l2(q, parsed)
        tally[outcome] = tally.get(outcome, 0) + 1
    return tally


def check(problems: list[str], label: str, tally: dict[str, int],
          outcome: str, want: int, why: str) -> None:
    got = tally.get(outcome, 0)
    if got != want:
        problems.append(f"{label}: {got} {outcome!r}, expected {want} - {why}")


def main() -> int:
    problems: list[str] = []

    # --- the L1 pack must not have moved -----------------------------------
    l1 = build_pack()
    digest = hashlib.sha256(l1.encode()).hexdigest()
    print(f"L1 pack: {len(l1):,} chars, sha256 {digest[:16]}")
    if len(l1) != L1_CHARS or not digest.startswith(L1_SHA256_PREFIX):
        problems.append(
            f"L1 pack CHANGED: {len(l1)} chars / {digest[:16]} vs expected "
            f"{L1_CHARS} / {L1_SHA256_PREFIX} - completed arms no longer compare"
        )

    pack = build_pack_l2()
    print(f"L2 pack: {len(DOCUMENTS_L2)} documents, {len(pack):,} chars, "
          f"~{len(pack)//4:,} tokens")
    print(f"L2 questions: {len(QUESTIONS_L2)}\n")

    missing = [q["id"] for q in QUESTIONS_L2 if q["id"] not in PERFECT]
    if missing:
        problems.append(f"no reference answer for: {missing}")
        print(f"  ABORT - {missing}")
        return 1

    perfect = score({})
    print(f"  PERFECT      {perfect}")
    if perfect.get("correct") != len(QUESTIONS_L2):
        problems.append(
            f"PERFECT scored {perfect.get('correct', 0)}/{len(QUESTIONS_L2)} - "
            f"the grader rejects known-correct answers: {perfect}"
        )

    prem = score(PREMATURE_OVERRIDES)
    print(f"  PREMATURE    {prem}")
    check(problems, "PREMATURE", prem, "premature", len(PREMATURE_OVERRIDES),
          "applying an amendment before its effective date is not being distinguished "
          "from generic wrongness, and it is the inverse of stale_value")

    heur = score(HEURISTIC_OVERRIDES)
    print(f"  HEURISTIC    {heur}")
    check(problems, "HEURISTIC", heur, "stale_value", 1,
          "the revocation item is not detecting a model that read only AMD-2")
    check(problems, "HEURISTIC", heur, "wrong", 1,
          "the partial-supersession item is not detecting wholesale-replacement reasoning")

    blind = score(PREC_BLIND_OVERRIDES)
    print(f"  PREC_BLIND   {blind}")
    check(problems, "PREC_BLIND", blind, "precedence_missed", 1,
          "failing to apply the precedence rule is not being named")

    over = score(OVER_APPLIER_OVERRIDES)
    print(f"  OVER_APPLIER {over}")
    check(problems, "OVER_APPLIER", over, "over_applied", 1,
          "applying the precedence rule outside its scope is not being named, and it is "
          "the more expensive of the two precedence errors")

    fab = score(FABRICATOR_OVERRIDES)
    print(f"  FABRICATOR   {fab}")
    check(problems, "FABRICATOR", fab, "over_claim", 1,
          "the underspecified item is not catching a confident invented answer")

    prose = score({}, formatted=False)
    print(f"  PROSE        {prose}")
    check(problems, "PROSE", prose, "format_error", len(QUESTIONS_L2),
          "unformatted output is being scored as content (F20)")

    # --- citations, BOTH directions ----------------------------------------
    # `citation_valid` appears in every result JSON, so the grader behind it
    # has to be shown to accept right citations AND reject wrong ones. A
    # one-directional check would pass a grader that returns True always.
    good = {
        "D1": "MSA-2024 clause 2.1", "D2": "MSA-2024 clause 4.1",
        "D3": "AMD-3 paragraph 2 (clause 2.1)",
        "V1": "AMD-3 paragraph 1 and MSA-2024 clause 5.2",
        "V2": "AMD-3 paragraph 3, MSA-2024 clause 4.2",
        "P1": "SIDE-1 paragraph 1 and POL-3.1 P-4.2",
        "P2": "SIDE-1 paragraph 2 and MSA-2024 clause 6.1",
        "M1": "MSA-2024 clauses 2.1 and 3.1",
        "M2": "AMD-1 paragraph 2 and AMD-3 paragraph 2",
        "M3": "AMD-2 paragraph 1 and AMD-3 paragraph 2",
        "N1": "NONE", "Z1": "NONE",
    }
    rejected = [q["id"] for q in QUESTIONS_L2 if not grade_citation(q, good[q["id"]])]
    # A citation naming a document that cannot answer the question must fail.
    accepted_junk = [q["id"] for q in QUESTIONS_L2
                     if grade_citation(q, "FIN-SUMMARY, quarterly revenue table")]
    print(f"  citations: {len(QUESTIONS_L2) - len(rejected)}/{len(QUESTIONS_L2)} good accepted, "
          f"{len(accepted_junk)} junk accepted")
    if rejected:
        problems.append(f"grader rejects known-good citations for: {rejected}")
    if accepted_junk:
        problems.append(
            f"grader accepts an irrelevant citation for: {accepted_junk} - citation_valid "
            f"would be meaningless for those questions"
        )

    # A safe decline on an ANSWERABLE item must be `wrong`, never `over_claim`.
    decline = grade_answer_l2(QUESTIONS_L2[0], "The pack does not specify.")
    print(f"\n  safe-decline on an answerable item -> {decline}")
    if decline != "wrong":
        problems.append(f"safe decline graded as {decline!r}, expected 'wrong'")

    # Every named trap must be reachable: a trap value that can never be
    # produced is a category that will silently report zero for ever.
    unreachable = []
    for q in QUESTIONS_L2:
        spec = q["expect"]
        for label in ("premature", "over_applied", "precedence_missed", "stale"):
            if label in spec:
                got = grade_answer_l2(q, str(spec[label][0]))
                want = "stale_value" if label == "stale" else label
                if got != want:
                    unreachable.append((q["id"], label, got))
    print(f"  trap reachability: {'all reachable' if not unreachable else unreachable}")
    if unreachable:
        problems.append(f"unreachable traps (id, label, actual): {unreachable}")

    print()
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"L2 graders sound: perfect set scores {len(QUESTIONS_L2)}/{len(QUESTIONS_L2)}, "
          f"each failure mode detected, L1 pack unmoved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
