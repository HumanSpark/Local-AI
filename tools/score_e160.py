# File: tools/score_e160.py
# Purpose: Score E160 (KFL vs KX) against the prereg's fields and predictions P1-P11.
# Project: sparkbench | Date: 2026-11-13
#
# Overview: Reads results/e160/raw/<arm>/<suite>.json written by the suites' own runners, takes each suite's
# correct count from the runner's own grading (kw-eval via score_kw_eval.score_file), the judge tally from
# results/e160/writing-judge.json, and per-item completion tokens and wall seconds where the runner records them
# (tool use records neither per item, so it is out of the pooled speed figures). Prints a table and each
# prediction's verdict. A missing file or field raises: an absent suite must not score as zero.
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "results/e160/raw"
ARMS = ("KFL", "KX")
MULTI_STEP = {
    "payment_clock",
    "statutory_period",
    "acceptance_window",
    "precedence",
    "conflict",
    "composition",
}
sys.path.insert(0, str(ROOT / "tools"))


def load(arm: str, suite: str) -> dict:
    return json.loads((RAW / arm / f"{suite}.json").read_text())


def kw_scored(arm: str) -> dict:
    import score_kw_eval  # noqa: PLC0415 - tools path set above

    return score_kw_eval.score_file(RAW / arm / "kw.json")


def arm_fields(arm: str) -> dict:
    f: dict = {"tok": [], "wall": []}
    for suite in ("l5", "pr1"):
        d = load(arm, suite)
        f[suite] = d["correct"]
        f[f"{suite}_n"] = d["total"]
        f["tok"] += [r["completion_tokens"] for r in d["results"]]
        f["wall"] += [r["wall_s"] for r in d["results"]]
        if suite == "l5":
            f["l5_cat"] = d["by_category"]
            f["l5_lost"] = {
                r["id"]: r["category"]
                for r in d["results"]
                if r["outcome"] != "correct"
            }
            f["over_claim_l5"] = d["over_claim_rate"]
    pr = load(arm, "pr1")
    f["missed_flag"] = pr["outcome_counts"].get("missed_flag", 0)
    w = load(arm, "writing")
    f["writing"] = sum(r["outcome"] == "correct" for r in w["results"])
    f["tok"] += [r["completion_tokens"] for r in w["results"]]
    f["wall"] += [r["wall_s"] for r in w["results"]]
    k = kw_scored(arm)
    f["kw"], f["kw_n"], f["kw_judge"] = k["correct"], k["n"], k["needs_judge"]
    f["tok"] += [r["completion_tokens"] for r in k["rows"]]
    f["wall"] += [r["wall_s"] for r in k["rows"]]
    # The scorer has no over_claim class: an over-claim is an UNANSWERABLE item answered with a figure, i.e. scored
    # wrong. Unanswerable ids come from the bank itself.
    sys.path.insert(0, str(ROOT / "spikes" / "kw-eval"))
    import kw_items  # noqa: PLC0415

    unanswerable = {
        i["id"] for i in kw_items.ITEMS if i["expect"].get("is_unanswerable")
    }
    f["over_claim_kw"] = sum(
        r["id"] in unanswerable and r["class"] == "wrong" for r in k["rows"]
    )
    f["unanswerable_kw_n"] = len(unanswerable)
    for conv in ("mt-l4", "mt-long"):
        d = load(arm, conv)
        graded = [r for r in d["results"] if r["graded"]]
        f[conv] = sum(r["outcome"] == "correct" for r in graded)
        f[f"{conv}_n"] = len(graded)
        f["tok"] += [r["completion_tokens"] for r in d["results"]]
        f["wall"] += [r["wall_s"] for r in d["results"]]
    t = load(arm, "tooluse")
    f["tooluse"] = sum(r["success_rate"] >= 2 / 3 for r in t["results"])
    f["tooluse_n"] = len(t["results"])
    f["leaks"] = sum(r["leak_runs"] for r in t["results"])
    h = load(arm, "h6-date")
    f["h6"] = sum(r["outcome"] == "correct" for r in h["results"])
    f["h6_n"] = len(h["results"])
    f["wall"] += [r["wall_s"] for r in h["results"]]
    f["tok_median"] = st.median(f["tok"])
    f["wall_median"] = st.median(f["wall"])
    f["wall_total_min"] = sum(f["wall"]) / 60
    return f


def main() -> int:
    F = {a: arm_fields(a) for a in ARMS}
    judge = json.loads((ROOT / "results/e160/writing-judge.json").read_text())["tally"][
        "KFL"
    ]
    rows = [
        ("L5 hard document Q&A", "l5"),
        ("pr1 refuse/comply", "pr1"),
        ("kw-eval real documents", "kw"),
        ("writing grader", "writing"),
        ("conversation l4", "mt-l4"),
        ("conversation long", "mt-long"),
        ("tool use (tasks passed)", "tooluse"),
        ("H6 dates with tool", "h6"),
    ]
    print(f"{'suite':28} {'KFL':>8} {'KX':>8}")
    for name, key in rows:
        n = F["KFL"].get(f"{key}_n", 7)
        print(f"{name:28} {F['KFL'][key]:>5}/{n:<2} {F['KX'][key]:>5}/{n:<2}")
    for a in ARMS:
        f = F[a]
        print(
            f"{a}: tokens_median {f['tok_median']:,.0f}  wall_median {f['wall_median']:.1f} s  "
            f"wall_total {f['wall_total_min']:.1f} min (excl. tool use)  over-claims l5 {f['over_claim_l5']} "
            f"kw {f['over_claim_kw']}  missed_flag {f['missed_flag']}  leaks {f['leaks']}  kw needs_judge {f['kw_judge']}"
        )
    print(f"judge KFL vs KX: {judge}")
    k, x = F["KFL"], F["KX"]
    lost_l5 = set(k["l5_lost"]) - set(x["l5_lost"])
    preds = {
        "P1 L5": k["l5"] >= x["l5"] - 1,
        "P2 kw-eval": k["kw"] >= x["kw"] - 1,
        "P3 pr1 + missed_flag 0": k["pr1"] >= x["pr1"] - 1 and k["missed_flag"] == 0,
        "P4 over_claim 0 both arms": all(
            F[a]["over_claim_l5"] == 0 and F[a]["over_claim_kw"] == 0 for a in ARMS
        ),
        "P5 writing grader": k["writing"] >= x["writing"] - 1,
        "P6 judge losses-wins <= 1": judge["loss"] - judge["win"] <= 1,
        "P7 conversations": all(k[c] >= x[c] - 1 for c in ("mt-l4", "mt-long")),
        "P8 tool use + no leaks": k["tooluse"] >= x["tooluse"] - 1 and k["leaks"] == 0,
        "P9 H6": k["h6"] >= x["h6"] - 1,
        "P10 L5 losses only multi-step": (k["l5"] >= x["l5"])
        or all(k["l5_lost"][i] in MULTI_STEP for i in lost_l5),
        "P11 speed <= 0.5x": k["tok_median"] <= 0.5 * x["tok_median"]
        and k["wall_median"] <= 0.5 * x["wall_median"],
    }
    print()
    for name, ok in preds.items():
        print(("HELD    " if ok else "FAILED  ") + name)
    print(f"\nL5 lost items: KFL {k['l5_lost']}  KX {x['l5_lost']}")
    print(
        f"speed ratio KFL/KX: tokens {k['tok_median'] / x['tok_median']:.2f}  wall {k['wall_median'] / x['wall_median']:.2f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
