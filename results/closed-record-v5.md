# File: closed-record-v5.md
# Purpose: The v5 run - three local models over all 13 matters at one setting, plus the
#          three new two-clocks/two-bases matters and the determinism measurement.
# Project: sparkbench | Date: 2026-08-14
#
# Overview: Second measurement of the closed-record corpus, extended from 10 matters to 13.
# The new matters (m11, m12, m13) were built to the ten-matter finding that what separates
# models is a second CLOCK or a second BASE, not a second rule over clean arithmetic. Serving
# is unchanged - temperature 0, -np 1 -c 32768, --jinja - at max_tokens 12,000 for every arm.
# Pre-registration and amendment A1: results/closed-record-prereg.md. The ten-matter table in
# results/closed-record.md stands as what was measured at the time and is not superseded.

## Results - 13 matters, 65 propositions

| Model | Score | Answer tokens |
|---|---|---|
| Qwen3-30B-A3B-Instruct-2507-Q4_K_M | **53/65 (82%)** | 11,935 |
| Mistral-Small-3.1-24B-Q4_K_M | **43/65 (66%)** | 7,950 |
| GLM-4.7-Flash-Q4_K_M | **40/65 (62%)** lower bound\* | 58,441 |

\* **Lower bound.** GLM burned the full 12,000-token ceiling on three matters - m08, m11 and
m13 - and in none of the three did it reach its `## Final answer` block, so all three score 0/5
on an answer that was never stated rather than on one that was wrong. Its misses on those
matters are not attributable to the model.

### Per matter, all three models

| Matter | Domain | Total | Mistral, Qwen, GLM |
|---|---|---|---|
| m01-scope-variation | prof services | 13/15 | 4, 5, 4 |
| m02-fee-termination | prof services | 13/15 | 3, 5, 5 |
| m03-rate-increase | prof services | 12/15 | 3, 5, 4 |
| m04-notice-pilon | employment | 14/15 | 4, 5, 5 |
| m05-redundancy-formula | employment | 11/15 | 4, 3, 4 |
| m06-erasure-retention | data protection | 10/15 | 3, 3, 4 |
| m07-breach-notification | data protection | 5/15 | 2, 1, 2 |
| m08-revenue-recognition | accountancy | 10/15 | 5, 5, 0\* |
| m09-capitalisation-split | accountancy | 11/15 | 3, 5, 3 |
| m10-receivables-provision | accountancy | 12/15 | 2, 5, 5 |
| **m11-limitation-clocks** | **employment** | **6/15** | **4, 2, 0\*** |
| **m12-liability-cap-basis** | **prof services** | **12/15** | **4, 4, 4** |
| **m13-interest-two-clocks** | **accountancy** | **7/15** | **2, 5, 0\*** |

\* truncated, not attributable.

## Generation at temperature 0 IS deterministic - an earlier claim in this session was wrong

GLM's ten shared matters were run twice at max_tokens 12,000, as `v4` and again inside `v5`.
**All ten answers are byte-identical**, compared as strings rather than by token count or hash.
So a fixed model, prompt and serving config reproduces its output exactly, and per-model numbers
from separate runs at the same setting CAN be compared.

Mid-session this was asserted the other way round, on the evidence that GLM's m08 completed at a
6,000-token ceiling and truncated at 12,000. That inference was wrong: **m08's `matter.md` was
rewritten between those two runs** (the hardening recorded in `results/closed-record.md`), so
the input changed, not just the ceiling. Comparing a before-hardening answer with an
after-hardening one and attributing the difference to `max_tokens` is a like-for-like failure -
two things changed and only one was named. Amendment A1 in the pre-registration carries the same
wrong rationale for re-running all 13 matters; the decision it justified is still the right one,
but for the ordinary reason that one table measured at one setting is easier to read, not
because the numbers were irreproducible.

## The new matters: the theory half worked

**P7 holds on its letter and fails on its spirit for m12.** No new matter scored 15/15, so none
is an m08 repeat. But **m12 returned 4/5 from all three models** - identical coverage, so it
separates nothing on score. It separated only on a trap: Qwen reproduced EUR 600, the service
credit computed on the opening EUR 12,000 monthly charge rather than the EUR 14,000 in force in
the month the failure occurred. Two bases were not enough on their own; what m11 and m13 have
that m12 lacks is that their second base or clock has to be **walked** - a calendar counted, a
day-count applied - rather than selected.

**m11 is the hardest matter in the whole corpus after m07**, at 6/15. On the two arms that
completed it, Qwen missed elements 3, 4 and 5: it got the appeal deadline wrong and therefore
reported the compliance conclusion wrong, which is the reversal the public holiday was placed
there to cause. Mistral got the holiday right and missed only element 5.

**The most-missed proposition in the new set is m11 element 5** - naming rule 4 as what decides
that an internal appeal does not extend the claim deadline - missed by both completed arms.
This is the same shape as m07's element 5, which the ten-matter run also found hard: models
compute the two periods and then do not say which rule governs their interaction.

**The new matters make GLM run away.** It truncated on two of the three at 12,000 tokens, having
truncated on only one of the original ten. It spent 58,441 answer tokens to score below Mistral's
7,950 - roughly 7.3x the tokens for 3 fewer propositions. Whatever the extra reasoning is doing,
on this corpus it is not converging.

## Prediction resolutions

| | Prediction | Outcome |
|---|---|---|
| P7 | No new matter scores 15/15 | **HOLDS**, but m12 scored 4/5 three times and separates nothing on coverage |
| P8 | m13 is the hardest of the three, below 8/15 | **SPLIT** - 7/15 is below 8, but m11 at 6/15 is harder, and harder too on completed arms only (6/10 against 7/10) |
| P9 | More models miss m11 element 3 than element 1 or 2 | **HOLDS** - element 3 missed once, elements 1 and 2 never, across the completed arms |
| P10 | m13 element 4 is the most-missed proposition in the new set | **MISS** - it was missed once; m11 element 5 was missed twice |
| P11 | At least one model reports the m12 cap on the gross total, EUR 254,302.50 | **MISS** - no model used the gross base. The trap that did fire was EUR 600, the credit on the wrong month's rate |
| P12 | Qwen3-30B-A3B still leads | **HOLDS** - 53/65, ahead of Mistral by 10 propositions |

P8 and P10 both predicted m13 would be the hard one because it carries two mechanisms. It was
Qwen's best matter of the thirteen, at 5/5. Stacking mechanisms in one matter did not make it
harder; **splitting a period across a calendar did.**

## What this does and does not show

Unchanged from the ten-matter run: no frontier arm has run, so this supports "the box gets
closed-record professional reasoning right most of the time" and NOT parity. Against F34's
open-ended drafting plateau of 3.0-3.4 out of 5, task shape still looks like the dominant
variable.

Reps remain 1. The determinism measurement above narrows what a rep count above 1 could tell
us: at temperature 0 with a fixed config, repeated reps reproduce the same answer byte for byte,
so reps measure nothing until something in the config varies.

## Next

1. **Run the frontier arm.** Still blocked on a live credential only.
2. **Raise GLM's ceiling or accept it as a finding.** Three of thirteen matters unfinished at
   12,000 tokens is now a result about the model, not a harness artefact - but the ceiling that
   would let it finish has not been found.
3. **Rework or retire m12.** Two bases that are selected rather than walked did not discriminate.
4. **The matters that separate are m07, m11 and m13** - all three carry a period that has to be
   counted across a calendar or a day-count basis.
