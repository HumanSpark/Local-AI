#!/usr/bin/env python3
# File: fake_llama_server.py
# Purpose: A llama-server stand-in that can be told to fail in one named way, so E97 can prove the harness goes red.
# Project: sparkbench | Date: 2026-08-31
#
# Overview: E97 drives tools/run_ps_eval.py END TO END and unmodified. Nothing
# inside the runner is stubbed or monkeypatched, because the seam under test is
# the real one: the runner spawns a server binary, greps its log for offload
# evidence, asks it to tokenize, and posts chat completions to it. This script
# is what it spawns.
#
# IT MUST LOOK ENOUGH LIKE llama-server TO GET PAST THE GATES, or the experiment
# measures the gates refusing a fake rather than the gates refusing a FAULT.
# Two things are load-bearing:
#
#   1. It prints `layer N assigned to device ROCm0` lines to stdout, which the
#      runner redirects to the .serverlog and which assert_full_offload() greps
#      (Rule 3). A fake that skipped them would fail every arm at the offload
#      gate and every fault would look like it went red for the wrong reason.
#   2. It serves /tokenize with a plausible count, because assert_context_fits()
#      refuses to run without one (Rule 11).
#
# It accepts and IGNORES llama-server's whole command line except --port. The
# runner builds that line; this script must not care what is on it.
#
# The fault comes from the E97_FAULT environment variable, never from argv,
# because argv is the runner's to build. `none` is a healthy server and is the
# control - a fault-injection suite with no healthy arm cannot tell a harness
# that goes red correctly from one that goes red at everything.
#
# Usage (the runner does this; you do not):
#   E97_FAULT=truncation fake_llama_server.py -m model.gguf -c 4096 --port 8113

from __future__ import annotations

import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

FAULTS = (
    "none",             # healthy control
    "truncation",       # finish_reason=length, no content
    "malformed",        # 200 OK, body is not the completions shape
    "empty",            # 200 OK, content is the empty string
    "interrupt",        # serves INTERRUPT_AFTER items, then exits the process
    "ctxlimit",         # 400s any prompt over E97_CTX_LIMIT tokens, like a declined task
)

FAULT = os.environ.get("E97_FAULT", "none")
INTERRUPT_AFTER = int(os.environ.get("E97_INTERRUPT_AFTER", "3"))
# Used by the `ctxlimit` fault, which exists so tools/e94/ctx_ceiling.py's binary
# search is exercised against a KNOWN answer before it is pointed at the GPU.
CTX_LIMIT = int(os.environ.get("E97_CTX_LIMIT", "4000"))

# A well-formed answer for the l1 bank's two-line template. Its CONTENT is
# meaningless by design - E97 measures the harness, never a score - but it must
# PARSE, so that the healthy control produces ordinary outcomes rather than
# format errors that would mask a real gap.
GOOD_ANSWER = "ANSWER: 30 days\nCITATION: MSA clause 4.2"

_served = 0
_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    # The runner logs the server's stdout; HTTP request lines would bury the
    # offload evidence the Rule 3 gate greps for.
    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, code: int, payload: dict | str) -> None:
        body = (payload if isinstance(payload, str) else json.dumps(payload)).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.startswith("/health"):
            self._send(200, {"status": "ok"})
        elif self.path.startswith("/props"):
            self._send(200, {"default_generation_settings": {"n_ctx": 16384}})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = {}

        if self.path.startswith("/tokenize"):
            # Whitespace count is a fine proxy: Rule 11 only needs a number that
            # scales with the prompt, and E97 never compares it to anything.
            self._send(200, {"tokens": list(range(len(body.get("content", "").split())))})
            return

        if not self.path.startswith("/v1/chat/completions"):
            self._send(404, {"error": "not found"})
            return

        global _served
        with _lock:
            _served += 1
            n = _served

        if FAULT == "interrupt" and n > INTERRUPT_AFTER:
            # Die the way a real server dies: mid-run, without answering. The
            # socket closes under the client, which is what the runner must cope
            # with. os._exit skips cleanup deliberately - a graceful shutdown
            # would be a different and gentler fault.
            print(f"E97: simulated server death after {INTERRUPT_AFTER} items", flush=True)
            os._exit(9)

        if FAULT == "ctxlimit":
            # Whitespace count is the same proxy /tokenize uses here, so the
            # limit the search discovers is exactly CTX_LIMIT.
            n = len(str(body.get("messages", [{}])[0].get("content", "")).split())
            if n > CTX_LIMIT:
                self._send(400, {"error": {"message":
                                 f"the request exceeds the available context size: "
                                 f"{n} > {CTX_LIMIT}"}})
                return
            self._send(200, _completion(content=GOOD_ANSWER, finish_reason="stop",
                                        completion_tokens=12))
            return

        if FAULT == "malformed":
            # 200 OK and valid JSON, but not the completions shape. This is the
            # realistic version: a proxy or an error envelope returning JSON the
            # client cannot read, rather than a transport failure.
            self._send(200, {"object": "error", "message": "upstream unavailable"})
            return

        if FAULT == "truncation":
            self._send(200, _completion(content="", finish_reason="length",
                                        completion_tokens=4096))
            return

        if FAULT == "empty":
            self._send(200, _completion(content="", finish_reason="stop",
                                        completion_tokens=0))
            return

        self._send(200, _completion(content=GOOD_ANSWER, finish_reason="stop",
                                    completion_tokens=12))


def _completion(content: str, finish_reason: str, completion_tokens: int) -> dict:
    return {
        "id": "chatcmpl-e97",
        "object": "chat.completion",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": content},
            "finish_reason": finish_reason,
        }],
        "usage": {"prompt_tokens": 100, "completion_tokens": completion_tokens,
                  "total_tokens": 100 + completion_tokens},
    }


def main() -> int:
    if FAULT not in FAULTS:
        print(f"unknown E97_FAULT={FAULT!r}. hint: one of {', '.join(FAULTS)}",
              file=sys.stderr)
        return 2

    port = 8113
    argv = sys.argv[1:]
    if "--port" in argv:
        port = int(argv[argv.index("--port") + 1])

    # Rule 3's evidence. Emitted BEFORE binding, because the runner polls
    # /health and starts grepping the log the moment health returns 200.
    for layer in range(48):
        print(f"load_tensors: layer {layer} assigned to device ROCm0", flush=True)
    print(f"E97 fake llama-server: fault={FAULT} port={port}", flush=True)

    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
