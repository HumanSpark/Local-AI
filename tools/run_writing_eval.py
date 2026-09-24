#!/usr/bin/env python3
# File: run_writing_eval.py
# Purpose: Run the technical-writing eval against a served or cloud model, graded without an LLM judge.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: Seven writing tasks from spikes/writing-eval/tasks.py, one request
# each, graded by numeric and string matching against a source brief and the
# owner's written house style. Mirrors run_ps_eval.py: Rule 1 HTTP-only
# serving, Rule 2 timeouts everywhere, Rule 3 full-offload gate asserted from
# the verbose server log and FAILING on zero evidence, Rule 9 quiet-GPU check
# on the local path.
#
# THE HEADLINE METRICS ARE fabrication_rate AND negative_retention, not a
# quality score. Nothing here claims to measure whether the writing is good.
# What it measures is whether a draft is publishable at all: does it invent
# figures, and does it keep the unfavourable findings it was told to report.
# A model can write beautifully and fail both.
#
# `dropped_negative` is its own outcome and is never folded into a generic
# failure, for the same reason `truncated` and `stale_value` are not: the most
# fluent summary of an awkward result is usually the one that omits it, so the
# failure is invisible to any measure of fluency and has to be named.

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "writing-eval"))
from bench_context import assert_context_fits  # noqa: E402
from house_style import JUDGEMENT_ONLY  # noqa: E402
from tasks import CATEGORIES, TASKS, grade  # noqa: E402

DEFAULT_SERVER = "/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server"
ASSIGN_RE = __import__("re").compile(r"layer\s+\d+\s+assigned to device\s+([A-Za-z0-9_]+)")


def wait_healthy(port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as r:
                if r.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001 - poll boundary, retried below
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


def ask(port: int, prompt: str, max_tokens: int, timeout: float,
        thinking: str = "default") -> dict:
    """One request. `thinking` controls the model's reasoning budget.

    Qwen3.8's chat template resolves `reasoning_effort` to **xhigh** when the
    caller says nothing, so every Qwen3.8 figure in this repo before
    2026-08-15 was measured at the MAXIMUM reasoning setting by default rather
    than by choice. "default" sends nothing and inherits that, and is kept so
    earlier runs stay reproducible.
    """

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    if thinking == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    elif thinking in ("low", "medium", "xhigh"):
        payload["reasoning_effort"] = thinking
    elif thinking != "default":
        raise ValueError(
            f"unknown thinking mode {thinking!r}. "
            f"hint: one of default, off, low, medium, xhigh"
        )
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=body, headers={"Content-Type": "application/json"}, method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.load(r)
    choice = payload["choices"][0]
    message = choice["message"]
    return {
        "content": message.get("content") or "",
        "reasoning": message.get("reasoning_content") or "",
        "finish_reason": choice.get("finish_reason"),
        "usage": payload.get("usage", {}),
        "wall_s": round(time.time() - t0, 2),
    }



# The slowest generation rate this box produces at -np 1 is about 12.6 tok/s
# (Qwen3.8-27B dense). Six is a deliberately conservative floor: a timeout that
# is too generous costs nothing, and one that is too tight destroys the run.
MIN_TOKENS_PER_SEC = 6.0
TIMEOUT_MARGIN_S = 300.0


def resolve_request_timeout(explicit: float | None, max_tokens: int) -> float:
    """Derive a request timeout that can actually accommodate max_tokens.

    THIS EXISTS BECAUSE THE E33 RE-RUN WAS DESTROYED BY THE DEFAULT. max_tokens
    was raised 8192 -> 24576 under a declared amendment and the 900s request
    timeout was left alone. At ~12.6 tok/s a full 24,576-token generation needs
    ~1,950s, so every task that used the extra budget - which is precisely the
    set the re-run existed to measure - died at 900.1s as `transport_failed`
    and produced no data at all.

    A caller can still set a shorter timeout deliberately; it warns rather than
    overriding, because there are legitimate reasons to cap a run. What must
    never happen again is the SILENT case, where raising a token budget quietly
    guarantees a wall-clock failure nobody declared.
    """
    floor = max_tokens / MIN_TOKENS_PER_SEC + TIMEOUT_MARGIN_S
    if explicit is None:
        return round(floor)
    if explicit < floor:
        print(
            f"WARNING: --request-timeout {explicit:.0f}s is below the {floor:.0f}s needed "
            f"for max_tokens={max_tokens} at {MIN_TOKENS_PER_SEC} tok/s. Generations that "
            f"use the full budget will fail as transport_failed, not truncated, and will "
            f"produce no data. This destroyed the E33 re-run on 2026-08-15.",
            file=sys.stderr,
        )
    return explicit


def latency_summary(results: list[dict]) -> dict:
    """Per-item response times, which is what decides batch vs interactive use.

    A total run wall-clock says nothing about whether a person can sit in front
    of the thing. Median is the typical wait; p95 is the one that decides
    whether it feels usable, because the slow tail is what a user remembers.
    """
    waits = sorted(r["wall_s"] for r in results if isinstance(r.get("wall_s"), (int, float)))
    if not waits:
        return {"n": 0}
    def pct(q: float) -> float:
        return round(waits[min(len(waits) - 1, int(q * len(waits)))], 2)
    return {
        "n": len(waits), "median_s": pct(0.5), "p95_s": pct(0.95),
        "min_s": round(waits[0], 2), "max_s": round(waits[-1], 2),
        # A rough interactive bar: a person will wait a few seconds, not a minute.
        "under_10s": sum(1 for w in waits if w < 10),
        "under_30s": sum(1 for w in waits if w < 30),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Technical-writing eval, graded without an LLM judge.",
        epilog="example: python3 tools/run_writing_eval.py "
               "--model /opt/models/staging/x.gguf --label e40-x --out results/raw/e40-x.json",
    )
    ap.add_argument("--model", required=True,
                    help="GGUF path for --provider local, or the API model id for a cloud provider")
    ap.add_argument("--provider", default="local", choices=["local", "mistral", "openrouter"])
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--server-bin", default=os.environ.get("SPARKBENCH_SERVER_BIN", DEFAULT_SERVER))
    # 32768, not 16384. The old default was IMPOSSIBLE: paired with the
    # --max-tokens default of 16384 it left zero room for the prompt, so any
    # run at the defaults would have overflowed -c and been silently
    # front-truncated. Nobody hit it because every recorded invocation passed
    # --ctx 32768 explicitly (checked across E40 and E42, 2026-08-17), which is
    # exactly why it survived - a default nobody uses is a default nobody
    # checks. The preflight above now refuses rather than truncating, and this
    # value is the one the runs actually used.
    ap.add_argument("--ctx", type=int, default=32768,
                    help="-c TOTAL; -np is 1 so this is the per-request budget (F20). "
                         "Must exceed the longest prompt plus --max-tokens or the "
                         "run refuses to start")
    ap.add_argument("--max-tokens", type=int, default=16384,
                    help="a 300-word answer is ~400 tokens, so this looks absurd until "
                         "you measure it: at the reasoning_effort Qwen3.8 defaults to "
                         "(xhigh) the FIRST writing task consumed all 4,096 tokens on "
                         "reasoning in 339s and emitted no draft at all. A truncated "
                         "draft scored as a writing failure is exactly F20's trap, and "
                         "the budget has to clear the reasoning, not the answer.")
    ap.add_argument("--thinking", default="default",
                    choices=["default", "off", "low", "medium", "xhigh"],
                    help="reasoning budget. Qwen3.8's template defaults to "
                         "xhigh, so 'default' is NOT neutral.")
    ap.add_argument("--only", default=None,
                    help="comma-separated task ids to run (e.g. 'plain_english'). "
                         "Omit to run all seven. An id that matches nothing is an "
                         "error, not a smaller run. A SUBSET run's aggregate "
                         "metrics are over the subset - do not compare them to a "
                         "full-run score")
    ap.add_argument("--port", type=int, default=8114)
    ap.add_argument("--load-timeout", type=float, default=300.0)
    ap.add_argument("--request-timeout", type=float, default=None,
                    help="seconds; derived from --max-tokens when omitted")
    args = ap.parse_args()
    args.request_timeout = resolve_request_timeout(
        args.request_timeout, args.max_tokens)

    cloud = args.provider != "local"
    budget = None
    if cloud:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from cloud_client import CloudBudget, chat  # noqa: PLC0415 - cloud path only
        budget = CloudBudget()
    else:
        # Rule 9: one GPU consumer. A busy GPU voids the timing columns.
        for name in ("llama-server", "llama-bench"):
            r = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
            if r.stdout.strip():
                print(f"FAIL: {name} already running (pids: {r.stdout.split()}). "
                      f"hint: a busy GPU voids the timing columns of this run", file=sys.stderr)
                return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = out_path.with_suffix(".serverlog")

    tasks = TASKS
    if args.only:
        wanted = [s.strip() for s in args.only.split(",") if s.strip()]
        available = [t["id"] for t in TASKS]
        unmatched = [w for w in wanted if w not in available]
        if unmatched:
            raise ValueError(
                f"--only named {unmatched}, absent from the writing task set. "
                f"available: {', '.join(available)}; "
                f"hint: a filter that matched nothing would silently run a smaller "
                f"set and be scored as though the missing tasks had no draft"
            )
        tasks = [t for t in TASKS if t["id"] in wanted]

    proc = None
    log_f = None
    print(f"=== writing eval: {args.label} ({args.provider}) ===")
    kinds = sorted({t["kind"] for t in tasks})
    print(f"{len(tasks)} tasks over {len(kinds)} kinds: {', '.join(kinds)}"
          + (f"  [SUBSET of {len(TASKS)}]" if len(tasks) != len(TASKS) else ""))
    if not cloud:
        cmd = [args.server_bin, "-m", args.model, "-c", str(args.ctx), "-np", "1",
               "--host", "127.0.0.1", "--port", str(args.port), "--no-webui", "-v"]
        print(f"server: {' '.join(cmd)}")
        log_f = log_path.open("w")
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)

    results: list[dict] = []
    started = time.time()
    try:
        if cloud:
            def ask_one(prompt: str) -> dict:
                r = chat(args.model, [{"role": "user", "content": prompt}], budget,
                         provider=args.provider, temperature=0,
                         max_tokens=args.max_tokens, timeout=args.request_timeout,
                         retries=6)
                return {"content": r["content"], "reasoning": " " * r.get("reasoning_chars", 0),
                        "finish_reason": r["finish_reason"], "usage": r["usage"],
                        "wall_s": r["wall_s"]}
            gate = {"skipped": "cloud arm - no local offload to gate"}
            fit = {"skipped": "cloud arm - context is the provider's to manage"}
        else:
            wait_healthy(args.port, args.load_timeout)
            gate = assert_full_offload(log_path)
            fit = assert_context_fits(
                f"http://127.0.0.1:{args.port}", [t["prompt"] for t in tasks],
                args.max_tokens, args.ctx, args.request_timeout)

            def ask_one(prompt: str) -> dict:
                return ask(args.port, prompt, args.max_tokens, args.request_timeout,
                           thinking=args.thinking)
        print(f"full-offload gate: {gate}")
        print(f"context preflight: {fit}")

        for i, task in enumerate(tasks, 1):
            t0 = time.time()
            try:
                resp = ask_one(task["prompt"])
            except Exception as exc:  # noqa: BLE001 - one task must not kill the run
                results.append({"id": task["id"], "kind": task["kind"],
                                "outcome": "transport_failed", "detail": {"error": str(exc)},
                                "wall_s": round(time.time() - t0, 2)})
                print(f"  [{i}/{len(tasks)}] {task['id']:20s} transport_failed: {str(exc)[:90]}")
                continue
            if resp["finish_reason"] == "length":
                outcome, detail = "truncated", {"reason": f"hit max_tokens={args.max_tokens}"}
                text = resp["content"]
            else:
                text = resp["content"]
                outcome, detail = grade(task, text)
            usage = resp["usage"]
            results.append({
                "id": task["id"], "kind": task["kind"], "outcome": outcome,
                "detail": detail,
                # The draft itself is KEPT. A writing score nobody can read the
                # output behind is not auditable, and E37 already shipped one
                # unauditable number this week.
                "output": text,
                "finish_reason": resp["finish_reason"],
                "completion_tokens": usage.get("completion_tokens"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "reasoning_chars": len(resp["reasoning"]),
                "wall_s": resp["wall_s"],
            })
            note = ""
            if outcome == "fabricated":
                note = f"invented {detail['fabricated_numbers']}"
            elif outcome == "dropped_negative":
                note = f"omitted {detail['missing_negatives']}"
            elif outcome == "length_violation":
                note = f"{detail['words']} words (want {task['min_words']}-{task['max_words']})"
            elif outcome == "style_violation":
                note = "; ".join(detail["style"][:2])
            print(f"  [{i}/{len(tasks)}] {task['id']:20s} {outcome:17s} "
                  f"{resp['wall_s']}s  {note[:70]}")
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
        if log_f is not None:
            log_f.close()

    graded = [r for r in results if r["outcome"] not in ("transport_failed", "truncated")]
    fabricating = [r for r in graded if r["outcome"] == "fabricated"]
    required_neg = [r for r in graded
                    if next(t for t in TASKS if t["id"] == r["id"])["require_negatives"]]
    dropped = [r for r in required_neg if r["outcome"] == "dropped_negative"]
    correct = sum(1 for r in results if r["outcome"] == "correct")

    summary = {
        "label": args.label, "model": args.model, "provider": args.provider,
        "max_tokens": args.max_tokens, "ctx": args.ctx,
        "context_preflight": fit,
        "thinking": args.thinking,
        # A subset run's totals are over the SUBSET. Recorded so a 1/1 can
        # never be read as a 1/7 by a later reader or a summary script.
        "only": args.only,
        "tasks_run": [t["id"] for t in tasks],
        "task_set_size": len(TASKS),
        "request_timeout": args.request_timeout,
        "server_bin": args.server_bin if not cloud else None,
        "cloud_spend": budget.as_dict() if budget else None,
        "latency": latency_summary(results),
        "kernel": os.uname().release,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wall_s": round(time.time() - started, 1),
        "correct": correct, "total": len(results),
        "fabrication_rate": round(len(fabricating) / len(graded), 3) if graded else None,
        "negative_retention": (round(1 - len(dropped) / len(required_neg), 3)
                               if required_neg else None),
        "by_kind": {k: {"correct": sum(1 for r in results
                                       if r["kind"] == k and r["outcome"] == "correct"),
                        "total": sum(1 for r in results if r["kind"] == k)}
                    for k in CATEGORIES},
        "outcome_counts": {o: sum(1 for r in results if r["outcome"] == o)
                           for o in sorted({r["outcome"] for r in results})},
        "not_measured": JUDGEMENT_ONLY,
        "results": results,
    }
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\n{args.label}: {correct}/{len(results)} clean")
    print(f"FABRICATION {len(fabricating)}/{len(graded)} | "
          f"NEGATIVE RETENTION {summary['negative_retention']}")
    print(f"outcomes: {summary['outcome_counts']}")
    print(f"NOT measured (judgement rules, {len(JUDGEMENT_ONLY)}): a clean score here is "
          f"not a clean bill of writing quality")
    print(f"written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
