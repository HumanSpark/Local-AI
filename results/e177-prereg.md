<!--
# File: results/e177-prereg.md
# Purpose: Pre-registration for E177 - Flash-Next on the HTR (Halo Trellis) engine against production Halogen, same day, same timing tool.
# Project: sparkbench | Date: 2026-11-24
#
# Overview: Written before the HTR engine's first start. Speed first (tools/e163_speed.py on both engines), then, as a
# second leg, the hard coding bank on HTR. Predictions name their field. Deviations are findings.
-->

# E177 PRE-REGISTRATION - Flash-Next on HTR vs production Halogen (2026-11-24)

## In plain English

A community member published our production model, Qwen3.8 Flash-Next, compressed with their own method (HTR,
"Halo Trellis") and served by their own build of vLLM, both tuned for this chip. They say it writes 48-55 tokens a
second. Production runs the same model on Halogen. The owner asked to pause the Ling benchmark and test this instead.
Question: is HTR faster than what production already uses, and does its compression cost quality?

## Setup

- Model: hstolte/Qwen3.8-Flash-Next-HTR @ v0.2.4 (`5bca35b9`), variant Htr5Core, all 64 files verified against the HF
  API sha256 (results/e177/verify.log). About 65.7 GiB in GPU memory (card); a 95.4 GiB lookup table (PLE) is read
  from SSD while it runs.
- Engine: `ghcr.io/hawgauto/vllm-htr@sha256:cbd53758...` (card's pinned digest), rootless podman, card hardening, port
  127.0.0.1:8177, `VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1`, `--max-model-len 40960 --max-num-seqs 1
  --max-num-batched-tokens 2048 --kv-cache-memory-bytes 4294967296` (card defaults except context raised from 32,768 so
  the 32K prompts fit, and KV 4 GiB to hold it). MTP3 (card default) on. Pre-run image check: results/e177/security-scan.md.
- Comparison: production Halogen measured TODAY at 127.0.0.1:8433 (relay up, serving normally), same tool, thinking off
  via chat_template_kwargs. Its E163 figures (2026-11-16) are context only.
- Ruler: `tools/e163_speed.py` (E139's prompts: 8K x3, 32K x3 at 256 tokens out, a short prompt at 512), client-timed,
  temperature 0, thinking off (HTR: auto-off probe picks the switch).
- **Memory-edge rule (F193):** the HTR load is over ~60 GiB, so the owner is near the power button for the first load,
  no other heavy I/O runs, the page cache is cleared first, and any DeviceLost means reboot before further GPU work.

## Predictions (field named)

- **P1** (`decode_tps` median, short prompt, HTR): >= 45 tok/s.
- **P2** (`decode_tps` median, short prompt): HTR < Halogen-today (does not beat production on writing speed).
- **P3** (`prefill_tps` median, 32K prompt): HTR < Halogen-today.
- **P4** (HTR load): reaches /v1/models ready with no DeviceLost or out-of-memory, first start within 60 min (it
  compiles kernels on first start).

## Second leg (hard coding bank), declared now, run only after the speed leg

Same bank and settings as the Ling benchmark (E176) and the hard-bank run (E167): 10 tasks, 3,600 s each, podman
isolation, one attempt, HTR at `--max-model-len 131072` with 8 GiB BF16 KV (card's v0.2.0 default pool).
- **P5** (`pass_count`): HTR >= 4/10 (production solved 5; same model, so compression should cost at most one task).
