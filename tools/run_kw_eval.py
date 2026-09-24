#!/usr/bin/env python3
# File: tools/run_kw_eval.py
# Purpose: Run one arm over the KA-H1 real-document knowledge-work bank. Records everything, scores nothing.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: KA-H1 asks what share of serious knowledge work can be completed
# locally inside a 30-40 second budget. This executes one arm over the item bank
# in spikes/kw-eval and records the fields that question needs: correctness
# inputs, wall time, TTFT, prompt and generated tokens, measured context size,
# and non-termination.
#
# IT ASSIGNS NO SCORES. Scoring is a separate pass over banked transcripts
# (tools/score_kw_eval.py), so a scoring bug can be fixed and re-run at zero GPU
# cost - which is what saved E67 when its classifier turned out to be inverted.
#
# NO TOOL SCHEMA IS OFFERED. F94: the presence of a tool schema is a large,
# model-specific, non-monotonic variable - the workhorse lost three of twenty on
# a set containing no date question, and lost them as non-termination. An
# instrument that offers tools is measuring the serving config as much as the
# model.
#
# CONTEXT IS PROVEN, NOT ASSUMED (Rule 11). The pack is tokenized by the SERVER
# before any question is sent, and the run refuses to start if prompt plus
# max_tokens does not fit the allocated context. chars/4 understates technical
# text by roughly 40% here, so a preflight built on it would pass a run that
# silently truncates - which is how three of five E10 answers were lost and
# recorded as a capability result (F20).

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "kw-eval"))
from kw_corpus import PACKS, build_pack, pack_docs  # noqa: E402
from kw_items import load_items  # noqa: E402

# The runner is bank-agnostic from 2026-08-20 (E76). `kw` is the E74 bank and is
# the DEFAULT, so every banked E74 result was produced by the same code path
# this flag leaves untouched. `abstain` is the E76 abstention bank, which reuses
# nine of the E74 items verbatim as controls.
BANKS = {"kw": load_items}


def _abstain_loader(pack: str | None = None) -> list[dict[str, Any]]:
    from abstain_items import load_items as _load  # noqa: PLC0415 - optional bank

    return _load(pack)


BANKS["abstain"] = _abstain_loader

SYSTEM = (
    "You are answering questions about the documents supplied below. Answer from "
    "those documents only. If the documents do not settle a question, say so "
    "explicitly rather than guessing. Be specific: give figures, names and dates "
    "exactly as they appear. Keep answers under 200 words."
)


def tokenize(port: int, text: str, timeout: float = 300.0) -> int:
    """Ask the SERVER how long this is. Never chars/4 - see the header."""
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/tokenize",
        data=json.dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return len(json.loads(r.read())["tokens"])


def ask(
    port: int, pack: str, question: str, max_tokens: int, timeout: float
) -> dict[str, Any]:
    """One streaming request. Every failure shape is a RESULT, never an exception."""
    payload = {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"{pack}\n\n=====\n\nQUESTION: {question}"},
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": True,
        # Without this llama-server sends no usage block on a streamed response,
        # so prompt and generated token counts - which the programme requires per
        # item - come back null. Found on the first arm of the first run, before
        # any arm had a comparable figure to lose.
        "stream_options": {"include_usage": True},
    }
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    ttft = None
    text = ""
    reasoning = 0
    finish = None
    usage: dict[str, Any] = {}
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            for raw in r:
                line = raw.decode(errors="replace").strip()
                if not line.startswith("data:"):
                    continue
                body = line[5:].strip()
                if body == "[DONE]":
                    break
                try:
                    d = json.loads(body)
                except json.JSONDecodeError:
                    continue
                if d.get("usage"):
                    usage = d["usage"]
                ch = (d.get("choices") or [{}])[0]
                delta = ch.get("delta") or {}
                piece = delta.get("content") or ""
                think = delta.get("reasoning_content") or ""
                if (piece or think) and ttft is None:
                    ttft = time.time() - t0
                if ch.get("finish_reason"):
                    finish = ch["finish_reason"]
                text += piece
                reasoning += len(think)
    except Exception as exc:  # noqa: BLE001 - transport failure IS a result class (F87)
        return {
            "outcome": "transport_failed",
            "error": f"{type(exc).__name__}: {exc}",
            "answer": text,
            "ttft_s": round(ttft, 2) if ttft else None,
            "wall_s": round(time.time() - t0, 2),
            "reasoning_chars": reasoning,
            "finish_reason": finish,
            "usage": usage,
        }
    return {
        "outcome": "completed",
        "error": None,
        "answer": text,
        "ttft_s": round(ttft, 2) if ttft else None,
        "wall_s": round(time.time() - t0, 2),
        "reasoning_chars": reasoning,
        "finish_reason": finish,
        "usage": usage,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run one arm over the KA-H1 real-document knowledge-work bank.",
        epilog="example: python3 tools/run_kw_eval.py --label qwen38 --pack s "
        "--out results/raw/kw-qwen38-s.json",
    )
    ap.add_argument("--label", required=True, help="arm name, recorded in the results")
    ap.add_argument("--pack", default="s", choices=["s", "m", "l"])
    ap.add_argument("--port", type=int, default=8125)
    ap.add_argument(
        "--ctx",
        type=int,
        required=True,
        help="the -c the server was started with; used for the Rule 11 preflight",
    )
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--items", default=None, help="comma-separated ids")
    ap.add_argument(
        "--item-packs",
        default=None,
        help="which packs' ITEMS to ask, comma-separated (default: the same as "
        "--pack, which is the pre-2026-08-28 behaviour). Use --pack l "
        "--item-packs s,m,l to ask every question against the large context - "
        "the ladder the corpus was built for. Items may only be asked against "
        "their own pack or a larger one.",
    )
    ap.add_argument(
        "--bank",
        default="kw",
        choices=sorted(BANKS),
        help="item bank: kw = the E74 knowledge-work bank (default), "
        "abstain = the E76 abstention bank",
    )
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    items = BANKS[args.bank]()
    # WHICH ITEMS, as distinct from WHICH CONTEXT. The bank tags each item with
    # the pack it is INTRODUCED in, so an exact match asks only the questions the
    # extra documents added - which is why `--pack l` alone asks 2 questions and
    # not 26. The corpus was designed the other way round ("the same material,
    # growing - a question answerable in S must stay answerable in L"), and that
    # ladder cannot be expressed without separating the two. Default is the old
    # behaviour exactly: item pack == context pack.
    want_packs = (
        {s.strip() for s in args.item_packs.split(",")}
        if args.item_packs
        else {args.pack}
    )
    unknown = want_packs - set(PACKS)
    if unknown:
        raise SystemExit(
            f"unknown item pack(s): {sorted(unknown)}\n"
            f"hint: --item-packs takes a comma-separated subset of {sorted(PACKS)}"
        )
    # A question can only be asked against a context that contains its evidence.
    # Packs are prefixes of one ordered list, so pack X's evidence is present in
    # every pack at least as large - and absent from every smaller one. Asking a
    # larger pack's item against a smaller context would score a model wrong for
    # a document it was never shown.
    order = ["s", "m", "l"]
    too_big = {p for p in want_packs if order.index(p) > order.index(args.pack)}
    if too_big:
        raise SystemExit(
            f"--item-packs {sorted(too_big)} cannot be asked against pack "
            f"{args.pack!r}: their evidence is not in that context\n"
            f"hint: items may be asked against their own pack or any LARGER one"
        )
    items = [i for i in items if i["pack"] in want_packs]
    if args.items:
        want = {s.strip() for s in args.items.split(",")}
        items = [i for i in items if i["id"] in want]
    if not items:
        raise SystemExit(
            f"no items for pack {args.pack!r}\n"
            f"hint: pack sizes are s/m/l; check the {args.bank!r} bank in "
            f"spikes/kw-eval/"
        )

    pack = build_pack(args.pack)

    # Rule 11: the context is PROVEN to fit before any arm starts.
    try:
        prompt_tokens = tokenize(args.port, f"{SYSTEM}\n{pack}")
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"could not tokenize the pack via the server: {exc}\n"
            f"hint: is llama-server up on port {args.port}? The preflight is not "
            f"optional - chars/4 understates this corpus and would pass a run "
            f"that silently truncates (F20)"
        ) from exc
    longest_q = max(len(i["question"]) for i in items)
    needed = prompt_tokens + args.max_tokens + 256
    print(
        f"=== KW eval: {args.label}, pack {args.pack} "
        f"({len(pack_docs(args.pack))} docs, {len(pack):,} chars) ==="
    )
    print(f"  measured prompt tokens : {prompt_tokens:,}")
    print(f"  max_tokens             : {args.max_tokens:,}")
    print(f"  needed / allocated     : {needed:,} / {args.ctx:,}")
    if needed > args.ctx:
        raise SystemExit(
            f"CONTEXT PREFLIGHT FAILED: needs {needed:,} of {args.ctx:,}\n"
            f"hint: raise -c on the server, or use a smaller pack. Rule 11 - no "
            f"arm starts until the context is proven to fit"
        )
    print(f"  headroom               : {args.ctx - needed:,} tokens")
    print(
        f"  items                  : {len(items)} (longest question {longest_q} chars)"
    )

    records: list[dict[str, Any]] = []
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "label": args.label,
        "bank": args.bank,
        "pack": args.pack,
        # Recorded so a result file states which questions were asked as well
        # as which context they were asked against. A run that omits it
        # predates 2026-08-28 and asked item pack == context pack.
        "item_packs": sorted(want_packs),
        "pack_chars": len(pack),
        "pack_docs": pack_docs(args.pack),
        "measured_prompt_tokens": prompt_tokens,
        "ctx": args.ctx,
        "max_tokens": args.max_tokens,
        "system": SYSTEM,
        "tools_offered": False,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "kernel": subprocess.run(
            ["uname", "-r"], capture_output=True, text=True
        ).stdout.strip(),
    }
    for n, it in enumerate(items, 1):
        print(f"[{n}/{len(items)}] {it['id']} ({it['category']}) ...", flush=True)
        r = ask(args.port, pack, it["question"], args.max_tokens, args.timeout)
        rec = {
            "id": it["id"],
            "category": it["category"],
            "pack": it["pack"],
            "question": it["question"],
            **r,
            "prompt_tokens": (r.get("usage") or {}).get("prompt_tokens"),
            "completion_tokens": (r.get("usage") or {}).get("completion_tokens"),
            "answer_chars": len(r["answer"]),
            # A run that stops on the token ceiling is TRUNCATED, not wrong. F20
            # recorded three truncated answers as a capability result; this makes
            # the distinction visible in the record rather than in a footnote.
            "hit_token_cap": r.get("finish_reason") == "length",
            "within_30s": r["wall_s"] <= 30,
            "within_40s": r["wall_s"] <= 40,
        }
        records.append(rec)
        print(
            f"    {rec['outcome']} {rec['wall_s']}s ttft={rec['ttft_s']} "
            f"gen={rec['completion_tokens']} cap={rec['hit_token_cap']} "
            f"chars={rec['answer_chars']}",
            flush=True,
        )
        out.write_text(json.dumps({"meta": meta, "records": records}, indent=2))

    n_ok = sum(1 for r in records if r["outcome"] == "completed")
    walls = sorted(r["wall_s"] for r in records if r["outcome"] == "completed")
    med = walls[len(walls) // 2] if walls else None
    print(
        f"\n=== {args.label}/{args.pack}: {n_ok}/{len(records)} completed "
        f"(no scores assigned here) ==="
    )
    print(f"  median wall     : {med}s")
    print(
        f"  within 30s      : {sum(1 for r in records if r['within_30s'])}/{len(records)}"
    )
    print(
        f"  within 40s      : {sum(1 for r in records if r['within_40s'])}/{len(records)}"
    )
    print(f"  hit token cap   : {sum(1 for r in records if r['hit_token_cap'])}")
    print(
        f"  transport failed: {sum(1 for r in records if r['outcome'] != 'completed')}"
    )
    print(f"  written         : {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
