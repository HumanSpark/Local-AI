# File: closed-record-prereg.md
# Purpose: Predictions for the closed-record reasoning pilot, registered before any model ran.
# Project: sparkbench | Date: 2026-08-12
#
# Overview: Pre-registration for the first run of the closed-record matters (E38). Two matters,
# three local models, temperature 0, scored against sealed keys. Predictions are pinned here and
# committed BEFORE the run, per the standing rule; deviations are findings, not embarrassments.
# Spec: docs/plans/2026-08-12-closed-record-reasoning-experiment.md.

## What is being run

| | |
|---|---|
| Matters | `m01-scope-variation`, `m02-fee-termination` (5 propositions each) |
| Models | Mistral-Small-3.1-24B-Q4_K_M, Qwen3-30B-A3B-Instruct-2507-Q4_K_M, GLM-4.7-Flash-Q4_K_M |
| Serving | `llama-server -np 1 -c 32768 --jinja`, temperature 0, `max_tokens` 2000 |
| Scoring | `spikes/closed-record/score_matter.py` against the sealed keys |
| Reps | 1 (temperature 0; a rep count above 1 measures harness determinism and is deferred) |

Model choice follows F34: Mistral-Small-24B is the measured drafting default, Qwen3-30B-A3B is
the throughput workhorse, GLM-4.7-Flash is the reasoning arm. All three are deployment-realistic
for an SME, which is the point - CloseVector's parity result used a 304B MoE.

## Predictions

- **P1 - the keys discriminate.** The three models do NOT all score identically across the two
  matters. This is the pilot's gate: if they do, the propositions are too easy or too hard and
  the corpus needs rewriting before the remaining eight are authored.
- **P2 - m01 is the easier matter.** Mean coverage on m01 exceeds mean coverage on m02. m01 is
  arithmetic with an authorisation cut-off; m02 requires holding "submitted is not accepted"
  across three deliverables while also computing interest on a stated day-count basis.
- **P3 - element 2 of m02 is the most-missed proposition.** Counting deliverable 2b because it
  was delivered is the single distinction that matter is built on.
- **P4 - at least one model reproduces a trap value as its answer**, most likely `12,000` on m02
  (Phase 1 plus two thirds of Phase 2).
- **P5 - reasoning does not help.** GLM-4.7-Flash does not out-score Mistral-Small-24B on total
  coverage, despite emitting more tokens. F35 measured five reasoning models landing on the same
  drafting plateau as instruct models; this tests whether that carries to closed-record work
  where there IS a determinate answer. A GLM win would be a genuine and interesting deviation.
- **P6 - no answer is ceiling-bound.** With `-np 1 -c 32768` and a prompt near 1,200 tokens,
  every answer stops naturally. Any `finish_reason` of `length` is a harness finding, not a
  capability result (F20).

## What would make this pilot fail its own gate

P1 resolving false. Identical scores across three models of different families would mean the
instrument cannot separate anything, and no amount of running it on eight more matters would
fix that.

## Registered

Committed before the first model was loaded. Results: `results/closed-record.md`.


## Extension: m11-m13, registered 2026-08-14 before any model ran

Three matters added on the finding recorded in `results/closed-record.md`: **the matters that
discriminate carry two CLOCKS or two BASES, not two rules over clean arithmetic.** m08 was
hardened by adding a rule conflict and still scored 15/15 across both completed arms, separating
nothing. m07 (7/15), m09 and m03 are the matters that separate, and all three turn on a second
clock or a second base.

| Matter | Domain | Mechanism |
|---|---|---|
| `m11-limitation-clocks` | employment | Two clocks in different UNITS from different start dates - calendar months from the date the employee was told, working days from the date of the letter, across a public holiday |
| `m12-liability-cap-basis` | prof services | Two bases - a 12-month cap base net of expenses and VAT but including unpaid invoices, against a one-month service-credit base straddling a mid-year rate change |
| `m13-interest-two-clocks` | accountancy | Both - one invoice splitting into two parts on clocks with different start dates, on a base narrowed twice (VAT out, credited amount out) |

Corpus becomes **13 matters, 65 propositions**. Serving config, scoring and reps are unchanged
from the section above, so the extension is comparable to the existing arms.

### Predictions

- **P7 - all three new matters discriminate.** No new matter scores 15/15 across the three local
  models. This is the extension's gate: an m08 repeat means the two-clocks/two-bases theory of
  what makes a matter hard is wrong, and the theory - not the matter - is the finding.
- **P8 - m13 is the hardest of the three.** It carries a second clock AND a twice-narrowed base
  in one matter, where m11 and m12 carry one mechanism each. Predicted below 8/15.
- **P9 - the public holiday is the discriminating fact in m11.** More models miss element 3
  (the appeal deadline) than miss element 1 or element 2. It is the only
  proposition requiring a calendar to be walked rather than a period to be added.
- **P10 - element 4 of m13 is the most-missed proposition in the new set.** Running the disputed
  EUR 5,000 from the invoice due date rather than from 30 days after resolution is the error the
  matter is built around, and the wrong start date is stated twice in the facts where the right
  one is stated once.
- **P11 - at least one model reports the m12 cap on the gross invoiced total**, EUR 254,302.50.
  Fact 4 supplies that gross figure precisely because it is the number a reader reaches for.
- **P12 - Qwen3-30B-A3B still leads.** It led the ten-matter corpus at 42/50 and nothing in the
  new mechanisms favours a longer reasoning trace; if GLM-4.7-Flash wins the new set, that is a
  deviation worth its own finding, and it would qualify P5's result rather than overturn it.

### What would make this extension fail its own gate

P7 resolving false. If a matter built deliberately to the two-clocks/two-bases theory still
scores 15/15, the theory does not predict difficulty and the corpus needs a different account of
what separates models.

### Registered

Committed before any model was run against m11-m13. Keys gated by
`spikes/closed-record/check_keys.py` (13/13 pass) and the corpus size asserted at 13 in
`tests/test_closed_record_keys.py`.

### Amendment A1, declared 2026-08-14 BEFORE any model ran against m11-m13

Two changes to the "unchanged from the section above" claim, both forced by measurement rather
than chosen:

1. **`max_tokens` is 12,000, not 2,000, for the m11-m13 runs.** The 2,000 ceiling truncated
   GLM-4.7-Flash twice in the original corpus. At 12,000 its m09 answer completes (2,334 tokens,
   `finish=stop`) but **m08 truncates instead**, having completed at the 6,000 ceiling. Raising
   the ceiling moved the truncation rather than removing it, so the ceiling is set high enough
   that any remaining `finish=length` is a finding about the model and not about the harness.
2. **All 13 matters are re-run for all three models under one setting, labelled `v5-*`.** The
   ten-matter numbers in `results/closed-record.md` were measured at a different ceiling and,
   as the GLM re-run shows, are not reproducible answer-for-answer at temperature 0. Bolting
   three new matters onto them would mix two runs. The `v5` table is therefore self-consistent
   and supersedes nothing - the original table stands as what was measured at the time.

This means P7-P12 are scored against the `v5` run, and the ten-matter portion of `v5` is a
second measurement of the original corpus rather than a repeat of it.

### Amendment A2, recorded 2026-08-14 AFTER the v5 run - A1's rationale was wrong

A1 clause 2 justified re-running all 13 matters on the ground that generation is "not
reproducible answer-for-answer at temperature 0". **That is false and the v5 run disproves it:**
GLM-4.7-Flash's ten shared matters, run twice at max_tokens 12,000, produced **byte-identical
answers 10 times out of 10**.

The observation A1 reasoned from - m08 completing at a 6,000 ceiling and truncating at 12,000 -
had a different cause. **m08's `matter.md` was rewritten between those runs**, so the input
changed as well as the ceiling, and the difference was attributed to the only variable that had
been noticed. Two things changed and one was named.

The decision A1 made stands: one table measured at one setting is the right artefact. The reason
recorded for it did not, and is corrected here rather than edited away. Recorded as an
amendment because a pre-registration that is quietly rewritten after the run stops being one.
