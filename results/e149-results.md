# File: e149-results.md
# Purpose: Results for E149 - declaring the drafter's causal sliding-window layers to Atlas changed nothing; the cause of F175 is the drafter's 4,096-token context cap, in Atlas's own words.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: Scored against results/e149-prereg.md (with amendment 1). One window 11:51-12:31, one arm, capped at 2,400 s
# as declared: 109 of 206 turns. Acceptance 0.071 tokens per step against M3p's 0.064; per-turn server time 1.002 of M3p's on
# the same turns; 107 of 109 turns produced the identical output token count. The explanation under test is retired. What
# the run and Atlas's source together point at instead: ATLAS_DFLASH_CTX_WINDOW=4096 truncates the prefix the drafter sees,
# and Atlas's own comment says the drafter "was trained over the FULL captured prefix" and that the cap "cripples it".
# Scorer tools/score_e149.py (server-side path), output results/raw/e149/score.txt. Registered as F176.

# E149 RESULTS - the sliding-window declaration is inert; the context cap is the cause (2026-09-26)

## What ran

M4 = E148's M3p with one change: the drafter's `config.json` carried `"causal": true, "use_swa": true, "swa_window_size": 2048`
inside `dflash_config`. G1 held (same bytes as the pinned drafter; config differs in exactly those fields). G2 held on the
loader line (`causal=Some(true), swa=Some(true)/Some(2048)`), with the deviation declared in amendment 1 during the run: the
engine's `--dflash-window-size` argument overrides the config, so the head ran `causal=true, window=Some(4096)`. G3: kernel
7.0.0-31, Livepatch nothing-to-apply, GTT 66 GiB before the window, Chatterbox resident (5 spark-infer processes); 0 amdgpu fault
lines. The harness was killed at 2,400 s as declared, after 109 turns, and the window closed 12:31.

## Result: identical to M3p

| | M3p (E148, first 109 turns) | **M4 (first 109 turns)** | M1p (MTP, first 109 turns) |
|---|---|---|---|
| accepted tokens per 15-draft step, all logged | 0.064 (whole run) | **0.071** | - |
| accepted per step, 12,288-16,383 context | 0.009 | **0.006** | - |
| tokens per step (Atlas's per-turn line) | 1.082 | **1.080** | 1.685 |
| first-draft acceptance p1 | 0.041 | **0.045** | 0.685 |
| decode, tok/s | 4.42 | **4.40** | 14.98 |
| server-side time per turn (TTFT + tokens / decode) | 21,824 ms | **21,860 ms** | 8,806 ms |
| M4 / column, same turns | **1.002** | - | 2.482 |
| turns with the identical output token count as M4 | 107 of 109 | - | - |

Acceptance by context length (`tools/e148_dflash_accept.py results/raw/e149/M4/server.serverlog`): 2.21 per step under 4,096;
0.31 at 4-8K; 0.02 at 8-12K; 0.004-0.010 beyond. The same curve as M3p to two decimals.

**Method note.** A harness killed at the cap writes no `events.jsonl` (it flushes at the end), so the prereg's "scored from the
events stream" was wrong for a capped run. M4 is compared server-side on Atlas's own per-turn `Done` lines (one per turn, issue
order), the same lines in M3p's and M1p's logs, over the same first 109 turns. This is not the harness's client-side latency;
it is consistent across the three columns.

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `M4.accepted_per_step` | >= 1.0 | 0.071 | FALSIFIED |
| P2 | `M4/M3p` | <= 0.60 | 1.002 (server-side, first 109 turns) | FALSIFIED |
| P3 | `M4/M2` | 0.80-1.50 | - | UNSCORED (capped; M2 has no server-side turn lines) |
| P4 | accuracy within 0.03 of M3p | yes | - | UNSCORED (capped; no scores.json) |
| P5 | cap does not fire | no | fired at 2,400 s, 109 turns | FALSIFIED |
| P6 | accepted per step, 12,288-28,671 | >= 0.5 | 0.007 | FALSIFIED |

By the prereg's decision rule (P1 < 0.3): this explanation is retired, and P6 near 0.01 points at the context window.

## Why the declaration was inert

Two reasons, both visible in the logs. The sliding window ran at 4,096 (amendment 1) and the drafter's context is capped at
4,096 (`DFlash ctx_window = 4096`), so a 4,096 window over at most 4,096 tokens is full attention: the SWA flag could not
change a single attention score. And `causal=true` moved p1 from 0.041 to 0.045, noise.

## What the cause is

Atlas's own source (`spark-model/src/layers/dflash_head/from_weights.rs`, above the `ATLAS_DFLASH_CTX_WINDOW` read):

> The drafter was trained over the FULL captured prefix (paper §A.1), but capping at γ=16 cripples it on prompts past a tiny
> window — Atlas's 6-10% acceptance vs the paper's 70% is dominated by this cap. Default raised 512 → 4096 (2026-07-08): long
> generations ... blow past 512 captured rows → truncated prefix → accept collapse + droop.

Our curve is that sentence measured: acceptance is 2.2 per step while the prefix fits in 4,096 tokens and collapses as more of
it is cut, and the harness's turns run 2,000-28,000 tokens. The vendor moved the default from 512 to 4,096 for its own
workloads; MLCommons' agentic-coding turns are an order of magnitude longer. The scratch cost the comment gives is about 250 MB
per head at 4,096 and linear, so 36,864 (the serving context) is about 2.3 GB.

This is the next single-change arm (E150): the original drafter directory, `ATLAS_DFLASH_CTX_WINDOW=36864`, everything else M3p.

## Limits

109 of 206 turns, one run, server-side timing; the -swa config is kept on disk for provenance and is not used again. The engine's
`--dflash-window-size` default is not recorded by the log beyond `window=Some(4096)`.
