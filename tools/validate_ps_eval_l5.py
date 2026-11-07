#!/usr/bin/env python3
# File: tools/validate_ps_eval_l5.py
# Purpose: The L5 gate - prove the bank before any model sees it, with synthetic respondents whose signatures the graders must reproduce.
# Project: sparkbench | Date: 2026-08-28
#
# Overview: E54 established that a bank is not trustworthy because it was
# written carefully; it is trustworthy because a set of respondents with KNOWN
# behaviour score the way the design says they must. Its validator caught two
# live defects during construction, and this one is built to the same pattern
# with three checks added for what L5 does differently.
#
# The checks, in the order they run:
#
#  1. STRUCTURE     - 24 items, 12 per band, unique ids, declared categories,
#                     every cited document ID actually present in the pack.
#  2. ABSENCE       - every `underspecified` item's subject really is absent
#                     from the built pack. E76's gate refused six items on its
#                     first pass for exactly this, so it is not theoretical.
#  3. COPIER        - no band-R computed key appears verbatim in the pack. A
#                     key that coincides with a printed figure lets a model
#                     that copies a number grade as correct, and no score can
#                     reveal it (E48, and L4 caught two instances).
#  4. TRAP DISTINCT - every trap value differs from its own answer. A trap that
#                     equals the key cannot detect the error it names, and the
#                     first draft of this bank had exactly that: the parallel
#                     and sequential readings of the data-access period both
#                     landed on 29 August.
#  5. RESPONDENTS   - five synthetic answerers, each with a required signature.
#
# A failure here is a REFUSAL. The bank does not run until it passes.

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "spikes" / "ps-eval"))

from corpus_l5 import build_pack_l5  # noqa: E402
from questions_l5 import (  # noqa: E402
    BANDS,
    CATEGORIES_L5,
    QUESTIONS_L5,
    grade_answer_l5,
)

PACK = build_pack_l5()
PACK_LOW = PACK.lower()

# What each underspecified item claims the record does not settle. Checked
# literally: if any of these strings is in the pack, the item is answerable and
# the bank is refused.
ABSENCE_CLAIMS: dict[str, list[str]] = {
    "E09": ["governing law", "jurisdiction", "laws of ireland", "courts of"],
    "E10": ["contract value", "price", "eur 96,000 per", "fee for co-2"],
    "E11": [
        "passed acceptance",
        "failed acceptance",
        "acceptance test",
        "accepted the site c",
        "rejected",
    ],
    "E12": ["employees", "headcount", "staff of", "personnel numbers"],
}

failures: list[str] = []


def check(condition: bool, message: str) -> None:
    if not condition:
        failures.append(message)


def _fmt_date(value) -> str:
    return f"{value.day} {value:%B %Y}"


def perfect_answer(q: dict) -> str:
    """The answer a respondent who is right about everything would give."""
    spec = q["expect"]
    kind = spec["kind"]
    if kind == "underspecified":
        return "The documents do not state this. It is not in pack."
    if kind == "date":
        return f"The date is {_fmt_date(spec['want'])}."
    if kind == "numeric":
        return f"The figure is {spec['values'][0]:,.2f}."
    if kind == "choice":
        return f"The answer is {spec['want']}."
    if kind == "yes_no":
        return "No." if spec["want"] == "no" else "Yes."
    if kind == "set":
        return "The answer is " + ", ".join(spec["require"]) + "."
    raise ValueError(f"perfect_answer has no branch for kind {kind!r} ({q['id']})")


# --------------------------------------------------------------- 1. structure

check(len(QUESTIONS_L5) == 24, f"expected 24 items, found {len(QUESTIONS_L5)}")

ids = [q["id"] for q in QUESTIONS_L5]
check(
    len(ids) == len(set(ids)),
    f"duplicate item ids: {[i for i in ids if ids.count(i) > 1]}",
)

for band in BANDS:
    n = sum(1 for q in QUESTIONS_L5 if q["band"] == band)
    check(
        n == 12,
        f"band {band} has {n} items, expected 12 - the bands must be balanced "
        f"or a per-band comparison is confounded by sample size",
    )

for q in QUESTIONS_L5:
    check(q["band"] in BANDS, f"{q['id']}: unknown band {q['band']!r}")
    check(
        q["category"] in CATEGORIES_L5,
        f"{q['id']}: undeclared category {q['category']!r}",
    )
    check(
        q["difficulty"] in {"D1", "D2", "D3", "D4", "D5"},
        f"{q['id']}: bad difficulty {q['difficulty']!r}",
    )
    for doc in q["cite_doc"]:
        check(
            f"DOCUMENT ID: {doc}" in PACK,
            f"{q['id']}: cites {doc}, which is not a document in the pack",
        )

# Band R hands the evidence over, so every band-R item must name at least one
# document or clause in its own question text. An R item that requires a search
# is an E item wearing the wrong label.
for q in (x for x in QUESTIONS_L5 if x["band"] == "R"):
    named = any(
        tok in q["question"]
        for tok in (
            "FA-2025",
            "CO-1",
            "CO-2",
            "CO-3",
            "STAT-1",
            "CAL-2026",
            "BG-1",
            "clause",
            "section",
            "Framework Agreement",
        )
    )
    check(
        named,
        f"{q['id']} is band R but its question names no clause or document - "
        f"band R must hand the evidence over",
    )

# ----------------------------------------------------------------- 2. absence

for qid, claims in ABSENCE_CLAIMS.items():
    item = next((q for q in QUESTIONS_L5 if q["id"] == qid), None)
    check(
        item is not None,
        f"absence claim registered for {qid}, which is not in the bank",
    )
    if item is not None:
        check(
            item["expect"]["kind"] == "underspecified",
            f"{qid} has an absence claim but is not an underspecified item",
        )
    for phrase in claims:
        check(
            phrase.lower() not in PACK_LOW,
            f"{qid} asserts the pack is silent, but it contains {phrase!r}",
        )

declared = {q["id"] for q in QUESTIONS_L5 if q["expect"]["kind"] == "underspecified"}
check(
    declared == set(ABSENCE_CLAIMS),
    f"every underspecified item needs an absence claim; "
    f"missing {declared - set(ABSENCE_CLAIMS)}, extra {set(ABSENCE_CLAIMS) - declared}",
)

# ------------------------------------------------------------------ 3. copier

for q in (x for x in QUESTIONS_L5 if x["band"] == "R"):
    spec = q["expect"]
    if spec["kind"] != "numeric":
        continue
    for value in spec["values"]:
        rounded = round(value, 2)
        # A whole-number band lookup legitimately equals a printed figure; a
        # COMPUTED value must not.
        forms = (
            {f"{rounded:,.2f}", f"{rounded:,.0f}", str(int(rounded))}
            if rounded == int(rounded)
            else {f"{rounded:,.2f}", f"{rounded:.2f}"}
        )
        for form in forms:
            check(
                form not in PACK,
                f"{q['id']}: computed key {form} is PRINTED in the pack - a model that "
                f"copies a number would grade correct and no score could reveal it",
            )

# ------------------------------------------------------------ 4. traps differ

for q in QUESTIONS_L5:
    spec = q["expect"]
    if spec["kind"] == "date":
        for label in ("off_by_calendar", "wrong_trigger"):
            for trap in spec.get(label, ()):
                check(
                    trap != spec["want"],
                    f"{q['id']}: {label} trap {trap} EQUALS the answer - it cannot "
                    f"detect the error it names",
                )
    if spec["kind"] == "numeric":
        for label in ("off_by_calendar", "wrong_trigger", "partial"):
            for trap in spec.get(label, ()):
                check(
                    abs(trap - spec["values"][0]) > 1e-9,
                    f"{q['id']}: {label} trap {trap} EQUALS the answer",
                )

# -------------------------------------------------------------- 5. respondents


def run(name: str, answer_for) -> dict[str, int]:
    counts: dict[str, int] = {}
    for q in QUESTIONS_L5:
        verdict = grade_answer_l5(q, answer_for(q))
        counts[verdict] = counts.get(verdict, 0) + 1
    return counts


def _first_trap(q: dict):
    spec = q["expect"]
    traps = list(spec.get("off_by_calendar", ()))
    return traps[0] if traps else None


N_UNDERSPEC = len(ABSENCE_CLAIMS)
N_TRAPPED = sum(1 for q in QUESTIONS_L5 if _first_trap(q) is not None)

results: dict[str, dict[str, int]] = {}

results["perfect"] = run("perfect", perfect_answer)
check(
    results["perfect"].get("correct") == 24,
    f"`perfect` scored {results['perfect']} - the graders reject their own answer key",
)


def calendar_blind(q: dict) -> str:
    trap = _first_trap(q)
    if trap is None:
        return perfect_answer(q)
    if q["expect"]["kind"] == "date":
        return f"The date is {_fmt_date(trap)}."
    return f"The figure is {trap:,.2f}."


results["calendar_blind"] = run("calendar_blind", calendar_blind)
check(
    results["calendar_blind"].get("off_by_calendar") == N_TRAPPED,
    f"`calendar_blind` should show exactly {N_TRAPPED} off_by_calendar, "
    f"got {results['calendar_blind']}",
)

results["never_declines"] = run(
    "never_declines",
    lambda q: (
        "The figure is 42,000 and the date is 1 January 2027."
        if q["expect"]["kind"] == "underspecified"
        else perfect_answer(q)
    ),
)
check(
    results["never_declines"].get("over_claim") == N_UNDERSPEC,
    f"`never_declines` should show exactly {N_UNDERSPEC} over_claim, "
    f"got {results['never_declines']}",
)

results["always_declines"] = run(
    "always_declines", lambda q: "The documents do not state this."
)
check(
    results["always_declines"].get("correct") == N_UNDERSPEC,
    f"`always_declines` should score exactly the {N_UNDERSPEC} underspecified items, "
    f"got {results['always_declines']}",
)
check(
    results["always_declines"].get("over_claim", 0) == 0,
    "`always_declines` must never over-claim - declining is the safe direction",
)

# The posture check: an answerer that lists every document must NOT score the
# exhaustive item. Without this, "name them all" is a winning strategy.
results["lists_everything"] = run(
    "lists_everything",
    lambda q: (
        "CO-1, CO-2 and CO-3, all three of them."
        if q["expect"]["kind"] == "set"
        else perfect_answer(q)
    ),
)
e05 = next(q for q in QUESTIONS_L5 if q["id"] == "E05")
check(
    grade_answer_l5(e05, "CO-1, CO-2 and CO-3, all three of them.") != "correct",
    "`lists_everything` scores the exhaustive item - a posture wins, and the item "
    "measures nothing",
)

# The trap this bank was nearly shipped with: a correct answer that quotes the
# question's own wording about a document being silent.
check(
    grade_answer_l5(
        next(q for q in QUESTIONS_L5 if q["id"] == "E04"),
        "CO-2 does not state a Notice Period, so the Framework Agreement default of "
        "three months applies under clause 1.3.",
    )
    == "correct",
    "an answer that correctly explains a silence is being scored as a decline - "
    "the positive match must run BEFORE the decline check",
)

# ------------------------------------------------------------------- report

print(
    f"L5 bank: {len(QUESTIONS_L5)} items, "
    f"{sum(1 for q in QUESTIONS_L5 if q['band'] == 'R')} band R / "
    f"{sum(1 for q in QUESTIONS_L5 if q['band'] == 'E')} band E, "
    f"pack {len(PACK):,} chars"
)
for name, counts in results.items():
    print(f"  {name:16s} {counts}")

if failures:
    print(f"\nREFUSED - {len(failures)} check(s) failed:")
    for f in failures:
        print(f"  - {f}")
    raise SystemExit(1)

print("\nall checks passed - the bank may run")
