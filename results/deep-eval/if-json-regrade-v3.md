# File: if-json-regrade-v3.md
# Purpose: Offline v3 re-grade of the three JSON instruction-following tests after the IIFE/body-wrap grader bug fix (commit ea316a1).
# Project: sparkbench | Date: 2026-07-11
#
# Overview: The v2 suite fix wrapped the JSON assertions in IIFEs; promptfoo
# body-wraps any snippet containing 'return', so the IIFE value was discarded
# ("Got type undefined") and ALL 8 completed runs auto-failed all 3 JSON tests
# despite provably valid outputs. The fixed body-form assertions are pure
# functions of the stored output text, so completed runs were RE-GRADED
# offline (node, exact promptfoo body-wrap semantics) - no model re-runs
# needed, fully deterministic, identical assertion both sides.

## Corrected instruction-following totals (v2 grader -> v3 re-grade)

| Run | v2 | v3 | JSON tests recovered |
|---|---|---|---|
| cloud-gpt54mini-v2 | 19/24 | 22/24 (91.7%) | +3 |
| cloud-gpt56sol-v2 | 17/24 | 20/24 (83.3%) | +3 |
| sanity-workhorse-if-v2 (local) | 18/24 | 21/24 (87.5%) | +3 |
| e27-local-qwen3-4b | 18/24 | 21/24 (87.5%) | +3 |
| cloud-mistral-large-v2 | 12/24 | 15/24 (62.5%) | +3 |
| cloud-mistral-small-v2 | 11/24 | 14/24 (58.3%) | +3 |
| cloud-mistral-medium-v2 | 10/24 | 11/24 (45.8%) | +1 |
| cloud-magistral-medium-v2 | 3/24 | 3/24 (12.5%) | +0 (genuinely non-compliant) |

MiniMax and Qwen3.5-397B IF runs started AFTER the fix landed on disk and
need no re-grade. Summarisation and long-context runs are unaffected (no
IIFE assertions).

## Why this is sound

The assertion is a deterministic pure function of the stored output string;
re-evaluating it offline with the identical body-wrap semantics promptfoo
uses is the same measurement, correctly executed. Corrected totals supersede
the v2 IF columns everywhere; v2 raw JSONs remain untouched on disk.
