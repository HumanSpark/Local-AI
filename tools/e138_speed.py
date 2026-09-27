#!/usr/bin/env python3
# File: e138_speed.py
# Purpose: E138 block 1 - serve one arm, time real CODE and CHAT prompts, record draft acceptance and peak memory.
# Project: sparkbench | Date: 2026-09-22
#
# Overview: One llama-server per arm (model + optional DFlash2 drafter), health-waited and
# offload-gated with the helpers from run_longctx_eval.py. Each prompt runs --reps times at
# temperature 0; speed is the SERVER's own timings.predicted_per_second (not client wall
# time), and draft acceptance comes from timings.draft_n / draft_n_accepted. A sampler thread
# polls amdgpu GTT+VRAM used and MemAvailable every 0.5 s from before launch to after the last
# request, so peak memory is measured against the idle baseline rather than assumed from file
# sizes - the claim under test is "10.1 GB of RAM total".
#
# CODE is agentic-shaped: an edit request with a real ~3 KB Python class in context, so the
# output is mostly code the drafter can predict. CHAT is open prose. F85 found speculation's
# gain depends on exactly this split, so both are always run.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_longctx_eval import assert_full_offload, wait_healthy  # noqa: E402

ROOT = Path("/home/agent-spark/sparkbench")
DRM = Path("/sys/class/drm/card0/device")

CODE_SRC = (ROOT / "tools/cloud_client.py").read_text()
_start = CODE_SRC.index("class CloudBudget:")
CODE_CLASS = CODE_SRC[_start: CODE_SRC.index("\n\n\n", _start)]
PROMPTS = {
    "CODE": ("Here is a Python class from our codebase:\n\n```python\n" + CODE_CLASS + "\n```\n\n"
             "Add a `reset()` method that zeroes every counter, and a `remaining_usd()` method "
             "that returns how much of the ceiling is left (never negative). Return the complete "
             "updated class in one code block."),
    "CHAT": ("A small accountancy firm is deciding whether to run an AI model on a computer in "
             "their own office instead of paying for a cloud service. Explain the trade-offs they "
             "should weigh, in plain English, in about five paragraphs."),
}


def read_mem() -> dict:
    meminfo = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k, v = line.split(":", 1)
        meminfo[k] = int(v.split()[0]) * 1024
    return {"gtt": int((DRM / "mem_info_gtt_used").read_text()),
            "vram": int((DRM / "mem_info_vram_used").read_text()),
            "used": meminfo["MemTotal"] - meminfo["MemAvailable"]}


class MemSampler(threading.Thread):
    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.baseline = read_mem()
        self.peak = dict(self.baseline)
        self.stop = threading.Event()

    def run(self) -> None:
        while not self.stop.is_set():
            m = read_mem()
            for k in m:
                self.peak[k] = max(self.peak[k], m[k])
            self.stop.wait(0.5)

    def summary(self) -> dict:
        gib = 1024 ** 3
        return {
            "baseline_bytes": self.baseline, "peak_bytes": self.peak,
            "gpu_delta_gib": round((self.peak["gtt"] + self.peak["vram"]
                                    - self.baseline["gtt"] - self.baseline["vram"]) / gib, 2),
            "system_used_delta_gib": round((self.peak["used"] - self.baseline["used"]) / gib, 2),
        }


def ask(port: int, prompt: str, max_tokens: int, timeout: float) -> dict:
    body = json.dumps({"messages": [{"role": "user", "content": prompt}],
                       "temperature": 0, "max_tokens": max_tokens}).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    t = d["timings"]  # llama-server always returns it; missing means a different server
    msg = d["choices"][0]["message"]
    return {"predicted_n": t["predicted_n"], "predicted_per_second": round(t["predicted_per_second"], 2),
            "prompt_n": t["prompt_n"], "prompt_per_second": round(t["prompt_per_second"], 2),
            "draft_n": t.get("draft_n"), "draft_n_accepted": t.get("draft_n_accepted"),
            "finish_reason": d["choices"][0]["finish_reason"],
            "content_chars": len(msg.get("content") or ""),
            "reasoning_chars": len(msg.get("reasoning_content") or "")}


def main() -> int:
    ap = argparse.ArgumentParser(description="E138 block 1: one arm's decode speed, acceptance and memory.",
                                 epilog="example: e138_speed.py --label B1 --server-bin llama.cpp/wt/prism/build/bin/llama-server "
                                        "--model /opt/models/staging/Ternary-Bonsai-2-27B-PTQ1_0.gguf "
                                        "--draft /opt/models/staging/Bonsai-2-27B-DFlash2-Q8_0.gguf --out results/e138/B1.json")
    ap.add_argument("--label", required=True)
    ap.add_argument("--server-bin", required=True, help="the build is part of the config (F39) - no default")
    ap.add_argument("--model", required=True)
    ap.add_argument("--draft", default=None, help="DFlash2 drafter GGUF; omit for plain autoregressive")
    ap.add_argument("--draft-n-max", type=int, default=4, help="default 4, the n=4 optimum in the UntR Strix Halo sweep")
    ap.add_argument("--ctx", type=int, default=16384)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--port", type=int, default=8130)
    ap.add_argument("--load-timeout", type=float, default=600.0)
    ap.add_argument("--request-timeout", type=float, default=900.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dry-run", action="store_true", help="print the server command and exit")
    args = ap.parse_args()

    cmd = [args.server_bin, "-m", args.model, "-c", str(args.ctx), "-np", "1", "-fa", "on",
           "-ngl", "999", "--host", "127.0.0.1", "--port", str(args.port), "--no-webui", "-v"]
    if args.draft:
        cmd += ["-md", args.draft, "-ngld", "999", "--spec-type", "draft-dflash",
                "--spec-draft-n-max", str(args.draft_n_max)]
    if args.dry_run:
        print(" ".join(cmd))
        return 0

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    log_path = out.with_suffix(".serverlog")
    sampler = MemSampler()
    sampler.start()
    result: dict = {"label": args.label, "cmd": cmd, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "runs": []}
    with log_path.open("w") as log_f:
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
        try:
            t0 = time.time()
            # Poll the process too: wait_healthy alone spends the whole timeout on a server that
            # already exited (a drafter load failure cost 600 s this way on 2026-09-22).
            watcher = threading.Thread(target=wait_healthy, args=(args.port, args.load_timeout), daemon=True)
            watcher.start()
            while watcher.is_alive():
                if proc.poll() is not None:
                    raise RuntimeError(f"llama-server exited rc={proc.returncode} before becoming healthy. "
                                       f"hint: read the ' E ' lines in {log_path}")
                watcher.join(timeout=1)
            wait_healthy(args.port, 5)  # re-raise here if the watcher timed out rather than succeeded
            result["load_s"] = round(time.time() - t0, 1)
            result["offload_gate"] = assert_full_offload(log_path)
            with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/props", timeout=10) as r:
                props = json.loads(r.read().decode())
            result["server_props_build"] = props.get("build_info")
            for name, prompt in PROMPTS.items():
                for rep in range(args.reps):
                    r = ask(args.port, prompt, args.max_tokens, args.request_timeout)
                    r.update({"prompt": name, "rep": rep})
                    result["runs"].append(r)
                    acc = (f" acc {r['draft_n_accepted']}/{r['draft_n']}" if r["draft_n"] else "")
                    print(f"  {args.label} {name} rep{rep}: {r['predicted_per_second']} tok/s "
                          f"({r['predicted_n']} tok, {r['finish_reason']}){acc}", flush=True)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=60)
            sampler.stop.set()
            sampler.join(timeout=5)
    result["memory"] = sampler.summary()
    for name in PROMPTS:
        tps = sorted(r["predicted_per_second"] for r in result["runs"] if r["prompt"] == name)
        result[f"median_tps_{name}"] = tps[len(tps) // 2]
    out.write_text(json.dumps(result, indent=2))
    print(f"{args.label}: CODE {result['median_tps_CODE']} / CHAT {result['median_tps_CHAT']} tok/s median; "
          f"GPU +{result['memory']['gpu_delta_gib']} GiB, system +{result['memory']['system_used_delta_gib']} GiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
