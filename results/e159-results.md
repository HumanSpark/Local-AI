<!--
# File: e159-results.md
# Purpose: Results of E159 - does Flash-Next keep its coding score at lower reasoning effort, and does the community template help?
# Project: sparkbench | Date: 2026-11-13
#
# Overview: Scored by tools/score_e159.py against results/e159-prereg.md (P1-P6, amendments 1-6). Raw scoring records:
# results/e159/raw/<arm>/<task>.json (357e006); full transcripts on disk under results/e159/transcripts/<arm>
# (gitignored, sha256 in each record). Finding F187.
-->

# E159 RESULTS - low effort on the community template keeps 8/10 at 0.30x the time (2026-11-13)

## In plain English

Our best local coding model ran at its maximum thinking setting by default. That was slow: about 20 minutes per fix.
We tried four lower settings on the same ten real fixes.

Every setting except one scored 8 out of 10, the same as maximum thinking tonight. The exception was the stock template
at low, which scored 7. A one-fix difference is within our noise rule, so none of them is measurably worse.

The fastest was the community "fixed" template at low thinking: 5.8 minutes per fix against 19.1 at maximum, with about
a third of the thinking (17,802 tokens against 50,114).

Two details matter for choosing. On the stock template, "low" barely thinks less than "medium". On the community
template, low really does cut the thinking. And the community template at its own default thinks more than the stock
template at medium, so the template by itself is not what makes things fast. The setting is.

## Results (same 10 tasks as E156; one run each; temperature 1.0)

| arm | template | effort | solved | median tokens | median min/task | total h |
|---|---|---|---|---|---|---|
| HX | stock | xhigh (control) | 8/10 | 50,114 | 19.1 | 3.31 |
| HM | stock | medium | 8/10 | 24,957 | 10.2 | 1.68 |
| HL | stock | low | 7/10 | 24,185 | 8.3 | 1.30 |
| HF | community v22.5 | its default | 8/10 | 38,014 | 14.6 | 2.72 |
| **HFL** | community v22.5 | low | **8/10** | **17,802** | **5.8** | **1.06** |

E156 H (stock, xhigh by default, kernel 7.0.0-38) scored 9/10 at 59,437 tokens and 21.3 min.

### Per task

| task | HF | HFL | HM | HL | HX |
|---|---|---|---|---|---|
| clearmail-a5fc6d93b | P | P | P | P | P |
| clearmail-f7d71f21c | P | P | P | P | P |
| clearmail-ea3f86782 | P | P | P | P | P |
| sparkforge-baab4031f | P | P | P | P | P |
| sparkforge-99cb03e95 | P | . | . | . | P |
| sparkforge-49785eb67 | P | P | P | P | P |
| sparkforge-ccf81588b | . | P | P | . | . |
| workstation-dotfiles-d6d81ce51 | . | . | . | . | . |
| workstation-dotfiles-ad8324027 | P | P | P | P | P |
| workstation-dotfiles-08dad841c | P | P | P | P | P |

sparkforge-99cb03e95 has source-text tests (F183). Only the high-thinking arms pass it. workstation-dotfiles-d6d81ce51
fails at every setting.

## Predictions

| | prediction | verdict |
|---|---|---|
| P1 | HM tokens_median <= 0.5 x HX | HELD (24,957 v 50,114 = 0.50) |
| P2 | HM pass_count >= HX - 1 | HELD (8 v 8) |
| P3 | HL pass_count <= HM | HELD (7 v 8) |
| P4 | HF within 1 of HM on passes AND within 25% on tokens | **FAILED** (passes 8 v 8; tokens +52%) |
| P5 | HX pass_count >= 8 | HELD (8) |
| P6 | HX wall_median_s >= 3 x HM | **FAILED** (1,146 v 610 s = 1.9x) |

P4 failed on tokens: the community template's default (medium per its own text) thinks about half as much again as the
stock template's medium. P6 failed because medium took longer than predicted, not because xhigh was fast.

## Decision

The prereg's rule: an arm that meets the speed bar and is within 1 of HX on passes is recommended. HFL, HM and HF all
qualify; HFL is the fastest by a wide margin. The owner then asked for HFL to be tested across all usage as the
production candidate (E160, F186).

## Run notes (all declared in amendments before the affected runs)

- The first attempt (00:36Z) was stopped for another GPU job. It resumed at 18:25Z (amendment 1).
- HF 4/10 was cut off by a failed pause at 19:23Z, set aside, and re-run (amendment 2; the set-aside record is in
  `raw/HF/superseded/`).
- The deadline was extended, then removed (amendments 3-4). The order was swapped to HL before HM 8-10 (amendment 5).
  HX was paused for E160 after HX 7 and resumed for HX 8-10 (amendment 6).
- Amendment 5's stated time (00:55Z) should be 00:52Z. That is corrected in amendment 6.
