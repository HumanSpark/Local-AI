#!/usr/bin/env python3
# File: validate_expert_tasks_v3.py
# Purpose: Prove every v3 expert task is SOLVABLE, and discriminating against BOTH a naive and a competent-but-wrong solution.
# Project: sparkbench | Date: 2026-09-06
#
# Overview: The v2 validator carried two arms - a reference that must pass and
# a naive solution that must fail. E110 showed that contract admits a saturated
# bank: the incumbent scored 7/7 on tasks every one of which defeated its naive
# arm (F150). A competent model never writes the naive solution.
#
# So this validator requires THREE arms per task, and refuses the bank if any
# is missing:
#   REFERENCE  must PASS  - otherwise the task scores everything zero and reads
#                           as "the models failed" when the task is broken
#   NAIVE      must FAIL  - the old bar, kept
#   SUBTLE     must FAIL  - a solution a good engineer would plausibly write:
#                           correct-looking, idiomatic, wrong on ONE corner
#
# Each arm names the specific corner it misses, so an arm that unexpectedly
# passes tells you WHICH assertion is missing rather than only that something
# is off.
#
# Run: python3 tools/validate_expert_tasks_v3.py   (exit 0 = bank is usable)
#
# NOTE ON WALL CLOCK: two tasks are gated on complexity, so the arms that fail
# them fail by TIMING OUT. A full validation run therefore takes a couple of
# minutes, most of it spent proving that the slow arms are slow.

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "coding-eval"))
from expert_tasks_v3 import EXPERT_TASKS_V3  # noqa: E402

REFERENCE: dict[str, str] = {
"billing_schedule": '''
import calendar, datetime

def billing_schedule(start, n):
    if n < 1:
        raise ValueError("n must be >= 1. hint: there is no zero-period schedule")
    s = datetime.date.fromisoformat(start)
    anchor = s.day
    bounds = [s]
    y, m = s.year, s.month
    for _ in range(n):
        m += 1
        if m == 13:
            m, y = 1, y + 1
        last = calendar.monthrange(y, m)[1]
        bounds.append(datetime.date(y, m, min(anchor, last)))
    return [(bounds[i].isoformat(), bounds[i + 1].isoformat(),
             (bounds[i + 1] - bounds[i]).days) for i in range(n)]
''',
"peak_load": '''
def peak_load(intervals):
    ev = []
    for a, b in intervals:
        if a < b:
            ev.append((a, 1))
            ev.append((b, -1))
    if not ev:
        return (0, -1)
    ev.sort()          # at equal time -1 sorts before +1, which IS the half-open rule
    best, best_t, cur = 0, -1, 0
    for t, d in ev:
        cur += d
        if d == 1 and cur > best:
            best, best_t = cur, t
    return (best, best_t)
''',
"clear_days_deadline": '''
import datetime

def clear_days_deadline(start, n, holidays):
    if n < 1:
        raise ValueError("n must be >= 1. hint: a zero-business-day deadline is not defined")
    hol = set(holidays)
    def business(d):
        return d.weekday() < 5 and d.isoformat() not in hol
    d = datetime.date.fromisoformat(start)
    left = n
    while left:
        d += datetime.timedelta(days=1)
        if business(d):
            left -= 1
    in_vac = (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day == 1)
    if in_vac:
        year = d.year + 1 if d.month == 12 else d.year
        d = datetime.date(year, 1, 2)
        while not business(d):
            d += datetime.timedelta(days=1)
    return d.isoformat()
''',
"window_mode": '''
import heapq

def window_mode(xs, k):
    n = len(xs)
    if k < 1 or k > n:
        raise ValueError("k must satisfy 1 <= k <= len(xs). hint: got k=%r, len=%d" % (k, n))
    cnt = {}
    heap = []
    out = []
    for i, x in enumerate(xs):
        cnt[x] = cnt.get(x, 0) + 1
        heapq.heappush(heap, (-cnt[x], x))
        if i >= k:
            y = xs[i - k]
            cnt[y] -= 1
            if cnt[y]:
                heapq.heappush(heap, (-cnt[y], y))
            else:
                del cnt[y]
        if i >= k - 1:
            while -heap[0][0] != cnt.get(heap[0][1], 0):
                heapq.heappop(heap)
            out.append(heap[0][1])
    return out
''',
}

# Deliberately wrong, in the way a hurried or inexperienced answer is wrong.
NAIVE: dict[str, list[tuple[str, str]]] = {
"billing_schedule": [("advances by 30 days, so it is not monthly at all", '''
import datetime

def billing_schedule(start, n):
    if n < 1:
        raise ValueError("n")
    d = datetime.date.fromisoformat(start)
    out = []
    for _ in range(n):
        e = d + datetime.timedelta(days=30)
        out.append((d.isoformat(), e.isoformat(), 30))
        d = e
    return out
''')],
"peak_load": [("treats the intervals as CLOSED, so touching intervals read as overlapping", '''
def peak_load(intervals):
    iv = [(a, b) for a, b in intervals if a < b]
    if not iv:
        return (0, -1)
    best, best_t = 0, -1
    for a, _ in iv:
        c = sum(1 for x, y in iv if x <= a <= y)
        if c > best or (c == best and a < best_t):
            best, best_t = c, a
    return (best, best_t)
'''),
                ("walks time point by point, which cannot survive 10**9 coordinates", '''
def peak_load(intervals):
    cover = {}
    for a, b in intervals:
        for p in range(a, b):
            cover[p] = cover.get(p, 0) + 1
    if not cover:
        return (0, -1)
    mx = max(cover.values())
    return (mx, min(p for p, c in cover.items() if c == mx))
''')],
"clear_days_deadline": [("counts calendar days and only then nudges off a weekend", '''
import datetime

def clear_days_deadline(start, n, holidays):
    if n < 1:
        raise ValueError("n")
    hol = set(holidays)
    d = datetime.date.fromisoformat(start) + datetime.timedelta(days=n)
    while d.weekday() >= 5 or d.isoformat() in hol:
        d += datetime.timedelta(days=1)
    return d.isoformat()
''')],
"window_mode": [("Counter.most_common breaks ties by insertion order, not by smallest value", '''
from collections import Counter

def window_mode(xs, k):
    if k < 1 or k > len(xs):
        raise ValueError("k")
    return [Counter(xs[i:i + k]).most_common(1)[0][0]
            for i in range(len(xs) - k + 1)]
''')],
}

# The arm that matters. Each of these is what a competent engineer plausibly
# writes: idiomatic, readable, passes a casual review, wrong on ONE corner.
# The corner is sourced from a failure this repo has MEASURED, not imagined.
SUBTLE: dict[str, list[tuple[str, str]]] = {
"billing_schedule": [
    ("ANCHOR DRIFT (F92 shape): re-anchors on the PREVIOUS boundary, so a short "
     "month captures the anchor and 31 Jan -> 28 Feb -> 28 Mar", '''
import calendar, datetime

def billing_schedule(start, n):
    if n < 1:
        raise ValueError("n must be >= 1")
    d = datetime.date.fromisoformat(start)
    bounds = [d]
    for _ in range(n):
        y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
        d = datetime.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))
        bounds.append(d)
    return [(bounds[i].isoformat(), bounds[i + 1].isoformat(),
             (bounds[i + 1] - bounds[i]).days) for i in range(n)]
'''),
    ("counts the period length INCLUSIVELY (F89 shape), off by one on every row", '''
import calendar, datetime

def billing_schedule(start, n):
    if n < 1:
        raise ValueError("n must be >= 1")
    s = datetime.date.fromisoformat(start)
    anchor = s.day
    bounds = [s]
    y, m = s.year, s.month
    for _ in range(n):
        m += 1
        if m == 13:
            m, y = 1, y + 1
        bounds.append(datetime.date(y, m, min(anchor, calendar.monthrange(y, m)[1])))
    return [(bounds[i].isoformat(), bounds[i + 1].isoformat(),
             (bounds[i + 1] - bounds[i]).days + 1) for i in range(n)]
''')],
"peak_load": [
    ("SWEEP SORTED BY TIME ALONE (F89 shape): a stable sort then puts every start "
     "before every end at the same instant, so touching intervals read as overlapping", '''
def peak_load(intervals):
    starts = [(a, 1) for a, b in intervals if a < b]
    ends = [(b, -1) for a, b in intervals if a < b]
    if not starts:
        return (0, -1)
    ev = starts + ends
    ev.sort(key=lambda e: e[0])
    best, best_t, cur = 0, -1, 0
    for t, d in ev:
        cur += d
        if d == 1 and cur > best:
            best, best_t = cur, t
    return (best, best_t)
''')],
"clear_days_deadline": [
    ("ROLLS THE START FORWARD FIRST, then counts n from there - correct whenever "
     "the start is a business day, one day late whenever it is not", '''
import datetime

def clear_days_deadline(start, n, holidays):
    if n < 1:
        raise ValueError("n must be >= 1")
    hol = set(holidays)
    def business(d):
        return d.weekday() < 5 and d.isoformat() not in hol
    d = datetime.date.fromisoformat(start)
    while not business(d):          # normalise to a business day
        d += datetime.timedelta(days=1)
    for _ in range(n):
        d += datetime.timedelta(days=1)
        while not business(d):
            d += datetime.timedelta(days=1)
    if (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day == 1):
        year = d.year + 1 if d.month == 12 else d.year
        d = datetime.date(year, 1, 2)
        while not business(d):
            d += datetime.timedelta(days=1)
    return d.isoformat()
'''),
    ("applies the vacation rule but lands on 2 January unconditionally, without "
     "checking that it is itself a business day", '''
import datetime

def clear_days_deadline(start, n, holidays):
    if n < 1:
        raise ValueError("n must be >= 1")
    hol = set(holidays)
    def business(d):
        return d.weekday() < 5 and d.isoformat() not in hol
    d = datetime.date.fromisoformat(start)
    left = n
    while left:
        d += datetime.timedelta(days=1)
        if business(d):
            left -= 1
    if (d.month == 12 and d.day >= 24) or (d.month == 1 and d.day == 1):
        year = d.year + 1 if d.month == 12 else d.year
        d = datetime.date(year, 1, 2)
        while d.weekday() >= 5:
            d += datetime.timedelta(days=1)
    return d.isoformat()
''')],
"window_mode": [
    ("INCREMENTAL COUNTS AND A SCAN (sliding_median shape, F144/F149): correct on "
     "every value, and the per-window scan over the counts is what makes it too slow", '''
def window_mode(xs, k):
    n = len(xs)
    if k < 1 or k > n:
        raise ValueError("k")
    cnt = {}
    for x in xs[:k]:
        cnt[x] = cnt.get(x, 0) + 1
    out = []
    for i in range(n - k + 1):
        if i:
            y = xs[i - 1]
            cnt[y] -= 1
            if not cnt[y]:
                del cnt[y]
            x = xs[i + k - 1]
            cnt[x] = cnt.get(x, 0) + 1
        best_v, best_c = None, -1
        for v, c in cnt.items():
            if c > best_c or (c == best_c and v < best_v):
                best_v, best_c = v, c
        out.append(best_v)
    return out
''')],
}

ARM_TIMEOUT = 25.0


def run(code: str, tests: str, timeout: float = ARM_TIMEOUT) -> tuple[bool, str]:
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
    for task in EXPERT_TASKS_V3:
        tid = task["id"]
        ref = REFERENCE.get(tid)
        if ref is None:
            print(f"{tid:22s} NO REFERENCE - cannot prove the task is solvable")
            bad += 1
            continue
        ok, err = run(ref, task["tests"])
        print(f"{tid:22s} reference {'PASS' if ok else 'FAIL'}"
              + ("" if ok else f"  <- task is broken: {err.strip()[:200]}"))
        if not ok:
            bad += 1
        for label, bank in (("naive", NAIVE), ("subtle", SUBTLE)):
            arms = bank.get(tid, [])
            if not arms:
                print(f"{'':22s} NO {label.upper()} ARM - discrimination unproven")
                bad += 1
                continue
            for why, code in arms:
                aok, _ = run(code, task["tests"])
                # An arm PASSING is the failure: the task discriminates nothing.
                verdict = f"WEAK TASK - {label} PASSED" if aok else "fails as intended"
                print(f"{'':22s} {label:6s} {verdict}")
                print(f"{'':29s} ({why})")
                if aok:
                    bad += 1
    print()
    if bad:
        print(f"{bad} problem(s). The bank is NOT usable - a task a competent-but-wrong "
              f"solution passes discriminates nothing, and a task nothing passes is broken.")
        return 1
    print(f"all {len(EXPERT_TASKS_V3)} tasks solvable AND discriminating against both "
          f"a naive and a competent-but-wrong solution. Bank usable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
