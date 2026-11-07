# File: closed-record.md
# Purpose: Results for closed-record professional reasoning - three local models against a
#          ten-matter sealed-key corpus, plus the instrument defects the work surfaced.
# Project: sparkbench | Date: 2026-08-12
#
# Overview: Full-corpus run of the closed-record experiment (spec:
# docs/plans/2026-08-12-closed-record-reasoning-experiment.md). Ten professional matters across
# four domains, 50 machine-checkable propositions, three deployment-realistic local models,
# temperature 0, -np 1 -c 32768, max_tokens 6000. Headline: the local fleet scores 66-84 per cent
# on work with a determinate answer, where the same class of box plateaus at 3.0-3.4 out of 5 on
# open-ended drafting (F34). Second finding, and the one most likely to travel: the WORDING of the
# answer-format instruction moved scores by up to 3 points in 10 with the model unchanged.
# Pre-registration: results/closed-record-prereg.md, committed before the first model loaded.

## Results - full corpus

| Model | Score | Answer tokens |
|---|---|---|
| Qwen3-30B-A3B-Instruct-2507-Q4_K_M | **42/50 (84%)** | 8,587 |
| GLM-4.7-Flash-Q4_K_M | **38/50 (76%)*** | 27,080 |
| Mistral-Small-3.1-24B-Q4_K_M | **33/50 (66%)** | 5,812 |

\* **Lower bound.** One of GLM's thirty answers (m09) burned the full 6,000-token ceiling, never
reached its final-answer block, and scored 0/5. Its true score is somewhere in 38-43.

29 of 30 answers supplied the required final-answer block; 29 of 30 stopped naturally.

### Per matter, all three models

| Matter | Domain | Total | Spread |
|---|---|---|---|
| m08-revenue-recognition | accountancy | 15/15 | 5, 5, 5 |
| m01-scope-variation | prof services | 14/15 | 5, 5, 4 |
| m04-notice-pilon | employment | 14/15 | 4, 5, 5 |
| m02-fee-termination | prof services | 13/15 | 3, 5, 5 |
| m10-receivables-provision | accountancy | 12/15 | 2, 5, 5 |
| m05-redundancy-formula | employment | 11/15 | 4, 3, 4 |
| m06-erasure-retention | data protection | 10/15 | 3, 3, 4 |
| m03-rate-increase | prof services | 9/15 | 0, 5, 4 |
| m09-capitalisation-split | accountancy | 8/15 | 3, 5, 0 |
| m07-breach-notification | data protection | 7/15 | 4, 1, 2 |

**The instrument now has visible headroom.** No model is at the ceiling, the three separate by 9
points, and nine of the ten matters discriminate. That was the pilot's open question and it is
answered.

**m08 is too easy** - 15/15, the only matter that separates nothing. It should be replaced or
hardened before the corpus is used again.

**m07 is the hardest at 7/15**, and it is the one built most deliberately around the
conflicting-rules design: a 24-hour contractual notification period and a 72-hour statutory one,
running on clocks that start at different times. Every model applied the right rules and still
mis-set at least one deadline. Qwen, the overall leader, scored 1/5 on it.

## What this does and does not show

On this task shape, three deployment-realistic local models were correct on 66 to 84 per cent of
checkable propositions across authorisation cut-offs, part-rate calculations, statutory-versus-
contractual precedence, retention obligations, day-count and hour-count deadlines, revenue
recognition, capitalisation splits, and provisioning.

That contrasts with what this repo measured on OPEN-ENDED drafting: local plateaus at 3.0-3.4 out
of 5 usability against a frontier model's 4.37, with four training-free levers failing to move it
(F34, F35) and the fine-tune moving voice rather than send-readiness (F37v2). **Task shape looks
like the dominant variable.**

It does **not** show parity with a frontier model - no frontier arm has run. And the matters and
keys are ours, so they carry our judgement about what the right answer is.

## Prediction resolutions

Against `results/closed-record-prereg.md`, which covered the 2-matter pilot. Resolved there on
v3 and re-checked on the full corpus.

- **P1 (the keys discriminate): HOLDS, and more strongly at ten matters.** 42 / 38 / 33 across
  three model families, with different propositions missed by each.
- **P2 (m01 easier than m02): HOLDS** - 14/15 against 13/15, but one proposition of difference is
  not a result.
- **P3 (element 2 of m02 is the most-missed): MISS.** Every model held "submitted is not
  accepted". Across the full corpus the pattern generalises: models are good at the rule
  distinctions and worse at the arithmetic and date work that follows them.
- **P4 (at least one model reproduces a trap value): HOLDS.** Mistral gave EUR 11,880 and EUR 165
  on m03 - the invoiced total and the notified rate - scoring 0/5 by applying a rate increase the
  Special Conditions excluded. GLM reproduced m01's EUR 3,540 travel double-count, the same trap
  Mistral produced in the pilot, so that failure mode is now confirmed across two model families
  and two separate runs.
- **P5 (reasoning does not help): MISS, and the cost is stark.** GLM-4.7-Flash placed second at
  76 per cent while emitting **27,080 tokens against Qwen's 8,587** - 3.2x the output for 4 fewer
  points. Reasoning did not win here and was not cheap.
- **P6 (no answer is ceiling-bound): FALSE**, on both the pilot and the full corpus.

## F20, for the fourth time

GLM-4.7-Flash's m09 answer consumed all 6,000 tokens, never reached its final-answer block, and
scored 0/5. At `max_tokens` 2,000 in the pilot the same model scored 0/10 on two matters for the
same reason, and recovered fully at 6,000.

A reasoning model's verdict flips on the output budget, and a budget set by watching instruct
models measures the budget rather than the model. Per-answer delivery status is what keeps this
visible: the 0/5 is flagged as a lower bound rather than published as a capability result. **The
corpus needs a higher ceiling for reasoning arms - 6,000 is not enough for GLM on every matter.**

## The answer-format instruction moved scores by up to 3 points in 10

Measured on the 2-matter pilot; same models, same temperature, only the sentence describing how
to present the answer changed.

| Model | v1: no recap required | v2: "one short line per item and nothing else" | v3: full recap alongside working |
|---|---|---|---|
| Qwen3-30B-A3B | 10/10 | 8/10 | 10/10 |
| GLM-4.7-Flash | 10/10 | 7/10 | 9/10 |
| Mistral-Small-24B | 7/10 (6 corrected) | 7/10 | 8/10 |

**The v2 dip is the instruction, not the scorer.** Tested rather than assumed: re-scoring the v2
answers with v1's whole-answer matching gives 7/8/8 - within one point of the v2 figures - so
restricting scoring to the stated answer explains almost none of the drop. What explains it is
that models obeyed "one short line per item and nothing else" by omitting figures they had
correctly computed. Qwen's m02 answer fell from 1,337 tokens to 519 and lost the total
outstanding.

This is F39's rule reaching the prompt: **a benchmark measures a config, and the answer-format
instruction is part of the config.** Any published closed-record score has to state how the answer
was asked for, or it is not comparable - the same lesson F20 records for `max_tokens` and E11 for
WER normalisation, now on its fourth distinct mechanism. The full corpus uses v3 wording.

## Three defects the instrument found in itself

Each was found before it could corrupt a published number, and each is the reason the next one
was caught.

1. **The scorer over-credited.** In the pilot it matched key values anywhere in the answer, so
   Mistral's m01 element 4 scored a hit because "EUR 1,680" appeared in its working while the
   figure it gave was EUR 1,960. That is the same defect recorded eight days earlier in
   `results/keyed-vs-pairwise.md`, where `glm-4.7-flash` was scored PASS on E10 for numbers
   appearing in reasoning prose with no table. Fixed by requiring a labelled `## Final answer`
   section and matching only within it, with the fallback recorded rather than silent.
2. **The trap list was incomplete.** Mistral's EUR 3,540 double-counts travel; the key anticipated
   travel billed at the full rate but not travel billed twice. Added - and GLM then reproduced it
   on the full corpus, confirming it across model families.
3. **A key accepted a surface form that was a substring of its own trap.** m06 element 4 accepted
   "April 2", which sits inside the trap "3 April 2026" - a model giving the wrong date would have
   scored a hit. Caught by `check_keys.py` before any model ran.

A fourth, smaller correction: the m02 key claimed a clean 360-day interest figure meant a wrong
answer indicated a wrong method. Mistral used the correct method, rounded the daily rate, and
reached EUR 99.90. The claim is corrected and 99.90 is now named as a precision error.

## Corpus

Ten matters, four domains, 50 propositions, 38 traps. Every matter after m02 turns on two supplied
rules that both apply to the same facts and point different ways, with a third that resolves them.

| Domain | Matters |
|---|---|
| Professional services | m01 scope variation, m02 fee termination, m03 rate increase |
| Employment | m04 notice and PILON, m05 redundancy formula |
| Data protection | m06 erasure vs retention, m07 breach notification |
| Accountancy | m08 revenue recognition, m09 capitalisation split, m10 receivables provision |

Each carries at least one distractor present to be ignored. Several encode a second-order trap:
m05's weekly-pay cap belongs to the statutory formula but sits beside the policy one; m09's
"expense the whole amount" fallback is conditional on a split that has in fact been determined;
m10's VAT-relief rule is live in the rules and dead on the facts.

## Serving configuration

| | |
|---|---|
| Server | `llama-server -np 1 -c 32768 --jinja`, own build, port 8100 |
| Sampling | temperature 0, `max_tokens` 6000 |
| Reps | 1. At temperature 0 this measures the harness, not the model |
| Raw | `results/closed-record/full-{label}.json` + `.serverlog` |
| Runner | `tools/run_closed_record.sh` -> `spikes/closed-record/run_matters.py` |
| Scoring | `spikes/closed-record/score_matter.py` against the sealed keys |

The relay's own llama-server was serving on port 8400 throughout. These are small single-request
workloads rather than a throughput bench, so co-residency does not affect a coverage figure - the
wall-clock timings are not clean throughput numbers and must not be quoted as such.

## Hardening m08 did not make it discriminate

m08 scored 15/15 and separated nothing, so it was rebuilt: a mid-year price variation was added,
with rules deciding whether it is a new contract or a continuation, forcing month-by-month
recognition at two rates instead of one multiplication. The old correct answer (22,500) was kept
as a trap, so a model that reads the variation and fails to apply it lands on it.

**It changed nothing.** Re-run at a 12,000-token ceiling, Mistral and Qwen both still scored 5/5
on the hardened matter, and their corpus totals were unchanged at 33/50 and 42/50.

That is a more useful result than a successful hardening. Adding a second conflict made the
matter harder to CONSTRUCT and not harder to ANSWER: both models identified the price-only
variation as a continuation and split the nine months across two rates without difficulty. The
matters that actually discriminate are the ones carrying two CLOCKS or two BASES - m07 at 7/15,
m09, m03 - not the ones carrying two rules over clean arithmetic. A future corpus should be
built on that distinction rather than on rule count.

**The GLM arm of the 12,000-token re-run did not complete** and is the one open measurement. It
was stopped at the end of the session rather than left as a detached process; its m09 truncation
at 6,000 tokens is therefore still unresolved, and GLM's 38/50 remains a lower bound. Resume with:

```bash
printf 'v4-glm-4.7-flash|/opt/models/staging/GLM-4.7-Flash-Q4_K_M.gguf\n' > /tmp/glm.txt
MAXTOK=12000 tools/run_closed_record.sh /tmp/glm.txt
```

At roughly 58 tokens per second against a 12,000-token ceiling it needs about 35 minutes.

## Next

1. **Run the frontier arm.** Until it does, this file supports "the box gets closed-record
   professional reasoning right most of the time", not "as well as a frontier model". Blocked on
   a live credential only: the stored OpenRouter key returns 401 and the runner already accepts
   `--model` and `--api-key-env`.
2. **Finish the GLM 12,000-token arm** (command above) to clear its lower bound.
3. **Build the next matters on two clocks or two bases, not two rules.** Hardening m08 by adding
   a rule conflict did not move it.
4. **Reps remain 1.** Whether three reps at temperature 0 measure anything beyond harness
   determinism is untested.
