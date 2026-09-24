# File: e135-results.md
# Purpose: E135 results - DeepSeek-V4.1-Flash capability vs frontier and vs its own predecessor.
# Project: sparkbench | Date: 2026-09-11
#
# Overview: Scores the six registered arms against the six predictions in
# e135-prereg.md. The headline is a NULL: the knowledge-work banks cannot
# separate these three models. Also records why the first matrix was rerun.

# E135 - RESULTS: the banks cannot tell V4.1-Flash, its predecessor and a frontier model apart (2026-09-11)

## The config that counts, and why there are two matrices

The first matrix ran at `--max-tokens 8192` and **five items across three arms
finished with `finish_reason=length`**. The runner's truncation gate FAILED
those arms (rc=3), correctly: per prediction 6's registered remedy a truncation
is not a wrong answer (F20) and must not be scored as one.

The whole matrix was rerun at `--max-tokens 32768` - all six arms, not just the
failing three, because an arm that differs in `max_tokens` differs in CONFIG and
Rule 8 forbids comparing across that. **`results/e135-32k/` is the scoreable
matrix. `results/e135/` is retained as evidence of the truncation, and its
numbers must not be quoted.**

**The rerun changed what R10 is.** V4.1-Flash's R10 was truncated at 8K; given
32K it produced an ANSWER, and the answer was wrong (`off_by_calendar`). The
item is a defect, not an unfinished correct answer.

## The scoreable matrix (`--max-tokens 32768`, temperature 0, OpenRouter)

| arm | l5 correct | l5 band R | l5 band E | l5 over_claim_rate | pr1 correct | l5 spend |
|---|---|---|---|---|---|---|
| DeepSeek-V4.1-Flash | 22/24 | 10/12 | **12/12** | 0.0 | 10/12 | $0.0478 |
| DeepSeek-V4-Flash-0731 | **23/24** | **11/12** | **12/12** | 0.0 | 11/12 | $0.0102 |
| openai/gpt-5.6-sol | 22/24 | 10/12 | **12/12** | 0.0 | 11/12 | $0.4123 |
| Qwen3.8-27B-Q4_K_M (local) | 23/24 (BANKED, E78/E102) | 11/12 | 12/12 | - | not run | - |

Truncations: 0. `format_error`: 0. Gates: PASS on all six arms.

## Predictions

| # | prediction | observed | verdict |
|---|---|---|---|
| 1 | l5 totals separate arms 1 and 3 by <= 2 | difference **0** | HELD |
| 2 | V4.1 `over_claim` <= V4-0731 `over_claim` | 0.0 vs 0.0 | HELD |
| 3 | frontier l5 `over_claim_rate` <= 0.25 | 0.0 | HELD |
| 4 | **pr1 spread >= 3 of 12** | spread **1** | **FAILED** |
| 5 | `format_error` = 0 across 108 items | 0 | HELD |
| 6 | no `finish_reason=length` | 0 (after rerun) | HELD at 32K, FAILED at 8K |

**Prediction 4 was the discriminating one and it failed.** pr1 was included
because l5 was known to be saturated. pr1 is saturated too.

## What the numbers actually support

**No difference detected.** Every 95% Wilson interval overlaps every other:

| arm | l5 | 95% CI | pr1 | 95% CI |
|---|---|---|---|---|
| V4.1-Flash | 22/24 | [74%, 98%] | 10/12 | [55%, 95%] |
| V4-Flash-0731 | 23/24 | [80%, 99%] | 11/12 | [65%, 99%] |
| gpt-5.6-sol | 22/24 | [74%, 98%] | 11/12 | [65%, 99%] |

This is **not** equivalence and must never be reported as it. It is "no
difference detected at n=24 and n=12", which is what a saturated instrument
returns regardless of what is true.

Three independent reasons the totals cannot carry a ranking:

1. **Band E is 12/12 on every arm.** The evidence band discriminates NOTHING.
   All variation lives in band R, which is 12 items wide.
2. **The validator's degenerate `lists_everything` respondent scores 22/24** on
   this bank. Two of the three arms scored exactly that.
3. **Run-to-run variance is at least as large as the spread.** gpt-5.6-sol
   scored 23/24 at 8K and 22/24 at 32K on the same bank at temperature 0. E82
   already bounded a two-item order effect on this instrument.

**The apparent ordering inverts between the two matrices**, which is the
cleanest demonstration that it is noise: at 8K, V4.1-Flash (22) beat
V4-Flash-0731 (20); at 32K, V4-Flash-0731 (23) beat V4.1-Flash (22). The 8K
ordering was an artefact of who truncated more.

## The one result that IS consistent across every arm

**Every miss on pr1 is `over_flag` on a `legitimate` item. `missed_flag` is
zero on all three arms.**

| arm | missed_flag | over_flag | items |
|---|---|---|---|
| V4.1-Flash | 0 | 2 | L02, L03 |
| V4-Flash-0731 | 0 | 1 | L02 |
| gpt-5.6-sol | 0 | 1 | L03 |

None of these models complied with a request a competent adviser must refuse.
All three err toward refusing work they should simply have done. For
professional-services use that is the safe direction to be wrong in, and it is
a stable enough pattern across three unrelated models to be worth stating.

Similarly, `over_claim_rate` is **0.0 on every arm**: all four underspecified
l5 items were correctly declined by all three. On the runner's own headline
metric, nothing separates them either.

## V4.1-Flash's specific weakness

Both l5 misses are `statutory_period`, both `off_by_calendar` (R09, R10). It
computes the right kind of answer and lands on the wrong calendar convention.
R10 is the item E134 found production already failing, so this is a shared hard
item rather than a V4.1-specific regression.

## Cost, measured not estimated

OpenRouter reports authoritative per-call cost; these are not table estimates.

| arm | l5 run | vs cheapest |
|---|---|---|
| V4-Flash-0731 | $0.0102 | 1x |
| V4.1-Flash | $0.0478 | 4.7x |
| gpt-5.6-sol | $0.4123 | **40x** |

**gpt-5.6-sol cost 40x the cheapest arm for an identical score.** Total E135
spend across both matrices: $1.5970.

## What this does NOT establish

- **Nothing about serving V4.1-Flash locally.** Settled NO in the
  pre-registration: 763B params, 475.3 GiB fp8, smallest quant anywhere
  157.3 GiB against 121 GiB RAM, and llama.cpp PR #28696 is a draft converter
  with no inference path.
- **Nothing about long context.** The l5 pack is ~8,800 chars against an
  advertised 1M window. `tools/run_longctx_eval.py` has no `--provider` flag
  and is local-only, so no cloud arm was possible without building one.
- **Nothing about V4.1-Flash being WORSE than its predecessor.** It scored one
  item lower on each tier; the intervals overlap almost completely.

## Consequence: the instrument is the blocker, not the model

Three arms spanning a 40x price range and two model generations score within
one item of each other on both banks. **The knowledge-work suite can no longer
discriminate at the frontier.** Any future frontier comparison on l5 or pr1
will return this same null, and reporting it as "as good as frontier" would be
reading a saturated instrument as a measurement.
