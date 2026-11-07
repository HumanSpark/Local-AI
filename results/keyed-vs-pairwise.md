# File: keyed-vs-pairwise.md
# Purpose: Result of scoring the same five E10 answers by answer key and by blind pairwise
#          judging, and what the disagreement between the two methods measures.
# Project: sparkbench | Date: 2026-08-11
#
# Overview: Task 3 of the benchmark instrumentation uplift. Five stored E10 answers were scored
# against a ground-truth key (8 required elements derived from data/long-log.txt) and judged
# pairwise by Mistral-Small-24B under the Material-Outcome Test rubric, every pairing in both
# label orders. Headline: the two methods disagree on 9 of 10 pairings. Secondary and more
# consequential: every one of the five answers is length-truncated, so the E10 evidence cannot
# support capability claims about these models at all.

## Headline

**Disagreement rate: 9/10 pairings** (1 agree, 9 disagree, 0 excluded as position-dependent).

The judge returned `TIE, FUNCTIONALLY EQUIVALENT` on all 20 calls. Keyed scoring separated the
same five answers into 7/8, 6/8, 6/8, 0/8, 0/8. The single agreement is the pairing where both
answers scored 0/8 - the two methods agree there because both are floored, not because they
concur.

The judge called a **table-less answer functionally equivalent to an eight-row table**. That is
the finding: on this task, blind pairwise judging carried close to zero discriminating power,
while an answer key separated the field immediately.

## What was run

| | |
|---|---|
| Answers | 5 stored E10 responses, `results/eval-pilot/e10-*.json` |
| Task | enumerate every model with a depth-0 `tg128` in a 12k-word log |
| Key | `spikes/eval-pilot/keys/e10-full-table.yaml` - 8 required elements, 3 traps, 5 wrong-depth values |
| Judge | Mistral-Small-3.1-24B-Q4_K_M, temperature 0, deliberately NOT one of the five contestants |
| Rubric | `spikes/eval-pilot/rubrics/material-outcome-test.md` (verbatim third-party) |
| Calls | 10 pairings x 2 label orders = 20, ~21k-token prompts, 19 min wall |
| Raw | `results/eval-pilot/pairwise/e10-pairwise-run2.json` |

## Keyed scores

| Model | Coverage | Table rows | Contradictions |
|---|---|---|---|
| qwen3-30b-a3b | 7/8 | 8 | 253.5 |
| qwen3-4b | 6/8 | 9 | 253.5, 92.37 |
| qwen3-coder-30b | 6/8 | 7 | 253.5 |
| glm-4.7-flash | 0/8 | 0 | none |
| gpt-oss-20b | 0/8 | 0 | none |

Every coverage figure above is a **lower bound** - see the truncation finding below.

Four of the five reproduced `253.5` as table data. It is a Step 4a smoke-test figure phrased
"generation 253.5 t/s", measured with `llama-cli`, not a `llama-bench tg128` row. Reproducing it
asserts a benchmark value the log does not contain.

## The finding that outranks the headline: every answer is truncated

All five answers end mid-token. `qwen3-30b-a3b`'s final row stops at
`| GLM-4.7-Flash-MXFP4_MOE.gguf | 62` - cut off before `62.94`, which is exactly the one element
it was scored as missing. Its "7/8" is a harness artefact, not a model result.

`glm-4.7-flash` and `gpt-oss-20b` both consumed exactly 1200 completion tokens - the suite's
`max_tokens` ceiling - and were still inside a `Thinking:` block when cut. Neither ever produced
a table.

**Consequence: the E10 experiment does not measure what `results/eval-pilot.md` reports it as
measuring.** No capability claim about these five models should rest on this substrate without a
re-run. The comparison above remains valid as a comparison OF THE TWO SCORING METHODS on
identical inputs, which is what task 3 set out to measure.

### CORRECTED 2026-08-12: two ceilings, not one, and the fix was not a bigger budget

This section originally called for "a re-run at a higher `max_tokens`". That would have fixed two
of the five answers and left three truncated in exactly the same place. From the serverlogs:

| model | prompt tok | headroom in slot | decoded | stopped by |
|---|---|---|---|---|
| qwen3-30b-a3b | 16,140 | 244 | 244 | **context window** |
| qwen3-4b | 16,140 | 244 | 244 | **context window** |
| qwen3-coder-30b | 16,140 | 244 | 244 | **context window** |
| glm-4.7-flash | 14,929 | 1,455 | 1,200 | max_tokens |
| gpt-oss-20b | 14,877 | 1,507 | 1,200 | max_tokens |

The three Qwen models share a tokenizer and filled 98.5% of the slot; the server logged
`truncated = 1` for each. The slot was 16,384 rather than 32,768 because `tools/run_eval_pilot.sh`
served `-np 2` and llama-server divides `-c` by the slot count.

Re-running qwen3-30b-a3b at `NP=1` (`results/eval-pilot/ctxfix-ctxcheck.*`) gives
`n_ctx_slot = 32768`, the same 16,140-token prompt, **1,080 decoded tokens**, `truncated = 0`,
and a natural stop under the unchanged 1200-token `max_tokens`. Keyed coverage goes **7/8 (lower
bound) to 8/8**. The 253.5 trap contradiction survives the fix, so that is a real faithfulness
result rather than an artefact.

Two consequences for what this file claims. The keyed-vs-pairwise disagreement measurement is
unaffected - it compared two rulers on identical inputs, whatever produced those inputs. But the
"E10 cannot support capability claims" conclusion was right for the wrong reason, and the
remedy it named would not have worked.

`score_keyed.py` now flags this rather than letting it pass silently: `truncated` and
`coverage_is_lower_bound` travel with every score, and `compare_methods.py` prints a loud banner
when every answer in a set is truncated.

## Two grader defects this surfaced

1. **The original assertion checked 4 of 8 values.** `e10-generation.yaml` asserts
   `53.44 && 92.83 && 24.39 && 23.90`. The log contains eight depth-0 `tg128` values. A pass
   never established the table was complete.
2. **`glm-4.7-flash` was recorded as PASS with no table at all.** The assertion is
   `output.includes('53.44') && ...`, satisfied by those numbers appearing in reasoning prose.
   Same family as the `8,388.60` grader artefact already recorded in `results/eval-pilot.md`.

## Judge behaviour, measured

Run 1 (`results/eval-pilot/pairwise/e10-pairwise-run1-SUPERSEDED-prompt-hijack.json`) is kept
because its failure modes are the result:

| Judge behaviour, run 1 | Count |
|---|---|
| Clean verdict at the head of the report | 10 |
| Walked the rubric section by section, verdict at line 18-61 | 4 |
| **Answered the E10 question instead of judging it** | 6 |

The 6 hijacked calls were exactly the pairings where both answers were table-less prose. Cause:
our "question" is a 12k-word log ending in an imperative ("produce a table"), so the nearest
instruction beat a rubric 21k tokens earlier. The reviewed benchmark never hit this because its
matters are short prose.

Fix (a declared deviation from the reference harness, `judge_pairwise.py:CLOSING_INSTRUCTION`):
label the question as reference material and put the judging instruction AFTER both answers.
Run 2: 20/20 parsed, 0 hijacked.

**The rubric was delivered intact in both runs** - `load_rubric()` strips only our provenance
header, and that is asserted by test. Run 1's format failures are judge capability, not delivery.

## Rubric format compliance (task 4's acceptance check)

Measured across all 20 run-2 reports:

| Mandated section | Present |
|---|---|
| Verdict, first line, standing alone | 20/20 |
| Basis | 20/20 |
| Failed candidates | 20/20 |
| Hard stop | 19/20 |
| Neutralization log | 15/20 - conforming; the rubric says omit it when nothing was rejected |
| Seven-element proof | 2/20 - conforming; winner verdicts only, and all 20 were ties |

**Banned hedging phrases across all 20 reports: 0.** The rubric bans "could create risk",
"might affect strategy", "less complete" and "raises concerns" as substitutes for proof. None
appeared. That ban is the main reason the rubric was worth taking, and it held.

So the rubric is delivered intact and followed. Its weakness on this task is not compliance -
it is that a tie-heavy rubric applied to near-identical enumeration answers produces ties. Note
also that one Basis reads "Both answers correctly identify the same set of models" for a pairing
where one answer contained no table at all: the judge followed the format while getting the
underlying fact wrong, which is exactly the failure an answer key catches and a judge does not.

## Position bias: controlled, but the control could not fire

Both label orders were run for every pairing. Zero pairings were position-dependent. This is
**not** evidence that the judge is position-robust: a uniform-tie outcome cannot exhibit position
dependence, so the control had nothing to detect. It becomes informative only on a run that
produces decisive verdicts.

## What this changes

- Keyed scoring earns its place. It separated a field that pairwise judging could not, scores a
  single model with no opponent, and caught two grader defects and a whole-experiment truncation
  that binary assertions and an LLM judge both walked past.
- Pairwise judging is not retired on one task. A tie-heavy rubric applied to near-identical
  enumeration answers is close to its worst case; the reviewed benchmark's own tie rate was 86%.
  The honest statement is that on THIS task it discriminated nothing, measured over 10 pairings.
- The Material-Outcome rubric's format compliance is judge-dependent. Mistral-Small-24B complied
  about half the time before the prompt fix and fully after it. A weaker judge should be assumed
  worse, and the `unparsed` count is the metric to watch.

## Reproduce

```bash
cd spikes/eval-pilot
python3 compare_methods.py --pairwise ../../results/eval-pilot/pairwise/e10-pairwise-run2.json
```

Re-judging needs a llama-server; `judge_pairwise.py --reparse <file>` re-derives verdicts from
stored raw output with no model calls.

## Verification record

- 41 tests across `test_keyed_scoring.py`, `test_compare_methods.py`, `test_judge_pairwise.py`,
  `test_serve_bench_instrumentation.py`; ruff clean.
- Ground truth derived by reading every `tg128` line in `data/long-log.txt` in context and
  attributing it to the nearest preceding step heading; line numbers recorded in the key.
- Truncation established from the answer text itself (ends mid-token), not from `finishReason` -
  that field reads `length` for all five including the three that produced complete tables, and
  is inconsistent with their 244-token completion counts, so it was not relied on.
- The zero-coverage answers were re-read in full to confirm the scorer was not producing a false
  negative: `gpt-oss-20b` contains zero `|` characters.

## Not verified

- Whether a stronger judge (or a non-tie-heavy rubric) would discriminate on this task.
- Whether the disagreement rate holds on tasks with genuinely divergent answers - enumeration
  from a shared source is a task where near-identical outputs are expected.
- Model capability on E10 at all. Every answer was truncated; that needs a re-run.
