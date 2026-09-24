#!/usr/bin/env python3
# File: e116_short_turn_effort_cost.py
# Purpose: E116 - what does reasoning effort COST on short, chat-shaped turns?
# Project: sparkbench | Date: 2026-09-06
#
# Overview: The serving proposal's measured benefit is on LONG agentic work,
# where E101 saw `xhigh` run to the token cap in 11 of 18 generations for three
# times the tokens. Its own open item 2 says that if the relay mostly serves
# short chat turns, the change is "harmless but not worth much".
#
# E115b makes that sentence look wrong in a way that matters. On a short
# reasoning prompt the ladder ran xhigh 337 < low 542 < medium 633 reasoning
# characters - so switching the default to `medium` would INCREASE the cost of a
# short turn rather than leave it unchanged. Harmless and 1.9x are different
# recommendations.
#
# Two prompts cannot carry that claim, so this runs a spread of genuinely
# short, genuinely varied turns at both efforts and reports the ratio per
# prompt. Greedy, one server per effort, -np 1.
#
# It measures COST, not quality. Nine short turns cannot rank two efforts on
# correctness and this does not try - the quality question is E42's and E101's
# and is already answered for long work.

from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "probe", REPO / "tools" / "e115_effort_override_probe.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

# The shape a relay actually serves: a question, an instruction, a small
# transform. Deliberately spread across trivial / factual / light-reasoning /
# generative, because "short" is not one thing.
TURNS = [
    ("greeting",     "Say hello and tell me what you can help with, in two sentences."),
    ("factual",      "What is the capital of Australia?"),
    ("definition",   "In two sentences, what is idempotence in an HTTP API?"),
    ("rewrite",      "Rewrite this line to be less formal, one line only: "
                     "'Please be advised that the meeting has been rescheduled.'"),
    ("extract",      "From this sentence return only the date, nothing else: "
                     "'The invoice dated 14 March 2026 remains unpaid.'"),
    ("arith",        "A jacket costs 85 euro and is discounted 30 percent. "
                     "What is the final price?"),
    ("light_reason", "If all Bloops are Razzies and all Razzies are Lazzies, "
                     "are all Bloops Lazzies? Answer yes or no and give one line of reasoning."),
    ("code_snippet", "Write a Python one-liner that reverses a string. "
                     "Return only the line."),
    ("summarise",    "Summarise in one sentence: 'The committee met on Tuesday, "
                     "reviewed three tenders, rejected the lowest on technical "
                     "grounds, and deferred the decision to the next session.'"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=8120)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--efforts", default="xhigh,medium,low")
    a = ap.parse_args()
    out = Path(a.out)
    if out.is_dir():
        raise SystemExit(f"--out {a.out!r} is a directory; it names the results FILE")
    out.parent.mkdir(parents=True, exist_ok=True)

    efforts = [e.strip() for e in a.efforts.split(",") if e.strip()]
    rows: list[dict] = []
    # One server, effort varied PER REQUEST. E115 established the per-request
    # path is honoured and overrides the flag, so this needs one load rather
    # than three - and it removes cross-process variation from the comparison.
    log = out.parent / "e116-server.serverlog"
    proc = probe.serve(Path(str(probe.DEFAULT_BIN)), a.port, log, [])
    try:
        probe.wait_healthy(a.port, 300)
        layers = probe.assert_full_offload(log)
        print(f"full-offload gate OK, {layers} layers", flush=True)
        for name, prompt in TURNS:
            for eff in efforts:
                r = probe.ask(a.port, prompt, eff, a.max_tokens, 900.0)
                r.update({"turn": name, "effort": eff})
                rows.append(r)
                print(f"  {name:13s} {eff:7s} reasoning_chars={r['reasoning_chars']:>6} "
                      f"completion_tokens={r['completion_tokens']:>5} "
                      f"{r['finish_reason']:>6} {r['wall_s']:>7}s", flush=True)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=60)
        except Exception:  # noqa: BLE001 - best-effort teardown
            proc.kill()

    summary = {}
    for eff in efforts:
        toks = [r["completion_tokens"] for r in rows if r["effort"] == eff]
        summary[eff] = {"total_completion_tokens": sum(toks),
                        "median_completion_tokens": statistics.median(toks),
                        "total_wall_s": round(sum(r["wall_s"] for r in rows
                                                  if r["effort"] == eff), 1),
                        "hit_cap": sum(1 for r in rows if r["effort"] == eff
                                       and r["finish_reason"] == "length")}
    ratios = {}
    if "xhigh" in summary:
        for eff in efforts:
            if eff != "xhigh":
                ratios[f"{eff}_over_xhigh_tokens"] = round(
                    summary[eff]["total_completion_tokens"]
                    / summary["xhigh"]["total_completion_tokens"], 3)
    out.write_text(json.dumps({
        "model": probe.MODEL, "max_tokens": a.max_tokens, "n_turns": len(TURNS),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": summary, "ratios_vs_xhigh": ratios, "results": rows}, indent=2))
    print("\nsummary:", json.dumps(summary, indent=2), flush=True)
    print("ratios vs xhigh:", json.dumps(ratios, indent=2), flush=True)
    print(f"written: {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
