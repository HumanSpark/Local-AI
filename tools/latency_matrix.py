#!/usr/bin/env python3
# File: latency_matrix.py
# Purpose: Single-user time-to-answer for each candidate resident model, at the three prompt sizes the relay's own traffic shows.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: The routing guide scores ACCURACY per task. The relay's question is
# different - which model should be LOADED - and it turns on how long a person
# waits, which no instrument in this repo measures. serve_bench.py is the
# nearest thing and is the wrong one: it is a CONCURRENCY harness, driving one
# thread per slot with synthetic prompts for a fixed window at tg128 semantics.
# That answers "how much can the box push", not "how long until I have my
# answer", and the second is the residency question.
#
# THE TIERS COME FROM THE RELAY'S OWN LOG, not from taste. tools/
# relay_traffic_mix.py over 952 real requests (2026-07-19 to 2026-08-14) found
# 91.3% under 1,000 prompt tokens at a median of 68, and 5.3% at or above
# 4,000 carrying 67.9% of all generation time. The `chat` and `folder` tiers
# below are those two populations; `document` is the 3.9% between them. A
# latency table weighted differently from the traffic would be a table about a
# workload nobody runs.
#
# THE METRIC IS TIME TO A COMPLETE ANSWER, not time for N tokens. Capping
# generation would flatter a model that thinks before answering by cutting it
# off mid-thought, and the 27B's whole cost is that it thinks. So generation
# runs to completion under a safety ceiling, and `completion_tokens` and
# tokens/sec are recorded beside the wall time - a reader can then separate
# "slow because it generates a lot" from "slow per token", which are different
# problems with different fixes.
#
# COLD AND WARM ARE REPORTED SEPARATELY, because conflating them is how the
# 45:1 prefill effect (F74) gets misread. The first request against a prompt
# prefix pays the whole prefill; the next comes off the cache. A new
# conversation is cold, the fifth question in a session is warm, and the
# residency decision needs both rather than an average of two populations that
# are not the same population.
#
# ONE SERVING CONFIG ACROSS ALL ARMS, declared rather than tuned per model
# (Rule 8). Every arm runs `-b 512 -ub 128` because the 27B needs it on large
# packs (F72) - without it the big packs did not score badly, they took the GPU
# down. E49 measured `-b` as INERT for throughput (a 4x change moves it 0.6%)
# and `-ub 128` as the 27B's OPTIMUM, so if this setting biases anything it
# biases TOWARD the 27B. The workhorse's latency advantage is therefore
# understated here rather than flattered, which is the safe direction for a
# measurement that argues against switching.

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))
sys.path.insert(0, str(ROOT / "tools"))
from bench_context import assert_context_fits  # noqa: E402
from corpus_l3 import build_pack_l3  # noqa: E402
from corpus_l4 import build_pack_l4  # noqa: E402

DEFAULT_SERVER = "/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server"
ASSIGN_RE = re.compile(r"layer\s+\d+\s+assigned to device\s+([A-Za-z0-9_]+)")

RULES = """\
You are assisting on a professional advisory engagement. Answer using ONLY the \
engagement pack below.

Reply in EXACTLY this two-line format and nothing else:

ANSWER: <your answer>
CITATION: <document id and clause, or NONE>

=== ENGAGEMENT PACK ===
{pack}

=== QUESTION ===
"""

QUESTION = ("Under engagement letter ENG-2025 between Ardmore Composites and "
            "Calderwood Advisory, what monthly fee applies for November 2026? "
            "Give the amount in EUR, exclusive of VAT.")


def build_tiers() -> list[dict]:
    """Three prompt sizes from REAL corpora, named for the traffic they stand for.

    Not synthetic padding: a latency figure measured on repeated filler tokens
    is a figure about the tokenizer, not about the work.
    """
    return [
        # REPS ARE NOT EVEN, and the imbalance is the point. The decision this
        # tool exists for is whether the 27B can serve a TINY query acceptably
        # - 91.3% of real traffic - so that cell gets the reps and the two
        # expensive tiers get enough to be indicative. Spreading reps evenly
        # would spend most of the wall clock refining the cells that cannot
        # change the answer.
        {"tier": "chat", "reps": 7,
         "why": "91.3% of real relay traffic - median 68 prompt tokens, 56 generated",
         # Sized to the observed median rather than to a one-liner: 68 prompt
         # tokens with an answer-length instruction, so generation lands near
         # the 56 the relay actually sees. A 16-token toy prompt would measure
         # a request nobody makes.
         "prompt": ("I'm drafting a note for a client and want to get the "
                    "terminology right. In two or three sentences, and in plain "
                    "English a non-lawyer would follow, what is professional "
                    "indemnity insurance and what does it actually cover?")},
        {"tier": "document", "reps": 3,
         "why": "the 3.9% between - one engagement pack in front of you",
         "prompt": RULES.format(pack=build_pack_l4()) + QUESTION},
        {"tier": "folder", "reps": 2,
         "why": "the 1.4% that carries 34% of all generation time",
         "prompt": RULES.format(pack=build_pack_l3(distractor_count=9)) + QUESTION},
    ]


def wait_healthy(port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as r:
                if r.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001 - top-level poll boundary, retried below
            last = exc
        time.sleep(2)
    raise RuntimeError(
        f"server not healthy on port {port} within {timeout}s (last: {last}). "
        f"hint: read the server log for a load failure before assuming a port clash"
    )


def assert_full_offload(log_path: Path) -> dict:
    """Rule 3: zero offload evidence is a FAIL, never a pass."""
    devices = ASSIGN_RE.findall(log_path.read_text(errors="replace"))
    if not devices:
        raise RuntimeError(
            f"full-offload gate FAILED: no 'assigned to device' lines in {log_path}. "
            f"hint: the server must run with -v or the gate cannot be evidenced"
        )
    on_cpu = [d for d in devices if d == "CPU"]
    if on_cpu:
        raise RuntimeError(
            f"full-offload gate FAILED: {len(on_cpu)}/{len(devices)} layers on CPU. "
            f"hint: raise -ngl or these are not GPU latency figures"
        )
    return {"layers_assigned": len(devices), "devices": sorted(set(devices))}


def ask(port: int, prompt: str, max_tokens: int, timeout: float,
        thinking: str) -> dict:
    payload: dict = {"messages": [{"role": "user", "content": prompt}],
                     "temperature": 0, "max_tokens": max_tokens}
    if thinking == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    elif thinking in ("low", "medium", "xhigh"):
        payload["reasoning_effort"] = thinking
    elif thinking != "default":
        raise ValueError(
            f"unknown thinking mode {thinking!r}. "
            f"hint: one of default, off, low, medium, xhigh"
        )
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    wall = time.time() - t0
    choice = d["choices"][0]
    usage = d.get("usage", {})
    gen = usage.get("completion_tokens")
    # llama-server returns a non-standard `timings` block alongside the
    # OpenAI-shaped response. It carries the prompt/eval split, which is the
    # only way to tell "MTP made decoding faster" from "MTP made the answer
    # shorter" - E59's F1 emitted 41% fewer tokens for the same answer, so wall
    # time alone cannot separate the two.
    tim = d.get("timings", {})
    return {
        "wall_s": round(wall, 2),
        "prompt_ms": tim.get("prompt_ms"),
        "predicted_ms": tim.get("predicted_ms"),
        "predicted_per_second": tim.get("predicted_per_second"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": gen,
        "reasoning_chars": len(choice["message"].get("reasoning_content") or ""),
        "finish_reason": choice.get("finish_reason"),
        "tok_per_s": round(gen / wall, 2) if gen and wall > 0 else None,
        "answer": (choice["message"].get("content") or "")[:200],
    }


def run_arm(arm: dict, tiers: list[dict], args) -> dict:
    log_path = Path(args.out).with_suffix(f".{arm['label']}.serverlog")
    cmd = [args.server_bin, "-m", arm["model"], "-c", str(args.ctx), "-np", "1",
           "--host", "127.0.0.1", "--port", str(args.port), "--no-webui", "-v"]
    cmd += shlex.split(arm.get("server_extra_override", args.server_extra))
    print(f"\n=== {arm['label']} ===\n{' '.join(cmd)}")
    log_f = log_path.open("w")
    proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
    load_t0 = time.time()
    rows: list[dict] = []
    try:
        wait_healthy(args.port, args.load_timeout)
        load_s = round(time.time() - load_t0, 1)
        gate = assert_full_offload(log_path)
        print(f"  loaded in {load_s}s, full-offload gate: {gate}")
        base = f"http://127.0.0.1:{args.port}"
        fit = assert_context_fits(base, [t["prompt"] for t in tiers],
                                  args.max_tokens, args.ctx, args.request_timeout)
        print(f"  context preflight: {fit}")

        for tier in tiers:
            for rep in range(1, (args.reps or tier["reps"]) + 1):
                r = ask(args.port, tier["prompt"], args.max_tokens,
                        args.request_timeout, arm["thinking"])
                # rep 1 pays the whole prefill; 2+ come off the prompt cache.
                r.update(tier=tier["tier"], rep=rep,
                         cache="cold" if rep == 1 else "warm")
                rows.append(r)
                print(f"  {tier['tier']:9} rep{rep} {r['cache']:5} "
                      f"{r['wall_s']:8.2f}s  prompt={r['prompt_tokens']:>6,} "
                      f"gen={r['completion_tokens']:>5,} "
                      f"{str(r['tok_per_s']):>7} tok/s  {r['finish_reason']}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=30)
        log_f.close()
    return {**arm, "load_s": load_s, "gate": gate, "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Single-user time-to-answer per candidate resident model.",
        epilog="example: python3 tools/latency_matrix.py --out results/raw/latency-20260819.json",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=None,
                    help="override the per-tier rep counts (chat 7, document 3, "
                         "folder 2). Rep 1 of each tier is cold, the rest warm.")
    ap.add_argument("--ctx", type=int, default=32768)
    ap.add_argument("--max-tokens", type=int, default=8192,
                    help="a SAFETY ceiling, not a target - generation runs to "
                         "completion so the metric stays time-to-answer")
    ap.add_argument("--server-bin",
                    default=os.environ.get("SPARKBENCH_SERVER_BIN", DEFAULT_SERVER))
    ap.add_argument("--server-extra", default="-b 512 -ub 128",
                    help="IDENTICAL across arms and recorded (Rule 8)")
    ap.add_argument("--tiers", default=None,
                    help="comma-separated tier subset, e.g. 'chat'. Default: all.")
    ap.add_argument("--arm-set", default="residency",
                    choices=["residency", "stage2", "gptoss"],
                    help="residency = the four candidate resident models; "
                         "stage2 = 27B at reasoning_effort off, MTP off vs n=4; "
                         "gptoss = gpt-oss-120b alone, compared against the "
                         "BANKED residency figures rather than re-running them")
    ap.add_argument("--port", type=int, default=8119)
    ap.add_argument("--load-timeout", type=float, default=300.0)
    ap.add_argument("--request-timeout", type=float, default=1800.0)
    args = ap.parse_args()

    # Rule 9: one GPU consumer, or every number below is a number about
    # contention rather than about the model.
    for name in ("llama-server", "llama-bench"):
        r = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
        if r.stdout.strip():
            print(f"FAIL: {name} already running (pids: {r.stdout.split()}). "
                  f"hint: a busy GPU voids every timing in this tool", file=sys.stderr)
            return 2

    staging = "/opt/models/staging"
    # Stage 2 fixes the model and the reasoning effort and varies ONLY
    # speculation, so the power profile (recorded below) is the sole remaining
    # factor across invocations. n=2 is deliberately absent: E59 stage 1 earned
    # the right to drop it, being slower AND less deterministic than n=4.
    # gpt-oss-120b is measured ALONE and compared against the banked residency
    # run of the same day, same kernel, same server binary and the same
    # --server-extra. Re-running the other four would cost ~15 minutes of GPU
    # to reproduce figures that are already pinned in verify_report_numbers.py,
    # and would introduce a second measurement of them to reconcile. The
    # comparability assumption is stated in the results file rather than
    # assumed silently (Rule 8: name the serving config the finding needs).
    if args.arm_set == "gptoss":
        arms = [
            {"label": "gptoss-120b", "thinking": "default",
             "model": f"{staging}/gpt-oss-120b-mxfp4-00001-of-00003.gguf"},
        ]
    elif args.arm_set == "stage2":
        arms = [
            {"label": "27B-off-nomtp", "thinking": "off", "server_extra_override": "",
             "model": f"{staging}/Qwen3.8-27B-Q4_K_M.gguf"},
            {"label": "27B-off-mtp4", "thinking": "off",
             "server_extra_override": "--spec-type draft-mtp --spec-draft-n-max 4",
             "model": f"{staging}/Qwen3.8-27B-Q4_K_M.gguf"},
        ]
    else:
        arms = [
        {"label": "workhorse-30B-A3B", "thinking": "default",
         "model": f"{staging}/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf"},
        {"label": "qwen38-27B-off", "thinking": "off",
         "model": f"{staging}/Qwen3.8-27B-Q4_K_M.gguf"},
        {"label": "qwen38-27B-low", "thinking": "low",
         "model": f"{staging}/Qwen3.8-27B-Q4_K_M.gguf"},
        {"label": "qwen3-8B", "thinking": "default",
         "model": f"{staging}/Qwen3-8B-Q4_K_M.gguf"},
    ]
    tiers = build_tiers()
    if args.tiers:
        want = {t.strip() for t in args.tiers.split(",")}
        tiers = [t for t in tiers if t["tier"] in want]
        if not tiers:
            raise SystemExit(
                f"no tier matches {args.tiers!r}. "
                f"hint: one or more of chat, document, folder"
            )
    # The power profile is a live system setting this tool cannot change
    # (polkit denies agent-spark), so it is RECORDED rather than asserted. A
    # result whose profile is unknown cannot be compared with one whose is.
    prof = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True)
    power_profile = prof.stdout.strip() or "unknown"
    print(f"power profile: {power_profile}")
    print("prompt tiers:")
    for t in tiers:
        print(f"  {t['tier']:9} {len(t['prompt']):>7,} chars  - {t['why']}")

    started = time.time()
    results = [run_arm(a, tiers, args) for a in arms]

    print(f"\n{'arm':20} {'tier':9} {'cold s':>9} {'warm med s':>11} "
          f"{'gen tok':>8} {'tok/s':>7}")
    table = []
    for res in results:
        for tier in tiers:
            rows = [r for r in res["rows"] if r["tier"] == tier["tier"]]
            cold = next((r["wall_s"] for r in rows if r["cache"] == "cold"), None)
            warm = [r["wall_s"] for r in rows if r["cache"] == "warm"]
            gens = [r["completion_tokens"] for r in rows if r["completion_tokens"]]
            tps = [r["tok_per_s"] for r in rows if r["tok_per_s"]]
            cell = {"arm": res["label"], "tier": tier["tier"], "cold_s": cold,
                    "warm_median_s": round(statistics.median(warm), 2) if warm else None,
                    "median_gen_tokens": round(statistics.median(gens)) if gens else None,
                    "median_tok_per_s": round(statistics.median(tps), 2) if tps else None}
            table.append(cell)
            print(f"{cell['arm']:20} {cell['tier']:9} {str(cell['cold_s']):>9} "
                  f"{str(cell['warm_median_s']):>11} "
                  f"{str(cell['median_gen_tokens']):>8} {str(cell['median_tok_per_s']):>7}")

    out = {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kernel": os.uname().release,
        "power_profile": power_profile,
        "arm_set": args.arm_set,
        "ctx": args.ctx, "max_tokens": args.max_tokens, "reps": args.reps,
        "server_extra": args.server_extra, "server_bin": args.server_bin,
        "wall_s": round(time.time() - started, 1),
        "tiers": [{"tier": t["tier"], "why": t["why"], "chars": len(t["prompt"])}
                  for t in tiers],
        "table": table, "arms": results,
    }
    Path(args.out).write_text(json.dumps(out, indent=2))
    print(f"\nwritten: {args.out}  ({out['wall_s']}s total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
