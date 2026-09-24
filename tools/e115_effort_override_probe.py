#!/usr/bin/env python3
# File: e115_effort_override_probe.py
# Purpose: E115 - does a PER-REQUEST reasoning_effort still override llama-server's --reasoning-effort flag?
# Project: sparkbench | Date: 2026-09-06
#
# Overview: docs/plans/2026-09-06-serving-reasoning-effort-proposal.md asks
# sparkrouter to add `--reasoning-effort medium` for Qwen3.8-27B, and names this
# as the first thing that could reject the proposal outright: if the server flag
# is a HARD override rather than a default, every caller currently asking for
# xhigh deliberately silently stops getting it. The proposal says test it before
# applying. Nobody has.
#
# Four cells, two server starts. The B cells are the POSITIVE CONTROL and they
# are not optional: without them, "A2 looks like A1" is indistinguishable
# between "the flag is a hard override" and "my metric cannot tell medium from
# xhigh at all". That is the vacuous-success shape this repo keeps meeting.
#
#   cell  server flag        request param      reads as
#   A1    --reasoning-effort medium   (none)    medium, if the flag is applied
#   A2    --reasoning-effort medium   xhigh     xhigh, IF the request overrides
#   B1    (none)                      (none)    xhigh - the template default
#   B2    (none)                      medium    medium - the per-request path
#
# Metric: reasoning tokens actually emitted, at temperature 0 so one sample per
# cell is a measurement rather than a draw. The signal is a ratio between cells,
# never an absolute count.

from __future__ import annotations

import argparse
import json
import subprocess
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_BIN = REPO / "llama.cpp/wt/b10435/build/bin/llama-server"
MODEL = "/opt/models/staging/Qwen3.8-27B-Q4_K_M.gguf"

# Short, deterministic, and the kind of thing effort actually changes: a problem
# with a real answer that rewards deliberation but does not require it.
PROMPTS = [
    ("counting",
     "A bag holds 3 red, 4 blue and 5 green marbles. You draw three without "
     "replacement. What is the probability all three are the same colour? "
     "Give the exact fraction in lowest terms."),
    ("scheduling",
     "Five tasks take 3, 1, 4, 1 and 5 hours. Two identical workers run them in "
     "parallel, each task on one worker, no splitting. What is the minimum "
     "possible makespan, and which split achieves it?"),
]


def wait_healthy(port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as r:
                if r.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001 - poll boundary, retried
            last = exc
        time.sleep(2)
    raise RuntimeError(
        f"server not healthy on {port} within {timeout}s (last: {last}). "
        f"hint: read the server log before assuming a port clash"
    )


def ask(port: int, prompt: str, effort: str | None, max_tokens: int,
        timeout: float) -> dict:
    payload: dict = {"messages": [{"role": "user", "content": prompt}],
                     "temperature": 0, "max_tokens": max_tokens}
    if effort is not None:
        payload["reasoning_effort"] = effort
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    ch = d["choices"][0]
    msg = ch["message"]
    reasoning = msg.get("reasoning_content") or ""
    return {
        "reasoning_chars": len(reasoning),
        "completion_tokens": d.get("usage", {}).get("completion_tokens"),
        "finish_reason": ch.get("finish_reason"),
        "answer_tail": (msg.get("content") or "")[-160:],
        "wall_s": round(time.time() - t0, 2),
    }


def serve(bin_path: Path, port: int, log: Path, extra: list[str]) -> subprocess.Popen:
    cmd = [str(bin_path), "-m", MODEL, "-c", "32768", "-np", "1",
           "--host", "127.0.0.1", "--port", str(port), "--no-webui", "-v", *extra]
    fh = log.open("w")
    print("server:", " ".join(cmd), flush=True)
    return subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT)


def assert_full_offload(log: Path) -> int:
    """Rule 3: zero offload evidence is a FAIL, never a pass."""
    import re
    text = log.read_text(errors="replace")
    devs = re.findall(r"layer\s+\d+\s+assigned to device\s+([A-Za-z0-9_]+)", text)
    if not devs:
        raise RuntimeError(
            f"full-offload gate FAILED: no 'assigned to device' lines in {log}. "
            f"hint: the server must run with -v or the gate cannot be evidenced")
    cpu = [d for d in devs if d == "CPU"]
    if cpu:
        raise RuntimeError(
            f"full-offload gate FAILED: {len(cpu)}/{len(devs)} layers on CPU. "
            f"hint: this is not a GPU measurement")
    return len(devs)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument("--port", type=int, default=8117)
    ap.add_argument("--max-tokens", type=int, default=3072)
    ap.add_argument("--request-timeout", type=float, default=900.0)
    ap.add_argument("--server-bin", default=str(DEFAULT_BIN))
    a = ap.parse_args()

    out = Path(a.out)
    if out.is_dir():
        raise SystemExit(f"--out {a.out!r} is a directory; it names the results FILE")
    out.parent.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []
    arms = [
        ("A", ["--reasoning-effort", "medium"], [("A1", None), ("A2", "xhigh")]),
        ("B", [],                               [("B1", None), ("B2", "medium")]),
    ]
    for arm, extra, cells in arms:
        log = out.parent / f"e115-server-{arm}.serverlog"
        proc = serve(Path(a.server_bin), a.port, log, extra)
        try:
            wait_healthy(a.port, 300)
            layers = assert_full_offload(log)
            print(f"arm {arm}: full-offload gate OK, {layers} layers", flush=True)
            for cell, effort in cells:
                for name, prompt in PROMPTS:
                    r = ask(a.port, prompt, effort, a.max_tokens, a.request_timeout)
                    r.update({"arm": arm, "cell": cell, "server_flag": " ".join(extra) or "(none)",
                              "request_effort": effort or "(none)", "prompt": name})
                    results.append(r)
                    print(f"  {cell} {name:11s} reasoning_chars={r['reasoning_chars']:>6} "
                          f"completion_tokens={r['completion_tokens']:>5} "
                          f"{r['finish_reason']:>6} {r['wall_s']}s", flush=True)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
            time.sleep(5)

    out.write_text(json.dumps({
        "model": MODEL, "max_tokens": a.max_tokens,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "results": results}, indent=2))
    print(f"\nwritten: {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
