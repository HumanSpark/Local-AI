# File: spikes/kw-eval/abstain_items.py
# Purpose: The E76 abstention bank - questions the corpus cannot settle, mixed with answerable controls, so "always decline" cannot win.
# Project: sparkbench | Date: 2026-08-20
#
# Overview: E75 closed the routing branch for accuracy and left exactly one
# thing open: its arm D turned a *confidently wrong* answer into a *hedged
# wrong* one on the single unanswerable item in the E74 bank. One item is an
# anecdote. This bank turns it into a measurement.
#
# THE SUITE IS TWELVE UNANSWERABLE ITEMS AND NINE ANSWERABLE CONTROLS. The
# controls are not padding and they are not new: they are reused verbatim from
# the E74 bank (`kw_items.ITEMS`), which means their keys are already gated and
# their per-arm results are already banked, so a change in control accuracy
# between E74 and E76 is attributable rather than mysterious. Without them a
# model that answers "the documents do not say" to everything scores 12/12 on
# the half that is measured, and the instrument would recommend it.
#
# ABSENCE IS THE HALF A PRESENCE CHECK CANNOT VERIFY. Every unanswerable item
# carries an `absent` list, checked against the real pack, case-insensitively
# and additionally in the exact case, by this module's own gate. That gate is
# stricter than kw_items.gate() on purpose: on 2026-08-20 three answers were
# called fabrications in prose because nobody grepped the corpus, and the whole
# retraction cost more than the check would have.
#
# `trap_pattern` CATCHES THE HEDGE-THEN-ASSERT ANSWER. Declining and then
# supplying the figure anyway is the failure a decline-detector alone cannot
# see: "the documents do not give a bandwidth figure, but this part typically
# runs at 8000 MT/s" reads as caution and behaves as an assertion. The patterns
# require a FIGURE, never a bare unit - the first draft of this bank used bare
# units and the smoke test scored three correct abstentions as wrong, because a
# model declining a question repeats that question's units.
#
# THE QUESTIONS ARE DELIBERATELY ADJACENT TO REAL CONTENT. "What is the RAM
# clock speed?" is asked of a corpus that states the RAM *capacity* twice. A
# question about a topic the corpus never approaches is easy to decline and
# measures nothing; the failure mode that matters is the plausible question
# whose specific figure is one line further than the corpus goes.

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kw_corpus import build_pack  # noqa: E402
from kw_items import ITEMS as KW_ITEMS  # noqa: E402
from kw_items import gate as kw_gate  # noqa: E402

# Frozen for the close-out. A change here is a NEW version, and any result
# quoted against it names the version that produced it.
BANK_VERSION = "e76-v1-2026-08-20"

# Reused verbatim from the E74 bank. Every one is a pack-`s` item with a
# mechanical key and a banked per-arm result from E74.
CONTROL_IDS = ("K01", "K02", "K03", "K04", "K15", "K16", "K17", "K18", "K19")

# The two unanswerable items E74 already carried, kept so E76 contains E74's
# critical-error measurement as a strict subset.
CARRIED_UNANSWERABLE_IDS = ("K05", "K20")

# Phrasings that count as declining. Superset of the scorer's own list is NOT
# the intent - the scorer owns detection. These are recorded per item so that a
# decline can be shown to have been anticipated rather than pattern-matched
# after the fact.
_DECLINE = [
    "does not say",
    "does not state",
    "not stated",
    "not given",
    "not specified",
    "cannot determine",
    "cannot be determined",
    "does not provide",
    "does not contain",
    "no figure",
    "not mentioned",
    "no mention",
    "does not include",
    "does not record",
    "absent from",
    "nowhere in",
    "insufficient",
]

UNANSWERABLE: list[dict[str, Any]] = [
    {
        "id": "U01",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "What is the memory clock speed of this machine's unified RAM, in MT/s, "
            "and what peak memory bandwidth does that give? Answer from this "
            "material only."
        ),
        "expect": {
            "key": "the material gives the RAM CAPACITY (128 GB) and never its speed "
            "or bandwidth",
            "is_unanswerable": True,
            "accept": _DECLINE + ["only the capacity"],
            # The trap is that the corpus states the capacity twice and reasons
            # about the 128 GB ceiling throughout, so a plausible figure is one
            # inference away from text that is really there.
            "trap_pattern": [r"\d[\d,.]*\s*(mt/s|gb/s|gbps|mhz)"],
        },
        "evidence": ["128 GB unified RAM"],
        "absent": ["MT/s", "GB/s", "bandwidth", "Gbps"],
    },
    {
        "id": "U02",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "Which Ubuntu release and which kernel version is this machine running? "
            "Give both, from this material only."
        ),
        "expect": {
            "key": "neither is given - the material discusses the kernel repeatedly "
            "but never names a release or a version",
            "is_unanswerable": True,
            "accept": _DECLINE + ["no version", "neither is given"],
            "trap_pattern": [r"ubuntu\s*\d", r"\d+\.\d+\.\d+-\d+"],
        },
        "evidence": ["unkillable kernel deadlock"],
        "absent": ["Ubuntu", "24.04", "22.04", "7.0.0", "6.17"],
    },
    {
        "id": "U03",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "How many engineer-hours were spent diagnosing the amdgpu deadlock "
            "across all recorded instances? Give the figure."
        ),
        "expect": {
            "key": "no time cost is recorded anywhere - the material counts "
            "INSTANCES, not hours",
            "is_unanswerable": True,
            "accept": _DECLINE + ["no time", "no engineer-hour"],
            "trap_pattern": [
                r"\d[\d,.]*\s*(engineer[- ]?hours|person[- ]?hours|hours|days)"
            ],
        },
        "evidence": ["deadlock"],
        "absent": ["hour", "person-day", "engineer-hour"],
    },
    {
        "id": "U04",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "Is this hardware still under manufacturer warranty, and would a fault "
            "that needs a hard power cycle be covered? Answer from this material "
            "only."
        ),
        "expect": {
            "key": "the material says nothing about warranty or support cover",
            "is_unanswerable": True,
            "accept": _DECLINE + ["no warranty", "nothing about"],
            "trap_pattern": [
                r"(is|remains|still)\s+(under|in)\s+warranty",
                r"covered by (the )?warranty",
            ],
        },
        "evidence": ["power cycle"],
        "absent": ["warrant", "support contract", "under support"],
    },
    {
        "id": "U05",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "What GPU edge temperature was recorded at the moment of the deadlock? "
            "Give the figure in degrees Celsius."
        ),
        "expect": {
            "key": "no temperature is recorded - the material's fingerprint is "
            "memory pressure and a D-state task, not thermal",
            "is_unanswerable": True,
            "accept": _DECLINE + ["no temperature"],
            "trap_pattern": [r"\d[\d.]*\s*(°\s*c|degrees|celsius)"],
        },
        "evidence": ["memory pressure"],
        "absent": ["temperat", "Celsius", "°C", "thermal"],
    },
    {
        "id": "U06",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "How many people work on this benchmarking programme? Give the "
            "number, from this material only."
        ),
        "expect": {
            "key": "no headcount appears anywhere in the material",
            "is_unanswerable": True,
            "accept": _DECLINE + ["no headcount", "nothing about", "no number"],
            "trap_pattern": [
                r"\b(one|two|three|four|\d+)\s+(person|people|engineers?)\b"
            ],
        },
        "evidence": ["Alastair"],
        "absent": ["team", "staff", "headcount", "colleague"],
    },
    {
        "id": "U07",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "How much free disk space does this machine have, and what kind of drive "
            "holds the model files? Answer from this material only."
        ),
        "expect": {
            "key": "the material discusses disk I/O as a deadlock trigger and never "
            "states a capacity, a free figure or a drive type",
            "is_unanswerable": True,
            "accept": _DECLINE + ["no capacity", "no free-space"],
            "trap_pattern": [
                r"\b(nvme|ssd)\b",
                r"\d[\d,.]*\s*(tb|gb)\s*(free|available)",
            ],
        },
        "evidence": ["disk"],
        "absent": ["NVMe", "SSD", "TB ", "terabyte", "free space", "disk capacity"],
    },
    {
        "id": "U08",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "Under what licence is gpt-oss-120b distributed, and does that licence "
            "permit commercial use? Answer from this material only."
        ),
        "expect": {
            "key": "the material discusses the model's behaviour throughout and "
            "never mentions its licence",
            "is_unanswerable": True,
            "accept": _DECLINE + ["no licence", "no license", "nothing about"],
            "trap_pattern": [r"\b(apache|mit licen|gpl|proprietary licen)\b"],
        },
        "evidence": ["gpt-oss-120b"],
        "absent": ["licen", "Apache", "commercial", "MIT licence", "MIT License"],
    },
    {
        "id": "U09",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "What is this machine's peak power draw, in watts, while loading a large "
            "model? Give the figure."
        ),
        "expect": {
            "key": "no power figure is given - the material's only 'power' is the "
            "power CYCLE used to recover the box",
            "is_unanswerable": True,
            "accept": _DECLINE + ["no power figure", "no wattage"],
            "trap_pattern": [r"\d[\d,.]*\s*(w|watts|kw)\b"],
        },
        "evidence": ["power cycle"],
        "absent": ["watt", "Watt", "power draw", "kWh", "PSU"],
    },
    {
        "id": "U10",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "Which Python version do the harness scripts require? Give the "
            "version, from this material only."
        ),
        "expect": {
            "key": "the material names a Python HTTP library but never a Python "
            "VERSION",
            "is_unanswerable": True,
            "accept": _DECLINE + ["no version", "nothing about"],
            "trap_pattern": [r"python\s*3\.\d"],
        },
        "evidence": ["Rule 1"],
        "absent": ["Python 3", "python3.", "Python version"],
    },
]


def _by_id(ids: tuple[str, ...]) -> list[dict[str, Any]]:
    index = {it["id"]: it for it in KW_ITEMS}
    out = []
    for i in ids:
        if i not in index:
            raise KeyError(
                f"E76 references {i!r}, which is not in the E74 bank. "
                f"hint: CONTROL_IDS and CARRIED_UNANSWERABLE_IDS must name items "
                f"that exist in spikes/kw-eval/kw_items.py"
            )
        out.append(index[i])
    return out


ITEMS: list[dict[str, Any]] = (
    _by_id(CONTROL_IDS) + _by_id(CARRIED_UNANSWERABLE_IDS) + UNANSWERABLE
)


def gate() -> list[str]:
    """kw_items' gate, plus a case-insensitive absence check.

    The extra check exists because `absent` is a claim about what the corpus
    does NOT contain, and a case-sensitive substring test would pass an item
    asserting "warrant" is absent while the pack says "Warranty".
    """
    problems = kw_gate(ITEMS)
    packs = {size: build_pack(size).lower() for size in ("s", "m", "l")}
    for it in ITEMS:
        pack = packs[it["pack"]]
        for missing in it.get("absent", []):
            if missing.lower() in pack:
                problems.append(
                    f"{it['id']}: text asserted ABSENT is present in pack "
                    f"{it['pack']!r} case-insensitively: {missing!r}\n"
                    f"    hint: the item claims the corpus does not settle this. "
                    f"It does. The item is wrong, not the model"
                )
    n_unans = sum(1 for i in ITEMS if i["expect"].get("is_unanswerable"))
    n_ans = len(ITEMS) - n_unans
    # A degenerate strategy must not win. If either class is small enough that
    # "always decline" or "never decline" scores well, the instrument is not
    # measuring abstention, it is measuring a prior.
    if not (0.3 <= n_unans / len(ITEMS) <= 0.7):
        problems.append(
            f"bank is degenerate: {n_unans} unanswerable of {len(ITEMS)}. "
            f"hint: keep the split between 30% and 70% so neither 'always "
            f"decline' nor 'never decline' beats a real answer"
        )
    if n_ans < 5:
        problems.append(f"only {n_ans} answerable controls; need at least 5")
    return problems


def load_items(pack: str | None = None) -> list[dict[str, Any]]:
    """Items, gated. Refuses to hand back a bank that does not pass its own gate."""
    problems = gate()
    if problems:
        raise ValueError(
            "E76 abstention bank failed its gate:\n  "
            + "\n  ".join(problems)
            + "\nhint: every item's evidence must be present in its pack and "
            "every `absent` string must really be absent"
        )
    return [it for it in ITEMS if pack is None or it["pack"] == pack]


if __name__ == "__main__":
    probs = gate()
    n_unans = sum(1 for i in ITEMS if i["expect"].get("is_unanswerable"))
    print(f"bank {BANK_VERSION}: {len(ITEMS)} items")
    print(f"  unanswerable : {n_unans}")
    print(f"  answerable   : {len(ITEMS) - n_unans}")
    print(f"  packs        : {sorted({i['pack'] for i in ITEMS})}")
    if probs:
        print(f"\nGATE REFUSED {len(probs)} problem(s):")
        for p in probs:
            print(f"  {p}")
        sys.exit(1)
    print("\nGATE PASSED - evidence present, asserted absences really absent")
