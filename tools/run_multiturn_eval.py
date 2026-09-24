#!/usr/bin/env python3
# File: run_multiturn_eval.py
# Purpose: Run the multi-turn conversation against a served model, keeping full history, graded without a judge.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: Sends spikes/ps-eval/conversation_l4.py one turn at a time,
# resending the WHOLE conversation each turn as a chat client does, and grades
# the turns that carry a key. Mirrors run_ps_eval.py: Rule 1 HTTP-only serving,
# Rule 2 timeouts everywhere, Rule 3 full-offload gate that FAILS on zero
# evidence, Rule 9 quiet-GPU check, Rule 11 context preflight.
#
# THE CONTEXT PREFLIGHT WORKS DIFFERENTLY HERE, AND THIS IS THE INTERESTING
# PART. Rule 11 measures the longest prompt before the first request. In a
# conversation the longest prompt is the LAST one and it does not exist yet -
# it depends on how much the model has said. So the check runs in two places:
#
#   up front  every user turn concatenated, which is a LOWER BOUND, because it
#             excludes every assistant reply. Reported as a bound, never as a
#             pass.
#   per turn  before each request, the real history is measured and the run
#             REFUSES rather than letting llama-server silently drop the pack
#             off the front - which in a conversation is not a truncated answer
#             but a model that has quietly forgotten the engagement pack while
#             continuing to answer confidently.
#
# ONLY `content` GOES BACK INTO HISTORY, never `reasoning_content`. Feeding a
# model its own reasoning back is a different experiment with a different
# answer, and Qwen3.8's chat template does not do it either. Recorded here
# because it materially changes what is being measured.

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "ps-eval"))
from bench_context import assert_context_fits, count_tokens  # noqa: E402
from grade_multiturn import grade_multiturn  # noqa: E402
from questions import parse_response  # noqa: E402

# The conversation is chosen at run time, not imported at module scope. E55's
# script and E56's differ in length by design, so binding one of them here
# would make the runner an E55 runner that E56 had to fork - and a forked
# runner is two implementations of the Rule 11 preflight, which is exactly what
# the preflight consolidation existed to end.
# A value is either a module name (the module itself carries TURNS/GRADED/
# PROBES) or a (module, variant) pair for a conversation that comes in more
# than one order. E57 is a CROSSOVER - the same eighteen turns with the two
# halves swapped - so its two orders are one script parameterised, not two
# scripts that must be kept in step by hand.
CONVERSATIONS = {
    "l4": "conversation_l4",
    "long": "conversation_long",
    "heldout-ab": ("conversation_heldout", "ab"),
    "heldout-ba": ("conversation_heldout", "ba"),
}


def load_conversation(name: str):
    if name not in CONVERSATIONS:
        raise ValueError(
            f"unknown conversation {name!r}. "
            f"hint: one of {', '.join(sorted(CONVERSATIONS))}"
        )
    target = CONVERSATIONS[name]
    if isinstance(target, tuple):
        module, order = target
        return __import__(module).variant(order)
    return __import__(target)

DEFAULT_SERVER = "/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server"
ASSIGN_RE = __import__("re").compile(r"layer\s+\d+\s+assigned to device\s+([A-Za-z0-9_]+)")
MIN_TOKENS_PER_SEC = 6.0
TIMEOUT_MARGIN_S = 300.0


def wait_healthy(port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as r:
                if r.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001 - top-level poll boundary, retried below
            last = exc
        time.sleep(2)
    raise RuntimeError(
        f"server not healthy on port {port} within {timeout}s (last: {last}). "
        f"hint: read the server log for a load failure before assuming a port clash"
    )


def assert_full_offload(log_path: Path) -> dict:
    """Rule 3: zero offload evidence is a FAIL, never a pass."""
    text = log_path.read_text(errors="replace")
    devices = ASSIGN_RE.findall(text)
    if not devices:
        raise RuntimeError(
            f"full-offload gate FAILED: no 'assigned to device' lines in {log_path}. "
            f"hint: the server must run with -v or the gate cannot be evidenced"
        )
    on_cpu = [d for d in devices if d == "CPU"]
    if on_cpu:
        raise RuntimeError(
            f"full-offload gate FAILED: {len(on_cpu)}/{len(devices)} layers on CPU. "
            f"hint: raise -ngl or the figures are not a GPU measurement"
        )
    return {"layers_assigned": len(devices), "devices": sorted(set(devices))}


def resolve_request_timeout(explicit: float | None, max_tokens: int) -> float:
    """A timeout that can actually accommodate max_tokens at this box's slowest rate."""
    floor = max_tokens / MIN_TOKENS_PER_SEC + TIMEOUT_MARGIN_S
    if explicit is None:
        return round(floor)
    if explicit < floor:
        print(f"WARNING: --timeout {explicit:.0f}s is below the {floor:.0f}s needed for "
              f"max_tokens={max_tokens}. Turns that use the full budget will fail as "
              f"transport errors, not truncations, and produce no data at all.",
              file=sys.stderr)
    return explicit


def ask(port: int, messages: list[dict], max_tokens: int, timeout: float,
        thinking: str) -> dict:
    """One turn, sending the WHOLE conversation. Raises on transport failure."""
    payload: dict = {"messages": messages, "temperature": 0, "max_tokens": max_tokens}
    if thinking == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    elif thinking in ("low", "medium", "xhigh"):
        payload["reasoning_effort"] = thinking
    elif thinking != "default":
        raise ValueError(
            f"unknown thinking mode {thinking!r}. "
            f"hint: one of default, off, low, medium, xhigh"
        )
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    choice = d["choices"][0]
    msg = choice["message"]
    return {
        "content": msg.get("content") or "",
        "reasoning_chars": len(msg.get("reasoning_content") or ""),
        "finish_reason": choice.get("finish_reason"),
        "usage": d.get("usage", {}),
        "wall_s": round(time.time() - t0, 2),
    }


def render_messages(messages: list[dict]) -> str:
    """The history as one string, for token counting.

    An approximation of what the chat template will produce - it omits the
    per-message control tokens - so it UNDERSTATES by a handful of tokens per
    message. The preflight below adds a margin for that rather than pretending
    the number is exact.
    """
    return "\n".join(m["content"] for m in messages)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Multi-turn conversation eval over the L4 pack, graded without a judge.",
        epilog="example: python3 tools/run_multiturn_eval.py --model /opt/models/staging/x.gguf "
               "--label e55-qwen38 --out results/raw/e55-qwen38.json",
    )
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--conversation", default="l4", choices=sorted(CONVERSATIONS),
                    help="l4 = E55's 16-turn script; long = E56's 29-turn script "
                         "at real context pressure; heldout-ab / heldout-ba = "
                         "E57's crossover, questions asked ONLY once so the "
                         "model's own answer is never in the history")
    ap.add_argument("--server-bin", default=os.environ.get("SPARKBENCH_SERVER_BIN", DEFAULT_SERVER))
    ap.add_argument("--ctx", type=int, default=32768,
                    help="-c TOTAL; -np is 1 so this is the per-request budget (F20). "
                         "A conversation GROWS, so this needs headroom the "
                         "single-turn tiers do not")
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--thinking", default="default",
                    choices=["default", "off", "low", "medium", "xhigh"])
    ap.add_argument("--server-extra", default="", metavar="'FLAGS'",
                    help="extra llama-server flags as ONE quoted string. Recorded in the output.")
    ap.add_argument("--port", type=int, default=8117)
    ap.add_argument("--load-timeout", type=float, default=300.0)
    ap.add_argument("--request-timeout", type=float, default=None)
    # A conversation cannot skip a turn: turn N's prompt is turn N-1's answer
    # plus the next thing said. So a failed turn ends the run rather than being
    # recorded and stepped over, and the partial record is written out.
    ap.add_argument("--headroom", type=int, default=512,
                    help="tokens reserved for chat-template control tokens the "
                         "preflight's plain-text rendering cannot see")
    args = ap.parse_args()
    args.request_timeout = resolve_request_timeout(args.request_timeout, args.max_tokens)

    conv = load_conversation(args.conversation)
    TURNS, GRADED, PROBES = conv.TURNS, conv.GRADED, conv.PROBES
    anchor_pairs = getattr(conv, "ANCHOR_PAIRS", [])

    # Rule 9: one GPU consumer.
    for name in ("llama-server", "llama-bench"):
        r = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
        if r.stdout.strip():
            print(f"FAIL: {name} already running (pids: {r.stdout.split()}). "
                  f"hint: a busy GPU voids the timing columns of this run", file=sys.stderr)
            return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = out_path.with_suffix(".serverlog")
    base_url = f"http://127.0.0.1:{args.port}"

    cmd = [args.server_bin, "-m", args.model, "-c", str(args.ctx), "-np", "1",
           "--host", "127.0.0.1", "--port", str(args.port), "--no-webui", "-v"]
    cmd += shlex.split(args.server_extra)
    print(f"=== multi-turn eval: {args.label} ===")
    print(f"{len(TURNS)} turns, {len(GRADED)} graded, probes: {', '.join(PROBES)}")
    print(f"server: {' '.join(cmd)}")
    log_f = log_path.open("w")
    proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)

    results: list[dict] = []
    messages: list[dict] = []
    started = time.time()
    fit_final: dict = {"skipped": "run did not reach the last turn"}
    try:
        wait_healthy(args.port, args.load_timeout)
        gate = assert_full_offload(log_path)
        print(f"full-offload gate: {gate}")

        # Rule 11, adapted. This bound EXCLUDES every assistant reply, so it is
        # a floor on the final context and is labelled as one. It exists to
        # fail fast on a pack that could never fit at all.
        fit_bound = assert_context_fits(
            base_url, ["\n".join(t["say"] for t in TURNS)],
            args.max_tokens + args.headroom, args.ctx, args.request_timeout)
        print(f"context preflight (LOWER BOUND, excludes replies): {fit_bound}")

        for i, turn in enumerate(TURNS, 1):
            messages.append({"role": "user", "content": turn["say"]})
            # Per-turn hard check. In a conversation an overflow is not a
            # truncated answer, it is a model that has silently forgotten the
            # engagement pack and keeps answering confidently.
            n_hist = count_tokens(base_url, render_messages(messages), args.request_timeout)
            needed = n_hist + args.max_tokens + args.headroom
            if needed > args.ctx:
                raise RuntimeError(
                    f"context preflight FAILED at turn {turn['id']} ({i}/{len(TURNS)}): "
                    f"history is {n_hist:,} tokens, max_tokens {args.max_tokens:,}, "
                    f"headroom {args.headroom:,}, so the turn needs {needed:,} of "
                    f"-c {args.ctx:,}. hint: raise --ctx; a conversation that "
                    f"overflows does not truncate an answer, it silently drops the "
                    f"pack off the front and keeps answering"
                )
            resp = ask(args.port, messages, args.max_tokens, args.request_timeout,
                       args.thinking)
            messages.append({"role": "assistant", "content": resp["content"]})

            record = {
                "id": turn["id"], "turn": i, "probe": turn.get("probe"),
                "graded": "expect" in turn,
                "history_tokens": n_hist,
                "finish_reason": resp["finish_reason"],
                "completion_tokens": resp["usage"].get("completion_tokens"),
                "prompt_tokens": resp["usage"].get("prompt_tokens"),
                "reasoning_chars": resp["reasoning_chars"],
                "wall_s": resp["wall_s"],
            }
            if "expect" in turn:
                if resp["finish_reason"] == "length":
                    record.update(outcome="truncated", answer=None, citation=None)
                else:
                    answer, citation = parse_response(resp["content"])
                    record.update(outcome=grade_multiturn(turn, answer),
                                  answer=answer, citation=citation)
                print(f"  [{i:2}/{len(TURNS)}] {turn['id']} {turn.get('probe', ''):14} "
                      f"{record['outcome']:15} {str(record['answer'])[:34]:34} "
                      f"hist={n_hist:,} {resp['wall_s']}s")
            else:
                record.update(outcome="not_graded", answer=None, citation=None)
                print(f"  [{i:2}/{len(TURNS)}] {turn['id']} {'(told)':14} "
                      f"{'-':15} {'-':34} hist={n_hist:,} {resp['wall_s']}s")
            results.append(record)
        fit_final = {"final_history_tokens": results[-1]["history_tokens"],
                     "ctx": args.ctx,
                     "headroom": args.ctx - results[-1]["history_tokens"] - args.max_tokens}
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=30)
        log_f.close()

    graded = [r for r in results if r["graded"]]
    by_probe: dict[str, dict[str, int]] = {}
    for r in graded:
        b = by_probe.setdefault(r["probe"], {"correct": 0, "total": 0})
        b["total"] += 1
        b["correct"] += 1 if r["outcome"] == "correct" else 0
    outcomes: dict[str, int] = {}
    for r in graded:
        outcomes[r["outcome"]] = outcomes.get(r["outcome"], 0) + 1

    # The paired anchors ARE E56's measurement: the same question asked shallow
    # and deep, so depth is the only thing that differs between the two cells.
    # Reported per pair rather than as a total, because "4 of 5 held" hides
    # WHICH one moved, and which one moved is the finding.
    by_turn = {r["id"]: r for r in results}
    anchors = []
    for name, shallow, deep in anchor_pairs:
        s, d = by_turn.get(shallow), by_turn.get(deep)
        if not (s and d):
            continue
        anchors.append({
            "anchor": name, "shallow_turn": shallow, "deep_turn": deep,
            "shallow": s["outcome"], "deep": d["outcome"],
            "shallow_answer": s["answer"], "deep_answer": d["answer"],
            "shallow_history_tokens": s["history_tokens"],
            "deep_history_tokens": d["history_tokens"],
            "held": s["outcome"] == d["outcome"],
            "degraded": s["outcome"] == "correct" and d["outcome"] != "correct",
        })

    summary = {
        "label": args.label, "model": args.model,
        "conversation": args.conversation,
        "turns": len(TURNS), "graded_turns": len(graded),
        "max_tokens": args.max_tokens, "ctx": args.ctx, "headroom": args.headroom,
        "thinking": args.thinking, "server_extra": args.server_extra,
        "server_bin": args.server_bin, "request_timeout": args.request_timeout,
        "kernel": os.uname().release,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wall_s": round(time.time() - started, 1),
        "context_preflight_final": fit_final,
        "correct": sum(1 for r in graded if r["outcome"] == "correct"),
        "total": len(graded),
        # Reported on its own, never inside a percentage with the others: a
        # model that adopts what the user asserted has failed in the way that
        # costs money.
        "accepted_false": sum(1 for r in graded if r["outcome"] == "accepted_false"),
        "stale_answer": sum(1 for r in graded if r["outcome"] == "stale_answer"),
        "over_revised": sum(1 for r in graded if r["outcome"] == "over_revised"),
        "wrong_document": sum(1 for r in graded if r["outcome"] == "wrong_document"),
        "anchors": anchors,
        "anchors_degraded": sum(1 for a in anchors if a["degraded"]),
        "by_probe": by_probe,
        "outcome_counts": outcomes,
        "results": results,
    }
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\n{args.label}: {summary['correct']}/{summary['total']} correct")
    print(f"ACCEPTED-FALSE {summary['accepted_false']} | STALE {summary['stale_answer']} "
          f"| OVER-REVISED {summary['over_revised']} "
          f"| WRONG-DOC {summary['wrong_document']}")
    for a in anchors:
        flag = "DEGRADED" if a["degraded"] else ("held" if a["held"] else "changed")
        print(f"  anchor {a['anchor']}: {a['shallow']} @{a['shallow_history_tokens']:,} "
              f"-> {a['deep']} @{a['deep_history_tokens']:,}  {flag}")
    print(f"by_probe: {by_probe}")
    print(f"outcomes: {outcomes}")
    print(f"final history: {fit_final}")
    print(f"written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
