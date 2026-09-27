# File: e150-prereg.md
# Purpose: Pre-registration for E150 - one arm testing F176's cause: Atlas's DFlash drafter sees at most 4,096 tokens of prefix; raise the cap to the serving context.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: E148 (F175) measured 0.064 accepted tokens per 15-draft step for Atlas's DFlash on the MLPerf model, collapsing
# past 4K context. E149 (F176) retired the sliding-window explanation and found the vendor's own statement in
# from_weights.rs: the drafter was trained on the full captured prefix and the 4,096 ctx_window cap "cripples it". One arm,
# one variable: ATLAS_DFLASH_CTX_WINDOW=36864 (the serving context, so the drafter always sees the whole prefix). Written
# before the run; the scratch cost is the vendor's figure (about 250 MB per head at 4,096, linear).

# E150 PRE-REGISTRATION - Atlas DFlash with the drafter's context cap lifted (2026-09-26)

## The question

With the drafter allowed to see the whole prefix, does Atlas's DFlash mode recover acceptance, and where does it then sit against
Atlas MTP (M1p 9,307 ms), llama.cpp with the same drafter lineage (M2 7,775 ms) and the reference (M0 12,863 ms)?

## Arm

| arm | what changes from E148 M3p | what does not |
|---|---|---|
| **M5** | `ATLAS_DFLASH_CTX_WINDOW=36864` in the server's environment | binary (patched HEAD, sha256 `083e7efd...`), the ORIGINAL drafter directory (E149's -swa copy is not used), γ 16, `num_drafts` default, `--dflash-window-size` default, prefix caching, `serve-amd.sh` invocation, harness, 206 turns |

36,864 is `MAX_SEQ_LEN`, so no turn can exceed the drafter's window. The engine's guard (`ctx_count > ctx_window` bails) cannot
fire.

## Gates

- G1: the drafter's bytes match the pin (size 3,460,432,504, sha256 `e0c050b34798...`).
- G2: server answers `/v1/models`; log shows `DFlash ctx_window = 36864` and the drafter loaded. Any other ctx_window value is VOID.
- G3: kernel, Livepatch, GTT before the window, Chatterbox residency, recorded as E149. The memory guard (12 GiB MemAvailable)
  stays armed; if it kills the server, the arm is VOID with the scratch figure recorded, not slow.

## Conditions

E148's exactly, one arm, harness capped at **3,000 s** after start (M2 needed 1,602 s for 206 turns; M1p about 1,900; at M3p's
pace the cap fires at about 130 turns). A capped run is scored server-side on Atlas's per-turn lines against M3p, M1p and M4 on
the same first N turns (E149's method); a completed run is scored by `tools/score_e146.py`'s harness path, paired against M0,
M1p, M2 and M3p on all 206 turns.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `M5.accepted_per_step` (mean over logged verify steps) | >= 3.0 | the vendor's comment claims the cap dominates its 6-10% vs 70%; llama.cpp's probe accepted 0.74 of 4 drafts; at 15 drafts and a 70% rate the figure would be about 10, so 3.0 is a low bar |
| P2 | `M5.accepted_per_step`, 12,288-28,671 bucket | >= 1.0 | if the cap is the cause, long contexts recover most |
| P3 | `M5.mean_turn_latency_ms` (harness, if completed) | 6,000-10,000 | between M2 and M1p; DFlash verify at 15 drafts is expensive when acceptance is middling |
| P4 | `M5/M3p` paired (server-side if capped) | <= 0.50 | recovery of acceptance halves time per turn at least |
| P5 | `M5/M2` paired (harness, if completed) | 0.80-1.30 | wide; no prior for a working Atlas DFlash on HIP |
| P6 | cap does not fire | no | P3 implies about 35 minutes |
| P7 | `M5.accuracy_inline` within 0.03 of M0 (0.637) | yes | greedy verification; F84 |

## Decision bands (fixed now)

- **Cause confirmed:** P1 and P2 both held. **Cause partial:** P1 held, P2 not (something else still bites at long context).
  **Retired:** P1 < 1.0; then the remaining candidate is the HIP kernel path, which this project does not pursue further.
- Against M2: <= 0.85 with 2 of 3 thirds "Atlas faster"; 0.85-1.15 not separated; >= 1.15 open configuration faster. Only a
  completed run is banded; a capped run reports the server-side ratios and no band.

## Out of scope

`--dflash-window-size`, gamma, `num_drafts`, M3s, per-layer attention patterns, any second change.
