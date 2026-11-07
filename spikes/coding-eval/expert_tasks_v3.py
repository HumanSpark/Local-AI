# File: expert_tasks_v3.py
# Purpose: Third batch of expert-tier coding tasks, built to the THREE-ARM standard after expert2 saturated.
# Project: sparkbench | Date: 2026-09-06
#
# Overview: E110 served the seven expert2 tasks to the incumbent and it scored
# 7/7 in 16,917 tokens - a quarter of the original expert tier's cost (F150).
# Every one of those tasks had been proved to defeat a NAIVE solution. That
# test turns out to be necessary and nowhere near sufficient: a competent model
# does not write the naive solution, it writes the correct one. The bank
# measured the gap between RIGHT and OBVIOUSLY WRONG where a discriminating
# bank must measure the gap between RIGHT and NEARLY RIGHT.
#
# So every task here must satisfy THREE arms before admission
# (tools/validate_expert_tasks_v3.py), not two:
#   1. a REFERENCE solution that PASSES        - the task is solvable
#   2. a NAIVE solution that FAILS             - the old bar, kept
#   3. a SUBTLE solution that FAILS            - correct-looking, idiomatic,
#      the kind of thing a good engineer plausibly writes, wrong on one corner
#
# Arm 3 is the whole point, and its corner is NOT imagined. Owner decision
# 2026-09-06: source the subtle error from failures this repo has MEASURED,
# because my own sense of "plausible" is what produced a 7/7 bank.
#
#   billing_schedule       anchor drift in month arithmetic   <- F92 (two models
#                          miscounted the same deadline identically)
#   peak_load              half-open boundary that reads       <- F89 (gpt-oss-120b's
#                          correctly at a glance                  boundary error, which
#                                                                 no reasoning budget fixed)
#   clear_days_deadline    multi-step date calculation where   <- F92 + F146 (temperature
#                          one wrong step propagates              degraded calendar work
#                                                                 and nothing else)
#   window_mode            a structural complexity gate the    <- F144/F149 (sliding_median
#                          incremental-but-scanning answer        defeats every model at
#                          fails                                  every quant tested)
#
# This is a SEPARATE module, and the seven expert2 tasks are NOT deleted. They
# are valid, tested and self-contained; they measure a band this model is above,
# which is a different bank rather than a broken one (owner decision 2026-09-06).
# E42's, E104's and E110's scores stay comparable against unchanged tiers.
#
# Contract per task, inherited: `prompt` must FULLY determine behaviour. Any
# ambiguity is a bug in the task, not a failure of the model. Where practical
# the tests verify a PROPERTY by brute force rather than asserting a value
# copied from the reference, which keeps the reference out of the trust chain.
#
# The runner's bounds are part of the grade: 15 s wall clock and a 4 GB address
# space per candidate (run_coding_eval.run_candidate). Both complexity gates
# below are calibrated against them.

from __future__ import annotations

EXPERT_TASKS_V3: list[dict] = [
    {
        "id": "billing_schedule",
        "tier": "expert3",
        "axis": "date arithmetic + fixed anchor",
        "prompt": (
            "Write a Python function "
            "`billing_schedule(start: str, n: int) -> list[tuple[str, str, int]]` "
            "using only the standard library.\n\n"
            "`start` is a date as 'YYYY-MM-DD'. Return `n` consecutive monthly billing "
            "periods, each a tuple `(period_start, period_end, days)` where the two dates "
            "are 'YYYY-MM-DD' strings.\n\n"
            "Rules, which are the whole task:\n"
            "- The ANCHOR DAY is the day-of-month of `start`, and it is FIXED for the whole "
            "schedule. It never changes.\n"
            "- The first period starts on `start`. Each later boundary is the anchor day in "
            "the next calendar month.\n"
            "- If that month is too short to have the anchor day, use the LAST day of that "
            "month for that boundary ONLY. The anchor is unaffected: from a 31st anchor, "
            "February gives the 28th (29th in a leap year) and March gives the 31st again, "
            "not the 28th.\n"
            "- Each period is HALF-OPEN: it runs from its own start date up to but NOT "
            "including the next boundary. `period_end` is that next boundary.\n"
            "- `days` is the number of days in the period, i.e. the count of dates from "
            "`period_start` up to but not including `period_end`.\n"
            "- There are n periods, so n + 1 boundaries are computed by the same rule.\n"
            "- Raise ValueError if n < 1.\n\n"
            "Assume `start` is a well-formed real date. Return only the function."
        ),
        "tests": '''
import datetime, random

# The anchor is FIXED: a short month must not capture it.
got = billing_schedule("2026-01-31", 4)
assert [g[0] for g in got] == ["2026-01-31", "2026-02-28", "2026-03-31", "2026-04-30"], got
assert [g[1] for g in got] == ["2026-02-28", "2026-03-31", "2026-04-30", "2026-05-31"], got
assert [g[2] for g in got] == [28, 31, 30, 31], got

# Leap year.
got = billing_schedule("2024-01-31", 2)
assert [g[0] for g in got] == ["2024-01-31", "2024-02-29"], got
assert got[0][2] == 29, got

# A 30th anchor over February, then back out to the 30th.
got = billing_schedule("2026-01-30", 3)
assert [g[0] for g in got] == ["2026-01-30", "2026-02-28", "2026-03-30"], got

# Year rollover.
got = billing_schedule("2025-12-31", 2)
assert [g[0] for g in got] == ["2025-12-31", "2026-01-31"], got

# An unremarkable anchor is unremarkable.
got = billing_schedule("2026-03-15", 3)
assert [g[0] for g in got] == ["2026-03-15", "2026-04-15", "2026-05-15"], got
assert [g[2] for g in got] == [31, 30, 31], got

assert billing_schedule("2026-03-15", 1) == [("2026-03-15", "2026-04-15", 31)]

for bad in (0, -1):
    try:
        billing_schedule("2026-03-15", bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for n=%r" % (bad,))

# Properties, by brute force, so the reference is not in the trust chain.
random.seed(11)
for _ in range(60):
    y = random.randint(2019, 2031)
    m = random.randint(1, 12)
    d = random.randint(1, 28) if random.random() < 0.4 else random.choice([28, 29, 30, 31])
    try:
        s = datetime.date(y, m, d)
    except ValueError:
        continue
    n = random.randint(1, 30)
    out = billing_schedule(s.isoformat(), n)
    assert len(out) == n
    for i, (a, b, days) in enumerate(out):
        da = datetime.date.fromisoformat(a)
        db = datetime.date.fromisoformat(b)
        assert (db - da).days == days, (a, b, days)
        assert db > da, (a, b)
        # contiguous, no gap and no overlap
        if i + 1 < n:
            assert out[i + 1][0] == b, (out[i], out[i + 1])
        # each boundary is the anchor day, or the month end when the month is short
        last_of_month = (datetime.date(db.year + (db.month == 12),
                                       db.month % 12 + 1, 1)
                         - datetime.timedelta(days=1)).day
        assert db.day == min(s.day, last_of_month), (s.isoformat(), b)
        # exactly one month apart
        assert (db.year - da.year) * 12 + (db.month - da.month) == 1, (a, b)
''',
    },
    {
        "id": "peak_load",
        "tier": "expert3",
        "axis": "half-open boundary + complexity gate",
        "prompt": (
            "Write a Python function "
            "`peak_load(intervals: list[tuple[int, int]]) -> tuple[int, int]`.\n\n"
            "Each interval is HALF-OPEN `[start, end)`: it covers every integer point p "
            "with start <= p < end.\n\n"
            "Return `(peak, t)` where `peak` is the greatest number of intervals covering "
            "any single point, and `t` is the SMALLEST point at which that many intervals "
            "cover simultaneously.\n\n"
            "Rules, which are the whole task:\n"
            "- Because the intervals are half-open, an interval ENDING at time T and one "
            "STARTING at time T are NEVER simultaneous. [(0, 5), (5, 10)] has a peak of 1, "
            "not 2.\n"
            "- An interval with start >= end covers nothing and is ignored entirely.\n"
            "- If no interval covers anything, return (0, -1).\n"
            "- Coordinates are integers, may be negative, and may be up to 10**9 in "
            "magnitude. The list may contain duplicates.\n\n"
            "Performance: it must handle 200,000 intervals in a few seconds. Walking time "
            "point by point, or comparing every pair of intervals, is far too slow and will "
            "not pass.\n"
            "Return only the function."
        ),
        "tests": '''
import random, time

assert peak_load([]) == (0, -1)
assert peak_load([(5, 5)]) == (0, -1)
assert peak_load([(5, 4)]) == (0, -1)
assert peak_load([(0, 5), (5, 10)]) == (1, 0), "half-open: touching is not overlapping"
assert peak_load([(0, 10), (5, 15)]) == (2, 5)
assert peak_load([(0, 10), (2, 4), (3, 8)]) == (3, 3)
assert peak_load([(0, 1)]) == (1, 0)
assert peak_load([(-10, -5), (-7, -1)]) == (2, -7)
assert peak_load([(0, 5), (0, 5)]) == (2, 0), "duplicates stack"
assert peak_load([(3, 9), (0, 2), (0, 2)]) == (2, 0), "earliest point wins the tie"
assert peak_load([(0, 2), (0, 2), (3, 9), (4, 9)]) == (2, 0)
assert peak_load([(0, 2), (3, 9), (4, 9), (5, 9)]) == (3, 5)
assert peak_load([(1, 3), (3, 5), (5, 7)]) == (1, 1)

# Brute force over a small coordinate space, so the reference is not in the trust chain.
random.seed(5)
for _ in range(300):
    n = random.randint(0, 12)
    iv = []
    for _ in range(n):
        a = random.randint(-8, 8)
        b = random.randint(-8, 8)
        iv.append((a, b))
    cover = {}
    for a, b in iv:
        for p in range(a, b):
            cover[p] = cover.get(p, 0) + 1
    if not cover:
        exp = (0, -1)
    else:
        mx = max(cover.values())
        exp = (mx, min(p for p, c in cover.items() if c == mx))
    assert peak_load(list(iv)) == exp, (iv, exp)

# Complexity gate.
random.seed(19)
N = 200000
big = []
for _ in range(N):
    a = random.randint(-10**9, 10**9)
    big.append((a, a + random.randint(0, 5000)))
t0 = time.time()
pk, tt = peak_load(big)
el = time.time() - t0
assert el < 8.0, "too slow: %.1fs for %d intervals" % (el, N)
assert isinstance(pk, int) and isinstance(tt, int)
assert pk >= 1
# Spot-check the reported answer directly: no interval may be missing at t,
# and no point sampled at random may beat the reported peak.
cnt = sum(1 for a, b in big if a <= tt < b)
assert cnt == pk, (cnt, pk)
for _ in range(20):
    a, b = random.choice(big)
    if a >= b:
        continue
    p = random.randint(a, b - 1)
    c = sum(1 for x, y in big if x <= p < y)
    assert c <= pk, (p, c, pk)
''',
    },
    {
        "id": "clear_days_deadline",
        "tier": "expert3",
        "axis": "multi-step date rules + propagation",
        "prompt": (
            "Write a Python function "
            "`clear_days_deadline(start: str, n: int, holidays: list[str]) -> str` "
            "using only the standard library. All dates are 'YYYY-MM-DD'.\n\n"
            "A BUSINESS DAY is a Monday to Friday that is not a holiday.\n\n"
            "Rules, which are the whole task, applied in this order:\n"
            "1. COUNTING. The `start` date NEVER counts, whether or not it is a business "
            "day. Count forward from the day AFTER `start`. The n-th business day "
            "encountered is the provisional deadline. Non-business days are skipped and "
            "consume nothing.\n"
            "2. VACATION. If the provisional deadline falls on any date from 24 December to "
            "1 January INCLUSIVE, it moves to the first business day on or after the "
            "following 2 January. A date of 24-31 December moves into the NEXT calendar "
            "year; a date of 1 January moves within the SAME year.\n"
            "3. Dates inside 24 December to 1 January are still counted as business days in "
            "step 1 when they are Monday to Friday and not holidays. The vacation rule "
            "applies to the RESULT of the count, not to the counting.\n\n"
            "`holidays` may contain duplicates, dates that fall at weekends, and dates far "
            "outside the range of interest. All of that must be tolerated.\n\n"
            "Raise ValueError if n < 1.\n\n"
            "Assume every date string is a well-formed real date. Return only the function."
        ),
        "tests": '''
import datetime, random

def _bd(d, hol):
    return d.weekday() < 5 and d.isoformat() not in hol

# Plain forward count from a business day. 2026-03-02 is a Monday.
assert clear_days_deadline("2026-03-02", 1, []) == "2026-03-03"
assert clear_days_deadline("2026-03-02", 5, []) == "2026-03-09", "weekend is skipped"

# The start date never counts even when it is a business day.
assert clear_days_deadline("2026-03-03", 1, []) == "2026-03-04"

# The start date never counts when it is NOT a business day either, and the
# roll to the next business day is not itself a count. 2026-03-07 is a Saturday.
assert clear_days_deadline("2026-03-07", 1, []) == "2026-03-09"
assert clear_days_deadline("2026-03-08", 1, []) == "2026-03-09"
assert clear_days_deadline("2026-03-07", 2, []) == "2026-03-10"

# Holidays consume nothing. 2026-03-04 is a Wednesday.
assert clear_days_deadline("2026-03-02", 3, ["2026-03-04"]) == "2026-03-06"
assert clear_days_deadline("2026-03-02", 3, ["2026-03-04", "2026-03-04"]) == "2026-03-06"
# A holiday at a weekend changes nothing.
assert clear_days_deadline("2026-03-02", 5, ["2026-03-07", "2019-01-01"]) == "2026-03-09"

# Vacation. 2026-12-23 is a Wednesday; 2026-12-24 is a Thursday.
assert clear_days_deadline("2026-12-22", 1, []) == "2026-12-23"
assert clear_days_deadline("2026-12-22", 2, []) == "2027-01-04", "24 Dec moves past the vacation"
assert clear_days_deadline("2026-12-22", 3, []) == "2027-01-04"
# 1 January moves within the same year. 2027-01-01 is a Friday.
assert clear_days_deadline("2026-12-31", 1, []) == "2027-01-04"
# The first business day on or after 2 January, with 4 January a holiday.
assert clear_days_deadline("2026-12-22", 2, ["2027-01-04"]) == "2027-01-05"

for bad in (0, -1):
    try:
        clear_days_deadline("2026-03-02", bad, [])
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for n=%r" % (bad,))

# Property check by brute force, on dates that avoid the vacation window
# entirely, so this arm tests only the counting rule.
random.seed(23)
for _ in range(250):
    s = datetime.date(2026, 1, 1) + datetime.timedelta(days=random.randint(0, 300))
    hol = set()
    for _ in range(random.randint(0, 6)):
        hol.add((s + datetime.timedelta(days=random.randint(-3, 25))).isoformat())
    n = random.randint(1, 12)
    d = s
    left = n
    while left:
        d += datetime.timedelta(days=1)
        if _bd(d, hol):
            left -= 1
    if datetime.date(2026, 12, 24) <= d or d <= datetime.date(2026, 1, 1):
        continue
    got = clear_days_deadline(s.isoformat(), n, sorted(hol))
    assert got == d.isoformat(), (s.isoformat(), n, sorted(hol), got, d.isoformat())
''',
    },
    {
        "id": "window_mode",
        "tier": "expert3",
        "axis": "complexity gate + specified tie-break",
        "prompt": (
            "Write a Python function `window_mode(xs: list[int], k: int) -> list[int]`.\n\n"
            "For each window of k consecutive elements, left to right (there are "
            "len(xs) - k + 1 of them), return the MODE of that window: the value that "
            "occurs most often.\n\n"
            "Rules, which are the whole task:\n"
            "- If several values tie on count, return the SMALLEST of them.\n"
            "- Raise ValueError if k < 1 or k > len(xs).\n\n"
            "Performance: it must handle 300,000 elements at k = 4,000, with values spread "
            "over roughly 100,000 distinct integers, in a few seconds. Recounting each "
            "window is far too slow. So is keeping a running count per value and then "
            "scanning those counts to find the best one for every window - that scan is "
            "what makes it too slow, and it will not pass.\n"
            "Return only the function."
        ),
        "tests": '''
import random, time
from collections import Counter

def _mode(w):
    c = Counter(w)
    m = max(c.values())
    return min(v for v, n in c.items() if n == m)

assert window_mode([1, 2, 3], 1) == [1, 2, 3]
assert window_mode([1, 1, 2], 3) == [1]
assert window_mode([5, 5, 7, 7], 4) == [5], "tie goes to the smallest value"
assert window_mode([7, 7, 5, 5], 4) == [5], "tie goes to the smallest value, not the first seen"
assert window_mode([3, 1, 2], 3) == [1], "all counts equal: the smallest value"
assert window_mode([-4, -4, 9], 2) == [-4, -4]
assert window_mode([2, 2, 3, 3, 3, 2], 3) == [2, 3, 3, 3]

for bad in (0, -1, 4):
    try:
        window_mode([1, 2, 3], bad)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for k=%r" % (bad,))

# Brute force on small inputs, so the reference is not in the trust chain.
random.seed(31)
for trial in range(12):
    small = [random.randint(-6, 6) for _ in range(160)]
    for k in (1, 2, 3, 8, 40, 160):
        got = window_mode(small, k)
        exp = [_mode(small[i:i + k]) for i in range(len(small) - k + 1)]
        assert got == exp, (trial, k)

# Complexity gate. Values spread wide so a per-window scan over the counts
# cannot be cheap.
random.seed(37)
N, K = 300000, 4000
big = [random.randint(0, 99999) for _ in range(N)]
t0 = time.time()
out = window_mode(big, K)
el = time.time() - t0
assert el < 6.0, "too slow: %.1fs for N=%d k=%d" % (el, N, K)
assert len(out) == N - K + 1
# Spot-check windows directly rather than trusting a whole reference run.
for i in random.sample(range(N - K + 1), 25):
    assert out[i] == _mode(big[i:i + K]), i
''',
    },
]
