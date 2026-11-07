#!/usr/bin/env python3
# File: e152_prompts.py
# Purpose: Build E152's fixed prompt set - E139's exact-token windows plus a 100K-context prompt and six coding-agent turns.
# Project: sparkbench | Date: 2026-09-27
#
# Overview: Same method as tools/e139_prompts.py (real repo docs, encoded once with halogen's own
# tokenizer, cut at exact token boundaries) with two additions for the README rows E139 did not test.
# P100K is one 100,000-token window starting at corpus token 60,000 - a start no other window shares,
# so no request can hit another's prefix cache. CODE is six coding-agent turns cut from the MLCommons
# edge-agentic trajectories (real SWE-agent conversations, the vendor's own description of its
# "coding-agent turn" row): for six conversations, the system prompt plus the user/assistant turns up
# to the last point where the context is 1,000-1,800 tokens and the next turn is the assistant's.
# Tool results are carried as user messages; the tools schema is not passed. Output: results/e152/prompts.json.
# Needs the `tokenizers` package: run with var/ft-venv/bin/python.

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path("/home/bench/sparkbench")
TOKENIZER = Path(
    "/opt/models/staging/halogen-qwen3.8-flash-next/tokenizer/tokenizer.json"
)
CORPUS = [
    "docs/FINDINGS.md",
    "docs/PHASE-A-LOG.md",
    "docs/memory-edge-deadlock.md",
    "reports/2026-07-16-local-model-routing-guide.md",
    "docs/w3-audio-audit-report.md",
]
TRAJ = Path(
    "/home/bench/atlas-e146/endpoints/examples/11_Edge_Agentic_Example/agentic_coding_2.5h.jsonl"
)
QUESTION = (
    "\n\n---\n\nIn three sentences, what is the single most important finding in the "
    "text above, and what evidence supports it?"
)
FOLLOWUP = "In two sentences, which experiment number is mentioned most often in the text, and what was it about?"
# E139's windows from token 0 (same sizes, same order), then P100K from a start no window shares.
PLAN = [
    ("P32K", 32768, 3, 0),
    ("P8K", 8192, 3, None),
    ("D1500", 1500, 1, None),
    ("P100K", 100000, 1, 60000),
]
CODE_LO, CODE_HI, CODE_N = 1000, 1800, 6


def window(tok: Tokenizer, text: str, enc, pos: int, body_n: int) -> str:
    start_char = enc.offsets[pos][0]
    end_char = enc.offsets[pos + body_n - 1][1]
    return text[start_char:end_char] + QUESTION


def render(r: dict) -> str:
    # user turns carry `content`; assistant turns carry `tool_calls` (their reasoning is dropped - thinking is
    # off in the measured turn); tool turns carry `tool_results`. Each is rendered as the plain text the model would see.
    if r["role"] == "user":
        return r["content"]
    if r["role"] == "assistant":
        return json.dumps(r["tool_calls"])
    return "\n\n".join(x["content"] for x in r["tool_results"])


def code_turns(tok: Tokenizer) -> list[dict]:
    convs: dict[str, list[dict]] = {}
    with TRAJ.open() as f:
        for line in f:
            r = json.loads(line)
            convs.setdefault(r["conversation_id"], []).append(r)
    out = []
    for cid, recs in convs.items():
        recs = sorted(recs, key=lambda r: int(r["turn"]))
        msgs = [{"role": "system", "content": recs[0]["system"]}]
        n = len(tok.encode(recs[0]["system"], add_special_tokens=False).ids)
        best = None
        for r in recs:
            # the trajectories alternate assistant / tool after the first user turn; tool output is
            # carried as a user message so the chat stays user/assistant and the model's next turn is its own
            role = "user" if r["role"] == "tool" else r["role"]
            if (
                role == "assistant"
                and CODE_LO <= n <= CODE_HI
                and msgs[-1]["role"] == "user"
            ):
                best = (list(msgs), n)
            body = render(r)
            n += len(tok.encode(body, add_special_tokens=False).ids)
            msgs.append({"role": role, "content": body})
            if n > CODE_HI:
                break
        if best:
            m, ntok = best
            out.append(
                {
                    "conversation_id": cid,
                    "content_tokens": ntok,
                    "turns": len(m) - 1,
                    "sha256": hashlib.sha256(json.dumps(m).encode()).hexdigest()[:16],
                    "messages": m,
                }
            )
        if len(out) == CODE_N:
            break
    if len(out) < CODE_N:
        raise SystemExit(
            f"only {len(out)} conversations have a {CODE_LO}-{CODE_HI} token cut before an assistant turn. "
            f"hint: widen CODE_LO/CODE_HI"
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build E152's exact-token prompt set.",
        epilog="example: var/ft-venv/bin/python tools/e152_prompts.py",
    )
    ap.add_argument("--out", default=str(ROOT / "results/e152/prompts.json"))
    args = ap.parse_args()

    tok = Tokenizer.from_file(str(TOKENIZER))
    text = "\n\n".join((ROOT / p).read_text() for p in CORPUS)
    enc = tok.encode(text, add_special_tokens=False)
    q_tokens = len(tok.encode(QUESTION, add_special_tokens=False).ids)

    prompts: dict[str, list[dict]] = {}
    pos = 0
    for name, n, k, start in PLAN:
        if start is not None:
            pos = start
        body_n = n - q_tokens
        for rep in range(k):
            if pos + body_n > len(enc.ids):
                raise SystemExit(
                    f"{name} rep{rep} needs corpus tokens {pos}..{pos + body_n}, corpus has {len(enc.ids)}. "
                    f"hint: add another long doc to CORPUS"
                )
            prompt = window(tok, text, enc, pos, body_n)
            n_actual = len(tok.encode(prompt, add_special_tokens=False).ids)
            prompts.setdefault(name, []).append(
                {
                    "rep": rep,
                    "target_tokens": n,
                    "content_tokens": n_actual,
                    "corpus_start": pos,
                    "sha256": hashlib.sha256(prompt.encode()).hexdigest()[:16],
                    "text": prompt,
                }
            )
            print(
                f"{name} rep{rep}: {n_actual} tokens (target {n}), corpus tokens {pos}..{pos + body_n}"
            )
            pos += body_n
    starts = sorted(p["corpus_start"] for v in prompts.values() for p in v)
    assert len(starts) == len(set(starts)), (
        "two windows share a start: a prefix-cache hit would follow"
    )

    code = code_turns(tok)
    for c in code:
        print(
            f"CODE {c['conversation_id']}: {c['content_tokens']} tokens, {c['turns']} turns"
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "tokenizer": str(TOKENIZER),
                "corpus": CORPUS,
                "corpus_tokens": len(enc.ids),
                "trajectories": str(TRAJ),
                "followup": FOLLOWUP,
                "prompts": prompts,
                "code": code,
            },
            indent=1,
        )
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
