# E31 Local Results Summary (MAXTOK=8192)

> **⚠ Provenance note (2026-07-12).** The tables in the earlier version of this file were
> hand-typed and systematically corrupt: the Total column was set equal to the Passed count
> (e.g. `29/29` instead of `29/30`), so every model read a false 100%; the E27 comparison
> column had drifted too. All values below are CORRECTED against the raw promptfoo JSONs.
> **Canonical machine-generated table:** `results/deep-eval/local-results-canonical.md`.
> Regenerate/verify with `python3 tools/verify_cloud_results.py --prefix e31-local-`
> (add `--check <this file>` to gate against drift). CIs are Wilson 95%. E31 is the
> **uncapped** condition (MAXTOK=8192); E27 is the capped run - do not compare across without
> saying which.

## Overview

Complete local benchmark of four models (qwen3-4b, qwen3-30b-a3b workhorse, MiniMax-M2.7,
Qwen3.5-397B) across the two core suites, uncapped at MAXTOK=8192.

## Results: Summarisation Suite (n=30, uncapped)

| Model | Passed | Total | Score (Wilson 95% CI) | Raw file |
|---|---|---|---|---|
| qwen3-4b | 29 | 30 | 96.7% (CI 83.3-99.4) | `e31-local-qwen3-4b-summarisation.json` |
| qwen3-30b-a3b (workhorse) | 28 | 30 | 93.3% (CI 78.7-98.2) | `e31-local-workhorse-summarisation.json` |
| MiniMax-M2.7 | 24 | 30 | 80.0% (CI 62.7-90.5) | `e31-local-minimax-summarisation.json` |
| Qwen3.5-397B | 20 | 30 | 66.7% (CI 48.8-80.8) | `e31-local-qwen35-397b-summarisation.json` |

## Results: Instruction-Following Suite (n=24, uncapped)

| Model | Passed | Total | Score (Wilson 95% CI) | Raw file |
|---|---|---|---|---|
| qwen3-4b | 22 | 24 | 91.7% (CI 74.2-97.7) | `e31-local-qwen3-4b-instruction-following.json` |
| qwen3-30b-a3b (workhorse) | 21 | 24 | 87.5% (CI 69.0-95.7) | `e31-local-workhorse-instruction-following.json` |
| MiniMax-M2.7 | 9 | 24 | 37.5% (CI 21.2-57.3) | `e31-local-minimax-instruction-following.json` |
| Qwen3.5-397B | 9 | 24 | 37.5% (CI 21.2-57.3) | `e31-local-qwen35-397b-instruction-following.json` |

**Key findings:**
- No length-finishes at MAXTOK=8192.
- The direct small model (qwen3-4b) leads on both suites; the workhorse follows.
- The reasoning-emitting models (MiniMax, 397B) score low on instruction-following (37.5%
  as-emitted) - reasoning prose contaminates the strict-format output.

## Comparison: E27 (capped) vs E31 (uncapped)

Both columns verified against raw. The workhorse was not part of the E27 local batch, so its
capped baseline is not shown.

| Model | Summ E27 | Summ E31 | IF E27 | IF E31 |
|---|---|---|---|---|
| qwen3-4b | 28/30 (93.3%) | 29/30 (96.7%) | 18/24 (75.0%) | 22/24 (91.7%) |
| qwen3-30b-a3b (workhorse) | n/a (not in E27 batch) | 28/30 (93.3%) | n/a | 21/24 (87.5%) |
| MiniMax-M2.7 | 27/30 (90.0%) | 24/30 (80.0%) | 10/24 (41.7%) | 9/24 (37.5%) |
| Qwen3.5-397B | 26/30 (86.7%) | 20/30 (66.7%) | 10/24 (41.7%) | 9/24 (37.5%) |

Note the asymmetry: uncapping raised the direct small model (qwen3-4b, +3.4pp summ, +16.7pp
IF) but LOWERED the reasoning-emitting models (MiniMax summ 90.0% -> 80.0%; 397B 86.7% ->
66.7%). A larger budget gave the reasoning models more room to emit thinking prose, which the
as-emitted grader penalises - consistent with the E31 decision rule that reasoning emitters
are unsuitable for strict-format document work on this stack.

## Wall-Clock Times (estimates from server logs)

- qwen3-4b: ~3-5 min per suite
- qwen3-30b-a3b (workhorse): ~3-5 min per suite
- MiniMax-M2.7: ~8-10 min per suite (TIMEOUT_S=5400)
- Qwen3.5-397B: ~30-60 min per suite (TIMEOUT_S=7200, near-edge)

## Notes

- MAXTOK=8192 liberates token budgets; no output hit a length-finish.
- Reasoning models (MiniMax, 397B) need a content-extracted view for a fair capability read;
  the as-emitted scores above include the reasoning-contamination penalty.
- Paired with the cloud E31 results (`results/deep-eval/e31-cloud-summary.md`) for the full
  campaign assessment.
