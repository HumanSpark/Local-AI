# File: e147-prereg.md
# Purpose: Pre-registration for E147 - the like-for-like arm E146 lacked: llama.cpp WITH a speculative drafter on Qwen3.6-27B, under MLCommons' edge-agentic harness, against the banked reference and Atlas arms.
# Project: sparkbench | Date: 2026-09-25
#
# Overview: E146 found Atlas 27% faster per turn than MLPerf's llama.cpp reference (F169), but that reference has no
# speculation while Atlas runs MTP K=3. On Qwen3.8 a drafter closed most of the code-prompt gap (E146 block 1). This
# run adds the missing arm on the same 206 turns, same harness, same flags plus a drafter, and asks whether Atlas beats
# the best open configuration or only the reference. Written before any run; the drafter is pinned, not yet fetched.

# E147 PRE-REGISTRATION - llama.cpp plus a drafter on the MLPerf metric (2026-09-25)

## The question

Does Atlas (M1p, M1s in E146) beat llama.cpp when llama.cpp also speculates? E146 could only compare it with the
reference (M0, no speculation), so its "27% faster" is a claim about the reference, not about the best open setting.

## Arms

| arm | engine | model | speculation | source |
|---|---|---|---|---|
| M0 | llama.cpp `daef7b6`, reference flags | Qwen3.6-27B Q4_K_M | none | E146, banked, not re-run |
| M1p | patched Atlas HEAD | Qwen3.6-27B NVFP4 | MTP K=3 | E146, banked, not re-run |
| M1s | the MLPerf entry's shipped source | Qwen3.6-27B NVFP4 | MTP K=3 | E146, banked, not re-run |
| **M2** | llama.cpp `daef7b6`, reference flags **plus** `-md Qwen3.6-27B-DFlash-Q8_0.gguf -ngld 999 --spec-type draft-dflash --spec-draft-n-max 4` | Qwen3.6-27B Q4_K_M | DFlash drafter, n=4 | this run |

**Why not re-run M0.** Same build, same harness, same trajectories, same host; E146's M0 was 206 of 206 with 0
failures and is nine hours old. The pairing is by conversation and turn id, so the comparison does not depend on
the arms sharing a window. If the M2 window shows a GPU fault or a kernel change (`uname -r` against F57), M0 is re-run.

**Drafter.** `Alittlehammmer/Qwen3.6-27B-DFlash-GGUF-llama.cpp`, `Qwen3.6-27B-DFlash-Q8_0.gguf`, pinned in
`manifests/MANIFEST.md` (1,849,481,440 B). A community conversion of `z-lab/Qwen3.6-27B-DFlash`. E146 block 1 ran the
same flag set on mainline `daef7b6` with the Qwen3.8 DFlash2 drafter and it served (arm Q1); this drafter's fitness is
measured, not assumed.

## Gates (before the harness runs)

- G1: the drafter's size and sha256 equal the manifest pin.
- G2: the server starts with the drafter, passes the full-offload gate for BOTH models, and a 20-token probe reports
  `draft_n > 0` and `draft_n_accepted > 0` in its timings. A drafter that is loaded but never accepted makes the arm
  VOID, not slow.
- G3: `uname -r` is `7.0.0-31-generic` and Chatterbox is resident (the same conditions as E146's M0), recorded in the log.

## Conditions

Exactly E146 arm M0's: `--ctx-size 32768 -np 1 --reasoning off --flash-attn on --n-gpu-layers 99 --seed 42`, alias
`Qwen3.6-27B-Q4_K_M`, harness `inference-endpoint benchmark from-config --mode perf` on the same 4 trajectories via
`tools/e146_harness_config.py`, 12 GiB memory guard, loopback-only network watch, relay restored on every exit path,
one window of about 45 minutes. The drafter adds 1.7 GiB; peak memory is recorded.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `M2.turns_ok` | 206 of 206 | M0 was; the drafter changes speed, not termination |
| P2 | `M2.mean_turn_latency_ms` | 7,500-10,500 | M0 12,863; TTFT (median 4.5 s) is unchanged by a drafter, decode was 2.3x faster with one on code prompts |
| P3 | `M2/M0` paired ratio | 0.55-0.85 | as P2 |
| P4 | `M2.accuracy_inline` within 0.03 of M0 | yes | greedy speculation preserves the answer (F84); M0 0.637 |
| P5 | `M1p/M2` paired ratio | 0.85-1.20 | on Qwen3.8 Atlas was 1.15x the drafter on code, 1.39x on chat; this workload is tool calls |
| P6 | `M2.draft_acceptance` (mean over turns) | 0.55-0.85 | E138: 82% on code, 44% on prose; tool calls are code-shaped |

## Decision bands (fixed now)

- **Atlas beats the best open configuration:** `M1p/M2` <= 0.85 AND `M1s/M2` <= 0.85, each consistent in at least 2 of 3
  thirds (as E146). **Not separated:** 0.85-1.15. **Open configuration faster:** >= 1.15 on both.
- F169's "27% faster than the reference" stands regardless; this run qualifies it, it does not replace it.
- M2 VOID at G2 leaves the question open; no substitute drafter is tried in the same window.

## Out of scope

The full 1,007-turn run, ROCm 7.13, MTP-GGUF drafters (`unsloth/Qwen3.6-27B-MTP-GGUF` is a later arm if DFlash is VOID),
Atlas with DFlash (its serve script supports it; a separate registration), and block 2 (Aider through Atlas).
