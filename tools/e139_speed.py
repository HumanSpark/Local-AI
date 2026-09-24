#!/usr/bin/env python3
# File: e139_speed.py
# Purpose: E139 blocks 1-2 - serve one arm (halogen container or llama-server), time the fixed prompt set, record memory and power.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: One server per arm. --engine halogen runs the pinned image BY DIGEST in the
# foreground under podman (loopback-only port, models mounted read-only, no HALOGEN_DOWNLOAD so
# the container makes no outbound connections); --engine llama runs llama-server with the
# offload gate from run_longctx_eval.py. Both engines return llama-server-shaped `timings`, so
# prefill and decode rates are the SERVER's own (timings.prompt_per_second /
# predicted_per_second); client wall time per request is recorded beside them for the
# end-to-end ratio (P8). Prompts come from results/e139/prompts.json (tools/e139_prompts.py),
# non-overlapping so no request hits the other's prefix cache. A sampler thread records
# MemAvailable, amdgpu GTT+VRAM used and amdgpu power1_average at 1 Hz with timestamps, so
# each request gets its own power mean. Thinking is off on every request.
#
# Block 1 (default): P8K x3 and P32K x3 with the arm's default drafting (256 generated), then
# D1500 (512 generated) serial and, on halogen, with the MTP drafter.
# Block 2 (--identity): D1500 + the three P8K prompts, serial then MTP, texts compared byte for
# byte. Run it on a server started with HALOGEN_PROMPT_CACHE=0: the default cache mode is
# documented as NOT giving identical repeat answers, which would confound the test.

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_longctx_eval import assert_full_offload, wait_healthy  # noqa: E402

ROOT = Path("/home/agent-spark/sparkbench")
DRM = Path("/sys/class/drm/card0/device")
IMAGE = (
    "ghcr.io/peonist-ai/halogen-flash-server@"
    "sha256:6e626c979d536ab1edb07898e278be6686afd353758ea268817457f801d687dd"
)  # 0.13.8, MANIFEST
MODEL_ID = "halogen-qwen3.8-flash-next"


def power_path() -> Path:
    hits = sorted(DRM.glob("hwmon/hwmon*/power1_average"))
    if not hits:
        raise RuntimeError(
            f"no power1_average under {DRM}/hwmon. hint: amdgpu hwmon moved; "
            f"check /sys/class/hwmon/*/name for amdgpu"
        )
    return hits[0]


class Sampler(threading.Thread):
    """1 Hz timestamped samples; peak and per-window means are derived after the arm."""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.pw = power_path()
        self.samples: list[dict] = []
        self.stop = threading.Event()
        self.baseline = self.read()

    def read(self) -> dict:
        mem = {}
        for line in Path("/proc/meminfo").read_text().splitlines():
            k, v = line.split(":", 1)
            mem[k] = int(v.split()[0]) * 1024
        return {
            "t": time.time(),
            "avail": mem["MemAvailable"],
            "gpu": int((DRM / "mem_info_gtt_used").read_text())
            + int((DRM / "mem_info_vram_used").read_text()),
            "power_w": int(self.pw.read_text()) / 1e6,
        }

    def run(self) -> None:
        while not self.stop.is_set():
            self.samples.append(self.read())
            self.stop.wait(1.0)

    def power_mean(self, t0: float, t1: float) -> float | None:
        # None only when a request finished inside one sample interval - no reading to average.
        w = [s["power_w"] for s in self.samples if t0 <= s["t"] <= t1]
        return round(statistics.mean(w), 1) if w else None

    def summary(self) -> dict:
        gib = 1024**3
        return {
            "baseline_gpu_gib": round(self.baseline["gpu"] / gib, 2),
            "peak_gpu_gib": round(max(s["gpu"] for s in self.samples) / gib, 2),
            "gpu_delta_gib": round(
                (max(s["gpu"] for s in self.samples) - self.baseline["gpu"]) / gib, 2
            ),
            "min_memavailable_gib": round(
                min(s["avail"] for s in self.samples) / gib, 2
            ),
            "n_samples": len(self.samples),
        }


def ask(
    port: int,
    prompt: str,
    max_tokens: int,
    timeout: float,
    drafter: str | None,
    ready_timeout: float,
) -> dict:
    payload = {
        "model": MODEL_ID,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    if drafter:
        payload["drafter"] = (
            drafter  # halogen per-request switch, docs/FLAGS.md HALOGEN_DRAFTER_DEFAULT
        )
    body = json.dumps(payload).encode()
    deadline = time.time() + ready_timeout
    while True:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read().decode())
            break
        except urllib.error.HTTPError as e:
            # 503 while the engine finishes loading behind a live /health is a documented-shape
            # "not yet"; anything else, or 503 past the deadline, is a failure.
            if e.code != 503 or time.time() > deadline:
                raise RuntimeError(
                    f"HTTP {e.code} from :{port}: {e.read()[:300]!r}. "
                    f"hint: read the arm's .serverlog"
                ) from e
            time.sleep(5)
    t1 = time.time()
    t = d[
        "timings"
    ]  # both engines document it; missing means the wrong server answered
    return {
        "t0": t0,
        "t1": t1,
        "wall_s": round(t1 - t0, 2),
        "prompt_n": t["prompt_n"],
        "prompt_ms": round(t["prompt_ms"], 1),
        "prompt_per_second": round(t["prompt_per_second"], 2),
        "predicted_n": t["predicted_n"],
        "predicted_per_second": round(t["predicted_per_second"], 2),
        "cache_n": t.get("cache_n"),
        "draft_n": t.get("draft_n"),
        "draft_n_accepted": t.get("draft_n_accepted"),
        "finish_reason": d["choices"][0]["finish_reason"],
        "content": d["choices"][0]["message"].get("content") or "",
    }


def halogen_cmd(args: argparse.Namespace) -> list[str]:
    cmd = [
        "podman",
        "run",
        "--rm",
        "--name",
        f"e139-{args.label}",
        "-p",
        f"127.0.0.1:{args.port}:8731",
        "--device",
        "/dev/kfd",
        "--device",
        "/dev/dri",
        "--group-add",
        "keep-groups",
        "--ipc=host",
        "--ulimit",
        "memlock=-1:-1",
    ]
    for v in args.volume:
        cmd += ["-v", v]
    for e in args.env:
        cmd += ["-e", e]
    return cmd + [IMAGE]


def llama_cmd(args: argparse.Namespace) -> list[str]:
    # E91's Flash-Next config (tools/e91/run_e91.sh): -fa on, q8_0 KV. -c covers P32K + output.
    return [
        args.server_bin,
        "-m",
        args.model,
        "-c",
        str(args.ctx),
        "-np",
        "1",
        "-fa",
        "on",
        "-ctk",
        "q8_0",
        "-ctv",
        "q8_0",
        "-ngl",
        "999",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
        "--no-webui",
        "-v",
    ]


def wait_halogen(
    port: int, proc: subprocess.Popen, timeout: float, log_path: Path
) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"container exited rc={proc.returncode} before /health answered. "
                f"hint: read {log_path}"
            )
        try:
            with urllib.request.urlopen(
                f"http://127.0.0.1:{port}/health", timeout=5
            ) as r:
                if r.status == 200:
                    return json.loads(r.read().decode())
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass  # not listening yet - the expected state during load
        time.sleep(3)
    raise RuntimeError(
        f"/health not 200 within {timeout:.0f}s (P1 stop rule). hint: read {log_path}"
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E139: one arm's prefill/decode speed, memory and power.",
        epilog="example: e139_speed.py --engine halogen --label H0 "
        "-v /opt/models/staging/halogen-qwen3.8-flash-next:/models:ro "
        "--out results/e139/speed-H0.json",
    )
    ap.add_argument("--engine", choices=["halogen", "llama"], required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument(
        "-v",
        "--volume",
        action="append",
        default=[],
        help="halogen: podman -v, repeatable",
    )
    ap.add_argument(
        "-e",
        "--env",
        action="append",
        default=[],
        help="halogen: podman -e, repeatable",
    )
    ap.add_argument(
        "--server-bin", help="llama: the build is part of the config (F39) - no default"
    )
    ap.add_argument("--model", help="llama: GGUF path (first shard)")
    ap.add_argument("--ctx", type=int, default=40960)
    ap.add_argument(
        "--identity",
        action="store_true",
        help="run block 2 (serial vs MTP byte compare) instead of block 1",
    )
    ap.add_argument("--prompts", default=str(ROOT / "results/e139/prompts.json"))
    ap.add_argument("--port", type=int, default=8139)
    ap.add_argument(
        "--load-timeout",
        type=float,
        default=900.0,
        help="default 900 s, the P1 stop rule",
    )
    ap.add_argument(
        "--request-timeout",
        type=float,
        default=1800.0,
        help="default 1800 s: L0 at ~200 tok/s needs ~170 s for P32K, so this is slack, not a bound on H0",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--dry-run", action="store_true", help="print the server command and exit"
    )
    args = ap.parse_args()

    if args.engine == "llama" and not (args.server_bin and args.model):
        ap.error("--engine llama needs --server-bin and --model")
    if args.identity and args.engine != "halogen":
        ap.error("--identity tests halogen's drafter; llama-server has no MTP arm here")
    cmd = halogen_cmd(args) if args.engine == "halogen" else llama_cmd(args)
    if args.dry_run:
        print(" ".join(cmd))
        return 0

    P = json.loads(Path(args.prompts).read_text())["prompts"]
    halo = args.engine == "halogen"
    if args.identity:
        plan = [
            (f"{p}-{d}", P[p][i], 512 if p == "D1500" else 256, d)
            for p, i in [("D1500", 0), ("P8K", 0), ("P8K", 1), ("P8K", 2)]
            for d in ("serial", "mtp")
        ]
    else:
        plan = (
            [("P8K", x, 256, None) for x in P["P8K"]]
            + [("P32K", x, 256, None) for x in P["P32K"]]
            + [("D1500-serial", P["D1500"][0], 512, "serial" if halo else None)]
            + ([("D1500-mtp", P["D1500"][0], 512, "mtp")] if halo else [])
        )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    log_path = out.with_suffix(".serverlog")
    if halo:  # a container left by a killed run would hold the name and the port
        subprocess.run(
            ["podman", "rm", "-f", f"e139-{args.label}"],
            capture_output=True,
            timeout=120,
        )
    sampler = Sampler()
    sampler.start()
    result: dict = {
        "label": args.label,
        "engine": args.engine,
        "cmd": cmd,
        "identity": args.identity,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "runs": [],
    }
    with log_path.open("w") as log_f:
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
        try:
            t0 = time.time()
            if halo:
                result["health"] = wait_halogen(
                    args.port, proc, args.load_timeout, log_path
                )
            else:
                watcher = threading.Thread(
                    target=wait_healthy,
                    args=(args.port, args.load_timeout),
                    daemon=True,
                )
                watcher.start()
                while watcher.is_alive():
                    if proc.poll() is not None:
                        raise RuntimeError(
                            f"llama-server exited rc={proc.returncode}. hint: read {log_path}"
                        )
                    watcher.join(timeout=1)
                wait_healthy(args.port, 5)
                result["offload_gate"] = assert_full_offload(log_path)
            result["load_s"] = round(time.time() - t0, 1)
            for name, p, max_tok, drafter in plan:
                r = ask(
                    args.port,
                    p["text"],
                    max_tok,
                    args.request_timeout,
                    drafter,
                    args.load_timeout,
                )
                r.update(
                    {
                        "prompt": name,
                        "rep": p["rep"],
                        "prompt_sha": p["sha256"],
                        "drafter": drafter,
                        "power_w_mean": sampler.power_mean(r["t0"], r["t1"]),
                    }
                )
                result["runs"].append(r)
                print(
                    f"  {args.label} {name} rep{p['rep']}: prefill {r['prompt_per_second']} tok/s "
                    f"({r['prompt_n']} tok), decode {r['predicted_per_second']} ({r['predicted_n']} tok), "
                    f"wall {r['wall_s']}s, {r['power_w_mean']} W",
                    flush=True,
                )
        finally:
            if halo:
                subprocess.run(
                    ["podman", "stop", "-t", "30", f"e139-{args.label}"],
                    capture_output=True,
                    timeout=120,
                )
            proc.terminate()
            try:
                proc.wait(timeout=90)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=60)
            sampler.stop.set()
            sampler.join(timeout=5)
            result["memory"] = sampler.summary()
            result["power_samples_w"] = [
                (round(s["t"], 1), s["power_w"]) for s in sampler.samples
            ]
            out.write_text(
                json.dumps(result, indent=1)
            )  # partial results survive a failed arm

    if args.identity:
        pairs = {}
        for r in result["runs"]:
            pairs.setdefault(r["prompt"].rsplit("-", 1)[0] + f"#{r['rep']}", {})[
                r["drafter"]
            ] = r["content"]
        result["identity"] = {k: v["serial"] == v["mtp"] for k, v in pairs.items()}
        result["identity_equal"] = sum(result["identity"].values())
        print(
            f"{args.label}: identity {result['identity_equal']} of {len(pairs)} byte-equal {result['identity']}"
        )
    else:
        for name in ("P8K", "P32K"):
            xs = [r for r in result["runs"] if r["prompt"] == name]
            result[f"{name}_median_prefill_tps"] = statistics.median(
                r["prompt_per_second"] for r in xs
            )
            result[f"{name}_median_decode_tps"] = statistics.median(
                r["predicted_per_second"] for r in xs
            )
            result[f"{name}_median_wall_s"] = statistics.median(r["wall_s"] for r in xs)
        print(
            f"{args.label}: P32K prefill {result['P32K_median_prefill_tps']} / decode "
            f"{result['P32K_median_decode_tps']} tok/s median, wall {result['P32K_median_wall_s']}s; "
            f"peak GPU {result['memory']['peak_gpu_gib']} GiB"
        )
    out.write_text(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
