# File: e152-results.md
# Purpose: Results for E152 - halogen 0.14.0's served decode, coding-agent and 100K follow-up rows, measured with the TTS service actively rendering on the same GPU.
# Project: sparkbench | Date: 2026-09-27
#
# Overview: Scored against results/e152-prereg.md and amendment 1. One window 03:01-03:10 (560 s), two arms, no guard kill,
# 0 amdgpu fault lines, gateway restored 03:10:35. Under an active Chatterbox render (98% GPU busy at open) the coding-agent
# turns averaged 44.0 tok/s (two of six at the claimed 56), served decode at 32K was 33.9 (claim 46.0), the 100K follow-up
# served its whole prefix from cache in a 4.0 s turn (1.8 s before generation began), identity held 4 of 4, and power sat at
# 84.3-85.1 W throughout, the vendor's own envelope. Against E139 on the same box with the TTS service idle, prefill fell 27%
# and serial decode 33%: the cost of sharing the APU, measured. Registered as F179.

# E152 RESULTS - halogen 0.14.0 under contention: coding turns 44 tok/s, follow-up 4.0 s, identity holds (2026-09-27)

## Conditions

Image 0.14.0 by digest `ec7ec0c6f955...`; own checkpoint plus quality overlay; image defaults (prompt cache on, draft head +
prompt lookup); thinking off; kernel 7.0.0-31, Livepatch nothing-to-apply, IOMMU translated (DMA-FQ). **Chatterbox TTS was
rendering throughout: 98% `gpu_busy_percent` at window open, 5 spark-infer processes** (amendment 1; E139 had it resident but
idle). Load 86.8 s (H1) and 42.3 s (H1-id). Peak GTT+VRAM 41.41 GiB over a 6.34 GiB baseline; MemAvailable never below 71 GiB.
Power per request 84.3-85.1 W (amdgpu `power1_average`), the README's "~85 W sustained".

## Block 1 - the rows E139 did not test

| README row | claim | measured (H1) | ratio | band (amendment 1: under contention) |
|---|---|---|---|---|
| decode, MTP, served, ctx 32,768 | 46.0 tok/s | **33.89** median (34.85 / 19.36 / 33.89; 115-195 generated) | 0.74 | reproduced conditionally |
| coding-agent turn, draft head + prompt lookup, thinking off | 56.3 tok/s | **44.01** mean of 6 (17.59, 56.07, 55.93, 47.80, 41.35, 45.33; 47-103 generated) | 0.78 | reproduced conditionally; 2 of 6 turns at the claim |
| follow-up turn at 100,000 tokens | ~2 s | **4.0 s** wall for 64 generated at 29.4 tok/s; `cache_n` 100,012 of 100,227, 215 tokens prefilled; time before generation about **1.8 s** | 2.0 (wall) / 0.9 (to first token) | conditional on wall; the cache row itself holds |
| prefill, 32,768 (continuity) | 1,424 tok/s | **845.7** median (841.95-877.58) | 0.59 | not reproduced under contention (E139, TTS idle: 1,152, 0.81) |
| prefill, 100,012 tokens | 1,358 at 131K | **838.69** (119 s) | 0.62 | not reproduced under contention; depth decay 1%, as the README says |
| temperature-0 output byte-identical to serial greedy (H1-id, cache off) | stated | **4 of 4** (133 / 100 / 141 / 120 tokens each pair) | - | held |

Notes. Every coding-agent answer stopped on its own at 47-103 tokens (the README's row generates 400), so those rates carry
more warm-up weight than the vendor's; the two turns that reached 56 were the shortest prompts' neighbours, not the longest
answers. Halogen's `draft_n_accepted` exceeds `draft_n` on most requests (109/101, 41/35), so the pair is not drafted/accepted in
llama.cpp's sense; recorded, not scored (the JSON field `CODE_draft_accept_rate` = 1.214 is that quotient and means nothing).
Serial decode in H1-id: 22.67 / 22.46 / 16.20 / 21.66 tok/s; MTP on the same prompts 41.54 / 34.74 / 32.35 / 28.73.

## Same box, two days apart: the cost of an active neighbour

| | E139 (0.13.8, 2026-09-24, Chatterbox resident, idle) | E152 (0.14.0, Chatterbox rendering) | change |
|---|---|---|---|
| P32K prefill, median | 1,152.0 | 845.7 | -27% |
| P32K decode, default drafting | 38.1 | 33.9 | -11% |
| D1500 serial decode | 33.6 | 22.7 | -33% |
| D1500 MTP decode | 37-43 | 41.5 | 0 |
| power per request | (recorded) | 84.3-85.1 W | same envelope |
| peak GPU memory | 43.3 GiB | 41.4 GiB | same |

The version changed too (0.13.8 to 0.14.0), so the two arms are not a clean pair; the direction and size match what a second
compute-bound process on one APU should cost, and the power envelope did not move.

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `H1.load_s` | < 900 | 86.8 | HELD |
| P2 | `H1.P32K_median_prefill_tps` | 1,000-1,300 | 845.7 | FALSIFIED (contention; E139 1,152) |
| P3 | `H1.P32K_median_decode_tps` | 36-46 | 33.89 | FALSIFIED (2.1 below the floor) |
| P4 | `H1.CODE_mean_decode_tps` | 40-56 | 44.01 | HELD |
| P5 | `H1.FOLLOWUP_wall_s` | 1.5-6.0 | 4.0 | HELD |
| P6 | `H1.FOLLOWUP_cache_n` | >= 95,000 | 100,012 | HELD |
| P7 | `H1-id.identity_equal` | 4 of 4 | 4 of 4 | HELD |
| P8 | `H1.memory.peak_gpu_gib` | 40-70 | 41.41 | HELD |
| P9 | `H1.P100K` prefill | 1,000-1,400 | 838.69 | FALSIFIED (contention) |

## What this settles

1. The three untested rows are all in the right place and all overstated for a shared box: coding turns run at 78% of the
   claim on average and reach it on some turns; the served 32K decode at 74%; the 100K follow-up really does serve the whole
   prefix from cache and answers in about 2 s of overhead plus generation time.
2. The identity guarantee holds at 0.14.0 as it did at 0.13.8.
3. The number a buyer should carry is the contention column, not the README's: this engine assumes the machine. With the
   TTS service rendering beside it, prefill lost 27% and serial decode 33% against the same engine two days earlier with the
   service idle, at the same 85 W. The README says as much ("this server holds most of the host"); E152 puts a figure on it.
4. F165/F166 stand. The idle-box figures for 0.14.0 are not measured; a re-run with Chatterbox quiet would separate the version
   from the neighbour, and is one window when the GPU is free.

## Limits

One window, one run per arm, three P32K prompts against the README's ten, six coding turns cut once each from trajectories
rather than a live agent, a one-turn 100K context rather than a 20-turn session, IOMMU translated, GPU shared with an active
render throughout.
