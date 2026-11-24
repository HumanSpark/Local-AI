<!--
# File: results/e177-results.md
# Purpose: Results of E177 - Qwen3.8 Flash-Next on the HTR (Halo Trellis) engine against production Halogen.
# Project: sparkbench | Date: 2026-11-24
#
# Overview: Scored against results/e177-prereg.md. Speed: tools/e163_speed.py on both engines the same day
# (results/e177/raw/HS, HT). Quality: the hard coding bank (results/e167/bank.jsonl) on HTR, compared with production's
# run of the same bank on 2026-11-18. Raw task records: results/e177/raw/HT/ (stripped; transcripts gitignored).
-->

# E177 RESULTS - Flash-Next on HTR vs production Halogen (2026-11-24)

## In plain English

A community member compressed our production model, Qwen3.8 Flash-Next, with their own method (HTR) and serves it
with their own build of vLLM, tuned for this chip. We timed it against production's engine, Halogen, on the same day,
then gave it our ten hard real coding fixes. It solved 6, one more than production solved last week, so the compression
costs no quality we can measure. But it is slower: Halogen writes short answers about 30% faster and reads long
documents about 1.6 times faster. HTR is a credible second engine for the same model, not a replacement for Halogen.

## Speed (client-timed medians, thinking off, E139 prompts)

| field | HTR | Halogen (production, live, same day) |
|---|---|---|
| decode, short prompt (tok/s) | 47.8 | 62.5 |
| decode after an 8K prompt | 44.9 | 30.1 (see note) |
| decode after a 32K prompt | 44.1 | 43.7 |
| prefill, 8K prompt (tok/s) | 969 | 1,492 |
| prefill, 32K prompt (tok/s) | 924 | 1,462 |
| wait for first token, 32K prompt (s) | 35.5 | 22.4 |

Halogen was timed while serving normally, so another request may have shared the engine; its 8K decode (30.1) is out
of line with its own short and 32K figures. HTR was timed in a closed window, MTP3 (its default) on.

## Hard coding bank (10 tasks, 3,600 s each, podman isolation, one attempt)

| task | HTR (today) | production, Halogen (2026-11-18) |
|---|---|---|
| clearmail-3d41463d0 | pass (context limit reached after the fix) | pass |
| clearmail-7fe0a79c1 | pass | pass |
| clearmail-01d445d75 | **pass** | fail |
| sparkforge-22dee74e9 | fail | **pass** |
| sparkforge-66de8e1d0 | fail (context limit) | **pass** |
| sparkforge-625dcc2f8 | **pass** | fail |
| workstation-dotfiles-a0d0e6f0d | fail | fail |
| workstation-dotfiles-ffaf96580 | pass | pass |
| another GPU job-390973aee | **pass** (context limit reached after the fix) | fail |
| another GPU job-5ca87050b | fail (context limit) | fail |
| **pass_count** | **6** | **5** |

HTR median 1,459 s a task (production 685 s), 3.89 h in total. Four HTR tasks ended when the conversation reached the
131,072-token limit set for this run (vLLM refused the next request); two of those had already passed. Production's run
had no such stops (every task ended with the model declaring done); its context is set inside the Halogen image.

## Predictions

| | prediction (field) | result |
|---|---|---|
| P1 | HTR short-prompt decode >= 45 tok/s | **HELD** (47.8) |
| P2 | HTR short-prompt decode < Halogen same day | **HELD** (47.8 vs 62.5) |
| P3 | HTR 32K prefill < Halogen same day | **HELD** (924 vs 1,462) |
| P4 | HTR loads with no DeviceLost or out-of-memory, first start within 60 min | **HELD** (458 s, then ~450 s at 131K) |
| P5 | HTR pass_count >= 4/10 | **HELD** (6/10) |

## Deviations and notes

- **Memory during the 131K load:** free memory fell to about 2 GiB for a moment while the GPU took ~76 GiB, with ~42
  GiB of page cache that clearing could not release (unlike the first load, where clearing the container store freed
  35 GiB). It recovered without error. Loads of this size stay owner-attended.
- **Comparison limits:** one attempt per task, a week apart, different engines and compression; each side solved two
  tasks the other missed. 6 against 5 is within noise; the claim is "no measurable quality loss", not "better".
- The pre-run image check found only localhost URLs in HTR's code and vLLM usage statistics already off
  (results/e177/security-scan.md).
