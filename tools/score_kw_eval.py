#!/usr/bin/env python3
# File: tools/score_kw_eval.py
# Purpose: Score banked KA-H1 transcripts mechanically. Never calls a model.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: A separate scoring pass over banked answers, so a scoring bug costs
# a re-run of this file and not of the GPU. E67's classifier was inverted -
# comparing prose dates to ISO tool results by substring, so every obeyed call
# read as ignored - and was corrected from banked traces at zero GPU cost.
#
# THE HEADLINE IS A PAIR, NOT A MEDIAN. success_at_deadline first, conditional
# TTCA second and always beside its success count. A median wall time over
# successes only, quoted alone, has silently dropped the wrong answers and the
# non-terminating ones - exactly the cases the programme exists to study.
#
# IT REPORTS "I CANNOT DECIDE THIS" AS A THIRD OUTCOME. Forcing a mechanical
# check to choose between right and wrong on a free-text answer manufactures a
# verdict. Cells it cannot settle are counted as `needs_judge`, the totals are
# reported as a FLOOR, and nothing is silently rounded to zero.
#
# A CONFIDENTLY WRONG ANSWER TO AN UNANSWERABLE QUESTION IS A CRITICAL ERROR,
# counted separately from an ordinary miss. For advisory work that is the
# failure that costs something: a competent reader would have acted on it.

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "kw-eval"))
from kw_items import load_items  # noqa: E402

# The ruler has a version, because it has already been wrong once and results
# must name the ruler that produced them.
#
#   v1  2026-08-19  exact ASCII substring matching
#   v2  2026-08-20  INSTRUMENT DEFECT FIXED - v1 penalised models that write
#                   with typographic punctuation. gpt-oss-120b emits 383
#                   non-ASCII characters across 24 answers (166 U+2011
#                   NON-BREAKING HYPHEN, 119 U+202F NARROW NO-BREAK SPACE)
#                   against Qwen3-30B-A3B's 7 and the frontier arm's 0, so
#                   "memory-pressure", "power-cycle", "success-at-deadline" and
#                   "Qwen 3.8-27B" all scored as misses while being the required
#                   answers. Cells that moved v1 -> v2: gpt-oss-120b K04, K07,
#                   K14, K18, K20, K25 wrong -> correct (K20 also critical ->
#                   correct, the most serious class awarded to a correct
#                   abstention); Qwen3-30B-A3B K05 critical -> correct. No other
#                   arm or cell changed. NOTHING WAS REGENERATED - the same
#                   banked completions were re-scored.
SCORER_VERSION = "v2-2026-08-20"

_UNDETERMINED = (
    "cannot determine",
    "cannot be determined",
    "can't determine",
    "not stated",
    "does not state",
    "doesn't state",
    "does not say",
    "doesn't say",
    "not given",
    "no rate",
    "not specified",
    "insufficient",
    "does not provide",
    "does not settle",
    "not settled",
    "unable to determine",
    "not enough",
    "does not give",
    "no figure",
    "not possible to determine",
    # Added 2026-08-20 after the gpt-oss failure taxonomy: three arms declined
    # correctly in phrasings this list did not recognise, and one of those was
    # scored a CRITICAL ERROR - the most serious class the instrument has.
    "does not contain",
    "is not mentioned",
    "no mention",
    "does not include",
    "does not record",
    "nowhere in",
    "absent from",
)


# Typography is not content. Measured 2026-08-20: gpt-oss-120b emits 383
# non-ASCII characters across 24 answers - 166 NON-BREAKING HYPHENS and 119
# NARROW NO-BREAK SPACES - against the workhorse's 7 and the frontier arm's 0.
# An exact ASCII substring check therefore penalised ONE model for its
# formatting, scoring "memory-pressure", "power-cycle" and
# "success-at-deadline" as misses when each is the required answer. That
# inverted a headline finding. Suspect the ruler before the data.
# The table moved to tools/typography.py on 2026-08-20, unchanged, because
# spikes/eval-pilot/score_keyed.py carried the identical defect and a fix
# applied to one copy and not the other is how this defect survived in the
# first place. `_fold` is kept as a name so this file's v2 stamp still
# describes the same behaviour it described when it was written.
from typography import TYPOGRAPHY_VERSION, fold as _fold  # noqa: E402,F401


def _norm(s: str) -> str:
    """Lowercase, fold Unicode punctuation, collapse whitespace, strip emphasis."""
    s = _fold(s).lower().replace("*", "").replace("`", "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _strip_separators(s: str) -> str:
    """Content with separators removed - commas, hyphens, spaces, quotes.

    A model writing "Qwen 3.8-27B" has named the same model as one writing
    "Qwen3.8", and "6,223" is "6223". Separators are formatting choices.

    DELIBERATELY NARROW. It does NOT touch letters, digits, decimal points or
    operators, so "Qwen3.8" and "Qwen38" stay distinct, "3.66" never becomes
    "366", and a quoted source line keeps its content. The risk of a fold is
    making genuinely different identifiers indistinguishable, which would turn
    a false negative into a false positive - a worse defect, because nothing
    would ever surface it.
    """
    return re.sub(r"[\s,\-_/\"\']", "", s)


def _strip_with_index(s: str) -> tuple[str, list[int]]:
    """Separator-stripped text, plus each kept character's index in the original.

    The index map is what lets the boundary guard ask about the ORIGINAL text
    after matching against the stripped one.
    """
    out: list[str] = []
    idx: list[int] = []
    for i, ch in enumerate(s):
        if not re.match(r"[\s,\-_/\"\']", ch):
            out.append(ch)
            idx.append(i)
    return "".join(out), idx


def _bounded_find(hay: str, needle: str) -> bool:
    """Substring search with a DIGIT-BOUNDARY guard.

    Without it "Rule 9" matches "Rule 90" and "6,223" matches "6,2234". A needle
    ending in a digit must not be followed by another digit. Applied on BOTH
    comparison paths, because the plain path has the same exposure as the
    separator-folded one.
    """
    if not needle:
        return False
    start = 0
    while True:
        i = hay.find(needle, start)
        if i == -1:
            return False
        after = hay[i + len(needle) : i + len(needle) + 1]
        if not (needle[-1].isdigit() and after.isdigit()):
            return True
        start = i + 1


def _has(hay: str, needle: str) -> bool:
    """Substring match on normalised text, then again with separators removed."""
    h, n = _norm(hay), _norm(needle)
    if _bounded_find(h, n):
        return True
    # The separator-folded retry. Deliberately narrow: letters, digits, decimal
    # points and operators are untouched, so "Qwen3.8" and "Qwen38" stay
    # distinct and "3.66" never becomes "366". Turning a false negative into a
    # false positive would be the worse defect - nothing would surface it.
    #
    # The digit-boundary guard consults the ORIGINAL text, not the stripped
    # one. In "Qwen 3.8-27B" a separator sits between "3.8" and "27B", so
    # "Qwen3.8" is a legitimate match; in "Rule 90" nothing separates the
    # digits and it is not. Stripping first loses exactly that distinction.
    sh, idx = _strip_with_index(h)
    sn = _strip_separators(n)
    if not sn:
        return False
    start = 0
    while True:
        i = sh.find(sn, start)
        if i == -1:
            return False
        end = i + len(sn) - 1
        nxt = idx[end] + 1  # position in h just after the matched run
        after = h[nxt : nxt + 1]
        if not (sn[-1].isdigit() and after.isdigit()):
            return True
        start = i + 1


# Singular/plural and contracted auxiliaries are collapsed BEFORE matching, so
# "the documents do not say" and "the material does not say" hit the same entry.
# Growing the phrase list instead is how the AABR scorer acquired four false
# negatives across two patches before it was restructured.
_AUX = re.compile(r"\b(do not|don't|doesn't|did not|didn't|does not)\b")


# A trap phrase inside a NEGATION is the correct answer, not the trap. K07's
# expected answer is literally "do not use the workhorse", and a bare substring
# check for "use the workhorse" marked it wrong (2026-08-19, on the frontier
# arm, before any local arm had run). Negations are looked for in the ~24
# characters before the phrase - long enough for "do not", "never", "must not",
# "should not", "rather than".
_NEGATION = re.compile(
    r"\b(not|never|avoid|refuse|rather than|instead of|do not|don't|shouldn't|"
    r"mustn't|cannot|can't)\b[^.]{0,24}$"
)


def _says_without_negation(answer: str, phrase: str) -> bool:
    """True only where the phrase is ASSERTED, not where it is being ruled out."""
    a, p = _norm(answer), _norm(phrase)
    start = 0
    while True:
        i = a.find(p, start)
        if i == -1:
            return False
        if not _NEGATION.search(a[max(0, i - 40) : i]):
            return True
        start = i + 1


# "no euro-per-year figure is mentioned" is a decline, and no reasonable phrase
# list reaches it. A pattern does.
_NO_X = re.compile(
    r"\bno\b[^.]{0,50}\b(mention|figure|cost|information|"
    r"data|number|detail|reference)\b"
)


def says_undetermined(answer: str) -> bool:
    a = _AUX.sub("does not", _norm(answer))
    if any(_AUX.sub("does not", p) in a for p in _UNDETERMINED):
        return True
    return bool(_NO_X.search(a))


def outcome_matches(item: dict[str, Any], answer: str) -> bool | None:
    """True / False, or None meaning a judge is needed. Never guesses."""
    exp = item["expect"]
    if not answer.strip():
        return False

    for bad in exp.get("must_not_say", []):
        # A bare "yes" only counts as a trap when it OPENS the answer - "yes"
        # inside a sentence is ordinary prose.
        if _norm(bad) == "yes":
            if _norm(answer).split(" ")[:1] == ["yes"]:
                return False
            continue
        if _says_without_negation(answer, bad):
            return False

    if exp.get("is_unanswerable"):
        if says_undetermined(answer):
            return True
        if any(_has(answer, a) for a in exp.get("accept", [])):
            return True
        return False

    # An entry may be a LIST, meaning "any of these spellings". English
    # inflection is not a capability difference: an arm saying the model "hung"
    # has said the same thing as one saying it "hangs", and a check that cannot
    # see that manufactures a false negative.
    def _req_met(req: object) -> bool:
        if isinstance(req, (list, tuple)):
            return any(_has(answer, alt) for alt in req)
        return _has(answer, str(req))

    all_req = exp.get("must_contain_all", [])
    if all_req and not all(_req_met(r) for r in all_req):
        return False
    any_req = exp.get("must_contain_any", [])
    if any_req and not any(_has(answer, r) for r in any_req):
        # Nothing required was found and nothing forbidden was said. That is a
        # judgement call on free text, not a verdict this file can reach.
        return None
    if not all_req and not any_req:
        return None
    return True


def score_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text())
    by_id = {i["id"]: i for i in load_items()}
    rows: list[dict[str, Any]] = []
    for rec in data["records"]:
        item = by_id[rec["id"]]
        if rec["outcome"] != "completed":
            verdict: bool | None = False
            klass = "transport_failed"
        elif rec.get("hit_token_cap"):
            # Truncated is a COMPLETION failure, not a wrong answer (F87, F20).
            verdict = outcome_matches(item, rec["answer"])
            klass = "truncated" if verdict is not True else "correct_but_truncated"
        else:
            verdict = outcome_matches(item, rec["answer"])
            klass = {True: "correct", False: "wrong", None: "needs_judge"}[verdict]
        critical = bool(
            item["expect"].get("is_unanswerable")
            and verdict is False
            and not says_undetermined(rec["answer"])
        )
        rows.append(
            {
                "id": rec["id"],
                "category": rec["category"],
                "verdict": verdict,
                "class": klass,
                "critical_error": critical,
                "wall_s": rec["wall_s"],
                "ttft_s": rec.get("ttft_s"),
                "completion_tokens": rec.get("completion_tokens"),
                "prompt_tokens": rec.get("prompt_tokens"),
                "hit_token_cap": rec.get("hit_token_cap"),
                "answer_chars": rec.get("answer_chars"),
            }
        )

    n = len(rows)
    correct = [r for r in rows if r["verdict"] is True]
    judge = [r for r in rows if r["verdict"] is None]

    def med(xs: list[float]) -> float | None:
        if not xs:
            return None
        s = sorted(xs)
        return round(
            s[len(s) // 2] if len(s) % 2 else (s[len(s) // 2 - 1] + s[len(s) // 2]) / 2,
            2,
        )

    def pct(xs: list[float], q: float) -> float | None:
        if not xs:
            return None
        s = sorted(xs)
        return round(s[min(len(s) - 1, int(q * len(s)))], 2)

    ok_walls = [r["wall_s"] for r in correct]
    by_cat: dict[str, dict[str, int]] = {}
    for r in rows:
        c = by_cat.setdefault(r["category"], {"n": 0, "correct": 0})
        c["n"] += 1
        if r["verdict"] is True:
            c["correct"] += 1

    return {
        "scorer_version": SCORER_VERSION,
        "typography_version": TYPOGRAPHY_VERSION,
        "label": data["meta"]["label"],
        "pack": data["meta"]["pack"],
        "measured_prompt_tokens": data["meta"].get("measured_prompt_tokens"),
        "n": n,
        "correct": len(correct),
        "wrong": sum(1 for r in rows if r["verdict"] is False),
        "needs_judge": len(judge),
        "needs_judge_ids": [r["id"] for r in judge],
        "points_are_a_floor": bool(judge),
        "critical_errors": sum(1 for r in rows if r["critical_error"]),
        "transport_failed": sum(1 for r in rows if r["class"] == "transport_failed"),
        "truncated": sum(1 for r in rows if r["hit_token_cap"]),
        # The PAIR. Neither half is reportable without the other.
        "success_at_30s": sum(1 for r in correct if r["wall_s"] <= 30),
        "success_at_40s": sum(1 for r in correct if r["wall_s"] <= 40),
        "conditional_ttca_p50": med(ok_walls),
        "conditional_ttca_p95": pct(ok_walls, 0.95),
        "conditional_ttca_n": len(ok_walls),
        "wall_median_all": med([r["wall_s"] for r in rows]),
        "ttft_median": med([r["ttft_s"] for r in rows if r["ttft_s"]]),
        "generated_tokens_total": sum(r["completion_tokens"] or 0 for r in rows),
        "by_category": by_cat,
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Score banked KA-H1 runs mechanically. Never calls a model.",
        epilog="example: python3 tools/score_kw_eval.py results/raw/kw-*.json",
    )
    ap.add_argument("files", nargs="+")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    summaries = [score_file(Path(f)) for f in args.files]
    print(
        f"{'arm':22s} {'pack':4s} {'ctx tok':>8s} {'correct':>8s} {'@30s':>5s} "
        f"{'@40s':>5s} {'judge':>6s} {'crit':>5s} {'p50':>7s} {'p95':>7s}"
    )
    for s in summaries:
        print(
            f"{s['label']:22s} {s['pack']:4s} {s['measured_prompt_tokens'] or 0:>8,} "
            f"{s['correct']:>3d}/{s['n']:<4d} {s['success_at_30s']:>5d} "
            f"{s['success_at_40s']:>5d} {s['needs_judge']:>6d} "
            f"{s['critical_errors']:>5d} "
            f"{s['conditional_ttca_p50'] or 0:>7.1f} {s['conditional_ttca_p95'] or 0:>7.1f}"
        )
    floors = [s["label"] for s in summaries if s["points_are_a_floor"]]
    if floors:
        print(
            f"\nNOTE: totals are a FLOOR for {', '.join(floors)} - some cells could "
            f"not be settled mechanically and are counted as neither right nor wrong."
        )
    if args.out:
        Path(args.out).write_text(json.dumps(summaries, indent=2))
        print(f"written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
