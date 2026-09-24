#!/usr/bin/env python3
# File: relay_traffic_mix.py
# Purpose: Read-only summary of sparkrouter's request log, to answer which model should be RESIDENT rather than which is better.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: The routing guide answers "which model for this job". The relay
# asks a different question - "which model should be LOADED" - and that trades
# on traffic shape, which no benchmark in this repo measures. This reads
# /var/lib/sparkrouter/requests.jsonl and reports the distribution.
#
# NEEDS ELEVATION AND NOTHING ELSE. The runtime directory is mode 750 owned by
# spark-infer; agent-spark is not in that group. This script opens ONE file for
# reading, writes nothing, and starts no service - so the elevation buys a read
# and no other capability.
#
# WHAT THE LOG CAN AND CANNOT SAY. request_log.py records ts, model, n_prompt,
# n_gen, ms_total and tps - metadata only, never content, by design. There is
# no endpoint and no tool-call flag, so this CANNOT label a request "chat" or
# "tool call". What it can do is size it, and size is the discriminator the
# residency decision actually turns on: interactive traffic sits in the
# hundreds-to-low-thousands of prompt tokens and document work sits in the tens
# of thousands. The buckets below are drawn on that boundary and are named for
# what they imply, so nobody has to translate a histogram into a decision.

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

LOG = Path("/var/lib/sparkrouter/requests.jsonl")

# Bucket edges chosen for the DECISION, not for tidy powers of two. The line
# that matters is ~4,000 prompt tokens: below it the workhorse's sub-second
# answer is the whole point, above it F80's 0/8 on walked periods starts to bite.
BUCKETS = [
    (0, 1_000, "tiny - chat, a one-line question, a tool call"),
    (1_000, 4_000, "small - a short document or a few turns"),
    (4_000, 16_000, "medium - a real document, or a long conversation"),
    (16_000, 64_000, "large - a document set; the 27B's territory"),
    (64_000, 10**9, "huge - a folder; only the 27B has been measured here"),
]


def pct(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(q * len(ordered)))
    return ordered[idx]


def main() -> int:
    if not LOG.exists():
        raise SystemExit(
            f"{LOG} does not exist. "
            f"hint: sparkrouter-log.service writes it; if the relay has never "
            f"run since that unit was installed there is genuinely no traffic "
            f"to summarise, which is itself an answer"
        )
    try:
        text = LOG.read_text()
    except PermissionError:
        raise SystemExit(
            f"cannot read {LOG} - it is mode 750 owned by spark-infer. "
            f"hint: run this with sudo, or as spark-infer; it opens one file "
            f"for reading and writes nothing"
        ) from None

    records = []
    malformed = 0
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            # Counted and reported, never silently dropped: a partial write
            # from a killed logger is worth seeing, not smoothing over.
            malformed += 1

    if not records:
        raise SystemExit(
            f"{LOG} has no parseable records ({malformed} malformed lines). "
            f"hint: nothing to decide from - leave residency as it is"
        )

    stamps = sorted(r["ts"] for r in records)
    print(f"sparkrouter request log: {len(records):,} requests")
    print(f"  first  {stamps[0]}")
    print(f"  last   {stamps[-1]}")
    if malformed:
        print(f"  {malformed} malformed line(s) skipped - not counted anywhere below")

    days = len({s[:10] for s in records and stamps})
    print(f"  {days} distinct day(s) with traffic, "
          f"{len(records) / max(days, 1):.1f} requests/day on those days")

    print("\nby model served:")
    for model, n in Counter(r["model"] for r in records).most_common():
        print(f"  {n:6,}  {n / len(records) * 100:5.1f}%  {model}")

    print("\nby PROMPT SIZE - this is the residency decision:")
    print(f"  {'prompt tokens':>16}  {'n':>6} {'share':>7}  "
          f"{'med gen':>7} {'med ms':>8}   what it implies")
    for lo, hi, label in BUCKETS:
        rows = [r for r in records if lo <= r["n_prompt"] < hi]
        if not rows:
            continue
        share = len(rows) / len(records) * 100
        print(f"  {lo:>7,}-{hi if hi < 10**9 else 0:<8,} {len(rows):>6} {share:>6.1f}%  "
              f"{pct([r['n_gen'] for r in rows], 0.5):>7,.0f} "
              f"{pct([r['ms_total'] for r in rows], 0.5):>8,.0f}   {label}")

    prompts = [r["n_prompt"] for r in records]
    big = sum(1 for p in prompts if p >= 4_000)
    print(f"\n  median prompt {pct(prompts, 0.5):,.0f} tokens, "
          f"p90 {pct(prompts, 0.9):,.0f}, max {max(prompts):,}")
    print(f"  {big:,} of {len(records):,} requests ({big / len(records) * 100:.1f}%) "
          f"are >= 4,000 prompt tokens")

    print("\nRead this as: a high tiny/small share argues for keeping the fast "
          "workhorse resident and\nrouting document work to the 27B by name. A "
          "high medium/large share argues the default\nis wrong. It cannot tell "
          "you WHAT the request was - the log holds no content by design.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
