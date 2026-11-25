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

## Limits

Q3_K_M (about 3.9 bits) against production's 4.5-bit quant; one attempt per task; the context limit (131K) is a
configuration choice shared with every llama.cpp arm on this bank. A larger quant or context could change some
failures, but not five context exhaustions and three false "done"s on a bank where production solves half.

## Evidence

Speed: `results/e176/bench-94f3af3d0-d0.md`, `results/e176/bench-94f3af3d0-d32768.md`, `results/e176/bench-94f3af3d0-d8192.md`, `results/e176/bench-ae6a7ad2c-d0.md`, `results/e176/bench-ae6a7ad2c-d32768.md`, `results/e176/bench-ae6a7ad2c-d8192.md`.
Per-task coding records are withheld (WITHHELD.md): they quote private repositories.
