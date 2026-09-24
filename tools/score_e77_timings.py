#!/usr/bin/env python3
# File: tools/score_e77_timings.py
# Purpose: Extract prefill and decode rates per KV precision from E77's quiet-GPU re-run server logs.
# Project: sparkbench | Date: 2026-08-28
#
# Overview: E77's original wall times are VOID - the relay was resident and Rule 9
# was breached as registered. This reads the RE-RUN's server logs, taken on a
# measured-quiet box, and reports the two rates F16's q8_0 recommendation was
# actually made on.
#
# RATES COME FROM THE SERVER, NOT THE CLIENT. The client wall includes queueing
# and HTTP; llama-server prints what it actually spent.
#
# THE COLD PREFILL IS TASK 0 AND ONLY TASK 0. Every later request in a run
# re-uses the cached pack prefix and prefills only its own question - 32 to 45
# tokens, dominated by fixed overhead. Averaging those in with the 14,768-token
# prefill would report a number that is neither.

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LOGS = Path(
    "/tmp/claude-1001/-home-agent-spark-sparkbench/"
    "de1ef9e3-e792-416c-b46d-36e0dbe7effe/scratchpad/e77t"
)
KVS = ["f16", "q8_0", "q5_1", "q4_0"]
PACKS = ["s", "m"]

# "prompt eval time =  25353.62 ms / 14768 tokens (  1.72 ms per token,  582.48 tokens per second)"
_PROMPT = re.compile(
    r"prompt eval time\s*=\s*([\d.]+) ms /\s*(\d+) tokens .*?([\d.]+) tokens per second"
)
_EVAL = re.compile(
    r"\|\s+eval time\s*=\s*([\d.]+) ms /\s*(\d+) tokens .*?([\d.]+) tokens per second"
)


def parse(path: Path) -> dict[str, object]:
    """Pull the rates out of one server log. A log with no timing lines is an
    error, not an empty result - a silent zero here would read as 'measured and
    found nothing' when it means the run never happened."""
    if not path.exists():
        raise FileNotFoundError(
            f"server log missing: {path}\n"
            f"hint: run the E77 timing re-run; a missing log is not a zero rate"
        )
    text = path.read_text(errors="replace")
    prompts = [
        (float(m.group(1)), int(m.group(2)), float(m.group(3)))
        for m in _PROMPT.finditer(text)
    ]
    evals = [
        (float(m.group(1)), int(m.group(2)), float(m.group(3)))
        for m in _EVAL.finditer(text)
    ]
    if not prompts or not evals:
        raise ValueError(
            f"no timing lines in {path.name} "
            f"(prompt={len(prompts)}, eval={len(evals)})\n"
            f"hint: the server needs -lv 6 for slot print_timing lines"
        )
    # The cold prefill is the single largest-token prompt eval in the log.
    cold = max(prompts, key=lambda p: p[1])
    return {
        "cold_prefill_tokens": cold[1],
        "cold_prefill_tok_s": cold[2],
        "cold_prefill_ms": cold[0],
        "decode_tok_s_median": round(statistics.median(e[2] for e in evals), 2),
        "decode_samples": len(evals),
        "warm_prefill_tok_s_median": round(
            statistics.median(p[2] for p in prompts if p is not cold), 2
        )
        if len(prompts) > 1
        else None,
    }


def main() -> int:
    rows: dict[str, dict[str, dict]] = {}
    for pack in PACKS:
        rows[pack] = {}
        for kv in KVS:
            rows[pack][kv] = parse(LOGS / f"e77t-a-{kv}-{pack}.serverlog")

    print("=== E77 timing half, quiet GPU (relay down, GTT 4.54 GiB at rest) ===\n")
    for pack in PACKS:
        print(f"--- pack {pack} ---")
        print(
            f"    {'KV':6s} {'cold prefill':>18s} {'prefill tok/s':>14s} "
            f"{'decode tok/s':>13s} {'n':>4s}"
        )
        for kv in KVS:
            r = rows[pack][kv]
            print(
                f"    {kv:6s} {r['cold_prefill_tokens']:>12,} tok "
                f"{r['cold_prefill_tok_s']:>14.2f} "
                f"{r['decode_tok_s_median']:>13.2f} {r['decode_samples']:>4d}"
            )
        f16d = rows[pack]["f16"]["decode_tok_s_median"]
        f16p = rows[pack]["f16"]["cold_prefill_tok_s"]
        print("\n    vs f16 (decode / cold prefill):")
        for kv in KVS[1:]:
            d = rows[pack][kv]["decode_tok_s_median"]
            p = rows[pack][kv]["cold_prefill_tok_s"]
            print(
                f"      {kv:6s} decode {100 * (d - f16d) / f16d:+6.2f}%   "
                f"prefill {100 * (p - f16p) / f16p:+6.2f}%"
            )
        print()

    print("--- PREDICTION 2: q8_0 not slower to decode than f16 (>5% = falsified) ---")
    worst = min(
        100
        * (
            rows[p]["q8_0"]["decode_tok_s_median"]
            - rows[p]["f16"]["decode_tok_s_median"]
        )
        / rows[p]["f16"]["decode_tok_s_median"]
        for p in PACKS
    )
    print(f"    worst q8_0 vs f16 decode delta across packs: {worst:+.2f}%")
    print(f"    -> {'HELD' if worst >= -5 else 'FALSIFIED'}")

    print("\n--- PREDICTION 3: decode monotonic q4_0 >= q5_1 >= q8_0 >= f16 ---")
    ok = True
    for pack in PACKS:
        seq = [
            rows[pack][kv]["decode_tok_s_median"]
            for kv in ["q4_0", "q5_1", "q8_0", "f16"]
        ]
        mono = all(
            seq[i] >= seq[i + 1] or abs(seq[i] - seq[i + 1]) / seq[i + 1] <= 0.05
            for i in range(len(seq) - 1)
        )
        ok &= mono
        print(
            f"    pack {pack}: q4_0={seq[0]:.2f} q5_1={seq[1]:.2f} "
            f"q8_0={seq[2]:.2f} f16={seq[3]:.2f}  {'monotonic' if mono else 'INVERTED'}"
        )
    print(f"    -> {'HELD' if ok else 'FALSIFIED'}")

    print("\n--- PREDICTION 4: prefill spread across KV types <= 15% ---")
    for pack in PACKS:
        ps = [rows[pack][kv]["cold_prefill_tok_s"] for kv in KVS]
        spread = 100 * (max(ps) - min(ps)) / min(ps)
        print(
            f"    pack {pack}: {min(ps):.1f}-{max(ps):.1f} tok/s, spread {spread:.2f}%"
            f"  {'ok' if spread <= 15 else 'EXCEEDS'}"
        )

    out = REPO / "results" / "raw" / "e77t-timings.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"\nwritten {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
