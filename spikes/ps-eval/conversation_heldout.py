# File: conversation_heldout.py
# Purpose: The HELD-OUT deep tier - questions asked ONLY at depth, so the model's own earlier answer is not in the history it re-reads.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: E56 measured five questions twice, byte-identically, twenty
# thousand tokens apart, and every deep answer came back byte-identical to its
# shallow one. Its own write-up named the reason that headline is narrow: the
# model's earlier reply is inside the history it is re-sent, so the design
# cannot separate HELD the answer from RE-READ the answer. E54b's lesson is
# that an instrument can manufacture a positive result as easily as a negative
# one, and that confound is exactly the shape which would do it.
#
# THIS TIER REMOVES THE MODEL'S OWN ANSWER FROM THE EVIDENCE. Every graded
# question is asked EXACTLY ONCE in a run. A question answered at depth here
# has never been answered in this conversation, so a correct answer had to come
# from the pack, not from scrollback.
#
# THE PRICE OF HOLDING A QUESTION OUT, AND HOW IT IS PAID. Asking a question
# only once destroys E56's within-run control: a wrong answer at depth could be
# depth, or it could be a hard question. So the tier is a CROSSOVER, run twice
# per model over two disjoint sets of five:
#
#     order `ab`     set A shallow (turns 1-5),  set B deep (turns 14-18)
#     order `ba`     set B shallow (turns 1-5),  set A deep (turns 14-18)
#
# Every question is therefore observed shallow AND deep, but never twice in one
# conversation. Each question is its own control across the pair of runs, so
# set-level difficulty cancels by construction rather than by my judgement that
# two sets "look about as hard". That is the whole reason for the crossover;
# matching two sets by eye is the move E54's ambiguous question punished.
#
# THE MIDDLE IS BYTE-IDENTICAL ACROSS THE TWO ORDERS. Same pack, same ten
# agreements in the same order, same three `recent` probes in the same places.
# The ONLY difference between an `ab` run and a `ba` run is which five
# questions sit at turn 1 and which sit at turn 14. Asserted mechanically in
# tools/validate_conversation_heldout.py rather than left to this paragraph.
#
# THE TEN QUESTIONS ARE SELECTED BY RULE, NOT BY SCORE. They are every question
# in the L4 bank that the conversation lineage (E55, E56) has never asked, less
# U1. I know how all three models score on these standalone from E54b, so
# picking them by hand would be picking the result; the rule is declared here
# and re-derived in the validator from QUESTIONS_L4 itself, so a question added
# to the bank later changes the selection rather than silently sitting outside
# it. U1 is the one exclusion and it is a grader fact, not a taste: its correct
# answer is a DECLINE, and grade_multiturn treats declining as the safe
# direction of `wrong` - correct for every other item and exactly backwards for
# that one.
#
# The split into two sets alternates in declaration order. That is arbitrary,
# which is the point, and it happens to give each set two dates, one numeric,
# one choice and one yes/no - a balance nobody chose and the validator asserts
# so it cannot silently rot.
#
# WHAT THIS TIER DOES NOT MEASURE, said here rather than in a footnote:
# corrections. E56's revision probes need a fact stated mid-conversation and
# re-asked afterwards, which is a question that CANNOT be held out - its
# meaning depends on the turn before it. F81 and F82 already report that
# revisions survive both a short conversation and a deep one. This tier asks
# the narrower question those two could not: at depth, with nothing of its own
# to copy, can the model still read the pack?

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conversation_long import (  # noqa: E402
    FILLER_BATCHES,
    FILLER_CAPS,
    FILLER_IDS,
    FILLER_RETAINERS,
    RULES,
    _SPEC_BY_ID,
    _deliver,
)
from corpus_l4 import build_pack_l4  # noqa: E402
from questions_l4 import QUESTIONS_L4  # noqa: E402

# The middle is imported rather than rebuilt, deliberately. The filler
# selection was calibrated against a measured context budget for E56 and its
# DIS-05 exclusion is already proven load-bearing by that tier's validator.
# Re-deriving it here would produce a second implementation of a decision that
# was hard to get right once, and would break the one thing that makes E57
# readable next to E56: the depth is the same depth.

# ------------------------------------------------------------- the selection
#
# Asked by the conversation lineage and therefore NOT held out. E55 and E56 put
# each of these into a conversation already, so a model may carry a wording it
# has effectively been trained on within this programme's own corpus.
LINEAGE_ASKED = ("P1", "N2", "I1", "D3")

# Excluded for a grader reason, not a difficulty one. See the header.
DECLINE_ITEMS = ("U1",)

HELD_OUT_IDS = [q["id"] for q in QUESTIONS_L4
                if q["id"] not in LINEAGE_ASKED and q["id"] not in DECLINE_ITEMS]

SET_A = HELD_OUT_IDS[0::2]      # P2, B1, F1, D1, X1
SET_B = HELD_OUT_IDS[1::2]      # P3, N1, S1, D2, X2

_Q_BY_ID = {q["id"]: q for q in QUESTIONS_L4}

# One preamble, identical on all ten questions and identical in both positions.
#
# WHY IT IS THERE. Ten further services agreements arrive mid-conversation, and
# several of the bank's questions were written for a context where the pack was
# the only thing on the table - "the controller", "the Firm", with no document
# named. F78 says name the document and the party or a small model burns its
# whole budget deciding which one you meant. Left alone, a drop at depth would
# be ambiguous between "could not retrieve" and "did not know which file", and
# the ambiguity would bite ONLY at depth, which is precisely where the
# measurement is.
#
# WHAT IT COSTS, stated because it is a real limit on the claim. Pointing the
# model back at the pack makes this retrieval-WHEN-DIRECTED. It is the
# professionally realistic case - an advisor says "in the engagement letter" -
# but it is not spontaneous retrieval, and E57 cannot speak to that.
SCOPE = ("Referring to the engagement pack provided at the start of this "
         "conversation: ")

# Figures a wrong-document answer would carry, from the ten agreements this
# conversation actually delivers. Applied to numeric questions only, and
# applied IDENTICALLY shallow and deep - E56 could only add its traps at depth,
# because shallow the agreements had not arrived, and had to explain the
# asymmetry. Here each question appears once per run, so one expectation block
# serves both positions and there is no asymmetry to explain.
_FILLER_FIGURES = sorted(set(FILLER_RETAINERS) | set(FILLER_CAPS))


def _expect_for(qid: str) -> dict:
    """The L4 key, verbatim, plus wrong-document traps for numeric items.

    Derived from QUESTIONS_L4 rather than retyped. A key typed a second time is
    a key that can drift from the tier it is meant to be comparable with, and
    no score reveals it.
    """
    spec = _Q_BY_ID[qid]["expect"]
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in spec.items()}
    if out["kind"] != "numeric":
        return out
    # Never let a trap swallow a real answer or another named failure shape.
    taken = set(out.get("values", ()))
    for label in ("partial", "wrong_trigger", "off_by_calendar"):
        taken |= set(out.get(label, ()))
    traps = [f for f in _FILLER_FIGURES if f not in taken]
    if traps:
        out["wrong_document"] = traps
    return out


PROBES = ["shallow", "recent", "deep"]

# The recent probes. Identical in both orders, and placed so the last one sits
# immediately before the deep half: a model that answers it and then fails the
# deep questions has not lost the conversation, it has lost the OLD part of it,
# and that distinction is the finding rather than a caveat.
_RECENT = [
    ("R1", 0, f"From what you have just been sent: under {FILLER_IDS[0]}, what is "
              f"the monthly retainer? Give the amount in EUR, exclusive of VAT.",
     lambda: _SPEC_BY_ID[FILLER_IDS[0]][4]),
    ("R2", 4, f"And under {FILLER_IDS[4]}, what is the limit on the Supplier's "
              f"aggregate liability? Give the amount in EUR.",
     lambda: _SPEC_BY_ID[FILLER_IDS[4]][5]),
    ("R3", 8, f"Under {FILLER_IDS[8]}, what is the monthly retainer? Give the "
              f"amount in EUR, exclusive of VAT.",
     lambda: _SPEC_BY_ID[FILLER_IDS[8]][4]),
]


def _question_turn(qid: str, probe: str, first: bool) -> dict:
    say = SCOPE + _Q_BY_ID[qid]["question"]
    if first:
        say = RULES.format(pack=build_pack_l4()) + say
    return {"id": qid, "probe": probe, "say": say, "expect": _expect_for(qid)}


def build_turns(order: str) -> list[dict]:
    """The 18-turn conversation for one order. `ab` or `ba`."""
    if order == "ab":
        shallow_ids, deep_ids = SET_A, SET_B
    elif order == "ba":
        shallow_ids, deep_ids = SET_B, SET_A
    else:
        raise ValueError(
            f"unknown held-out order {order!r}. "
            f"hint: one of 'ab' (set A shallow) or 'ba' (set B shallow)"
        )

    turns: list[dict] = [
        _question_turn(qid, "shallow", first=(i == 0))
        for i, qid in enumerate(shallow_ids)
    ]

    # The long middle. Five deliveries of two agreements each, so the
    # conversation grows turn by turn rather than stepping once - a single
    # block would make this a long-PROMPT test with a conversation attached,
    # which F74 already measured at 236,122 tokens.
    recent_after = {idx: r for r in _RECENT for idx in (r[1],)}
    for batch_i, batch in enumerate(FILLER_BATCHES):
        turns.append({"id": f"DLV{batch_i + 1}", "say": _deliver(batch)})
        probe = recent_after.get(batch_i * 2)
        if probe:
            rid, _, say, key = probe
            turns.append({"id": rid, "probe": "recent", "say": say,
                          "expect": {"kind": "numeric", "values": [key()],
                                     "tol_rel": 0.001}})

    turns += [_question_turn(qid, "deep", first=False) for qid in deep_ids]
    return turns


def variant(order: str) -> SimpleNamespace:
    """The runner's view of one order: TURNS, GRADED, PROBES, ANCHOR_PAIRS.

    ANCHOR_PAIRS is EMPTY and that is the design, not an omission. E56's pairs
    were two turns inside one conversation; here the pair is one turn in THIS
    run and one turn in the mirror run, which no single run can report.
    tools/compare_heldout.py joins them.
    """
    turns = build_turns(order)
    return SimpleNamespace(
        TURNS=turns,
        GRADED=[t for t in turns if "expect" in t],
        PROBES=PROBES,
        ANCHOR_PAIRS=[],
        ORDER=order,
    )
