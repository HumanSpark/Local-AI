# File: tools/e161_skew.py
# Purpose: Read E161's llama-imatrix GGUF files and report how concentrated MoE expert routing is, per corpus and layer.
# Project: sparkbench | Date: 2026-11-15
#
# Overview: llama-imatrix (tools/imatrix/imatrix.cpp, llama.cpp e574a17) writes, for every matrix it saw, a tensor
# "<name>.counts" of shape [n_mat]; for a MoE expert tensor n_mat = n_expert and counts[e] is the number of tokens
# routed to expert e (imatrix.cpp line ~657). Per layer this takes ONE routed-expert tensor (gate/up/gate_up "_exps",
# which all see identical routing; the choice is printed) and computes the prereg's fields: cov20 / cov10 (share of
# routes to the top 20% / 10% of experts), dead (experts never routed) and the top-20% expert set, then
# jaccard_top20 between corpora. Writes results/e161/skew.json and prints the medians. Missing layers or a wrong
# expert count raise: a partial file must not score as a skew result.
from __future__ import annotations

import argparse
import itertools
import json
import re
import statistics as st
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "llama.cpp/wt/e574a17/gguf-py"))
import gguf  # noqa: E402

N_LAYER, N_EXPERT = 48, 512
PREF = ("ffn_gate_up_exps", "ffn_up_exps", "ffn_gate_exps")


def layer_counts(path: Path) -> tuple[dict[int, np.ndarray], str]:
    r = gguf.GGUFReader(str(path))
    by_layer: dict[int, dict[str, np.ndarray]] = {}
    for t in r.tensors:
        m = re.match(r"blk\.(\d+)\.(\w+?)\.weight\.counts$", t.name)
        if m and m.group(2) in PREF:
            by_layer.setdefault(int(m.group(1)), {})[m.group(2)] = np.asarray(
                t.data, dtype=np.float64
            ).ravel()
    if len(by_layer) != N_LAYER:
        raise ValueError(
            f"{path.name}: routed-expert counts for {len(by_layer)} layers, expected {N_LAYER}. "
            "hint: the imatrix run ended early or the tensor names differ; list tensors with gguf-py"
        )
    chosen = next(p for p in PREF if p in by_layer[0])
    out = {}
    for L, d in by_layer.items():
        c = d[chosen]
        if c.size != N_EXPERT:
            raise ValueError(
                f"{path.name} layer {L}: {c.size} counts, expected {N_EXPERT}. hint: wrong model or a non-MoE tensor"
            )
        out[L] = c
    return out, chosen


def fields(c: np.ndarray) -> dict:
    s = np.sort(c)[::-1]
    tot = s.sum()
    if tot <= 0:
        raise ValueError(
            "a layer has zero routed tokens. hint: the imatrix run processed no chunks"
        )
    k20, k10 = round(0.2 * N_EXPERT), round(0.1 * N_EXPERT)
    top20 = set(np.argsort(c)[::-1][:k20].tolist())
    return {
        "cov20": float(s[:k20].sum() / tot),
        "cov10": float(s[:k10].sum() / tot),
        "dead": int((c == 0).sum()),
        "routes": int(tot),
        "top20": top20,
    }


def summary(vals: list[float]) -> dict:
    return {
        "median": round(st.median(vals), 4),
        "min": round(min(vals), 4),
        "max": round(max(vals), 4),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E161 routing-skew fields from imatrix GGUFs.",
        epilog="example: python3 tools/e161_skew.py code=results/e161/imatrix-code.gguf docs=... prose=...",
    )
    ap.add_argument("corpora", nargs="+", help="name=path/to/imatrix.gguf")
    ap.add_argument("--out", default=str(ROOT / "results/e161/skew.json"))
    args = ap.parse_args()
    per: dict[str, dict[int, dict]] = {}
    report: dict = {"corpora": {}, "pairs": {}}
    for spec in args.corpora:
        name, path = spec.split("=", 1)
        counts, chosen = layer_counts(Path(path))
        per[name] = {L: fields(c) for L, c in counts.items()}
        f = per[name]
        report["corpora"][name] = {
            "tensor": chosen,
            "routes_per_layer": f[0]["routes"],
            "tokens_approx": f[0]["routes"] // 10,
            **{
                k: summary([f[L][k] for L in range(N_LAYER)])
                for k in ("cov20", "cov10", "dead")
            },
            "cov20_by_layer": [round(f[L]["cov20"], 4) for L in range(N_LAYER)],
        }
        print(
            f"{name}: tensor {chosen}, routes/layer {f[0]['routes']:,}, cov20 {report['corpora'][name]['cov20']}, "
            f"cov10 {report['corpora'][name]['cov10']}, dead {report['corpora'][name]['dead']}",
            flush=True,
        )
    for a, b in itertools.combinations(per, 2):
        j = [
            len(per[a][L]["top20"] & per[b][L]["top20"])
            / len(per[a][L]["top20"] | per[b][L]["top20"])
            for L in range(N_LAYER)
        ]
        report["pairs"][f"{a}-{b}"] = {"jaccard_top20": summary(j)}
        print(f"jaccard_top20 {a}-{b}: {report['pairs'][f'{a}-{b}']}", flush=True)
    Path(args.out).write_text(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
