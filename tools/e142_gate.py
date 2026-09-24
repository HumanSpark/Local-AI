#!/usr/bin/env python3
# File: e142_gate.py
# Purpose: E142 runner - 27B `off` as first stage of an escalate-or-ship gate (logprob and self-check) on L3-hard through the live gateway.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: results/e142-prereg.md registers the arms. Per item: O2 (27B off, logprobs), the
# H-self check (27B off), H-self escalation and H-lp escalation (27B low) if taken. Reuses
# e141_gate.call / answer_min_prob / CHECK_TAIL and e140_cascade's overlap watch, so E140
# amendment 1 conditions hold. Baseline L is E141's arm L, read from results/e141/calls.jsonl.

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e140_cascade as c  # noqa: E402
import e141_gate as g  # noqa: E402

OUT = c.ROOT / "results" / "e142" / "calls.jsonl"
E141 = c.ROOT / "results" / "e141" / "calls.jsonl"


def run() -> None:
    pack = c.build_pack_l3(0)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = c.load(OUT)
    t_run = time.time()

    def do(
        q: dict, arm: str, prompt: str, effort: str, max_tokens: int, lp: bool = False
    ) -> dict:
        if (q["id"], arm) in done:
            return done[(q["id"], arm)]
        for attempt in range(1, 5):
            c.wait_idle(1800)
            try:
                resp = g.call(c.SMART, prompt, effort, max_tokens, lp)
            except OSError as exc:
                rec = {
                    "id": q["id"],
                    "arm": arm,
                    "valid": False,
                    "void": f"transport: {exc}",
                }
            else:
                answer, _ = c.parse_response(resp["content"])
                grade = (
                    "truncated"
                    if resp["finish_reason"] == "length"
                    else c.grade_answer_l3(q, answer)
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
                    "model": c.SMART,
                    "effort": effort,
                    "valid": void is None,
                    "void": void,
                    "grade": grade,
                    "answer": answer,
                    "attempt": attempt,
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    **resp,
                }
            with OUT.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            print(
                f"  {q['id']} {arm:12s} {rec.get('grade', '-'):17s} {rec.get('wall_s', '-')}s "
                f"void={rec['void']} elapsed {time.time() - t_run:.0f}s",
                flush=True,
            )
            if rec["valid"]:
                done[(q["id"], arm)] = rec
                return rec
        raise SystemExit(
            f"{q['id']} {arm} void 4 times. hint: read {OUT}; the run resumes"
        )

    for q in c.QUESTIONS_L3:
        base = c.PROMPT_TEMPLATE.format(pack=pack, question=q["question"])
        o = do(q, "O2", base, "off", c.MAX_TOKENS, lp=True)
        chk = do(
            q, "H-self.check", base + g.CHECK_TAIL.format(draft=o["content"]), "off", 16
        )
        if "CONFIDENT" not in chk["content"].upper():
            do(q, "H-self.esc", base, "low", c.MAX_TOKENS)
        if o["tokens"] is None or g.answer_min_prob(o["tokens"]) < g.LP_THRESHOLD:
            do(q, "H-lp.esc", base, "low", c.MAX_TOKENS)
    print(f"run complete in {time.time() - t_run:.0f}s")


def score() -> None:
    d, b = c.load(OUT), c.load(E141)
    ids = [q["id"] for q in c.QUESTIONS_L3]
    ok = lambda r: r["grade"] == "correct"  # noqa: E731
    L = {
        "correct": sum(ok(b[(i, "L")]) for i in ids),
        "wall": sum(b[(i, "L")]["wall_s"] for i in ids),
    }
    O2 = {
        "correct": sum(ok(d[(i, "O2")]) for i in ids),
        "wall": sum(d[(i, "O2")]["wall_s"] for i in ids),
    }
    print(f"L(E141)  {L}\nO2       {O2}")
    res = {}
    for gate in ("H-self", "H-lp", "H-oracle"):
        corr = wall = sw = esc = 0
        for i in ids:
            o = d[(i, "O2")]
            wall += o["wall_s"] + (
                d[(i, "H-self.check")]["wall_s"] if gate == "H-self" else 0
            )
            key = {"H-self": "H-self.esc", "H-lp": "H-lp.esc"}.get(gate)
            escalated = (not ok(o)) if gate == "H-oracle" else (i, key) in d
            if escalated:
                esc += 1
                e = b[(i, "L")] if gate == "H-oracle" else d[(i, key)]
                wall += e["wall_s"]
                corr += ok(e)
            else:
                corr += ok(o)
                sw += not ok(o)
        res[gate] = {
            "correct": corr,
            "wall": round(wall, 1),
            "shipped_wrong": sw,
            "escalated": esc,
        }
        band = (
            "REJECT"
            if sw >= 1
            else "ADOPT"
            if corr == 12 and wall <= 0.80 * L["wall"]
            else "INCONCLUSIVE"
        )
        print(f"{gate:9s} {res[gate]}  ratio_vs_L={wall / L['wall']:.3f}  band={band}")
    print("\nP1 O2.correct", O2["correct"], "| P2 O2.wall", round(O2["wall"], 1))
    print(
        "P3 H-lp.shipped_wrong",
        res["H-lp"]["shipped_wrong"],
        "| P4 H-self.shipped_wrong",
        res["H-self"]["shipped_wrong"],
    )
    print(
        "P5 H-oracle/L",
        round(res["H-oracle"]["wall"] / L["wall"], 3),
        "| P6 H-lp.escalated",
        res["H-lp"]["escalated"],
    )
    print("\nsweep (min ANSWER-line prob, O2 grade):")
    for i in ids:
        o = d[(i, "O2")]
        p = g.answer_min_prob(o["tokens"]) if o["tokens"] else None
        print(f"  {i} {p!s:22s} {o['grade']}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E142: 27B-off first-stage gate (results/e142-prereg.md).",
        epilog="examples:\n  tools/e142_gate.py run\n  tools/e142_gate.py score",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("cmd", choices=["run", "score"])
    args = ap.parse_args()
    run() if args.cmd == "run" else score()
    return 0


if __name__ == "__main__":
    sys.exit(main())
