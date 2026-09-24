#!/usr/bin/env python3
# File: e139_prompts.py
# Purpose: Build E139's fixed prompt set - real text cut to exact token counts by the model's own tokenizer.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: Concatenates this repo's own long-form docs (real, non-synthetic prose and tables),
# encodes the whole corpus ONCE with halogen's tokenizer.json (Qwen3.8-Flash-Next's), and slices
# NON-OVERLAPPING windows at exact token boundaries: 3 x P32K, 3 x P8K, 1 x D1500. Non-overlap
# matters because both engines cache prompt prefixes - a shared prefix would turn a cold
# prefill into a cache hit. Each window gets the same closing question. The window size is the
# content only; chat-template overhead is recorded later from the server's timings.prompt_n.
# Needs the `tokenizers` package: run with var/ft-venv/bin/python (no system install).
# Output: results/e139/prompts.json, committed so every arm reads byte-identical prompts.

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tokenizers import Tokenizer

ROOT = Path("/home/agent-spark/sparkbench")
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
QUESTION = (
    "\n\n---\n\nIn three sentences, what is the single most important finding in the "
    "text above, and what evidence supports it?"
)
# Template + question overhead is small and recorded from prompt_n; the targets are the
# pre-registered prompt sizes (results/e139-prereg.md, Block 1).
PLAN = [("P32K", 32768, 3), ("P8K", 8192, 3), ("D1500", 1500, 1)]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build E139's exact-token prompt set.",
        epilog="example: var/ft-venv/bin/python tools/e139_prompts.py",
    )
    ap.add_argument("--out", default=str(ROOT / "results/e139/prompts.json"))
    args = ap.parse_args()

    tok = Tokenizer.from_file(str(TOKENIZER))
    text = "\n\n".join((ROOT / p).read_text() for p in CORPUS)
    enc = tok.encode(text, add_special_tokens=False)
    q_tokens = len(tok.encode(QUESTION, add_special_tokens=False).ids)
    need = sum((n - q_tokens) * k for _, n, k in PLAN)
    if len(enc.ids) < need:
        raise SystemExit(
            f"corpus is {len(enc.ids)} tokens, plan needs {need}. "
            f"hint: add another long doc to CORPUS"
        )

    prompts: dict[str, list[dict]] = {}
    pos = 0
    for name, n, k in PLAN:
        body_n = n - q_tokens
        for rep in range(k):
            start_char = enc.offsets[pos][0]
            end_char = enc.offsets[pos + body_n - 1][1]
            body = text[start_char:end_char]
            prompt = body + QUESTION
            # Re-encode the final string: a cut can merge tokens at the join, so the count is
            # measured on what is actually sent, never assumed from the slice.
            n_actual = len(tok.encode(prompt, add_special_tokens=False).ids)
            prompts.setdefault(name, []).append(
                {
                    "rep": rep,
                    "target_tokens": n,
                    "content_tokens": n_actual,
                    "sha256": hashlib.sha256(prompt.encode()).hexdigest()[:16],
                    "text": prompt,
                }
            )
            print(
                f"{name} rep{rep}: {n_actual} tokens (target {n}), corpus tokens {pos}..{pos + body_n}"
            )
            pos += body_n

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "tokenizer": str(TOKENIZER),
                "corpus": CORPUS,
                "corpus_tokens": len(enc.ids),
                "prompts": prompts,
            },
            indent=1,
        )
    )
    print(f"wrote {out} ({pos} of {len(enc.ids)} corpus tokens used)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
