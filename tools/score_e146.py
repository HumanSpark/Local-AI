#!/usr/bin/env python3
# File: score_e146.py
# Purpose: Score E146 (Atlas vs llama.cpp on Strix Halo) against results/e146-prereg.md and Amendment 1.
# Project: sparkbench | Date: 2026-09-25
#
# Overview: Block M reads each arm's MLCommons harness report (performance/result_summary.json, scores.json,
# events.jsonl): mean latency per turn, tps, TTFT, inline accuracy, and a PAIRED per-turn latency comparison
# joined on (conversation_id, turn) from the issue and completion timestamps. Block 1 reads the speed-client
# JSONs (Q0, Q1, X1). Every registered prediction (P1-P8, P10, PM1-PM6) is printed with its range and a verdict;
# an absent or failed arm is reported as VOID, never as slow. Bands are the registered ones. The "thirds"
# consistency rule (Atlas faster only if the paired ratio is <= 0.85 in at least 2 of 3 contiguous thirds of the
# turns, in issue order) is the operationalisation of the prereg's "trajectory-quartile splits" and is stated in
# the results. Usage: tools/score_e146.py [--raw results/raw/e146]

from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

PUBLISHED_STRIX_MS = 7058.99
PUBLISHED_STRIX_TPS = 10.216
WINDOW_BASELINE_GIB = 8.29


def load_harness(arm_dir: Path) -> dict | None:
    rep = arm_dir / "harness-report"
    summ = rep / "performance" / "result_summary.json"
    if not summ.exists():
        return None
    s = json.loads(summ.read_text())
    scores = (
        json.loads((rep / "scores.json").read_text())
        if (rep / "scores.json").exists()
        else {}
    )
    issued: dict[str, tuple[int, str, int]] = {}
    lat: dict[tuple[str, int], float] = {}
    order: list[tuple[str, int]] = []
    ev = rep / "events.jsonl"
    if ev.exists():
        for line in ev.read_text().splitlines():
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            uid = e.get("sample_uuid")
            if e.get("event_type") == "sample.issued" and uid:
                issued[uid] = (
                    e["timestamp_ns"],
                    e.get("conversation_id"),
                    e.get("turn"),
                )
                order.append((e.get("conversation_id"), e.get("turn")))
            elif e.get("event_type") == "sample.complete" and uid in issued:
                t0, conv, turn = issued[uid]
                lat[(conv, turn)] = (e["timestamp_ns"] - t0) / 1e6
    return {
        "n_issued": s["n_samples_issued"],
        "n_ok": s.get("n_samples_succeeded", s["n_samples_completed"]),
        "n_failed": s["n_samples_failed"],
        "duration_s": s["duration_ns"] / 1e9,
        "mean_ms": s["latency"]["avg"] / 1e6,
        "median_ms": s["latency"]["median"] / 1e6,
        "p95_ms": s["latency"]["percentiles"].get("95.0", float("nan")) / 1e6,
        "ttft_median_ms": s["ttft"]["median"] / 1e6,
        "tps": s.get("tps"),
        "out_tokens": s["output_sequence_lengths"].get("total"),
        "finish": s.get("finish_reason_counts"),
        "accuracy": scores.get("score"),
        "scored_turns": (scores.get("turns") or {}).get("scored"),
        "lat": lat,
        "order": order,
    }


def verdict(ok: bool | None) -> str:
    return "VOID" if ok is None else ("HELD" if ok else "FALSIFIED")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score E146 against its pre-registered predictions and bands.",
        epilog="example:\n  tools/score_e146.py --raw results/raw/e146",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--raw", default="/home/agent-spark/sparkbench/results/raw/e146")
    ap.add_argument(
        "--e147",
        default="/home/agent-spark/sparkbench/results/raw/e147",
        help="E147 raw dir; its M2 arm is scored against M0, M1p and M1s when present",
    )
    ap.add_argument(
        "--e148",
        default="/home/agent-spark/sparkbench/results/raw/e148",
        help="E148 raw dir; its M3p and M3s arms (Atlas DFlash) are scored against M0, M1p and M2 when present",
    )
    args = ap.parse_args()
    raw = Path(args.raw)

    print("=== BLOCK M - MLCommons harness, 4 of 20 trajectories ===")
    arms = ("M0", "M1", "M1p", "M1s")
    m = {a: load_harness(raw / a) for a in arms}
    m2 = load_harness(Path(args.e147) / "M2")
    for a, h in m.items():
        if h is None:
            continue
        acc = {}
        sc = raw / a / "harness-report" / "scores.json"
        if sc.exists():
            for t in json.loads(sc.read_text()).get("per_turn", []):
                acc[(t["conversation_id"], t["turn"])] = t.get("score")
        rows = [
            {
                "conversation_id": k[0],
                "turn": k[1],
                "latency_ms": round(v, 1),
                "accuracy": acc.get(k),
            }
            for k, v in sorted(h["lat"].items(), key=lambda kv: h["order"].index(kv[0]))
        ]
        (raw / a / "per-turn.json").write_text(json.dumps(rows))
    labels = {
        "M0": "llama.cpp MLPerf reference",
        "M1": "Atlas-Inf HEAD 2d1aab8 (registered)",
        "M1p": "PATCHED Atlas-Inf HEAD (one-line W4A16_NVFP4 change; not the vendor's code)",
        "M1s": "MLPerf entry's shipped source, native-HIP reconstruction",
    }
    if m2:
        m["M2"] = m2
        labels["M2"] = (
            "E147: llama.cpp reference flags + Qwen3.6-27B DFlash drafter n=4"
        )
        arms = arms + ("M2",)
    for a in arms:
        h = m[a]
        if h is None:
            print(f"{a} [{labels[a]}]: VOID (no harness report)")
            continue
        print(
            f"{a} [{labels[a]}]: {h['n_ok']}/{h['n_issued']} turns ok ({h['n_failed']} failed), duration {h['duration_s']:.0f}s, "
            f"mean latency {h['mean_ms']:.0f} ms, median {h['median_ms']:.0f}, p95 {h['p95_ms']:.0f}, TTFT median "
            f"{h['ttft_median_ms']:.0f} ms, tps {h['tps']:.2f}, out tokens {h['out_tokens']}, accuracy {h['accuracy']}, "
            f"finish {h['finish']}"
        )
    m0 = m["M0"]
    if m0:
        print()
        print(
            "registered predictions, block M (PM3 is M0's; PM1, PM2, PM4-PM6 apply to each Atlas arm that served):"
        )
        print(
            f"  PM3 M0.mean_turn_latency_ms 8,000-16,000: {m0['mean_ms']:.0f} -> {verdict(8000 <= m0['mean_ms'] <= 16000)}"
        )
    for a in [x for x in ("M1", "M1p", "M1s", "M2") if x in m]:
        h = m[a]
        print()
        print(f"--- {a}: {labels[a]}")
        if h is None:
            print(
                f"  PM1 {a}.serves: {'FALSIFIED' if a == 'M1' else 'VOID'} (no harness report); PM2, PM4, PM5, PM6: VOID"
            )
            continue
        print(f"  PM1 serves: HELD ({h['n_ok']} turns ok)")
        print(
            f"  PM2 mean_turn_latency_ms 5,500-9,500: {h['mean_ms']:.0f} -> {verdict(5500 <= h['mean_ms'] <= 9500)}"
        )
        print(f"  PM6 tps 7-14: {h['tps']:.2f} -> {verdict(7 <= h['tps'] <= 14)}")
        lo, hi = PUBLISHED_STRIX_MS * 0.75, PUBLISHED_STRIX_MS * 1.25
        inside = lo <= h["mean_ms"] <= hi
        print(
            f"  band, published Strix Halo latency ({PUBLISHED_STRIX_MS} ms, {lo:.0f}-{hi:.0f}): {h['mean_ms']:.0f} ms -> "
            f"{'REPRODUCED' if inside else 'NOT reproduced'} ({h['mean_ms'] / PUBLISHED_STRIX_MS:.2f}x published) - for THIS code only"
        )
        if not m0:
            continue
        keys = sorted(
            set(m0["lat"]) & set(h["lat"]),
            key=lambda k: m0["order"].index(k) if k in m0["order"] else 0,
        )
        print(
            f"  paired turns: {len(keys)} (same turn set as M0: {set(m0['lat']) == set(h['lat'])})"
        )
        if not keys:
            continue
        r = [h["lat"][k] / m0["lat"][k] for k in keys]
        ratio = sum(h["lat"][k] for k in keys) / sum(m0["lat"][k] for k in keys)
        n3 = len(keys) // 3
        thirds = [keys[i * n3 : (i + 1) * n3 if i < 2 else len(keys)] for i in range(3)]
        tr = [
            sum(h["lat"][k] for k in t) / sum(m0["lat"][k] for k in t) for t in thirds
        ]
        print(
            f"  paired ratio {a}/M0: sum-of-latency {ratio:.3f}; mean of per-turn ratios {st.mean(r):.3f}; median "
            f"{st.median(r):.3f}; thirds {[round(x, 3) for x in tr]}"
        )
        print(
            f"  PM4 paired ratio 0.45-0.90: {ratio:.3f} -> {verdict(0.45 <= ratio <= 0.90)}"
        )
        if m0["accuracy"] is not None and h["accuracy"] is not None:
            d = abs(h["accuracy"] - m0["accuracy"])
            print(
                f"  PM5 |accuracy - M0| <= 0.05: {h['accuracy']:.3f} vs {m0['accuracy']:.3f} (diff {d:.3f}) -> {verdict(d <= 0.05)}"
            )
        faster_thirds = sum(1 for x in tr if x <= 0.85)
        if ratio <= 0.85 and faster_thirds >= 2:
            band = "ATLAS-CODE FASTER than the reference"
        elif ratio <= 0.85:
            band = "ratio <= 0.85 but not consistent across thirds: NOT SEPARATED (inconsistent)"
        elif ratio <= 1.15:
            band = "NOT SEPARATED"
        else:
            band = "REFERENCE FASTER"
        print(
            f"  band vs reference: ratio {ratio:.3f}, {faster_thirds} of 3 thirds <= 0.85 -> {band}"
        )

    if m2 and m0:
        print()
        print("=== E147 - Atlas against the best open configuration (M2) ===")
        for a in ("M1p", "M1s"):
            h = m.get(a)
            if not h:
                continue
            keys = sorted(
                set(h["lat"]) & set(m2["lat"]),
                key=lambda k: m0["order"].index(k) if k in m0["order"] else 0,
            )
            if not keys:
                print(f"  {a}/M2: no paired turns")
                continue
            ratio = sum(h["lat"][k] for k in keys) / sum(m2["lat"][k] for k in keys)
            n3 = len(keys) // 3
            thirds = [
                keys[i * n3 : (i + 1) * n3 if i < 2 else len(keys)] for i in range(3)
            ]
            tr = [
                sum(h["lat"][k] for k in t) / sum(m2["lat"][k] for k in t)
                for t in thirds
            ]
            fast = sum(1 for x in tr if x <= 0.85)
            band = (
                "ATLAS FASTER than the open configuration"
                if ratio <= 0.85 and fast >= 2
                else "NOT SEPARATED"
                if ratio <= 1.15
                else "OPEN CONFIGURATION FASTER"
            )
            print(
                f"  {a}/M2 paired ratio {ratio:.3f}, thirds {[round(x, 3) for x in tr]} ({len(keys)} turns) -> {band}"
            )
            if a == "M1p":
                print(
                    f"  E147 P5 M1p/M2 0.85-1.20: {ratio:.3f} -> {verdict(0.85 <= ratio <= 1.20)}"
                )
        r2 = sum(m2["lat"][k] for k in m2["lat"] if k in m0["lat"]) / sum(
            m0["lat"][k] for k in m2["lat"] if k in m0["lat"]
        )
        print(
            f"  E147 P1 M2.turns_ok 206: {m2['n_ok']} -> {verdict(m2['n_ok'] == 206)}"
        )
        print(
            f"  E147 P2 M2.mean_turn_latency_ms 7,500-10,500: {m2['mean_ms']:.0f} -> {verdict(7500 <= m2['mean_ms'] <= 10500)}"
        )
        print(
            f"  E147 P3 M2/M0 paired ratio 0.55-0.85: {r2:.3f} -> {verdict(0.55 <= r2 <= 0.85)}"
        )
        if m2["accuracy"] is not None and m0["accuracy"] is not None:
            d = abs(m2["accuracy"] - m0["accuracy"])
            print(
                f"  E147 P4 |accuracy M2 - M0| <= 0.03: {m2['accuracy']:.3f} vs {m0['accuracy']:.3f} (diff {d:.3f}) -> {verdict(d <= 0.03)}"
            )
    m3 = {a: load_harness(Path(args.e148) / a) for a in ("M3p", "M3s")}
    for a, h in m3.items():
        # events.jsonl is not banked (12 MB, hook), so the per-turn record is written beside the report as for E146's arms
        if h is None:
            continue
        acc = {}
        sc = Path(args.e148) / a / "harness-report" / "scores.json"
        if sc.exists():
            for t in json.loads(sc.read_text()).get("per_turn", []):
                acc[(t["conversation_id"], t["turn"])] = t.get("score")
        rows = [
            {
                "conversation_id": k[0],
                "turn": k[1],
                "latency_ms": round(v, 1),
                "accuracy": acc.get(k),
            }
            for k, v in sorted(h["lat"].items(), key=lambda kv: h["order"].index(kv[0]))
        ]
        (Path(args.e148) / a / "per-turn.json").write_text(json.dumps(rows))
    if m0 and any(m3.values()):
        print()
        print(
            "=== E148 - Atlas DFlash (z-lab Qwen3.6-27B drafter) on the MLPerf model ==="
        )
        lab3 = {
            "M3p": "PATCHED Atlas-Inf HEAD, --dflash --draft-model",
            "M3s": "MLPerf entry's shipped source, --dflash --draft-model",
        }

        def paired(a_lat: dict, b_lat: dict) -> tuple[float, list[float], int] | None:
            keys = sorted(
                set(a_lat) & set(b_lat),
                key=lambda k: m0["order"].index(k) if k in m0["order"] else 0,
            )
            if not keys:
                return None
            ratio = sum(a_lat[k] for k in keys) / sum(b_lat[k] for k in keys)
            n3 = len(keys) // 3
            thirds = [
                keys[i * n3 : (i + 1) * n3 if i < 2 else len(keys)] for i in range(3)
            ]
            tr = [sum(a_lat[k] for k in t) / sum(b_lat[k] for k in t) for t in thirds]
            return ratio, tr, len(keys)

        for a in ("M3p", "M3s"):
            h = m3[a]
            print()
            print(f"--- {a}: {lab3[a]}")
            if h is None:
                print(
                    "  VOID (no harness report); its predictions are VOID, its band stays open"
                )
                continue
            print(
                f"  {h['n_ok']}/{h['n_issued']} turns ok ({h['n_failed']} failed), duration {h['duration_s']:.0f}s, "
                f"mean latency {h['mean_ms']:.0f} ms, median {h['median_ms']:.0f}, p95 {h['p95_ms']:.0f}, TTFT median "
                f"{h['ttft_median_ms']:.0f} ms, tps {h['tps']:.2f}, out tokens {h['out_tokens']}, accuracy {h['accuracy']}, "
                f"finish {h['finish']}"
            )
            print(f"  P1 {a}.turns_ok 206: {h['n_ok']} -> {verdict(h['n_ok'] == 206)}")
            if a == "M3p":
                print(
                    f"  P2 M3p.mean_turn_latency_ms 5,500-9,000: {h['mean_ms']:.0f} -> {verdict(5500 <= h['mean_ms'] <= 9000)}"
                )
            else:
                print(
                    f"  M3s.mean_turn_latency_ms (reported beside P2): {h['mean_ms']:.0f}"
                )
            r0 = paired(h["lat"], m0["lat"])
            if r0:
                tag = (
                    "P3 M3p/M0 paired ratio 0.45-0.72"
                    if a == "M3p"
                    else "M3s/M0 paired ratio"
                )
                v = f" -> {verdict(0.45 <= r0[0] <= 0.72)}" if a == "M3p" else ""
                print(
                    f"  {tag}: {r0[0]:.3f}, thirds {[round(x, 3) for x in r0[1]]} ({r0[2]} turns){v}"
                )
            if m2:
                r2 = paired(h["lat"], m2["lat"])
                if r2:
                    ratio, tr, n = r2
                    fast = sum(1 for x in tr if x <= 0.85)
                    band = (
                        "ATLAS FASTER than the open configuration"
                        if ratio <= 0.85 and fast >= 2
                        else "NOT SEPARATED"
                        if ratio <= 1.15
                        else "OPEN CONFIGURATION FASTER"
                    )
                    print(
                        f"  P4 {a}/M2 paired ratio 0.80-1.20: {ratio:.3f}, thirds {[round(x, 3) for x in tr]} ({n} turns) "
                        f"-> {verdict(0.80 <= ratio <= 1.20)}; band -> {band}"
                    )
            m1p = m.get("M1p")
            if m1p:
                r1 = paired(h["lat"], m1p["lat"])
                if r1:
                    tag = (
                        "P6 M3p/M1p paired ratio 0.65-0.95"
                        if a == "M3p"
                        else "M3s/M1s paired ratio"
                        if m.get("M1s")
                        else "M3s/M1p paired ratio"
                    )
                    base = m["M1s"] if (a == "M3s" and m.get("M1s")) else m1p
                    r1 = paired(h["lat"], base["lat"])
                    v = f" -> {verdict(0.65 <= r1[0] <= 0.95)}" if a == "M3p" else ""
                    print(
                        f"  {tag}: {r1[0]:.3f}, thirds {[round(x, 3) for x in r1[1]]} ({r1[2]} turns){v}"
                    )
                if (
                    a == "M3p"
                    and h["accuracy"] is not None
                    and m1p["accuracy"] is not None
                ):
                    d = abs(h["accuracy"] - m1p["accuracy"])
                    print(
                        f"  P5 |accuracy M3p - M1p| <= 0.03: {h['accuracy']:.3f} vs {m1p['accuracy']:.3f} (diff {d:.3f}) -> {verdict(d <= 0.03)}"
                    )
    print()
    print("=== BLOCK 1 - speed client (Qwen3.8-27B) ===")
    sp: dict[str, dict | None] = {}
    for a in ("Q0", "Q1", "X1"):
        f = raw / a / f"speed-{a}.json"
        sp[a] = json.loads(f.read_text()) if f.exists() else None
        if sp[a] is None:
            print(f"{a}: VOID (no speed JSON)")
            continue
        md = sp[a]["medians"]
        mem = sp[a]["memory"]
        print(
            f"{a}: CODE {md['CODE']['decode_tps']} CHAT {md['CHAT']['decode_tps']} D1500 {md['D1500']['decode_tps']} tok/s | "
            f"P8K prefill {md['P8K']['prefill_tps']} P32K prefill {md['P32K']['prefill_tps']} (ttft {md['P32K']['ttft_s']} s) "
            f"decode@32K {md['P32K']['decode_tps']} | determinism {sp[a]['determinism']['distinct']} distinct of "
            f"{sp[a]['determinism']['n']} | peak GPU {mem['peak_gpu_gib']} GiB (baseline {mem['baseline_gpu_gib']})"
        )
    q1, x1, q0 = sp["Q1"], sp["X1"], sp["Q0"]
    print()
    print("registered predictions, block 1:")
    if x1:
        md = x1["medians"]
        print("  P1 X1.serves YES: HELD")
        print(
            f"  P2 X1.CODE decode 22-32: {md['CODE']['decode_tps']} -> {verdict(22 <= md['CODE']['decode_tps'] <= 32)}"
        )
        print(
            f"  P3 X1.CHAT decode 13-20: {md['CHAT']['decode_tps']} -> {verdict(13 <= md['CHAT']['decode_tps'] <= 20)}"
        )
        print(
            f"  P7 X1 decode at ~32K 9-16: {md['P32K']['decode_tps']} -> {verdict(md['P32K']['decode_tps'] is not None and 9 <= md['P32K']['decode_tps'] <= 16)}"
        )
        print(
            f"  P8 X1 determinism 10 of 10 byte-equal: {x1['determinism']['byte_equal']} -> {verdict(x1['determinism']['byte_equal'])} (the fresh-process half was not run)"
        )
        # The client sampler starts AFTER the server has loaded, so its baseline already holds the model; the
        # window-open baseline (Chatterbox TTS resident, 8.29 GiB in E139) is the honest zero.
        net = x1["memory"]["peak_gpu_gib"] - WINDOW_BASELINE_GIB
        print(
            f"  P10 X1 peak GPU above the window-open baseline 20-32 GiB: {net:.1f} (peak {x1['memory']['peak_gpu_gib']}) -> {verdict(20 <= net <= 32)}"
        )
    else:
        print("  P1 X1.serves: FALSIFIED / VOID. P2, P3, P7, P8, P10: VOID")
    if x1 and q1:
        a, b = x1["medians"], q1["medians"]
        rc = a["CODE"]["decode_tps"] / b["CODE"]["decode_tps"]
        rh = a["CHAT"]["decode_tps"] / b["CHAT"]["decode_tps"]
        rp = a["P32K"]["prefill_tps"] / b["P32K"]["prefill_tps"]
        print(f"  P4 X1/Q1 CODE 0.85-1.25: {rc:.3f} -> {verdict(0.85 <= rc <= 1.25)}")
        print(f"  P5 X1/Q1 CHAT 0.75-1.25: {rh:.3f} -> {verdict(0.75 <= rh <= 1.25)}")
        print(
            f"  P6 X1/Q1 P32K prefill 0.5-2.0: {rp:.3f} -> {verdict(0.5 <= rp <= 2.0)}"
        )
        both = rc >= 1.15 and rh >= 1.15
        neither = rc <= 0.87 and rh <= 0.87
        print(
            f"  band X1 vs Q1: CODE {rc:.2f}, CHAT {rh:.2f} -> "
            + (
                "ATLAS FASTER on both"
                if both
                else "LLAMA.CPP FASTER on both"
                if neither
                else "not separated or workload-dependent"
            )
        )
    if x1:
        c = x1["medians"]["CODE"]["decode_tps"]
        band = (
            "CONFIRMED"
            if c >= 26.0
            else "REPRODUCED-CONDITIONALLY"
            if c >= 20
            else "NOT REPRODUCED"
        )
        print(f"  README claim 28.3-28.6 tok/s (Qwen3.8 K=4): X1 CODE {c} -> {band}")
    if q0 and q1:
        print(
            f"  reference check: Q0 CODE {q0['medians']['CODE']['decode_tps']} (E138 12.33), Q1 CODE {q1['medians']['CODE']['decode_tps']} (E138 25.67)"
        )
    print("  P9 withdrawn (Amendment 1). P11 (block 2, Aider) not run in this window.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
