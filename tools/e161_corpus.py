# File: tools/e161_corpus.py
# Purpose: Build E161's three routing-skew corpora (code, docs, prose) as plain text for llama-imatrix.
# Project: sparkbench | Date: 2026-11-15
#
# Overview: code = E159 HFL agent transcripts in order (the model's responses and tool-call arguments, plus the tool
# results it read, which are real source files); docs = the real lab documents listed in spikes/kw-eval/kw_corpus.py
# DOCS; prose = Flash-Next's own E160 KFL and KX answers (amendment 1) (every string field named output/response/answer/content over 40
# characters, recursively). Writes results/e161/corpus/<name>.txt (gitignored: code quotes private repositories) and
# prints character counts. imatrix's --chunks fixes the token count, so each corpus only has to be long enough;
# a corpus under MIN_CHARS raises, because imatrix would silently run fewer chunks than the prereg states.
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/e161/corpus"
# 61,440 tokens at a conservative 2.5 chars/token for code-heavy text; the real check is imatrix's own chunk count.
MIN_CHARS = 160_000
# Amendment 1: prose is short by nature of its source; it runs at the chunks it has (recorded), floor 40,000 chars.
MIN_CHARS_BY = {"prose": 40_000}
PROSE_KEYS = {"output", "response", "answer", "content"}


def code_corpus() -> str:
    parts: list[str] = []
    files = sorted((ROOT / "results/e159/transcripts/HFL").glob("*.json"))
    if not files:
        raise FileNotFoundError(
            "no E159 HFL transcripts. hint: they are gitignored and live only on benchhost under results/e159/transcripts/HFL"
        )
    for f in files:
        for ev in json.loads(f.read_text())["transcript"]:
            if ev["type"] == "model_response":
                if ev["content"] != "(no text)":
                    parts.append(ev["content"])
            elif ev["type"] == "tool_call":
                parts.append(ev["args"])
                parts.append(ev["result"])
    return "\n\n".join(parts)


def docs_corpus() -> str:
    sys.path.insert(0, str(ROOT / "spikes/kw-eval"))
    import kw_corpus  # noqa: PLC0415 - path set above

    return "\n\n".join((ROOT / path).read_text() for _, path in kw_corpus.DOCS)


def _strings(node: object, out: list[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if k in PROSE_KEYS and isinstance(v, str) and len(v) > 40:
                out.append(v)
            else:
                _strings(v, out)
    elif isinstance(node, list):
        for v in node:
            _strings(v, out)


def prose_corpus() -> str:
    out: list[str] = []
    # Amendment 1 (before any run): KFL alone is 33,827 chars, so KX (same model, maximum effort) is added.
    for arm in ("KFL", "KX"):
        for f in sorted((ROOT / "results/e160/raw" / arm).glob("*.json")):
            _strings(json.loads(f.read_text()), out)
    return "\n\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, epilog="example: python3 tools/e161_corpus.py"
    )
    ap.add_argument(
        "--dry-run", action="store_true", help="print sizes, write nothing"
    )
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in (
        ("code", code_corpus),
        ("docs", docs_corpus),
        ("prose", prose_corpus),
    ):
        text = fn()
        print(f"{name}: {len(text):,} chars", flush=True)
        floor = MIN_CHARS_BY.get(name, MIN_CHARS)
        if len(text) < floor:
            raise SystemExit(
                f"{name} corpus is {len(text):,} chars, under {floor:,}. "
                "hint: imatrix would run fewer than the prereg's 120 chunks; widen the source and declare it as an amendment"
            )
        if not args.dry_run:
            (OUT / f"{name}.txt").write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
