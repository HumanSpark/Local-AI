#!/usr/bin/env python3
# File: tools/strip_task_transcripts.py
# Purpose: Split coding-harness task files into a committable scoring record and a full copy kept on disk.
# Project: sparkbench | Date: 2026-11-05
#
# Overview: The full task file (agent transcript + final diff) quotes the repo code the agent read, and that trips the
# pre-commit secret gate on false positives (a keyword argument passing a password variable, vault key NAMES). Evidence is
# never redacted and the gate is never bypassed, so: copy each full file byte-for-byte to <transcripts>/<name>, verify the
# copy, then rewrite the record in <raw> without `transcript`/`diff`, adding length_stops, transcript_entries, diff_chars,
# transcript_file and transcript_sha256. Idempotent: a record already stripped is re-derived from its kept copy.
# Used by tools/capability_index.sh and by hand for E154's local arms. The scorers read length_stops from the record.

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path


def strip_dir(raw: Path, keep: Path) -> int:
    if not raw.is_dir():
        raise SystemExit(f"{raw} is not a directory. hint: pass the per-arm raw directory, e.g. results/e154/raw/Q")
    keep.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(raw.glob("*-*.json")):
        r = json.loads(f.read_text())
        full = keep / f.name
        if "transcript" in r:
            shutil.copy2(f, full)
            if full.read_bytes() != f.read_bytes():
                raise SystemExit(f"copy of {f} does not match. hint: check free space on {keep}; nothing was stripped")
        elif not full.exists():
            raise SystemExit(f"{f} has no transcript and no kept copy at {full}. hint: the full file was lost; re-run the task")
        full_r = json.loads(full.read_text())
        t = full_r["transcript"]
        r.pop("transcript", None)
        r.pop("diff", None)
        r["length_stops"] = sum(1 for e in t if e.get("finish_reason") == "length")
        r["transcript_entries"] = len(t)
        r["diff_chars"] = len(full_r.get("diff") or "")
        r["transcript_file"] = str(full)
        r["transcript_sha256"] = hashlib.sha256(full.read_bytes()).hexdigest()
        f.write_text(json.dumps(r, indent=1))
        n += 1
        print(f"{f.name}: {r['status']}, {r['transcript_entries']} transcript entries kept in {full}", flush=True)
    return n


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Strip transcripts/diffs from harness task files, keeping verified full copies on disk.",
        epilog="Example: tools/strip_task_transcripts.py results/e154/raw/Q results/e154/transcripts/Q",
    )
    ap.add_argument("raw", type=Path, help="per-arm directory of task JSON files (rewritten in place)")
    ap.add_argument("keep", type=Path, help="directory for the full copies (must be gitignored)")
    args = ap.parse_args()
    n = strip_dir(args.raw, args.keep)
    print(f"{n} task files processed", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
