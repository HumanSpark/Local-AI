#!/usr/bin/env python3
# File: e153_prompts.py
# Purpose: Build E153's fixed prompt set - E152's exact-token windows and agent turns plus short code, prose and JSON prompts.
# Project: sparkbench | Date: 2026-11-04
#
# Overview: E153 compares five Strix Halo engines on Qwen3.8-Flash-Next through one HTTP client, so
# every engine must receive byte-identical requests. The long-context windows (P8K x3, P32K x3) and
# the six coding-agent turns (AGENT) are copied unchanged from results/e152/prompts.json (exact token
# windows from the Flash-Next tokenizer, distinct starts, so no request can reuse another's prefix
# cache). E152 had no short-prompt generation buckets, and the community claims this experiment
# checks ("60-65 vs 45-55 tok/s", "73 writing code, 54 prose") are about exactly that, so three new
# buckets are added here: CODE x4, PROSE x4, JSON x3. They are fixed strings, written once, hashed.
# Output: results/e153/prompts.json with a sha256 per prompt. No dependencies beyond the stdlib.

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path("/home/bench/sparkbench")
SOURCE = ROOT / "results/e152/prompts.json"

# Each prompt asks for more output than max_tokens allows, so a well-behaved answer runs to the cap
# and every engine is timed over the same number of generated tokens.
CODE = [
    "Write a complete Python module that implements an LRU cache with a maximum byte size (not item "
    "count), thread safety with a single lock, per-entry TTL expiry, and hit/miss statistics. Include "
    "type hints, docstrings and a pytest test file covering eviction order, expiry and concurrency.",
    "Write a Rust command-line program that reads a CSV file of bank transactions (date, description, "
    "amount, currency), groups them by month and currency, and prints a summary table with totals, "
    "counts and the largest single debit. Use the csv and chrono crates, handle malformed rows with a "
    "clear error, and include unit tests.",
    "Write a TypeScript Express server with three endpoints for a todo list (list, create, toggle "
    "done), backed by SQLite through better-sqlite3, with input validation using zod, proper HTTP "
    "status codes, and a Jest test suite using supertest.",
    "Write a Bash script that backs up a list of directories to a remote host with rsync over ssh, "
    "keeps the last seven daily snapshots using hard links, logs each run with timestamps, refuses "
    "to run twice at once using flock, and supports --dry-run and --help.",
]
PROSE = [
    "Write a long, detailed essay for a small-business owner on the practical differences between "
    "running an AI model on their own hardware and paying for a cloud AI service. Cover cost over "
    "three years, privacy, reliability, staff skills and what can go wrong. Use flowing paragraphs.",
    "Write a long short story about a lighthouse keeper on a remote island who discovers that the "
    "supply boat has stopped coming, told over one winter, with vivid description of the weather, "
    "the sea and the keeper's routines.",
    "Explain in depth, for an intelligent reader with no technical background, how a modern "
    "electricity grid keeps supply and demand balanced second by second, and what changes when a "
    "large share of the power comes from wind and solar.",
    "Write a long, detailed history of the bicycle from the 1817 draisine to modern carbon road "
    "bikes, covering the key inventions, the social changes bicycles caused, and why the basic "
    "diamond frame has lasted so long.",
]
JSON_ = [
    "Return only JSON, no prose. Produce an array of 25 fictional customer records for a bakery. Each "
    "record has: id (integer), name, email, city (Irish towns), signup_date (ISO 8601), "
    "favourite_products (array of 1-3 strings), lifetime_spend_eur (number with two decimals), and "
    "notes (one sentence).",
    "Return only JSON, no prose. Produce a JSON object describing a two-week project plan for "
    "migrating a small company's email to a new provider: a 'phases' array, each phase with name, "
    "start_day, end_day, owner_role, tasks (array of objects with title, duration_hours, depends_on) "
    "and risks (array of strings). Include at least five phases.",
    "Return only JSON, no prose. Produce an OpenAPI 3.1 document, in JSON, for a library lending "
    "service with endpoints to search books, view a book, borrow, return and list a member's loans, "
    "with full request and response schemas and error responses.",
]


def entry(name: str, text: str) -> dict:
    return {
        "name": name,
        "messages": [{"role": "user", "content": text}],
        "sha256": hashlib.sha256(text.encode()).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build results/e153/prompts.json from E152's windows plus fixed generation prompts.",
        epilog="example: python3 tools/e153_prompts.py --out results/e153/prompts.json",
    )
    ap.add_argument("--out", default=str(ROOT / "results/e153/prompts.json"))
    args = ap.parse_args()

    src = json.loads(SOURCE.read_text())
    buckets: dict[str, list[dict]] = {}
    for key in ("P8K", "P32K"):
        windows = src["prompts"][key]
        buckets[key] = [
            entry(f"{key}-{i}", w["text"] if isinstance(w, dict) else w)
            for i, w in enumerate(windows)
        ]
    buckets["AGENT"] = [
        {
            "name": f"AGENT-{i}",
            "messages": c["messages"],
            "sha256": c["sha256"],
            "content_tokens": c["content_tokens"],
        }
        for i, c in enumerate(src["code"])
    ]
    buckets["CODE"] = [entry(f"CODE-{i}", t) for i, t in enumerate(CODE)]
    buckets["PROSE"] = [entry(f"PROSE-{i}", t) for i, t in enumerate(PROSE)]
    buckets["JSON"] = [entry(f"JSON-{i}", t) for i, t in enumerate(JSON_)]

    out = {
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "buckets": buckets,
    }
    Path(args.out).write_text(json.dumps(out, indent=1))
    counts = {k: len(v) for k, v in buckets.items()}
    print(f"wrote {args.out}: {counts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
