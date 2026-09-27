# File: e146-gates.md
# Purpose: Record of the E146 pre-run gates (G1-G7) for the Atlas inference engine test, with what each found.
# Project: sparkbench | Date: 2026-09-25
#
# Overview: results/e146-prereg.md registered six CPU-only gates before any GPU window. This file records
# their outcomes as measured on 2026-09-25 (00:00-01:20). Nothing has run on the GPU. G5 changed the design,
# which Amendment 1 of the prereg declares. Sources are named beside each fact.

# E146 GATE RECORD (2026-09-25)

| gate | result | detail |
|---|---|---|
| G1 provenance | recorded | see below |
| G2 build review | PASSED, no network fetch or home read found | see below |
| G3 sandboxed build | **built twice, rc=0** | see below |
| G4 weights | in progress | both NVFP4 snapshots downloading, sha256 checked on arrival |
| G5 primary MLPerf entry | **read; two claims on the vendor page do not match it** | see below |
| G6 runner | designed in Amendment 1 | not yet written |
| G7 harness (added) | installed, pinned | MLCommons `inference-endpoint` |

## G1 - provenance

- `Atlas-Inf/atlas` @ `2d1aab8bf4f813059d5614776117b27d17931c05`: 824 commits, 4,414 files, AGPL-3.0-only,
  `CLA.md` present, created 2026-08-24, 30 stars (GitHub API, 2026-09-25).
- `Avarok-Cybersecurity/atlas` HEAD `d822945614e64854978ab416e434f6e5eea8a975`: created 2026-05-05, 699 stars,
  AGPL-3.0, tags include `mlperf-edge-strix-k3-m64-20260724` and `toolchain-scale-1.7.1`.
- The vendor page (atlasinference.dev) shows "675 stars" and links "PR #187". `Atlas-Inf/atlas` has 30 stars and
  no PR #187 (404). Both match the older repo's numbers, not the one linked. Recorded, not judged.
- The page's build hash `ee15431af` (2026-09-10) exists in `Atlas-Inf/atlas`'s history ("spark-server: accept
  single-quoted --default-chat-template-kwargs"). Whether it exists in the older repo was not established
  (API 422, then rate limit).
- The MLPerf entry ships its own source snapshot (`closed/Atlas_Inference/src/Halo/atlas`). Its `Cargo.lock`
  is 0.907 similar (difflib line ratio) to `Atlas-Inf/atlas` @ 2d1aab8. The comparison against the older repo
  was rate-limited and is open.
- Both repos carry AI-agent instruction files (`AGENTS.md`, and in Atlas-Inf `CLAUDE.md`, `GEMINI.md`). They are
  third-party data and were not followed.

## G2 - build review (Atlas-Inf @ 2d1aab8)

- `build-amd.sh` default `ATLAS_TARGET_HW=strix-hip`: native HIP via `hipcc`, needs ROCm and cargo only. SCALE is
  used only by the alternative `strix` path. It states "Verified on gfx1151 / Strix Halo, ROCm 7.13/10"; this box
  has ROCm 7.2.4 (pinned, F58).
- `Cargo.toml`: no git dependencies; the only patch is a vendored local crate (`vendor/cudarc`).
- `build.rs` files (7, non-vendored) execute only `hipcc`, `nvcc`, `ar`, `dumpbin`; read only `CUDA_HOME`,
  `CUTLASS_HOME`, `FLASHINFER_HOME`; no absolute paths, no network calls.
- Network paths that remain: `cargo` fetching locked crates from crates.io, and `serve-amd.sh` downloading weights
  from Hugging Face when given a repo id (avoided: a local, hash-verified path is passed).
- `serve-amd.sh` binds `0.0.0.0` by default; the runs set `HOST=127.0.0.1`.
- Not contained: unprivileged user namespaces are blocked here and `bwrap` is absent, so there is no network sandbox.
  Mitigation used: minimal environment (`env -i`), throwaway `HOME`, user-local Rust, no sudo.

## G3 - sandboxed build

- Rust: `rustup-init` downloaded over HTTPS and verified against its published sha256 (dda72343...), installed
  under `/home/agent-spark/atlas-e146/rust/` only; toolchain `1.93.1` as pinned by the repo. Nothing written to
  `~/.cargo` or `~/.rustup`.
- Build 1 (`ATLAS_TARGET_MODEL=qwen3.8-27b`): rc=0 in 82 s, 262 crates, `spark` 43,500,816 B,
  sha256 `3b21bf140c1876c409c58d3eb7d3418ebfb5725feaae7d9df7fcf41ef04d98e7`.
- Build 2 (`ATLAS_TARGET_MODEL='*'`, all kernel targets incl. `qwen3.6-27b`): rc=0 in 101 s, `spark` 44,784,816 B,
  sha256 `603095a26b00764af9b062b8e9cbc2798cf4c25b75fb8d4c9d72d70297299df4`. This is the binary used, because the
  MLPerf model is Qwen3.6-27B.
- System ROCm 7.2.4 and its apt pin were not touched. The binary links the generated `libcuda.so` and
  `libcublasLt.so` HIP shims (built by `atlas-kernels`); it has not been started.

## G5 - the primary MLPerf entry (mlcommons/inference_results_v6.1, closed/Atlas_Inference)

Read from the public results repository on 2026-09-25.

- **Division and type:** closed, edge, `status: available`, scenario SingleStream, model `qwen3.6-27b`.
- **Strix Halo system:** "Atlas (spark), native-HIP NVFP4", **Ubuntu 24.04 (Linux), ROCm 7.13**, hipcc, GPU-addressable
  GTT about 62.5 GB. `sw_notes`: "Atlas NVFP4 native-HIP serve; **MTP K=3 (2 drafts)** + drafter context-prefill".
- **Weights:** `nvidia/Qwen3.6-27B-NVFP4`, snapshot `0893e1606ff3d5f97a441f405d5fc541a6bdf404`.
- **Workload (`config.yaml`):** `agentic_coding_2.5h.jsonl`, 20 trajectories, concurrency 1, temperature 0, seed 42,
  max 1,024 new tokens; plus BFCL v4 accuracy. The tokenizer path names a user `azeez`.
- **Official metric (`summary.csv`, Units "Latency (ms)"):** mean latency per turn.

| system | official result | accuracy |
|---|---|---|
| DGX Spark GB10 | 3,807.66 ms | 0.8724 |
| **Strix Halo** | **7,058.99 ms** | 0.8623 |

- **Strix Halo `performance/result_summary.json`:** duration 7,108.6 s (118.5 min); 1,007 turns (1,006 tool calls,
  1 stop); 72,624 output tokens; `tps` 10.216; TTFT median 2.71 s.
- **Reading against the vendor page.** The page states "20.1 tok/s DGX Spark, 19.63 tok/s Strix Halo",
  "under 64 minutes" for 1,007 turns, and "cross-architecture parity". The official metric is latency, and the
  Strix Halo turn takes **1.85x** the DGX Spark's (7,059 vs 3,808 ms). "Under 64 minutes" matches the DGX Spark
  (1,007 x 3.808 s = 63.9 min) and not Strix Halo (118.5 min). The entry's own `tps` for Strix Halo is 10.2. How
  19.63 tok/s was derived is not in what was read. This is recorded as a mismatch between the page and the source,
  not as an accusation; a decode-only rate is a plausible derivation.
- **The published Strix Halo configuration is Qwen3.6-27B at K=3, native HIP, Linux.** The README's "28.3 to
  28.6 tok/s" is Qwen3.8-27B at K=4: a different configuration.
- The Avarok tags (`mlperf-edge-strix-*`, SCALE toolchain) are therefore not the MLPerf configuration, whose
  descriptor says native HIP.

## G7 - the MLCommons harness

- `mlcommons/endpoints` @ `4235a9c8bd3e31736acfaa74a71c8c36d04add76` (2026-09-24), Python 3.12, installed in
  `/home/agent-spark/atlas-e146/venv-endpoints` (74 packages, throwaway HOME). Dataset
  `agentic_coding_2.5h.jsonl` sha256 `b7da8c4ffbe1cabd79c4d8169e5201541e006364b4bfc016d01d893e20ee6f70`, 2,014 lines.
  Reference config `online_edge_full_run.yaml` sha256 `745269aa...`; the entry's own `config.yaml` sha256
  `b5a1cde9...` (edited for their endpoint and model).
- The harness's README states the **reference implementation is Qwen3.6-27B Q4_K_M under llama.cpp**, launched with
  `--ctx-size 32768 -np 1 --reasoning off --flash-attn on --n-gpu-layers 99 --seed 42`, validated at llama.cpp
  commit `cfff1fc` on a Jetson AGX Thor.
