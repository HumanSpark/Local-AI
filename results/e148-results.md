# File: e148-results.md
# Purpose: Results for E148 - Atlas's own DFlash speculative mode on the MLPerf model, the Atlas-side like-for-like of E147.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: Scored against results/e148-prereg.md. One window 02:40-04:01 (4,843 s). M3p (patched Atlas HEAD, DFlash)
# ran 206 turns with 0 failures and 0 amdgpu fault lines, at 22,898 ms per turn: 1.78x the reference and 2.46x Atlas's
# own MTP arm, because the drafter accepted 0.064 tokens per 15-token draft step. M3s (the MLPerf entry's source) voided
# at G2: its HIP build has no kernel module for DFlash prefill. Scorer tools/score_e146.py (E148 section), acceptance
# tools/e148_dflash_accept.py, output results/raw/e148/score.txt. Registered as F175.

# E148 RESULTS - Atlas's DFlash mode is slower than its MTP mode and than the reference on this box (2026-09-26)

## The arms and their comparators (same 206 turns, paired by conversation and turn)

| arm | what | mean latency per turn | median | p95 | TTFT median | accuracy | vs M0 |
|---|---|---|---|---|---|---|---|
| M0 (E146) | llama.cpp reference, no speculation | 12,863 ms | 8,704 | 33,553 | 4,479 | 0.637 | 1.000 |
| M1p (E146) | Atlas HEAD plus a one-line patch, MTP K=3 | 9,307 ms | 6,358 | 25,133 | 3,432 | 0.622 | 0.724 |
| M2 (E147) | llama.cpp reference flags + Qwen3.6-27B DFlash drafter GGUF, n=4 | 7,775 ms | 5,790 | 15,720 | 3,070 | 0.637 | 0.604 |
| **M3p** | Atlas HEAD plus the same patch, `--dflash --draft-model` z-lab Qwen3.6-27B-DFlash, γ=16 | **22,898 ms** | 14,499 | 64,820 | 7,501 | 0.631 | **1.780** |
| M3s | the MLPerf entry's source, the same flags | VOID at G2 | - | - | - | - | - |

- **M3p against the reference:** paired ratio **1.780**, thirds 1.782 / 1.895 / 1.657. Against M2: **2.945** (2.407 / 3.458 / 2.989).
  Against Atlas's own MTP arm M1p: **2.460** (2.383 / 2.644 / 2.329). Band: **open configuration faster**, in every third.
- **Accuracy held:** 0.631 against M1p's 0.622 and M0's 0.637. The WARN the server printed about prefix caching with DFlash
  ("community-reported correctness regression on SM12.x ... outputs may be wrong on multi-turn cache hits") did not show in the score.
- **Why it is slow: the drafter accepts almost nothing.** Of 4,160 logged verify steps (γ=15 drafts each), 4,006 accepted zero
  tokens; 268 tokens were accepted in all, **0.064 per step**. Atlas's own per-turn summary lines agree: tokens per step
  **1.074** for M3p against **1.689** for M1p (MTP K=3), first-draft acceptance 0.039 against 0.689, decode 4.36 tok/s against
  14.84. Each step still pays the 15-token verify, so DFlash here costs more than plain decode would.
- **Acceptance collapses with context length** (`tools/e148_dflash_accept.py results/raw/e148/M3p/server.serverlog`):

  | sequence length | verify steps | accepted per step |
  |---|---|---|
  | under 4,096 | 63 | 1.984 |
  | 4,096-8,191 | 330 | 0.318 |
  | 8,192-12,287 | 506 | 0.016 |
  | 12,288-28,671 | 3,261 | 0.007-0.016 |

  The harness's turns run 2,000-28,000 tokens of context, so almost every step sat where the drafter is useless.
- **M3s voided in 75 s.** The drafter loaded ("DFlash drafter loaded: 5 layers, hidden=5120, vocab=248320, γ=16"), then
  `Error: Failed to build model ... Kernel lookup prefill_paged_indirect::inferspark_prefill_paged_indirect: Module load failed:
  Module 'prefill_paged_indirect' not loaded`. The MLPerf-era source has the `--dflash` flag and no HIP kernel behind it. Per the
  prereg, no retry in the window; its question stays open.

## Gates

- G1 HELD: `model.safetensors` 3,460,432,504 B, sha256 `e0c050b34798...`, as pinned in the manifest.
- G2 M3p HELD (drafter loaded, γ=16 from `MODEL.toml`, `num_drafts: using default 15 (K=16)`, `DFlash ctx_window = 4096`,
  prefix caching ENABLED); M3s FAILED (above).
- G3: kernel 7.0.0-31-generic, Livepatch `nothing-to-apply`, Chatterbox resident (spark-infer's python processes) throughout.
  **GTT before the window was not recorded** - the window script was derived from E146's follow-up script, which lacks E147's
  capture. GTT after the window with the relay back was 57.0 GiB (04:03). 0 amdgpu fault lines in either arm.

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `M3p.turns_ok`, `M3s.turns_ok` | 206 of 206 | M3p 206; M3s VOID | HELD for M3p; VOID for M3s |
| P2 | `M3p.mean_turn_latency_ms` | 5,500-9,000 | 22,898 | FALSIFIED |
| P3 | `M3p/M0` paired ratio | 0.45-0.72 | 1.780 | FALSIFIED |
| P4 | `M3p/M2`, `M3s/M2` paired ratio | 0.80-1.20 | 2.945; VOID | FALSIFIED; VOID |
| P5 | `M3p.accuracy_inline` within 0.03 of M1p | yes | 0.631 vs 0.622, diff 0.009 | HELD |
| P6 | `M3p/M1p` paired ratio | 0.65-0.95 | 2.460 | FALSIFIED |

Four of six falsified, all in the same direction: the prediction assumed the vendor's faster path is faster on this box. It is
not. The window ran 81 minutes against the 90 announced only because M3s voided in 75 s; M3p alone took 79 minutes against the
30 the prediction implied.

## What this settles and what it does not

F172 stands and is strengthened: with a drafter of the same lineage on both engines, llama.cpp takes 7,775 ms per turn and
Atlas 22,898. Atlas's MTP mode (9,307 ms) remains its best configuration measured here, and it loses to llama.cpp with a drafter.
"Atlas's own faster path" is, on this box with this drafter, its slowest.

Two log lines are recorded and not interpreted: `MTP speculative decoding: ENABLED (single-module)` appears alongside the DFlash
lines even though `serve-amd.sh` forces the MTP `--speculative` arguments off under `DFLASH=1`; and the two Atlas builds disagree on
the drafter's capture layers - HEAD logs `target layer capture indices = [1, 16, 31, 46, 61] (drafter target_layer_ids, used
directly)`, the MLPerf-era source logs `[0, 15, 30, 45, 60] (offset=-1 from raw [1, 16, 31, 46, 61])`.

**Unproven explanations, in the order they are cheapest to test:** (1) the off-by-one above - if HEAD feeds the drafter the
wrong layers' hidden states, near-zero acceptance is what that looks like, and the fix is one line of the same kind as the
W4A16 patch; (2) `DFlash ctx_window = 4096`, which coincides with the length at which acceptance collapses, overridable with
`ATLAS_DFLASH_CTX_WINDOW`; (3) a HIP kernel path the vendor has not exercised (its DFlash issue reports are all GB10). None of
these was tried in the window, by the prereg's rule. Each is a one-arm follow-up, not a re-run of this one.

Limits: 4 of 20 trajectories, one run; the z-lab drafter as published, γ and K at the engine's defaults; ROCm 7.2.4; the patched
HEAD only, because the MLPerf-era build cannot serve DFlash on HIP at all. M0, M1p and M2 were not re-run (same build, host and
kernel; declared in the prereg).
