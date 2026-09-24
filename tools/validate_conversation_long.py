#!/usr/bin/env python3
# File: validate_conversation_long.py
# Purpose: Prove E56's paired anchors are byte-identical, its filler cannot corrupt the answer key, and every failure shape is reachable.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: E56's claim is that DEPTH is the only variable between an anchor's
# shallow ask and its deep one. That claim lives entirely in the construction of
# the turn list, so it has to be checked mechanically rather than read. Three
# families of check, and each one has already caught something in this repo:
#
#   PAIRING       the shallow and deep asks must be byte-identical and must
#                 carry the same answer. A one-character drift between them
#                 turns the headline measurement into a comparison of two
#                 different questions, and nothing in the results would show it.
#
#   COLLISION     no agreement delivered mid-conversation may contain a figure
#                 that is an L4 answer. DIS-05's retainer is EUR 27,600, which
#                 is exactly the November fee - so this file also asserts that
#                 DIS-05 WOULD have collided, which keeps the exclusion honest
#                 rather than decorative. This is E48's class, found again.
#
#   SIGNATURE     each synthetic respondent must produce the outcome it was
#                 designed to produce. If the one that answers from the wrong
#                 document grades as `wrong`, the tier's new outcome is
#                 unreachable and the run reports zero of them for the wrong
#                 reason.
#
# Run: python3 tools/validate_conversation_long.py   (exit 0 = every check holds)

from __future__ import annotations

import datetime as dt
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "ps-eval"))

from conversation_long import (  # noqa: E402
    ANCHOR_PAIRS,
    DSR_ONE_MONTH,
    FILLER_BATCHES,
    FILLER_CAPS,
    FILLER_EXCLUDED,
    FILLER_IDS,
    FILLER_RETAINERS,
    GRADED,
    NOTICE_AFTER_23_DELETED,
    NOTICE_GOVERNING,
    NOVEMBER_FEE,
    PROBES,
    REVISED_DSR_DEADLINE,
    SUB_INSURANCE_GAP,
    SUB_INSURANCE_WRONG_BASIS,
    TURNS,
)
from corpus_l3 import DISTRACTORS, _DISTRACTOR_SPECS  # noqa: E402
from corpus_l4 import build_pack_l4  # noqa: E402
from grade_multiturn import grade_multiturn  # noqa: E402

_MONTHS = ("January February March April May June July August September "
           "October November December").split()


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
        traps = spec.get("stale_answer")
        return _fmt(traps[0]) if traps else correct
    if who == "always_updates":
        if turn.get("probe") == "over_revision":
            return "YES" if kind == "yes_no" else _fmt(spec["over_revised"][0])
        return correct
    if who == "agrees_with_me":
        traps = spec.get("accepted_false")
        return _fmt(traps[0]) if traps else correct
    if who == "wrong_file":
        # Reaches for the most recently delivered agreement instead of the pack.
        traps = spec.get("wrong_document")
        return str(traps[0]) if traps else correct
    if who == "unformatted":
        return None
    raise ValueError(
        f"unknown respondent {who!r}. hint: add a branch or fix the signature table"
    )


SIGNATURES: dict[str, dict[str, int]] = {
    "perfect":        {"correct": len(GRADED)},
    "never_updates":  {"stale_answer": 4},
    "always_updates": {"over_revised": 1},
    "agrees_with_me": {"accepted_false": 2},
    "wrong_file":     {"wrong_document": 2},
    "unformatted":    {"format_error": len(GRADED)},
}


def _money_in(text: str) -> set[float]:
    """Every distinctive figure in a document, integers and decimals alike.

    Decimals are scanned separately because the integer pattern would read
    `493.99` as `493` and `99` and miss the figure that is actually an answer.
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


def _protected() -> tuple[set[float], set[dt.date]]:
    """Every figure a filler document must NOT contain.

    Two sources, unioned, because either alone leaves a hole:

      the ANSWER KEY   derived from the graded turns rather than typed out, so
                       a question added later is protected the moment it exists.
      the PACK ITSELF  every distinctive figure in the real documents. A filler
                       agreement that reuses the Firm's EUR 2,000,000 insurance
                       limit is a wrong-document trap the answer key cannot
                       name, because no question asks for that figure directly
                       - it is an OPERAND of one that does.

    `recent` turns are excluded, and so are the `wrong_document` traps: their
    answers are by design inside the filler, which is the point of them.

    Clause and section numbers are unavoidable in any legal document, and years
    are unavoidable in any dated one, so only figures at or above 1,000 and
    outside 1900-2100 count as distinctive.
    """
    nums: set[float] = set()
    dates: set[dt.date] = set()

    def add_num(v: float) -> None:
        if v >= 1000 and not (1900 <= v <= 2100):
            nums.add(float(v))

    for t in GRADED:
        if t.get("probe") == "recent":
            continue
        spec = t["expect"]
        pool = []
        if spec["kind"] == "date":
            pool.append(spec["want"])
        elif spec["kind"] == "numeric":
            pool.extend(spec["values"])
        for label in ("stale_answer", "accepted_false", "over_revised",
                      "wrong_trigger", "off_by_calendar"):
            pool.extend(spec.get(label, ()))
        for v in pool:
            if isinstance(v, dt.date):
                dates.add(v)
            elif isinstance(v, (int, float)) and not isinstance(v, bool):
                add_num(float(v))

    for m in re.finditer(r"\b\d[\d,]*(?:\.\d+)?\b", build_pack_l4()):
        add_num(float(m.group(0).replace(",", "")))

    return nums, dates


def main() -> int:
    checks: list[tuple[str, bool]] = []

    def eq(label: str, got, want) -> None:
        checks.append((f"{label}: {want!r} (got {got!r})", got == want))

    order = [t["id"] for t in TURNS]

    def before(a: str, b: str) -> bool:
        return order.index(a) < order.index(b)

    # ---- shape -----------------------------------------------------------
    eq("turns", len(TURNS), 29)
    eq("graded turns", len(GRADED), 20)
    eq("turn ids unique", len({t["id"] for t in TURNS}), len(TURNS))
    eq("every probe is used", sorted({t["probe"] for t in GRADED}), sorted(PROBES))
    for probe, want in (("baseline", 5), ("revision", 2), ("over_revision", 1),
                        ("false_premise", 2), ("recent", 5), ("depth", 5)):
        eq(f"{probe} turns", sum(1 for t in GRADED if t["probe"] == probe), want)

    # ---- pairing: the headline measurement -------------------------------
    by_id = {t["id"]: t for t in TURNS}
    for name, shallow, deep in ANCHOR_PAIRS:
        s, d = by_id[shallow], by_id[deep]
        eq(f"{name} asks are BYTE-IDENTICAL ({shallow} vs {deep})",
           s["say"] == d["say"], True)
        eq(f"{name} kind is unchanged at depth",
           s["expect"]["kind"], d["expect"]["kind"])
        s_key = (s["expect"].get("want"), tuple(s["expect"].get("values", ())))
        d_key = (d["expect"].get("want"), tuple(d["expect"].get("values", ())))
        eq(f"{name} ANSWER is unchanged at depth", s_key, d_key)
        eq(f"{name}'s deep ask comes after its shallow one",
           before(shallow, deep), True)
    eq("every depth turn is the deep half of a pair",
       sorted(t["id"] for t in GRADED if t["probe"] == "depth"),
       sorted(d for _, _, d in ANCHOR_PAIRS))

    # The deep anchors must sit after ALL the filler, or they are not deep.
    delivery_ids = ("T10", "T12", "T15", "T19", "T21")
    eq("every filler batch has a delivery turn",
       len(delivery_ids), len(FILLER_BATCHES))
    last_delivery = max(order.index(i) for i in delivery_ids)
    eq("every deep anchor comes after the last document delivery",
       all(order.index(d) > last_delivery for _, _, d in ANCHOR_PAIRS), True)

    # ---- revision structure ----------------------------------------------
    eq("T07 revises T01, and the correction T06 sits between them",
       before("T01", "T06") and before("T06", "T07"), True)
    eq("T09 revises T02, and the correction T08 sits between them",
       before("T02", "T08") and before("T08", "T09"), True)
    eq("a stale trap IS the pre-correction answer (T07)",
       by_id["T07"]["expect"]["stale_answer"], [DSR_ONE_MONTH])
    eq("a stale trap IS the pre-correction answer (T09)",
       by_id["T09"]["expect"]["stale_answer"], [NOTICE_GOVERNING])
    eq("both revisions actually change the answer",
       [DSR_ONE_MONTH != REVISED_DSR_DEADLINE,
        NOTICE_GOVERNING != NOTICE_AFTER_23_DELETED], [True, True])
    # One correction must move its date EARLIER, or the tier only ever tests
    # "corrections push dates later" and a model passes on direction alone.
    eq("one correction moves the date earlier and one later",
       sorted([REVISED_DSR_DEADLINE > DSR_ONE_MONTH,
               NOTICE_AFTER_23_DELETED > NOTICE_GOVERNING]), [False, True])
    # And the deep asks must carry the stale trap too, or a lost correction at
    # depth would grade as plain `wrong` and the retention result vanishes.
    for deep in ("T23", "T24"):
        eq(f"{deep} still carries its stale trap at depth",
           bool(by_id[deep]["expect"].get("stale_answer")), True)

    # ---- false premise ----------------------------------------------------
    eq("T18 tests the assertion made in T17", before("T17", "T18"), True)
    eq("T29 tests the assertion made in T28", before("T28", "T29"), True)
    eq("the asserted shortfall differs from the true one",
       SUB_INSURANCE_WRONG_BASIS != SUB_INSURANCE_GAP, True)

    # ---- collision: the filler may not contain an L4 answer ---------------
    nums, dates = _protected()
    eq("protected figures were actually derived", len(nums) >= 5 and len(dates) >= 5,
       True)
    dirty = {}
    for did in FILLER_IDS:
        text = DISTRACTORS[did]
        bad = sorted(_money_in(text) & nums) + sorted(
            str(x) for x in (_dates_in(text) & dates))
        if bad:
            dirty[did] = bad
    eq("filler agreements containing an L4 answer figure", dirty, {})

    # The exclusion must be load-bearing: prove DIS-05 WOULD have collided.
    spec_by_id = {s[0]: s for s in _DISTRACTOR_SPECS}
    eq("DIS-05 is excluded", list(FILLER_EXCLUDED), ["DIS-05"])
    eq("and DIS-05's retainer really is the November fee",
       spec_by_id["DIS-05"][4], NOVEMBER_FEE)
    eq("so DIS-05 is not in the filler", "DIS-05" in FILLER_IDS, False)

    # The wrong-document traps must not be the right answer.
    eq("no filler retainer equals the November fee",
       NOVEMBER_FEE in FILLER_RETAINERS, False)
    eq("no filler cap equals the insurance shortfall",
       SUB_INSURANCE_GAP in FILLER_CAPS, False)
    eq("the filler supplies enough distinct traps to be diagnostic",
       len(FILLER_RETAINERS) == len(FILLER_IDS) and len(FILLER_CAPS) == len(FILLER_IDS),
       True)

    # ---- no trap may equal its own turn's answer -------------------------
    collisions: list[str] = []
    for t in GRADED:
        spec = t["expect"]
        keys = ([spec["want"]] if spec["kind"] in ("date", "yes_no")
                else list(spec.get("values", ())))
        for label in ("accepted_false", "stale_answer", "over_revised",
                      "wrong_document", "wrong_trigger", "off_by_calendar"):
            for trap in spec.get(label, ()):
                if trap in keys:
                    collisions.append(f"{t['id']} {label} {trap}")
    eq("traps colliding with their own answer", collisions, [])

    # ---- respondent signatures -------------------------------------------
    for who, signature in SIGNATURES.items():
        counts = Counter(grade_multiturn(t, _answer(t, who)) for t in GRADED)
        for outcome, want in signature.items():
            eq(f"{who} produces {outcome}", counts[outcome], want)

    bad = [c for c, ok in checks if not ok]
    for c, ok in checks:
        print(("  ok    " if ok else "  WRONG ") + c)
    print(f"\n{len(checks) - len(bad)}/{len(checks)} checks pass")
    if bad:
        print("\nA pairing, a collision guard or a signature does not hold. Fix the "
              "CONVERSATION or the GRADER, not this file.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
