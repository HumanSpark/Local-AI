# File: e141-results.md
# Purpose: Results for E141 - escalation gates and a workhorse effort router in front of the 27B, against fixed effort, on L3-hard.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: Scored against results/e141-prereg.md (4a70f91), runner tools/e141_gate.py (3fab544).
# One run, 76 calls, live gateway, 0 void, 2,343 s. All three deployable designs REJECTED; fixed
# `low` is the best setting measured. Per-call evidence results/e141/calls.jsonl, log
# results/e141/run-2026-09-24.log. Registered as F162.

# E141 RESULTS - no cheap decision beats fixed `low` (2026-09-24)

## Per arm

| arm | correct | total wall s | vs L | shipped wrong | band |
|---|---|---|---|---|---|
| M - 27B `medium` (E140 A) | 12 | 894.6 | 1.183 | - | - |
| **L - 27B `low`** | **12** | **756.4** | 1.000 | - | the baseline |
| O - 27B `off` | 9 | 296.6 | 0.392 | - | - |
| W - workhorse | 5 | 67.9 | 0.090 | - | - |
| G-self (self-check gate) | 7 | 235.2 | 0.311 | **5** | **REJECT** |
| G-lp (logprob >= 0.90 gate) | 7 | 215.4 | 0.285 | **5** | **REJECT** |
| G-oracle (bound, not deployable) | 12 | 553.2 | 0.731 | 0 | - |
| R - workhorse effort router | 12 | 906.6 | **1.199** | - | **REJECT** (> 0.95) |

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `L.correct` | 11-12 | 12 | HELD |
| P2 | `L/M wall` | 0.70-0.95 | 0.845 | HELD (F69's L2 ratio was 0.84) |
| P3 | `O.correct` | 6-9 | 9 | HELD |
| P4 | `W.correct` | 5 | 5 | HELD |
| P5 | `G-self.shipped_wrong` | >= 2 | 5 | HELD |
| P6 | `G-lp.shipped_wrong` | >= 1 | 5 | HELD |
| P7 | `G-oracle/L wall` | 0.55-0.75 | 0.731 | HELD |
| P8 | `R.correct` | 10-12 | 12 | HELD |
| P9 | `R/L wall` | 0.85-1.15 | 1.199 | **FALSIFIED** - worse than predicted |

## The gates: the workhorse cannot tell its right answers from its wrong ones

Of W's 7 wrong answers, the self-check called **5 CONFIDENT** (D2, P1, M1, M2, M3) and escalated
only P2 and Z1. The logprob gate shipped a different 5 (D2, P1, P2, M1, Z1).

**No threshold works, which makes the 0.90 choice irrelevant.** W's minimum ANSWER-line
probability, sorted descending, with grade:

| item | min prob | W grade |
|---|---|---|
| P2 | 0.999998 | **over_applied** |
| D2 | 0.999979 | **premature** |
| V1 | 0.999902 | correct |
| V2 | 0.999644 | correct |
| N1 | 0.999301 | correct |
| D1 | 0.993705 | correct |
| Z1 | 0.993263 | **over_claim** |
| P1 | 0.968461 | **precedence_missed** |
| D3 | 0.937190 | correct |
| M1 | 0.904894 | **wrong** |
| M2 | 0.306120 | wrong |
| M3 | 0.302224 | wrong |

The single most confident answer is wrong. The workhorse's trap errors (stale, premature,
over-applied, precedence, fabrication) are made CONFIDENTLY; only its arithmetic failures (M2, M3)
show as uncertainty. A gate on this signal ships exactly the errors that matter most.

## The router: it never chose `off`, and chose `medium` 7 times

Routes: off 0, low 5, medium 7. Every `medium` pick costs more than fixed `low` for nothing - both
are 12/12 - so the router's own ~4 s call plus its upward bias makes it **1.199x** slower than
simply sending `low` every time. At 906.6 s it is also marginally slower than the production
default `medium` (894.6 s).

The router's picks do not track difficulty either. `off` would have been correct on 9 items; the
three items `off` fails (P1, M1, M2) were routed medium, low and medium.

## What IS worth having

1. **Fixed `low` over `medium` on document questions: 12/12 both, 15.4% less time** (756.4 vs
   894.6 s). This reproduces F69 on the live gateway, and production runs `medium`. `medium` was
   chosen for CODING, where `low` truncates ([[F71]]), so it is a per-route setting, not a global
   swap. A caller asking document questions can send `reasoning_effort: low` today.
2. **The oracle bound says the prize is real but unreachable with these signals:** a perfect gate
   saves 27% against `low`. 27B `off` is 9/12 at a 23.8 s median - a far better first stage than the
   workhorse (5/12) - but the same confident-wrong problem would need checking there before it
   could be trusted.

## Relation to the external reasoning-gate project

Its published result (-54% wall clock) had no quality measure. Here the same role, with quality
measured, is slower than a fixed setting and never picked the cheapest level. That is one bank,
one router model, n=12: it does not show their router fails on their workload. It does show a
router must be scored against the best FIXED setting with correctness beside it, or it measures
nothing.
