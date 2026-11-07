#!/usr/bin/env python3
# File: harness_probe.py
# Purpose: E108's recording proxy - capture what an agentic harness actually SENDS, without a GPU.
# Project: sparkbench | Date: 2026-09-05
#
# Overview: Presents the two endpoints a local-model harness expects - the
# OpenAI-compatible /v1/chat/completions and the Anthropic /v1/messages - plus
# the small discovery endpoints clients probe on startup (/v1/models, /health).
# Every request body is written verbatim to <outdir>/<label>-NNN.json and a
# minimal valid response is returned so the client proceeds far enough to have
# revealed its system prompt and tool schema.
#
# WHY THIS EXISTS: F103-F105 measured a ~60x overhead difference between
# harnesses driving the SAME weights, and the field publishes no such numbers.
# This measures the CLIENT, so it needs no model and no GPU.
#
# THE PRIMARY METRIC IS BYTES, NOT TOKENS, and that is deliberate. F104 located
# the blocker in llama.cpp's grammar builder at roughly 70KB of tool-schema
# JSON. A byte threshold is exact and needs no tokenizer, so it cannot be wrong
# by the ~40% that chars/4 is wrong by on technical text.
#
# Responses are deliberately MINIMAL and non-agentic ("done", stop). A response
# that invited another tool call would measure the harness's second turn, which
# is a different and less interesting number than its floor.

from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STATE = {"outdir": Path("."), "label": "unknown", "n": 0, "started": time.time()}


def _record(path: str, raw: bytes) -> int:
    STATE["n"] += 1
    n = STATE["n"]
    out = STATE["outdir"] / f"{STATE['label']}-{n:03d}.json"
    try:
        body = json.loads(raw.decode("utf-8"))
        parsed = True
    except Exception as exc:  # noqa: BLE001 - a body we cannot parse is still evidence
        body = {"_unparseable": raw.decode("utf-8", "replace")[:20000], "_error": str(exc)}
        parsed = False
    out.write_text(json.dumps({
        "label": STATE["label"], "seq": n, "path": path,
        "t_since_start_s": round(time.time() - STATE["started"], 3),
        "raw_bytes": len(raw), "parsed": parsed, "body": body,
    }, indent=2))
    print(f"  [{n:03d}] {path}  {len(raw):,} bytes  -> {out.name}", flush=True)
    return n


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):  # noqa: A003 - silence the default access log
        pass

    def _send(self, obj: dict, code: int = 200) -> None:
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler's interface
        if self.path.startswith("/health"):
            self._send({"status": "ok"})
        elif self.path.startswith("/v1/models") or self.path.startswith("/models"):
            self._send({"object": "list", "data": [
                {"id": "sparkbench-probe", "object": "model", "owned_by": "sparkbench"}]})
        else:
            self._send({"error": "not found"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        _record(self.path, raw)
        if "messages" in self.path:  # Anthropic Messages API
            self._send({
                "id": "msg_probe", "type": "message", "role": "assistant",
                "model": "sparkbench-probe",
                "content": [{"type": "text", "text": "done"}],
                "stop_reason": "end_turn",
                "usage": {"input_tokens": 1, "output_tokens": 1},
            })
        else:  # OpenAI chat completions
            self._send({
                "id": "chatcmpl-probe", "object": "chat.completion",
                "created": int(time.time()), "model": "sparkbench-probe",
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": "done"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
            })


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Record what an agentic harness sends. No model, no GPU.",
        epilog="example: harness_probe.py --label aider --outdir results/raw/e108")
    ap.add_argument("--label", required=True, help="harness name; prefixes each capture file")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--port", type=int, default=8199)
    a = ap.parse_args()
    STATE["outdir"] = Path(a.outdir)
    STATE["outdir"].mkdir(parents=True, exist_ok=True)
    STATE["label"] = a.label
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    print(f"recording {a.label} on http://127.0.0.1:{a.port} -> {a.outdir}/", flush=True)
    print("  OpenAI:    /v1/chat/completions", flush=True)
    print("  Anthropic: /v1/messages", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print(f"\ncaptured {STATE['n']} request(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
