<!--
# File: e152-prereg.md
# Purpose: Pre-registration for E152 - halogen-flash-server 0.14.0's README rows that E139 did not test: served MTP decode at 32K, the coding-agent turn, the 100K follow-up.
# Project: sparkbench | Date: 2026-09-27
#
# Overview: E139 (F165, F166) tested halogen 0.13.8's prefill, serial decode and identity claims on this box. The README at
# 0.14.0 (fetched 2026-09-27, owner-pasted header) carries three rows a buyer feels and E139 did not measure: 46.0 tok/s
# served decode with the draft head at 32K, 55.7-56.3 tok/s on coding-agent turns with draft head plus prompt lookup, and
# ~2 s for a follow-up turn at 100,000 tokens of context through the prompt cache. One image (0.14.0 by digest), two arms,
# the E139 method (server-reported timings, 1 Hz memory and power, thinking off), Chatterbox resident, IOMMU translated.
# Written before any run; the image is pulled and the prompt set is built and committed.
-->

# E152 PRE-REGISTRATION - halogen 0.14.0: served decode, coding-agent turns, 100K follow-up (2026-09-27)

## The claims (README "Measured", 0.14.0, reference machine: 128 GB, ROCm 7.14.0, ~85 W sustained, IOMMU off)

| # | README row | figure | how it is measured there |
|---|---|---|---|
| C4' | decode, MTP speculation @ ctx 32,768, served | **46.0 tok/s** | mean over ten prompts, through the HTTP stack |
| C8 | decode, coding-agent turn, draft head + prompt lookup | **56.3** thinking off, 55.7 thinking on | six SWE-agent turns, ~1,000-1,800 tokens of context, 400 generated, greedy |
| C9 | follow-up turn at 100,000 tokens of context | **~2 s** | prompt cache on (default), a 20-turn session growing to 108,000 tokens |
| C1' | prefill @ 32,768 | 1,424 tok/s | continuity row; E139 measured 1,152 at 0.13.8 |
| C6' | temperature-0 output byte-identical to serial greedy | stated, "verified on every release" | E139: 4 of 4 at 0.13.8 |

The README also says decode depends on the power envelope ("match the power envelope before comparing decode numbers"; a tester
at 70 W saw 11-12% less) and prefill on the IOMMU (13-16%). Our box: IOMMU translated (DMA-FQ), power recorded per request.

## Arms

| arm | image | config | block |
|---|---|---|---|
| **H1** | 0.14.0, digest `ec7ec0c6f955...` (pulled 2026-09-27) | own checkpoint + quality overlay, image defaults (prompt cache on, draft head + prompt lookup) | 1: P32K x3 (256 gen), CODE x6 (400 gen), P100K (256 gen) then FOLLOWUP (64 gen) |
| **H1-id** | same | `HALOGEN_PROMPT_CACHE=0` | 2: D1500 + P8K x3, serial then MTP, byte compare |

Prompts: `results/e152/prompts.json` (`tools/e152_prompts.py`): E139's exact-token windows from the repo's own docs, plus P100K
(100,000 tokens from corpus token 60,000, a start no other window shares) and six coding-agent turns cut from the MLCommons
edge-agentic SWE-agent trajectories at 1,290-1,797 tokens of context with the assistant's turn next (tool results carried as
user messages, tools schema not passed). FOLLOWUP re-sends the P100K conversation plus the assistant's reply plus one 20-word
question. Differences from the README's method, declared: our coding turns are six trajectories cut once each, not a live
agent; our follow-up is one prior turn of 100K, not a 20-turn session; three P32K prompts, not ten.

## Gates

- G1: image present by digest and labelled 0.14.0; checkpoint files present; prompt set present.
- G2: `/health` 200 within 900 s (E139's P1 rule); the first request answers.
- G3: kernel, Livepatch, IOMMU type, GTT and Chatterbox residency recorded before the window; memory guard at 12 GiB
  MemAvailable armed per arm (a guard kill voids the arm, as E139's G0).

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `H1.load_s` | < 900 | E139: 77.3 s |
| P2 | `H1.P32K_median_prefill_tps` | 1,000-1,300 | E139 1,152; IOMMU translated here |
| P3 | `H1.P32K_median_decode_tps` (default drafting) | 36-46 | E139 38.1 at 0.13.8; the claim is 46.0 at 0.14.0 |
| P4 | `H1.CODE_mean_decode_tps` | 40-56 | claim 56.3; prompt lookup gains depend on how much the turn repeats its context; our power envelope unknown vs 85 W |
| P5 | `H1.FOLLOWUP_wall_s` | 1.5-6.0 | claim ~2 s; ours is one 100K turn then a question, 64 generated |
| P6 | `H1.FOLLOWUP_cache_n` | >= 95,000 | the cache must serve nearly the whole prefix or P5 cannot hold |
| P7 | `H1-id.identity_equal` | 4 of 4 | E139 4 of 4; "verified on every release" |
| P8 | `H1.memory.peak_gpu_gib` | 40-70 | E139 43.3 with 32K; the 100K prompt adds KV |
| P9 | `H1.P100K` prefill tok/s | 1,000-1,400 | README: 131,072 tokens at 1,358 (95% of 32K rate) |

## Decision bands (fixed now)

- A README row is **reproduced** if our figure is within 15% of it (the README's own IOMMU and power allowances are 11-16%);
  **reproduced conditionally** at 70-85%; **not reproduced** below 70%. For C9 (~2 s) the bands are <= 2.3 s, 2.3-4 s, > 4 s.
- Power is recorded per request (amdgpu `power1_average`) and reported beside every decode figure; no correction is applied.
- E139's F165/F166 stand; this experiment adds rows, it does not re-score them.

## Out of scope

The 1M-context configuration, GGUF mode (E139 G0: cannot load beside Chatterbox), vision, thinking-on decode, IOMMU off (a BIOS
change on the production box, the owner's), stopping Chatterbox.

## Amendment 1 (2026-09-27 03:01, before the window opened)

The GPU is not idle: Chatterbox TTS (spark-infer) has held it at 81-99% `gpu_busy_percent` since at least 02:00 (synth's render
batch), and 50 minutes of waiting for it to finish did not end it. The window opens anyway, as E139 did with Chatterbox resident,
and the difference is declared: E139 had the service RESIDENT (memory), E152 has it ACTIVE (compute). Every decode figure is
therefore a lower bound on what the engine does on an idle box; `gpu_busy_percent` is recorded at window open, and the bands
stand as written. If a claim lands in "not reproduced" with Chatterbox active, it is reported as "not reproduced under
contention" and not as a verdict on the engine.
