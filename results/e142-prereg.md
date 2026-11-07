# File: e142-prereg.md
# Purpose: Pre-registration for E142 - does the 27B at `off` give a usable confidence signal as the first stage of an escalate-or-ship gate, where the workhorse did not (F162)?
# Project: sparkbench | Date: 2026-09-24
#
# Overview: E141 rejected the workhorse as gate (5 shipped-wrong, most confident answer wrong). The
# 27B at `off` is 9/12 at a 23.8 s median, so a perfect gate on it saves more. This run measures
# whether its own logprobs or a self-check can find its 3 wrong answers. Written before any run.

# E142 PRE-REGISTRATION - 27B `off` as first stage (2026-09-24)

## Question

Can a gate that ships the 27B-`off` answer or escalates to 27B `low` reach 12/12 with ZERO shipped
wrong answers in less total time than fixed `low`? Same bank (L3-hard, 12 items), live gateway, all
E140 amendment 1 conditions (temp 0, max_tokens 8,192, cache_prompt false, /slots overlap watch,
interleaved by item, JSONL resume). No window: the live gateway carries it, as E140/E141.

## Baseline (reused, not re-run)

Fixed `low` from E141: **12/12, 756.4 s** (`results/e141/calls.jsonl`, arm L). Escalation target is
27B `low`, fixed now.

## Arms

| arm | calls | what it is |
|---|---|---|
| **O2** | 27B `off`, `logprobs` on | the draft every gate ships or escalates; a re-run of E141 arm O plus logprobs |
| **H-self** | O2 + 27B `off` self-check -> [27B `low`] | 27B sees pack, question and ITS OWN answer, replies `CONFIDENT` or `ESCALATE` (`max_tokens` 16); no `CONFIDENT` = escalate |
| **H-lp** | O2 -> [27B `low`] | ship if the minimum token probability on the ANSWER line >= **0.90** (E141's threshold, unchanged) |
| **H-oracle** | O2 -> [E141 L call] | ships exactly what O2 got right. Bound, not deployable; composed from measured calls |

Check prompt is E141's `CHECK_TAIL` verbatim. Escalations run LIVE per gate. Time per item = O2 +
check (H-self only) + escalation if taken.

## Metrics

`correct` /12, `total_wall_s`, `shipped_wrong` (O2 answer shipped and not correct), `escalated`.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `O2.correct` | 8-10 | E141 O 9/12 at temp 0 |
| P2 | `O2.total_wall_s` | 250-340 | E141 O 296.6 s |
| P3 | `H-lp.shipped_wrong` | >= 1 | E141: W's trap errors were confident; expect P1 (precedence) or D2 (premature) to repeat |
| P4 | `H-self.shipped_wrong` | >= 1 | a model checking its own answer inherits its blind spot |
| P5 | `H-oracle.total_wall_s / L.total_wall_s` | 0.50-0.65 | 12 O calls + 3 L escalations |
| P6 | `H-lp.escalated` | 1-5 | O2's 3 wrong items are arithmetic and rule-application |

## Decision bands (fixed now)

- **ADOPT (candidate):** `shipped_wrong` = 0 AND `correct` = 12 AND `total_wall_s` <= 0.80 x 756.4 s.
- **REJECT:** `shipped_wrong` >= 1 (zero tolerance, as E141).
- Otherwise INCONCLUSIVE.

## Out of scope

Other thresholds are a descriptive sweep over O2's measured probabilities, not a result. A
long-output bank and the production routing proposal are separate items. n=12: an ADOPT would be a
candidate to re-test on a larger bank, not a deployment.
