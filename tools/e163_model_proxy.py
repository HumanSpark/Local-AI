#!/usr/bin/env python3
# File: tools/e163_model_proxy.py
# Purpose: E163 amendment 1 - give Loom the `model` field the E160 suites do not send, changing nothing else.
# Project: sparkbench | Date: 2026-11-16
#
# Overview: The 2026-11-16 smoke (results/e163/raw/LM-smoke.jsonl) showed loom-serve rejects a chat request with no
# `model` (400) or model "x" / Halogen's id (404), and /tokenize without `model` (400). run_kw_eval sends no model and
# tokenizes with {"content"} only; the tool-use and H6 runners send "x"; the others send Halogen's id. This proxy listens
# on 127.0.0.1:LISTEN, and for a POST with a JSON object body sets body["model"] to the upstream's served id, then
# forwards to 127.0.0.1:UPSTREAM and streams the response back byte for byte (SSE included), closing the connection
# at the end. GET requests pass through unchanged, except /health, renamed to loom-serve's /healthz. Every other field, the prompt and the response are untouched; the
# number of rewritten requests is printed per request so the log proves what it did.

from __future__ import annotations

import argparse
import http.client
import json
import sys
import threading
import time
from pathlib import Path
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LOG_LOCK = threading.Lock()
HOP = {
    "connection",
    "keep-alive",
    "transfer-encoding",
    "content-length",
    "proxy-connection",
    "upgrade",
    "te",
    "trailer",
}


def make_handler(
    upstream: int, model_id: str, log_bodies: Path | None = None
) -> type[BaseHTTPRequestHandler]:
    class H(BaseHTTPRequestHandler):
        protocol_version = (
            "HTTP/1.0"  # close-delimited bodies: no re-chunking of the upstream stream
        )

        def _forward(self, body: bytes | None) -> None:
            conn = http.client.HTTPConnection("127.0.0.1", upstream, timeout=21600)
            headers = {
                k: v for k, v in self.headers.items() if k.lower() not in HOP | {"host"}
            }
            if body is not None:
                headers["Content-Length"] = str(len(body))
            conn.request(self.command, self.path, body=body, headers=headers)
            r = conn.getresponse()
            captured: list[bytes] = []
            self.send_response(r.status, r.reason)
            for k, v in r.getheaders():
                if k.lower() not in HOP:
                    self.send_header(k, v)
            self.send_header("Connection", "close")
            self.end_headers()
            while True:
                chunk = r.read1(65536)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
                if log_bodies is not None:
                    captured.append(chunk)
            conn.close()
            if log_bodies is not None and self.command == "POST":
                # Diagnostic transcript (E163 follow-up): the request as forwarded and the raw response, one JSON line.
                rec = {
                    "t": time.time(),
                    "path": self.path,
                    "status": r.status,
                    "request": json.loads(body) if body else None,
                    "response": b"".join(captured).decode(errors="replace"),
                }
                with LOG_LOCK, log_bodies.open("a") as f:
                    f.write(json.dumps(rec) + "\n")

        def do_GET(self) -> None:  # noqa: N802 - http.server API
            # ps-eval, writing and multiturn poll llama-server's /health; loom-serve names it /healthz (2026-11-16,
            # LM l5 failed its 300 s health wait on the first run). Path rename only.
            if self.path == "/health":
                self.path = "/healthz"
                print("mapped GET /health -> /healthz", flush=True)
            self._forward(None)

        def do_POST(self) -> None:  # noqa: N802
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = None
            if isinstance(body, dict):
                old = body.get("model", "<absent>")
                body["model"] = model_id
                raw = json.dumps(body).encode()
                print(
                    f"rewrote model {old!r} -> {model_id!r} on {self.path}", flush=True
                )
            self._forward(raw)

        def log_message(self, *args: object) -> None:
            pass

    return H


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E163 amendment 1: set `model` on requests to loom-serve.",
        epilog="example: tools/e163_model_proxy.py --listen 8163 --upstream 8154",
    )
    ap.add_argument("--listen", type=int, default=8163)
    ap.add_argument("--upstream", type=int, default=8154)
    ap.add_argument(
        "--log-bodies",
        type=Path,
        default=None,
        help="append each POST's forwarded request and raw response as a JSON line (diagnostics only)",
    )
    a = ap.parse_args()
    with urllib.request.urlopen(
        f"http://127.0.0.1:{a.upstream}/v1/models", timeout=30
    ) as r:
        data = json.loads(r.read())["data"]
    if len(data) != 1:
        raise SystemExit(
            f"upstream lists {len(data)} models, expected exactly 1. hint: one deployment per loom-serve"
        )
    model_id = data[0]["id"]
    print(f"proxy 127.0.0.1:{a.listen} -> :{a.upstream}, model {model_id}", flush=True)
    ThreadingHTTPServer(
        ("127.0.0.1", a.listen), make_handler(a.upstream, model_id, a.log_bodies)
    ).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
