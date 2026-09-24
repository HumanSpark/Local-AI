#!/usr/bin/env python3
# File: validate_conversation_heldout.py
# Purpose: Assert E57's crossover holds - one ask per question, an identical middle across both orders, and a filler disjoint from the held-out key.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: E57's whole claim rests on three structural facts, and every one of
# them is the kind that a plausible edit breaks silently:
#
#   ASKED ONCE      a question asked twice in one run puts the model's own
#                   answer back into the history, which is the confound the
#                   tier exists to remove. A copy-paste while adding a probe
#                   re-introduces it and no score would show it.
#   ONE VARIABLE    the two orders must differ ONLY in which five questions sit
#                   shallow and which sit deep. If the middles drift apart, the
#                   crossover stops cancelling difficulty and starts measuring
#                   the drift.
#   DISJOINT KEY    Rule 12: a corpus is only disjoint from the answer key it
#                   was BUILT against. The filler was built disjoint from L2/L3
#                   and re-checked against E56's key - NOT against these ten
#                   questions, which E56 never asked. So it is re-checked here,
#                   from the figures, not from the fact that it passed before.
#
# The respondent signatures at the end are the same idea applied to the GRADER:
# a hand-written wrong answer of each shape must produce the label that shape
# is named for. A grader that silently stopped emitting `wrong_document` would
# otherwise look exactly like a model that stopped making that mistake.

from __future__ import annotations

import datetime as dt
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))

import conversation_heldout as H  # noqa: E402
from conversation_long import FILLER_IDS  # noqa: E402
from corpus_l3 import DISTRACTORS  # noqa: E402
from corpus_l4 import build_pack_l4  # noqa: E402
from grade_multiturn import grade_multiturn  # noqa: E402
from questions_l4 import QUESTIONS_L4  # noqa: E402

_MONTHS = ("January February March April May June July August September "
           "October November December").split()


def _fmt(value) -> str:
    return value.strftime("%d %B %Y") if hasattr(value, "strftime") else str(value)


def _answer(turn: dict, who: str) -> str | None:
    """What `who` answers this turn. One deliberate failure mode each."""
    spec = turn["expect"]
    kind = spec["kind"]
    if kind == "date":
        correct = _fmt(spec["want"])
    elif kind in ("yes_no", "choice"):
        correct = spec["want"]
    else:
        correct = str(spec["values"][0])

    if who == "perfect":
        return correct
    if who == "wrong_file":
        # Reaches for a delivered agreement instead of the pack.
        traps = spec.get("wrong_document")
        return str(traps[0]) if traps else correct
    if who == "quotes_the_operand":
        # Reads the right clause and returns a figure off the page rather than
        # the difference the question asked for - L4's `partial`, which only
        # survives into a conversation because grade_multiturn now carries it.
        traps = spec.get("partial")
        return str(traps[0]) if traps else correct
    if who == "says_yes_anyway":
        # The failure that exposed the yes/no label bug: a wrong YES on an item
        # that probes for an ABSENT defect. There is no revision in this tier,
        # so the only correct label is `wrong` - and nothing caught it until a
        # real arm produced it, because no synthetic respondent had ever
        # answered YES to a want-NO item.
        return "YES" if (kind == "yes_no" and spec["want"] == "no") else correct
    if who == "unformatted":
        return None
    raise ValueError(
        f"unknown respondent {who!r}. hint: add a branch or fix the signature table"
    )


def _money_in(text: str) -> set[float]:
    """Every distinctive figure in a document, integers and decimals alike.

    Decimals are scanned separately because the integer pattern reads `493.99`
    as `493` and `99` and misses the figure that is actually an answer.
    """
    out: set[float] = {float(m.group(0).replace(",", ""))
                       for m in re.finditer(r"\b\d[\d,]*\b", text)}
    out |= {float(m.group(0).replace(",", ""))
            for m in re.finditer(r"\b\d[\d,]*\.\d+\b", text)}
    return out


def _dates_in(text: str) -> set[dt.date]:
    out = set()
    for m in re.finditer(r"\b(\d{1,2})\s+(" + "|".join(_MONTHS) + r")\s+(\d{4})\b",
                         text):
        out.add(dt.date(int(m.group(3)), _MONTHS.index(m.group(2)) + 1,
                        int(m.group(1))))
    return out


def _protected(graded: list[dict]) -> tuple[set[float], set[dt.date]]:
    """Every figure the filler must NOT contain, for THIS tier's key.

    Two sources, unioned. The answer key is derived from the graded turns
    rather than typed, so a question added later is protected the moment it
    exists. The PACK's own figures are added because a filler agreement
    reusing, say, the Firm's EUR 2,000,000 insurance limit is a wrong-document
    trap no answer key can name - that figure is an OPERAND of a question, not
    the answer to one.

    `recent` turns are excluded, and so are the `wrong_document` traps: their
    values are inside the filler by design, which is the entire point of them.

    Clause and section numbers are unavoidable in a legal document and years in
    a dated one, so only figures at or above 1,000 and outside 1900-2100 count.
    """
    nums: set[float] = set()
    dates: set[dt.date] = set()

    def add_num(v: float) -> None:
        if v >= 1000 and not (1900 <= v <= 2100):
            nums.add(float(v))

    for t in graded:
        if t.get("probe") == "recent":
            continue
        spec = t["expect"]
        pool: list = []
        if spec["kind"] == "date":
            pool.append(spec["want"])
        elif spec["kind"] == "numeric":
            pool.extend(spec["values"])
        for label in ("wrong_trigger", "off_by_calendar", "partial"):
            pool.extend(spec.get(label, ()))
        for v in pool:
            if isinstance(v, dt.date):
                dates.add(v)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                add_num(float(v))

    for m in re.finditer(r"\b\d[\d,]*(?:\.\d+)?\b", build_pack_l4()):
        add_num(float(m.group(0).replace(",", "")))
    return nums, dates


SIGNATURES: dict[str, dict[str, int]] = {
    "perfect":            {"correct": 13},
    "unformatted":        {"format_error": 13},
    # F1, D2 and the three `recent` probes are the numeric turns; the recent
    # probes get no filler traps because their answers ARE filler figures.
    "wrong_file":         {"wrong_document": 2},
    "quotes_the_operand": {"partial": 1},
    # X1 and X2. `over_revised` must be 0: this tier has nothing to over-revise.
    "says_yes_anyway":    {"wrong": 2, "over_revised": 0},
}


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def eq(label: str, got, want) -> None:
        checks.append((f"{label}: {want!r} (got {got!r})", got == want))

    ab, ba = H.variant("ab"), H.variant("ba")

    # ---- the selection is a RULE, re-derived here from the bank ----------
    bank = [q["id"] for q in QUESTIONS_L4]
    expected_selection = [i for i in bank
                          if i not in H.LINEAGE_ASKED and i not in H.DECLINE_ITEMS]
    eq("held-out set IS every bank question the lineage never asked, less U1",
       H.HELD_OUT_IDS, expected_selection)
    eq("ten of them", len(H.HELD_OUT_IDS), 10)
    eq("the lineage questions are genuinely excluded",
       sorted(set(H.HELD_OUT_IDS) & set(H.LINEAGE_ASKED)), [])
    eq("U1 is excluded, and it really is the decline item",
       [i for i in H.DECLINE_ITEMS
        if next(q for q in QUESTIONS_L4 if q["id"] == i)["expect"]["kind"]
        == "underspecified"], list(H.DECLINE_ITEMS))
    eq("the two sets are disjoint", sorted(set(H.SET_A) & set(H.SET_B)), [])
    eq("and together they are the whole selection",
       sorted(H.SET_A + H.SET_B), sorted(H.HELD_OUT_IDS))
    eq("five each", [len(H.SET_A), len(H.SET_B)], [5, 5])
    # Nobody chose this balance - it falls out of alternating declaration
    # order - but if a bank edit destroys it the sets stop being interchangeable
    # and the crossover quietly starts comparing a date set with a numeric one.
    kinds = {s: sorted(Counter(
        next(q for q in QUESTIONS_L4 if q["id"] == i)["expect"]["kind"]
        for i in ids).items())
        for s, ids in (("A", H.SET_A), ("B", H.SET_B))}
    eq("both sets have the same mix of question kinds", kinds["A"], kinds["B"])

    # ---- asked once: the confound E57 exists to remove -------------------
    for name, v in (("ab", ab), ("ba", ba)):
        ids = [t["id"] for t in v.TURNS]
        eq(f"[{name}] turn ids unique", len(set(ids)), len(ids))
        eq(f"[{name}] 18 turns, 13 graded",
           [len(v.TURNS), len(v.GRADED)], [18, 13])
        asked = [t["id"] for t in v.GRADED if t["probe"] in ("shallow", "deep")]
        eq(f"[{name}] every held-out question asked EXACTLY once",
           sorted(asked), sorted(H.HELD_OUT_IDS))
        eq(f"[{name}] no within-run pairs to re-read", v.ANCHOR_PAIRS, [])
        eq(f"[{name}] probes used", sorted({t["probe"] for t in v.GRADED}),
           sorted(H.PROBES))
        for probe, want in (("shallow", 5), ("deep", 5), ("recent", 3)):
            eq(f"[{name}] {probe} turns",
               sum(1 for t in v.GRADED if t["probe"] == probe), want)
        # Deep means deep: after every document delivery, not merely later.
        last_dlv = max(i for i, t in enumerate(v.TURNS)
                       if t["id"].startswith("DLV"))
        first_dlv = min(i for i, t in enumerate(v.TURNS)
                        if t["id"].startswith("DLV"))
        eq(f"[{name}] every deep question comes after the LAST delivery",
           all(i > last_dlv for i, t in enumerate(v.TURNS)
               if t.get("probe") == "deep"), True)
        eq(f"[{name}] every shallow question comes before the FIRST delivery",
           all(i < first_dlv for i, t in enumerate(v.TURNS)
               if t.get("probe") == "shallow"), True)
        eq(f"[{name}] only the first turn carries the pack",
           [i for i, t in enumerate(v.TURNS) if "ENGAGEMENT PACK" in t["say"]], [0])

    # ---- one variable: the orders differ ONLY in placement ---------------
    ab_by, ba_by = {t["id"]: t for t in ab.TURNS}, {t["id"]: t for t in ba.TURNS}
    for qid in H.HELD_OUT_IDS:
        a, b = ab_by[qid], ba_by[qid]
        # Turn 1 carries the pack and the rules, so that one question's `say`
        # legitimately differs between orders. Compare the question itself.
        a_say = a["say"].split("=== QUESTION ===\n")[-1]
        b_say = b["say"].split("=== QUESTION ===\n")[-1]
        eq(f"{qid} is asked in BYTE-IDENTICAL words in both orders",
           a_say == b_say, True)
        eq(f"{qid} is graded against an IDENTICAL key in both orders",
           a["expect"] == b["expect"], True)
        eq(f"{qid} swaps position between the orders",
           sorted([a["probe"], b["probe"]]), ["deep", "shallow"])
    middle_ab = [t for t in ab.TURNS if t["id"].startswith(("DLV", "R"))]
    middle_ba = [t for t in ba.TURNS if t["id"].startswith(("DLV", "R"))]
    eq("the middle is byte-identical across the two orders",
       [(t["id"], t["say"]) for t in middle_ab],
       [(t["id"], t["say"]) for t in middle_ba])
    eq("the middle is where it should be - same turn indices in both orders",
       [i for i, t in enumerate(ab.TURNS) if t["id"].startswith(("DLV", "R"))],
       [i for i, t in enumerate(ba.TURNS) if t["id"].startswith(("DLV", "R"))])

    # ---- the questions are the BANK's, not retyped ------------------------
    for qid in H.HELD_OUT_IDS:
        bank_q = next(q for q in QUESTIONS_L4 if q["id"] == qid)
        say = ab_by[qid]["say"].split("=== QUESTION ===\n")[-1]
        eq(f"{qid} is the bank question verbatim behind a fixed scope preamble",
           say, H.SCOPE + bank_q["question"])
        # The key may gain wrong-document traps; nothing else may move.
        for field in ("kind", "want", "values", "aliases", "tol_rel", "tol_abs",
                      "partial", "wrong_trigger", "off_by_calendar"):
            if field in bank_q["expect"]:
                eq(f"{qid} key field {field} is unchanged from the bank",
                   ab_by[qid]["expect"].get(field), bank_q["expect"][field])
    eq("the scope preamble is identical on all ten",
       len({ab_by[q]["say"].split("=== QUESTION ===\n")[-1][:len(H.SCOPE)]
            for q in H.HELD_OUT_IDS}), 1)

    # ---- Rule 12: re-check the filler against THIS key --------------------
    nums, dates = _protected(ab.GRADED)
    eq("protected figures were actually derived",
       len(nums) >= 5 and len(dates) >= 5, True)
    dirty = {}
    for did in FILLER_IDS:
        text = DISTRACTORS[did]
        bad = sorted(_money_in(text) & nums) + sorted(
            str(x) for x in (_dates_in(text) & dates))
        if bad:
            dirty[did] = bad
    eq("filler agreements containing a HELD-OUT answer figure", dirty, {})

    # ---- no trap may equal its own turn's answer --------------------------
    collisions: list[str] = []
    for t in ab.GRADED + ba.GRADED:
        spec = t["expect"]
        keys = ([spec["want"]] if spec["kind"] in ("date", "yes_no", "choice")
                else list(spec.get("values", ())))
        for label in ("wrong_document", "wrong_trigger", "off_by_calendar",
                      "partial"):
            for trap in spec.get(label, ()):
                if trap in keys:
                    collisions.append(f"{t['id']} {label} {trap}")
    eq("traps colliding with their own answer", collisions, [])

    # ---- the recent probes must be answerable and not self-trapping ------
    recent = [t for t in ab.GRADED if t["probe"] == "recent"]
    eq("every recent probe asks about an agreement already delivered",
       all(any(fid in t["say"] for fid in FILLER_IDS) for t in recent), True)
    eq("recent probes carry no wrong-document trap (their answer IS filler)",
       [t["id"] for t in recent if "wrong_document" in t["expect"]], [])
    eq("recent answers are distinct, so a lucky repeat cannot pass two",
       len({t["expect"]["values"][0] for t in recent}), len(recent))

    # ---- respondent signatures -------------------------------------------
    for who, signature in SIGNATURES.items():
        counts = Counter(grade_multiturn(t, _answer(t, who)) for t in ab.GRADED)
        for outcome, want in signature.items():
            eq(f"{who} produces {outcome}", counts[outcome], want)

    bad = [c for c, ok in checks if not ok]
    for c, ok in checks:
        print(("  ok    " if ok else "  WRONG ") + c)
    print(f"\n{len(checks) - len(bad)}/{len(checks)} checks pass")
    if bad:
        print("\nThe crossover, a collision guard or a signature does not hold. "
              "Fix the CONVERSATION or the GRADER, not this file.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
