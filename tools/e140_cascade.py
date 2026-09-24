#!/usr/bin/env python3
# File: e140_cascade.py
# Purpose: E140 runner - L3-hard through the live gateway as five arms: 27B alone, workhorse alone, and three draft-then-27B-review arms.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: results/e140-prereg.md registers the design; amendment 1 there
# declares everything this file pins down. Three subcommands:
#
#   selftest  no network. Grades every planted draft with the unchanged
#             grade_answer_l3 and refuses to continue unless each FLAW draft
#             grades to its registered trap and each CORRECT draft grades
#             correct. A planted draft that does not spring its trap would
#             make D measure nothing, silently.
#   run       for each item in bank order: A, B, C, D, E. Interleaved by item
#             so a drift in production traffic over the run hits every arm
#             alike. One JSONL line per call, appended as it lands, so an
#             interrupted run resumes by skipping calls already banked VALID.
#   score     reads the JSONL and prints every field P1-P10 names, plus the
#             registered decision band.
#
# Every call polls /slots on all three residents at 1 Hz while it runs. Any
# processing slot beyond our own marks the call `overlap`: void, re-run once the
# gateway is idle again. `cache_prompt: false` on every request, so no arm rides
# a pack prefix another arm paid for. Grading imports the banked grader and
# parser; nothing here re-implements scoring.

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import threading
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))
sys.path.insert(0, str(ROOT / "tools"))
from corpus_l3 import build_pack_l3  # noqa: E402
from questions import _matches, _numbers, grade_citation, parse_response  # noqa: E402
from questions_l3 import QUESTIONS_L3, grade_answer_l3  # noqa: E402
from run_ps_eval import PROMPT_TEMPLATE, resolve_request_timeout  # noqa: E402

GATEWAY = "http://127.0.0.1:8400"
FAST, SMART = "local_fast", "local_smart"
RESIDENTS = ("local_fast", "local_smart", "local_code")
MAX_TOKENS = 8192
ARMS = ("A", "B", "C", "D", "E")
DEFAULT_OUT = ROOT / "results" / "e140" / "calls.jsonl"

# The review template is PROMPT_TEMPLATE plus one section, so a reviewer sees
# the same rules, pack and output format as arm A. Neutral on purpose: it says
# neither "may be wrong" nor "is probably right" (prereg, Arms).
REVIEW_TEMPLATE = (
    PROMPT_TEMPLATE
    + """
=== DRAFT ANSWER ===
A colleague has drafted an answer to this question. Review it against the \
engagement pack and give your own final answer in the two-line format above.

{draft}
"""
)

# Planted drafts in the SAME two-line envelope the workhorse emits, so C and D
# differ in content only (amendment 1, item 1). Values are the prereg's table.
# `planted` is what makes an answer ANCHORED; `expect` is the grade the
# selftest demands of the draft itself.
FLAW: dict[str, dict] = {
    "D1": {
        "text": "ANSWER: EUR 46,500\nCITATION: AMD-1 clause 1 (replacing MSA-2024 clause 2.1)",
        "planted": 46500,
        "expect": "premature",
    },
    "D2": {
        "text": "ANSWER: EUR 1,250,000\nCITATION: AMD-2 clause 1 (replacing MSA-2024 clause 4.1)",
        "planted": 1250000,
        "expect": "premature",
    },
    "D3": {
        "text": "ANSWER: EUR 46,500\nCITATION: AMD-1 clause 1 (replacing MSA-2024 clause 2.1)",
        "planted": 46500,
        "expect": "stale_value",
    },
    "V1": {
        "text": "ANSWER: 12 months\nCITATION: AMD-2 clause 3 (replacing MSA-2024 clause 5.2)",
        "planted": 12,
        "expect": "stale_value",
    },
    "V2": {
        "text": "ANSWER: NO\nCITATION: AMD-3 clause 3; MSA-2024 clause 4.2",
        "planted": "no",
        "expect": "wrong",
    },
    "P1": {
        "text": "ANSWER: 24 months\nCITATION: AMD-3 clause 1 (reinstating MSA-2024 clause 5.2)",
        "planted": 24,
        "expect": "precedence_missed",
    },
    "P2": {
        "text": "ANSWER: 1 business day\nCITATION: POL-3.1 P-2.3",
        "planted": 1,
        "expect": "over_applied",
    },
    "M1": {
        "text": "ANSWER: EUR 418,500\nCITATION: MSA-2024 clauses 2.1 and 3.1; AMD-1 clause 1",
        "planted": 418500,
        "expect": "premature",
    },
    "M2": {
        "text": "ANSWER: EUR 139,500\nCITATION: AMD-1 clauses 1 and 2",
        "planted": 139500,
        "expect": "stale_value",
    },
    "M3": {
        "text": "ANSWER: 26.9\nCITATION: AMD-2 clause 1; AMD-1 clause 1",
        "planted": 26.9,
        "expect": "wrong",
    },
    "N1": {"text": "ANSWER: (a)\nCITATION: NONE", "planted": "a", "expect": "wrong"},
    "Z1": {
        "text": "ANSWER: Yes, VAT is chargeable at the standard rate of 23%\nCITATION: MSA-2024 clause 6.3",
        "planted": "over_claim",
        "expect": "over_claim",
    },
}
CORRECT: dict[str, str] = {
    "D1": "ANSWER: EUR 42,000\nCITATION: MSA-2024 clause 2.1",
    "D2": "ANSWER: EUR 500,000\nCITATION: MSA-2024 clause 4.1",
    "D3": "ANSWER: EUR 51,000\nCITATION: AMD-3 clause 2 (replacing MSA-2024 clause 2.1)",
    "V1": "ANSWER: 24 months\nCITATION: AMD-3 clause 1 (reinstating MSA-2024 clause 5.2)",
    "V2": "ANSWER: YES\nCITATION: AMD-3 clause 3; MSA-2024 clause 4.2",
    "P1": "ANSWER: 6 months\nCITATION: SIDE-1 paragraph 1; POL-3.1 P-4.2",
    "P2": "ANSWER: 2 business days\nCITATION: SIDE-1 paragraph 2; MSA-2024 clause 6.1",
    "M1": "ANSWER: EUR 378,000\nCITATION: MSA-2024 clauses 2.1 and 3.1",
    "M2": "ANSWER: EUR 445,500\nCITATION: AMD-1 clause 2; AMD-3 clauses 1.2 and 2.1",
    "M3": "ANSWER: 24.5\nCITATION: AMD-2 clause 1; AMD-3 clause 2",
    "N1": "ANSWER: (d)\nCITATION: NONE",
    "Z1": "ANSWER: NOT_IN_PACK\nCITATION: NONE",
}


def selftest() -> None:
    bad = []
    for q in QUESTIONS_L3:
        fl = grade_answer_l3(q, parse_response(FLAW[q["id"]]["text"])[0])
        ok = grade_answer_l3(q, parse_response(CORRECT[q["id"]])[0])
        if fl != FLAW[q["id"]]["expect"]:
            bad.append(
                f"{q['id']} flaw grades {fl!r}, registered {FLAW[q['id']]['expect']!r}"
            )
        if ok != "correct":
            bad.append(f"{q['id']} correct draft grades {ok!r}")
        if not is_anchored(q, parse_response(FLAW[q["id"]]["text"])[0], fl):
            bad.append(
                f"{q['id']} flaw draft is not detected as anchored by is_anchored"
            )
        print(f"  {q['id']}  flaw={fl:18s} correct={ok}")
    if bad:
        raise SystemExit(
            "selftest FAILED:\n  "
            + "\n  ".join(bad)
            + "\nhint: fix the draft text, never the grader - the grader is banked"
        )
    print(
        f"selftest passed: {len(QUESTIONS_L3)} flaw and {len(QUESTIONS_L3)} correct drafts grade as registered"
    )


def is_anchored(q: dict, answer: str | None, grade: str) -> bool:
    """True when a non-correct final answer is the PLANTED answer (prereg, Arms)."""
    if grade == "correct" or answer is None:
        return False
    planted = FLAW[q["id"]]["planted"]
    if planted == "over_claim":
        return grade == "over_claim"
    if planted in ("no", "a"):
        # Same test grade_answer_l2 applies to yes_no and choice answers.
        return re.match(rf"\s*\(?{planted}\b", answer.lower()) is not None
    return _matches(_numbers(answer), [planted], 0.001, 0.051)


class SlotWatch:
    """Polls /slots on every resident at 1 Hz; `overlap` if anyone else is busy."""

    def __init__(self, target: str) -> None:
        self.target, self.overlap, self.samples, self.errors = target, False, 0, 0
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._loop, daemon=True)

    def sample(self) -> None:
        busy = busy_slots()
        if busy is None:
            self.errors += 1
            return
        self.samples += 1
        others = sum(n for m, n in busy.items() if m != self.target)
        if others > 0 or busy.get(self.target, 0) > 1:
            self.overlap = True

    def _loop(self) -> None:
        # Sample FIRST, then every second: a workhorse call can finish inside
        # one second, and a watcher that only sampled after a wait would record
        # zero samples and void every B call.
        while True:
            self.sample()
            if self._stop.wait(1.0):
                return

    def __enter__(self) -> SlotWatch:
        self._t.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        self._t.join(timeout=10)
        self.sample()  # one after the response, so every call has >= 1 sample


def busy_slots() -> dict[str, int] | None:
    """Processing-slot count per resident, or None if the gateway did not answer.

    None is a real, expected outcome during a poll (the caller counts it and a
    call with no successful sample is void), not a sentinel for "idle".
    """
    out = {}
    for m in RESIDENTS:
        try:
            with urllib.request.urlopen(f"{GATEWAY}/slots?model={m}", timeout=5) as r:
                out[m] = sum(1 for s in json.load(r) if s["is_processing"])
        except OSError:
            return None
    return out


def wait_idle(max_wait_s: float) -> None:
    t0 = time.time()
    while True:
        busy = busy_slots()
        if busy is not None and not any(busy.values()):
            return
        if time.time() - t0 > max_wait_s:
            raise SystemExit(
                f"gateway not idle after {max_wait_s:.0f}s (last: {busy}). "
                f"hint: production traffic is running; re-run later, the JSONL resumes"
            )
        print(
            f"    waiting for an idle gateway ({busy}), {time.time() - t0:.0f}s",
            flush=True,
        )
        time.sleep(10)


def call(model: str, prompt: str, timeout: float) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": MAX_TOKENS,
        "stream": False,
        "cache_prompt": False,
    }
    if model == SMART:
        payload["reasoning_effort"] = "medium"
    req = urllib.request.Request(
        f"{GATEWAY}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with SlotWatch(model) as watch:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.load(r)
        wall = round(time.time() - t0, 2)
    choice = body["choices"][0]
    return {
        "content": choice["message"].get("content") or "",
        "reasoning_chars": len(choice["message"].get("reasoning_content") or ""),
        "finish_reason": choice["finish_reason"],
        "usage": body["usage"],
        "model_reported": body.get("model"),
        "wall_s": wall,
        "overlap": watch.overlap,
        "slot_samples": watch.samples,
        "slot_errors": watch.errors,
    }


def load(out: Path) -> dict[tuple[str, str], dict]:
    """Latest VALID record per (item, arm). Void records stay in the file as evidence."""
    done: dict[tuple[str, str], dict] = {}
    if out.exists():
        for line in out.read_text().splitlines():
            rec = json.loads(line)
            if rec["valid"]:
                done[(rec["id"], rec["arm"])] = rec
    return done


def run(out: Path, max_wait_s: float, retries: int) -> None:
    selftest()
    pack = build_pack_l3(0)
    timeout = resolve_request_timeout(None, MAX_TOKENS)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = load(out)
    todo = [(q, a) for q in QUESTIONS_L3 for a in ARMS if (q["id"], a) not in done]
    print(f"{len(done)} calls banked, {len(todo)} to run -> {out}", flush=True)
    t_run = time.time()
    for n, (q, arm) in enumerate(todo, 1):
        base = PROMPT_TEMPLATE.format(pack=pack, question=q["question"])
        if arm == "C":
            draft = done[(q["id"], "B")]["content"]
        elif arm == "D":
            draft = FLAW[q["id"]]["text"]
        elif arm == "E":
            draft = CORRECT[q["id"]]
        else:
            draft = None
        prompt = (
            base
            if draft is None
            else REVIEW_TEMPLATE.format(pack=pack, question=q["question"], draft=draft)
        )
        model = FAST if arm == "B" else SMART
        for attempt in range(1, retries + 2):
            wait_idle(max_wait_s)
            try:
                resp = call(model, prompt, timeout)
            except OSError as exc:
                rec = {
                    "id": q["id"],
                    "arm": arm,
                    "valid": False,
                    "void": f"transport: {exc}",
                }
            else:
                answer, citation = parse_response(resp["content"])
                grade = (
                    "truncated"
                    if resp["finish_reason"] == "length"
                    else grade_answer_l3(q, answer)
                )
                void = (
                    "overlap"
                    if resp["overlap"]
                    else "no slot sample"
                    if resp["slot_samples"] == 0
                    else None
                )
                rec = {
                    "id": q["id"],
                    "arm": arm,
                    "model": model,
                    "valid": void is None,
                    "void": void,
                    "grade": grade,
                    "answer": answer,
                    "citation": citation,
                    "citation_ok": grade_citation(q, citation),
                    "anchored": arm == "D" and is_anchored(q, answer, grade),
                    "draft": draft,
                    "content": resp["content"],
                    "attempt": attempt,
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    **{
                        k: resp[k]
                        for k in (
                            "wall_s",
                            "reasoning_chars",
                            "finish_reason",
                            "usage",
                            "model_reported",
                            "slot_samples",
                            "slot_errors",
                        )
                    },
                }
            with out.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            print(
                f"  [{n}/{len(todo)}] {q['id']} {arm} {rec.get('grade', '-'):17s} "
                f"{rec.get('wall_s', '-')}s  void={rec['void']}  elapsed {time.time() - t_run:.0f}s",
                flush=True,
            )
            if rec["valid"]:
                done[(q["id"], arm)] = rec
                break
        else:
            raise SystemExit(
                f"{q['id']} {arm} void on all {retries + 1} attempts. "
                f"hint: read the void reasons in {out}; the run resumes from here"
            )
    print(f"run complete in {time.time() - t_run:.0f}s")


def score(out: Path) -> None:
    done = load(out)
    ids = [q["id"] for q in QUESTIONS_L3]
    missing = [(i, a) for i in ids for a in ARMS if (i, a) not in done]
    if missing:
        raise SystemExit(
            f"{len(missing)} calls not banked, first {missing[:5]}. "
            f"hint: finish `run` before scoring - a partial arm is not an arm"
        )
    r = {a: [done[(i, a)] for i in ids] for a in ARMS}
    correct = {a: sum(x["grade"] == "correct" for x in r[a]) for a in ARMS}
    wall = {a: sum(x["wall_s"] for x in r[a]) for a in ARMS}
    wall["C"] += wall["B"]  # the draft is paid for: TTCA for C spans both calls
    b_wrong = [i for i, x in zip(ids, r["B"]) if x["grade"] != "correct"]
    caught = sum(done[(i, "C")]["grade"] == "correct" for i in b_wrong)
    anchored = sum(x["anchored"] for x in r["D"])
    over = sum(x["grade"] != "correct" for x in r["E"])
    trunc = {a: sum(x["grade"] == "truncated" for x in r[a]) for a in ARMS}
    med = {
        a: statistics.median(x["usage"]["completion_tokens"] for x in r[a])
        for a in ("D", "E")
    }
    fields = {
        "P1 A.correct": correct["A"],
        "P2 B.correct": correct["B"],
        "P3 C.correct": correct["C"],
        "P4 C.caught": f"{caught}/{len(b_wrong)}",
        "P5 C.total_wall_s / A.total_wall_s": round(wall["C"] / wall["A"], 3),
        "P6 D.anchored": anchored,
        "P7 D.correct": correct["D"],
        "P8 E.overcorrected": over,
        "P9 median D.completion_tokens > median E": f"{med['D']} > {med['E']} = {med['D'] > med['E']}",
        "P10 E.total_wall_s / A.total_wall_s": round(wall["E"] / wall["A"], 3),
    }
    for k, v in fields.items():
        print(f"{k:42s} {v}")
    print(
        f"{'total_wall_s (C includes B)':42s} { ({a: round(v, 1) for a, v in wall.items()}) }"
    )
    print(f"{'truncated per arm':42s} {trunc}")
    print(f"{'grades D':42s} {[x['grade'] for x in r['D']]}")
    ratio = wall["C"] / wall["A"]
    if anchored >= 3:
        band = "REJECT (anchoring)"
    elif ratio > 0.95:
        band = "REJECT (speed)"
    elif correct["C"] >= correct["A"] and ratio <= 0.80 and anchored <= 1:
        band = "ADOPT as a hard-route candidate"
    else:
        band = "INCONCLUSIVE"
    print(f"{'decision band':42s} {band}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E140 cascade runner: L3-hard, five arms, live gateway (results/e140-prereg.md).",
        epilog="examples:\n  tools/e140_cascade.py selftest\n  tools/e140_cascade.py run\n"
        "  tools/e140_cascade.py score",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("cmd", choices=["selftest", "run", "score"])
    ap.add_argument(
        "--out", type=Path, default=DEFAULT_OUT, help="JSONL of calls (append + resume)"
    )
    ap.add_argument(
        "--max-wait",
        type=float,
        default=1800,
        help="seconds to wait for an idle gateway per call",
    )
    ap.add_argument(
        "--retries", type=int, default=3, help="re-runs of a void (overlapped) call"
    )
    args = ap.parse_args()
    if args.cmd == "selftest":
        selftest()
    elif args.cmd == "run":
        run(args.out, args.max_wait, args.retries)
    else:
        score(args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
