# File: tools/score_e159.py
# Purpose: Score E159 arms against the prereg's fields (pass_count, tokens_median, wall_median_s) and P1-P6.
# Project: sparkbench | Date: 2026-11-13
#
# Overview: reads results/e159/raw/<arm>/<task>.json (top level only; superseded/ is ignored), prints per-arm fields,
# a per-task pass grid in bank order, and each prediction's verdict. Missing arms raise rather than score as zero.
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/bench/sparkbench")
ARMS = ["HF", "HFL", "HM", "HL", "HX"]
bank = [
    json.loads(line)["id"]
    for line in (ROOT / "results/e156/bank.jsonl").read_text().splitlines()
    if line.strip()
]


def load(arm: str) -> dict[str, dict]:
    recs = {}
    for f in sorted((ROOT / "results/e159/raw" / arm).glob("*.json")):
        r = json.loads(f.read_text())
        recs[r["task"]] = r
    if len(recs) != len(bank):
        raise SystemExit(
            f"{arm}: {len(recs)} records, bank has {len(bank)}. hint: arm incomplete, do not score yet"
        )
    return recs


data = {a: load(a) for a in ARMS}
F = {}
for a, recs in data.items():
    rs = list(recs.values())
    F[a] = {
        "pass_count": sum(r["status"] == "pass" for r in rs),
        "tokens_median": st.median(r["usage"]["completion_tokens"] for r in rs),
        "wall_median_s": st.median(r["wall_time"] for r in rs),
        "wall_total_h": sum(r["wall_time"] for r in rs) / 3600,
    }
    f = F[a]
    print(
        f"{a:4} pass {f['pass_count']}/10  tokens_median {f['tokens_median']:,.0f}  "
        f"wall_median {f['wall_median_s']:.0f} s ({f['wall_median_s'] / 60:.1f} min)  total {f['wall_total_h']:.2f} h"
    )

print("\nper task (P pass, . fail):")
print("task".ljust(34) + " ".join(a.rjust(4) for a in ARMS))
for t in bank:
    print(
        t.ljust(34)
        + " ".join(
            ("P" if data[a][t]["status"] == "pass" else ".").rjust(4) for a in ARMS
        )
    )

hm, hx, hl, hf = F["HM"], F["HX"], F["HL"], F["HF"]
preds = {
    "P1 HM tokens_median <= 0.5 x HX": hm["tokens_median"] <= 0.5 * hx["tokens_median"],
    "P2 HM pass_count >= HX - 1": hm["pass_count"] >= hx["pass_count"] - 1,
    "P3 HL pass_count <= HM": hl["pass_count"] <= hm["pass_count"],
    "P4 HF pass within 1 of HM AND tokens within 25%": abs(
        hf["pass_count"] - hm["pass_count"]
    )
    <= 1
    and abs(hf["tokens_median"] - hm["tokens_median"]) <= 0.25 * hm["tokens_median"],
    "P5 HX pass_count >= 8": hx["pass_count"] >= 8,
    "P6 HX wall_median_s >= 3 x HM": hx["wall_median_s"] >= 3 * hm["wall_median_s"],
}
print()
for k, v in preds.items():
    print(("HELD    " if v else "FAILED  ") + k)
print(
    f"\nP4 detail: HF tokens {hf['tokens_median']:,.0f} vs HM {hm['tokens_median']:,.0f} "
    f"({(hf['tokens_median'] / hm['tokens_median'] - 1) * 100:+.0f}%)"
)
