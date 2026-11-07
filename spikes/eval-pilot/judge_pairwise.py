#!/usr/bin/env python3
# File: judge_pairwise.py
# Purpose: Run the Material-Outcome Test rubric as a blind pairwise judge over stored answers.
# Project: sparkbench | Date: 2026-08-11
#
# Overview: Builds the judge prompt exactly as the reviewed benchmark does - rubric, then the
# original question, then two anonymised answers - and posts it to a llama-server /v1 endpoint.
# Every pairing is judged in BOTH label orders, which controls position bias directly rather
# than hoping randomisation cancels it, and yields a position-consistency figure as a by-product.
# The judge model must not be one of the contestants: self-preference would confound the result.
# Verdicts are parsed from the first non-empty line and recorded RAW when unrecognised, never
# coerced into a winner. Plan: docs/plans/2026-08-11-benchmark-instrumentation-uplift.md task 3.

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

VERDICTS = {
    "TIE, FUNCTIONALLY EQUIVALENT": "tie",
    "ANSWER A IS MATERIALLY BETTER": "A",
    "ANSWER B IS MATERIALLY BETTER": "B",
    "BOTH MATERIALLY INADEQUATE": "both_inadequate",
}


def load_rubric(path: str | Path) -> str:
    """Return the rubric body, stripped of our provenance header."""
    text = Path(path).read_text()
    marker = "\n---\n\n"
    if marker not in text:
        raise ValueError(
            f"no provenance separator in {path}; "
            f"hint: the rubric body must follow a '---' line - see rubrics/material-outcome-test.md"
        )
    return text.split(marker, 1)[1].strip()


# Deliberate deviation from the reviewed harness, which appended nothing after the two
# answers. Measured 2026-08-11: 6 of 20 calls ANSWERED the E10 question instead of
# judging it. Our "question" is a 12k-word log ending in an imperative ("produce a
# table"), so the nearest instruction beat a rubric 21k tokens earlier. The reviewed
# harness never hit this because its matters were short prose. Closing instruction goes
# last, where recency works for us; the rubric text itself is still untouched.
CLOSING_INSTRUCTION = (
    "# YOUR TASK\n"
    "Apply the Material-Outcome Test above to ANSWER A and ANSWER B. The ORIGINAL "
    "QUESTION is reference material for checking their accuracy - do NOT answer it "
    "yourself, and do not produce a table of your own.\n"
    "Reply in the mandated report format, beginning with exactly one of the four "
    "verdict lines, standing alone."
)


def build_prompt(rubric: str, question: str, answer_a: str, answer_b: str) -> str:
    return (
        f"{rubric}\n\n# ORIGINAL QUESTION (reference only - do NOT answer it)\n{question}\n\n"
        f"# ANSWER A\n{answer_a}\n\n# ANSWER B\n{answer_b}\n\n{CLOSING_INSTRUCTION}\n"
    )


# The rubric's Output Format lists "Verdict." as a report item, so a judge that writes
# the label before the verdict is CONFORMING and must parse. Only the HEAD of the report
# is searched: the prompt quotes all four verdict options, so scanning the whole body
# would let an echoed rubric supply a verdict the judge never actually reached.
HEAD_LINES = 10
LABEL_RE = re.compile(r"^(?:\d+[.)]\s*)?(?:verdict\b[\s.:—-]*)?", re.IGNORECASE)


def parse_verdict(text: str) -> tuple[str, str]:
    """Map the head of the judge's report onto one of the four verdicts.

    Returns (normalised, raw_line). Text carrying no recognisable verdict normalises to
    "unparsed" and keeps its first line - a judge that ignored the mandated format is a
    finding about the prompt, and silently guessing a winner would hide it AND put a
    fabricated result into the comparison.
    """
    first_line = ""
    seen = 0
    for raw_line in text.splitlines():
        line = raw_line.strip().strip("#*_ ").strip()
        if not line:
            continue
        if not first_line:
            first_line = line
        seen += 1
        if seen > HEAD_LINES:
            break
        candidate = LABEL_RE.sub("", line).strip().strip("*_ ").strip()
        upper = re.sub(r"[.\s]+$", "", candidate.upper())
        for canon, short in VERDICTS.items():
            if upper.startswith(canon):
                return short, line
    return "unparsed", first_line


def judge(base_url: str, prompt: str, timeout: float, max_tokens: int) -> str:
    payload = {
        "model": "local-model",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }
    req = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": "Bearer dummy"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read())
    return body["choices"][0]["message"]["content"]


def reparse_records(records: list[dict]) -> list[dict]:
    """Re-derive verdict/winner from each record's stored raw output.

    Generation is the expensive part and it is preserved verbatim, so a parser fix must
    never cost a re-run. Every record is re-derived from `raw` - not just the ones that
    previously failed - so the whole set is parsed by one version of the rules.
    """
    out = []
    for r in records:
        if "raw" not in r:
            raise KeyError(
                f"record for pair {r.get('pair')} has no stored raw output; "
                f"hint: only runs written by this script can be re-parsed"
            )
        verdict, line = parse_verdict(r["raw"])
        winner = {"A": r["slot_a"], "B": r["slot_b"]}.get(verdict, verdict)
        out.append({**r, "verdict": verdict, "winner": winner, "verdict_line": line})
    return out


def load_answers(results_glob: str) -> dict[str, str]:
    """label -> answer text, read from stored promptfoo result JSONs."""
    answers: dict[str, str] = {}
    for f in sorted(Path().glob(results_glob)):
        label = f.stem.replace("e10-", "")
        d = json.loads(f.read_text())
        results = d["results"]["results"]
        if not results:
            raise ValueError(
                f"{f} contains no results; "
                f"hint: re-run the eval-pilot suite for this model before scoring it"
            )
        answers[label] = str(results[0]["response"]["output"])
    return answers


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Blind pairwise judging with the Material-Outcome Test rubric.",
        epilog="Example: python3 judge_pairwise.py --base-url http://127.0.0.1:8100/v1 "
               "--out ../../results/eval-pilot/e10-pairwise.json",
    )
    ap.add_argument("--reparse", help="re-derive verdicts from a previous run's stored raw "
                                      "output and rewrite it; no model calls, no --base-url needed")
    ap.add_argument("--base-url", help="llama-server OpenAI-compatible base, e.g. http://127.0.0.1:8100/v1")
    ap.add_argument("--rubric", default="rubrics/material-outcome-test.md")
    ap.add_argument("--question-file", default="data/long-log.txt")
    ap.add_argument("--task", default="From the benchmark log above, produce a complete markdown "
                                      "table with columns Model and tg128, listing EVERY model that "
                                      "has a tg128 value recorded at depth 0 anywhere in the log. "
                                      "Use the exact values from the log.")
    ap.add_argument("--results-glob", default="../../results/eval-pilot/e10-*.json")
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--max-tokens", type=int, default=1400)
    ap.add_argument("--out", help="result JSON path (required unless --reparse)")
    args = ap.parse_args()

    if args.reparse:
        path = Path(args.reparse)
        data = json.loads(path.read_text())
        before = [r.get("verdict") for r in data["records"]]
        data["records"] = reparse_records(data["records"])
        after = [r["verdict"] for r in data["records"]]
        changed = sum(1 for a, b in zip(before, after) if a != b)
        path.write_text(json.dumps(data, indent=1))
        print(f"re-parsed {len(after)} records, {changed} changed")
        for v in sorted(set(after)):
            print(f"  {v}: {after.count(v)}")
        return 0

    if not args.base_url or not args.out:
        ap.error("--base-url and --out are required unless --reparse is given")
    rubric = load_rubric(args.rubric)
    question = Path(args.question_file).read_text() + "\n\n" + args.task
    answers = load_answers(args.results_glob)
    labels = sorted(answers)
    pairs = list(itertools.combinations(labels, 2))
    print(f"{len(labels)} answers, {len(pairs)} pairings, both label orders "
          f"= {len(pairs) * 2} judge calls", flush=True)

    records = []
    t_start = time.monotonic()
    for i, (x, y) in enumerate(pairs, 1):
        for order, (a, b) in (("xy", (x, y)), ("yx", (y, x))):
            t0 = time.monotonic()
            prompt = build_prompt(rubric, question, answers[a], answers[b])
            raw = judge(args.base_url, prompt, args.timeout, args.max_tokens)
            verdict, line = parse_verdict(raw)
            # Re-express the A/B verdict in terms of the LABELS, so the two orders
            # of the same pairing are directly comparable.
            winner = {"A": a, "B": b}.get(verdict, verdict)
            records.append({"pair": [x, y], "order": order, "slot_a": a, "slot_b": b,
                            "verdict": verdict, "winner": winner,
                            "verdict_line": line, "raw": raw})
            print(f"  [{i}/{len(pairs)}] {order} {a} vs {b} -> {winner} "
                  f"({time.monotonic() - t0:.0f}s, {time.monotonic() - t_start:.0f}s elapsed)",
                  flush=True)

    Path(args.out).write_text(json.dumps(
        {"judge_base_url": args.base_url, "n_pairs": len(pairs), "records": records}, indent=1))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
