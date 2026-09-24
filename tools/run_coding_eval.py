#!/usr/bin/env python3
# File: run_coding_eval.py
# Purpose: Execute the coding-eval task set against a served model and score by running the code.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: Starts llama-server for one model (Rule 1: HTTP only; Rule 2:
# every subprocess wait and HTTP call carries a timeout; Rule 3: the
# full-offload gate is asserted by parsing the verbose server log and FAILS
# on zero evidence), sends each task in spikes/coding-eval/tasks.py at
# temperature 0, extracts the code block, and executes it against hidden
# tests. Emits one JSON per model plus a markdown summary.
#
# WHY EXECUTION AND NOT STRING MATCHING: the eval pilot lost a point to a
# grader artifact (asserting "8,388.60" when "8388.60" was returned). Running
# the code removes that whole failure class - the only thing being judged is
# whether the program does what the spec said.
#
# EXECUTING MODEL-GENERATED CODE IS THE POINT, AND IT IS BOUNDED: candidate
# code runs in a separate `python3` subprocess with a hard wall-clock timeout,
# a scratch cwd under /tmp, and no arguments or stdin it could use to reach
# session state. It is NOT a security sandbox and must never be pointed at
# untrusted third-party model output on a machine that matters; it is a
# blast-radius limiter for our own local models on a bench box.
#
# OUTCOME VOCABULARY is deliberately five-way rather than pass/fail, because
# F20's lesson was that a silently TRUNCATED answer got recorded as a
# capability result. `truncated` is therefore its own outcome and is never
# folded into `failed`.

from __future__ import annotations

import argparse
import json
import os
import re
import resource
import shlex
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "coding-eval"))
from bench_context import assert_context_fits  # noqa: E402
from expert_tasks import EXPERT_TASKS  # noqa: E402
from expert_tasks_v2 import EXPERT_TASKS_V2  # noqa: E402
from expert_tasks_v3 import EXPERT_TASKS_V3  # noqa: E402
from tasks import TASKS  # noqa: E402

# Two task sets, kept apart rather than merged into one graded pool.
#
# `core` is the original 15 (2 easy / 7 medium / 6 hard). A cheap cloud model
# scored 14/15 on it, so it does not locate the frontier of anything.
#
# `expert` is 8 tasks made hard by EXACTNESS - stated contracts (laziness,
# non-mutation, atomicity), complexity gates enforced by timing, specified
# tie-breaks, and edge-case grammar - not by obscurity. Each was validated
# against a reference solution that must pass AND a naive solution that must
# fail, so a task that everything passes is a broken task and is caught
# before a model is scored against it.
#
# They are not concatenated: a 23-task pool would let a strong core score
# hide an expert-tier collapse behind one aggregate number, which is the
# failure mode that made the eval-pilot suite useless.
#
# `expert2` is 7 tasks built after three banks saturated. It saturated too: the
# incumbent scored 7/7 (E110, F150), because defeating a NAIVE solution is a
# much weaker property than discriminating between two competent models. It is
# kept, not deleted - it measures a band this model is above.
#
# `expert3` raises the admission standard to three arms: a reference that
# passes, a naive solution that fails, AND a competent-but-subtly-wrong
# solution that fails, with the subtle corner sourced from a failure this repo
# has measured rather than one I imagined.
TASK_SETS: dict[str, list[dict]] = {"core": TASKS, "expert": EXPERT_TASKS,
                                    "expert2": EXPERT_TASKS_V2,
                                    "expert3": EXPERT_TASKS_V3}

DEFAULT_SERVER = "/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server"
ASSIGN_RE = re.compile(r"layer\s+\d+\s+assigned to device\s+([A-Za-z0-9_]+)")
FENCE_RE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)


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
    non_gpu = [d for d in devices if d == "CPU"]
    if non_gpu:
        raise RuntimeError(
            f"full-offload gate FAILED: {len(non_gpu)}/{len(devices)} layers on CPU. "
            f"hint: raise -ngl or the throughput figure is not a GPU measurement"
        )
    return {"layers_assigned": len(devices), "devices": sorted(set(devices))}


def repetition_stats(text: str) -> dict:
    """Degenerate-repetition signal, for arms that sample rather than take argmax.

    Two independent measures, because a model loops in two different shapes and
    either one alone reads as clean when the other is firing:
      * `max_line_run`  - the longest run of consecutive IDENTICAL non-blank
        lines. Catches the "hmm. hmm. hmm." shape.
      * `max_ngram_rep` - the highest number of occurrences of any single
        8-word window. Catches a paragraph re-stated verbatim on a cycle
        longer than one line, which max_line_run cannot see.

    Returns counts, never a verdict. What threshold counts as "looping" is the
    experiment's call and belongs in its pre-registration, not in the meter.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    max_line_run = 0
    run = 0
    prev = None
    for ln in lines:
        run = run + 1 if ln == prev else 1
        max_line_run = max(max_line_run, run)
        prev = ln
    words = text.split()
    counts: dict[tuple, int] = {}
    n = 8
    for i in range(len(words) - n + 1):
        key = tuple(words[i:i + n])
        counts[key] = counts.get(key, 0) + 1
    return {
        "max_line_run": max_line_run,
        "max_ngram_rep": max(counts.values()) if counts else 0,
        "distinct_line_ratio": round(len(set(lines)) / len(lines), 4) if lines else None,
    }


def ask(port: int, prompt: str, max_tokens: int, timeout: float,
        thinking: str = "default", sampler: dict | None = None) -> dict:
    """One request. `thinking` controls the model's reasoning budget.

    Qwen3.8's chat template resolves `reasoning_effort` to **xhigh** when the
    caller says nothing, so every Qwen3.8 figure in this repo before
    2026-08-15 was measured at the MAXIMUM reasoning setting by default rather
    than by choice. "default" sends nothing and inherits that, and is kept so
    earlier runs stay reproducible.

    `sampler` is None for every arm banked before 2026-09-04, and None must
    keep producing a BYTE-IDENTICAL payload to the one those arms sent -
    temperature 0, no sampler keys at all. That is why this is an
    opt-in dict rather than a set of parameters with non-None defaults: the
    safe default here is "change nothing", because every existing result in
    results/raw/ was measured against the old payload and a new key in it
    would silently restate them.

    NOTE FOR ANYONE ADDING A SAMPLER ARM: min_p, top_k and top_p are INERT at
    temperature 0. Greedy decoding takes the argmax and never samples, so a
    truncation filter has nothing to filter. An arm that varies them while
    leaving temperature at 0 measures nothing and returns a clean null.
    """

    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    if sampler:
        payload.update(sampler)
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
        data=body,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    choice = d["choices"][0]
    msg = choice["message"]
    return {
        "content": msg.get("content") or "",
        "reasoning": msg.get("reasoning_content") or "",
        "finish_reason": choice.get("finish_reason"),
        "usage": d.get("usage", {}),
        "wall_s": round(time.time() - t0, 2),
    }


def extract_code(content: str) -> str | None:
    blocks = FENCE_RE.findall(content)
    if blocks:
        # Concatenate every block: some models split helpers across blocks.
        return "\n\n".join(b.strip() for b in blocks)
    # A model that ignored the fence instruction but emitted a bare def/class
    # is still answering the question; do not fail it on formatting alone.
    if re.search(r"^\s*(def|class)\s+\w+", content, re.MULTILINE):
        return content
    return None


def run_candidate(code: str, tests: str, timeout: float,
                  mem_gb: int = 4) -> tuple[str, str]:
    """Execute candidate + hidden tests in a bounded subprocess. Returns (outcome, detail).

    BOTH bounds are load-bearing, and the memory one was learned the hard way.
    On 2026-08-15 at 03:12 an unbounded candidate reached 100 GB anon-rss and
    the kernel OOM-killer took the overnight benchmark with it. A wall clock
    does not stop a process that allocates faster than it computes.

    The memory bound is also part of the GRADE, not just a safety rail. The
    expert tier's `interval_map` task is gated on refusing to materialise a
    10**9 range: its naive solution fails at ~9.4s by exhausting a 4 GB cap,
    and with no cap at all on a 128 GB box it would swallow the machine
    instead of failing the task. An unbounded runner does not merely risk the
    box - it stops enforcing the complexity gate it claims to enforce.
    """
    def _limit() -> None:
        resource.setrlimit(resource.RLIMIT_AS, (mem_gb * 1024**3, mem_gb * 1024**3))

    with tempfile.TemporaryDirectory(prefix="sparkbench-coding-") as td:
        script = Path(td) / "run.py"
        script.write_text(code + "\n\n# --- hidden tests ---\n" + tests + "\nprint('__ALL_TESTS_PASSED__')\n")
        try:
            proc = subprocess.run(
                [sys.executable, str(script)],
                cwd=td,
                capture_output=True,
                text=True,
                timeout=timeout,
                stdin=subprocess.DEVNULL,
                env={"PATH": "/usr/bin:/bin", "HOME": td},
                preexec_fn=_limit,  # noqa: PLW1509 - the bound is the point
            )
        except subprocess.TimeoutExpired:
            return "timeout", f"exceeded {timeout}s"
    if "__ALL_TESTS_PASSED__" in proc.stdout:
        return "pass", ""
    err = (proc.stderr or "").strip().splitlines()
    detail = err[-1] if err else f"rc={proc.returncode}, no stderr"
    if "AssertionError" in proc.stderr:
        return "wrong_answer", detail
    return "error", detail



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
    ap = argparse.ArgumentParser(description="Executable coding eval against a locally served model.")
    ap.add_argument("--model", required=True,
                    help="GGUF path for --provider local, or the API model id for a cloud provider")
    ap.add_argument("--provider", default="local", choices=["local", "mistral", "openrouter"],
                    help="local = served by llama-server here; mistral/openrouter = cloud reference arms")
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    # Defaults to core so every command line issued before the expert tier
    # existed keeps its exact meaning.
    ap.add_argument("--task-set", default="core", choices=sorted(TASK_SETS),
                    help="core = the original 15; expert = 8 tasks with stated contracts, "
                         "complexity gates and specified tie-breaks")
    ap.add_argument("--server-bin", default=os.environ.get("SPARKBENCH_SERVER_BIN", DEFAULT_SERVER))
    ap.add_argument("--ctx", type=int, default=16384, help="-c TOTAL; -np is 1 so this is per request (F20)")
    ap.add_argument("--max-tokens", type=int, default=8192,
                    help="generous by design: reasoning models spend budget on the chain before "
                         "emitting code, and a truncated answer scored as wrong is the F20 trap")
    ap.add_argument("--allow-truncation", action="store_true",
                    help="record a run in which tasks hit the token cap and produced "
                         "no code. Off by default: a truncated task was never "
                         "attempted to completion, so scoring it as a fail reports "
                         "the token budget as capability (Rule 13).")
    ap.add_argument("--thinking", default="default",
                    choices=["default", "off", "low", "medium", "xhigh"],
                    help="reasoning budget. Qwen3.8's template defaults to "
                         "xhigh, so 'default' is NOT neutral.")
    # Sampler arm (E101). EVERY default here is None, and None sends NOTHING,
    # so an invocation that omits them produces the exact payload every arm
    # banked before 2026-09-04 sent. The safe default is "change nothing":
    # results/raw/ is full of runs measured against the old payload.
    ap.add_argument("--temp", type=float, default=None,
                    help="sampling temperature. OMIT for the historical greedy "
                         "behaviour (temperature 0). Setting this is what makes "
                         "--min-p/--top-k/--top-p do anything at all.")
    ap.add_argument("--min-p", type=float, default=None,
                    help="min-p truncation. INERT unless --temp is set above 0.")
    ap.add_argument("--top-p", type=float, default=None,
                    help="nucleus sampling. INERT unless --temp is set above 0.")
    ap.add_argument("--top-k", type=int, default=None,
                    help="top-k truncation. INERT unless --temp is set above 0.")
    ap.add_argument("--presence-penalty", type=float, default=None)
    ap.add_argument("--repeat-penalty", type=float, default=None)
    ap.add_argument("--seed", type=int, default=None,
                    help="server-side sampling seed. Set a DIFFERENT one per "
                         "replicate: at temperature > 0 two runs with the same "
                         "seed are one measurement, not two (F96).")
    ap.add_argument("--server-extra", default="", metavar="'FLAGS'",
                    help="extra flags appended to the llama-server command line, "
                         "e.g. --server-extra '--reasoning-effort medium'. Quote the "
                         "whole string. Recorded in the output.")
    ap.add_argument("--port", type=int, default=8110)
    ap.add_argument("--load-timeout", type=float, default=300.0)
    ap.add_argument("--request-timeout", type=float, default=None,
                    help="seconds; derived from --max-tokens when omitted")
    ap.add_argument("--exec-timeout", type=float, default=15.0)
    ap.add_argument("--only", default=None,
                    help="comma-separated task ids to run from --task-set "
                         "(e.g. 'parse_semver,eval_expr'). Omit to run all. An "
                         "id that matches nothing is an error, not a smaller run")
    args = ap.parse_args()
    # --out is a FILE. Checking it here rather than at the end is the whole
    # point: on 2026-09-06 a directory was passed, the run completed, and
    # IsADirectoryError destroyed the results of 19 minutes of GPU time at the
    # last line. A precondition that can be checked before the work must be.
    if Path(args.out).is_dir():
        raise SystemExit(
            f"--out {args.out!r} is a directory, and --out names the results "
            f"FILE. hint: pass e.g. {Path(args.out) / (args.label + '.json')}"
        )
    args.request_timeout = resolve_request_timeout(
        args.request_timeout, args.max_tokens)

    # F128: a flag can load without acting. min_p/top_k/top_p filter a
    # distribution that greedy decoding never samples from, so setting them at
    # temperature 0 is a silent no-op that returns a clean null. Refuse it
    # rather than measure it.
    _SAMPLER_KEYS = {
        "min_p": args.min_p, "top_p": args.top_p, "top_k": args.top_k,
        "presence_penalty": args.presence_penalty,
        "repeat_penalty": args.repeat_penalty,
    }
    _truncators = {k: v for k, v in _SAMPLER_KEYS.items() if v is not None}
    if _truncators and not args.temp:
        raise SystemExit(
            f"refusing to run: {sorted(_truncators)} set with temperature "
            f"{args.temp!r}. These are truncation filters over a sampled "
            f"distribution; greedy decoding takes the argmax and never samples, "
            f"so they would have NO effect and the arm would report a null it "
            f"did not earn. hint: pass --temp above 0, or drop these flags."
        )
    sampler: dict = {}
    if args.temp is not None:
        sampler["temperature"] = args.temp
    sampler.update(_truncators)
    if args.seed is not None:
        sampler["seed"] = args.seed
    sampler = sampler or None
    tasks = TASK_SETS[args.task_set]
    if args.only:
        wanted = [s.strip() for s in args.only.split(",") if s.strip()]
        available = [t["id"] for t in tasks]
        unmatched = [w for w in wanted if w not in available]
        if unmatched:
            raise ValueError(
                f"--only named {unmatched}, absent from task-set {args.task_set!r}. "
                f"available: {', '.join(available)}; "
                f"hint: ids are matched exactly here (unlike run_matters.py's prefix "
                f"match) because coding task ids are already short and unambiguous"
            )
        tasks = [t for t in tasks if t["id"] in wanted]

    cloud = args.provider in ("mistral", "openrouter")
    budget = None
    if cloud:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from cloud_client import CloudBudget, chat  # noqa: PLC0415 - only needed on the cloud path
        budget = CloudBudget(usd_ceiling=float(os.environ.get("SPARKBENCH_USD_CEILING", "40")))
    else:
        # Rule 9: only enforce a quiet GPU when this run actually uses it. A
        # cloud arm may legitimately run alongside a local one.
        for p in ("llama-server", "llama-bench"):
            r = subprocess.run(["pgrep", "-x", p], capture_output=True, text=True)
            if r.stdout.strip():
                print(
                    f"FAIL: {p} already running (pids: {r.stdout.split()}). "
                    f"hint: a busy GPU voids the timing columns of this run",
                    file=sys.stderr,
                )
                return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = out_path.with_suffix(".serverlog")

    proc = None
    log_f = None
    print(f"=== coding eval: {args.label} ({args.provider}) ===")
    if not cloud:
        cmd = [
            args.server_bin, "-m", args.model,
            "-c", str(args.ctx), "-np", "1",
            "--host", "127.0.0.1", "--port", str(args.port),
            "--no-webui", "-v",
        ]
        # SERVER-SIDE flags. This exists because every quality figure in this
        # repo was measured through the PER-REQUEST path (`reasoning_effort` in
        # the body), while sparkrouter would deploy the SERVER path
        # (`--reasoning-effort` on the unit). E115 measured those two paths
        # producing different generations at the same nominal level, so they
        # are not interchangeable and the difference has to be runnable.
        cmd += shlex.split(args.server_extra)
        print(f"server: {' '.join(cmd)}")
        log_f = log_path.open("w")
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
    results: list[dict] = []
    started = time.time()
    try:
        if cloud:
            def ask_one(prompt: str) -> dict:
                if sampler:
                    raise SystemExit(
                        "refusing to run: --temp/--min-p/... are not plumbed "
                        "through the cloud client, so a cloud arm would silently "
                        "run at temperature 0 and be compared against a local arm "
                        "that did not. hint: run the sampler arm locally."
                    )
                r = chat(args.model, [{"role": "user", "content": prompt}], budget,
                         provider=args.provider, temperature=0,
                         max_tokens=args.max_tokens, timeout=args.request_timeout)
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
                           thinking=args.thinking, sampler=sampler)
        print(f"full-offload gate: {gate}")
        print(f"context preflight: {fit}")
        for i, task in enumerate(tasks, 1):
            t0 = time.time()
            try:
                resp = ask_one(task["prompt"])
            except Exception as exc:  # noqa: BLE001 - one task's transport failure must not kill the run
                results.append({"id": task["id"], "tier": task["tier"], "outcome": "transport_failed",
                                "detail": str(exc), "wall_s": round(time.time() - t0, 2)})
                print(f"  [{i}/{len(tasks)}] {task['id']:22s} transport_failed: {exc}")
                continue
            if resp["finish_reason"] == "length":
                outcome, detail = "truncated", f"hit max_tokens={args.max_tokens}"
            else:
                code = extract_code(resp["content"])
                if code is None:
                    outcome, detail = "no_code", "no code block or bare def/class in response"
                else:
                    outcome, detail = run_candidate(code, task["tests"], args.exec_timeout)
            usage = resp["usage"]
            rec = {
                "id": task["id"], "tier": task["tier"], "outcome": outcome, "detail": detail,
                "finish_reason": resp["finish_reason"],
                "completion_tokens": usage.get("completion_tokens"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "reasoning_chars": len(resp["reasoning"]),
                "wall_s": resp["wall_s"],
                "repetition": repetition_stats(
                    (resp["reasoning"] or "") + "\n" + (resp["content"] or "")),
            }
            results.append(rec)
            print(f"  [{i}/{len(tasks)}] {task['id']:22s} {outcome:16s} "
                  f"{usage.get('completion_tokens')} tok, {resp['wall_s']}s  {detail[:70]}")
    finally:
        # Cloud arms never started a server, so there is nothing to reap.
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
        if log_f is not None:
            log_f.close()

    passed = sum(1 for r in results if r["outcome"] == "pass")
    by_tier: dict[str, dict[str, int]] = {}
    for r in results:
        t = by_tier.setdefault(r["tier"], {"pass": 0, "total": 0})
        t["total"] += 1
        t["pass"] += 1 if r["outcome"] == "pass" else 0
    summary = {
        "label": args.label,
        "model": args.model,
        "provider": args.provider,
        # ctx and request_timeout are recorded because their ABSENCE cost real
        # time: diagnosing the E33 re-run meant inferring the timeout from a
        # wall_s of 900.1 rather than reading it. A config a result cannot be
        # re-derived from is a config that will be argued about later.
        "max_tokens": args.max_tokens, "ctx": args.ctx,
        # Rule 8: the arm's CONFIG travels with its numbers. null means the
        # historical greedy payload, which is what every pre-2026-09-04 arm sent.
        "sampler": sampler,
        "context_preflight": fit,
        "thinking": args.thinking,
        "request_timeout": args.request_timeout,
        "exec_timeout": args.exec_timeout,
        "server_bin": args.server_bin if not cloud else None,
        "server_extra": args.server_extra if not cloud else None,
        "cloud_spend": budget.as_dict() if budget else None,
        "latency": latency_summary(results),
        "kernel": os.uname().release,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wall_s": round(time.time() - started, 1),
        "passed": passed,
        "total": len(results),
        "by_tier": by_tier,
        "outcome_counts": {o: sum(1 for r in results if r["outcome"] == o)
                           for o in sorted({r["outcome"] for r in results})},
        "results": results,
    }
    # RULE 13 GATE - see run_ps_eval.py for the full reasoning. E92 scored
    # Kwaipilot 0/8 on this bank when 7 of the 8 outputs were cut off at the cap
    # with empty content. That is not a coding result, it is a budget result.
    truncated = sum(1 for r in results if r["outcome"] == "truncated")
    summary["truncated"] = truncated
    summary["truncation_gate"] = "PASS" if truncated == 0 else (
        "OVERRIDDEN" if args.allow_truncation else "FAIL")
    out_path.write_text(json.dumps(summary, indent=2))
    if truncated:
        print(f"\n*** TRUNCATION GATE: {truncated}/{len(results)} tasks hit the "
              f"token cap and produced no usable output. ***", file=sys.stderr)
        print(f"    max_tokens={args.max_tokens}. These are NOT failures - they were "
              f"never finished.\n"
              f"    hint: raise --max-tokens (and --ctx to fit it). Verify the chat "
              f"template honours\n"
              f"    any effort flag before using one - an ignored flag is recorded as "
              f"applied.", file=sys.stderr)
        if not args.allow_truncation:
            print("    Refusing to report a score. Pass --allow-truncation to record "
                  "it anyway.", file=sys.stderr)
            return 3
    print(f"\n{args.label}: {passed}/{len(results)} passed  by_tier={by_tier}")
    print(f"outcomes: {summary['outcome_counts']}")
    print(f"written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
