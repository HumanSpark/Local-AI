#!/usr/bin/env python3
# File: climb_envelope.py
# Purpose: Execute the envelope rung climb with server management
# Project: sparkbench | Date: 2026-07-11

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

LLAMA_SERVER_BIN = "/home/agent-spark/sparkbench/llama.cpp/build/bin/llama-server"
LLAMA_MODEL = "/opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf"


def wait_for_server(endpoint: str = "http://127.0.0.1:8100/health", timeout: int = 120) -> bool:
    """Wait for llama-server to be healthy."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            urllib.request.urlopen(endpoint, timeout=2)
            print(f"  Server healthy")
            return True
        except Exception:
            time.sleep(1)
    print(f"  Server never became healthy")
    return False


def run_rung(
    rung_tokens: int,
    rung_name: str,
    ctx: int,
    np_val: int = 1,
) -> dict[str, str | int | float | bool] | None:
    """
    Execute a single rung: start server, run eval, return result.

    Args:
        rung_tokens: target tokens (for naming/identification)
        rung_name: '48k', '64k', etc.
        ctx: context window size
        np_val: number of parallel slots

    Returns:
        Result dict with 'passed', 'accuracy', 'wall_clock_max', 'usable' keys, or None if failed.
    """
    corpus_path = f"spikes/deep-eval/envelope/corpus-{rung_name}-probe.txt"
    output_path = f"results/deep-eval/e30-config1-{rung_name}.json"

    if not Path(corpus_path).exists():
        print(f"  ERROR: corpus not found: {corpus_path}")
        return None

    print(f"\n{'='*60}")
    print(f"RUNG: {rung_name} (CTX={ctx}, corpus {rung_tokens//1000}K)")
    print(f"{'='*60}")

    # Kill any existing server
    subprocess.run(["pkill", "-9", "llama-server"], stderr=subprocess.DEVNULL)
    time.sleep(1)

    # Start server
    print(f"Starting llama-server (CTX={ctx}, NP={np_val})...")
    server_proc = subprocess.Popen(
        [
            LLAMA_SERVER_BIN,
            "-m", LLAMA_MODEL,
            "-c", str(ctx),
            "-np", str(np_val),
            "--host", "127.0.0.1",
            "--port", "8100",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for startup
    print(f"Waiting for server startup (high context may take time)...")
    time.sleep(max(30, ctx // 2000))  # Scale wait time with context

    if not wait_for_server(timeout=180):
        server_proc.terminate()
        return None

    # Run evaluation
    print(f"Running probe suite (6 tests)...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "tools/eval_envelope.py",
                "--corpus", corpus_path,
                "--rung-name", rung_name,
                "--timeout", "600",  # 10 min per query
                "--output", output_path,
            ],
            timeout=900,  # 15 min total
            capture_output=True,
            text=True,
        )

        # Parse result
        if result.returncode == 0 and Path(output_path).exists():
            with open(output_path) as f:
                data = json.load(f)

            passed = data["summary"]["passed"]
            usable = data["summary"]["usable"]

            # Extract wall-clock times
            first_q_time = max(
                t.get("wall_clock_seconds", 0)
                for t in data["tests"][:1]
            )
            follow_q_time = max(
                t.get("wall_clock_seconds", 0)
                for t in data["tests"][1:2]
            )

            print(f"  Result: {passed}/6 passed (usable={usable})")
            print(f"  Latency: first={first_q_time:.1f}s, follow={follow_q_time:.1f}s")

            return {
                "rung": rung_name,
                "passed": passed,
                "accuracy": f"{passed}/6",
                "usable": usable,
                "first_q_time": first_q_time,
                "follow_q_time": follow_q_time,
            }
        else:
            print(f"  ERROR: eval failed or output missing")
            if result.stderr:
                print(f"  STDERR: {result.stderr[:200]}")
            return None

    except subprocess.TimeoutExpired:
        print(f"  ERROR: eval timeout (>15 min)")
        return None
    except Exception as e:
        print(f"  ERROR: {e}")
        return None
    finally:
        # Stop server
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()


def main():
    os.chdir("/home/agent-spark/sparkbench")

    # Rungs to climb (Config 1: workhorse Q4_K_M, Vulkan, F16 KV)
    rungs = [
        (48000, "48k", 50176),
        (64000, "64k", 66176),
        (80000, "80k", 82176),
        (96000, "96k", 98176),  # Will hit corpus limit (~86K tokens)
    ]

    results = []
    for rung_tokens, rung_name, ctx in rungs:
        # Banking audit before rung
        audit = subprocess.run(["bash", "tools/banking_audit.sh"], capture_output=True, text=True)
        if "AUDIT-FAIL" in audit.stdout:
            print(f"\n!!! AUDIT FAIL before {rung_name} !!!")
            print(audit.stdout)
            break

        # Run rung
        result = run_rung(rung_tokens, rung_name, ctx)

        if result is None:
            print(f"\n{rung_name} failed - stopping climb")
            break

        results.append(result)

        # Commit after each rung
        subprocess.run(["git", "add", f"results/deep-eval/e30-config1-{rung_name}.json"])
        commit_msg = f"results: E30 Config 1 {rung_name} rung - {result['accuracy']} usable={result['usable']}"
        subprocess.run(["git", "commit", "-m", commit_msg], capture_output=True)
        subprocess.run(["git", "push", "-q"], capture_output=True)
        print(f"Committed and pushed {rung_name}")

        # Stop if not usable
        if not result["usable"]:
            print(f"\n{rung_name} not usable - stopping Config 1 climb")
            break

        time.sleep(2)  # Brief pause between rungs

    # Summary
    print(f"\n{'='*60}")
    print(f"CONFIG 1 CLIMB COMPLETE")
    print(f"{'='*60}")
    for r in results:
        print(f"  {r['rung']}: {r['accuracy']} usable={r['usable']} (first={r['first_q_time']:.0f}s)")

    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
