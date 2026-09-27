#!/usr/bin/env python3
# File: e146_speed.py
# Purpose: E146 block 1 client - time decode, prefill, decode-at-depth and determinism on ANY OpenAI-compatible server, identically for every engine.
# Project: sparkbench | Date: 2026-09-25
#
# Overview: results/e146-prereg.md (Amendment 1) requires ONE ruler for llama.cpp and Atlas, so speed is
# measured client-side from the streaming API and never taken from an engine's own timing fields (those are
# recorded beside it when present). Per request: TTFT = first content chunk minus send time; decode rate =
# (completion_tokens - 1) / (last chunk - first chunk), which assumes the first chunk carried one token
# (declared; speculative engines may put more in it, a small bias that is the same for every engine);
# prefill rate = prompt_tokens / TTFT, which includes one decode step (declared). Prompts: CODE and CHAT are
# E138's (imported, never copied), P8K/P32K/D1500 are E139's exact-token prompts from results/e139/prompts.json.
# Determinism sends one CHAT prompt N times at temperature 0 and compares byte hashes. A sampler thread polls
# amdgpu GTT+VRAM and MemAvailable every 0.5 s. Data flow: prompts -> stream_chat() -> runs[] -> medians ->
# JSON at --out. Dependencies: stdlib only (E138's prompts are read by importing tools/e138_speed.py).

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import statistics
import sys
import threading
import time
import urllib.parse
from pathlib import Path

ROOT = Path("/home/agent-spark/sparkbench")
DRM = Path("/sys/class/drm/card0/device")
sys.path.insert(0, str(ROOT / "tools"))


def load_prompts() -> dict[str, list[str]]:
    """CODE/CHAT from E138 (imported so they cannot drift), P8K/P32K/D1500 from E139's frozen file."""
    from e138_speed import PROMPTS as e138  # noqa: PLC0415 - heavy import only when needed

    e139 = json.loads((ROOT / "results/e139/prompts.json").read_text())["prompts"]
    out = {"CODE": [e138["CODE"]] * 3, "CHAT": [e138["CHAT"]] * 3}
    for name in ("P8K", "P32K", "D1500"):
        out[name] = [p["text"] for p in e139[name]]
    return out


def read_mem() -> dict[str, int]:
    meminfo = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, val = line.split(":", 1)
        meminfo[key] = int(val.split()[0]) * 1024
    return {
        "gtt": int((DRM / "mem_info_gtt_used").read_text()),
        "vram": int((DRM / "mem_info_vram_used").read_text()),
        "used": meminfo["MemTotal"] - meminfo["MemAvailable"],
    }


class MemSampler(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.baseline = read_mem()
        self.peak = dict(self.baseline)
        self.halt = threading.Event()

    def run(self) -> None:
        while not self.halt.is_set():
            for key, val in read_mem().items():
                self.peak[key] = max(self.peak[key], val)
            self.halt.wait(0.5)

    def summary(self) -> dict[str, float]:
        gib = 1024**3
        return {
            "baseline_gpu_gib": round(
                (self.baseline["gtt"] + self.baseline["vram"]) / gib, 2
            ),
            "peak_gpu_gib": round((self.peak["gtt"] + self.peak["vram"]) / gib, 2),
            "peak_host_used_gib": round(self.peak["used"] / gib, 2),
        }


def stream_chat(
    base_url: str,
    model: str,
    prompt: str,
    max_tokens: int,
    extra: dict,
    timeout_s: float,
) -> dict:
    """One streaming chat request. Raises RuntimeError with a hint on any transport or protocol failure."""
    parts = urllib.parse.urlsplit(base_url)
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
        "chat_template_kwargs": {"enable_thinking": False},
        **extra,
    }
    conn = http.client.HTTPConnection(parts.hostname, parts.port, timeout=timeout_s)
    t_send = time.perf_counter()
    try:
        conn.request(
            "POST",
            "/v1/chat/completions",
            json.dumps(body),
            {"Content-Type": "application/json"},
        )
        resp = conn.getresponse()
        if resp.status != 200:
            raise RuntimeError(
                f"HTTP {resp.status} from {base_url}: {resp.read()[:300]!r}. "
                f"hint: the engine rejected the request body; check --extra-json and the served model name"
            )
        first = last = None
        pieces: list[str] = []
        usage: dict | None = None
        chunks = 0
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            obj = json.loads(payload)
            if obj.get("usage"):
                usage = obj["usage"]
            choices = obj.get("choices") or []
            if not choices:
                continue
            delta = choices[0].get("delta") or {}
            piece = (delta.get("content") or "") + (
                delta.get("reasoning_content") or ""
            )
            if piece:
                now = time.perf_counter()
                first = first if first is not None else now
                last = now
                pieces.append(piece)
                chunks += 1
    except OSError as exc:
        raise RuntimeError(
            f"transport failure talking to {base_url}: {exc}. hint: is the server still up?"
        ) from exc
    finally:
        conn.close()
    if first is None or last is None:
        raise RuntimeError(
            f"no content chunks received from {base_url}. hint: the server answered 200 but streamed nothing; "
            f"check its log"
        )
    text = "".join(pieces)
    comp = (
        usage["completion_tokens"] if usage and "completion_tokens" in usage else None
    )
    prompt_n = usage["prompt_tokens"] if usage and "prompt_tokens" in usage else None
    n_out = comp if comp is not None else chunks
    ttft = first - t_send
    return {
        "ttft_s": round(ttft, 4),
        "wall_s": round(last - t_send, 4),
        "prompt_tokens": prompt_n,
        "completion_tokens": comp,
        "completion_tokens_source": "usage" if comp is not None else "chunk_count",
        "decode_tps": round((n_out - 1) / (last - first), 3)
        if last > first and n_out > 1
        else None,
        "prefill_tps": round(prompt_n / ttft, 2) if prompt_n and ttft > 0 else None,
        "sha256": hashlib.sha256(text.encode()).hexdigest()[:16],
        "text_head": text[:60],
    }


def median(values: list[float | None]) -> float | None:
    real = [v for v in values if v is not None]
    return round(statistics.median(real), 3) if real else None


def wait_ready(base_url: str, model: str, extra: dict, budget_s: float) -> None:
    """Poll with a tiny real request until the engine answers; a health route is not assumed to exist."""
    t0 = time.time()
    last = "no attempt"
    while time.time() - t0 < budget_s:
        try:
            stream_chat(base_url, model, "Say OK.", 4, extra, 60)
            return
        except RuntimeError as exc:
            last = str(exc)[:160]
            time.sleep(3)
    raise RuntimeError(
        f"engine at {base_url} not ready after {budget_s:.0f}s (last: {last}). hint: read the server log"
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E146 speed client: identical timing of decode, prefill and determinism on any OpenAI-compatible server.",
        epilog=(
            "examples:\n"
            "  tools/e146_speed.py --label Q0 --base-url http://127.0.0.1:8080 --model Qwen3.8-27B-Q4_K_M "
            "--out results/e146/speed-Q0.json --extra-json '{\"cache_prompt\": false}'\n"
            "  tools/e146_speed.py --label X1 --base-url http://127.0.0.1:8081 --model nvidia/Qwen3.8-27B-NVFP4 "
            "--out results/e146/speed-X1.json\n"
            "  tools/e146_speed.py ... --dry-run   (load prompts, print the plan, send nothing)"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--label", required=True, help="arm label recorded in the output")
    ap.add_argument(
        "--base-url", required=True, help="server root, e.g. http://127.0.0.1:8080"
    )
    ap.add_argument(
        "--model", required=True, help="model name the server expects in requests"
    )
    ap.add_argument("--out", required=True, help="JSON output path")
    ap.add_argument(
        "--extra-json",
        default="{}",
        help="extra request-body fields as JSON (e.g. cache_prompt:false)",
    )
    ap.add_argument(
        "--decode-max-tokens",
        type=int,
        default=384,
        help="max tokens for CODE/CHAT/D1500 (default 384)",
    )
    ap.add_argument(
        "--depth-max-tokens",
        type=int,
        default=128,
        help="max tokens for P8K/P32K (default 128)",
    )
    ap.add_argument(
        "--determinism-n",
        type=int,
        default=10,
        help="identical greedy requests (default 10)",
    )
    ap.add_argument(
        "--ready-budget-s",
        type=float,
        default=900,
        help="seconds to wait for the engine (default 900)",
    )
    ap.add_argument(
        "--timeout-s",
        type=float,
        default=1800,
        help="per-request timeout (default 1800)",
    )
    ap.add_argument("--dry-run", action="store_true", help="plan only; sends nothing")
    args = ap.parse_args()

    extra = json.loads(args.extra_json)
    prompts = load_prompts()
    plan = [
        ("CODE", args.decode_max_tokens),
        ("CHAT", args.decode_max_tokens),
        ("D1500", args.decode_max_tokens),
        ("P8K", args.depth_max_tokens),
        ("P32K", args.depth_max_tokens),
    ]
    print(
        f"[{args.label}] plan: {[(n, len(prompts[n]), m) for n, m in plan]} + determinism x{args.determinism_n}",
        flush=True,
    )
    if args.dry_run:
        return 0

    sampler = MemSampler()
    sampler.start()
    t_start = time.time()
    print(f"[{args.label}] waiting for {args.base_url} ...", flush=True)
    wait_ready(args.base_url, args.model, extra, args.ready_budget_s)
    print(f"[{args.label}] ready after {time.time() - t_start:.0f}s", flush=True)

    runs: list[dict] = []
    for name, max_tokens in plan:
        for rep, prompt in enumerate(prompts[name]):
            r = stream_chat(
                args.base_url, args.model, prompt, max_tokens, extra, args.timeout_s
            )
            r.update({"prompt": name, "rep": rep, "max_tokens": max_tokens})
            runs.append(r)
            print(
                f"[{args.label}] {name} rep{rep}: ttft {r['ttft_s']}s, decode {r['decode_tps']} tok/s "
                f"({r['completion_tokens']} out), prefill {r['prefill_tps']} tok/s ({r['prompt_tokens']} in) "
                f"elapsed {time.time() - t_start:.0f}s",
                flush=True,
            )

    hashes = []
    for i in range(args.determinism_n):
        r = stream_chat(
            args.base_url, args.model, prompts["CHAT"][0], 128, extra, args.timeout_s
        )
        hashes.append(r["sha256"])
        print(
            f"[{args.label}] determinism {i + 1}/{args.determinism_n}: {r['sha256']}",
            flush=True,
        )
    sampler.halt.set()

    by_prompt = {n: [r for r in runs if r["prompt"] == n] for n, _ in plan}
    result = {
        "label": args.label,
        "base_url": args.base_url,
        "model": args.model,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "extra_body": extra,
        "ruler": "client-side streaming; decode=(completion_tokens-1)/(last-first chunk); prefill=prompt_tokens/TTFT",
        "runs": runs,
        "medians": {
            n: {
                "decode_tps": median([r["decode_tps"] for r in rs]),
                "prefill_tps": median([r["prefill_tps"] for r in rs]),
                "ttft_s": median([r["ttft_s"] for r in rs]),
                "prompt_tokens": median([r["prompt_tokens"] for r in rs]),
            }
            for n, rs in by_prompt.items()
        },
        "determinism": {
            "n": len(hashes),
            "distinct": len(set(hashes)),
            "byte_equal": len(set(hashes)) == 1,
        },
        "memory": sampler.summary(),
        "total_s": round(time.time() - t_start, 1),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=1))
    med = result["medians"]
    print(
        f"[{args.label}] DONE CODE {med['CODE']['decode_tps']} CHAT {med['CHAT']['decode_tps']} tok/s | "
        f"P32K prefill {med['P32K']['prefill_tps']} decode@32K {med['P32K']['decode_tps']} | "
        f"determinism {result['determinism']['distinct']} distinct of {result['determinism']['n']} | "
        f"peak GPU {result['memory']['peak_gpu_gib']} GiB",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"FATAL: {exc}", file=sys.stderr)
        sys.exit(1)
