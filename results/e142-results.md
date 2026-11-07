# File: e142-results.md
# Purpose: Results for E142 - the 27B at `off` as first stage of an escalate-or-ship gate, against fixed `low`, on L3-hard.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: Scored against results/e142-prereg.md (2a7e85e), runner tools/e142_gate.py. One run, 39
# calls, live gateway, 0 void, 1,365 s. Neither gate shipped a wrong answer, and neither saves
# time. Per-call evidence results/e142/calls.jsonl, score output results/e142/score.txt.
# Registered as F163.

# E142 RESULTS - the 27B can gate itself, but the gate costs what it saves (2026-09-24)

## Per arm (baseline L = E141 arm L: 12/12, 756.4 s)

| arm | correct | total wall s | vs L | shipped wrong | escalated | band |
|---|---|---|---|---|---|---|
| O2 - 27B `off`, logprobs | 9 | 246.7 | 0.326 | - | - | - |
| H-self (self-check gate) | 12 | 851.0 | **1.125** | **0** | 6 | INCONCLUSIVE |
| H-lp (logprob >= 0.90 gate) | 12 | 759.7 | **1.004** | **0** | 9 | INCONCLUSIVE |
| H-oracle (bound) | 12 | 503.2 | 0.665 | 0 | 3 | not deployable |

No arm meets ADOPT (needs <= 0.80 x L = 605.1 s). Both gates are safe and both are no faster than
sending every request at `low`.

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `O2.correct` | 8-10 | 9 | HELD |
| P2 | `O2.total_wall_s` | 250-340 | 246.7 | **FALSIFIED** by 3.3 s (below range) |
| P3 | `H-lp.shipped_wrong` | >= 1 | 0 | **FALSIFIED** |
| P4 | `H-self.shipped_wrong` | >= 1 | 0 | **FALSIFIED** |
| P5 | `H-oracle/L` | 0.50-0.65 | 0.665 | **FALSIFIED** (above range) |
| P6 | `H-lp.escalated` | 1-5 | 9 | **FALSIFIED** |

## What the 27B does that the workhorse did not

O2 got the same three items wrong as E141's arm O (P1 `precedence_missed`, M1, M2) and both gates
caught all three. The self-check answered ESCALATE on P1, M1, M2 and also on D2, P2, M3 (all
correct); it shipped six answers, all correct. The workhorse's self-check shipped 5 wrong (F162).

Logprob: O2's minimum ANSWER-line probability was 0.346 (M1) and 0.362 (M2) on two wrong items,
the two lowest on the bank, and 0.595 on P1. At 0.90 only V1 (0.942), V2 (0.988) and Z1 (0.994)
ship, all correct. P1 sits above D1, D3, P2 and N1 (0.519-0.527, all correct), so a threshold that
catches P1 escalates most of the bank - hence 9 of 12 escalated. The workhorse's most confident
answer was wrong; here the most confident ones are right.

## Why it does not pay

1. **The self-check costs as much as the answer.** 12 checks took 220 s (18.3 s each) - the check
   re-reads the 3.6K-token pack, so it is roughly one more `off` call. O2 alone is 246.7 s;
   O2 + checks is 466.7 s before a single escalation.
2. **An escalation costs ~4x a draft** (39.6-88.6 s at `low` against ~20 s at `off`), and a gate
   that fails toward the 27B escalates 6 to 9 of 12.
3. **The oracle bound is 0.665, not 0.73 as for the workhorse - and still a bound.** The prize
   is a third of the time, and only a gate that is free and never wrong would collect it.

Post-hoc, descriptive only (a threshold chosen after seeing the data is not a result): a logprob
threshold between 0.595 and 0.750 would ship D2, M3, V1, V2, Z1 and escalate 7. At the measured
mean escalation cost (~59 s) that is roughly 246.7 + 7 x 59 = 660 s, ~0.87 x L - still above 0.80.

## Limits

n=12, three wrong items. "Caught all three" is 3 of 3, and the self-check's choice to ESCALATE on
three correct items shows it is not discriminating so much as cautious. One run, one bank, temp 0.
A separating logprob threshold cannot be set from these data without fitting them.
