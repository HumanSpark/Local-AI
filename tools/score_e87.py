# File: tools/score_e87.py
# Purpose: Score E87 - decode/prefill throughput, f16 vs f16+fa vs q8_0 KV, on relay build 9865.
# Project: sparkbench | Date: 2026-08-29
#
# Overview: Decode is computed per ITEM as completion_tokens/(wall_s - ttft_s),
# which needs no server-log verbosity. Prefill is prompt_tokens/ttft_s and is
# read ONLY from rep 1 item 1 of each pack, because every later item hits the
# shared pack prefix in cache and its ttft is not a prefill measurement.
# Answer TEXT for the control comes from the RAW records, never a scored row.
from __future__ import annotations

import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_kw_eval import score_file  # noqa: E402

RAW = Path(__file__).resolve().parent.parent / "results" / "raw"
ARMS = ("A", "B", "C")
PACKS = ("s", "m")
REPS = (1, 2, 3)
LABEL = {"A": "f16 (production now)", "B": "f16 + -fa on", "C": "q8_0 + -fa on"}
E77 = {"s": 8.35, "m": 14.82}
F15_NOISE = 1.5


def recs(arm: str, pack: str, rep: int) -> list[dict]:
    return json.loads((RAW / f"e87-{arm}-{pack}-r{rep}.json").read_text())["records"]


def decode_samples(arm: str, pack: str) -> list[float]:
    out = []
    for rep in REPS:
        for r in recs(arm, pack, rep):
            if r["outcome"] != "completed":
                continue
            ct, wall, ttft = r["completion_tokens"], r["wall_s"], r["ttft_s"]
            if not ct or ttft is None or (wall - ttft) <= 0:
                continue
            out.append(ct / (wall - ttft))
    return out


def cold_prefill(arm: str, pack: str) -> float | None:
    r = recs(arm, pack, 1)[0]
    if r["ttft_s"] is None or r["ttft_s"] <= 0:
        return None
    return r["prompt_tokens"] / r["ttft_s"]


def answers(path: Path) -> dict[str, str]:
    out = {}
    for r in json.loads(path.read_text())["records"]:
        if "answer" not in r:
            raise KeyError(f"{path.name}: no 'answer' on {r.get('id')!r}")
        out[r["id"]] = r["answer"] or ""
    return out


def main() -> int:
    print("=" * 78)
    print("PREDICTION 1 (control): the TIMED configs are the ones E85/E86 characterised")
    print("=" * 78)
    p1 = True
    for arm, base in (("A", "e85-p0-s.json"), ("C", "e85-p1-s.json")):
        old = answers(RAW / base)
        for rep in REPS:
            new = answers(RAW / f"e87-{arm}-s-r{rep}.json")
            same = sum(old[k] == new.get(k, "\0") for k in old)
            flag = "" if same == len(old) else "   <-- DIFFERS"
            print(f"  arm {arm} rep{rep} vs {base}: {same}/{len(old)} byte-identical{flag}")
            if same != len(old):
                p1 = False
    print(f"  => PREDICTION 1 {'HELD' if p1 else 'FALSIFIED'}")

    print()
    print("=" * 78)
    print("DECODE tok/s  (per item, completion_tokens / (wall_s - ttft_s); 3 reps pooled)")
    print("=" * 78)
    dec: dict[tuple[str, str], float] = {}
    print(f"  {'arm':<3} {'config':<22} {'pack':<5} {'n':>4} {'median':>9} {'mean':>9} {'p10':>8} {'p90':>8}")
    for arm in ARMS:
        for pack in PACKS:
            s = decode_samples(arm, pack)
            dec[(arm, pack)] = st.median(s)
            q = st.quantiles(s, n=10)
            print(f"  {arm:<3} {LABEL[arm]:<22} {pack:<5} {len(s):>4} "
                  f"{st.median(s):>9.2f} {st.mean(s):>9.2f} {q[0]:>8.2f} {q[-1]:>8.2f}")

    print()
    print("=" * 78)
    print("PREDICTIONS 2 and 4: which change actually buys the decode?")
    print("=" * 78)
    print(f"  {'pack':<5} {'B vs A (flash attn)':<24} {'C vs B (KV quant)':<24} {'C vs A (shipped)':<20}")
    p2 = p4 = True
    ca: dict[str, float] = {}
    for pack in PACKS:
        ba = (dec[("B", pack)] / dec[("A", pack)] - 1) * 100
        cb = (dec[("C", pack)] / dec[("B", pack)] - 1) * 100
        c_a = (dec[("C", pack)] / dec[("A", pack)] - 1) * 100
        ca[pack] = c_a
        print(f"  {pack:<5} {ba:>+22.2f}%  {cb:>+22.2f}%  {c_a:>+18.2f}%")
        if dec[("C", pack)] <= dec[("A", pack)]:
            p2 = False
        if dec[("B", pack)] <= dec[("A", pack)]:
            p4 = False
    print(f"  => PREDICTION 2 (C faster than A) {'HELD' if p2 else 'FALSIFIED'}")
    print(f"  => PREDICTION 4 (flash attn alone buys decode) {'HELD' if p4 else 'FALSIFIED'}")

    print()
    print("=" * 78)
    print("PREDICTION 3: E77's build-770 figures do NOT reproduce here")
    print("=" * 78)
    within = []
    for pack in PACKS:
        d = abs(ca[pack] - E77[pack])
        ok = d <= F15_NOISE
        within.append(ok)
        print(f"  pack {pack}: E77 {E77[pack]:+.2f}%  E87 {ca[pack]:+.2f}%  "
              f"|delta| {d:.2f}pp  {'WITHIN' if ok else 'OUTSIDE'} F15 +/-{F15_NOISE}pp")
    p3 = not all(within)
    print(f"  => PREDICTION 3 {'HELD - they do not reproduce' if p3 else 'FALSIFIED - both reproduced'}")

    print()
    print("=" * 78)
    print("PREDICTION 5: q8_0 COSTS prefill (cold, rep1 item1 only - n=1, declared)")
    print("=" * 78)
    p5 = True
    for pack in PACKS:
        a, c = cold_prefill("A", pack), cold_prefill("C", pack)
        if a is None or c is None:
            print(f"  pack {pack}: unavailable")
            continue
        d = (c / a - 1) * 100
        print(f"  pack {pack}: A {a:8.1f} tok/s   C {c:8.1f} tok/s   {d:+.2f}%")
        if c > a:
            p5 = False
    print(f"  => PREDICTION 5 {'HELD - q8_0 prefill is slower' if p5 else 'FALSIFIED - q8_0 prefill is FASTER'}")

    print()
    print("=" * 78)
    print("PREDICTION 6: nothing runner-owned")
    print("=" * 78)
    bad = 0
    for arm in ARMS:
        for pack in PACKS:
            for rep in REPS:
                rows = score_file(RAW / f"e87-{arm}-{pack}-r{rep}.json")["rows"]
                bad += sum(r["class"] == "transport_failed" for r in rows)
    print(f"  transport failures across all 18 runs: {bad}")
    print(f"  => PREDICTION 6 {'HELD' if bad == 0 else 'FALSIFIED'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
