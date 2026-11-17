#!/usr/bin/env python3
# File: tools/cloud_proxy.py
# Purpose: Let the local-only eval runners call one OpenRouter model, with the vaulted key and a hard USD ceiling.
# Project: sparkbench | Date: 2026-11-17
#
# Overview: The E160 suites (ps-eval, writing, multiturn, tool use v2, H6) talk only to a llama-server-shaped
# endpoint: GET /health and non-streaming POST /v1/chat/completions. This proxy listens on 127.0.0.1:LISTEN and
# answers /health itself; for a chat POST it sets body["model"] to --model, forwards the request otherwise unchanged
# to OpenRouter with the key read from sparkvault (in memory only, never argv or disk), and returns the response.
# Two response edits, both declared: OpenRouter's `reasoning` text is copied to `reasoning_content` (the field the
# runners record), and nothing else changes. Every call is appended to --ledger as one JSON line (tokens, provider-
# reported cost, the request and the response) so the spend and transcripts are auditable. Once the ledger total
# reaches --usd-ceiling, or the token total reaches --token-ceiling, every further chat POST gets HTTP 402 and the
# runner stops loudly. The ledger is re-read at start, so the ceiling holds across restarts and across suites.
# Amendment 1 (E164): /tokenize answers a UTF-8 byte count (an upper bound) and /props answers --ctx, because the
# runners' context preflight needs both and OpenRouter has neither. Streaming is refused (no runner uses it, and its usage arrives in a chunk this proxy would have to parse).

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

OPENROUTER = "https://openrouter.ai/api/v1/chat/completions"
VAULT_GET = "/opt/vault/tools/vault_get.py"
VAULT_KEY = "SPARKBENCH_OPENROUTER_API_KEY"
RETRY_STATUS = {429, 502, 503, 504}
LOCK = threading.Lock()


def read_key() -> str:
    r = subprocess.run(
        ["python3", VAULT_GET, VAULT_KEY], capture_output=True, text=True, timeout=60
    )
    if r.returncode != 0 or not r.stdout:
        raise RuntimeError(
            f"vault_get.py {VAULT_KEY} failed (rc={r.returncode}). "
            "hint: check this account is a sops recipient of the sparkbench app file"
        )
    return r.stdout


def ledger_totals(ledger: Path) -> tuple[float, int]:
    usd, tok = 0.0, 0
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            rec = json.loads(line)
            usd += rec["cost_usd"]
            tok += rec["prompt_tokens"] + rec["completion_tokens"]
    return usd, tok


def make_handler(
    args: argparse.Namespace, key: str, state: dict
) -> type[BaseHTTPRequestHandler]:
    class H(BaseHTTPRequestHandler):
        def _reply(self, status: int, obj: dict) -> None:
            data = json.dumps(obj).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:  # noqa: N802 - http.server API
            if self.path == "/health":
                self._reply(
                    200, {"status": "ok", "proxy": "cloud_proxy", "model": args.model}
                )
            elif self.path == "/props":
                # E164 amendment 1: runners attached by URL ask the server's -c. Report --ctx (set BELOW the
                # model's real window), so the preflight can only be stricter than reality.
                self._reply(
                    200,
                    {
                        "default_generation_settings": {"n_ctx": args.ctx},
                        "proxy": "cloud_proxy",
                    },
                )
            else:
                self._reply(
                    404,
                    {
                        "error": f"cloud_proxy serves only /health on GET, not {self.path}"
                    },
                )

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/tokenize":
                # E164 amendment 1: OpenRouter has no tokenizer endpoint. A byte-level BPE token covers at least
                # one byte, so the UTF-8 byte count is a strict UPPER bound: the context preflight can over-refuse,
                # never pass a prompt that does not fit. The authoritative size is each call's usage.prompt_tokens.
                text = json.loads(self.rfile.read(int(self.headers["Content-Length"])))[
                    "content"
                ]
                n = len(text.encode())
                print(f"tokenize: upper bound {n} (UTF-8 bytes)", flush=True)
                self._reply(200, {"tokens": [0] * n, "upper_bound_from": "utf8_bytes"})
                return
            if self.path != "/v1/chat/completions":
                self._reply(
                    404,
                    {
                        "error": f"cloud_proxy forwards only /v1/chat/completions, not {self.path}"
                    },
                )
                return
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if body.get("stream"):
                self._reply(
                    400,
                    {
                        "error": "cloud_proxy refuses stream=true. hint: no E160 runner streams"
                    },
                )
                return
            with LOCK:
                usd, tok = state["usd"], state["tok"]
            if usd >= args.usd_ceiling or tok >= args.token_ceiling:
                msg = (
                    f"cloud_proxy ceiling reached: ${usd:.4f} of ${args.usd_ceiling}, {tok} of "
                    f"{args.token_ceiling} tokens. hint: raise the ceiling only with the owner's approval"
                )
                print(msg, flush=True)
                self._reply(402, {"error": msg})
                return
            old = body.get("model", "<absent>")
            body["model"] = args.model
            req_bytes = json.dumps(body).encode()
            t0 = time.time()
            status, resp = self._forward(req_bytes)
            wall = time.time() - t0
            if status != 200:
                print(f"upstream HTTP {status}: {json.dumps(resp)[:300]}", flush=True)
                self._reply(status, resp)
                return
            usage = resp["usage"]
            cost = float(
                usage["cost"]
            )  # OpenRouter's billed cost; absent means the accounting is broken - fail
            msg = resp["choices"][0]["message"]
            if msg.get("reasoning") and not msg.get("reasoning_content"):
                msg["reasoning_content"] = msg["reasoning"]
            rec = {
                "t": t0,
                "wall_s": round(wall, 2),
                "model_requested": old,
                "model": args.model,
                "provider": resp.get("provider"),
                "id": resp.get("id"),
                "prompt_tokens": usage["prompt_tokens"],
                "completion_tokens": usage["completion_tokens"],
                "reasoning_tokens": (usage.get("completion_tokens_details") or {}).get(
                    "reasoning_tokens"
                ),
                "cost_usd": cost,
                "finish_reason": resp["choices"][0].get("finish_reason"),
                "request": body,
                "response": resp,
            }
            with LOCK:
                state["usd"] += cost
                state["tok"] += usage["prompt_tokens"] + usage["completion_tokens"]
                state["n"] += 1
                with args.ledger.open("a") as f:
                    f.write(json.dumps(rec) + "\n")
                print(
                    f"call {state['n']}: {usage['prompt_tokens']}+{usage['completion_tokens']} tok, "
                    f"${cost:.4f}, total ${state['usd']:.4f}, {wall:.1f}s, finish {rec['finish_reason']}",
                    flush=True,
                )
            self._reply(200, resp)

        def _forward(self, req_bytes: bytes) -> tuple[int, dict]:
            for attempt in range(4):
                req = urllib.request.Request(
                    OPENROUTER,
                    data=req_bytes,
                    method="POST",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        "X-Title": "sparkbench",
                    },
                )
                try:
                    with urllib.request.urlopen(req, timeout=args.timeout) as r:
                        return 200, json.load(r)
                except urllib.error.HTTPError as e:
                    payload = e.read().decode(errors="replace")
                    if e.code in RETRY_STATUS and attempt < 3:
                        print(
                            f"upstream {e.code}, retry {attempt + 1} in {20 * (attempt + 1)}s",
                            flush=True,
                        )
                        time.sleep(20 * (attempt + 1))
                        continue
                    try:
                        return e.code, json.loads(payload)
                    except json.JSONDecodeError:
                        return e.code, {"error": payload[:2000]}
            raise RuntimeError(
                "unreachable: retry loop exited without a return. hint: bug in _forward"
            )

        def log_message(self, *a: object) -> None:
            pass

    return H


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Local llama-server-shaped proxy to one OpenRouter model, with a hard USD ceiling.",
        epilog="example: tools/cloud_proxy.py --model qwen/qwen4-max --ledger results/e164/raw/ledger.jsonl "
        "--usd-ceiling 5.5",
    )
    ap.add_argument("--listen", type=int, default=8164)
    ap.add_argument(
        "--model", required=True, help="OpenRouter model id every request is pinned to"
    )
    ap.add_argument(
        "--ledger",
        type=Path,
        required=True,
        help="JSONL of every call; its total is the spend",
    )
    ap.add_argument(
        "--usd-ceiling",
        type=float,
        required=True,
        help="refuse calls once the ledger reaches this",
    )
    ap.add_argument(
        "--token-ceiling",
        type=int,
        default=6_000_000,
        help="backstop if cost reporting misbehaves",
    )
    ap.add_argument(
        "--timeout", type=int, default=900, help="seconds per upstream call"
    )
    ap.add_argument(
        "--ctx",
        type=int,
        default=262144,
        help="context reported on /props; keep it at or below the model's real window",
    )
    args = ap.parse_args()
    args.ledger.parent.mkdir(parents=True, exist_ok=True)
    usd, tok = ledger_totals(args.ledger)
    state = {"usd": usd, "tok": tok, "n": 0}
    key = read_key()
    print(
        f"cloud_proxy :{args.listen} -> {args.model}; ledger ${usd:.4f}, {tok} tok; ceiling ${args.usd_ceiling}",
        flush=True,
    )
    ThreadingHTTPServer(
        ("127.0.0.1", args.listen), make_handler(args, key, state)
    ).serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
