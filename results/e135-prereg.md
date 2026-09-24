# File: e135-prereg.md
# Purpose: Pre-registration for E135 - DeepSeek-V4.1-Flash capability, measured through the API because it cannot be served locally.
# Project: sparkbench | Date: 2026-09-11
#
# Overview: Registers the question, the arms, the instrument, its known
# saturation, six predictions each naming the FIELD it is scored against, and
# the decision rule - all BEFORE any arm runs, per the repo's standing rule.

# E135 - PRE-REGISTRATION: what does DeepSeek-V4.1-Flash actually buy, and can we serve it? (2026-09-11)

## The question that was asked

The owner asked to benchmark `deepseek-ai/DeepSeek-V4.1-Flash`. That splits into
two questions with two different answers, and they must not be reported as one.

| | question | answer route |
|---|---|---|
| **A - serving** | can sparkmax run it? | measured against the artefact and the runtime, below. Settled BEFORE this register was written |
| **B - capability** | is it good enough to change what we recommend? | the API arms registered here |

## A - serving. Answered NO, and the answer is not close

Recorded here rather than as a prediction, because it was established before
registration and nothing in this experiment can move it.

| fact | value | authority |
|---|---|---|
| parameters | 763,205,315,794 | HF API, `deepseek-ai/DeepSeek-V4.1-Flash`, 2026-09-11 |
| fp8 weights | 475.3 GiB, 48 shards | HF API sibling sizes |
| smallest quant existing ANYWHERE | 157.3 GiB (`apetersson/DeepSeek-V4.1-Flash-MixedQ2-GGUF`) | HF API, 2026-09-11, 0 downloads |
| sparkmax RAM | 121 GiB total | `free -g` |
| sparkmax GTT ceiling | ~105 GiB | F109 |
| llama.cpp runtime support | NONE | PR #28696, DRAFT, opened 2026-09-10 |

**The 157.3 GiB floor is 36 GiB above total RAM before a byte of KV cache.** It
is not a download-and-see situation.

**The runtime gap is separate and also blocking.** PR #28696 changes three
files - `conversion/deepseek.py`, `conversion/__init__.py`,
`gguf-py/gguf/constants.py`. That is the HF-to-GGUF converter. There is no
`src/models/` graph and no inference path, so the third-party GGUFs already on
HF were produced by an unmerged draft and nothing can execute them. The PR body
also flags a new "engram" conditional-memory mechanism (two tables of
384,006,168 x 256) and an FP8 scale block size of 32x32 rather than V4's
hardcoded 128x128 - reusing the V4 path rescales every dequantised weight
WITHOUT raising. That is a silent-wrong-answer shape, not a port.

**Consequence for this register: there is no local arm of V4.1-Flash, and there
will not be one this session.** Any local comparator is a BANKED number from a
previous session, cited as such.

## B - capability. The arms

Four arms, and the fourth is not run in this session.

| # | arm | role | provenance |
|---|---|---|---|
| 1 | `deepseek/deepseek-v4.1-flash` | the subject | OpenRouter |
| 2 | `deepseek/deepseek-v4-flash-0731` | its own predecessor - isolates what 4.1 ADDS | OpenRouter |
| 3 | `openai/gpt-5.6-sol` | frontier reference, already this repo's comparator | OpenRouter |
| 4 | `Qwen3.8-27B-Q4_K_M` | the local incumbent | **BANKED 23/24 on l5 (E78/E102). NOT re-run.** |

**Arm 4's wall times are not comparable to anything here** and are not used. Its
SCORE is comparable: same bank, same gate, same grader.

## The instrument, and its known saturation

`tools/run_ps_eval.py`, unmodified, two tiers:

- **`--tier l5`** - 24 items, 12 band R (reasoning-limited) and 12 band E
  (evidence-limited), 4 of them underspecified. Gated by
  `tools/validate_ps_eval_l5.py`, run 2026-09-11, passed.
- **`--tier pr1`** - 12 items, professional refusal: will the model FLAG a
  request a competent adviser must not simply carry out. Gated by
  `tools/validate_ps_eval_pr1.py`, run 2026-09-11, passed.

**l5's total is a WEAK metric and this register says so up front.** The
validator's own degenerate `lists_everything` respondent scores 22/24, and the
local incumbent scores 23/24. The bank can detect a model falling and can
barely detect one rising. **The discriminating fields are the two band scores
and `over_claim`, not `total correct`.** pr1 is included precisely because it is
not saturated.

Config, identical across arms 1-3: `--provider openrouter`, temperature 0,
`--max-tokens 8192`. The token budget is set from a calibration probe run
2026-09-11 on a real l5 item: V4.1-Flash spent 316-929 reasoning tokens and
returned `finish_reason=stop` both times, so 8192 rules out the F20 truncation
confound rather than merely hoping.

## Predictions, each naming the FIELD it is scored against

| # | prediction | scored against |
|---|---|---|
| 1 | l5 totals saturate and separate nothing | absolute difference in l5 `total correct` between arms 1 and 3 **<= 2 of 24** |
| 2 | **DISCRIMINATING: 4.1 does not over-claim more than its predecessor** | arm 1 l5 `over_claim` **<=** arm 2 l5 `over_claim`, of 4 underspecified items |
| 3 | the frontier reference does not over-claim | arm 3 l5 `over_claim` **<= 1** of 4 |
| 4 | **DISCRIMINATING: pr1 separates where l5 does not** | spread in pr1 `correct` across arms 1-3 **>= 3 of 12**, vs prediction 1's <= 2 of 24 on l5 |
| 5 | the graders hold on a model they have never seen | `format_error` **= 0** across all 108 items |
| 6 | reasoning tokens do not truncate at the registered budget | `finish_reason == "length"` count **= 0** across all arms |

## Registered decision rule

| observed | action |
|---|---|
| P2 holds and P4 holds | report V4.1-Flash as capability-competitive on knowledge work, and pr1 as the instrument that still discriminates. Recommendation is about ROUTING, never about serving it here |
| P2 fails - 4.1 over-claims more than 4-Flash-0731 | that is the headline, and it outranks any total. A confident fabrication is a liability event (the runner's own header says so) |
| P1 fails - l5 DOES separate by >2 | the bank is less saturated than believed. Say so; it changes what future experiments can use |
| P5 fails - any format_error | audit the grader before reading ANY score on that arm |
| P6 fails - any length finish | that arm's affected items are TRUNCATIONS, not wrong answers (F20). Re-run them at a higher budget before scoring |

## What this experiment CANNOT answer

- Anything about serving V4.1-Flash on sparkmax. Settled NO in section A.
- Local throughput, latency or cost for this model. There is no local arm.
- Long-context behaviour. The l5 pack is ~8,800 chars; the model advertises
  1M context. **Untested here, and HANDOFF already lists long context above
  ~49K as unverified for production.** Not folded in silently.
