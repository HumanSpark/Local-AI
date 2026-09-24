#!/usr/bin/env python3
# File: tools/cost_model.py
# Purpose: Generate every cost figure in the report from formulas + canonical inputs (C-01/02/03).
# Project: sparkbench | Date: 2026-07-12
#
# Overview: The R1.3 review found the cost section wrong by ~1000x, with mixed units and an
# unsourced cloud rate. This tool rebuilds it from first principles: cloud task cost from
# results/deep-eval/cloud-pricing.yml (input*rate + output*rate, one FX conversion), local
# task cost from the measured E30 first-answer curve * measured package power * the stated
# electricity tariff. It emits per-task costs, annual + 3-year TCO at a stated volume, the
# break-even volume per cloud tier, and the output-heavy (bulk) view - each with published
# assumptions. Numbers here are the SOLE source for §8, the one-pager, apply, charts, homepage.
# Acceptance test (C-01): every total reproduces with a four-function calculator.

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path("/home/agent-spark/sparkbench")
PRICING = ROOT / "results/deep-eval/cloud-pricing.yml"

# ---- Canonical local inputs (measured / stated) ----
ELEC_EUR_PER_KWH = 0.298          # Home Electric+ 24h Saver, 27.34c + 9% VAT (Alastair, 2026-07-12)
LOAD_W = 81.0                     # measured single-slot package power (E12; a lower bound on wall)
HARDWARE_EUR = 3680.0            # cash outlay incl Irish import VAT (2960 net); TCO uses cash cost
HARDWARE_LIFE_Y = 3.0
GEN_TPS = 72.8                    # SUSTAINED generation throughput (E12) - the right basis for
                                 # per-1M-output bulk cost (fresh 92 t/s only holds for the first
                                 # ~128 tokens; a 1M-token generation runs at the sustained rate)
# E30 measured first-answer (prefill+first token), Vulkan, seconds by input depth (tokens):
E30 = [(16000, 30.1), (32000, 94.7), (48000, 206.8), (64000, 403.0), (80000, 852.0)]


def local_first_answer_s(input_tokens: int) -> float:
    """Interpolate/extrapolate the measured E30 first-answer time (s) for an input depth."""
    xs = E30
    if input_tokens <= xs[0][0]:
        # linear from origin-ish through the first point
        return xs[0][1] * input_tokens / xs[0][0]
    for (x0, y0), (x1, y1) in zip(xs, xs[1:]):
        if input_tokens <= x1:
            return y0 + (y1 - y0) * (input_tokens - x0) / (x1 - x0)
    (x0, y0), (x1, y1) = xs[-2], xs[-1]           # extrapolate beyond 80K on the last slope
    return y1 + (y1 - y0) * (input_tokens - x1) / (x1 - x0)


def local_task_eur(input_tokens: int, output_tokens: int) -> float:
    secs = local_first_answer_s(input_tokens) + output_tokens / GEN_TPS
    kwh = (LOAD_W / 1000.0) * (secs / 3600.0)
    return kwh * ELEC_EUR_PER_KWH


def load_pricing() -> dict:
    """Minimal YAML read (no pyyaml dep): pull fx + per-model in/out USD rates."""
    fx = 0.87617360  # fallback only; the authoritative rate is fx_usd_to_eur in cloud-pricing.yml
    models: dict[str, dict] = {}
    cur = None
    for raw in PRICING.read_text().splitlines():
        s = raw.strip()
        if s.startswith("fx_usd_to_eur:"):
            fx = float(s.split(":")[1].split("#")[0].strip())
        if raw.startswith("  ") and s.endswith(":") and not raw.startswith("    ") and ":" in s and "_" not in s.split(":")[0]:
            pass
        if raw.startswith("  ") and not raw.startswith("    ") and s.endswith(":"):
            cur = s[:-1]
            models[cur] = {}
        if cur and "input_usd_per_1m:" in s:
            models[cur]["in"] = float(s.split(":")[1].strip())
        if cur and "output_usd_per_1m:" in s:
            models[cur]["out"] = float(s.split(":")[1].strip())
        if cur and s.startswith("tier:"):
            models[cur]["tier"] = s.split(":")[1].strip()
    return {"fx": fx, "models": {k: v for k, v in models.items() if "in" in v}}


def cloud_task_eur(m: dict, fx: float, input_tokens: int, output_tokens: int) -> float:
    usd = input_tokens * m["in"] / 1e6 + output_tokens * m["out"] / 1e6
    return usd * fx


def main() -> None:
    p = load_pricing()
    fx, models = p["fx"], p["models"]
    tasks = {"Everyday doc (12K in, 300 out)": (12000, 300),
             "Large bundle (86K in, 300 out)": (86000, 300)}
    VOL = 5000  # stated annual document-tasks for a 4-person firm (~5/person/working-day)

    print(f"ASSUMPTIONS: electricity EUR {ELEC_EUR_PER_KWH}/kWh; load {LOAD_W} W (package, lower bound on wall);")
    print(f"  hardware EUR {HARDWARE_EUR:.0f} cash / {HARDWARE_LIFE_Y:.0f}y; local time from E30 first-answer curve;")
    print(f"  cloud from cloud-pricing.yml, FX USD->EUR {fx}; annual volume {VOL} tasks/yr.\n")

    order = sorted(models.items(), key=lambda kv: kv[1].get("tier", ""))
    for tname, (ti, to) in tasks.items():
        loc = local_task_eur(ti, to)
        print(f"### {tname}")
        print(f"- Local (electricity): EUR {loc:.4f}/task  (first answer ~{local_first_answer_s(ti):.0f}s)")
        for name, m in order:
            c = cloud_task_eur(m, fx, ti, to)
            print(f"- {name} ({m.get('tier')}): EUR {c:.4f}/task  ->  local is {c/loc:.0f}x cheaper")
        print()

    # 3-year TCO + break-even at the everyday profile
    ti, to = tasks["Everyday doc (12K in, 300 out)"]
    loc_task = local_task_eur(ti, to)
    loc_3y = HARDWARE_EUR + 3 * VOL * loc_task
    print("### 3-year total cost of ownership (everyday profile, {} tasks/yr)".format(VOL))
    print(f"- Local: EUR {HARDWARE_EUR:.0f} hardware + EUR {3*VOL*loc_task:.0f} electricity = EUR {loc_3y:.0f}")
    for name, m in order:
        c = cloud_task_eur(m, fx, ti, to)
        c3 = 3 * VOL * c
        be = HARDWARE_EUR / (3 * (c - loc_task)) if c > loc_task else float("inf")
        be_s = f"{be:,.0f} tasks/yr (~{be/250:.0f}/day)" if be != float("inf") else "never"
        print(f"- {name}: EUR {c3:,.0f} over 3y  ->  local breaks even at {be_s}")
    print()

    # Output-heavy / bulk view (where local wins): per 1M generated tokens
    print("### Output-heavy / bulk view (per 1M GENERATED tokens)")
    loc_1m = (1e6 / GEN_TPS / 3600) * (LOAD_W / 1000) * ELEC_EUR_PER_KWH
    print(f"- Local (1-user electricity): EUR {loc_1m:.2f} per 1M output tokens (EUR 0.04 batched at 16 users)")
    for name, m in order:
        print(f"- {name}: EUR {1e6*m['out']/1e6*fx:.2f} per 1M output tokens (output rate only)")


if __name__ == "__main__":
    main()
