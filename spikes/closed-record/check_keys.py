#!/usr/bin/env python3
# File: check_keys.py
# Purpose: Gate every sealed key against the authoring rules before it is ever scored against.
# Project: sparkbench | Date: 2026-08-12
#
# Overview: A wrong key makes every downstream number wrong, and unlike a model answer it is
# never re-derived - it is written once and trusted forever. This checks the properties that can
# be checked mechanically: required fields present, every proposition carrying its named failure
# mode and its derivation, no trap value that is also a correct answer, and no two OWNERS
# (elements, traps) accepting the same normalised value. Comparison is across owners only -
# several surface forms of one proposition are the point of the values set, not a collision.
# The quiet defect this exists for: bare "100" against "9,100", which naive tokenisation splits
# into ["9", "100"] so the wrong proposition scores a hit. Real, found in m02's first draft.
# Schema: schema/key.yaml. Plan: docs/plans/2026-08-12-closed-record-reasoning-PLAN.md task 6.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from typography import TYPOGRAPHY_VERSION, fold, fold_digit_groups  # noqa: E402,F401

# The normalisation has a version because it has been wrong once by omission.
#
#   v1  2026-08-12  ASCII comma stripped, currency prefix stripped, .00 trimmed
#   v2  2026-08-20  F95 typography fold added. v1 stripped the ASCII comma and
#                   nothing else, so "8 388.60" written with a NARROW NO-BREAK
#                   SPACE, or a value carrying a NON-BREAKING HYPHEN, compared
#                   as a different value from its ASCII twin. The F95 audit
#                   listed five substring scorers and did not reach this one;
#                   it is the third instance of the same defect and is fixed
#                   here in the same pass as the second.
NORMALISE_VERSION = f"keys-v2-2026-08-20+{TYPOGRAPHY_VERSION}"

REQUIRED_KEY_FIELDS = ("matter", "source", "proposition", "required")
REQUIRED_ELEMENT_FIELDS = ("id", "statement", "values", "missed", "derivation")
REQUIRED_TRAP_FIELDS = ("value", "displaces", "why")

# Currency prefixes a model may or may not write. Stripped before comparison so that
# "EUR 100" and "100" are recognised as the same claim rather than two.
CURRENCY_PREFIXES = ("eur ", "eur", "€", "e ")


def normalise(value: str) -> str:
    """The comparison form: what the scorer must reduce a value to before matching.

    Typography is formatting too, and so are thousands separators and trailing zero decimals -
    none of them is correctness - the E10 key
    already learned that when an assertion on "8,388.60" failed two models that answered the
    numerically identical "8388.60". Stripping separators is also what makes WHOLE-TOKEN matching
    possible: "9,100" naively tokenises to ["9", "100"], so a bare "100" would match it and
    credit the wrong proposition.
    """
    v = fold(value).strip().lower()
    for prefix in CURRENCY_PREFIXES:
        if v.startswith(prefix):
            v = v[len(prefix) :].strip()
            break
    v = fold_digit_groups(v).replace(",", "")
    if v.endswith(".00"):
        v = v[:-3]
    return v


def is_numeric(value: str) -> bool:
    return normalise(value).replace(".", "", 1).isdigit()


def load_keys(matters_dir: Path) -> dict[str, dict]:
    """Every key.yaml under matters/, addressed by its directory name."""
    if not matters_dir.exists():
        raise FileNotFoundError(
            f"matters directory not found: {matters_dir}; "
            f"hint: matters live in spikes/closed-record/matters/<id>-<slug>/"
        )
    keys: dict[str, dict] = {}
    for key_path in sorted(matters_dir.glob("*/key.yaml")):
        keys[key_path.parent.name] = yaml.safe_load(key_path.read_text())
    if not keys:
        raise ValueError(
            f"no key.yaml found under {matters_dir}; "
            f"hint: each matter directory needs both matter.md and key.yaml"
        )
    return keys


def check_key(name: str, key: dict) -> list[str]:
    """Return one problem string per defect. An empty list is the pass state."""
    problems: list[str] = []

    for field in REQUIRED_KEY_FIELDS:
        if field not in key:
            problems.append(f"{name}: missing top-level field '{field}'")
    if "required" not in key:
        return problems

    seen_ids: set[int] = set()
    for el in key["required"]:
        for field in REQUIRED_ELEMENT_FIELDS:
            if field not in el:
                problems.append(
                    f"{name}: element {el.get('id', '?')} missing '{field}'"
                )
        el_id = el.get("id")
        if el_id in seen_ids:
            problems.append(f"{name}: duplicate element id {el_id}")
        seen_ids.add(el_id)
        if not el.get("values"):
            problems.append(f"{name}: element {el_id} has an empty values set")

    # Every trap must name the proposition it displaces. Without it the scorer cannot tell a
    # model that quoted a distractor and rejected it from one that gave it as the answer, and
    # would penalise the behaviour the traps exist to reward.
    element_ids = {el.get("id") for el in key["required"]}
    for trap in key.get("traps", []):
        for field in REQUIRED_TRAP_FIELDS:
            if field not in trap:
                problems.append(
                    f"{name}: trap '{trap.get('value', '?')}' missing '{field}'"
                )
        if "displaces" in trap and trap["displaces"] not in element_ids:
            problems.append(
                f"{name}: trap '{trap['value']}' displaces element "
                f"{trap['displaces']}, which does not exist"
            )

    # Values are compared ACROSS owners only. Several surface forms of one proposition
    # ("2,980", "2980", "2,980.00") are the point of the values SET, not a collision.
    owners: list[tuple[str, list[str]]] = [
        (f"element {el['id']}", el.get("values", [])) for el in key["required"]
    ]
    owners += [(f"trap {t['value']}", [t["value"]]) for t in key.get("traps", [])]

    for i, (owner_a, values_a) in enumerate(owners):
        for owner_b, values_b in owners[i + 1 :]:
            norm_a = {normalise(v) for v in values_a}
            norm_b = {normalise(v) for v in values_b}
            for shared in sorted(norm_a & norm_b):
                problems.append(
                    f"{name}: {owner_a} and {owner_b} both accept '{shared}' - one answer "
                    f"cannot satisfy two propositions, and a trap that is also a correct "
                    f"answer marks a right answer wrong"
                )
            # Substring collisions only matter where whole-token numeric matching cannot be
            # used. Two numbers that differ are safely distinguishable once separators are
            # stripped; free text has no token boundary to rely on.
            for a in values_a:
                for b in values_b:
                    if is_numeric(a) and is_numeric(b):
                        continue
                    na, nb = normalise(a), normalise(b)
                    if na != nb and (na in nb or nb in na):
                        problems.append(
                            f"{name}: {owner_a} '{a}' and {owner_b} '{b}' overlap as "
                            f"substrings, and neither is a plain number that could be matched "
                            f"on token boundaries"
                        )
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Check sealed keys against the authoring rules.",
        epilog="Example: python3 check_keys.py",
    )
    ap.add_argument("--matters-dir", default=str(Path(__file__).parent / "matters"))
    args = ap.parse_args()

    keys = load_keys(Path(args.matters_dir))
    all_problems: list[str] = []
    for name, key in keys.items():
        problems = check_key(name, key)
        all_problems += problems
        n_el = len(key.get("required", []))
        n_trap = len(key.get("traps", []))
        status = "OK" if not problems else f"{len(problems)} PROBLEM(S)"
        print(f"{name:<28} {n_el} propositions, {n_trap} traps  {status}")

    if all_problems:
        print()
        for p in all_problems:
            print(f"  ! {p}")
        return 1
    print("\nAll keys pass.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
