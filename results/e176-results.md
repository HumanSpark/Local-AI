<!--
# File: results/e176-results.md
# Purpose: Results of E176 - Ling-3.2-air (124B total / 5.5B active) on benchhost: speed on two llama.cpp builds and the hard coding bank.
# Project: sparkbench | Date: 2026-11-25
#
# Overview: Scored against results/e176-prereg.md. Speed: llama-bench, f16 KV (files listed under Evidence). Bank:
# results/e176/raw/LG/ (stripped task records; transcripts gitignored). The bank leg was paused after task 4 for the
# HTR test (E177) and resumed with task 5 re-run from scratch (prereg run log).
-->

# E176 RESULTS - Ling-3.2-air on benchhost (2026-11-24)

## In plain English

Ling-3.2-air is a large model that only uses about 5 billion of its 124 billion parameters per word, so it writes fast
here: about 37% faster than production's model on the same engine. But it solved none of our ten hard real coding
fixes, where production solves five. It ran out of working memory on half of them, ran out of time on two, and on the
rest declared itself finished with the tests still failing. Fast, but not the knowledge-work model the owner wants.

## Speed (llama-bench, Q3_K_M, f16 KV, -fa on, tok/s, mean of 3)

| depth | build | pp512 | tg128 |
|---|---|---|---|
| 0 | 94f3af3d0 | 479.90 | 36.62 |
| 8,192 | 94f3af3d0 | 354.32 | 34.71 |
| 32,768 | 94f3af3d0 | 207.46 | 29.93 |
| 0 | ae6a7ad2c | 475.05 | 36.60 |
| 8,192 | ae6a7ad2c | 350.53 | 34.68 |
| 32,768 | ae6a7ad2c | 205.42 | 30.33 |

Flash-Next on 94f3af3d0 (E174, f16): pp512 516.68 / 427.77 / 346.06, tg128 26.68 / 25.92 / 25.01.

## Hard coding bank (10 tasks, 3,600 s, podman, one attempt; compared with E167 production and E177 HTR)

| task | Ling | production (2026-11-18) | HTR (2026-11-24) |
|---|---|---|---|
| clearmail-3d41463d0 | fail (context limit) | pass | pass |
| clearmail-7fe0a79c1 | fail | pass | pass |
| clearmail-01d445d75 | fail | fail | pass |
| sparkforge-22dee74e9 | fail (time limit) | pass | fail |
| sparkforge-66de8e1d0 | fail (time limit) | pass | fail |
| sparkforge-625dcc2f8 | fail | fail | pass |
| workstation-dotfiles-a0d0e6f0d | fail (context limit) | fail | fail |
| workstation-dotfiles-ffaf96580 | fail (context limit) | pass | pass |
| another GPU job-390973aee | fail (context limit) | fail | pass |
| another GPU job-5ca87050b | fail (context limit) | fail | fail |
| **pass_count** | **0** | **5** | **6** |

Stop reasons: 5 hit the 131,072-token context, 2 the 3,600 s limit, 3 declared done with tests failing. Median 1,426 s
a task. Tool calls parsed cleanly throughout (task 1: 46 calls, 0 malformed; llama.cpp's Ling parser, PR #28682, is in
both builds). Task 1 edited only test files and never the code under test.

## Everyday fixes (A1: the 15-fix bank, 1,200s per task, podman, one attempt; 2026-11-25)

Ling solved **1 of 15**; production solved all 15 within the same 20 minutes (E154). Every task ran to the time limit.
On 14 of 15 it changed no code at all: it spent a median 100s per turn, took a median 12 turns, and was still
reading files when time ran out. The one pass (`voxmachina-c134bbe44`) also hit the limit; its change passed the
tests when graded afterwards, the same rule that scored three of Hy4-Flash's passes in E171. Tool calls stayed well
formed throughout, so this is the model's working pace, not a harness fault.

| arm | solved | stopped by the time limit | no code change | median turns | median s/turn |
|---|---|---|---|---|---|
| Ling-3.2-air (LG) | **1/15** | 15 | 14 | 12 | 100 |
| production, Flash-Next on Halogen (E154) | 15/15 | 0 | 0 | | |

## Thinking off (A2: the first 5 everyday fixes, same server and sampling, `enable_thinking: false` per request)

**0 of 5, and no code changed on any of them.** Turns became about 14 times faster (median 7.1s against 100s), but Ling
used them to repeat itself: on one task it ran the same search 175 times out of 200 turns. Two runs hit the 200-turn
limit, two the 20-minute limit, and one filled the 131,072-token context with repeated output. The switch took
effect by the evidence available (replies 3-5 times shorter than with thinking on); the harness does not store
reasoning text for either arm, so that check is indirect.

So thinking was not only slowing Ling down; it was what kept it from looping. Neither setting makes it a coding
candidate. The 10-fix bank (A1's second leg) is not run: with 1/15 on the everyday fixes and 0/5 with thinking off,
it would cost about 10h to confirm a result the easier bank already gives.

## Predictions

| | prediction (field) | result |
|---|---|---|
| P1 | tg128 d0 (94f3af3d0) > 26.68 | **HELD** (36.62) |
| P2 | tg128 d32768 / d0 >= 90% | **FALSIFIED** (82%) |
| P3 | pp512 d0 >= 300 | **HELD** (479.90) |
| P4 | ae6a7ad2c vs 94f3af3d0 tg128 d0 within 5% | **HELD** (0.05%) |
| P5 | pass_count >= 3 | **FALSIFIED** (0) |
| P6 | pass_count < 5 | **HELD** (0) |
| P7 | wall_median_s < 685 | **FALSIFIED** (1,426) |
| P8 (A1) | pass_count on the 15 everyday fixes >= 5 | **FALSIFIED** (1/15) |
| P11 (A2) | median wall_time / turns under 30s | **HELD** (7.1s) |
| P12 (A2) | passed on at least 1 of 5 | **FALSIFIED** (0/5) |
| P13 (A2) | diff non-empty on at least 3 of 5 | **FALSIFIED** (0/5) |

## Limits

Q3_K_M (about 3.9 bits) against production's 4.5-bit quant; one attempt per task; the context limit (131K) is a
configuration choice shared with every llama.cpp arm on this bank. A larger quant or context could change some
failures, but not five context exhaustions and three false "done"s on a bank where production solves half.

## Evidence

Speed: `results/e176/bench-94f3af3d0-d0.md`, `results/e176/bench-94f3af3d0-d32768.md`, `results/e176/bench-94f3af3d0-d8192.md`, `results/e176/bench-ae6a7ad2c-d0.md`, `results/e176/bench-ae6a7ad2c-d32768.md`, `results/e176/bench-ae6a7ad2c-d8192.md`.
Per-task coding records are withheld (WITHHELD.md): they quote private repositories.
