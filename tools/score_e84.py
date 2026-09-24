#!/usr/bin/env python3
# File: tools/score_e84.py
# Purpose: Score E84's KA-H2 ladder - the same questions asked at three context sizes, plus the KV-allocation isolator.
# Project: sparkbench | Date: 2026-08-28
#
# Overview: E84 asks the 11 s-items identically in four arms so the ladder is a
# measurement of context handling rather than of three different tests, which is
# what the banked KA-H1 runs actually were. This reads the s-subset out of each
# arm, reports the spread across A/B/C that prediction 2 is scored against, and
# compares D against A to separate "bigger KV allocation" from "bigger pack".
#
# VERDICTS ARE `bool | None`, NEVER STRINGS. score_kw_eval encodes correct as
# True, wrong as False and needs_judge as None. Comparing against "correct"
# silently matches nothing and reports a clean zero - that defect produced a
# wrong E77 result on 2026-08-28 and is why this file says `is True`.

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_kw_eval import score_file  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
RAW = REPO / "results" / "raw"

ARMS = {
    "A": ("e84-a-qwen38.json", "pack s, items s,   -c 32768   (control)"),
    "B": ("e84-b-qwen38.json", "pack m, items s+m, -c 65536"),
    "C": ("e84-c-qwen38.json", "pack l, items s+m+l, -c 131072 (the l pack)"),
    "D": ("e84-d-qwen38.json", "pack s, items s,   -c 131072  (KV isolator)"),
    "E": ("e84-e-qwen38.json", "pack m, items s+m, -c 131072  (clean ladder)"),
}

# The CLEAN ladder. A/B/C co-vary pack size with -c, and arm D showed -c alone
# rewrites 7 of 11 answers and moves a verdict - so nothing in A/B/C can be
# attributed to context CONTENT. D, E and C hold -c at 131072 across packs s, m
# and l, leaving content as the only variable. This is the comparison that
# answers KA-H2; A/B/C answer "what does the banked convention measure".
CLEAN = ["D", "E", "C"]
CLEAN_PACK = {"D": "s", "E": "m", "C": "l"}


def rows_by_id(path: Path) -> tuple[dict[str, dict], dict]:
    """Grade one arm and index its rows. Missing file is fatal - an arm that did
    not run must not be silently read as an arm that scored zero."""
    if not path.exists():
        raise FileNotFoundError(
            f"E84 arm result missing: {path}\n"
            f"hint: run tools/run_e84.sh; a missing arm is not a zero"
        )
    s = score_file(path)
    return {r["id"]: r for r in s["rows"]}, s


def answers_by_id(path: Path) -> dict[str, str]:
    """Answer TEXT, read from the raw record - `score_file` does not carry it.

    Indexed with `[...]`, never `.get`. The first version of this file used
    `row.get("answer")` against a scored row that has no such key, so every
    comparison was None == None and reported 11/11 identical while the verdict
    table showed four items moving. A missing field must raise here, not return
    a sentinel that reads as agreement - the same defect shape as E77's
    `verdict == "correct"` against a `bool | None`.
    """
    data = json.loads(path.read_text())
    out: dict[str, str] = {}
    for rec in data["records"]:
        if "answer" not in rec:
            raise KeyError(
                f"record {rec.get('id')!r} in {path.name} has no 'answer' field\n"
                f"hint: text stability cannot be measured from a scored row; it "
                f"needs the raw record. Do not default this to '' - an absent "
                f"answer compared against another absent answer reads as identical"
            )
        out[rec["id"]] = rec["answer"] or ""
    return out


def main() -> int:
    scored: dict[str, tuple[dict[str, dict], dict]] = {}
    answers: dict[str, dict[str, str]] = {}
    for arm, (fname, _desc) in ARMS.items():
        scored[arm] = rows_by_id(RAW / fname)
        answers[arm] = answers_by_id(RAW / fname)

    # The s-items are the only questions asked identically in all four arms, so
    # they are the ladder. Taken from arm A, which by construction asks exactly
    # them, rather than from the bank - the arm is the ground truth for what ran.
    s_ids = sorted(scored["A"][0])
    print(f"=== E84: the ladder is the {len(s_ids)} s-items: {', '.join(s_ids)} ===\n")

    print(f"{'arm':4s} {'configuration':44s} {'items':>6s} {'s-subset correct':>17s}")
    ladder: dict[str, int] = {}
    for arm, (fname, desc) in ARMS.items():
        rows, s = scored[arm]
        missing = [i for i in s_ids if i not in rows]
        if missing:
            raise SystemExit(
                f"arm {arm} is missing s-items {missing}\n"
                f"hint: every arm must ask all {len(s_ids)} s-items or the ladder "
                f"compares different questions - the defect E84 exists to fix"
            )
        n_ok = sum(1 for i in s_ids if rows[i]["verdict"] is True)
        ladder[arm] = n_ok
        print(f"{arm:4s} {desc:44s} {s['n']:>6d} {n_ok:>13d}/{len(s_ids)}")

    abc = [ladder[a] for a in ("A", "B", "C")]
    spread = max(abc) - min(abc)
    print("\n--- PREDICTION 2: spread of the s-subset across A/B/C ---")
    print(f"    A={ladder['A']}  B={ladder['B']}  C={ladder['C']}   spread = {spread}")
    print("    registered: HELD if spread <= 1, FALSIFIED if >= 2")
    print(f"    -> {'HELD' if spread <= 1 else 'FALSIFIED'}")

    print("\n--- PREDICTION 3: D (big KV, small pack) vs A ---")
    a_rows, d_rows = scored["A"][0], scored["D"][0]
    same_v = sum(1 for i in s_ids if a_rows[i]["verdict"] is d_rows[i]["verdict"])
    same_t = sum(1 for i in s_ids if answers["A"][i] == answers["D"][i])
    print(
        f"    correct: A={ladder['A']}  D={ladder['D']}  "
        f"{'EQUAL' if ladder['A'] == ladder['D'] else 'DIFFER'}"
    )
    print(f"    verdicts identical : {same_v}/{len(s_ids)}")
    print(f"    answers byte-equal : {same_t}/{len(s_ids)}")
    print(
        f"    -> {'HELD' if ladder['A'] == ladder['D'] and same_t >= 9 else 'FALSIFIED'}"
    )

    print("\n--- PREDICTION 4: arm B's m-subset re-controls banked 13/13 ---")
    b_rows = scored["B"][0]
    m_ids = sorted(set(b_rows) - set(s_ids))
    m_ok = sum(1 for i in m_ids if b_rows[i]["verdict"] is True)
    print(f"    m-items in arm B: {len(m_ids)}   correct: {m_ok}/{len(m_ids)}")
    print(f"    -> {'HELD' if (m_ok, len(m_ids)) == (13, 13) else 'FALSIFIED'}")

    print("\n--- PREDICTION 5: nothing runner-owned ---")
    bad = 0
    for arm, (_rows, s) in scored.items():
        tf, tr = s["transport_failed"], s["truncated"]
        bad += tf + tr
        print(
            f"    {arm}: transport_failed={tf}  truncated(hit token cap)={tr}  "
            f"needs_judge={s['needs_judge']} {s['needs_judge_ids']}"
        )
    print(f"    -> {'HELD' if bad == 0 else 'FALSIFIED'} (total {bad})")

    # TEXT STABILITY: the sensitive readout. 11 items resolve to 9 percentage
    # points, so verdict counts can only catch LARGE degradation. Greedy decoding
    # plus identical questions means any perturbation of the model shows up in the
    # answer text long before it changes a verdict - E77 measured q8_0 rewriting 9
    # answers in 10 while moving no verdict at all. A ladder that is stable in
    # VERDICT but unstable in TEXT is a different finding from one stable in both,
    # and only this comparison can tell them apart.
    print("\n--- text stability up the ladder (s-items, vs arm A) ---")
    for arm in ("B", "C", "D"):
        same = sum(1 for i in s_ids if answers["A"][i] == answers[arm][i])
        print(
            f"    A vs {arm}: {same}/{len(s_ids)} answers byte-identical, "
            f"{len(s_ids) - same} rewritten"
        )

    print("\n--- per-item verdicts up the ladder (s-items only) ---")
    print(f"    {'id':5s} {'A':>3s} {'B':>3s} {'C':>3s} {'D':>3s}   moved?")
    sym = {True: "ok", False: "X", None: "?"}
    for i in s_ids:
        v = [scored[a][0][i]["verdict"] for a in ("A", "B", "C", "D")]
        moved = "" if len(set(map(repr, v))) == 1 else "  <-- MOVED"
        print(f"    {i:5s} " + " ".join(f"{sym[x]:>3s}" for x in v) + moved)

    print("\n=== THE CLEAN LADDER: -c held at 131072, only pack content varies ===")
    print(
        f"    {'arm':4s} {'pack':5s} {'s-subset correct':>17s} {'rewritten vs D':>16s}"
    )
    clean_ok: dict[str, int] = {}
    for arm in CLEAN:
        rows = scored[arm][0]
        n_ok = sum(1 for i in s_ids if rows[i]["verdict"] is True)
        clean_ok[arm] = n_ok
        rew = sum(1 for i in s_ids if answers["D"][i] != answers[arm][i])
        print(
            f"    {arm:4s} {CLEAN_PACK[arm]:5s} {n_ok:>13d}/{len(s_ids)} "
            f"{rew:>13d}/{len(s_ids)}"
        )
    cspread = max(clean_ok.values()) - min(clean_ok.values())
    print(f"\n    clean spread (content only) = {cspread}")
    print(
        "    -> "
        + (
            "no capability degradation from context CONTENT at 70,415 tokens"
            if cspread <= 1
            else "context CONTENT degrades capability"
        )
    )

    out = RAW / "e84-scores.json"
    out.write_text(
        json.dumps(
            {
                "s_ids": s_ids,
                "ladder_s_subset": ladder,
                "spread_abc": spread,
                "m_subset_arm_b": {"correct": m_ok, "n": len(m_ids)},
                "d_vs_a": {"verdicts_same": same_v, "answers_identical": same_t},
                "clean_ladder_fixed_ctx": {
                    "arms": {
                        a: {"pack": CLEAN_PACK[a], "correct": clean_ok[a]}
                        for a in CLEAN
                    },
                    "spread": cspread,
                    "n_items": len(s_ids),
                },
                "per_arm": {
                    a: {
                        k: s[k]
                        for k in (
                            "n",
                            "correct",
                            "wrong",
                            "needs_judge",
                            "truncated",
                            "transport_failed",
                            "measured_prompt_tokens",
                            "conditional_ttca_p50",
                            "conditional_ttca_p95",
                            "ttft_median",
                        )
                    }
                    for a, (_r, s) in scored.items()
                },
            },
            indent=2,
        )
    )
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
