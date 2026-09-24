# File: tasks.py
# Purpose: Executable coding-eval task set - prompts plus hidden unit tests, scored by running the code.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: 15 Python tasks across three difficulty tiers, chosen so the set
# has HEADROOM - the eval-pilot suite saturates at 17/17 for every 20B+ model
# and therefore discriminates nothing. Each task gives the model a signature
# and a precise spec; the tests are hidden from the model and probe the edge
# cases the spec implies rather than the happy path. Grading is execution,
# not string matching, so there is no grader-artifact class of failure (the
# eval pilot lost a point to exactly that in 2026-07).
#
# Contract per task: `prompt` must fully determine behaviour - any ambiguity
# is a bug in the task, because the model is being scored on the spec it was
# given. `tests` runs against the model's module namespace and raises on
# failure. Tiers: easy (sanity floor), medium, hard (expected to separate).

from __future__ import annotations

TASKS: list[dict] = [
    {
        "id": "rle_encode",
        "tier": "easy",
        "prompt": (
            "Write a Python function `rle_encode(s: str) -> str` that run-length encodes a string.\n"
            "Each run of a repeated character becomes the character followed by the run length, "
            "ALWAYS including the count even when it is 1. For example 'aaab' -> 'a3b1'.\n"
            "An empty string returns an empty string.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert rle_encode('') == ''
assert rle_encode('a') == 'a1'
assert rle_encode('aaab') == 'a3b1'
assert rle_encode('abc') == 'a1b1c1'
assert rle_encode('aabbaa') == 'a2b2a2'
assert rle_encode('x'*12) == 'x12'
""",
    },
    {
        "id": "is_balanced",
        "tier": "easy",
        "prompt": (
            "Write a Python function `is_balanced(s: str) -> bool` returning True if the brackets "
            "in s are balanced and correctly nested. Consider only these characters: ( ) [ ] { }. "
            "Any other character is ignored.\n"
            "An empty string is balanced.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert is_balanced('') is True
assert is_balanced('()') is True
assert is_balanced('([{}])') is True
assert is_balanced('(]') is False
assert is_balanced('([)]') is False
assert is_balanced('(') is False
assert is_balanced(')(') is False
assert is_balanced('a(b)c[d]') is True
""",
    },
    {
        "id": "merge_intervals",
        "tier": "medium",
        "prompt": (
            "Write a Python function `merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]` "
            "that merges overlapping intervals and returns them sorted ascending by start.\n"
            "Intervals that merely TOUCH (e.g. (1,3) and (3,5)) DO merge, into (1,5).\n"
            "The input may be unsorted and may be empty. Do not mutate the input.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert merge_intervals([]) == []
assert merge_intervals([(1,3)]) == [(1,3)]
assert merge_intervals([(1,3),(3,5)]) == [(1,5)]
assert merge_intervals([(5,7),(1,3)]) == [(1,3),(5,7)]
assert merge_intervals([(1,10),(2,3)]) == [(1,10)]
assert merge_intervals([(1,4),(2,6),(8,10),(9,12)]) == [(1,6),(8,12)]
src = [(3,4),(1,2)]
merge_intervals(src)
assert src == [(3,4),(1,2)], 'input was mutated'
""",
    },
    {
        "id": "parse_semver",
        "tier": "medium",
        "prompt": (
            "Write a Python function `parse_semver(v: str) -> tuple[int, int, int, str | None]` that parses "
            "a semantic version string of the form MAJOR.MINOR.PATCH with an optional '-PRERELEASE' suffix.\n"
            "Return (major, minor, patch, prerelease) where prerelease is None when absent.\n"
            "Raise ValueError for anything malformed: missing components, non-numeric components, "
            "leading zeros in a numeric component (except the single digit '0'), or an empty prerelease after '-'.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert parse_semver('1.2.3') == (1,2,3,None)
assert parse_semver('0.0.0') == (0,0,0,None)
assert parse_semver('1.2.3-rc1') == (1,2,3,'rc1')
assert parse_semver('10.20.30-alpha.1') == (10,20,30,'alpha.1')
for bad in ['1.2', '1.2.3.4', 'a.b.c', '1.02.3', '01.2.3', '1.2.3-', '', '1.2.x']:
    try:
        parse_semver(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('expected ValueError for %r' % bad)
""",
    },
    {
        "id": "top_k_frequent",
        "tier": "medium",
        "prompt": (
            "Write a Python function `top_k_frequent(nums: list[int], k: int) -> list[int]` returning the k "
            "most frequent values.\n"
            "Order the result by descending frequency; ties are broken by SMALLER value first.\n"
            "If k exceeds the number of distinct values, return all distinct values under the same ordering.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert top_k_frequent([1,1,1,2,2,3], 2) == [1,2]
assert top_k_frequent([1,2], 2) == [1,2]
assert top_k_frequent([3,3,2,2,1], 2) == [2,3]
assert top_k_frequent([5,5,4,4,3,3], 3) == [3,4,5]
assert top_k_frequent([1], 5) == [1]
assert top_k_frequent([], 3) == []
""",
    },
    {
        "id": "spiral_order",
        "tier": "medium",
        "prompt": (
            "Write a Python function `spiral_order(matrix: list[list[int]]) -> list[int]` returning the "
            "elements of a rectangular matrix in clockwise spiral order starting at the top-left.\n"
            "Handle non-square matrices, single rows, single columns, and an empty matrix (return []).\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert spiral_order([]) == []
assert spiral_order([[1]]) == [1]
assert spiral_order([[1,2,3]]) == [1,2,3]
assert spiral_order([[1],[2],[3]]) == [1,2,3]
assert spiral_order([[1,2],[3,4]]) == [1,2,4,3]
assert spiral_order([[1,2,3],[4,5,6],[7,8,9]]) == [1,2,3,6,9,8,7,4,5]
assert spiral_order([[1,2,3,4],[5,6,7,8],[9,10,11,12]]) == [1,2,3,4,8,12,11,10,9,5,6,7]
""",
    },
    {
        "id": "group_anagrams",
        "tier": "medium",
        "prompt": (
            "Write a Python function `group_anagrams(words: list[str]) -> list[list[str]]` grouping words "
            "that are anagrams of each other.\n"
            "Within each group, preserve the order the words appeared in the input.\n"
            "Order the groups by the position of each group's FIRST word in the input.\n"
            "Comparison is case-sensitive. An empty input returns [].\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert group_anagrams([]) == []
assert group_anagrams(['eat','tea','tan','ate','nat','bat']) == [['eat','tea','ate'],['tan','nat'],['bat']]
assert group_anagrams(['a']) == [['a']]
assert group_anagrams(['Ab','ba']) == [['Ab'],['ba']]
assert group_anagrams(['abc','cba','bca']) == [['abc','cba','bca']]
""",
    },
    {
        "id": "normalize_path",
        "tier": "medium",
        "prompt": (
            "Write a Python function `normalize_path(p: str) -> str` that normalises a POSIX-style path "
            "purely lexically, without touching the filesystem.\n"
            "Collapse repeated slashes, remove '.' components, and resolve '..' against the preceding "
            "component. A leading '/' makes the path absolute and '..' at the root is discarded.\n"
            "For a relative path, leading '..' components that cannot be resolved are KEPT.\n"
            "The empty string normalises to '.'. A result that would be empty is '.'.\n"
            "Do not return a trailing slash except for the root '/'.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert normalize_path('') == '.'
assert normalize_path('/') == '/'
assert normalize_path('//a//b') == '/a/b'
assert normalize_path('/a/./b') == '/a/b'
assert normalize_path('/a/b/..') == '/a'
assert normalize_path('/..') == '/'
assert normalize_path('/../..') == '/'
assert normalize_path('a/b/../..') == '.'
assert normalize_path('../a') == '../a'
assert normalize_path('a/../../b') == '../b'
assert normalize_path('/a/b/') == '/a/b'
""",
    },
    {
        "id": "roman_roundtrip",
        "tier": "medium",
        "prompt": (
            "Write TWO Python functions:\n"
            "`int_to_roman(n: int) -> str` for 1 <= n <= 3999 using standard subtractive notation "
            "(4=IV, 9=IX, 40=XL, 90=XC, 400=CD, 900=CM).\n"
            "`roman_to_int(s: str) -> int` parsing that same notation.\n"
            "Both must raise ValueError on out-of-range or malformed input.\n"
            "Return only the functions in a single Python code block."
        ),
        "tests": """
assert int_to_roman(1) == 'I'
assert int_to_roman(4) == 'IV'
assert int_to_roman(9) == 'IX'
assert int_to_roman(58) == 'LVIII'
assert int_to_roman(1994) == 'MCMXCIV'
assert int_to_roman(3999) == 'MMMCMXCIX'
assert roman_to_int('MCMXCIV') == 1994
assert roman_to_int('LVIII') == 58
for n in [1, 4, 9, 14, 40, 90, 400, 999, 1000, 2026, 3999]:
    assert roman_to_int(int_to_roman(n)) == n, n
for bad in [0, 4000, -1]:
    try:
        int_to_roman(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('expected ValueError for %r' % bad)
""",
    },
    {
        "id": "longest_valid_parens",
        "tier": "hard",
        "prompt": (
            "Write a Python function `longest_valid_parens(s: str) -> int` returning the length of the "
            "longest substring of s that is a well-formed sequence of '(' and ')'.\n"
            "s contains only '(' and ')'. An empty string returns 0.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert longest_valid_parens('') == 0
assert longest_valid_parens('(') == 0
assert longest_valid_parens('()') == 2
assert longest_valid_parens(')()())') == 4
assert longest_valid_parens('(()') == 2
assert longest_valid_parens('()(()') == 2
assert longest_valid_parens('()(())') == 6
assert longest_valid_parens('(()())') == 6
assert longest_valid_parens('))((') == 0
assert longest_valid_parens('()' * 500) == 1000
""",
    },
    {
        "id": "lru_cache",
        "tier": "hard",
        "prompt": (
            "Write a Python class `LRUCache` with:\n"
            "`__init__(self, capacity: int)` - capacity >= 1, else raise ValueError.\n"
            "`get(self, key) -> int` returning the value or -1 if absent. A successful get counts as a USE.\n"
            "`put(self, key, value) -> None` inserting or updating. An update also counts as a USE.\n"
            "When over capacity, evict the LEAST recently used entry.\n"
            "Return only the class in a Python code block."
        ),
        "tests": """
try:
    LRUCache(0)
except ValueError:
    pass
else:
    raise AssertionError('expected ValueError for capacity 0')
c = LRUCache(2)
c.put(1,1); c.put(2,2)
assert c.get(1) == 1
c.put(3,3)                 # evicts key 2 (1 was just used)
assert c.get(2) == -1
assert c.get(3) == 3
c.put(4,4)                 # evicts key 1
assert c.get(1) == -1
assert c.get(3) == 3 and c.get(4) == 4
d = LRUCache(2)
d.put(1,1); d.put(2,2); d.put(1,10)   # update counts as use
d.put(3,3)                            # evicts 2
assert d.get(2) == -1
assert d.get(1) == 10
""",
    },
    {
        "id": "word_break",
        "tier": "hard",
        "prompt": (
            "Write a Python function `word_break(s: str, words: list[str]) -> list[str] | None` that splits s "
            "entirely into a sequence of words from the dictionary, each usable any number of times.\n"
            "Return the segmentation as a list of words, or None if no segmentation exists.\n"
            "When several segmentations exist, return the one that is lexicographically smallest when "
            "compared as a list of strings.\n"
            "An empty s returns [].\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert word_break('', ['a']) == []
assert word_break('leetcode', ['leet','code']) == ['leet','code']
assert word_break('abc', ['a','b']) is None
assert word_break('aaa', ['a','aa']) == ['a','a','a']
assert word_break('catsanddog', ['cat','cats','and','sand','dog']) == ['cat','sand','dog']
assert word_break('ab', ['ab','a','b']) == ['a','b']
""",
    },
    {
        "id": "topo_schedule",
        "tier": "hard",
        "prompt": (
            "Write a Python function `schedule(deps: dict[str, list[str]]) -> list[str] | None`.\n"
            "deps maps a task name to the list of tasks it DEPENDS ON (which must run before it).\n"
            "Return a valid execution order, or None if there is a cycle.\n"
            "Every name appearing as a dependency is itself a task even if absent as a key.\n"
            "When several orders are valid, return the lexicographically smallest one.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert schedule({}) == []
assert schedule({'a': []}) == ['a']
assert schedule({'b': ['a']}) == ['a','b']
assert schedule({'a': ['b'], 'b': ['a']}) is None
assert schedule({'c': ['a','b'], 'a': [], 'b': []}) == ['a','b','c']
assert schedule({'z': ['y'], 'y': ['x']}) == ['x','y','z']
r = schedule({'build': ['fetch'], 'test': ['build'], 'lint': []})
assert r == ['fetch','build','lint','test'] or r == ['lint','fetch','build','test'], r
""",
    },
    {
        "id": "min_window",
        "tier": "hard",
        "prompt": (
            "Write a Python function `min_window(s: str, t: str) -> str` returning the shortest substring of s "
            "containing every character of t including duplicates.\n"
            "If no such substring exists return ''. If several are equally short, return the leftmost.\n"
            "An empty t returns ''.\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert min_window('ADOBECODEBANC','ABC') == 'BANC'
assert min_window('a','a') == 'a'
assert min_window('a','aa') == ''
assert min_window('','a') == ''
assert min_window('abc','') == ''
assert min_window('aaflslflsldkalskaaa','aaa') == 'aaa'
assert min_window('bba','ab') == 'ba'
""",
    },
    {
        "id": "eval_expr",
        "tier": "hard",
        "prompt": (
            "Write a Python function `eval_expr(s: str) -> int` evaluating an integer arithmetic expression.\n"
            "Supports + - * / and parentheses, unary minus, and arbitrary whitespace.\n"
            "Division is INTEGER division TRUNCATED TOWARD ZERO (so -7/2 == -3, not -4).\n"
            "Standard precedence: parentheses, then unary minus, then * and / left-to-right, then + and - "
            "left-to-right.\n"
            "Raise ValueError on malformed input and ZeroDivisionError on division by zero.\n"
            "Do NOT use eval() or exec().\n"
            "Return only the function in a Python code block."
        ),
        "tests": """
assert eval_expr('1+1') == 2
assert eval_expr(' 2*3 + 4 ') == 10
assert eval_expr('2+3*4') == 14
assert eval_expr('(2+3)*4') == 20
assert eval_expr('-7/2') == -3
assert eval_expr('7/-2') == -3
assert eval_expr('-(3+4)') == -7
assert eval_expr('2*(3+(4-1))') == 12
assert eval_expr('100/10/2') == 5
try:
    eval_expr('1/0')
except ZeroDivisionError:
    pass
else:
    raise AssertionError('expected ZeroDivisionError')
for bad in ['', '1+', '(1', '1)', '*2', '1 2']:
    try:
        eval_expr(bad)
    except ValueError:
        pass
    else:
        raise AssertionError('expected ValueError for %r' % bad)
""",
    },
]

TIERS = ("easy", "medium", "hard")
