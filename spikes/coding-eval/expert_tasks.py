# File: expert_tasks.py
# Purpose: EXPERT-tier executable coding tasks - the frontier-locating set above spikes/coding-eval/tasks.py.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: Eight Python tasks that exist because the core set's "hard" tier
# does not discriminate at the top - upstage/solar-pro4, a cheap cloud model,
# scored 14/15 on it. That tier is made of named textbook algorithms
# (longest-valid-parens, LRU, word-break, topological sort, min-window,
# expression eval), which are dense in training data, so it measures recall
# of a known solution rather than capability.
#
# THE DIFFICULTY HERE IS DELIBERATELY OF A DIFFERENT KIND. Nothing is
# obscure; every task is a thing a working engineer would recognise. What
# separates them is that the SPEC has corners a fluent-but-shallow answer
# misses, and the tests are written to land exactly on those corners:
#
#   1. exactness  - a float shortcut gives a visibly wrong digit (round_decimal)
#   2. contracts  - laziness and non-mutation are requirements, not qualities
#                   (kmerge, apply_patch)
#   3. atomicity  - a failure midway must leave no trace (apply_patch)
#   4. complexity - a timing gate fails the naive-but-correct answer
#                   (glob_match, sliding_median, IntervalMap)
#   5. tie-breaks - "minimise X" is not enough; which optimum is required
#                   (wrap)
#   6. edge grammar - quoting, escaping and terminator rules that read as
#                   trivial and are not (parse_csv, glob_match)
#
# Contract per task, inherited from tasks.py: `prompt` must fully determine
# behaviour, because the model is scored on the spec it was given - any
# ambiguity is a bug in the TASK. Every task here was validated against a
# reference solution before use (tools/validate_expert_tasks.py), and each
# test block was additionally checked to FAIL a plausible naive solution, so
# a task that everything passes is a task that discriminates nothing.
#
# Where practical the tests verify a PROPERTY by brute force in-test rather
# than asserting a hardcoded expected value copied from my own reference -
# that keeps my reference out of the trust chain (see `wrap`).

from __future__ import annotations

EXPERT_TASKS: list[dict] = [
    {
        "id": "glob_match",
        "tier": "expert",
        "prompt": (
            "Write a Python function `glob_match(pattern: str, text: str) -> bool` implementing "
            "shell-style wildcard matching. The ENTIRE text must match the pattern.\n\n"
            "Rules:\n"
            "- `*` matches any sequence of characters, including the empty sequence.\n"
            "- `?` matches exactly one character.\n"
            "- `[...]` matches exactly one character from the set. Inside a class:\n"
            "    * `a-z` is an inclusive range by character code.\n"
            "    * a leading `!` negates the whole class.\n"
            "    * a `]` immediately after the opening `[`, or immediately after a leading `!`, "
            "is a literal `]` and does not close the class.\n"
            "    * a `-` first or last in the class is a literal `-`.\n"
            "- A backslash escapes the next character, making it literal. This applies both "
            "inside and outside a class. A lone trailing backslash matches a literal backslash.\n"
            "- If a `[` has no closing `]`, it is a literal `[`.\n\n"
            "Performance: the implementation must not be exponential. The pattern "
            "'a*a*a*a*a*a*b' against forty 'a' characters must return promptly.\n"
            "Return only the function in a Python code block."
        ),
        "tests": r"""
assert glob_match('', '') is True
assert glob_match('', 'a') is False
assert glob_match('*', '') is True
assert glob_match('*', 'anything') is True
assert glob_match('?', '') is False
assert glob_match('?', 'a') is True
assert glob_match('a*b', 'ab') is True
assert glob_match('a*b', 'axxxb') is True
assert glob_match('a*b', 'axxxbc') is False
assert glob_match('*.txt', 'notes.txt') is True
assert glob_match('*.txt', 'notes.txt.bak') is False
assert glob_match('[abc]x', 'bx') is True
assert glob_match('[abc]x', 'dx') is False
assert glob_match('[!abc]x', 'dx') is True
assert glob_match('[!abc]x', 'ax') is False
assert glob_match('[a-c]', 'b') is True
assert glob_match('[a-c]', 'd') is False
assert glob_match('[!a-c]', 'd') is True
assert glob_match('[]]', ']') is True
assert glob_match('[!]]', 'a') is True
assert glob_match('[!]]', ']') is False
assert glob_match('[-a]', '-') is True
assert glob_match('[a-]', '-') is True
assert glob_match('a[', 'a[') is True
assert glob_match('a[bc', 'a[bc') is True
assert glob_match('\\*', '*') is True
assert glob_match('\\*', 'x') is False
assert glob_match('\\?', '?') is True
assert glob_match('\\\\', '\\') is True
assert glob_match('[\\]]', ']') is True
assert glob_match('[a\\-c]', '-') is True
assert glob_match('[a\\-c]', 'b') is False
assert glob_match('*a*b*c*', 'xxaxxbxxcxx') is True
assert glob_match('*a*b*c*', 'xxaxxcxxbxx') is False
import time as _t
_start = _t.time()
assert glob_match('a*a*a*a*a*a*b', 'a'*40) is False
assert glob_match('*a*a*a*a*a*a*a*b', 'a'*60) is False
assert _t.time() - _start < 3.0, 'exponential backtracking'
""",
    },
    {
        "id": "round_decimal",
        "tier": "expert",
        "prompt": (
            "Write a Python function `round_decimal(s: str, places: int) -> str`.\n\n"
            "`s` is a decimal number as a string, optionally signed - for example '-12.345', "
            "'5', '0.5'. `places` is >= 0.\n\n"
            "Round `s` to exactly `places` decimal places using ROUND HALF TO EVEN (banker's "
            "rounding): when the discarded part is exactly one half, round so that the last "
            "kept digit is even.\n\n"
            "The result must be EXACT. Do not convert to float - a float cannot represent "
            "values such as 2.675 exactly and produces the wrong digit.\n\n"
            "Output format:\n"
            "- exactly `places` digits after the decimal point; the point is omitted entirely "
            "when places == 0.\n"
            "- the integer part has no leading zeros, except a single '0' for values below 1.\n"
            "- a leading '-' appears only when the rounded result is non-zero and negative; a "
            "negative value that rounds to zero returns the unsigned form.\n\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert round_decimal('2.675', 2) == '2.68'
assert round_decimal('2.665', 2) == '2.66'
assert round_decimal('0.5', 0) == '0'
assert round_decimal('1.5', 0) == '2'
assert round_decimal('2.5', 0) == '2'
assert round_decimal('3.5', 0) == '4'
assert round_decimal('-2.5', 0) == '-2'
assert round_decimal('-3.5', 0) == '-4'
assert round_decimal('9.99', 1) == '10.0'
assert round_decimal('9.95', 1) == '10.0'
assert round_decimal('0.05', 1) == '0.0'
assert round_decimal('0.15', 1) == '0.2'
assert round_decimal('0.25', 1) == '0.2'
assert round_decimal('0.35', 1) == '0.4'
assert round_decimal('5', 2) == '5.00'
assert round_decimal('123', 0) == '123'
assert round_decimal('-0.04', 1) == '0.0'
assert round_decimal('-0.06', 1) == '-0.1'
assert round_decimal('-0.5', 0) == '0'
assert round_decimal('0.000', 0) == '0'
assert round_decimal('12.3456789', 5) == '12.34568'
assert round_decimal('0.999999999999999999999', 2) == '1.00'
assert round_decimal('1.0049999999999999999', 2) == '1.00'
assert round_decimal('-12.345', 2) == '-12.34'
assert round_decimal('-12.355', 2) == '-12.36'
assert round_decimal('007.5', 0) == '8'
assert round_decimal('0.4999999999999999999999999', 0) == '0'
""",
    },
    {
        "id": "kmerge",
        "tier": "expert",
        "prompt": (
            "Write a Python generator function `kmerge(*iterables)` that yields the elements of "
            "several already-sorted iterables in sorted order.\n\n"
            "Requirements:\n"
            "- It must be LAZY. It may never consume more elements from an input than are "
            "needed to produce what the caller has already requested. Inputs may be infinite.\n"
            "- Ties break by argument position: when two inputs offer equal values, the one "
            "passed earlier is yielded first.\n"
            "- Calling it with no iterables yields nothing; empty iterables are allowed.\n"
            "- Elements are only required to support `<`.\n\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
import itertools
assert list(kmerge([1,3,5],[2,4,6])) == [1,2,3,4,5,6]
assert list(kmerge()) == []
assert list(kmerge([],[],[1])) == [1]
assert list(kmerge([1,1],[1])) == [1,1,1]
assert list(kmerge([1,2,3])) == [1,2,3]
assert list(kmerge([],[])) == []

g = kmerge(itertools.count(0,2), itertools.count(1,2))
assert list(itertools.islice(g,6)) == [0,1,2,3,4,5]

def _bomb(limit):
    for i in range(limit):
        yield i
    raise RuntimeError('over-consumed')

g2 = kmerge(_bomb(5), _bomb(5))
assert list(itertools.islice(g2,4)) == [0,0,1,1]

class _T:
    def __init__(self, v, tag):
        self.v = v
        self.tag = tag
    def __lt__(self, o):
        return self.v < o.v

out = list(kmerge([_T(1,'a'),_T(2,'a')], [_T(1,'b')]))
assert [t.tag for t in out] == ['a','b','a']

import random
random.seed(11)
srcs = [sorted(random.randint(0,50) for _ in range(40)) for _ in range(7)]
merged = list(kmerge(*srcs))
assert merged == sorted(x for s in srcs for x in s)
""",
    },
    {
        "id": "wrap",
        "tier": "expert",
        "prompt": (
            "Write a Python function `wrap(words: list[str], width: int) -> list[str]`.\n\n"
            "Pack the words, in order, into lines joined by a single space. Every word is "
            "guaranteed to be at most `width` characters. A line's length is the sum of its "
            "word lengths plus one space between adjacent words, and must not exceed `width`.\n\n"
            "Choose the wrapping that MINIMISES the sum, over every line EXCEPT THE LAST, of "
            "(width - line_length) ** 3. The last line contributes nothing.\n\n"
            "If several wrappings tie on that cost, return the one whose list of words-per-line "
            "is lexicographically smallest - that is, compare the per-line word counts in order, "
            "and the wrapping with FEWER words on the first differing line wins.\n\n"
            "An empty word list returns an empty list.\n"
            "Return only the function in a Python code block."
        ),
        # Brute force in-test: for small inputs this enumerates every legal
        # wrapping and derives the required answer independently, so the
        # reference implementation is NOT in the trust chain.
        "tests": """
import itertools, random

def _brute(words, width):
    n = len(words)
    if n == 0:
        return []
    best = None
    for mask in range(1 << max(n-1, 0)):
        lines, cur = [], [words[0]]
        for i in range(1, n):
            if mask >> (i-1) & 1:
                lines.append(cur); cur = [words[i]]
            else:
                cur.append(words[i])
        lines.append(cur)
        lens = [sum(len(w) for w in ln) + len(ln) - 1 for ln in lines]
        if any(L > width for L in lens):
            continue
        cost = sum((width - L) ** 3 for L in lens[:-1])
        counts = tuple(len(ln) for ln in lines)
        key = (cost, counts)
        if best is None or key < best[0]:
            best = (key, [' '.join(ln) for ln in lines])
    return best[1]

assert wrap([], 10) == []
assert wrap(['a'], 5) == ['a']
assert wrap(['aaaaa'], 5) == ['aaaaa']

# EXHAUSTIVE over a small space, not sampled. A cost TIE is what exercises
# the tie-break rule, and random word sets almost never produce one - a
# sampled test therefore certifies a solution that ignores the rule entirely.
for width in (4, 5, 6):
    for n in range(1, 7):
        for combo in itertools.product((1, 2, 3), repeat=n):
            words = ['x' * L for L in combo]
            expected = _brute(words, width)
            got = wrap(words, width)
            assert got == expected, (words, width, got, expected)

random.seed(23)
for _ in range(60):
    width = random.randint(4, 12)
    n = random.randint(1, 9)
    words = [''.join('x' for _ in range(random.randint(1, width))) for _ in range(n)]
    expected = _brute(words, width)
    got = wrap(words, width)
    assert got == expected, (words, width, got, expected)
    assert all(len(line) <= width for line in got)
    assert ' '.join(' '.join(got).split()) == ' '.join(words)
""",
    },
    {
        "id": "sliding_median",
        "tier": "expert",
        "prompt": (
            "Write a Python function `sliding_median(xs: list[int], k: int) -> list[int]`.\n\n"
            "For each window of k consecutive elements, left to right (there are "
            "len(xs) - k + 1 of them), return the LOWER median: the element at index "
            "(k - 1) // 2 of the sorted window.\n\n"
            "Raise ValueError if k < 1 or k > len(xs).\n\n"
            "Performance: it must handle 250,000 elements at k = 2,500 in a few seconds. "
            "Sorting each window independently is far too slow and will not pass.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
import random, time
assert sliding_median([1,2,3], 1) == [1,2,3]
assert sliding_median([5,1,3], 3) == [3]
assert sliding_median([1,2,3,4], 2) == [1,2,3]
assert sliding_median([4,3,2,1], 3) == [3,2]
assert sliding_median([7,7,7], 2) == [7,7]
assert sliding_median([-5,0,5], 3) == [0]

for bad in (0, -1, 4):
    try:
        sliding_median([1,2,3], bad)
    except ValueError:
        pass
    else:
        raise AssertionError('expected ValueError for k=%r' % (bad,))

random.seed(3)
small = [random.randint(-20, 20) for _ in range(200)]
for k in (1, 2, 3, 7, 50, 200):
    got = sliding_median(small, k)
    exp = [sorted(small[i:i+k])[(k-1)//2] for i in range(len(small)-k+1)]
    assert got == exp, k

random.seed(7)
N, K = 250000, 2500
xs = [random.randint(0, 10**6) for _ in range(N)]
t0 = time.time()
out = sliding_median(xs, K)
elapsed = time.time() - t0
assert len(out) == N - K + 1
for i in (0, 1, 500, 12345, len(out)-1):
    assert out[i] == sorted(xs[i:i+K])[(K-1)//2], i
assert elapsed < 8.0, 'too slow: %.1fs' % elapsed
""",
    },
    {
        "id": "apply_patch",
        "tier": "expert",
        "prompt": (
            "Write a Python function `apply_patch(doc, ops: list[dict])` applying RFC 6902 "
            "style operations to a JSON-like document of dicts, lists, strings, numbers, "
            "booleans and None. Return the NEW document. The input `doc` must NOT be mutated "
            "in any way.\n\n"
            "Paths are JSON Pointers. '' addresses the whole document. Otherwise the path is "
            "'/' separated tokens, and within a token '~1' decodes to '/' and '~0' decodes to "
            "'~', in that order.\n\n"
            "Operations:\n"
            "- {'op':'add','path':P,'value':V} - for an object member, insert or replace. For "
            "an array, insert BEFORE index P, where the token '-' means append.\n"
            "- {'op':'remove','path':P} - the location must exist.\n"
            "- {'op':'replace','path':P,'value':V} - the location must already exist.\n"
            "- {'op':'move','from':F,'path':P}\n"
            "- {'op':'copy','from':F,'path':P}\n"
            "- {'op':'test','path':P,'value':V} - fails unless the value at P equals V.\n\n"
            "ATOMICITY: apply the operations in order; if ANY operation fails, raise ValueError "
            "and leave the input document unchanged.\n\n"
            "Failures include a path that does not exist (except an 'add' creating a new object "
            "member or appending to an array), an array index that is not a valid integer or is "
            "out of range, a failing 'test', and an unknown op.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
import copy

d = {'a': 1, 'b': {'c': [1, 2, 3]}}
snap = copy.deepcopy(d)

assert apply_patch(d, []) == d
assert apply_patch(d, [{'op':'replace','path':'/a','value':9}]) == {'a':9,'b':{'c':[1,2,3]}}
assert d == snap, 'input was mutated'

assert apply_patch(d, [{'op':'add','path':'/z','value':5}])['z'] == 5
assert apply_patch(d, [{'op':'add','path':'/b/c/1','value':99}])['b']['c'] == [1,99,2,3]
assert apply_patch(d, [{'op':'add','path':'/b/c/-','value':4}])['b']['c'] == [1,2,3,4]
assert apply_patch(d, [{'op':'remove','path':'/b/c/0'}])['b']['c'] == [2,3]
assert apply_patch(d, [{'op':'remove','path':'/a'}]) == {'b':{'c':[1,2,3]}}
assert apply_patch(d, [{'op':'move','from':'/a','path':'/b/a'}]) == {'b':{'c':[1,2,3],'a':1}}
assert apply_patch(d, [{'op':'copy','from':'/a','path':'/b/a'}])['a'] == 1
assert apply_patch(d, [{'op':'test','path':'/a','value':1}]) == d
assert apply_patch(d, [{'op':'replace','path':'','value':{'q':1}}]) == {'q':1}
assert d == snap, 'input was mutated'

# escaping
esc = {'a/b': 1, 'm~n': 2}
assert apply_patch(esc, [{'op':'replace','path':'/a~1b','value':7}])['a/b'] == 7
assert apply_patch(esc, [{'op':'replace','path':'/m~0n','value':7}])['m~n'] == 7

def _must_fail(document, operations, why):
    before = copy.deepcopy(document)
    try:
        apply_patch(document, operations)
    except ValueError:
        assert document == before, 'mutated input on failure: ' + why
        return
    raise AssertionError('expected ValueError: ' + why)

_must_fail(d, [{'op':'replace','path':'/nope','value':1}], 'replace missing')
_must_fail(d, [{'op':'remove','path':'/nope'}], 'remove missing')
_must_fail(d, [{'op':'test','path':'/a','value':2}], 'test mismatch')
_must_fail(d, [{'op':'add','path':'/b/c/9','value':1}], 'array index out of range')
_must_fail(d, [{'op':'add','path':'/b/c/x','value':1}], 'array index not an integer')
_must_fail(d, [{'op':'remove','path':'/b/c/-'}], 'dash is not valid for remove')
_must_fail(d, [{'op':'frobnicate','path':'/a'}], 'unknown op')
_must_fail(d, [{'op':'move','from':'/nope','path':'/x'}], 'move from missing')

# ATOMICITY: a good op followed by a bad one leaves nothing behind
_must_fail(d, [{'op':'add','path':'/ok','value':1},
               {'op':'remove','path':'/nope'}], 'atomic rollback')
assert d == snap, 'input was mutated overall'
""",
    },
    {
        "id": "interval_map",
        "tier": "expert",
        "prompt": (
            "Write a Python class `IntervalMap`:\n"
            "- `__init__(self, default)` - every integer maps to `default` initially.\n"
            "- `assign(self, lo: int, hi: int, value) -> None` - set every integer x with "
            "lo <= x < hi to value. Raise ValueError if lo > hi; lo == hi is a no-op.\n"
            "- `get(self, x: int)` - the value at x.\n"
            "- `runs(self) -> list[tuple]` - the maximal half-open intervals whose value differs "
            "from the default, as (lo, hi, value), in increasing order of lo. Adjacent or "
            "overlapping intervals holding EQUAL values must be merged into a single run, and "
            "a later assign overwrites an earlier one on any overlap.\n\n"
            "Coordinates span the whole integer range, so per-integer storage is not viable: "
            "30,000 assignments of intervals up to 100,000 wide, spread over a range of 10**9, "
            "must complete in seconds.\n"
            "Return only the class in a Python code block."
        ),
        "tests": """
import random, time

m = IntervalMap(0)
assert m.get(5) == 0
assert m.runs() == []
m.assign(0, 10, 1)
assert m.get(0) == 1 and m.get(9) == 1 and m.get(10) == 0 and m.get(-1) == 0
assert m.runs() == [(0, 10, 1)]

m.assign(10, 20, 1)
assert m.runs() == [(0, 20, 1)], 'adjacent equal runs must merge'

m.assign(5, 15, 2)
assert m.runs() == [(0, 5, 1), (5, 15, 2), (15, 20, 1)]
assert m.get(4) == 1 and m.get(5) == 2 and m.get(14) == 2 and m.get(15) == 1

m.assign(0, 20, 0)
assert m.runs() == [], 'assigning the default removes the run'

m2 = IntervalMap('d')
m2.assign(3, 3, 'x')
assert m2.runs() == []
try:
    m2.assign(5, 4, 'x')
except ValueError:
    pass
else:
    raise AssertionError('expected ValueError for lo > hi')

m2.assign(-100, -50, 'a')
m2.assign(-50, -20, 'a')
assert m2.runs() == [(-100, -20, 'a')]

# randomised cross-check against a brute-force dict over a small universe
random.seed(31)
for _ in range(30):
    ref = {}
    im = IntervalMap(0)
    for _ in range(20):
        lo = random.randint(-30, 30)
        hi = lo + random.randint(0, 20)
        v = random.randint(0, 3)
        im.assign(lo, hi, v)
        for x in range(lo, hi):
            ref[x] = v
    for x in range(-40, 55):
        assert im.get(x) == ref.get(x, 0), x
    expected = []
    for x in range(-60, 80):
        v = ref.get(x, 0)
        if v == 0:
            continue
        if expected and expected[-1][1] == x and expected[-1][2] == v:
            expected[-1] = (expected[-1][0], x + 1, v)
        else:
            expected.append((x, x + 1, v))
    assert [tuple(r) for r in im.runs()] == expected

# scale: per-integer storage would need ~1.5x10**9 entries here, so it cannot
# finish on time OR fit in memory - interval logic is the only way through
random.seed(5)
big = IntervalMap(0)
t0 = time.time()
for i in range(30000):
    lo = random.randint(0, 10**9)
    big.assign(lo, lo + random.randint(1, 100000), i % 5 + 1)
elapsed = time.time() - t0
assert elapsed < 10.0, 'too slow: %.1fs' % elapsed
assert len(big.runs()) > 0
""",
    },
    {
        "id": "parse_csv",
        "tier": "expert",
        "prompt": (
            "Write a Python function `parse_csv(text: str) -> list[list[str]]` implementing "
            "RFC 4180 parsing.\n\n"
            "- Fields are separated by commas; records by a line break, which may be a newline "
            "or a carriage-return + newline pair.\n"
            "- A field may be quoted with double quotes. Inside a quoted field, two consecutive "
            "double quotes denote one literal double quote, and commas and line breaks are "
            "ordinary characters preserved as-is.\n"
            "- A quote only opens a field when it is the field's very first character. A double "
            "quote inside an UNQUOTED field is an ordinary character.\n"
            "- Any text between the closing quote of a quoted field and the next comma or line "
            "break is an error.\n"
            "- An unterminated quoted field is an error.\n"
            "- Errors raise ValueError.\n"
            "- A single trailing line break at the end of the text does NOT create an extra "
            "empty record. Empty text returns an empty list.\n"
            "- A record consisting of one empty field yields a list holding one empty string.\n\n"
            "Return only the function in a Python code block."
        ),
        "tests": r"""
assert parse_csv('') == []
assert parse_csv('a,b,c') == [['a','b','c']]
assert parse_csv('a,b,c\n') == [['a','b','c']]
assert parse_csv('a,b\r\nc,d') == [['a','b'],['c','d']]
assert parse_csv('a,b\r\nc,d\r\n') == [['a','b'],['c','d']]
assert parse_csv('\n') == [['']]
assert parse_csv('a,,b') == [['a','','b']]
assert parse_csv(',') == [['','']]
assert parse_csv('a\n\nb') == [['a'],[''],['b']]
assert parse_csv('"a"') == [['a']]
assert parse_csv('"a,b"') == [['a,b']]
assert parse_csv('"a""b"') == [['a"b']]
assert parse_csv('""') == [['']]
assert parse_csv('"a\nb"') == [['a\nb']]
assert parse_csv('"a\r\nb"') == [['a\r\nb']]
assert parse_csv('"a",b') == [['a','b']]
assert parse_csv('a,"b"') == [['a','b']]
assert parse_csv('a"b,c') == [['a"b','c']]
assert parse_csv('a"b"c') == [['a"b"c']]
assert parse_csv('"a"\n"b"') == [['a'],['b']]
assert parse_csv(' "a" ') == [[' "a" ']]
assert parse_csv('"",""') == [['','']]

for bad, why in [
    ('"a', 'unterminated'),
    ('"a"b', 'text after closing quote'),
    ('a,"b"c', 'text after closing quote mid-record'),
    ('"a""', 'unterminated after escaped quote'),
]:
    try:
        parse_csv(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('expected ValueError: ' + why)
""",
    },
]
