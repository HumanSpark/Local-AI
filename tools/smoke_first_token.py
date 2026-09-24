#!/usr/bin/env python3
# File: smoke_first_token.py
# Purpose: Does this model emit a FIRST TOKEN at all? Separates a stalled decode from a runaway generation, cheaply.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: gpt-oss-120b loaded completely on 2026-08-19 - full-offload gate
# passed, context preflight passed, 64 GiB resident, request tokenized, decode
# posted - and then stopped responding and stopped logging. Twelve questions
# recorded `transport_failed` and no capability information was produced. See
# docs/2026-08-19-gptoss120b-decode-hang.md.
#
# Re-running a twelve-question tier against a model that may not emit ONE token
# costs twelve minutes and yields nothing. This asks the smallest question that
# discriminates: a ten-token prompt, a 32-token ceiling, a hard timeout.
#
# TIME TO FIRST TOKEN IS THE MEASUREMENT, not the response. If loading succeeds,
# prompt evaluation succeeds, and the first sampled token never appears, the
# boundary is narrowed enormously - that is a different fault from one where
# tokens flow and never stop. So this STREAMS, and stamps the arrival of the
# first chunk separately from completion. A non-streaming call cannot tell those
# apart: both look like one long silence.
#
# IT DOES NOT NAME A CAUSE. A stalled first token is consistent with waiting on
# a GPU fence, but the observed symptom is a stalled decode and nothing more.
# The output says what was observed and which branch it supports; it does not
# claim a mechanism it did not measure.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_SERVER = "/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server"

# Deliberately trivial: no document pack, no reasoning bait, nothing that could
# justify a long think. If THIS does not produce a token, the prompt is not why.
PROMPT = "Reply with exactly the word: ready"


def stream_first_token(port: int, max_tokens: int, timeout: float,
                       thinking: str) -> dict:
    """Send one streaming request; stamp first chunk and completion separately."""
    payload: dict = {
        "messages": [{"role": "user", "content": PROMPT}],
        "temperature": 0, "max_tokens": max_tokens, "stream": True,
    }
    if thinking == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    elif thinking in ("low", "medium", "xhigh"):
        payload["reasoning_effort"] = thinking

    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    ttft = None
    chunks = 0
    text = ""
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
                piece = delta.get("content") or ""
                think = delta.get("reasoning_content") or ""
                if (piece or think) and ttft is None:
                    ttft = time.time() - t0
                chunks += 1
                text += piece
                reasoning += len(think)
    except Exception as exc:  # noqa: BLE001 - every failure shape is a RESULT here
        return {"outcome": "transport_failed", "error": f"{type(exc).__name__}: {exc}",
                "ttft_s": round(ttft, 2) if ttft else None,
                "total_s": round(time.time() - t0, 2), "chunks": chunks,
                "text": text[:200], "reasoning_chars": reasoning}
    return {"outcome": "completed", "error": None,
            "ttft_s": round(ttft, 2) if ttft else None,
            "total_s": round(time.time() - t0, 2), "chunks": chunks,
            "text": text[:200], "reasoning_chars": reasoning}


def verdict(r: dict, max_tokens: int) -> tuple[str, str]:
    """Which PRE-REGISTERED branch the observation supports. Registered 2026-08-19."""
    if r["outcome"] == "transport_failed" and r["ttft_s"] is None:
        return ("STALLED_BEFORE_FIRST_TOKEN",
                "No generated token before the timeout. Supports a first-decode "
                "stall. This does NOT by itself prove the Vulkan/RADV backend is "
                "the cause - the observed symptom is a stalled decode.")
    if r["ttft_s"] is not None and r["outcome"] == "transport_failed":
        return ("TOKENS_THEN_NO_TERMINATION",
                f"First token at {r['ttft_s']}s, then generation never "
                f"terminated. Supports the reasoning/runaway branch (the F71 "
                f"shape).")
    if r["outcome"] == "completed" and r["chunks"] > 0:
        return ("COMPLETED_NORMALLY",
                f"Generation completed in {r['total_s']}s, first token at "
                f"{r['ttft_s']}s. The failure is INTERMITTENT or workload/context "
                f"dependent. Only NOW is a slightly larger reproduction justified.")
    return ("UNCLEAR", "Completed with no content. Preserve the serverlog and "
                       "inspect before another attempt.")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Smallest test that separates a stalled decode from a runaway.",
        epilog="example: python3 tools/smoke_first_token.py "
               "--model /opt/models/staging/gpt-oss-120b-mxfp4-00001-of-00003.gguf",
    )
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", default="smoke")
    ap.add_argument("--max-tokens", type=int, default=32)
    ap.add_argument("--timeout", type=float, default=120.0,
                    help="HARD ceiling on the request, in seconds")
    ap.add_argument("--ctx", type=int, default=8192)
    ap.add_argument("--thinking", default="default",
                    choices=["default", "off", "low", "medium", "xhigh"])
    ap.add_argument("--server-extra", default="")
    ap.add_argument("--server-bin", default=DEFAULT_SERVER)
    ap.add_argument("--port", type=int, default=8123)
    ap.add_argument("--load-timeout", type=float, default=900.0)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    r = subprocess.run(["pgrep", "-x", "llama-server"], capture_output=True, text=True)
    if r.stdout.strip():
        print(f"FAIL: llama-server already running (pids: {r.stdout.split()}). "
              f"hint: one GPU consumer at a time", file=sys.stderr)
        return 2

    log_path = Path(args.out).with_suffix(".serverlog") if args.out else Path(
        f"/tmp/{args.label}.serverlog")
    cmd = [args.server_bin, "-m", args.model, "-c", str(args.ctx), "-np", "1",
           "--host", "127.0.0.1", "--port", str(args.port), "--no-webui", "-v"]
    cmd += args.server_extra.split()
    print(f"=== smoke: {args.label} ===\n{' '.join(cmd)}")
    log_f = log_path.open("w")
    proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)

    result: dict = {}
    try:
        deadline = time.time() + args.load_timeout
        healthy = False
        while time.time() < deadline:
            if proc.poll() is not None:
                # A crash IS a result - preserve the evidence before retrying.
                print(f"\nSERVER EXITED during load, code {proc.returncode}. "
                      f"Preserve {log_path}, and ask Alastair for `dmesg | grep -i "
                      f"amdgpu` - agent-spark cannot read the kernel ring buffer.")
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
            print(f"server never became healthy within {args.load_timeout}s")
            return 4
        print(f"loaded. sending a {len(PROMPT)}-char prompt, max_tokens="
              f"{args.max_tokens}, hard timeout {args.timeout}s...")
        result = stream_first_token(args.port, args.max_tokens, args.timeout,
                                    args.thinking)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=30)
        log_f.close()

    name, why = verdict(result, args.max_tokens)
    print(f"\n  time to FIRST token : {result['ttft_s']}")
    print(f"  total request time  : {result['total_s']}s")
    print(f"  stream chunks       : {result['chunks']}")
    print(f"  reasoning chars     : {result['reasoning_chars']}")
    print(f"  text                : {result['text']!r}")
    print(f"  error               : {result['error']}")
    print(f"\n>>> {name}\n    {why}")

    if args.out:
        Path(args.out).write_text(json.dumps(
            {**result, "verdict": name, "why": why, "model": args.model,
             "label": args.label, "max_tokens": args.max_tokens,
             "timeout": args.timeout, "ctx": args.ctx,
             "thinking": args.thinking, "server_extra": args.server_extra,
             "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, indent=2))
        print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
