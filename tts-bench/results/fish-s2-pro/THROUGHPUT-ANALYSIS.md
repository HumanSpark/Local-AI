# Fish s2-pro throughput analysis (W3 T6, 2026-07-25)

**Engine:** `fishaudio/s2-pro` (4B Dual-AR, S2 generation) via upstream `docker/Dockerfile.rocm`
on rootless podman (base `rocm/pytorch:rocm7.2.3` torch 2.9.1), `tools/api_server.py` :8080,
ormsgpack `/v1/tts`. GPU: sparkmax gfx1151 (Radeon 8060S), ROCm 7.2.4.

## Headline

Fish s2-pro **SERVES on the AMD/ROCm path** (first audio achieved; valid WAV) but at
**end-to-end RTF ~0.04x (≈25x slower than realtime)** in this configuration. A 3-min post
would take ~75 min to render; the 7 dark + 139 backfill posts would be ~180 GPU-hours. Not
operationally viable for the narration backfill as-is - **but the bottleneck is the vocoder,
which is plausibly tunable** (see below), and quality is a separate axis (listening pack pending).

## The bottleneck is the DECODER, not the LLM (measured, not assumed)

Per HARNESS-RULES Rule 8, both serving configs were run:

| Config | LLM generate rate | First-shape compile | End-to-end RTF |
|---|---|---|---|
| `COMPILE=0` (eager) | ~1.0 tok/sec | none | ~0.04x |
| `COMPILE=1` (torch.compile) | ~8.5-9.2 tok/sec | ~141s one-time | ~0.04x |

`torch.compile` gives a **~9x speedup on the LLM stage** but **~no end-to-end change**, because
the DAC/GAN vocoder (VQ tokens -> waveform) dominates wall time:

- 43-word excerpt (`COMPILE=1`): server log = LLM "Generated 297 tokens in 34.97s" (8.5 tok/s),
  but client round-trip = **307.8s**. The missing ~270s is the decode stage.
- Confirmed two independent ways: (a) client wall minus server-gen time; (b) the ~5-min gap
  between consecutive "Generated ... tokens" log lines for back-to-back requests.
- The container logs are flooded with `MIOpen(HIP) Warning [IsEnoughWorkspace] Solver
  <GemmFwdRest> ... workspace required: N, provided ptr: 0 size: 0` - the conv-heavy vocoder is
  falling back to MIOpen's no-workspace GEMM/conv solver, the slow path. This is the smoking gun.

RTF is ~0.04x across BOTH configs AND both short (1.5s audio) and medium (13.7s audio) clips -
the decode cost is fixed-conv-dominated, not length-dominated, so the LLM speedup is masked.

## Tuning leads (NOT chased in Stage 1 - timebox; recorded for T10 decision)

- Provide MIOpen a conv workspace / set `MIOPEN_FIND_MODE` (the no-workspace fallback is the slow
  path being hit).
- `ROCBLAS_USE_HIPBLASLT=0` is currently forced by the compose/Dockerfile; re-test with hipBLASLt.
- MIOpen kernel DB / `MIOPEN_USER_DB_PATH` persistence across container runs (first-run autotune).
- These are vocoder-path tuning; the LLM stage is already healthy under `COMPILE=1`.

## Memory / coexistence

GPU (GTT) with Fish + resident Qwen3-30B LLM co-resident: ~39.7 GiB total on the 112 GiB pool
(Fish ~19.5 GiB incl. compile buffers; server self-reported "GPU Memory used: 22.53 GB").
Coexists comfortably; the production LLM was never paused (plan's T5-acknowledged coexistence).

## Raw evidence

- `compile0-log-evidence.txt` - eager-mode generation rates (0.96-1.03 tok/s, GPU 22.5 GB)
- `compile1-log-evidence.txt` - torch.compile generation rates (8.4-9.2 tok/s) + compile times
- `compile1-client-walltimes.txt` - client round-trip wall times (the end-to-end RTF source)
- `metrics.json` - full per-excerpt corpus run (1 sample/excerpt; see run's DEVIATION note)
