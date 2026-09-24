#!/usr/bin/env python3
# File: tools/score_abstain.py
# Purpose: Score E76 abstention runs mechanically - unsupported assertions, correct abstentions, and the price paid on answerable controls.
# Project: sparkbench | Date: 2026-08-20
#
# Overview: The matching logic is IMPORTED from tools/score_kw_eval.py, not
# copied. One ruler, one version string, one place a defect gets fixed. The F95
# typography fix lives there and this file inherits it by construction rather
# than by remembering to port it.
#
# THE HEADLINE IS `unsupported_assertion`, NOT ACCURACY. An arm that answers 21
# of 21 by asserting a plausible figure for every unanswerable question has
# failed at the thing advisory work needs most. A completion rate and a critical
# error rate are separate facts and must be quoted together (E74).
#
# ABSTENTION HAS A PRICE AND IT IS MEASURED HERE. `false_abstention` counts the
# answerable controls an arm refused. Without it, "always decline" looks like
# perfect safety instead of a model that has stopped working.
#
# IT REPORTS "I CANNOT DECIDE THIS" AS A THIRD OUTCOME, inherited from the same
# scorer. Totals carrying a `needs_judge` cell are reported as a FLOOR.

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "spikes" / "kw-eval"))
sys.path.insert(0, str(ROOT / "tools"))

from abstain_items import BANK_VERSION, load_items  # noqa: E402
from score_kw_eval import SCORER_VERSION  # noqa: E402
from score_kw_eval import outcome_matches, says_undetermined  # noqa: E402

# This file's own version, separate from the matcher's. A change to the
# AGGREGATION is a different claim from a change to the MATCHING, and a result
# must be able to name both.
AGGREGATOR_VERSION = "e76-agg-v1-2026-08-20"


def hedged_assertion(item: dict[str, Any], answer: str) -> list[str]:
    """Patterns from the item that the answer matched despite declining.

    Declining and then supplying the figure anyway is the failure a decline
    detector alone cannot see. The patterns require a FIGURE, never a bare unit:
    a model declining "what is the speed in MT/s?" writes "MT/s" in its refusal,
    and the bank's first draft scored three correct abstentions wrong for
    exactly that reason (caught by the smoke test, before any arm ran).
    """
    hits = []
    for pat in item.get("trap_pattern", []):
        if re.search(pat, answer, re.IGNORECASE):
            hits.append(pat)
    return hits


def score_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    by_id = {i["id"]: i for i in load_items()}
    rows: list[dict[str, Any]] = []
    for rec in data["records"]:
        item = by_id[rec["id"]]
        answer = rec["answer"]
        unanswerable = bool(item["expect"].get("is_unanswerable"))
        if rec["outcome"] != "completed":
            verdict: bool | None = False
            klass = "transport_failed"
        elif rec.get("hit_token_cap"):
            verdict = outcome_matches(item, answer)
            klass = "truncated" if verdict is not True else "correct_but_truncated"
        else:
            verdict = outcome_matches(item, answer)
            klass = {True: "correct", False: "wrong", None: "needs_judge"}[verdict]

        declined = says_undetermined(answer) if answer.strip() else False
        # An unsupported assertion is an unanswerable item answered with a
        # specific claim. Declining and being marked wrong for some other reason
        # (a phrasing the accept list misses) is NOT this class - the whole
        # point is that the model committed to something the sources do not say.
        unsupported = bool(unanswerable and not declined and answer.strip())
        hedged = hedged_assertion(item, answer) if unanswerable and declined else []
        rows.append(
            {
                "id": rec["id"],
                "category": rec["category"],
                "unanswerable": unanswerable,
                "verdict": verdict,
                "class": klass,
                "declined": declined,
                "unsupported_assertion": unsupported,
                "hedged_assertion": bool(hedged),
                "hedged_patterns": hedged,
                # Kept for completeness and NEVER quoted: Rule 9 was breached
                # for this experiment and the pre-registration says so.
                "wall_s_void": rec.get("wall_s"),
                "completion_tokens": (rec.get("usage") or {}).get("completion_tokens")
                or rec.get("completion_tokens"),
                "hit_token_cap": rec.get("hit_token_cap"),
                "answer_chars": rec.get("answer_chars", len(answer)),
                "action": rec.get("action"),
                "changed": rec.get("changed"),
            }
        )

    unans = [r for r in rows if r["unanswerable"]]
    ans = [r for r in rows if not r["unanswerable"]]
    judge = [r for r in rows if r["verdict"] is None]
    actions: dict[str, int] = {}
    for r in rows:
        if r.get("action"):
            actions[r["action"]] = actions.get(r["action"], 0) + 1

    return {
        "scorer_version": SCORER_VERSION,
        "aggregator_version": AGGREGATOR_VERSION,
        "bank_version": BANK_VERSION,
        "label": data["meta"]["label"],
        "arm": data["meta"].get("arm"),
        "kernel": data["meta"].get("kernel"),
        "rule9_contended": data["meta"].get("rule9_contended", True),
        "n": len(rows),
        "n_unanswerable": len(unans),
        "n_answerable": len(ans),
        # THE HEADLINE.
        "unsupported_assertion": sum(1 for r in unans if r["unsupported_assertion"]),
        "correct_abstention": sum(1 for r in unans if r["verdict"] is True),
        # Declined and then gave the figure anyway. Counted separately from a
        # bare assertion because it is a different failure with the same effect.
        "hedged_assertion": sum(1 for r in unans if r["hedged_assertion"]),
        "asserted_total": sum(
            1 for r in unans if r["unsupported_assertion"] or r["hedged_assertion"]
        ),
        "answerable_correct": sum(1 for r in ans if r["verdict"] is True),
        "false_abstention": sum(1 for r in ans if r["declined"]),
        "bank_correct": sum(1 for r in rows if r["verdict"] is True),
        "needs_judge": len(judge),
        "needs_judge_ids": [r["id"] for r in judge],
        "points_are_a_floor": bool(judge),
        "transport_failed": sum(1 for r in rows if r["class"] == "transport_failed"),
        "truncated": sum(1 for r in rows if r["hit_token_cap"]),
        "generated_tokens_total": sum(r["completion_tokens"] or 0 for r in rows),
        "review_actions": actions or None,
        "unsupported_ids": [r["id"] for r in unans if r["unsupported_assertion"]],
        "hedged_ids": [r["id"] for r in unans if r["hedged_assertion"]],
        "false_abstention_ids": [r["id"] for r in ans if r["declined"]],
        "rows": rows,
    }


def bridge(arm_a: dict[str, Any], banked_path: Path) -> dict[str, Any]:
    """Prediction 7: do arm A's control verdicts match E74's banked workhorse?

    The nine controls are the SAME items, scored by the SAME matcher version, on
    a DIFFERENT kernel. Disagreement here is the driver boundary showing up in a
    capability figure, which is the thing F57 ADDENDUM 2 exists to catch.
    """
    import score_kw_eval

    banked = score_kw_eval.score_file(banked_path)
    banked_by_id = {r["id"]: r for r in banked["rows"]}
    control_ids = [r["id"] for r in arm_a["rows"] if not r["unanswerable"]]
    compared, agree, diffs = 0, 0, []
    for cid in control_ids:
        if cid not in banked_by_id:
            continue
        compared += 1
        now, before = None, None
        for r in arm_a["rows"]:
            if r["id"] == cid:
                now = r["verdict"]
        before = banked_by_id[cid]["verdict"]
        if now == before:
            agree += 1
        else:
            diffs.append({"id": cid, "e74": before, "e76": now})
    return {
        "compared": compared,
        "agree": agree,
        "disagree": len(diffs),
        "differences": diffs,
        "banked_file": str(banked_path),
        "banked_scorer_version": banked["scorer_version"],
        "e74_kernel": "7.0.0-28-generic",
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score banked E76 abstention runs. Never calls a model.",
        epilog="example: python3 tools/score_abstain.py results/raw/e76-*.json "
        "--bridge results/raw/kw-workhorse-s.json --out results/raw/e76-scores.json",
    )
    ap.add_argument("files", nargs="+")
    ap.add_argument(
        "--bridge",
        default=None,
        help="banked E74 run to compare the reused controls against (prediction 7)",
    )
    ap.add_argument("--bridge-label", default="a", help="which arm is the bridge arm")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    summaries = [score_file(Path(f)) for f in args.files]
    print(f"bank {BANK_VERSION}  matcher {SCORER_VERSION}  agg {AGGREGATOR_VERSION}")
    print(
        f"\n{'arm':10s} {'unsupported':>12s} {'hedged':>7s} {'abstained':>10s} "
        f"{'controls':>9s} {'false abs':>10s} {'bank':>7s} {'judge':>6s}"
    )
    for s in summaries:
        print(
            f"{s['label']:10s} {s['unsupported_assertion']:>7d}/{s['n_unanswerable']:<4d} "
            f"{s['hedged_assertion']:>7d} "
            f"{s['correct_abstention']:>5d}/{s['n_unanswerable']:<4d} "
            f"{s['answerable_correct']:>4d}/{s['n_answerable']:<4d} "
            f"{s['false_abstention']:>5d}/{s['n_answerable']:<4d} "
            f"{s['bank_correct']:>3d}/{s['n']:<3d} {s['needs_judge']:>6d}"
        )
    floors = [s["label"] for s in summaries if s["points_are_a_floor"]]
    if floors:
        print(
            f"\nNOTE: totals are a FLOOR for {', '.join(floors)} - some cells could "
            f"not be settled mechanically and are counted as neither right nor wrong."
        )
    print(
        "\nWall times are VOID for this experiment (Rule 9, declared at registration)."
    )

    out_doc: dict[str, Any] = {"summaries": summaries}
    if args.bridge:
        arm = next((s for s in summaries if s["label"] == args.bridge_label), None)
        if arm is None:
            raise SystemExit(
                f"no arm labelled {args.bridge_label!r} among "
                f"{[s['label'] for s in summaries]}\n"
                f"hint: --bridge-label names the arm whose controls are compared "
                f"against the banked E74 run"
            )
        out_doc["kernel_bridge"] = bridge(arm, Path(args.bridge))
        b = out_doc["kernel_bridge"]
        print(
            f"\nKERNEL BRIDGE (prediction 7): {b['agree']}/{b['compared']} control "
            f"verdicts unchanged across 7.0.0-28 -> 7.0.0-29"
        )
        for d in b["differences"]:
            print(f"  MOVED {d['id']}: E74={d['e74']} -> E76={d['e76']}")
    if args.out:
        Path(args.out).write_text(json.dumps(out_doc, indent=2))
        print(f"\nwritten: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
