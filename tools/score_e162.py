#!/usr/bin/env python3
# File: tools/score_e162.py
# Purpose: Score E162 against its pre-registration: pair-level nets per judge, judge agreement, completion before and
# after amendment 1's retries, judging cost, and P1-P10.
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Reads results/e162/judge-<slug>.json (records with outcome x|y|tie|unparsed per pair-task, a first_pass
# copy where amendment 1 re-asked an empty reply) and results/e162/grade.json. A pair-task is decided for an arm only
# when both orders agreed (run_e162 combine); net(P over Q) = tasks decided for P minus tasks decided for Q over the 10
# tasks. Unparsed pair-tasks count for neither side and are reported. Writes results/e162/score.json and prints it.
# Mechanical counts are RAW; hand adjudication lives in results/e162/adjudication.json (not read here).
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/e162"
JUDGES = {"grok": "grok-4.7", "kimi": "kimi-k3.1-pro"}
ARMS = ["C", "G", "L", "M", "X"]
# The first retry process for kimi was stopped after 2 calls to add amendment 1's metadata; its spend was printed in
# the session (0.1344 USD) and is not in the file's spend_redo, which the restarted process wrote afresh.
KIMI_FIRST_REDO_PROCESS_USD = 0.1344


def nets(records: list[dict], key: str) -> dict[str, dict]:
    """net(P over Q) for every ordered pair, from either the final outcome or the first pass."""
    out: dict[str, dict] = {}
    for p, q in itertools.combinations(ARMS, 2):
        rows = [r for r in records if (r["x"], r["y"]) == (p, q)]
        if len(rows) != 10:
            raise ValueError(f"pair {p},{q} has {len(rows)} records, expected 10. hint: judge run incomplete")
        get = (lambda r: (r.get("first_pass") or r)["outcome"]) if key == "first" else (lambda r: r["outcome"])
        wp = sum(get(r) == "x" for r in rows)
        wq = sum(get(r) == "y" for r in rows)
        un = sum(get(r) == "unparsed" for r in rows)
        out[f"{p}>{q}"] = {"net": wp - wq, "for": wp, "against": wq, "ties": 10 - wp - wq - un, "unparsed": un}
        out[f"{q}>{p}"] = {"net": wq - wp, "for": wq, "against": wp, "ties": 10 - wp - wq - un, "unparsed": un}
    return out


def completion(records: list[dict]) -> dict:
    calls_first = sum(
        bool((r.get("first_pass") or r)[f"raw_{k}"].strip()) for r in records for k in ("xy", "yx")
    )
    calls_final = sum(bool(r[f"raw_{k}"].strip()) for r in records for k in ("xy", "yx"))
    pt_first = sum((r.get("first_pass") or r)["outcome"] != "unparsed" for r in records)
    pt_final = sum(r["outcome"] != "unparsed" for r in records)
    retries = [v for r in records for v in r.get("redo", {}).values()]
    return {
        "calls": 2 * len(records),
        "calls_answered_first_pass": calls_first,
        "calls_answered_after_retry": calls_final,
        "pair_tasks_resolved_first_pass": pt_first,
        "pair_tasks_resolved_after_retry": pt_final,
        "retries": len(retries),
        "retry_finish_reasons": {f: sum(v["finish_reason"] == f for v in retries) for f in {v["finish_reason"] for v in retries}},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Score E162 (pair nets, agreement, P1-P10).", epilog="example: tools/score_e162.py")
    ap.parse_args()
    grade = json.loads((OUT / "grade.json").read_text())
    tot = {a: grade[a]["totals"] for a in ARMS}
    res: dict = {"judges": {}}
    recs = {}
    for short, slug in JUDGES.items():
        d = json.loads((OUT / f"judge-{slug}.json").read_text())
        recs[short] = {(r["task"], r["x"], r["y"]): r for r in d["records"]}
        cost_first = d["spend"]["usd_total"]
        cost_redo = d.get("spend_redo", {}).get("usd_total", 0.0) + (KIMI_FIRST_REDO_PROCESS_USD if short == "kimi" else 0.0)
        res["judges"][short] = {
            "model": d["judge"],
            "nets_final": nets(d["records"], "final"),
            "nets_first_pass": nets(d["records"], "first"),
            "completion": completion(d["records"]),
            "usd_first_pass": round(cost_first, 4),
            "usd_retries": round(cost_redo, 4),
            "usd_total": round(cost_first + cost_redo, 4),
        }
    keys = sorted(recs["grok"])
    same = sum(recs["grok"][k]["outcome"] == recs["kimi"][k]["outcome"] for k in keys)
    both = [k for k in keys if "unparsed" not in (recs["grok"][k]["outcome"], recs["kimi"][k]["outcome"])]
    same_both = sum(recs["grok"][k]["outcome"] == recs["kimi"][k]["outcome"] for k in both)
    res["agreement"] = {"identical": same, "of": len(keys), "share": round(same / len(keys), 3),
                        "share_where_both_resolved": round(same_both / len(both), 3), "both_resolved": len(both)}
    n = {j: res["judges"][j]["nets_final"] for j in JUDGES}
    net = lambda pair: [n[j][pair]["net"] for j in JUDGES]  # noqa: E731
    P = {
        "P1": (all(v >= 2 for v in net("C>L")), net("C>L")),
        "P2": (all(v >= 2 for v in net("G>L")), net("G>L")),
        "P3": (all(abs(v) <= 1 for v in net("M>L")), net("M>L")),
        "P4": (all(abs(v) <= 2 for v in net("X>L")), net("X>L")),
        "P5": (tot["L"]["dropped_negatives"] <= 3 and tot["L"]["dropped_negatives"] <= tot["C"]["dropped_negatives"] + 2,
               [tot["L"]["dropped_negatives"], tot["C"]["dropped_negatives"]]),
        "P6": (tot["L"]["trap_hits"] <= 2 and tot["C"]["trap_hits"] <= 2, [tot["L"]["trap_hits"], tot["C"]["trap_hits"]]),
        "P7": (all(tot[a]["fabrication_candidates"] <= 3 for a in ARMS), {a: tot[a]["fabrication_candidates"] for a in ARMS}),
        "P8": (res["agreement"]["share"] >= 0.60, res["agreement"]["share"]),
        "P9": (tot["L"]["wall_s_total"] <= 0.5 * tot["X"]["wall_s_total"], [tot["L"]["wall_s_total"], tot["X"]["wall_s_total"]]),
        "P10": (all(tot[a]["incomplete"] == 0 and tot[a]["think_leaks"] == 0 for a in ARMS),
                {a: [tot[a]["incomplete"], tot[a]["think_leaks"]] for a in ARMS}),
    }
    res["predictions"] = {k: {"held": v[0], "value": v[1]} for k, v in P.items()}
    # Decision rule inputs: every local effort against each frontier arm, per judge.
    res["frontier_vs_local"] = {f"{f}>{loc}": net(f"{f}>{loc}") for f in ("C", "G") for loc in ("L", "M", "X")}
    (OUT / "score.json").write_text(json.dumps(res, indent=1))
    for k, v in res["predictions"].items():
        print(k, "HELD" if v["held"] else "FAILED", v["value"])
    print("agreement", res["agreement"])
    print("frontier vs local (grok, kimi):", res["frontier_vs_local"])
    for j in JUDGES:
        r = res["judges"][j]
        print(j, r["completion"], "usd", r["usd_first_pass"], "+", r["usd_retries"], "=", r["usd_total"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
