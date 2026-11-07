#!/usr/bin/env python3
# File: validate_expert_tasks_v2.py
# Purpose: Prove every v2 expert task is SOLVABLE and DISCRIMINATING before it scores any model.
# Project: sparkbench | Date: 2026-09-06
#
# Overview: Same contract as validate_expert_tasks.py. A task is evidence only
# if a correct solution PASSES (else it scores everything zero and reads as
# "the models failed") and a plausible wrong solution FAILS (else it
# discriminates nothing and inflates every score). Each naive solution below
# names the specific corner it misses, so a naive arm that unexpectedly passes
# tells you which assertion is missing rather than only that something is off.
#
# Run: python3 tools/validate_expert_tasks_v2.py   (exit 0 = bank is usable)

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "coding-eval"))
from expert_tasks_v2 import EXPERT_TASKS_V2  # noqa: E402

REFERENCE: dict[str, str] = {
"semver_cmp": '''
def _key(v):
    core, _, rest = v.partition("+")
    core, _, pre = core.partition("-")
    nums = [int(x) for x in core.split(".")]
    return nums, pre

def _cmp_pre(a, b):
    if a == b:
        return 0
    if a == "":
        return 1
    if b == "":
        return -1
    ai, bi = a.split("."), b.split(".")
    for x, y in zip(ai, bi):
        xd, yd = x.isdigit(), y.isdigit()
        if xd and yd:
            if int(x) != int(y):
                return -1 if int(x) < int(y) else 1
        elif xd != yd:
            return -1 if xd else 1
        elif x != y:
            return -1 if x < y else 1
    if len(ai) == len(bi):
        return 0
    return -1 if len(ai) < len(bi) else 1

def semver_cmp(a, b):
    na, pa = _key(a)
    nb, pb = _key(b)
    if na != nb:
        return -1 if na < nb else 1
    return _cmp_pre(pa, pb)
''',
"txn_update": '''
def txn_update(store, ops):
    snapshot = dict(store)
    for op in ops:
        kind = op[0]
        if kind == "set":
            store[op[1]] = op[2]
        elif kind == "incr":
            if op[1] not in store or store[op[1]] + op[2] < 0:
                store.clear(); store.update(snapshot); return False
            store[op[1]] += op[2]
        elif kind == "del":
            if op[1] not in store:
                store.clear(); store.update(snapshot); return False
            del store[op[1]]
        else:
            store.clear(); store.update(snapshot); return False
    return True
''',
"topo_stable": '''
import heapq

def topo_stable(nodes, edges):
    nodes = list(nodes)
    indeg = {n: 0 for n in nodes}
    adj = {n: [] for n in nodes}
    for a, b in edges:
        adj[a].append(b)
        indeg[b] += 1
    heap = sorted(n for n in nodes if indeg[n] == 0)
    heapq.heapify(heap)
    out = []
    while heap:
        n = heapq.heappop(heap)
        out.append(n)
        for m in sorted(adj[n]):
            indeg[m] -= 1
            if indeg[m] == 0:
                heapq.heappush(heap, m)
    if len(out) != len(nodes):
        raise ValueError("cycle")
    return out
''',
"ttl_cache": '''
class TTLCache:
    def __init__(self, capacity, ttl):
        self.capacity = capacity
        self.ttl = ttl
        self.data = {}      # key -> (value, set_time)
        self.order = []     # least recently used first

    def _purge(self, now):
        dead = [k for k, (_, t) in self.data.items() if now - t >= self.ttl]
        for k in dead:
            del self.data[k]
            if k in self.order:
                self.order.remove(k)

    def _touch(self, key):
        if key in self.order:
            self.order.remove(key)
        self.order.append(key)

    def set(self, key, value, now):
        self._purge(now)
        self.data[key] = (value, now)
        self._touch(key)
        while len(self.data) > self.capacity:
            lru = self.order.pop(0)
            self.data.pop(lru, None)

    def get(self, key, now):
        self._purge(now)
        if key not in self.data:
            return None
        self._touch(key)
        return self.data[key][0]

    def size(self, now):
        self._purge(now)
        return len(self.data)
''',
"interval_cover": """
def interval_cover(target, intervals):
    start, end = target
    iv = sorted(intervals)
    n, i, cur, count, best = len(iv), 0, start, 0, start
    while cur < end:
        while i < n and iv[i][0] <= cur:
            if iv[i][1] > best:
                best = iv[i][1]
            i += 1
        if best <= cur:
            return -1
        cur = best
        count += 1
    return count
""",
"round_half_even": """
from decimal import Decimal, ROUND_HALF_EVEN, getcontext

getcontext().prec = 200   # default 28 is too small for the long-input cases

def round_half_even(value, places):
    q = Decimal(1).scaleb(-places)
    r = Decimal(value).quantize(q, rounding=ROUND_HALF_EVEN)
    if r == 0:
        r = abs(r)
    s = format(r, "f")
    if places == 0 and "." in s:
        s = s.split(".")[0]
    return s
""",
"stream_dedupe": """
from collections import deque

def stream_dedupe(items, window):
    seen = deque()
    inwin = set()
    for x in items:
        if window and x in inwin:
            continue
        yield x
        if window:
            seen.append(x)
            inwin.add(x)
            if len(seen) > window:
                inwin.discard(seen.popleft())
""",
}

# Each naive solution names the ONE corner it misses.
NAIVE: dict[str, list[tuple[str, str]]] = {
"semver_cmp": [("compares prerelease as plain strings and ignores the release-is-higher rule", '''
def semver_cmp(a, b):
    a = a.split("+")[0]; b = b.split("+")[0]
    if a == b:
        return 0
    return -1 if a < b else 1
''')],
"txn_update": [("applies in place with no rollback, so a mid-sequence failure leaves partial state", '''
def txn_update(store, ops):
    for op in ops:
        kind = op[0]
        if kind == "set":
            store[op[1]] = op[2]
        elif kind == "incr":
            if op[1] not in store or store[op[1]] + op[2] < 0:
                return False
            store[op[1]] += op[2]
        elif kind == "del":
            if op[1] not in store:
                return False
            del store[op[1]]
    return True
''')],
"topo_stable": [("returns ANY valid topological order - a plain queue, not a heap", '''
from collections import deque

def topo_stable(nodes, edges):
    indeg = {n: 0 for n in nodes}
    adj = {n: [] for n in nodes}
    for a, b in edges:
        adj[a].append(b); indeg[b] += 1
    q = deque(n for n in nodes if indeg[n] == 0)
    out = []
    while q:
        n = q.popleft(); out.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                q.append(m)
    if len(out) != len(nodes):
        raise ValueError("cycle")
    return out
''')],
"ttl_cache": [("evicts for capacity WITHOUT first removing expired entries", '''
class TTLCache:
    def __init__(self, capacity, ttl):
        self.capacity = capacity; self.ttl = ttl
        self.data = {}; self.order = []

    def set(self, key, value, now):
        self.data[key] = (value, now)
        if key in self.order: self.order.remove(key)
        self.order.append(key)
        while len(self.data) > self.capacity:
            lru = self.order.pop(0); self.data.pop(lru, None)

    def get(self, key, now):
        if key not in self.data: return None
        v, t = self.data[key]
        if now - t >= self.ttl:
            del self.data[key]
            if key in self.order: self.order.remove(key)
            return None
        if key in self.order: self.order.remove(key)
        self.order.append(key)
        return v

    def size(self, now):
        return len([k for k, (_, t) in self.data.items() if now - t < self.ttl])
''')],
"interval_cover": [("rescans every interval for each step - correct but quadratic", """
def interval_cover(target, intervals):
    start, end = target
    cur, count = start, 0
    while cur < end:
        best = cur
        for a, b in intervals:
            if a <= cur and b > best:
                best = b
        if best <= cur:
            return -1
        cur = best
        count += 1
    return count
""")],
"round_half_even": [("goes through float, so exactly-half cases and long inputs are wrong", """
def round_half_even(value, places):
    r = round(float(value), places)
    if r == 0:
        r = abs(r)
    if places == 0:
        return str(int(r))
    return ("%%.%df" %% places) %% r
""")],
"stream_dedupe": [("materialises the input into a list, so it is neither lazy nor infinite-safe", """
def stream_dedupe(items, window):
    out = []
    seen = []
    for x in list(items):
        if window and x in seen[-window:]:
            continue
        out.append(x)
        seen.append(x)
    return out
""")],
}


def run(code: str, tests: str, timeout: float = 20.0) -> tuple[bool, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as fh:
        fh.write(code + "\n\n" + tests)
        path = fh.name
    try:
        p = subprocess.run([sys.executable, path], capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode == 0, (p.stderr or p.stdout)[-300:]
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s"
    finally:
        Path(path).unlink(missing_ok=True)


def main() -> int:
    bad = 0
    for task in EXPERT_TASKS_V2:
        tid = task["id"]
        ref = REFERENCE.get(tid)
        if ref is None:
            print(f"{tid:14s} NO REFERENCE - cannot prove the task is solvable")
            bad += 1
            continue
        ok, err = run(ref, task["tests"])
        print(f"{tid:14s} reference {'PASS' if ok else 'FAIL'}"
              + ("" if ok else f"  <- task is broken: {err.strip()[:160]}"))
        if not ok:
            bad += 1
        for why, naive in NAIVE.get(tid, []):
            nok, _ = run(naive, task["tests"])
            # A naive solution PASSING is the failure: the task discriminates nothing.
            print(f"{'':14s} naive {'WEAK TASK - naive PASSED' if nok else 'fails as intended'}"
                  f"  ({why})")
            if nok:
                bad += 1
        if not NAIVE.get(tid):
            print(f"{'':14s} NO NAIVE ARM - discrimination unproven")
            bad += 1
    print()
    if bad:
        print(f"{bad} problem(s). The bank is NOT usable - a task that everything "
              f"passes discriminates nothing, and a task nothing passes is broken.")
        return 1
    print(f"all {len(EXPERT_TASKS_V2)} tasks solvable AND discriminating. Bank usable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
