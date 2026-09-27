#!/usr/bin/env python3
# File: tools/score_e149.py
# Purpose: Score E149's arm M4 against its pre-registered predictions, server-side when the harness was capped.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: A harness killed at the cap writes no events.jsonl (it flushes at the end, found 2026-09-26), so a capped run
# is compared SERVER-SIDE on Atlas's per-turn "Done" lines (one per turn, issue order; est_ms = TTFT + 1000*tokens/decode)
# against M3p (E148) and M1p (E146) over the same first N turns. A completed run is scored from events.jsonl, paired against
# M0, M1p, M2 and M3p by (conversation, turn). Acceptance per step comes from the verify lines (e148_dflash_accept's regex).
# Predictions P1-P6 of results/e149-prereg.md print as HELD/FALSIFIED/UNSCORED.
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAW = Path("/home/agent-spark/sparkbench/results/raw")
ANSI = re.compile(r"\x1b\[[0-9;]*m")
VERIFY = re.compile(r"accepted=(\d+)/(\d+) \((\d+)%\) seq_len=(\d+)")
DONE = re.compile(
    r"Done: (\d+) tokens \((\w+)\) ([\d.]+) tok/s, TTFT=([\d.]+)ms, serial=[\d.]+ mtp=[\d.]+ "
    r"p1=([\d.]+) mean_na=[\d.]+ tok_step=([\d.]+)"
)


def clean(p: Path) -> str:
    return ANSI.sub("", p.read_text(errors="replace"))


def server_turns(serverlog: Path) -> list[dict]:
    rows = []
    for m in DONE.finditer(clean(serverlog)):
        tokens, _reason, tps, ttft, p1, tok_step = m.groups()
        rows.append(
            {
                "tokens": int(tokens),
                "decode_tps": float(tps),
                "ttft_ms": float(ttft),
                "p1": float(p1),
                "tok_step": float(tok_step),
                "est_ms": float(ttft) + 1000 * int(tokens) / float(tps),
            }
        )
    if not rows:
        raise SystemExit(
            f"no per-turn Done lines in {serverlog}. hint: not an Atlas server log"
        )
    return rows


def acceptance(serverlog: Path) -> tuple[float, float, int]:
    steps = [tuple(map(int, m.groups())) for m in VERIFY.finditer(clean(serverlog))]
    if not steps:
        raise SystemExit(
            f"no DFlash verify lines in {serverlog}. hint: the arm did not run DFlash"
        )
    mean_all = sum(a for a, *_ in steps) / len(steps)
    long = [a for a, _g, _p, s in steps if 12288 <= s < 28672]
    mean_long = sum(long) / len(long) if long else float("nan")
    return mean_all, mean_long, len(steps)


def events_latencies(arm_dir: Path) -> tuple[dict, list]:
    ev = arm_dir / "harness-report" / "events.jsonl"
    issued: dict[str, tuple[int, str, int]] = {}
    lat: dict[tuple[str, int], float] = {}
    order: list[tuple[str, int]] = []
    for line in ev.read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        uid = e.get("sample_uuid")
        if e.get("event_type") == "sample.issued" and uid:
            issued[uid] = (e["timestamp_ns"], e["conversation_id"], e["turn"])
            order.append((e["conversation_id"], e["turn"]))
        elif e.get("event_type") == "sample.complete" and uid in issued:
            t0, conv, turn = issued[uid]
            lat[(conv, turn)] = (e["timestamp_ns"] - t0) / 1e6
    return lat, order


def per_turn_from_bank(arm_dir: Path) -> dict:
    pt = arm_dir / "per-turn.json"
    if not pt.exists():
        raise SystemExit(
            f"no per-turn.json under {arm_dir}. hint: run the arm's scorer first"
        )
    return {
        (r["conversation_id"], r["turn"]): r["latency_ms"]
        for r in json.loads(pt.read_text())
    }


def paired(a: dict, b: dict, order: list) -> tuple[float, list[float], int]:
    keys = [k for k in order if k in a and k in b]
    if not keys:
        raise SystemExit(
            "no paired turns. hint: check the (conversation_id, turn) keys of both arms"
        )
    ratio = sum(a[k] for k in keys) / sum(b[k] for k in keys)
    n3 = len(keys) // 3
    thirds = [keys[i * n3 : (i + 1) * n3 if i < 2 else len(keys)] for i in range(3)]
    tr = [sum(a[k] for k in t) / sum(b[k] for k in t) for t in thirds if t]
    return ratio, tr, len(keys)


def verdict(ok: bool | None) -> str:
    return "UNSCORED" if ok is None else ("HELD" if ok else "FALSIFIED")


def score_capped(m4: Path, acc_all: float, acc_long: float, nsteps: int) -> None:
    t4 = server_turns(m4 / "server.serverlog")
    n = len(t4)
    print(
        f"=== E149 M4 - CAPPED run, {n} turns; server-side comparison (a capped harness writes no events) ==="
    )

    def line(name: str, t: list[dict]) -> None:
        print(
            f"  {name}: tok_step {sum(x['tok_step'] for x in t) / n:.3f}, p1 {sum(x['p1'] for x in t) / n:.3f}, "
            f"decode {sum(x['decode_tps'] for x in t) / n:.2f} tok/s, est {sum(x['est_ms'] for x in t) / n:.0f} ms/turn"
        )

    line("M4 ", t4)
    ratios = {}
    for name, p in (("M3p", RAW / "e148" / "M3p"), ("M1p", RAW / "e146" / "M1p")):
        t = server_turns(p / "server.serverlog")[:n]
        line(name, t)
        same = sum(1 for a, b in zip(t4, t) if a["tokens"] == b["tokens"])
        ratios[name] = sum(x["est_ms"] for x in t4) / sum(x["est_ms"] for x in t)
        print(
            f"    M4/{name} est ratio {ratios[name]:.3f}; identical output token counts {same}/{n}"
        )
    print(
        f"acceptance: {acc_all:.3f} tokens per step over {nsteps} logged steps; 12,288-28,671 bucket {acc_long:.3f}"
    )
    print()
    print("registered predictions:")
    print(
        f"  P1 M4.accepted_per_step >= 1.0: {acc_all:.3f} -> {verdict(acc_all >= 1.0)}"
    )
    print(
        f"  P2 M4/M3p <= 0.60: {ratios['M3p']:.3f} (server-side, first {n} turns) -> {verdict(ratios['M3p'] <= 0.60)}"
    )
    print("  P3 M4/M2: UNSCORED (capped; M2 is llama.cpp, no server-side turn lines)")
    print("  P4 accuracy: UNSCORED (capped; no scores.json)")
    print("  P5 cap does not fire: fired -> FALSIFIED")
    print(
        f"  P6 accepted per step, 12,288-28,671 bucket >= 0.5: {acc_long:.3f} -> {verdict(acc_long >= 0.5)}"
    )


def score_completed(m4: Path, acc_all: float, acc_long: float, nsteps: int) -> None:
    lat4, order4 = events_latencies(m4)
    print(f"=== E149 M4 - {len(lat4)} turns completed of {len(order4)} issued ===")
    rows = [
        {"conversation_id": k[0], "turn": k[1], "latency_ms": round(v, 1)}
        for k, v in sorted(lat4.items(), key=lambda kv: order4.index(kv[0]))
    ]
    (m4 / "per-turn.json").write_text(json.dumps(rows))
    print(f"M4 mean latency: {sum(lat4.values()) / len(lat4):.0f} ms")
    comps = {
        "M0": RAW / "e146" / "M0",
        "M1p": RAW / "e146" / "M1p",
        "M2": RAW / "e147" / "M2",
        "M3p": RAW / "e148" / "M3p",
    }
    ratios: dict[str, float] = {}
    for name, d in comps.items():
        r, tr, n = paired(lat4, per_turn_from_bank(d), order4)
        ratios[name] = r
        print(
            f"  M4/{name} paired ratio {r:.3f}, thirds {[round(x, 3) for x in tr]} ({n} turns)"
        )
    print(
        f"acceptance: {acc_all:.3f} tokens per step over {nsteps} logged steps; 12,288-28,671 bucket {acc_long:.3f}"
    )
    print()
    print("registered predictions:")
    print(
        f"  P1 M4.accepted_per_step >= 1.0: {acc_all:.3f} -> {verdict(acc_all >= 1.0)}"
    )
    print(
        f"  P2 M4/M3p <= 0.60: {ratios['M3p']:.3f} -> {verdict(ratios['M3p'] <= 0.60)}"
    )
    print(
        f"  P3 M4/M2 0.80-1.50: {ratios['M2']:.3f} -> {verdict(0.80 <= ratios['M2'] <= 1.50)}"
    )
    sc = m4 / "harness-report" / "scores.json"
    if sc.exists():
        a4 = json.loads(sc.read_text())["score"]
        print(
            f"  P4 |accuracy M4 - M3p| <= 0.03: {a4:.3f} vs 0.631 -> {verdict(abs(a4 - 0.631) <= 0.03)}"
        )
    else:
        print("  P4 accuracy: UNSCORED (no scores.json)")
    print("  P5 cap does not fire: did not fire -> HELD")
    print(
        f"  P6 accepted per step, 12,288-28,671 bucket >= 0.5: {acc_long:.3f} -> {verdict(acc_long >= 0.5)}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score E149 (arm M4) against results/e149-prereg.md.",
        epilog="example:\n  tools/score_e149.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--raw", type=Path, default=RAW / "e149")
    args = ap.parse_args()
    m4 = args.raw / "M4"
    acc = acceptance(m4 / "server.serverlog")
    if (m4 / "harness-report" / "events.jsonl").exists():
        score_completed(m4, *acc)
    else:
        score_capped(m4, *acc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
