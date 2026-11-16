#!/usr/bin/env python3
# File: tools/e163_smoke.py
# Purpose: E163 transport smoke - learn which request shapes an engine accepts before any scored prompt is sent.
# Project: sparkbench | Date: 2026-11-16
#
# Overview: Unscored. Sends only "Reply with OK", "What is 2+2?" and a one-tool weather call, in the shapes the E160
# suites use: no `model` field (run_kw_eval), model "x" (tooluse_harness_v2, run_h6_date_arm), the served id, Halogen's
# id; /tokenize with {"content"} only (run_kw_eval's preflight); reasoning_effort low/medium/xhigh; thinking off by
# both spellings; a streamed request with stream_options.include_usage. Every probe's HTTP status and a short body go
# to stdout as JSON lines, so a rejection is recorded, not raised. Prereg results/e163-prereg.md ("Smoke").

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def call(
    base: str, path: str, body: dict | None, timeout: float = 1800.0
) -> tuple[int, str]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(
        f"{base}{path}", data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode(errors="replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E163 transport smoke (unscored).",
        epilog="example: tools/e163_smoke.py --base http://127.0.0.1:8154",
    )
    ap.add_argument("--base", default="http://127.0.0.1:8154")
    a = ap.parse_args()
    st, models = call(a.base, "/v1/models", None)
    print(
        json.dumps({"probe": "models", "status": st, "body": models[:3000]}), flush=True
    )
    mid = json.loads(models)["data"][0]["id"]
    ok = [{"role": "user", "content": "Reply with OK"}]
    sum_ = [{"role": "user", "content": "What is 2+2? Answer with the number."}]
    probes = {
        "served_id": {
            "model": mid,
            "messages": ok,
            "max_tokens": 32,
            "enable_thinking": False,
        },
        "no_model": {"messages": ok, "max_tokens": 32, "enable_thinking": False},
        "model_x": {
            "model": "x",
            "messages": ok,
            "max_tokens": 32,
            "enable_thinking": False,
        },
        "model_halogen": {
            "model": "halogen-qwen3.8-flash-next",
            "messages": ok,
            "max_tokens": 32,
            "enable_thinking": False,
        },
        "kwargs_off": {
            "model": mid,
            "messages": ok,
            "max_tokens": 32,
            "chat_template_kwargs": {"enable_thinking": False},
        },
        "effort_low": {
            "model": mid,
            "messages": sum_,
            "max_tokens": 2048,
            "reasoning_effort": "low",
            "temperature": 0,
        },
        "effort_medium": {
            "model": mid,
            "messages": sum_,
            "max_tokens": 2048,
            "reasoning_effort": "medium",
            "temperature": 0,
        },
        "effort_xhigh": {
            "model": mid,
            "messages": sum_,
            "max_tokens": 4096,
            "reasoning_effort": "xhigh",
            "temperature": 0,
        },
        "no_effort": {
            "model": mid,
            "messages": sum_,
            "max_tokens": 4096,
            "temperature": 0,
        },
        "tool": {
            "model": mid,
            "temperature": 0,
            "max_tokens": 2048,
            "reasoning_effort": "low",
            "messages": [
                {
                    "role": "user",
                    "content": "What is the weather in Dublin? Use the tool.",
                }
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": "get_weather",
                        "description": "Current weather for a city",
                        "parameters": {
                            "type": "object",
                            "properties": {"city": {"type": "string"}},
                            "required": ["city"],
                        },
                    },
                }
            ],
        },
    }
    for name, body in probes.items():
        st, txt = call(a.base, "/v1/chat/completions", body)
        print(json.dumps({"probe": name, "status": st, "body": txt[:1500]}), flush=True)
    st, txt = call(a.base, "/tokenize", {"content": "Reply with OK"})
    print(
        json.dumps({"probe": "tokenize_content_only", "status": st, "body": txt[:400]}),
        flush=True,
    )
    st, txt = call(a.base, "/tokenize", {"model": mid, "content": "Reply with OK"})
    print(
        json.dumps({"probe": "tokenize_with_model", "status": st, "body": txt[:400]}),
        flush=True,
    )
    req = urllib.request.Request(
        f"{a.base}/v1/chat/completions",
        data=json.dumps(
            {
                "model": mid,
                "messages": ok,
                "max_tokens": 32,
                "enable_thinking": False,
                "stream": True,
                "stream_options": {"include_usage": True},
            }
        ).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            lines = [ln.decode(errors="replace").strip() for ln in r if ln.strip()]
        print(
            json.dumps(
                {"probe": "stream_usage", "status": 200, "last_lines": lines[-3:]}
            ),
            flush=True,
        )
    except urllib.error.HTTPError as e:
        print(
            json.dumps(
                {
                    "probe": "stream_usage",
                    "status": e.code,
                    "body": e.read().decode()[:400],
                }
            ),
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
