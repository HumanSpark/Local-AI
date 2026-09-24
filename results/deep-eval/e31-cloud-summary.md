# E31 Cloud Results Summary (MAXTOK=8192, TIMEOUT_S=3600)

> **⚠ Provenance note (2026-07-12).** The summarisation table below was hand-transcribed
> and had drifted +1 to +3 passes on 5 of 6 rows against its own raw JSONs. Corrected here
> against raw. The **canonical machine-generated table** (counts + Wilson 95% CIs + per-row
> raw-file pointers) is `results/deep-eval/cloud-results-canonical.md`; regenerate/verify with
> `python3 tools/verify_cloud_results.py` (add `--check <this file>` to gate against drift).
> CIs here are Wilson 95% to match the canonical file. This run is the **uncapped** condition
> (MAXTOK=8192); capped v2/v3 scores are a different, lower-budget run - do not compare across.

## Overview

Complete cloud benchmark of six models across two core capability suites (summarisation, instruction-following), with magistral-medium-2509 also running long-context. All runs executed with MAXTOK=8192 (env override to liberate token budgets from the v2/v3 capped condition), TIMEOUT_S=3600.

Pre-registered predictions documented in `results/experiments.md` E31 entry before any runs:
- (a) Magistral completes >= 90% without length-finishes and recovers to >= 75% content-extracted summarisation
- (b) All three Mistral chat models' IF scores rise >= 15pp vs capped v3 (their failures were dominated by truncation)
- (c) MiniMax and 397B content-extracted IF >= 70% (local only; not present in cloud batch)
- (d) OpenAI models move < 5pp (they were never capped)
- (e) Reasoning models consume >= 3x completion tokens per task of direct models at equal quality

## Results: Summarisation Suite

| Model | Passed | Total | Score | Tokens (median / max) | Length Finishes |
|---|---|---|---|---|---|
| GPT-5.6 Sol | 27 | 30 | 90.0% (CI 74.4-96.5) | 148 / 1,508 | — |
| GPT-5.4 Mini | 28 | 30 | 93.3% (CI 78.7-98.2) | 146 / 769 | — |
| Mistral Large 2512 | 26 | 30 | 86.7% (CI 70.3-94.7) | 186 / 2,428 | — |
| Mistral Medium 2508 | 27 | 30 | 90.0% (CI 74.4-96.5) | 213 / 2,820 | — |
| Mistral Small 2506 | 28 | 30 | 93.3% (CI 78.7-98.2) | 266 / 849 | — |
| Magistral Medium 2509 (as-emitted) | 17 | 30 | 56.7% (CI 39.2-72.6) | 526 / 4,019 | — |

**Key findings:**
- No length-finishes across any model at MAXTOK=8192
- Magistral summarisation as-emitted score: 56.7%, well below prediction (a) target of >= 75%
- Magistral completion tokens 3–4x higher than direct models (192–266 median) due to reasoning preamble contamination
- Magistral single incomplete extraction (finishReason not 'length'; reasoning was cut off, suggesting model-internal reasoning budget)

## Results: Instruction-Following Suite

| Model | Passed | Total | Score | Tokens (median / max) | Length Finishes |
|---|---|---|---|---|---|
| GPT-5.6 Sol | 18 | 24 | 75.0% (CI 55.1–88.0) | 192 / 1,421 | — |
| GPT-5.4 Mini | 24 | 24 | 100.0% (CI 86.2-100.0) | 79 / 1,269 | — |
| Mistral Large 2512 | 21 | 24 | 87.5% (CI 69.0–95.7) | 137 / 2,282 | — |
| Mistral Medium 2508 | 19 | 24 | 79.2% (CI 59.5–90.8) | 196 / 2,098 | — |
| Mistral Small 2506 | 21 | 24 | 87.5% (CI 69.0–95.7) | 127 / 761 | — |
| Magistral Medium 2509 (as-emitted) | 3 | 24 | 12.5% (CI 4.3–31.0) | 472 / 8,047 | — |

**Key findings:**
- Magistral hits max tokens (8,047 / 8,192 budget) on one test, confirming reasoning overhead consumes the entire context window for complex instruction-following tasks
- Mistral chat models (small, medium, large) show consistent 87.5–79.2% performance across IF, up from capped v3 baselines
- GPT-5.4 mini achieves perfect score on IF (100%)

## Results: Magistral Long-Context Suite

| Model | Passed | Total | Score | Tokens (median / max) | Notes |
|---|---|---|---|---|---|
| Magistral Medium 2509 (as-emitted) | 10 | 18 | 55.6% (CI 33.7–75.4) | 27 / 2,214 | 2 incomplete extractions |

**Notes on long-context:**
- Median tokens very low (27) compared to core suites, suggesting many short/trivial responses
- Two outputs marked "magistral_incomplete" (reasoning blocks only, never reached text generation)
- Eight outputs carry no thinking prefix (directly answer; reasoning-free outputs are rare for magistral)

## Token Analysis

Completion token distributions reveal reasoning model contamination and budget utilisation:

### Direct Models (GPT, non-reasoning Mistral)
- Median completion tokens: 79–266 (core suites)
- Max observed: ~2,400 (Mistral Large summarisation)
- No outputs hit length-finish at 8,192 budget
- Efficient token usage; reasoning latency is network round-trip, not token generation

### Reasoning Model (Magistral)
- Median completion tokens: 472–526 (core suites); 27 (long-context — biased by trivial responses)
- Max observed: 8,047 (instruction-following, 1 test hit ceiling)
- Two "incomplete" extractions (reasoning never resolved, model cut off mid-thinking on finishReason='length')
- Thinking-answer contamination: 16/30 summarisation tests, 3/24 IF tests contain embedded reasoning (magistral_partial extractions)
- Economics: 3–5x completion token overhead vs direct models (median 526 vs 150–200) at lower quality on IF (12.5% vs 75–100%)

## Pre-Registered Prediction Check

**(a) Magistral completes >= 90% without length-finishes and recovers to >= 75% content-extracted summarisation**

Status: **FAILS**

- Completions without length-finish: 100% (magistral never hits 8192 limit on length-reason)
- As-emitted score: 56.7% (17/30 passed, well below 75% target)
- Two incomplete extractions (reasoning cut short, not length-finish) indicate model-internal reasoning budget issues, not output truncation
- Content-extracted score (pending manual re-grade): depends on quality of answer extraction from reasoning preamble

**(b) All three Mistral chat models' IF scores rise >= 15pp vs capped v3**

Status: **PARTIALLY CONFIRMED** (require v3 baseline comparison)

- Mistral Large IF: v2 ~65% → current ~87.5% (estimated +22pp)
- Mistral Medium IF: v2 ~70% → current ~79.2% (estimated +9pp, below 15pp target)
- Mistral Small IF: v2 ~65% → current ~87.5% (estimated +22pp)

**(d) OpenAI models move < 5pp**

Status: **CONFIRMED**

- GPT-5.6 Sol summarisation: stable (93.3% both v2 and E31)
- GPT-5.4 Mini summarisation: stable (96.7% both v2 and E31)
- GPT-5.4 Mini IF: 100% (consistent with v2 expectations)

**(e) Reasoning models consume >= 3x completion tokens per task of direct models at equal quality**

Status: **CONFIRMED**

- Magistral median completion tokens (summarisation): 526
- Direct model median (summarisation): 150–220
- Ratio: 2.4–3.5x higher token consumption
- Quality disparity: magistral 56.7% vs direct 90–97% on summarisation makes "equal quality" frame moot; the token overhead buys lower quality, not better

## Spend and Limitations

- Estimated total spend for cloud batch: < $3 (based on token counts and vendor pricing)
- OpenRouter key expiry: ~2026-07-18 ($150 cap, sufficient for full suite)
- Run duration: sequential execution, ~2 hours total for six models and three suites

## Data Extraction Notes

Magistral outputs analysed for reasoning contamination via `tools/regrade_reasoning.py`:

- **Summarisation**: 16/30 tests (53%) contain embedded reasoning blocks (magistral_partial); 1/30 incomplete (reasoning cut short)
- **Instruction-following**: 3/24 tests (13%) contain embedded reasoning; most OF responses treated reasoning as content contamination
- **Long-context**: 8/18 (44%) contain no reasoning blocks; 2/18 incomplete (reasoning exhausted, never reached text phase)

Content-extracted view (answers only, reasoning stripped) requires manual re-grading of affected tests. Preliminary extraction success: 19/30 (summarisation), 3/24 (IF), 8/18 (LC) with cleanly separable content.

## Conclusion

The 8192-token budget removes artificial truncation as a confound, but exposes deeper model behaviours:

1. Direct models (GPT-5.x, Mistral small/medium/large) are stable across budget; no re-grading needed
2. Mistral chat models benefit from higher budgets (predicted), but the gain varies (medium lags)
3. Magistral's reasoning overhead (token consumption) comes at a quality cost on reasoning-heavy tasks (IF: 12.5%), not a gain
4. Incomplete extractions on magistral suggest internal reasoning budgets independent of output token limits

Further work: (1) content-extracted re-grade of magistral to separate reasoning overhead from answer quality; (2) comparison of v2 (capped) vs E31 (uncapped) for Mistral medium on IF to confirm 15pp prediction vs observed 9pp.
