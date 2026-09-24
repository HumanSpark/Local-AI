#!/usr/bin/env python3
# File: soak_load.py
# Purpose: Repeated controlled load+first-decode cycles on one model, to measure a FAULT RATE rather than diagnose a cause.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: S-H2 (AMENDMENT 3) gates every unattended role for gpt-oss-120b on
# the unexplained load/decode failure of 2026-08-19 being understood OR shown
# rare under repeated controlled loading. This tool does the second half. It
# drives N independent cycles - start server, wait for /health, send ONE trivial
# streaming prompt, tear down - and classifies each into a pre-registered
# outcome class (see the E71 entry in results/experiments.md).
#
# IT DOES NOT DIAGNOSE. The output is a rate and a fingerprint. Naming a
# mechanism for a Vulkan/RADV stall is out of scope and is not claimed.
#
# WHY THE PROMPT IS TRIVIAL. This measures the load-and-first-decode path. A
# capability figure must never be read out of it, so the prompt is chosen to
# make that reading obviously wrong: ten tokens in, 32 out.
#
# WHY IT STREAMS. Time to FIRST token is stamped separately from completion.
# A stalled decode and a runaway generation are both one long silence to a
# non-streaming client, and separating them is the point of the exercise.
#
# THE ABORT RULE IS LOAD-BEARING. docs/memory-edge-deadlock.md documents an
# amdgpu suballocator deadlock that only a hard power cycle clears. The
# 2026-08-19 fault was NOT it on six axes - but "not that, observed once" is not
# "never that". If a server survives SIGKILL, or VRAM parks at exactly 2.00 GiB
# across two samples, this stops rather than starting another cycle. Hammering a
# wedged GPU is how a recoverable fault becomes a power cycle.
#
# RESULTS ARE FLUSHED AFTER EVERY ITERATION, so a wedge still leaves the
# evidence for every cycle that completed before it.

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
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke_first_token import PROMPT, stream_first_token  # noqa: E402

DEFAULT_SERVER = (
    "/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server"
)
VRAM = Path("/sys/class/drm/card0/device/mem_info_vram_used")
GTT = Path("/sys/class/drm/card0/device/mem_info_gtt_used")
PARK_BYTES = 2147483648  # 2.00 GiB exactly - the documented deadlock park value


def evict_from_page_cache(first_shard: Path) -> dict[str, Any]:
    """Drop every shard of a multi-part GGUF from the page cache. No root needed.

    WHY THIS EXISTS. E71 measured 25/25 clean at a 22.0s median load - but the
    documented cold load of this model is 117.68s and the 2026-08-19 fault
    struck a load that read 57.65 GiB off disk. A warm soak may therefore have
    had NO POWER against the fault it was measuring, which makes a clean result
    far weaker than its n suggests.

    posix_fadvise(DONTNEED) evicts exactly these files' pages and nothing else.
    `echo 3 > /proc/sys/vm/drop_caches` needs root this account does not have,
    and would flush every unrelated page on the box as well.

    Eviction is BEST EFFORT and says so: the kernel may decline to drop pages
    that are dirty or still mapped. The resulting load time is the evidence that
    it worked, which is why load_s is reported per iteration and not only as a
    median.
    """
    stem = first_shard.name
    if "00001-of-" in stem:
        shards = sorted(first_shard.parent.glob(stem.replace("00001-of-", "*-of-")))
    else:
        shards = [first_shard]
    if not shards:
        shards = [first_shard]
    detail = []
    for sh in shards:
        try:
            fd = os.open(str(sh), os.O_RDONLY)
        except OSError as exc:
            detail.append({"file": sh.name, "ok": False, "error": str(exc)})
            continue
        try:
            os.posix_fadvise(fd, 0, 0, os.POSIX_FADV_DONTNEED)
            detail.append({"file": sh.name, "ok": True, "bytes": sh.stat().st_size})
        finally:
            os.close(fd)
    return {"shards": len(shards), "detail": detail}


def _read_int(p: Path) -> int | None:
    """Sysfs counter, or None when it cannot be read. Never invent a value."""
    try:
        return int(p.read_text().strip())
    except (OSError, ValueError):
        return None


def vram_parked() -> bool:
    """Two samples five seconds apart, both exactly at the park value.

    One sample cannot tell a deadlock from a healthy load PASSING THROUGH
    2.00 GiB on its way up, which is why is_it_stuck.sh samples twice too.
    """
    a = _read_int(VRAM)
    if a != PARK_BYTES:
        return False
    time.sleep(5)
    return _read_int(VRAM) == PARK_BYTES


def kill_server(proc: subprocess.Popen, grace: float = 30.0) -> str:
    """Tear the server down. Returns how it died - that IS evidence.

    A process surviving SIGKILL is the deadlock's signature (SIGKILL is inert
    in the drm_suballoc_new path), so the return value feeds the abort rule.
    """
    if proc.poll() is not None:
        return "already_exited"
    proc.terminate()
    try:
        proc.wait(timeout=grace)
        return "sigterm"
    except subprocess.TimeoutExpired:
        pass
    proc.kill()
    try:
        proc.wait(timeout=grace)
        return "sigkill"
    except subprocess.TimeoutExpired:
        return "survived_sigkill"


def wait_healthy(
    port: int, proc: subprocess.Popen, load_timeout: float, log_path: Path
) -> tuple[str, float, int | None]:
    """Poll /health. Returns (state, elapsed_s, peak_gtt_bytes).

    Peak GTT is sampled during the wait because it is the only cheap witness
    that the weights actually landed on the device.
    """
    t0 = time.time()
    peak_gtt = _read_int(GTT) or 0
    while time.time() - t0 < load_timeout:
        if proc.poll() is not None:
            return ("server_crashed", time.time() - t0, peak_gtt or None)
        g = _read_int(GTT)
        if g is not None and g > peak_gtt:
            peak_gtt = g
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=5
            ) as h:
                if h.status == 200:
                    return ("healthy", time.time() - t0, peak_gtt or None)
        except Exception:  # noqa: BLE001 - poll boundary; absence is expected here
            pass
        time.sleep(2)
    return ("load_timeout", time.time() - t0, peak_gtt or None)


def classify(health_state: str, r: dict[str, Any] | None) -> str:
    """One of the E71 pre-registered outcome classes. Registered 2026-08-19."""
    if health_state != "healthy":
        return health_state
    assert r is not None
    if r["outcome"] == "transport_failed" and r["ttft_s"] is None:
        return "stalled_before_first_token"
    if r["outcome"] == "transport_failed":
        return "tokens_then_no_termination"
    if r["outcome"] == "completed" and r["chunks"] > 0:
        return "ok"
    return "unclear"


def run_iteration(i: int, args: argparse.Namespace, raw_dir: Path) -> dict[str, Any]:
    """One complete independent cycle. Every failure shape is a RESULT, not an error."""
    log_path = raw_dir / f"{args.label}-iter{i:03d}.serverlog"
    cmd = [
        args.server_bin,
        "-m",
        args.model,
        "-c",
        str(args.ctx),
        "-np",
        "1",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
        "--no-webui",
        "-v",
    ]
    if args.server_extra:
        cmd += args.server_extra.split()

    rec: dict[str, Any] = {
        "iteration": i,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    if args.cold:
        ev = evict_from_page_cache(Path(args.model))
        rec["evicted"] = ev
        print(f"    evicted {ev['shards']} shard(s) from page cache", flush=True)
    log_f = log_path.open("w")
    t_start = time.time()
    proc = subprocess.Popen(
        cmd, stdout=log_f, stderr=subprocess.STDOUT, preexec_fn=os.setsid
    )
    smoke: dict[str, Any] | None = None
    try:
        state, load_s, peak_gtt = wait_healthy(
            args.port, proc, args.load_timeout, log_path
        )
        rec["health_state"] = state
        rec["load_s"] = round(load_s, 2)
        rec["peak_gtt_bytes"] = peak_gtt
        rec["peak_gtt_gib"] = round(peak_gtt / 1024**3, 2) if peak_gtt else None
        if state == "healthy":
            print(
                f"    loaded in {load_s:.1f}s (GTT peak {rec['peak_gtt_gib']} GiB) "
                f"- sending smoke prompt",
                flush=True,
            )
            smoke = stream_first_token(
                args.port, args.max_tokens, args.timeout, args.thinking
            )
            rec["smoke"] = smoke
        else:
            print(f"    {state} after {load_s:.1f}s", flush=True)
    finally:
        death = kill_server(proc)
        rec["teardown"] = death
        log_f.close()

    rec["outcome"] = classify(rec["health_state"], smoke)
    rec["cycle_s"] = round(time.time() - t_start, 2)
    rec["serverlog"] = str(log_path)
    rec["serverlog_bytes"] = log_path.stat().st_size if log_path.exists() else None

    # The abort conditions, evaluated on THIS iteration's evidence.
    rec["survived_sigkill"] = death == "survived_sigkill"
    rec["vram_parked"] = vram_parked() if death == "survived_sigkill" else False
    rec["possible_deadlock"] = rec["survived_sigkill"] or rec["vram_parked"]

    # An `ok` iteration's serverlog carries no information a summary does not.
    # Keep every failure's log in full - that is the evidence a diagnosis needs.
    if rec["outcome"] == "ok" and not args.keep_all_logs and log_path.exists():
        rec["serverlog_removed"] = True
        log_path.unlink()
    return rec


def summarise(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate. Reports the fields E71's predictions are scored against."""
    ok = [r for r in records if r["outcome"] == "ok"]
    failed = [r for r in records if r["outcome"] != "ok"]
    loads = [
        r["load_s"]
        for r in records
        if r.get("load_s") is not None and r["health_state"] == "healthy"
    ]
    by_class: dict[str, int] = {}
    for r in records:
        by_class[r["outcome"]] = by_class.get(r["outcome"], 0) + 1

    def med(xs: list[float]) -> float | None:
        if not xs:
            return None
        s = sorted(xs)
        n = len(s)
        return round(s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2, 2)

    first5, last5 = med(loads[:5]), med(loads[-5:])
    drift = None
    if first5 and last5:
        drift = round((last5 - first5) / first5 * 100, 1)
    ttfts = [r["smoke"]["ttft_s"] for r in ok if r.get("smoke", {}).get("ttft_s")]
    return {
        "iterations": len(records),
        "iterations_ok": len(ok),
        "iterations_failed": len(failed),
        "possible_deadlock": sum(1 for r in records if r["possible_deadlock"]),
        "by_outcome": by_class,
        "load_s_median": med(loads),
        "load_s_min": round(min(loads), 2) if loads else None,
        "load_s_max": round(max(loads), 2) if loads else None,
        "load_s_first5_median": first5,
        "load_s_last5_median": last5,
        "load_drift_pct": drift,
        "ttft_s_median": med(ttfts),
        "failed_iterations": [r["iteration"] for r in failed],
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Repeated load+first-decode soak. Measures a rate, not a cause.",
        epilog=(
            "example: python3 tools/soak_load.py "
            "--model /opt/models/staging/gpt-oss-120b-mxfp4-00001-of-00003.gguf "
            "--iterations 25 --label e71-gptoss120b"
        ),
    )
    ap.add_argument("--model", required=True, help="first shard of the GGUF")
    ap.add_argument("--iterations", type=int, default=25)
    ap.add_argument("--label", default="soak")
    ap.add_argument("--ctx", type=int, default=8192)
    ap.add_argument("--max-tokens", type=int, default=32)
    ap.add_argument(
        "--timeout",
        type=float,
        default=180.0,
        help="HARD ceiling on the smoke request, in seconds",
    )
    ap.add_argument("--load-timeout", type=float, default=900.0)
    ap.add_argument(
        "--settle",
        type=float,
        default=10.0,
        help="seconds between iterations, for GTT to be reclaimed",
    )
    ap.add_argument(
        "--thinking",
        default="default",
        choices=["default", "off", "low", "medium", "xhigh"],
    )
    ap.add_argument("--server-bin", default=DEFAULT_SERVER)
    ap.add_argument("--server-extra", default="")
    ap.add_argument("--port", type=int, default=8123)
    ap.add_argument(
        "--cold",
        action="store_true",
        help="evict the model from the page cache before every iteration, so "
        "each load reads from disk (no root required)",
    )
    ap.add_argument(
        "--keep-all-logs",
        action="store_true",
        help="retain serverlogs for successful iterations too",
    )
    ap.add_argument(
        "--out", required=True, help="JSON results path (flushed every iteration)"
    )
    args = ap.parse_args()

    if not Path(args.model).exists():
        raise SystemExit(
            f"model not found: {args.model}\n"
            f"hint: pass the FIRST shard of a multi-shard GGUF"
        )
    if not Path(args.server_bin).exists():
        raise SystemExit(
            f"server binary not found: {args.server_bin}\n"
            f"hint: check llama.cpp/wt/<build>/build/bin/llama-server"
        )

    # Rule 9: exactly one GPU consumer. Refuse rather than contend - memory
    # contention is the documented deadlock trigger.
    r = subprocess.run(["pgrep", "-x", "llama-server"], capture_output=True, text=True)
    if r.stdout.strip():
        raise SystemExit(
            f"llama-server already running (pids {r.stdout.split()})\n"
            f"hint: one GPU consumer at a time - `pkill -x llama-server`"
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw_dir = out.parent

    records: list[dict[str, Any]] = []
    meta = {
        "label": args.label,
        "model": args.model,
        "iterations_planned": args.iterations,
        "ctx": args.ctx,
        "max_tokens": args.max_tokens,
        "request_timeout_s": args.timeout,
        "load_timeout_s": args.load_timeout,
        "thinking": args.thinking,
        "server_bin": args.server_bin,
        "server_extra": args.server_extra,
        "prompt": PROMPT,
        "cold": args.cold,
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "kernel": subprocess.run(
            ["uname", "-r"], capture_output=True, text=True
        ).stdout.strip(),
    }
    t0 = time.time()
    aborted: str | None = None

    for i in range(1, args.iterations + 1):
        el = time.time() - t0
        print(
            f"[{i}/{args.iterations}] elapsed {el / 60:.1f}min - starting server",
            flush=True,
        )
        rec = run_iteration(i, args, raw_dir)
        records.append(rec)
        print(
            f"  -> {rec['outcome']} ({rec['cycle_s']}s, teardown={rec['teardown']})",
            flush=True,
        )

        payload = {
            "meta": meta,
            "summary": summarise(records),
            "iterations": records,
            "aborted": aborted,
        }
        out.write_text(json.dumps(payload, indent=2))

        if rec["possible_deadlock"]:
            aborted = (
                f"ABORT at iteration {i}: possible deadlock "
                f"(survived_sigkill={rec['survived_sigkill']}, "
                f"vram_parked={rec['vram_parked']}). "
                f"hint: read docs/memory-edge-deadlock.md; a hard power "
                f"cycle may be required before the GPU is usable again"
            )
            print(f"\n!!! {aborted}", file=sys.stderr, flush=True)
            payload["aborted"] = aborted
            out.write_text(json.dumps(payload, indent=2))
            break

        if i < args.iterations:
            time.sleep(args.settle)

    s = summarise(records)
    print(f"\n=== {args.label}: {s['iterations_ok']}/{s['iterations']} ok ===")
    print(f"  by outcome        : {s['by_outcome']}")
    print(f"  possible_deadlock : {s['possible_deadlock']}")
    print(
        f"  load_s median     : {s['load_s_median']}  "
        f"(min {s['load_s_min']}, max {s['load_s_max']})"
    )
    print(
        f"  load drift        : first5 {s['load_s_first5_median']} -> "
        f"last5 {s['load_s_last5_median']}  ({s['load_drift_pct']}%)"
    )
    print(f"  ttft median       : {s['ttft_s_median']}")
    print(f"  written           : {out}")
    return 3 if aborted else 0


if __name__ == "__main__":
    sys.exit(main())
