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
    elif thinking_off == "effort-none-kwargs":
        # llama.cpp / Loom pass chat_template_kwargs straight to the template (E172 A4)
        payload["chat_template_kwargs"] = {"reasoning_effort": "none"}
    elif thinking_off == "effort0":
        # CIRU's Inkling template has no enable_thinking; its off switch is reasoning_effort "none" -> 0.0 (default 0.9).
        # Must be the top-level request field: vLLM merges its own reasoning_effort (None when unset) OVER
        # chat_template_kwargs, so a kwargs value never reaches the template. E172 A3 notes 2-3.
        payload["reasoning_effort"] = "none"
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
                    # llama.cpp/Loom stream thinking as reasoning_content; vLLM 0.34 (CIRU, E172 IC) as reasoning
                    piece = (d.get("content") or "") + (
                        d.get("reasoning_content") or d.get("reasoning") or ""
                    )
                    reasoning_chars += len(d.get("reasoning_content") or d.get("reasoning") or "")
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
        choices=["top", "kwargs", "effort0", "effort-none-kwargs", "auto-off", "min-thinking"],
        required=True,
        help="top = enable_thinking:false (Loom); kwargs = chat_template_kwargs (llama-server, Halogen); "
        "effort0 = top-level reasoning_effort none (vLLM); effort-none-kwargs = chat_template_kwargs reasoning_effort none; "
        "auto-off = probe those switches on one short request, keep the first that streams content with zero reasoning, "
        "and refuse to measure if none does (E172 A4)",
    )
    ap.add_argument("--prompts", default=str(ROOT / "results/e139/prompts.json"))
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    P = json.loads(Path(a.prompts).read_text())["prompts"]
    model = served_model(a.base)
    mode = a.thinking_off
    probe_log = []
    if mode == "min-thinking":
        # E172 A5: Inkling-2-Mini never reaches zero reasoning; use the switch that leaves the LEAST reasoning before a
        # real answer, and record how much remained. Default thinking (no switch effect) is probed as the baseline.
        best = None
        for cand in ("effort0", "effort-none-kwargs", "kwargs", "top"):
            try:
                r = ask(a.base, model, "In one sentence, what is a spreadsheet?", 128, cand, a.timeout)
            except RuntimeError as e:
                probe_log.append({"switch": cand, "error": str(e)[:200]})
                print(f"[{a.label}] min-thinking probe {cand}: error {str(e)[:120]}", flush=True)
                continue
            has = bool(r["content_head"].strip())
            probe_log.append({"switch": cand, "reasoning_chars": r["reasoning_chars"], "content": has,
                              "content_head": r["content_head"][:80]})
            print(f"[{a.label}] min-thinking probe {cand}: reasoning_chars {r['reasoning_chars']}, content {has}", flush=True)
            if has and (best is None or r["reasoning_chars"] < best[1]):
                best = (cand, r["reasoning_chars"])
        if best is None:
            raise SystemExit(f"[{a.label}] no switch produced an answer ({probe_log}). hint: read the serverlog")
        mode = best[0]
        print(f"[{a.label}] min-thinking: using {mode} (probe reasoning_chars {best[1]})", flush=True)
    if mode == "auto-off":
        mode = None
        for cand in ("effort0", "effort-none-kwargs", "kwargs", "top"):
            try:
                r = ask(a.base, model, "In one sentence, what is a spreadsheet?", 128, cand, a.timeout)
                ok = r["reasoning_chars"] == 0 and bool(r["content_head"].strip())
                probe_log.append({"switch": cand, "ok": ok, "reasoning_chars": r["reasoning_chars"],
                                  "content_head": r["content_head"][:80]})
                print(f"[{a.label}] thinking-off probe {cand}: reasoning_chars {r['reasoning_chars']}, "
                      f"content {r['content_head'][:60]!r} -> {'OK' if ok else 'no'}", flush=True)
            except RuntimeError as e:
                probe_log.append({"switch": cand, "ok": False, "error": str(e)[:200]})
                print(f"[{a.label}] thinking-off probe {cand}: error {str(e)[:120]}", flush=True)
                continue
            if ok:
                mode = cand
                break
        if mode is None:
            raise SystemExit(f"[{a.label}] no switch turned thinking off ({probe_log}). "
                             "hint: report this arm as 'thinking cannot be disabled'; do not measure it as thinking-off")
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
        r = ask(a.base, model, p["text"], mt, mode, a.timeout)
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
    # Spread beside the medians (2026-11-25, E179: a 7.6% "regression" was one request against one request, while
    # repeats of one prompt varied ~15% under speculative decoding). Compare setups on `spread`, never a lone median.
    def spread(prompt: str, key: str) -> dict:
        v = [r[key] for r in rows if r["prompt"] == prompt and r[key] is not None]
        if not v:
            return {"n": 0}
        mean = statistics.mean(v)
        return {"n": len(v), "mean": round(mean, 2), "min": round(min(v), 2), "max": round(max(v), 2),
                "range_pct_of_mean": round(100 * (max(v) - min(v)) / mean, 1) if mean else None}

    spreads = {p: {k: spread(p, k) for k in ("prefill_tps", "decode_tps", "ttft_s")} for p in ("P8K", "P32K", "D1500")}
    for p, ks in spreads.items():
        if ks["decode_tps"].get("n") == 1:
            print(f"[{a.label}] NOTE {p}: one request only - it cannot show a difference smaller than the spread "
                  f"between repeats; do not compare setups on it", flush=True)
    out = {
        "label": a.label,
        "base": a.base,
        "model": model,
        "thinking_off": a.thinking_off,
        "thinking_off_switch_used": mode,
        "thinking_off_probe": probe_log,
        "requests_with_reasoning": sum(1 for r in rows if r["reasoning_chars"]),
        "prompts_file": a.prompts,
        "summary": summary,
        "spread": spreads,
        "requests": rows,
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps({"label": a.label, "summary": summary}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
