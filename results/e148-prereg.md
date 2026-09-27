# File: e148-prereg.md
# Purpose: Pre-registration for E148 - Atlas's own DFlash speculative mode on the MLPerf model, the Atlas-side like-for-like of E147.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: E147 gave llama.cpp a DFlash drafter and it beat Atlas's MTP K=3 by 1.20-1.22x per turn (F172). Atlas has its
# own DFlash mode, and z-lab's Qwen3.6-27B drafter is the checkpoint the E147 GGUF was converted from, so both engines
# can run the same drafter lineage. One arm, same harness, same 206 turns, compared with the banked M0, M1p, M1s and M2.
# Written before any run; the drafter is pinned and fetching.

# E148 PRE-REGISTRATION - Atlas with DFlash against llama.cpp with DFlash (2026-09-26)

## The question

With the same drafter lineage on both engines, does Atlas beat llama.cpp on MLCommons' edge-agentic metric? F172 answered
"no" for Atlas MTP against llama.cpp DFlash; that left Atlas's own DFlash mode untested, and it is the vendor's own faster
path (its serve script offers it, its issue tracker reports 24 to 42 tok/s aggregate gains from it on GB10).

## Arms

| arm | engine | drafter | comparators (banked, not re-run) |
|---|---|---|---|
| **M3p** | Atlas-Inf HEAD 2d1aab8 plus the one-line W4A16 patch (E146 M1p's binary, sha256 083e7efd...), `--dflash --draft-model <local z-lab/Qwen3.6-27B-DFlash>` | z-lab safetensors, MIT, 3.22 GiB | M0 12,863 ms; M1p 9,307; M1s 9,453; M2 (llama.cpp + the GGUF of this drafter) 7,775 |
| **M3s** | the MLPerf entry's shipped source, native-HIP build (E146 M1s's binary, sha256 dc63085d...), the same `--dflash --draft-model` | same | same |

Both builds carry `--dflash` (checked in their `serve --help` on 2026-09-26). M3p is Atlas plus one line, declared as such
throughout, as in E146; M3s is the code MLCommons recorded, built native HIP as in E146. Each is scored on its own.

**Serve configuration (M3p):** `serve-amd.sh` with `DFLASH=1 DRAFT_MODEL=/opt/models/staging/qwen3.6-27b-dflash`, which turns MTP off
(the two are exclusive in that script), `HOST=127.0.0.1`, `MAX_SEQ_LEN=36864`, prefix caching on with `SSM_SLOTS=32` and
`SSM_CKPT_INTERVAL=128` (E146 amendment 3), `GPU_UTIL=0.60`, `MODEL_NAME=nvidia/Qwen3.6-27B-NVFP4`. **M3s:** the binary called directly with E146 M1s's flags, `--speculative`
removed and `--dflash --draft-model` added. DFlash gamma is left at the target's `MODEL.toml` value or the engine default of 16 on
both, and the value each server logs is recorded. Everything else is E146.

## Gates

- G1: the drafter's files match the manifest pin (size and sha256 for the safetensors).
- G2: the server answers `/v1/models` and its log shows DFlash enabled with the drafter loaded; a 20-token probe completes.
  If the log shows DFlash disabled, or the engine's auto-disable trips (its `--speculative` help describes one), the arm is
  VOID, not slow, and the log line is quoted.
- G3: kernel, Chatterbox residency and GTT before the window recorded, as E147.

## Conditions

E146/E147's exactly: `inference-endpoint benchmark from-config --mode perf` on the same 4 trajectories via
`tools/e146_harness_config.py`, 12 GiB memory guard, loopback-only network watch, relay restored on every exit path, one window
of about 1.5 hours for the two arms, M3p first. Paired comparison by conversation and turn id against M0 and M2.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `M3p.turns_ok` and `M3s.turns_ok` | 206 of 206 | M1p was |
| P2 | `M3p.mean_turn_latency_ms` (M3s reported beside it) | 5,500-9,000 | between M1p (MTP) and M2's 7,775; DFlash is the vendor's faster path |
| P3 | `M3p/M0` paired ratio | 0.45-0.72 | as P2 |
| P4 | `M3p/M2` (and `M3s/M2`) paired ratio | 0.80-1.20 | no prior separating the two engines with the same drafter; wide on purpose |
| P5 | `M3p.accuracy_inline` within 0.03 of M1p (0.622) | yes | DFlash verifies against the target; F84 |
| P6 | `M3p/M1p` paired ratio | 0.65-0.95 | DFlash faster than MTP K=3 on the same engine |

## Decision bands (fixed now)

- **Atlas faster than the open configuration:** `M3p/M2` (and `M3s/M2`) <= 0.85, consistent in at least 2 of 3 thirds. **Not separated:**
  0.85-1.15. **Open configuration faster:** >= 1.15.
- F172 stands whatever M3 does: it is about MTP. E148 qualifies it or not.
- Each arm is banded on its own. An arm VOID at G2 leaves its question open; no substitute drafter or gamma is tried in the same window.

## Out of scope

Gamma sweeps, `--dflash-window-size`, the full 1,007-turn run, ROCm 7.13, and Atlas DFlash on Qwen3.8 (a later arm if this one serves).
