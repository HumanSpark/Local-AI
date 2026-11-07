#!/usr/bin/env python3
# File: e153_speed.py
# Purpose: E153 - time one already-running OpenAI-compatible engine on the fixed Flash-Next prompt set, on the client's clock.
# Project: sparkbench | Date: 2026-11-04
#
# Overview: E153 compares gufo, Halogen, Strata, Talus and llama.cpp. Their server-side `timings`
# blocks are not defined the same way (or absent), so the scored figures here are measured by this
# client from the stream, identically for every engine:
#   ttft_s        request sent -> first streamed text (content or reasoning)
#   prefill_tps   prompt_tokens / ttft_s
#   decode_tps    (completion_tokens - 1) / (last text chunk - first text chunk)
# completion_tokens is the engine's own usage.completion_tokens when it reports one (the ids it
# generated), else a local count with the Flash-Next tokenizer on the returned text; the local count
# is always recorded beside it and a gap over 2% is flagged (count_mismatch) as a ruler problem.
# prompt_tokens is counted locally on the user/assistant text plus the engine's usage figure; the
# prefill rate uses the engine's usage.prompt_tokens when present (it includes the chat template),
# else the local count, and records which. Requests: greedy, thinking off, single stream, one at a
# time, in a fixed order; a short warm-up request is sent first and excluded. A 1 Hz sampler records
# power, GTT+VRAM and MemAvailable. The process that serves the engine is started and stopped by
# tools/run_e153_window.sh; this client only waits for /v1/models, then measures.
# Run with var/ft-venv/bin/python (needs the `tokenizers` package).

from __future__ import annotations

import argparse
import json
import statistics
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path("/home/bench/sparkbench")
DRM = Path("/sys/class/drm/card0/device")
TOKENIZER = Path(
    "/opt/models/staging/halogen-qwen3.8-flash-next-v2/tokenizer/tokenizer.json"
)
ORDER = ["CODE", "PROSE", "JSON", "AGENT", "P8K", "P32K"]
MAX_TOKENS = {
    "CODE": 512,
    "PROSE": 512,
    "JSON": 512,
    "AGENT": 400,
    "P8K": 256,
    "P32K": 256,
}


def power_path() -> Path:
    hits = sorted(DRM.glob("hwmon/hwmon*/power1_average"))
    if not hits:
        raise RuntimeError(
            f"no power1_average under {DRM}/hwmon. hint: check /sys/class/hwmon/*/name for amdgpu"
        )
    return hits[0]


class Sampler(threading.Thread):
    """1 Hz timestamped MemAvailable, GTT+VRAM and package power."""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.pw = power_path()
        self.samples: list[dict] = []
        self.stop = threading.Event()
        self.baseline = self.read()

    def read(self) -> dict:
        mem = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, v = line.split(":", 1)
            mem[k] = int(v.split()[0]) * 1024
        return {
            "t": time.time(),
            "avail": mem["MemAvailable"],
            "gpu": int((DRM / "mem_info_gtt_used").read_text())
            + int((DRM / "mem_info_vram_used").read_text()),
            "power_w": int(self.pw.read_text()) / 1e6,
        }

    def run(self) -> None:
        while not self.stop.is_set():
            self.samples.append(self.read())
            self.stop.wait(1.0)

    def power_mean(self, t0: float, t1: float) -> float | None:
        w = [s["power_w"] for s in self.samples if t0 <= s["t"] <= t1]
        return round(statistics.mean(w), 1) if w else None

    def summary(self) -> dict:
        gib = 1024**3
        peak = max(s["gpu"] for s in self.samples)
        return {
            "baseline_gpu_gib": round(self.baseline["gpu"] / gib, 2),
            "peak_gpu_gib": round(peak / gib, 2),
            "min_memavailable_gib": round(
                min(s["avail"] for s in self.samples) / gib, 2
            ),
            "n_samples": len(self.samples),
        }


def wait_ready(base: str, timeout: float, headers: dict) -> str:
    """Poll /v1/models until it answers; return the first model id."""
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        try:
            req = urllib.request.Request(f"{base}/v1/models", headers=headers)
            with urllib.request.urlopen(req, timeout=10) as r:
                ids = [m["id"] for m in json.loads(r.read().decode())["data"]]
                if ids:
                    return ids[0]
                last = "empty model list"
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError) as e:
            last = repr(e)  # not listening yet - the expected state during load
        time.sleep(3)
    raise RuntimeError(
        f"{base}/v1/models did not answer within {timeout:.0f}s (last: {last}). hint: read the arm's serverlog"
    )


def stream_one(
    base: str,
    model: str,
    messages: list[dict],
    max_tokens: int,
    timeout: float,
    headers: dict,
) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        f"{base}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
    )
    content: list[str] = []
    reasoning: list[str] = []
    t_first = t_last = None
    usage = timings = None
    finish = None
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                if chunk.get("usage"):
                    usage = chunk["usage"]
                if chunk.get("timings"):
                    timings = chunk["timings"]
                for ch in chunk.get("choices") or []:
                    delta = ch.get("delta") or {}
                    text = delta.get("content") or ""
                    rtext = (
                        delta.get("reasoning_content") or delta.get("reasoning") or ""
                    )
                    if text or rtext:
                        now = time.time()
                        t_first = t_first or now
                        t_last = now
                        content.append(text)
                        reasoning.append(rtext)
                    if ch.get("finish_reason"):
                        finish = ch["finish_reason"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"HTTP {e.code} from {base}: {e.read()[:300]!r}. hint: read the arm's serverlog"
        ) from e
    t_end = time.time()
    if t_first is None:
        raise RuntimeError(
            f"no streamed text from {base} (finish={finish}). hint: the engine may not stream deltas; read its serverlog"
        )
    return {
        "t0": t0,
        "t_first": t_first,
        "t_last": t_last,
        "t_end": t_end,
        "content": "".join(content),
        "reasoning": "".join(reasoning),
        "usage": usage,
        "timings": timings,
        "finish_reason": finish,
    }


def local_prompt_tokens(tok: Tokenizer, messages: list[dict]) -> int:
    return sum(
        len(tok.encode(m["content"], add_special_tokens=False).ids) for m in messages
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E153: time one running engine on results/e153/prompts.json (client-side clock).",
        epilog="example: var/ft-venv/bin/python tools/e153_speed.py --arm G --url http://127.0.0.1:8153 "
        "--out results/e153/speed-G.json",
    )
    ap.add_argument("--arm", required=True)
    ap.add_argument("--url", required=True, help="base URL, without /v1")
    ap.add_argument("--prompts", default=str(ROOT / "results/e153/prompts.json"))
    ap.add_argument(
        "--buckets",
        default=",".join(ORDER),
        help=f"comma list, run in this order (default {','.join(ORDER)})",
    )
    ap.add_argument(
        "--model",
        default=None,
        help="model id to send (default: first id from /v1/models)",
    )
    ap.add_argument(
        "--api-key", default=None, help="Bearer key, if the engine requires one"
    )
    ap.add_argument("--load-timeout", type=float, default=1200.0)
    ap.add_argument("--request-timeout", type=float, default=900.0)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="load prompts and tokenizer, print the plan, send nothing",
    )
    args = ap.parse_args()

    tok = Tokenizer.from_file(str(TOKENIZER))
    P = json.loads(Path(args.prompts).read_text())["buckets"]
    buckets = [b for b in args.buckets.split(",") if b]
    for b in buckets:
        if b not in P:
            raise SystemExit(
                f"unknown bucket {b!r}; have {sorted(P)}. hint: rebuild with tools/e153_prompts.py"
            )
    plan = [(b, item) for b in buckets for item in P[b]]
    if args.dry_run:
        print(f"{args.arm}: {len(plan)} requests in {buckets}; tokenizer {TOKENIZER}")
        return 0

    headers = {"Authorization": f"Bearer {args.api_key}"} if args.api_key else {}
    sampler = Sampler()
    sampler.start()
    t_load0 = time.time()
    model = args.model or wait_ready(args.url, args.load_timeout, headers)
    if args.model:
        wait_ready(args.url, args.load_timeout, headers)
    ready_s = round(time.time() - t_load0, 1)
    print(f"{args.arm}: ready after {ready_s}s, model id {model!r}", flush=True)

    warm = stream_one(
        args.url,
        model,
        [{"role": "user", "content": "Say hello in five words."}],
        16,
        args.request_timeout,
        headers,
    )
    print(f"{args.arm}: warm-up {round(warm['t_end'] - warm['t0'], 2)}s", flush=True)

    records = []
    for b, item in plan:
        r = stream_one(
            args.url,
            model,
            item["messages"],
            MAX_TOKENS[b],
            args.request_timeout,
            headers,
        )
        n_local = len(
            tok.encode(r["content"] + r["reasoning"], add_special_tokens=False).ids
        )
        u = r["usage"] or {}
        p_engine = u.get("prompt_tokens")
        p_local = local_prompt_tokens(tok, item["messages"])
        ttft = r["t_first"] - r["t0"]
        span = r["t_last"] - r["t_first"]
        n_engine = u.get("completion_tokens")
        n = n_engine or n_local
        rec = {
            "bucket": b,
            "name": item["name"],
            "prompt_sha256": item["sha256"],
            "max_tokens": MAX_TOKENS[b],
            "ttft_s": round(ttft, 3),
            "wall_s": round(r["t_end"] - r["t0"], 3),
            "prompt_tokens_engine": p_engine,
            "prompt_tokens_local": p_local,
            "prefill_tps": round((p_engine or p_local) / ttft, 1),
            "prefill_basis": "engine" if p_engine else "local",
            "completion_tokens_local": n_local,
            "completion_tokens_engine": n_engine,
            "decode_basis": "engine" if n_engine else "local",
            # Re-tokenising text can differ slightly from the ids generated; a gap over 2% is a ruler
            # problem to resolve before comparing engines, not a speed difference.
            "count_mismatch": bool(n_engine)
            and abs(n_local - n_engine) > 0.02 * n_engine,
            "decode_tps": round((n - 1) / span, 2) if span > 0 and n > 1 else None,
            "finish_reason": r["finish_reason"],
            "thinking_leak": bool(r["reasoning"].strip()) or "<think>" in r["content"],
            "power_w": sampler.power_mean(r["t0"], r["t_end"]),
            "timings_engine": r["timings"],
            "content": r["content"],
        }
        records.append(rec)
        print(
            f"  {args.arm} {item['name']}: ttft {rec['ttft_s']}s prefill {rec['prefill_tps']} decode {rec['decode_tps']} "
            f"tok/s, {n} tok [{rec['decode_basis']}] ({rec['finish_reason']}), {rec['power_w']} W"
            + ("  THINKING LEAK" if rec["thinking_leak"] else "")
            + ("  COUNT MISMATCH" if rec["count_mismatch"] else ""),
            flush=True,
        )
    sampler.stop.set()

    def med(b: str, k: str) -> float | None:
        v = [r[k] for r in records if r["bucket"] == b and r[k] is not None]
        return round(statistics.median(v), 2) if v else None

    result = {
        "arm": args.arm,
        "url": args.url,
        "model_id": model,
        "ready_s": ready_s,
        "prompts_file": args.prompts,
        "tokenizer": str(TOKENIZER),
        "buckets": {
            b: {
                "n": sum(1 for r in records if r["bucket"] == b),
                "decode_tps_median": med(b, "decode_tps"),
                "prefill_tps_median": med(b, "prefill_tps"),
                "ttft_s_median": med(b, "ttft_s"),
                "wall_s_median": med(b, "wall_s"),
                "power_w_median": med(b, "power_w"),
            }
            for b in buckets
        },
        "thinking_leaks": sum(r["thinking_leak"] for r in records),
        "count_mismatches": sum(r["count_mismatch"] for r in records),
        "memory": sampler.summary(),
        "records": records,
    }
    Path(args.out).write_text(json.dumps(result, indent=1))
    print(
        f"{args.arm}: "
        + json.dumps(
            {
                b: [v["prefill_tps_median"], v["decode_tps_median"]]
                for b, v in result["buckets"].items()
            }
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
