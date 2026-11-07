#!/usr/bin/env python3
# File: validate_expert_tasks.py
# Purpose: Prove every expert coding task is both SOLVABLE and DISCRIMINATING before it scores any model.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: An eval task is only evidence if two things hold, and neither is
# self-evident from writing it. First, a correct solution passes - otherwise
# the task is broken and scores every model zero, which reads as "the models
# failed" when the truth is "I wrote a bad test". Second, a plausible WRONG
# solution fails - otherwise the task discriminates nothing and inflates
# every score, which is precisely how the core set ended up saturating at
# 14/15 for a cheap cloud model.
#
# So this runs each task's hidden tests twice: against a REFERENCE solution
# that must pass, and against one or more NAIVE solutions that must fail. A
# naive arm that unexpectedly passes is reported as a WEAK TASK - the test
# block does not land on the corner it was written for.
#
# Run: python3 tools/validate_expert_tasks.py   (exit 0 = tier is usable)

from __future__ import annotations

import resource
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "coding-eval"))
from expert_tasks import EXPERT_TASKS  # noqa: E402

# --------------------------------------------------------------------------
# REFERENCE SOLUTIONS - each must pass its task's hidden tests.
# --------------------------------------------------------------------------

REFERENCE: dict[str, str] = {
    "glob_match": '''
def _parse(pattern):
    toks, i, n = [], 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == "\\\\":
            if i + 1 < n:
                toks.append(("lit", pattern[i + 1])); i += 2
            else:
                toks.append(("lit", "\\\\")); i += 1
        elif c == "*":
            toks.append(("star",)); i += 1
        elif c == "?":
            toks.append(("any",)); i += 1
        elif c == "[":
            j = i + 1
            neg = False
            if j < n and pattern[j] == "!":
                neg = True; j += 1
            items, first, closed = [], True, False
            while j < n:
                if pattern[j] == "]" and not first:
                    closed = True; break
                if pattern[j] == "\\\\" and j + 1 < n:
                    ch = pattern[j + 1]; j += 2
                else:
                    ch = pattern[j]; j += 1
                if j < n and pattern[j] == "-" and j + 1 < n and pattern[j + 1] != "]":
                    j += 1
                    if pattern[j] == "\\\\" and j + 1 < n:
                        hi = pattern[j + 1]; j += 2
                    else:
                        hi = pattern[j]; j += 1
                    items.append((ch, hi))
                else:
                    items.append((ch, ch))
                first = False
            if closed:
                toks.append(("class", neg, items)); i = j + 1
            else:
                toks.append(("lit", "[")); i += 1
        else:
            toks.append(("lit", c)); i += 1
    return toks


def _one(tok, ch):
    if tok[0] == "lit":
        return ch == tok[1]
    if tok[0] == "any":
        return True
    inside = any(lo <= ch <= hi for lo, hi in tok[2])
    return (not inside) if tok[1] else inside


def glob_match(pattern, text):
    toks = _parse(pattern)
    cur = [False] * (len(text) + 1)
    cur[0] = True
    for tok in toks:
        nxt = [False] * (len(text) + 1)
        if tok[0] == "star":
            acc = False
            for j in range(len(text) + 1):
                acc = acc or cur[j]
                nxt[j] = acc
        else:
            for j in range(len(text)):
                if cur[j] and _one(tok, text[j]):
                    nxt[j + 1] = True
        cur = nxt
    return cur[len(text)]
''',
    "round_decimal": '''
def round_decimal(s, places):
    neg = s.startswith("-")
    body = s[1:] if s[0] in "+-" else s
    if "." in body:
        ip, fp = body.split(".", 1)
    else:
        ip, fp = body, ""
    value = int(ip or "0") * (10 ** len(fp)) + (int(fp) if fp else 0)
    if len(fp) <= places:
        q = value * (10 ** (places - len(fp)))
    else:
        drop = len(fp) - places
        div = 10 ** drop
        q, r = divmod(value, div)
        half = div // 2
        if r > half or (r == half and q % 2 == 1):
            q += 1
    if places == 0:
        out = str(q)
    else:
        t = str(q).zfill(places + 1)
        out = t[:-places] + "." + t[-places:]
    return ("-" + out) if (neg and q != 0) else out
''',
    "kmerge": '''
import heapq


class _Node:
    __slots__ = ("v", "idx", "it")

    def __init__(self, v, idx, it):
        self.v = v; self.idx = idx; self.it = it

    def __lt__(self, o):
        if self.v < o.v:
            return True
        if o.v < self.v:
            return False
        return self.idx < o.idx


def kmerge(*iterables):
    heap = []
    for idx, src in enumerate(iterables):
        it = iter(src)
        try:
            v = next(it)
        except StopIteration:
            continue
        heap.append(_Node(v, idx, it))
    heapq.heapify(heap)
    while heap:
        node = heapq.heappop(heap)
        yield node.v
        try:
            node.v = next(node.it)
        except StopIteration:
            continue
        heapq.heappush(heap, node)
''',
    "wrap": '''
def wrap(words, width):
    n = len(words)
    if n == 0:
        return []
    lens = [len(w) for w in words]
    pref = [0] * (n + 1)
    for i, L in enumerate(lens):
        pref[i + 1] = pref[i] + L

    def line_len(i, j):
        return pref[j] - pref[i] + (j - i - 1)

    INF = float("inf")
    best = [None] * (n + 1)
    best[n] = (0, ())
    for i in range(n - 1, -1, -1):
        chosen = None
        for j in range(i + 1, n + 1):
            L = line_len(i, j)
            if L > width:
                break
            if best[j] is None:
                continue
            if j == n:
                cand = (0, (j - i,))
            else:
                sub = best[j]
                if sub[0] == INF:
                    continue
                cand = (sub[0] + (width - L) ** 3, (j - i,) + sub[1])
            if chosen is None or cand < chosen:
                chosen = cand
        best[i] = chosen if chosen is not None else (INF, ())
    out, i = [], 0
    for count in best[0][1]:
        out.append(" ".join(words[i:i + count]))
        i += count
    return out
''',
    "sliding_median": '''
import bisect


def sliding_median(xs, k):
    if k < 1 or k > len(xs):
        raise ValueError(
            f"k={k} out of range for {len(xs)} elements. "
            f"hint: k must satisfy 1 <= k <= len(xs)"
        )
    win = sorted(xs[:k])
    idx = (k - 1) // 2
    out = [win[idx]]
    for i in range(k, len(xs)):
        win.pop(bisect.bisect_left(win, xs[i - k]))
        bisect.insort(win, xs[i])
        out.append(win[idx])
    return out
''',
    "apply_patch": '''
import copy


def _tokens(path):
    if path == "":
        return []
    if not path.startswith("/"):
        raise ValueError(f"bad JSON pointer {path!r}. hint: must be empty or start with /")
    return [t.replace("~1", "/").replace("~0", "~") for t in path[1:].split("/")]


def _index(seq, token, allow_end):
    if token == "-":
        if allow_end:
            return len(seq)
        raise ValueError("'-' is only valid when adding to an array")
    if not token.isdigit():
        raise ValueError(f"array index {token!r} is not a non-negative integer")
    i = int(token)
    limit = len(seq) if allow_end else len(seq) - 1
    if i > limit:
        raise ValueError(f"array index {i} out of range (limit {limit})")
    return i


def _get(doc, tokens):
    cur = doc
    for t in tokens:
        if isinstance(cur, list):
            cur = cur[_index(cur, t, False)]
        elif isinstance(cur, dict):
            if t not in cur:
                raise ValueError(f"missing member {t!r}")
            cur = cur[t]
        else:
            raise ValueError(f"cannot descend into {type(cur).__name__} at {t!r}")
    return cur


def _set(doc, tokens, value, mode):
    if not tokens:
        return value
    parent = _get(doc, tokens[:-1])
    last = tokens[-1]
    if isinstance(parent, list):
        i = _index(parent, last, mode == "add")
        if mode == "add":
            parent.insert(i, value)
        else:
            parent[i] = value
    elif isinstance(parent, dict):
        if mode == "replace" and last not in parent:
            raise ValueError(f"cannot replace missing member {last!r}")
        parent[last] = value
    else:
        raise ValueError(f"cannot set on {type(parent).__name__}")
    return doc


def _remove(doc, tokens):
    if not tokens:
        raise ValueError("cannot remove the whole document")
    parent = _get(doc, tokens[:-1])
    last = tokens[-1]
    if isinstance(parent, list):
        parent.pop(_index(parent, last, False))
    elif isinstance(parent, dict):
        if last not in parent:
            raise ValueError(f"cannot remove missing member {last!r}")
        del parent[last]
    else:
        raise ValueError(f"cannot remove from {type(parent).__name__}")
    return doc


def apply_patch(doc, ops):
    work = copy.deepcopy(doc)
    for op in ops:
        kind = op.get("op")
        if kind == "add":
            work = _set(work, _tokens(op["path"]), copy.deepcopy(op["value"]), "add")
        elif kind == "replace":
            toks = _tokens(op["path"])
            if toks:
                _get(work, toks)
            work = _set(work, toks, copy.deepcopy(op["value"]), "replace")
        elif kind == "remove":
            work = _remove(work, _tokens(op["path"]))
        elif kind == "test":
            if _get(work, _tokens(op["path"])) != op["value"]:
                raise ValueError("test failed")
        elif kind in ("move", "copy"):
            src = _tokens(op["from"])
            val = copy.deepcopy(_get(work, src))
            if kind == "move":
                work = _remove(work, src)
            work = _set(work, _tokens(op["path"]), val, "add")
        else:
            raise ValueError(f"unknown op {kind!r}")
    return work
''',
    "interval_map": '''
import bisect


class IntervalMap:
    def __init__(self, default):
        self.default = default
        self.los = []
        self.runs_ = []

    def _split(self, x):
        i = bisect.bisect_right(self.los, x) - 1
        if i < 0:
            return
        lo, hi, v = self.runs_[i]
        if lo < x < hi:
            self.runs_[i] = (lo, x, v)
            self.runs_.insert(i + 1, (x, hi, v))
            self.los.insert(i + 1, x)

    def assign(self, lo, hi, value):
        if lo > hi:
            raise ValueError(
                f"lo={lo} exceeds hi={hi}. hint: assign takes a half-open [lo, hi)"
            )
        if lo == hi:
            return
        self._split(lo)
        self._split(hi)
        a = bisect.bisect_left(self.los, lo)
        b = bisect.bisect_left(self.los, hi)
        del self.runs_[a:b]
        del self.los[a:b]
        if value != self.default:
            self.runs_.insert(a, (lo, hi, value))
            self.los.insert(a, lo)
            self._merge_around(a)
        elif a > 0:
            self._merge_around(a - 1)

    def _merge_around(self, i):
        for j in (i, i - 1):
            if 0 <= j < len(self.runs_) - 1:
                lo1, hi1, v1 = self.runs_[j]
                lo2, hi2, v2 = self.runs_[j + 1]
                if hi1 == lo2 and v1 == v2:
                    self.runs_[j] = (lo1, hi2, v1)
                    del self.runs_[j + 1]
                    del self.los[j + 1]

    def get(self, x):
        i = bisect.bisect_right(self.los, x) - 1
        if i < 0:
            return self.default
        lo, hi, v = self.runs_[i]
        return v if lo <= x < hi else self.default

    def runs(self):
        return list(self.runs_)
''',
    "parse_csv": '''
def parse_csv(text):
    if text == "":
        return []
    n = len(text)
    rows, row, i = [], [], 0
    while True:
        buf = []
        if i < n and text[i] == '"':
            i += 1
            while True:
                if i >= n:
                    raise ValueError("unterminated quoted field")
                if text[i] == '"':
                    if i + 1 < n and text[i + 1] == '"':
                        buf.append('"'); i += 2
                    else:
                        i += 1; break
                else:
                    buf.append(text[i]); i += 1
            if i < n and not (text[i] == "," or text[i] == "\\n"
                              or (text[i] == "\\r" and i + 1 < n and text[i + 1] == "\\n")):
                raise ValueError("text after closing quote")
        else:
            while i < n:
                c = text[i]
                if c == "," or c == "\\n" or (c == "\\r" and i + 1 < n and text[i + 1] == "\\n"):
                    break
                buf.append(c); i += 1
        row.append("".join(buf))
        if i >= n:
            rows.append(row)
            break
        if text[i] == ",":
            i += 1
            continue
        i += 2 if text[i] == "\\r" else 1
        rows.append(row)
        row = []
        if i >= n:
            break
    return rows
''',
}

# --------------------------------------------------------------------------
# NAIVE SOLUTIONS - each MUST fail, naming the corner the task exists to probe.
# --------------------------------------------------------------------------

NAIVE: dict[str, list[tuple[str, str]]] = {
    "glob_match": [
        ("exponential recursion (correct but times out)", '''
def glob_match(pattern, text):
    def go(p, t):
        if not p:
            return not t
        if p[0] == "*":
            return go(p[1:], t) or (bool(t) and go(p, t[1:]))
        if not t:
            return False
        if p[0] == "?":
            return go(p[1:], t[1:])
        return p[0] == t[0] and go(p[1:], t[1:])
    return go(pattern, text)
'''),
        ("fnmatch (wrong escape and class semantics)", '''
import fnmatch


def glob_match(pattern, text):
    return fnmatch.fnmatchcase(text, pattern)
'''),
    ],
    "round_decimal": [
        ("float round() - inexact and half-even only by accident", '''
def round_decimal(s, places):
    v = round(float(s), places)
    return f"%.{places}f" % v if places else str(int(v))
'''),
    ],
    "kmerge": [
        ("materialises every input - not lazy", '''
def kmerge(*iterables):
    merged = []
    for src in iterables:
        merged.extend(list(src))
    for x in sorted(merged):
        yield x
'''),
        ("heapq of raw tuples - tie-break breaks without __eq__", '''
import heapq


def kmerge(*iterables):
    heap = []
    for idx, src in enumerate(iterables):
        it = iter(src)
        try:
            v = next(it)
        except StopIteration:
            continue
        heap.append((v, idx, it))
    heapq.heapify(heap)
    while heap:
        v, idx, it = heapq.heappop(heap)
        yield v
        try:
            heapq.heappush(heap, (next(it), idx, it))
        except StopIteration:
            pass
'''),
    ],
    "wrap": [
        ("greedy - correct-looking, not cost-optimal", '''
def wrap(words, width):
    if not words:
        return []
    lines, cur = [], []
    for w in words:
        trial = len(" ".join(cur + [w]))
        if cur and trial > width:
            lines.append(" ".join(cur)); cur = [w]
        else:
            cur.append(w)
    lines.append(" ".join(cur))
    return lines
'''),
        # Scans j ASCENDING and takes the last equal-cost option, so among
        # optimal wrappings it prefers MORE words on the earlier line - the
        # exact inverse of the registered tie-break. The earlier version of
        # this arm scanned descending, which accidentally implemented the
        # required rule and made the task look discriminating when it was not.
        ("optimal cost, inverted tie-break", '''
def wrap(words, width):
    n = len(words)
    if n == 0:
        return []
    pref = [0]
    for w in words:
        pref.append(pref[-1] + len(w))
    INF = float("inf")
    best = [INF] * (n + 1)
    nxt = [n] * (n + 1)
    best[n] = 0
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n + 1):
            L = pref[j] - pref[i] + (j - i - 1)
            if L > width:
                break
            c = 0 if j == n else (width - L) ** 3 + best[j]
            if c <= best[i]:
                best[i] = c; nxt[i] = j
    out, i = [], 0
    while i < n:
        j = nxt[i]
        out.append(" ".join(words[i:j])); i = j
    return out
'''),
    ],
    "sliding_median": [
        ("sort every window - correct but quadratic", '''
def sliding_median(xs, k):
    if k < 1 or k > len(xs):
        raise ValueError("bad k")
    return [sorted(xs[i:i + k])[(k - 1) // 2] for i in range(len(xs) - k + 1)]
'''),
    ],
    "apply_patch": [
        ("mutates the input document in place", '''
def _toks(path):
    return [] if path == "" else [
        t.replace("~1", "/").replace("~0", "~") for t in path[1:].split("/")
    ]


def apply_patch(doc, ops):
    for op in ops:
        toks = _toks(op["path"])
        cur = doc
        for t in toks[:-1]:
            cur = cur[int(t)] if isinstance(cur, list) else cur[t]
        if op["op"] == "replace":
            cur[toks[-1]] = op["value"]
        elif op["op"] == "add":
            cur[toks[-1]] = op["value"]
        elif op["op"] == "remove":
            del cur[toks[-1]]
    return doc
'''),
        ("non-atomic: earlier ops survive a later failure", '''
import copy


def apply_patch(doc, ops):
    work = copy.deepcopy(doc)
    done = []
    for op in ops:
        toks = [] if op["path"] == "" else [
            t.replace("~1", "/").replace("~0", "~") for t in op["path"][1:].split("/")
        ]
        cur = work
        for t in toks[:-1]:
            cur = cur[int(t)] if isinstance(cur, list) else cur[t]
        if op["op"] in ("add", "replace"):
            cur[toks[-1]] = op["value"]
        elif op["op"] == "remove":
            del cur[toks[-1]]
        else:
            raise ValueError("unknown")
        done.append(op)
    return work
'''),
    ],
    "interval_map": [
        ("per-integer dict - cannot survive a 10**9 range", '''
class IntervalMap:
    def __init__(self, default):
        self.default = default
        self.d = {}

    def assign(self, lo, hi, value):
        if lo > hi:
            raise ValueError("lo > hi")
        for x in range(lo, hi):
            self.d[x] = value

    def get(self, x):
        return self.d.get(x, self.default)

    def runs(self):
        out = []
        for x in sorted(k for k, v in self.d.items() if v != self.default):
            v = self.d[x]
            if out and out[-1][1] == x and out[-1][2] == v:
                out[-1] = (out[-1][0], x + 1, v)
            else:
                out.append((x, x + 1, v))
        return out
'''),
    ],
    "parse_csv": [
        ("csv module - does not raise on text after a closing quote", '''
import csv
import io


def parse_csv(text):
    if text == "":
        return []
    return [row for row in csv.reader(io.StringIO(text, newline=""))]
'''),
        ("naive split - no quote handling at all", '''
def parse_csv(text):
    if text == "":
        return []
    body = text[:-1] if text.endswith("\\n") else text
    return [line.split(",") for line in body.replace("\\r\\n", "\\n").split("\\n")]
'''),
    ],
}


def run(code: str, tests: str, wall_s: float = 90.0, mem_gb: int = 4) -> tuple[bool, str]:
    """Execute a candidate in a BOUNDED subprocess.

    This ran in-process once and it was a mistake worth not repeating. The
    naive `interval_map` arm exists precisely to be infeasible - it builds a
    per-integer dict over a 10**9 range - and an unbounded validation pass
    that can consume the box is a validation pass that can kill the overnight
    benchmark it is meant to support. Address-space and wall limits make the
    failure of a naive arm cheap and local, which is what "it must fail"
    was always supposed to mean.
    """
    with tempfile.TemporaryDirectory(prefix="sparkbench-validate-") as scratch:
        src = Path(scratch) / "candidate.py"
        src.write_text(code + "\n\n" + tests + "\n")
        try:
            proc = subprocess.run(
                [sys.executable, str(src)],
                cwd=scratch,
                capture_output=True,
                text=True,
                timeout=wall_s,
                stdin=subprocess.DEVNULL,
                preexec_fn=lambda: resource.setrlimit(
                    resource.RLIMIT_AS, (mem_gb * 1024**3, mem_gb * 1024**3)
                ),
            )
        except subprocess.TimeoutExpired:
            return False, f"TIMEOUT after {wall_s:.0f}s"
        if proc.returncode == 0:
            return True, ""
        tail = (proc.stderr or "").strip().splitlines()
        if not tail:
            return False, f"exit {proc.returncode} with no stderr"
        last = tail[-1]
        if "MemoryError" in proc.stderr:
            last = f"MemoryError (hit the {mem_gb}GB cap): {last}"
        return False, last


def main() -> int:
    problems: list[str] = []
    print(f"validating {len(EXPERT_TASKS)} expert tasks\n")
    for task in EXPERT_TASKS:
        tid = task["id"]
        ref = REFERENCE.get(tid)
        if ref is None:
            problems.append(f"{tid}: NO REFERENCE SOLUTION - cannot certify the task is solvable")
            print(f"  {tid:<16} NO REFERENCE")
            continue
        ok, err = run(ref, task["tests"])
        print(f"  {tid:<16} reference {'PASS' if ok else 'FAIL  ' + err}")
        if not ok:
            problems.append(f"{tid}: reference solution FAILS its own tests - the task is broken ({err})")
        for label, naive in NAIVE.get(tid, []):
            n_ok, n_err = run(naive, task["tests"])
            verdict = "PASSED (task is WEAK)" if n_ok else f"failed as intended ({n_err[:60]})"
            print(f"  {'':<16}   naive: {label} -> {verdict}")
            if n_ok:
                problems.append(
                    f"{tid}: naive solution '{label}' PASSES - the tests do not land on the corner "
                    f"this task exists to probe"
                )
        if not NAIVE.get(tid):
            problems.append(f"{tid}: no naive counterexample - discrimination is unproven")

    print()
    if problems:
        print(f"{len(problems)} PROBLEM(S):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"all {len(EXPERT_TASKS)} tasks: solvable by a reference, and each defeats a naive attempt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
