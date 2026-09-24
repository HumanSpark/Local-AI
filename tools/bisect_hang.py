#!/usr/bin/env python3
# File: bisect_hang.py
# Purpose: Find WHICH variable makes a model stall, by walking a ladder of conditions inside ONE model load.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: gpt-oss-120b stalled on the L3-hard tier (12x transport_failed) but
# a smoke test completed normally - first token in 0.98s, 31 chunks, 1.5s total.
# So it is not a load failure, not a first-decode stall, and not a runaway. The
# smoke test's registered branch 3 applies: the failure is INTERMITTENT or
# WORKLOAD/CONTEXT DEPENDENT, and a slightly larger reproduction is justified.
#
# THE LOAD IS THE EXPENSIVE PART, not the request. Loading 59 GiB takes minutes;
# a request takes seconds. Testing N conditions with N loads wastes almost all of
# the wall clock on reloading a model that already works. This loads ONCE and
# walks a ladder, which also removes load-to-load variation as a confound - every
# rung sees the identical resident model.
#
# THE LADDER MOVES ONE VARIABLE AT A TIME, from the condition known to WORK
# toward the condition known to FAIL:
#
#   rung 1  tiny prompt,  small max_tokens   - the smoke test, reproduced
#   rung 2  tiny prompt,  large max_tokens   - is the ANSWER BUDGET the trigger?
#   rung 3  medium prompt, small max_tokens  - is PROMPT SIZE the trigger?
#   rung 4  real pack,    small max_tokens   - the real prompt, cheap answer
#   rung 5  real pack,    large max_tokens   - the failing condition, in full
#
# The first rung that stalls names the variable. If none stall, the failure is
# intermittent rather than deterministic, which is itself the finding and is
# reported as such rather than as a pass.
#
# EVERY RUNG HAS A HARD TIMEOUT and the ladder STOPS at the first stall - there
# is nothing to learn from rungs above the one that already failed, and each
# costs a timeout's worth of wall clock.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))
DEFAULT_SERVER = "/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server"


def build_rungs() -> list[dict]:
    from corpus_l3 import build_pack_l3  # noqa: PLC0415 - needs the spike path set above
    pack = build_pack_l3(distractor_count=0)
    tiny = "Reply with exactly the word: ready"
    medium = ("Summarise the following in one sentence.\n\n" + pack[:4000])
    real = ("You are assisting on a professional advisory engagement. Answer "
            "using ONLY the pack below.\n\n=== PACK ===\n" + pack +
            "\n\n=== QUESTION ===\nWhat is the monthly fee? Give the amount in EUR.")
    return [
        {"rung": 1, "why": "the smoke test, reproduced", "prompt": tiny, "max_tokens": 32},
        {"rung": 2, "why": "is the ANSWER BUDGET the trigger?", "prompt": tiny, "max_tokens": 4096},
        {"rung": 3, "why": "is PROMPT SIZE the trigger?", "prompt": medium, "max_tokens": 32},
        {"rung": 4, "why": "real pack, cheap answer", "prompt": real, "max_tokens": 32},
        {"rung": 5, "why": "the failing condition, in full", "prompt": real, "max_tokens": 4096},
    ]


def ask_stream(port: int, prompt: str, max_tokens: int, timeout: float) -> dict:
    payload = {"messages": [{"role": "user", "content": prompt}],
               "temperature": 0, "max_tokens": max_tokens, "stream": True}
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    ttft = None
    chunks = 0
    content = ""
    reasoning = 0
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for raw in r:
                line = raw.decode(errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                body = line[5:].strip()
                if body == "[DONE]":
                    break
                try:
                    d = json.loads(body)
                except json.JSONDecodeError:
                    continue
                delta = (d.get("choices") or [{}])[0].get("delta") or {}
                c, th = delta.get("content") or "", delta.get("reasoning_content") or ""
                if (c or th) and ttft is None:
                    ttft = time.time() - t0
                chunks += 1
                content += c
                reasoning += len(th)
        return {"stalled": False, "error": None, "ttft_s": round(ttft, 2) if ttft else None,
                "total_s": round(time.time() - t0, 2), "chunks": chunks,
                "content_chars": len(content), "reasoning_chars": reasoning}
    except Exception as exc:  # noqa: BLE001 - a failure here IS the measurement
        return {"stalled": True, "error": f"{type(exc).__name__}: {exc}",
                "ttft_s": round(ttft, 2) if ttft else None,
                "total_s": round(time.time() - t0, 2), "chunks": chunks,
                "content_chars": len(content), "reasoning_chars": reasoning}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Walk a ladder of conditions inside one model load to find the stall trigger.",
        epilog="example: python3 tools/bisect_hang.py --model /opt/models/staging/x.gguf "
               "--out results/raw/bisect.json")
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", default="bisect")
    ap.add_argument("--ctx", type=int, default=32768,
                    help="matched to the FAILING run, not to the smoke test")
    ap.add_argument("--timeout", type=float, default=180.0, help="per rung")
    ap.add_argument("--server-bin", default=DEFAULT_SERVER)
    ap.add_argument("--server-extra", default="")
    ap.add_argument("--port", type=int, default=8124)
    ap.add_argument("--load-timeout", type=float, default=900.0)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    r = subprocess.run(["pgrep", "-x", "llama-server"], capture_output=True, text=True)
    if r.stdout.strip():
        print(f"FAIL: llama-server already running ({r.stdout.split()})", file=sys.stderr)
        return 2

    rungs = build_rungs()
    log_path = Path(args.out).with_suffix(".serverlog")
    cmd = [args.server_bin, "-m", args.model, "-c", str(args.ctx), "-np", "1",
           "--host", "127.0.0.1", "--port", str(args.port), "--no-webui", "-v"]
    cmd += args.server_extra.split()
    print(f"=== bisect: {args.label} ===\n{' '.join(cmd)}")
    for x in rungs:
        print(f"  rung {x['rung']}: {len(x['prompt']):>6,} prompt chars, "
              f"max_tokens {x['max_tokens']:>5}  - {x['why']}")
    log_f = log_path.open("w")
    proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)

    results: list[dict] = []
    trigger = None
    try:
        deadline = time.time() + args.load_timeout
        healthy = False
        while time.time() < deadline:
            if proc.poll() is not None:
                print(f"SERVER EXITED during load, code {proc.returncode}. "
                      f"Preserve {log_path}.")
                return 3
            try:
                with urllib.request.urlopen(
                        f"http://127.0.0.1:{args.port}/health", timeout=5) as h:
                    if h.status == 200:
                        healthy = True
                        break
            except Exception:  # noqa: BLE001 - poll boundary
                pass
            time.sleep(3)
        if not healthy:
            print(f"server never healthy within {args.load_timeout}s")
            return 4
        print("\nloaded. walking the ladder...\n")
        for x in rungs:
            res = ask_stream(args.port, x["prompt"], x["max_tokens"], args.timeout)
            results.append({**x, "prompt": None, "prompt_chars": len(x["prompt"]), **res})
            flag = "STALLED" if res["stalled"] else "ok"
            print(f"  rung {x['rung']}  {flag:8} ttft={str(res['ttft_s']):>6} "
                  f"total={res['total_s']:>7}s chunks={res['chunks']:>5} "
                  f"reasoning={res['reasoning_chars']:>7} {res['error'] or ''}")
            if res["stalled"]:
                trigger = x
                print(f"\n  >>> STOPPING. Rung {x['rung']} is the first to stall: "
                      f"{x['why']}")
                break
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=30)
        log_f.close()

    if trigger:
        verdict = (f"First stall at rung {trigger['rung']} "
                   f"({trigger['prompt_chars'] if 'prompt_chars' in trigger else '?'} "
                   f"prompt chars, max_tokens {trigger['max_tokens']}). "
                   f"The variable that rung introduced is the trigger.")
    else:
        verdict = ("NO rung stalled. The original failure is INTERMITTENT rather "
                   "than deterministic - it is not reproduced by any condition on "
                   "this ladder. Report as intermittent; do NOT report the "
                   "original run as explained.")
    print(f"\n>>> {verdict}")
    Path(args.out).write_text(json.dumps(
        {"label": args.label, "model": args.model, "ctx": args.ctx,
         "timeout": args.timeout, "server_extra": args.server_extra,
         "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "verdict": verdict, "first_stall_rung": trigger["rung"] if trigger else None,
         "rungs": results}, indent=2))
    print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
