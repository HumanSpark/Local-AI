#!/usr/bin/env python3
# File: tools/score_e79.py
# Purpose: Score E79 by BAND and by direction - what the tool converted, what it destroyed, and which of those was infrastructure.
# Project: sparkbench | Date: 2026-08-28
#
# Overview: E79's question is not "did the score go up". A date tool aimed at a
# reasoning band can gain items there and lose items on a band it has no
# business touching, and a total reports one number that hides both. So this
# reports conversions and regressions PER BAND and separates the two kinds of
# regression, because they need different responses:
#
#   capability regression - the model was offered a tool and stopped producing
#                           an answer, or produced a worse one. That is a
#                           property of the configuration and it counts.
#   runner-owned outcome  - transport_failed or truncated. The request never
#                           completed. Folding that into a capability count
#                           would blame the model for an HTTP 500.
#
# The distinction is not academic here: E79 arm B lost six band-E items, five to
# non-termination and one to a server error, and reporting six would have
# overstated the effect by a fifth.

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "spikes" / "ps-eval"))

from questions_l5 import QUESTIONS_L5  # noqa: E402

ANALYSIS_VERSION = "e79-agg-v1-2026-08-28"
ITEMS = {q["id"]: q for q in QUESTIONS_L5}
RUNNER_OWNED = frozenset({"transport_failed", "truncated"})


def load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    rows = {}
    for r in data["results"]:
        item = ITEMS[r["id"]]
        rows[r["id"]] = {
            "outcome": r["outcome"],
            "class": r["class"],
            "band": item["band"],
            # A transport_failed row is written by the harness's exception path
            # and carries no call record. Branch on it rather than defaulting:
            # "the request never completed" and "the model made no call" are
            # different facts and only one of them is about the model.
            "n_calls": None if r["outcome"] in RUNNER_OWNED else r["n_calls"],
        }
    return {
        "label": data["label"],
        "tools": data["tools"],
        "schema_version": data["schema_version"],
        "thinking": data["thinking"],
        "model": data["model"],
        "total_correct": data["correct"],
        "total_tool_calls": data["total_tool_calls"],
        "rule9_breach_acknowledged": data["rule9_breach_acknowledged"],
        "rows": rows,
    }


def band_counts(run: dict[str, Any]) -> dict[str, Any]:
    ok, outcomes, calling = Counter(), {"R": Counter(), "E": Counter()}, Counter()
    for r in run["rows"].values():
        outcomes[r["band"]][r["outcome"]] += 1
        if r["outcome"] == "correct":
            ok[r["band"]] += 1
        if r["n_calls"] is not None and r["n_calls"] >= 1:
            calling[r["band"]] += 1
    return {
        "band_R_correct": ok["R"],
        "band_E_correct": ok["E"],
        "band_R_outcomes": dict(outcomes["R"]),
        "band_E_outcomes": dict(outcomes["E"]),
        "band_R_items_calling": calling["R"],
        "band_E_items_calling": calling["E"],
    }


def compare(base: dict[str, Any], cand: dict[str, Any]) -> dict[str, Any]:
    if set(base["rows"]) != set(cand["rows"]):
        raise ValueError(
            f"item sets differ between {base['label']} and {cand['label']}\n"
            f"hint: both arms must run the same bank, or conversions and "
            f"regressions compare different questions"
        )
    conv: dict[str, list[str]] = {"R": [], "E": []}
    regr_cap: dict[str, list[str]] = {"R": [], "E": []}
    regr_infra: dict[str, list[str]] = {"R": [], "E": []}
    for i, b in base["rows"].items():
        c, band = cand["rows"][i], b["band"]
        if b["outcome"] != "correct" and c["outcome"] == "correct":
            conv[band].append(i)
        elif b["outcome"] == "correct" and c["outcome"] != "correct":
            (regr_infra if c["outcome"] in RUNNER_OWNED else regr_cap)[band].append(i)
    return {
        "baseline": base["label"],
        "candidate": cand["label"],
        "conversions": conv,
        "capability_regressions": regr_cap,
        "infrastructure_regressions": regr_infra,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score E79 per band, separating conversions, capability "
        "regressions and runner-owned failures.",
        epilog="example: python3 tools/score_e79.py results/raw/e79-*-l5.json "
        "--baseline e79-a --out results/raw/e79-scores.json",
    )
    ap.add_argument("files", nargs="+")
    ap.add_argument(
        "--baseline",
        default="e79-a",
        help="label of the arm every other arm is compared against",
    )
    ap.add_argument(
        "--also-baseline",
        default=None,
        help="a SECOND baseline to report against, for the case where the "
        "decision rule says the prompt-change arm is the honest one",
    )
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    runs = {}
    for f in args.files:
        r = load(Path(f))
        runs[r["label"]] = r

    if args.baseline not in runs:
        raise SystemExit(
            f"baseline {args.baseline!r} not among the loaded arms {sorted(runs)}\n"
            f"hint: --baseline takes the arm's label, not its file name"
        )

    print(
        f"{'arm':10s} {'tools':15s} {'total':>7s} {'band R':>8s} {'band E':>8s} "
        f"{'R calling':>10s} {'E calling':>10s}"
    )
    summary = {}
    for label, run in runs.items():
        bc = band_counts(run)
        summary[label] = {
            **{
                k: run[k]
                for k in (
                    "tools",
                    "schema_version",
                    "thinking",
                    "model",
                    "total_correct",
                    "total_tool_calls",
                    "rule9_breach_acknowledged",
                )
            },
            **bc,
        }
        print(
            f"{label:10s} {run['tools']:15s} {run['total_correct']:>4d}/24 "
            f"{bc['band_R_correct']:>6d}/12 {bc['band_E_correct']:>6d}/12 "
            f"{bc['band_R_items_calling']:>10d} {bc['band_E_items_calling']:>10d}"
        )

    comparisons = []
    for base_label in filter(None, (args.baseline, args.also_baseline)):
        for label, run in runs.items():
            if label == base_label:
                continue
            cmp_ = compare(runs[base_label], run)
            comparisons.append(cmp_)
            for band in ("R", "E"):
                conv, cap, infra = (
                    cmp_["conversions"][band],
                    cmp_["capability_regressions"][band],
                    cmp_["infrastructure_regressions"][band],
                )
                if conv or cap or infra:
                    print(
                        f"  {base_label} -> {label} band {band}: "
                        f"+{len(conv)} {conv}  -{len(cap)} {cap}"
                        + (f"  (infra -{len(infra)} {infra})" if infra else "")
                    )

    out = {
        "analysis_version": ANALYSIS_VERSION,
        "arms": summary,
        "comparisons": comparisons,
    }
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
        print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
