# File: e143-results.md
# Purpose: Results for E143 - the chat-recommended coding models (Flash-Next, 27B, 35B-A3B) and our incumbent Qwen3-Coder through Aider on the three E113 tasks.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: Scored against results/e143-prereg.md (6e74f7e), runner tools/run_e143_window.sh (ecb3029).
# One window 18:29-20:57, 8,831 s, four arms, 36 attempts, 0 void, 0 amdgpu fault lines. No arm is
# distinguished from another on pass count; the arms differ 10x in time and have OPPOSITE task
# profiles. Per-attempt evidence results/raw/e143/<arm>/r{1,2,3}.{json,log}. Registered as F164.

# E143 RESULTS - four models tie on passes, and split the tasks in opposite ways (2026-09-24)

## Per arm (3 tasks x 3 repeats, llama.cpp daef7b6, served solo)

| arm | model | passes | T1 | T2 | T3 | time per repeat | median attempt s | median requests |
|---|---|---|---|---|---|---|---|---|
| D | Qwen3-Coder-30B-A3B (incumbent) | 5/9 | 3/3 | **0/3** | **2/3** | 166 s | 23.4 | 3 |
| A | Qwen3.8-27B | 5/9 | 3/3 | 2/3 | 0/3 | 1,719 s | 440.6 | 1 |
| C | Qwen3.6-35B-A3B | 6/9 | 3/3 | 3/3 | 0/3 | 321 s | 125.1 | 1 |
| B | Qwen3.8-Flash-Next | 6/9 | 3/3 | 3/3 | 0/3 | 707 s | 237.2 | 2 |

Largest pass-count gap between any two arms: 1 of 9. **No model is distinguished** (band: 4 or more).

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `A.passes` | 4-7 | 5 | HELD |
| P2 | `D.passes` | 4-7 | 5 | HELD |
| P3 | `B.passes` | 3-7 | 6 | HELD |
| P4 | `C.passes` | 1-4 | 6 | **FALSIFIED** |
| P5 | `B/A median wall` | 0.6-1.0 | 0.538 | **FALSIFIED** (faster than predicted) |
| P6 | T3 passes <= 1 of 3 in >= 3 of 4 arms | yes | A, C, B at 0/3; D at 2/3 | HELD (3 of 4) |
| P7 | `max - min` of A, B, D passes | <= 3 | 1 | HELD |

## Bands

- **Chat picks CONFIRMED on code** (not distinguished below A and median wall <= A's): **B and C both
  confirmed.** That is a weak statement: A itself is not separated from the incumbent D either.
- **Nothing recommends replacing `local_code`.** D ties the field on passes and is 2.0x to 10.3x
  faster per repeat than the others. The chat's picks are not worse on this bank; they are not shown
  better, and only the 35B comes within 2x of the incumbent's speed.

## The finding the totals hide

Pass counts tie, task profiles do not. **T2** (a new module written against a read-only spec):
the three Qwen3.8/3.6 models pass **8 of 9**, the Coder **0 of 3**. **T3** (bounded change across
two test files): the Coder passes **2 of 3**, the other three **0 of 9**. Equal totals from opposite
strengths. With three tasks this is a pointer for the next bank, not a rule about models.

## Limits

3 tasks, so 3 independent draws per model, each repeated; the repeats measure sampling noise, not
task variety. T3's failures for A, C and B were not diagnosed here: F152 found one such failure was
an Aider application fault, and that has not been checked for these 9. Thinking defaults differ per
model (declared in the prereg). Server-default sampling, not tuned.
