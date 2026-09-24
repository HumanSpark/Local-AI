#!/usr/bin/env python3
# File: preflight.py
# Purpose: Pure memory pre-check used by model_swap.sh before starting a second llama-server instance.
# Project: sparkbench | Date: 2026-07-07
#
# Overview: Parses /proc/meminfo for MemAvailable, compares against the
# target model file's size plus a fixed safety margin, and reports whether
# there's room to run both the old and new llama-server instances at once
# (a blue/green swap) or whether model_swap.sh must fall back to
# stop-then-start. Stdlib only, deliberately - runs under the system
# python3 from a bash script, no venv needed for this one file.

from __future__ import annotations

import sys
from pathlib import Path

SAFETY_MARGIN_BYTES = 4 * 1024 ** 3  # headroom for the OS + the second process's non-weight overhead


def mem_available_bytes(meminfo_path: str = "/proc/meminfo") -> int:
    for line in Path(meminfo_path).read_text().splitlines():
        if line.startswith("MemAvailable:"):
            kib = int(line.split()[1])
            return kib * 1024
    raise RuntimeError(f"MemAvailable not found in {meminfo_path}")


def can_run_both(model_path: str, meminfo_path: str = "/proc/meminfo") -> bool:
    model_bytes = Path(model_path).stat().st_size
    return mem_available_bytes(meminfo_path) >= model_bytes + SAFETY_MARGIN_BYTES


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: preflight.py <new-model-path>", file=sys.stderr)
        return 2
    ok = can_run_both(sys.argv[1])
    print("yes" if ok else "no")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
