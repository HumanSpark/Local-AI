# File: e141-prereg.md
# Purpose: Pre-registration for E141 - can a cheap decision in front of the 27B (escalate-or-ship, or pick the effort) beat a fixed setting on correct answers per second?
# Project: sparkbench | Date: 2026-09-24
#
# Overview: F161 closed the draft-review cascade: the reviewer re-solves, so it cannot save time on
# short answers. The remaining small-model-in-front designs save time by SKIPPING or SHORTENING the
# 27B's work. Two families, one bank (L3-hard, as E140), one live gateway: escalation gates (ship the
# workhorse's answer or escalate to the 27B) and an effort router (the workhorse picks the 27B's
# reasoning_effort per request - the "reasoning-gate" design). Written before any run.

# E141 PRE-REGISTRATION - escalation gates and an effort router vs fixed effort (2026-09-24)

## The question

Does a cheap per-request decision reach the same correct answers in less total time than the best
FIXED setting? Two ways it can:

1. **Escalation gate.** The workhorse answers (~5 s). A cheap check decides SHIP (return it) or
   ESCALATE (ask the 27B). Saving = the 27B calls skipped. Ceiling on this bank: the workhorse is
   right on 5/12 (E140 B).
2. **Effort router.** The workhorse reads the request and picks the 27B's `reasoning_effort` (off /
   low / medium). Saving = shorter reasoning where it is not needed. This is the external
   reasoning-gate project's design (Kev-4B picking effort), with the workhorse in Kev's role
   because it is already resident: no new server, no GPU contention with production.

**The baseline to beat is fixed `low`, not the production `medium`.** [[F69]]: on knowledge work
effort is a routing axis with no middle setting - L2 at `low` 12/12 in 462.6 s against `medium`
12/12 in 552.2 s. A router that only beats `medium` has beaten a setting nobody should use here.

## Arms (12 L3-hard items each, live gateway, E140 amendment 1 conditions)

Every condition of E140 amendment 1 applies unchanged: temperature 0, `max_tokens` 8,192,
`cache_prompt: false`, `/slots` overlap watch voiding calls under traffic, interleaved by item,
JSONL append + resume, banked grader and parser.

| arm | calls per item | what it is |
|---|---|---|
| **M** | - | 27B at `medium`: **E140 arm A reused** (12/12, 894.6 s), not re-run |
| **L** | 27B `low` | fixed-effort baseline |
| **O** | 27B `off` (`enable_thinking: false`) | fixed-effort floor, and the router's third option |
| **W** | workhorse, `logprobs` on | the draft every gate ships or escalates |
| **G-self** | W + workhorse self-check -> [27B `low`] | the workhorse is shown pack, question and ITS OWN answer and replies `CONFIDENT` or `ESCALATE` |
| **G-lp** | W -> [27B `low`] | no extra call: SHIP if the minimum token probability on W's ANSWER line is >= **0.90** |
| **G-oracle** | W -> [27B `low`] | ships exactly the items W got right. Not deployable; the ceiling any gate can reach |
| **R** | workhorse router -> 27B at the chosen effort | router sees the full request (pack + question) and replies `off`, `low` or `medium` |

**Escalation always goes to 27B `low`**, fixed now before L is measured. An escalated item's
27B call is run LIVE per gate (not copied from L), so each gate's time is its own.

**Composed timing:** a gate's time per item = W + check (G-self only) + escalation if taken. R's
time = router call + the 27B call at the chosen effort. G-oracle = W + L's call on the items W got
wrong (composed from measured calls, declared as such; it is a bound, not an arm).

## Prompts (fixed here)

- W, L, O, M: `run_ps_eval.PROMPT_TEMPLATE`, identical to E140.
- **G-self check** (workhorse, `max_tokens` 16): PROMPT_TEMPLATE's pack and question, then
  `=== DRAFT ANSWER ===` + W's answer, then: *"Is the draft answer correct according to the
  engagement pack? Reply with exactly one word: CONFIDENT if you are certain it is correct,
  ESCALATE otherwise."* A reply without `CONFIDENT` is ESCALATE (fail toward the 27B).
- **R router** (workhorse, `max_tokens` 16): the pack and question, then: *"You are routing this
  question to a strong reasoning model. How much reasoning does it need to answer correctly? Reply
  with exactly one word: off (lookup, no reasoning), low (brief reasoning), or medium (careful
  multi-step reasoning)."* An unparseable reply routes to `low` (the baseline, so a broken router
  costs nothing but its own call).

## Metrics

Per arm: `correct` (of 12), `total_wall_s`, and **`shipped_wrong`** for gates: items where the gate
SHIPPED the workhorse's answer and it was not correct. A shipped wrong answer is a confident error
delivered to the user with no 27B ever consulted - the liability this design must not create.
`escalated` (count) for gates; the effort distribution for R.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `L.correct` | 11-12 | E41 12/12 at `low`; F69 |
| P2 | `L.total_wall_s / M.total_wall_s` | 0.70-0.95 | F69 L2: 462.6 / 552.2 = 0.84 |
| P3 | `O.correct` | 6-9 | F69 L2 `off` 8/12 |
| P4 | `W.correct` | 5 | E140 B, same request plus `logprobs` |
| P5 | `G-self.shipped_wrong` | >= 2 | a model checking its own answer inherits its blind spots; Z1 was a confident fabrication |
| P6 | `G-lp.shipped_wrong` | >= 1 | W's wrong answers are fluent in the same two-line format as its right ones |
| P7 | `G-oracle.total_wall_s / L.total_wall_s` | 0.55-0.75 | skip 5 of 12 27B calls, pay 12 cheap W calls |
| P8 | `R.correct` | 10-12 | routing to `off` costs items (P3); the router will sometimes pick it |
| P9 | `R.total_wall_s / L.total_wall_s` | 0.85-1.15 | the router's saving on `off` picks roughly offsets its own call and any `medium` picks |

## Decision bands (fixed now)

- **Gate ADOPT (candidate):** `shipped_wrong` = 0 AND `correct` >= `L.correct` AND `total_wall_s`
  <= 0.80 x `L.total_wall_s`.
- **Gate REJECT:** `shipped_wrong` >= 1. Zero tolerance: on a 12-item bank, one confident wrong
  answer shipped without the 27B is 8% of traffic answered wrong on purpose.
- **Router ADOPT (candidate):** `R.correct` >= `L.correct` AND `R.total_wall_s` <= 0.85 x
  `L.total_wall_s`.
- **Router REJECT:** `R.correct` < `L.correct`, or `R.total_wall_s` > 0.95 x `L.total_wall_s`.
- Otherwise INCONCLUSIVE.

## Stop rules

As E140. Additionally: if the gateway rejects `logprobs` or returns none, G-lp is VOID (recorded,
not substituted) and the rest runs.

## Out of scope

- A separate small model (0.6B-4B) as gate or router: it would need its own server beside the
  live gateway, contending for the GPU. The workhorse plays the role here; a dedicated tiny model
  is a later arm only if this run finds signal.
- Thresholds other than 0.90 for G-lp are REPORTED as a sweep over W's measured probabilities, and
  are descriptive only: a threshold chosen after seeing the data is not a result.
