#!/usr/bin/env python3
# File: e109_harness_knowledge.py
# Purpose: E109 arm B - ask the L5 questions THROUGH a harness, documents on disk.
# Project: sparkbench | Date: 2026-09-05
#
# Overview: Every L1-L5 figure in this repo is a bare API call with the whole
# document pack pasted into one request. That is not the shape a deployed system
# takes. This writes the SAME ten documents to disk and asks the SAME 24
# questions through an agent that must go and read them, graded by the SAME
# grader, so the only difference is the harness.
#
# L5 is saturated for MODEL comparison (F142) and that does not defeat this: the
# bare-API control scores 23/24, so the harness arm has 23 points of room to
# LOSE. Whether scaffolding costs accuracy is the question.
#
# The failure this is built to detect is RETRIEVAL: an agent that never opens
# the governing document cannot answer from it, however capable the model is.
# Which files it read are recorded per item so a miss can be attributed.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "spikes" / "ps-eval"))
import corpus_l5 as corpus  # noqa: E402
from questions_l5 import QUESTIONS_L5, grade_answer_l5  # noqa: E402

PROMPT = (
    "The documents in this directory are the complete record for a contract "
    "dispute. Read whichever files you need, then answer this question.\n\n"
    "QUESTION: {q}\n\n"
    "Answer with the specific value asked for. If the documents do not state "
    "it, say that they do not state it - do not infer or estimate.\n"
    "Put your final answer on the last line, prefixed exactly with 'ANSWER: '."
)


def write_docs(root: Path) -> list[str]:
    """The ten documents, one file each, names a reader would recognise."""
    root.mkdir(parents=True, exist_ok=True)
    names = []
    for attr in sorted(a for a in dir(corpus)
                       if not a.startswith("_")
                       and isinstance(getattr(corpus, a), str)
                       and len(getattr(corpus, a)) > 200):
        fn = attr.lower() + ".md"
        (root / fn).write_text(getattr(corpus, attr))
        names.append(fn)
    if len(names) != 10:
        raise SystemExit(
            f"expected 10 documents, wrote {len(names)}: {names}. hint: the "
            f"corpus changed shape; a partial pack would score as capability."
        )
    return names


def extract(text: str) -> str:
    for line in reversed(text.splitlines()):
        if line.strip().upper().startswith("ANSWER:"):
            return line.split(":", 1)[1].strip()
    return text.strip().splitlines()[-1].strip() if text.strip() else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--harness", required=True, choices=["hermes"])
    ap.add_argument("--workdir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--timeout", type=float, default=600.0)
    ap.add_argument("--only", default=None, help="comma-separated question ids")
    a = ap.parse_args()

    root = Path(a.workdir)
    docs = write_docs(root)
    print(f"wrote {len(docs)} documents to {root}", flush=True)

    qs = QUESTIONS_L5
    if a.only:
        want = {s.strip() for s in a.only.split(",")}
        qs = [q for q in qs if q["id"] in want]

    results = []
    for i, q in enumerate(qs, 1):
        t0 = time.time()
        try:
            p = subprocess.run(
                ["hermes", "-z", PROMPT.format(q=q["question"]), "--yolo"],
                cwd=root, capture_output=True, text=True, timeout=a.timeout)
            out, rc = p.stdout or "", p.returncode
        except subprocess.TimeoutExpired:
            out, rc = "", None
        ans = extract(out)
        if not ans:
            outcome = "transport_failed" if rc is None else "format_error"
        else:
            outcome = grade_answer_l5(q, ans)
            if isinstance(outcome, tuple):
                outcome = outcome[0]
        # Which documents it actually opened - the retrieval evidence P3 needs.
        read = sorted({d for d in docs if d in out})
        results.append({"id": q["id"], "band": q["band"], "outcome": outcome,
                        "answer": ans[:300], "docs_mentioned": read,
                        "rc": rc, "wall_s": round(time.time() - t0, 1)})
        print(f"  [{i}/{len(qs)}] {q['id']:5s} {outcome:16s} "
              f"docs={len(read)} {results[-1]['wall_s']}s", flush=True)

    correct = sum(1 for r in results if r["outcome"] == "correct")
    summary = {
        "harness": a.harness, "n": len(results), "correct": correct,
        "over_claim": sum(1 for r in results if r["outcome"] == "over_claim"),
        "band_R": sum(1 for r in results if r["band"] == "R" and r["outcome"] == "correct"),
        "band_E": sum(1 for r in results if r["band"] == "E" and r["outcome"] == "correct"),
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": results,
    }
    Path(a.out).write_text(json.dumps(summary, indent=2))
    print(f"\n{correct}/{len(results)} correct "
          f"(band R {summary['band_R']}/12, band E {summary['band_E']}/12, "
          f"over_claim {summary['over_claim']}). wrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
