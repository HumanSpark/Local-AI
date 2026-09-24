#!/usr/bin/env python3
# File: serve_bench.py
# Purpose: llama-server lifecycle + concurrency load harness (Step 9; Phase B server-lifecycle core).
# Project: sparkbench | Date: 2026-07-04
#
# Overview: Launches llama-server for one config (model, slots, KV type),
# waits for health, enforces the HARNESS-RULES Rule 3 full-offload gate by
# parsing the verbose server log, then drives one thread per slot against
# the native /completion endpoint for a fixed-duration window and records
# server-side timings per request. Emits one JSON result file per config.
# Rule 1: HTTP only. Rule 2: every subprocess wait and HTTP call carries a
# timeout; the server is killed in a finally block (SIGTERM then SIGKILL).
# Rule 4: models come from /opt/models/staging (manifest-recorded).
# Rule 8 / F39: the result records BOTH the config we asked for (`config`) and
# the state the server reports via GET /props (`server_props`), plus the fields
# where they disagree (`config_divergence`) and the flags /props cannot confirm
# at all (`config_unverifiable`). Per-request outcomes use the five-way delivery
# vocabulary rather than a binary ok/failed - see classify_delivery().
# Spec + safe-defaults review: docs/plans/2026-07-04-step9-concurrency.md.
# Instrumentation uplift: docs/plans/2026-08-11-benchmark-instrumentation-uplift.md.

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

# Third instance of the same defect (run_step8_leg.sh BENCH_BIN and
# run_eval_pilot.sh SERVER were the first two), so fixed as a class: the
# default stays the b9864 build every prior result used, and a caller needing
# a newer build names it via SPARKBENCH_SERVER_BIN. The build is part of the
# CONFIG a result names (F39), so it is stated, never inferred.
SERVER_BIN = Path(
    os.environ.get(
        "SPARKBENCH_SERVER_BIN",
        "/home/agent-spark/sparkbench/llama.cpp/build/bin/llama-server",
    )
)
BASE_PROMPT = " ".join(["The quick brown fox jumps over the lazy dog."] * 16)
ASSIGN_RE = re.compile(r"layer\s+\d+\s+assigned to device\s+([A-Za-z0-9_]+)")

# Flags we pass that GET /props does NOT report back, so no divergence check is
# possible for them. Recorded in the result JSON beside config_divergence: an
# empty divergence list means "nothing checkable disagreed", NOT "config
# verified", and the difference has to be visible to whoever reads the result.
UNVERIFIABLE_FLAGS = ("kv", "fa", "extra")


def http_json(url: str, payload: dict | None = None, timeout: float = 10.0) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def start_server(args: argparse.Namespace, log_path: Path) -> subprocess.Popen:
    cmd = [
        str(SERVER_BIN), "-m", args.model,
        "-np", str(args.slots),
        "-c", str(args.slots * args.ctx_per_slot),
        "-fa", args.fa, "-ctk", args.kv, "-ctv", args.kv,
        "--host", "127.0.0.1", "--port", str(args.port),
        "--no-webui", "-v",
    ]
    if args.extra:
        cmd += args.extra.split()
    if args.dry_run:
        print("DRY-RUN server cmd:", " ".join(cmd))
        sys.exit(0)
    log_f = open(log_path, "w")
    return subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)


def wait_healthy(port: int, proc: subprocess.Popen, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"llama-server exited rc={proc.returncode} during startup; "
                "hint: read the -v log recorded next to the result JSON"
            )
        try:
            http_json(f"http://127.0.0.1:{port}/health", timeout=3)
            return
        except (urllib.error.URLError, urllib.error.HTTPError, OSError):
            time.sleep(1.0)
    raise TimeoutError(
        f"server not healthy within {timeout}s; "
        "hint: raise --load-timeout for very large models, or read the -v log"
    )


def offload_gate(log_path: Path) -> dict:
    # Rule 3: zero layers on CPU, and zero evidence is itself a failure.
    counts: dict[str, int] = {}
    for line in log_path.read_text(errors="replace").splitlines():
        m = ASSIGN_RE.search(line)
        if m:
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    if not counts:
        raise RuntimeError(
            "offload gate: no layer-assignment lines found in server log; "
            "hint: gate needs -v output - do not weaken this to a pass (Rule 3)"
        )
    cpu = sum(n for dev, n in counts.items() if dev.upper().startswith("CPU"))
    if cpu:
        raise RuntimeError(
            f"offload gate FAIL: {cpu} layers assigned to CPU ({counts}); "
            "hint: partial offload invalidates the measurement - check model size vs heap"
        )
    return {"pass": True, "assignments": counts}


def props_record(props: dict) -> dict:
    """Normalise GET /props into the server-reported state stored in the result.

    Rule 8 / F39: the command line is what we INTENDED. This is what the server
    says it actually did, and the two are kept side by side so a mismatch is
    visible instead of inferred. Required keys are subscripted, not .get() -
    a llama-server that omits them is one we do not understand, and that must
    surface here rather than as a null in a published result.
    """
    dgs = props["default_generation_settings"]
    template = props.get("chat_template") or ""  # base models legitimately have none
    return {
        "build_info": props["build_info"],
        "model_path": props["model_path"],
        "model_file": Path(props["model_path"]).name,
        "n_ctx": dgs["n_ctx"],
        "total_slots": props["total_slots"],
        "chat_template_sha256": hashlib.sha256(template.encode()).hexdigest()[:16] if template else None,
        "params": dgs["params"],
    }


def config_divergence(args: argparse.Namespace, rec: dict) -> list[dict]:
    """Every server-level flag where what we asked for differs from what /props reports.

    Only server-level state is compared. Per-request values (temperature, n_predict)
    are sent in the payload and legitimately differ from the server defaults /props
    reports, so comparing them would produce false divergences.

    `ctx` compares against ctx_per_slot, NOT the -c total we pass. /props reports
    meta->slot_n_ctx (server-context.cpp:4568), which is the PER-SLOT context:
    -c 4096 across -np 2 comes back as 2048. Comparing the total here fires on
    every correct multi-slot run, which is how a divergence check gets ignored.

    Empty list is the pass state. It is NOT proof the config is correct - see
    UNVERIFIABLE_FLAGS for what /props cannot tell us.
    """
    checks = [
        ("model", args.model, rec["model_path"]),
        ("slots", args.slots, rec["total_slots"]),
        ("ctx", args.ctx_per_slot, rec["n_ctx"]),
    ]
    return [
        {"field": f, "intended": intended, "reported": reported}
        for f, intended, reported in checks
        if intended != reported
    ]


def classify_delivery(resp: dict | None, transport_failed: bool, expect_limit: bool = False) -> dict:
    """Map a native /completion response onto the five-way delivery vocabulary.

    A clean HTTP 200 is not proof a usable answer arrived. The binary ok/failed
    split this replaces could not tell a dead socket from a token-ceiling
    truncation from an empty body, and scored the last two as successes.

    NOTE the endpoint difference: llama.cpp's native /completion reports
    `stop_type` ("eos" | "limit" | "word" | "none"), NOT the OpenAI-compatible
    `finish_reason` ("stop" | "length"). The vocabulary below is portable; the
    field it reads is not. stop_type is recorded raw and never normalised, so an
    unrecognised future value stays visible as itself.

    `expect_limit` says the caller deliberately imposed the token ceiling, which
    is this harness's normal mode - it sends a fixed n_predict, so a healthy
    throughput run stops at "limit" on every request. Without it, a perfect run
    would report zero complete deliveries. `length_truncated` still records the
    raw fact either way; only whether that counts as a FAILURE changes.

    `refusal_detected` on this endpoint means an empty content body - the native
    completion API carries no refusal field. It is the closest available proxy.
    """
    stop_type = None if resp is None else resp.get("stop_type")
    content = "" if resp is None else (resp.get("content") or "")
    refusal = (not transport_failed) and not content.strip()
    clean_stop = stop_type == "eos" or (expect_limit and stop_type == "limit")
    complete = (not transport_failed) and clean_stop and not refusal
    return {
        "transport_failed": transport_failed,
        "stop_type": stop_type,
        "length_truncated": stop_type == "limit",
        "refusal_detected": refusal,
        "delivery_complete": complete,
        "delivery_failure": not complete,
    }


def worker(tid: int, args: argparse.Namespace, barrier: threading.Barrier,
           stop_at: list[float], records: list[dict], lock: threading.Lock) -> None:
    url = f"http://127.0.0.1:{args.port}/completion"
    def one(n: int) -> dict:
        payload = {
            "prompt": f"[req {tid}-{n}] " + BASE_PROMPT,
            "n_predict": args.gen_tokens, "temperature": 0.0, "cache_prompt": False,
        }
        t0 = time.monotonic()
        resp = http_json(url, payload, timeout=args.request_timeout)
        t1 = time.monotonic()
        tm = resp.get("timings", {})
        return {
            "thread": tid, "seq": n, "start": t0, "end": t1,
            "prompt_n": tm.get("prompt_n"), "prompt_ms": tm.get("prompt_ms"),
            "predicted_n": tm.get("predicted_n"),
            "predicted_per_second": tm.get("predicted_per_second"),
            # gen_tokens is the ceiling WE imposed, so stopping at it is expected.
            **classify_delivery(resp, transport_failed=False, expect_limit=args.gen_tokens > 0),
        }
    try:
        one(-1)  # warmup, discarded
    except Exception as exc:  # a dead warmup means the config is broken - surface it
        with lock:
            records.append({"thread": tid, "error": f"warmup failed: {exc}"})
        barrier.abort()
        return
    try:
        idx = barrier.wait()
        if idx == 0:
            stop_at[0] = time.monotonic() + args.duration
    except threading.BrokenBarrierError:
        return
    while stop_at[0] == 0.0:
        time.sleep(0.01)
    n = 0
    while time.monotonic() < stop_at[0]:
        try:
            rec = one(n)
        except Exception as exc:
            # Transport only. A refusal or a non-eos stop is OBSERVED MODEL
            # BEHAVIOUR - it is recorded and kept, never silently re-rolled.
            rec = {"thread": tid, "seq": n, "error": str(exc),
                   **classify_delivery(None, transport_failed=True)}
        with lock:
            records.append(rec)
        n += 1


def summarize(records: list[dict], slots: int) -> dict:
    ok = [r for r in records if "error" not in r and r.get("predicted_n")]
    errors = [r for r in records if "error" in r]
    if not ok:
        raise RuntimeError(
            "no successful requests in the measurement window; "
            "hint: check per-request errors in the JSON records list"
        )
    wall = max(r["end"] for r in ok) - min(r["start"] for r in ok)
    ttfts = sorted(r["prompt_ms"] for r in ok if r.get("prompt_ms") is not None)
    def pct(p: float) -> float:
        return ttfts[min(len(ttfts) - 1, int(p * len(ttfts)))] if ttfts else float("nan")
    per_thread = min(sum(1 for r in ok if r["thread"] == t) for t in {r["thread"] for r in ok})
    # Five-way delivery breakdown. requests_ok/requests_failed are kept for
    # continuity with pre-2026-08-11 result files, but they cannot distinguish a
    # dead socket from an empty body - these can.
    def n_true(field: str) -> int:
        return sum(1 for r in records if r.get(field))
    stop_types: dict[str, int] = {}
    for r in records:
        stop_types[str(r.get("stop_type"))] = stop_types.get(str(r.get("stop_type")), 0) + 1
    return {
        "requests_ok": len(ok), "requests_failed": len(errors),
        "delivery": {
            "complete": n_true("delivery_complete"),
            "failure": n_true("delivery_failure"),
            "transport_failed": n_true("transport_failed"),
            "length_truncated": n_true("length_truncated"),
            "refusal_detected": n_true("refusal_detected"),
            "stop_type_counts": stop_types,
        },
        "min_requests_per_stream": per_thread,
        "under_sampled": per_thread < 3,  # loud flag per safe-defaults review
        "wall_s": round(wall, 3),
        "aggregate_gen_tps": round(sum(r["predicted_n"] for r in ok) / wall, 2),
        "mean_stream_gen_tps": round(statistics.mean(r["predicted_per_second"] for r in ok), 2),
        "ttft_ms_p50": round(pct(0.50), 1), "ttft_ms_p95": round(pct(0.95), 1),
        "streams": slots,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Step 9 concurrency bench: llama-server lifecycle + fixed-duration load.",
        epilog="Example: python3 tools/serve_bench.py --model /opt/models/staging/X.gguf "
               "--slots 4 --kv f16 --label ws4 --out llama.cpp/bench-step9-ws4.json",
    )
    ap.add_argument("--model", required=True, help="GGUF path (manifest-recorded, Rule 4)")
    ap.add_argument("--slots", type=int, required=True, help="llama-server -np value")
    ap.add_argument("--kv", default="f16", choices=["f16", "q8_0"], help="KV cache type (default f16 = canonical)")
    ap.add_argument("--fa", default="auto", choices=["on", "off", "auto"], help="flash attention (default auto)")
    ap.add_argument("--ctx-per-slot", type=int, default=4096, help="context per slot; -c is ALWAYS slots*this")
    ap.add_argument("--duration", type=int, default=45, help="measured window seconds (default 45)")
    ap.add_argument("--gen-tokens", type=int, default=128, help="n_predict per request (default 128 = tg128 semantics)")
    ap.add_argument("--port", type=int, default=8100)
    ap.add_argument("--load-timeout", type=float, default=180.0)
    ap.add_argument("--request-timeout", type=float, default=120.0)
    ap.add_argument("--label", required=True, help="config label for logs and JSON")
    ap.add_argument("--out", required=True, help="result JSON path")
    ap.add_argument("--extra", default="", help="extra llama-server args, space-separated (e.g. '-md /path/draft.gguf')")
    ap.add_argument("--dry-run", action="store_true", help="print server command and exit")
    args = ap.parse_args()

    out_path = Path(args.out)
    log_path = out_path.with_suffix(".serverlog")
    proc = start_server(args, log_path)
    result: dict = {"label": args.label, "config": vars(args).copy(), "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        wait_healthy(args.port, proc, args.load_timeout)
        # Rule 8 / F39: record what the server REPORTS, not only what we asked for.
        # A /props failure is a hard failure - if the server will not describe
        # itself we do not know what we benched, so let it propagate.
        try:
            props = http_json(f"http://127.0.0.1:{args.port}/props", timeout=10)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            raise RuntimeError(
                f"GET /props failed on port {args.port}: {exc}; "
                f"hint: without it the result cannot name the config it measured - "
                f"read {log_path} rather than recording the run unverified"
            ) from exc
        result["server_props"] = props_record(props)
        result["config_unverifiable"] = list(UNVERIFIABLE_FLAGS)
        result["config_divergence"] = config_divergence(args, result["server_props"])
        if result["config_divergence"]:
            for d in result["config_divergence"]:
                print(f"!! CONFIG DIVERGENCE {d['field']}: asked {d['intended']!r}, "
                      f"server reports {d['reported']!r}", file=sys.stderr)
        result["offload_gate"] = offload_gate(log_path)
        records: list[dict] = []
        lock = threading.Lock()
        barrier = threading.Barrier(args.slots)
        stop_at = [0.0]
        threads = [threading.Thread(target=worker, args=(t, args, barrier, stop_at, records, lock), daemon=True)
                   for t in range(args.slots)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=args.load_timeout + args.duration + 4 * args.request_timeout)
            if t.is_alive():
                raise TimeoutError(
                    "worker thread failed to finish inside its bounded window; "
                    "hint: server likely wedged - see .serverlog"
                )
        result["summary"] = summarize(records, args.slots)
        result["records"] = records
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=15)
        result["server_exit"] = proc.returncode
    out_path.write_text(json.dumps(result, indent=1))
    s = result.get("summary", {})
    d = s.get("delivery", {})
    print(f"{args.label}: slots={args.slots} kv={args.kv} "
          f"aggregate={s.get('aggregate_gen_tps')} t/s "
          f"per-stream-mean={s.get('mean_stream_gen_tps')} t/s "
          f"ttft_p50={s.get('ttft_ms_p50')}ms ok={s.get('requests_ok')} "
          f"under_sampled={s.get('under_sampled')}")
    print(f"  delivery: complete={d.get('complete')} failure={d.get('failure')} "
          f"transport_failed={d.get('transport_failed')} refusal={d.get('refusal_detected')} "
          f"| divergence={len(result.get('config_divergence', []))} "
          f"unverifiable={','.join(result.get('config_unverifiable', []))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
