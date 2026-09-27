# File: e150-results.md
# Purpose: Results for E150 - lifting Atlas's DFlash context cap to the serving context changed nothing; the vendor's own explanation of its low acceptance does not hold on this workload.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: Scored against results/e150-prereg.md. One window 12:37-13:27, one arm, capped at 3,000 s as declared: 128 of
# 206 turns. ATLAS_DFLASH_CTX_WINDOW=36864 (G2 held) produced the same acceptance curve as M3p to the third decimal
# (0.060 per step against 0.064; 0.008 past 12K), the same tokens per step (1.071 both), and the identical output length
# on 127 of 128 turns. F176's cause claim is retracted. Scorer tools/score_capped_atlas_arm.py, output
# results/raw/e150/score.txt. Registered as F177.

# E150 RESULTS - the context cap is not the cause (2026-09-26)

## What ran

M5 = E148's M3p with one change: `ATLAS_DFLASH_CTX_WINDOW=36864` in the server's environment, so the drafter could attend to
the whole captured prefix on every turn. G1 held (pinned drafter bytes). G2 held: `DFlash ctx_window = 36864 (set
ATLAS_DFLASH_CTX_WINDOW to override; drafter trained on full captured prefix — larger is better, scratch grows linearly)`; the
drafter-loaded line as M3p's (`causal=None, swa=None/None`). G3: kernel 7.0.0-31, Livepatch nothing-to-apply, GTT 66 GiB before
the window, 5 spark-infer processes resident; memory guard did not fire; 0 amdgpu fault lines. Harness killed at 3,000 s as
declared, after 128 turns; window closed 13:27:37.

## Result: identical to M3p, again

| same first 128 turns | M3p (E148) | **M5** | M1p (MTP) |
|---|---|---|---|
| tokens per step | 1.071 | **1.071** | 1.681 |
| first-draft acceptance p1 | 0.036 | **0.036** | 0.681 |
| decode, tok/s | 4.44 | **4.45** | 14.99 |
| server-side time per turn | 23,349 ms | **23,323 ms** | 9,291 ms |
| M5 / column | **0.999** | - | 2.510 |
| turns with the identical output token count as M5 | 127 of 128 | - | 113 of 128 |

Acceptance per 15-draft step over 2,689 logged steps: **0.060** (M3p whole run 0.064). By context and turn position:

| | 0-4K | 4-8K | 8-12K | 12K+ |
|---|---|---|---|---|
| first turn of a conversation | 2.429 | 1.125 | - | - |
| later turns | 1.667 (3 steps) | 0.161 | 0.018 | 0.008 |

The first-turn figures are M3p's to three decimals; the later-turn figures are within noise of M3p's (0.207 / 0.016 / 0.009).

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `M5.accepted_per_step` | >= 3.0 | 0.060 | FALSIFIED |
| P2 | `M5.accepted_per_step`, 12,288-28,671 | >= 1.0 | 0.008 | FALSIFIED |
| P3 | `M5.mean_turn_latency_ms` (harness) | 6,000-10,000 | - | UNSCORED (capped) |
| P4 | `M5/M3p` | <= 0.50 | 0.999 (server-side, 128 turns) | FALSIFIED |
| P5 | `M5/M2` | 0.80-1.30 | - | UNSCORED (capped) |
| P6 | cap does not fire | no | fired at 3,000 s | FALSIFIED |
| P7 | accuracy within 0.03 of M0 | yes | - | UNSCORED (capped) |

Band: **retired** (P1 < 1.0). The prereg said the remaining candidate would then be the HIP kernel path; E151, pre-registered
during this run on evidence from M3p's own log (first turns accept 5.4x more than later turns at the same context), tests the
prefix cache first, because Atlas's startup WARN names exactly that interaction.

## What this settles

Three configurations (as shipped; causal SWA declared; context cap lifted) produced one acceptance curve, and the same output on
383 of 386 compared turns across E149 and E150. Whatever starves the drafter, it is not the drafter's attention pattern and it is
not how much prefix it may see. The vendor comment in `from_weights.rs` ("Atlas's 6-10% acceptance vs the paper's 70% is
dominated by this cap") describes the vendor's workloads and hardware, not this one: with the cap lifted nine-fold, acceptance
here did not move. [[F176]]'s cause claim is retracted in F177.

## Limits

128 of 206 turns, server-side timing, one run; the scratch growth the comment predicts was not measured (GTT before the window was
66 GiB both times; the guard did not fire).
