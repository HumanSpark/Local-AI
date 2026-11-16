#!/usr/bin/env python3
# File: tools/e163_speed.py
# Purpose: E163 speed block - time E139's fixed prompts against ANY OpenAI-compatible server with one client-side ruler.
# Project: sparkbench | Date: 2026-11-16
#
# Overview: Loom reports no server `timings`, Halogen and llama-server do, so comparing engines on their own
# timings would compare rulers (MEASUREMENT-TRAPS). Every arm is therefore timed HERE, from a streamed response:
#   prefill_tps = prompt_tokens / time-to-first-streamed-token   (includes one decode step and HTTP: a slight undercount)
#   decode_tps  = (completion_tokens - 1) / (t_last_token - t_first_token)
# prompt_tokens and completion_tokens come from the server's usage block (stream_options.include_usage); a missing
# usage block is an error, never a guess. Server `timings`, when present, are recorded beside the client figures.
# Prompts: results/e139/prompts.json (P8K x3, P32K x3 at 256 generated tokens; D1500 at 512), non-overlapping, so no
# request reuses another's prefix cache. Thinking is off on every request (--thinking-off picks the field spelling the
# engine consumes). Temperature 0. Writes one JSON with every request and the medians. Prereg results/e163-prereg.md.

from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def served_model(base: str) -> str:
    with urllib.request.urlopen(f"{base}/v1/models", timeout=30) as r:
        data = json.loads(r.read())["data"]
    if not data:
        raise RuntimeError(
            f"{base}/v1/models lists no model. hint: the server is not ready"
        )
    return data[0]["id"]


def ask(
    base: str,
    model: str,
    prompt: str,
    max_tokens: int,
    thinking_off: str,
    timeout: float,
) -> dict:
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    if thinking_off == "top":
        payload["enable_thinking"] = False
    else:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(
        f"{base}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    t_first = t_last = None
    usage = None
    timings = None
    text = []
    reasoning_chars = 0
    finish = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for raw in r:
                line = raw.decode(errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                body = line[5:].strip()
                if body == "[DONE]":
                    break
                ev = json.loads(body)
                if ev.get("usage"):
                    usage = ev["usage"]
                if ev.get("timings"):
                    timings = ev["timings"]
                for ch in ev.get("choices") or []:
                    d = ch.get("delta") or {}
                    piece = (d.get("content") or "") + (
                        d.get("reasoning_content") or ""
                    )
                    reasoning_chars += len(d.get("reasoning_content") or "")
                    if piece:
                        now = time.time()
                        t_first = t_first or now
                        t_last = now
                        text.append(d.get("content") or "")
                    if ch.get("finish_reason"):
                        finish = ch["finish_reason"]
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"HTTP {e.code} from {base}: {e.read()[:400]!r}. hint: read the arm's serverlog"
        ) from e
    t_end = time.time()
    if usage is None or t_first is None:
        raise RuntimeError(
            f"no usage block or no streamed token from {base} (usage={usage!r}). "
            "hint: the engine must honour stream_options.include_usage"
        )
    pt, ct = usage["prompt_tokens"], usage["completion_tokens"]
    ttft = t_first - t0
    dec_span = t_last - t_first
    return {
        "prompt_tokens": pt,
        "completion_tokens": ct,
        "cached_tokens": (usage.get("prompt_tokens_details") or {}).get(
            "cached_tokens"
        ),
        "ttft_s": round(ttft, 3),
        "wall_s": round(t_end - t0, 3),
        "prefill_tps": round(pt / ttft, 1),
        "decode_tps": round((ct - 1) / dec_span, 2)
        if ct > 1 and dec_span > 0
        else None,
        "finish_reason": finish,
        "reasoning_chars": reasoning_chars,
        "content_head": "".join(text)[:160],
        "server_timings": timings,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E163 speed block: client-timed prefill and decode on E139's prompts.",
        epilog="example: tools/e163_speed.py --label LM --base http://127.0.0.1:8154 --thinking-off top "
        "--out results/e163/raw/LM/speed.json",
    )
    ap.add_argument("--label", required=True)
    ap.add_argument("--base", default="http://127.0.0.1:8154")
    ap.add_argument(
        "--thinking-off",
        choices=["top", "kwargs"],
        required=True,
        help="top = enable_thinking:false (Loom); kwargs = chat_template_kwargs (llama-server, Halogen)",
    )
    ap.add_argument("--prompts", default=str(ROOT / "results/e139/prompts.json"))
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    P = json.loads(Path(a.prompts).read_text())["prompts"]
    model = served_model(a.base)
    plan = (
        [("P8K", p, 256) for p in P["P8K"]]
        + [("P32K", p, 256) for p in P["P32K"]]
        + [("D1500", p, 512) for p in P["D1500"]]
    )
    rows = []
    t_start = time.time()
    for i, (name, p, mt) in enumerate(plan, 1):
        print(
            f"[{a.label}] {i}/{len(plan)} {name} rep {p['rep']} ({p['content_tokens']} content tokens) "
            f"elapsed {time.time() - t_start:.0f}s",
            flush=True,
        )
        r = ask(a.base, model, p["text"], mt, a.thinking_off, a.timeout)
        r.update(
            {"prompt": name, "rep": p["rep"], "sha256": p["sha256"], "max_tokens": mt}
        )
        print(
            f"[{a.label}]   prompt {r['prompt_tokens']} tok, ttft {r['ttft_s']}s -> prefill {r['prefill_tps']} tok/s; "
            f"decode {r['decode_tps']} tok/s over {r['completion_tokens']} tok; finish {r['finish_reason']}",
            flush=True,
        )
        rows.append(r)

    def med(prompt: str, key: str) -> float | None:
        v = [r[key] for r in rows if r["prompt"] == prompt and r[key] is not None]
        return round(statistics.median(v), 2) if v else None

    summary = {
        p: {
            "prefill_tps": med(p, "prefill_tps"),
            "decode_tps": med(p, "decode_tps"),
            "ttft_s": med(p, "ttft_s"),
        }
        for p in ("P8K", "P32K", "D1500")
    }
    out = {
        "label": a.label,
        "base": a.base,
        "model": model,
        "thinking_off": a.thinking_off,
        "prompts_file": a.prompts,
        "summary": summary,
        "requests": rows,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps({"label": a.label, "summary": summary}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
