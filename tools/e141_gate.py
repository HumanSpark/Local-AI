#!/usr/bin/env python3
# File: e141_gate.py
# Purpose: E141 runner - escalation gates and a workhorse effort router in front of the 27B, on L3-hard through the live gateway.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: results/e141-prereg.md registers the arms. Per item, in order: O (27B off), L (27B
# low), W (workhorse, logprobs), the G-self check, G-self's escalation if taken, G-lp's
# escalation if taken, the R router call, then R's 27B call at the chosen effort. Every call goes
# through e140_cascade's overlap watch and idle wait, so E140 amendment 1's conditions hold
# unchanged. `score` composes the arms from the banked calls and prints every P-field and band;
# arm M is E140's arm A, read from results/e140/calls.jsonl.

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e140_cascade as c  # noqa: E402

OUT = c.ROOT / "results" / "e141" / "calls.jsonl"
E140 = c.ROOT / "results" / "e140" / "calls.jsonl"
LP_THRESHOLD = 0.90

CHECK_TAIL = """
=== DRAFT ANSWER ===
{draft}

Is the draft answer correct according to the engagement pack? Reply with exactly one word: \
CONFIDENT if you are certain it is correct, ESCALATE otherwise.
"""
ROUTER_TAIL = """
You are routing this question to a strong reasoning model. How much reasoning does it need to \
answer correctly? Reply with exactly one word: off (lookup, no reasoning), low (brief \
reasoning), or medium (careful multi-step reasoning).
"""


def call(
    model: str, prompt: str, effort: str | None, max_tokens: int, logprobs: bool = False
) -> dict:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": False,
        "cache_prompt": False,
    }
    if effort == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    elif effort is not None:
        payload["reasoning_effort"] = effort
    if logprobs:
        payload["logprobs"] = True
        payload["top_logprobs"] = 1
    req = urllib.request.Request(
        f"{c.GATEWAY}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with c.SlotWatch(model) as watch:
        t0 = time.time()
        with urllib.request.urlopen(
            req, timeout=c.resolve_request_timeout(None, max_tokens)
        ) as r:
            body = json.load(r)
        wall = round(time.time() - t0, 2)
    ch = body["choices"][0]
    lp = (ch.get("logprobs") or {}).get("content") if logprobs else None
    return {
        "content": ch["message"].get("content") or "",
        "reasoning_chars": len(ch["message"].get("reasoning_content") or ""),
        "finish_reason": ch["finish_reason"],
        "usage": body["usage"],
        "wall_s": wall,
        "tokens": [[t["token"], t["logprob"]] for t in lp] if lp else None,
        "overlap": watch.overlap,
        "slot_samples": watch.samples,
        "slot_errors": watch.errors,
    }


def answer_min_prob(tokens: list[list]) -> float:
    """Minimum token probability over the ANSWER line (tokens after 'ANSWER:' up to a newline)."""
    text, probs, started = "", [], False
    for tok, lp in tokens:
        if started:
            if "\n" in tok:
                break
            probs.append(math.exp(lp))
        text += tok
        if not started and "ANSWER:" in text:
            started = True
    if not probs:
        raise ValueError(
            f"no ANSWER-line tokens in {text[:80]!r}. "
            f"hint: the workhorse broke the two-line format; G-lp cannot score this item"
        )
    return min(probs)


def parse_route(text: str) -> str:
    m = re.search(r"\b(off|low|medium)\b", text.lower())
    return (
        m.group(1) if m else "low"
    )  # registered fallback: unparseable routes to the baseline


def run() -> None:
    pack = c.build_pack_l3(0)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    done = c.load(OUT)
    t_run = time.time()

    def do(
        q: dict,
        arm: str,
        model: str,
        prompt: str,
        effort: str | None,
        max_tokens: int,
        logprobs: bool = False,
        extra: dict | None = None,
    ) -> dict:
        if (q["id"], arm) in done:
            return done[(q["id"], arm)]
        for attempt in range(1, 5):
            c.wait_idle(1800)
            try:
                resp = call(model, prompt, effort, max_tokens, logprobs)
            except OSError as exc:
                rec = {
                    "id": q["id"],
                    "arm": arm,
                    "valid": False,
                    "void": f"transport: {exc}",
                }
            else:
                answer, citation = c.parse_response(resp["content"])
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
                    "model": model,
                    "effort": effort,
                    "valid": void is None,
                    "void": void,
                    "grade": grade,
                    "answer": answer,
                    "attempt": attempt,
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                    **(extra or {}),
                    **resp,
                }
            with OUT.open("a") as f:
                f.write(json.dumps(rec) + "\n")
            print(
                f"  {q['id']} {arm:9s} {rec.get('grade', '-'):17s} {rec.get('wall_s', '-')}s "
                f"void={rec['void']} {str(rec.get('content', ''))[:40]!r}  elapsed {time.time() - t_run:.0f}s",
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
        do(q, "O", c.SMART, base, "off", c.MAX_TOKENS)
        do(q, "L", c.SMART, base, "low", c.MAX_TOKENS)
        w = do(q, "W", c.FAST, base, None, c.MAX_TOKENS, logprobs=True)
        chk = do(
            q,
            "G-self.check",
            c.FAST,
            base + CHECK_TAIL.format(draft=w["content"]),
            None,
            16,
        )
        if "CONFIDENT" not in chk["content"].upper():
            do(q, "G-self.esc", c.SMART, base, "low", c.MAX_TOKENS)
        if w["tokens"] is None or answer_min_prob(w["tokens"]) < LP_THRESHOLD:
            do(q, "G-lp.esc", c.SMART, base, "low", c.MAX_TOKENS)
        route = do(q, "R.route", c.FAST, base + ROUTER_TAIL, None, 16)
        effort = parse_route(route["content"])
        do(q, "R.exec", c.SMART, base, effort, c.MAX_TOKENS, extra={"route": effort})
    print(f"run complete in {time.time() - t_run:.0f}s")


def score() -> None:
    d = c.load(OUT)
    m = c.load(E140)
    ids = [q["id"] for q in c.QUESTIONS_L3]
    ok = lambda r: r["grade"] == "correct"  # noqa: E731
    res: dict[str, dict] = {}
    res["M"] = {
        "correct": sum(ok(m[(i, "A")]) for i in ids),
        "wall": sum(m[(i, "A")]["wall_s"] for i in ids),
    }
    for a in ("L", "O", "W"):
        res[a] = {
            "correct": sum(ok(d[(i, a)]) for i in ids),
            "wall": sum(d[(i, a)]["wall_s"] for i in ids),
        }
    for g in ("G-self", "G-lp", "G-oracle"):
        corr = wall = shipped_wrong = esc = 0
        for i in ids:
            w = d[(i, "W")]
            wall += w["wall_s"]
            if g == "G-self":
                wall += d[(i, "G-self.check")]["wall_s"]
            key = {"G-self": "G-self.esc", "G-lp": "G-lp.esc"}.get(g)
            escalated = (not ok(w)) if g == "G-oracle" else (i, key) in d
            if escalated:
                esc += 1
                e = d[(i, "L")] if g == "G-oracle" else d[(i, key)]
                wall += e["wall_s"]
                corr += ok(e)
            else:
                corr += ok(w)
                shipped_wrong += not ok(w)
        res[g] = {
            "correct": corr,
            "wall": wall,
            "shipped_wrong": shipped_wrong,
            "escalated": esc,
        }
    routes = [d[(i, "R.exec")]["route"] for i in ids]
    res["R"] = {
        "correct": sum(ok(d[(i, "R.exec")]) for i in ids),
        "wall": sum(
            d[(i, "R.route")]["wall_s"] + d[(i, "R.exec")]["wall_s"] for i in ids
        ),
        "routes": {k: routes.count(k) for k in ("off", "low", "medium")},
    }
    for k, v in res.items():
        print(
            f"{k:9s} "
            + "  ".join(
                f"{a}={round(b, 1) if isinstance(b, float) else b}"
                for a, b in v.items()
            )
        )
    L = res["L"]
    print("\nP1 L.correct", L["correct"])
    print("P2 L/M wall", round(L["wall"] / res["M"]["wall"], 3))
    print("P3 O.correct", res["O"]["correct"])
    print("P4 W.correct", res["W"]["correct"])
    print("P5 G-self.shipped_wrong", res["G-self"]["shipped_wrong"])
    print("P6 G-lp.shipped_wrong", res["G-lp"]["shipped_wrong"])
    print("P7 G-oracle/L wall", round(res["G-oracle"]["wall"] / L["wall"], 3))
    print("P8 R.correct", res["R"]["correct"])
    print("P9 R/L wall", round(res["R"]["wall"] / L["wall"], 3))
    for g in ("G-self", "G-lp"):
        r = res[g]
        band = (
            "REJECT"
            if r["shipped_wrong"] >= 1
            else "ADOPT"
            if r["correct"] >= L["correct"] and r["wall"] <= 0.80 * L["wall"]
            else "INCONCLUSIVE"
        )
        print(f"band {g}: {band}")
    r = res["R"]
    band = (
        "REJECT"
        if r["correct"] < L["correct"] or r["wall"] > 0.95 * L["wall"]
        else "ADOPT"
        if r["wall"] <= 0.85 * L["wall"]
        else "INCONCLUSIVE"
    )
    print(f"band R: {band}")
    print("\nG-lp descriptive sweep (min ANSWER-line prob, W grade):")
    for i in ids:
        w = d[(i, "W")]
        print(
            f"  {i} {answer_min_prob(w['tokens']) if w['tokens'] else None!s:22s} {w['grade']}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E141: escalation gates and effort router (results/e141-prereg.md).",
        epilog="examples:\n  tools/e141_gate.py run\n  tools/e141_gate.py score",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("cmd", choices=["run", "score"])
    args = ap.parse_args()
    run() if args.cmd == "run" else score()
    return 0


if __name__ == "__main__":
    sys.exit(main())
