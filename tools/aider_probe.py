# File: tools/aider_probe.py
# Purpose: Recording pass-through proxy in front of the production llama-server, so an
#          Aider session's real first-turn latency and token counts can be measured.
# Project: sparkbench | Date: 2026-08-30
#
# Overview: Aider talks to an OpenAI-compatible endpoint through litellm, which hides the
# wire. This proxy sits between them and records, per request: wall time to the FIRST
# streamed byte (that is the user-visible first-turn latency), total wall, and llama.cpp's
# own prompt/predicted token counts and millisecond timings when the server reports them.
# It forwards bytes unmodified in both directions and adds no buffering, so the numbers it
# writes are the numbers Aider experienced. One JSON object per request, appended to
# --log. It never records prompt or completion TEXT (sparkrouter charter invariant 7).
#
# Data flow: aider -> litellm -> :8499 (this) -> :8400 llama-server -> back, streamed.
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

_LOG_LOCK = threading.Lock()


class _Handler(BaseHTTPRequestHandler):
    upstream: str = "http://127.0.0.1:8400"
    log_path: Path = Path("aider_probe.jsonl")
    timeout_s: float = 900.0

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        """Silence the default stderr access log; this proxy has its own record."""

    def _record(self, row: dict[str, Any]) -> None:
        with _LOG_LOCK:
            with self.log_path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")

    def _relay(self, method: str) -> None:
        body = b""
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            body = self.rfile.read(length)

        # Prompt/completion TEXT is never logged. Only shape.
        n_messages = None
        stream = None
        if body:
            try:
                payload = json.loads(body)
                msgs = payload.get("messages")
                if isinstance(msgs, list):
                    n_messages = len(msgs)
                stream = bool(payload.get("stream"))
            except (ValueError, AttributeError):
                pass  # a non-JSON body is legitimate here; shape fields stay None

        req = urllib.request.Request(
            self.upstream + self.path, data=body or None, method=method
        )
        for k, v in self.headers.items():
            if k.lower() in ("host", "content-length", "connection", "accept-encoding"):
                continue
            req.add_header(k, v)

        t0 = time.monotonic()
        t_first: float | None = None
        n_chunks = 0
        total_bytes = 0
        tail = b""
        row: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "path": self.path,
            "method": method,
            "n_messages": n_messages,
            "stream": stream,
            "request_bytes": len(body),
        }

        try:
            resp = urllib.request.urlopen(req, timeout=self.timeout_s)
        except urllib.error.HTTPError as e:
            row.update(status=e.code, error="HTTPError", wall_s=round(time.monotonic() - t0, 4))
            self._record(row)
            payload = e.read()
            self.send_response(e.code)
            self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        except Exception as e:  # noqa: BLE001 - top-level relay boundary; recorded then re-signalled
            row.update(status=None, error=f"{type(e).__name__}: {e}",
                       wall_s=round(time.monotonic() - t0, 4))
            self._record(row)
            self.send_error(502, f"upstream: {type(e).__name__}")
            return

        with resp:
            self.send_response(resp.status)
            for k, v in resp.headers.items():
                if k.lower() in ("transfer-encoding", "connection", "content-length"):
                    continue
                self.send_header(k, v)
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            while True:
                chunk = resp.read1(65536) if hasattr(resp, "read1") else resp.read(65536)
                if not chunk:
                    break
                if t_first is None:
                    t_first = time.monotonic() - t0
                n_chunks += 1
                total_bytes += len(chunk)
                tail = (tail + chunk)[-16384:]
                self.wfile.write(f"{len(chunk):X}\r\n".encode())
                self.wfile.write(chunk)
                self.wfile.write(b"\r\n")
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
            self.wfile.flush()

        row.update(
            status=resp.status,
            ttfb_s=round(t_first, 4) if t_first is not None else None,
            wall_s=round(time.monotonic() - t0, 4),
            chunks=n_chunks,
            response_bytes=total_bytes,
        )
        row.update(_extract_metrics(tail))
        self._record(row)

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler naming
        self._relay("POST")

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler naming
        self._relay("GET")


def _extract_metrics(tail: bytes) -> dict[str, Any]:
    """Pull llama.cpp's own token counts and timings out of the response tail.

    Both the non-streamed body and the final SSE frames carry `usage` and, on
    llama.cpp, a `timings` object. Absence is expected on some routes, so these
    keys are optional by design - the caller branches on their presence.
    """
    out: dict[str, Any] = {}
    text = tail.decode("utf-8", errors="replace")
    for frag in reversed(text.split("data: ")):
        frag = frag.strip()
        if not frag or frag == "[DONE]":
            continue
        try:
            obj = json.loads(frag)
        except ValueError:
            continue
        usage = obj.get("usage")
        if isinstance(usage, dict):
            out.setdefault("prompt_tokens", usage.get("prompt_tokens"))
            out.setdefault("completion_tokens", usage.get("completion_tokens"))
        timings = obj.get("timings")
        if isinstance(timings, dict):
            out.setdefault("prompt_n", timings.get("prompt_n"))
            out.setdefault("prompt_ms", timings.get("prompt_ms"))
            out.setdefault("predicted_n", timings.get("predicted_n"))
            out.setdefault("predicted_ms", timings.get("predicted_ms"))
        if out:
            break
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Recording pass-through proxy for measuring an Aider session against "
                    "the production llama-server.",
        epilog="example:\n"
               "  python3 tools/aider_probe.py --port 8499 "
               "--upstream http://127.0.0.1:8400 --log /tmp/run.jsonl",
    )
    p.add_argument("--port", type=int, default=8499, help="local port to listen on")
    p.add_argument("--upstream", default="http://127.0.0.1:8400",
                   help="llama-server base URL to forward to")
    p.add_argument("--log", default="aider_probe.jsonl",
                   help="JSONL file to append one row per request to")
    p.add_argument("--timeout", type=float, default=900.0,
                   help="upstream read timeout in seconds")
    args = p.parse_args(argv)

    _Handler.upstream = args.upstream.rstrip("/")
    _Handler.log_path = Path(args.log)
    _Handler.timeout_s = args.timeout

    srv = ThreadingHTTPServer(("127.0.0.1", args.port), _Handler)
    print(f"aider_probe: 127.0.0.1:{args.port} -> {_Handler.upstream}, "
          f"logging to {_Handler.log_path}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("aider_probe: stopping", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
