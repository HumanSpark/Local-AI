# File: tools/evict_page_cache.py
# Purpose: Evict the page cache held by files under given paths, without root, and report how much Cached fell.
# Project: sparkbench | Date: 2026-11-23
#
# Overview: E174 A1. bench cannot write /proc/sys/vm/drop_caches, but posix_fadvise(POSIX_FADV_DONTNEED) on a
# file this account can open drops that file's clean cached pages. Walks each path, fadvises every regular file,
# prints progress, then prints Cached (MiB) before/after from /proc/meminfo. Pages still mapped by a running process
# (e.g. flash_serve's mmap) are NOT evicted - stop the server first. Exit 1 if any file could not be opened.
from __future__ import annotations

import argparse
import os
import sys
import time


def cached_mib() -> int:
    with open("/proc/meminfo") as fh:
        for line in fh:
            if line.startswith("Cached:"):
                return int(line.split()[1]) // 1024
    raise RuntimeError("no Cached: line in /proc/meminfo; hint: not a Linux procfs?")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Drop page cache for files under PATHs via posix_fadvise DONTNEED (no root needed).",
        epilog="example: python3 tools/evict_page_cache.py /opt/models/staging",
    )
    ap.add_argument("paths", nargs="+", help="files or directories to evict")
    args = ap.parse_args()
    before = cached_mib()
    t0 = time.monotonic()
    done = failed = 0
    for root in args.paths:
        walk = [(root, [], [""])] if os.path.isfile(root) else os.walk(root)
        for d, _, files in walk:
            for f in files:
                p = os.path.join(d, f) if f else d
                if not os.path.isfile(p) or os.path.islink(p):
                    continue
                try:
                    fd = os.open(p, os.O_RDONLY)
                except OSError as e:
                    print(f"[evict] cannot open {p}: {e}", file=sys.stderr)
                    failed += 1
                    continue
                try:
                    os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
                finally:
                    os.close(fd)
                done += 1
                if done % 200 == 0:
                    print(f"[evict] {done} files, {time.monotonic() - t0:.1f}s", flush=True)
    after = cached_mib()
    print(f"[evict] {done} files fadvised, {failed} unopenable; Cached {before} -> {after} MiB "
          f"({before - after} MiB freed) in {time.monotonic() - t0:.1f}s")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
