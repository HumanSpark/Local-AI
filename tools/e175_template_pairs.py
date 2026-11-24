# File: tools/e175_template_pairs.py
# Purpose: Send gbench's four chat-template pair cases to a local OpenAI-compatible server and score each one.
# Project: sparkbench | Date: 2026-11-24
#
# Overview: E175 (results/e175-prereg.md). Loads the case JSONs copied from google-deepmind/gbench @ d3e4283
# (Apache-2.0, results/e175/cases/), POSTs each conversation (with tools/tool_choice where the case has them) to
# http://127.0.0.1:PORT/v1/chat/completions at temperature 0 with thinking off, and scores it with gbench's rule:
# contains_all expected_outputs (case-insensitive substring), none of expected_not_contains, none of the Qwen
# chat-template tokens below. An HTTP error or empty reply is scored "harness-error", never "fail". Writes one JSON
# line per case to --out and prints a summary. Local server only; no cloud calls.
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CASES = (
    "template_tool_response",
    "template_tool_response_twin",
    "template_multi_turn",
    "template_multi_turn_twin",
)
# Qwen3.8 chat-template tokens that must never appear in a visible answer (read from results/e175/templates/stock.jinja).
QWEN_TEMPLATE_TOKENS = (
    "<|im_start|>",
    "<|im_end|>",
    "<|endoftext|>",
    "<tool_call>",
    "</tool_call>",
    "<tool_response>",
    "</tool_response>",
    "<tools>",
    "</tools>",
    "<think>",
    "</think>",
)


def score(text: str, truth: dict) -> tuple[str, list[str]]:
    why = []
    low = text.lower()
    why += [f"missing {e!r}" for e in truth["expected_outputs"] if e.lower() not in low]
    why += [
        f"contains {e!r}"
        for e in truth.get("expected_not_contains", [])
        if e.lower() in low
    ]
    if truth.get("forbid_chat_template_tokens"):
        why += [f"leaked {t!r}" for t in QWEN_TEMPLATE_TOKENS if t in text]
    return ("pass" if not why else "fail"), why


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run gbench's chat-template pair cases against a local server.",
        epilog="example: python3 tools/e175_template_pairs.py --port 8471 --arm stock "
        "--out results/e175/stock.jsonl",
    )
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--arm", required=True, help="label written into each record")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument(
        "--cases",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "results/e175/cases",
    )
    args = ap.parse_args()
    url = f"http://127.0.0.1:{args.port}/v1/chat/completions"
    counts: dict[str, int] = {}
    with open(args.out, "w") as out:
        for cid in CASES:
            case = json.loads((args.cases / f"{cid}.json").read_text())
            body = {
                "messages": case["conversation"]["messages"],
                "temperature": 0,
                "max_tokens": 512,
                "chat_template_kwargs": {"enable_thinking": False},
            }
            if "tools" in case:
                body["tools"] = case["tools"]
                body["tool_choice"] = case["tool_choice"]
            req = urllib.request.Request(
                url, json.dumps(body).encode(), {"Content-Type": "application/json"}
            )
            t0 = time.monotonic()
            rec: dict = {"arm": args.arm, "case": cid}
            try:
                with urllib.request.urlopen(req, timeout=300) as r:
                    resp = json.loads(r.read())
                msg = resp["choices"][0]["message"]
                text = (
                    msg.get("content") or ""
                )  # content may be null when the model calls a tool instead
                rec.update(
                    content=text,
                    tool_calls=msg.get("tool_calls"),
                    finish=resp["choices"][0]["finish_reason"],
                )
                if not text.strip():
                    rec.update(
                        status="harness-error" if not msg.get("tool_calls") else "fail",
                        why=[
                            "empty content"
                            + (
                                " (model called a tool again)"
                                if msg.get("tool_calls")
                                else ""
                            )
                        ],
                    )
                else:
                    rec["status"], rec["why"] = score(text, case["golden_truth"])
            except urllib.error.HTTPError as e:
                rec.update(
                    status="harness-error",
                    why=[f"HTTP {e.code}: {e.read()[:400].decode(errors='replace')}"],
                )
            except (urllib.error.URLError, TimeoutError) as e:
                rec.update(status="harness-error", why=[f"{type(e).__name__}: {e}"])
            rec["wall_s"] = round(time.monotonic() - t0, 2)
            out.write(json.dumps(rec) + "\n")
            out.flush()
            counts[rec["status"]] = counts.get(rec["status"], 0) + 1
            print(
                f"[e175] {args.arm} {cid}: {rec['status']} {rec['why']} ({rec['wall_s']}s)",
                flush=True,
            )
    print(f"[e175] {args.arm} summary {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
