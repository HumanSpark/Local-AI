# File: e140-results.md
# Purpose: Results for E140 - the workhorse-draft -> 27B-review cascade against the 27B alone on L3-hard.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: Scored against results/e140-prereg.md (registration 9b88dbd, amendment 1 fca54a1).
# One run, 60 calls, live gateway, 2026-09-24. Verdict REJECT (speed): the review is perfectly
# safe and slower than solving from scratch. Per-call evidence: results/e140/calls.jsonl; run log
# results/e140/run-2026-09-24.log. Registered as F161.

# E140 RESULTS - the cascade is safe and slower (2026-09-24)

**Verdict: REJECT (speed).** `C.total_wall_s / A.total_wall_s` = **1.299** against the 0.95
rejection line. The review stage never anchored and never broke a correct draft, so the
counter-hypothesis the experiment was built around is falsified in the good direction, and
the premise the cascade rests on is falsified in the bad one.

## Run

Build `daef7b687` (gateway, as served), `local_fast` = Qwen3-30B-A3B-Instruct-2507,
`local_smart` = Qwen3.8-27B Q4_K_M at `reasoning_effort: medium`. 60 of 60 calls valid on the
first attempt: **0 void, 0 overlap, 0 truncated, 0 format_error**. 4,047 s end to end. 35 slot
polls failed across the run (of roughly 4,000); every call still had samples, so none was void
under amendment 1 item 5.

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `A.correct` | 11-12 | **12** | HELD |
| P2 | `B.correct` | 4-6 | **5** | HELD (E41: 5) |
| P3 | `C.correct` | 10-12 | **12** | HELD |
| P4 | `C.caught` | >= 0.70 | **7/7** | HELD |
| P5 | `C.total_wall_s / A.total_wall_s` | 0.60-0.95 | **1.299** | **FALSIFIED** - slower, not faster |
| P6 | `D.anchored` | 1-3 | **0** | **FALSIFIED** - no anchoring at all |
| P7 | `D.correct` | 8-11 | **12** | **FALSIFIED** - follows from P6 |
| P8 | `E.overcorrected` | 0 | **0** | HELD |
| P9 | `median(D.ctok) > median(E.ctok)` | TRUE | 568 > 513.5 | HELD |
| P10 | `E.total_wall_s / A.total_wall_s` | 0.40-0.85 | **1.093** | **FALSIFIED** - confirming a correct draft costs more than solving |

Decision bands: ADOPT needs ratio <= 0.80 (1.299, fails); REJECT (anchoring) needs `D.anchored`
>= 3 (0, clear); **REJECT (speed) fires at > 0.95.**

## Per arm

| arm | correct | total wall s | completion tokens | median reasoning chars |
|---|---|---|---|---|
| A 27B alone | 12 | 894.6 | 6,631 | 1,484 |
| B workhorse alone | 5 | 64.6 | 276 | 0 |
| C draft -> review (incl. B) | 12 | 1,162.2 | 8,722 | 1,995 |
| D planted flaw -> review | 12 | 1,011.2 | 7,618 | 1,556 |
| E planted correct -> review | 12 | 978.1 | 7,251 | 1,446 |

Per item, C (including B's draft) beat A on **1 of 12** items; E beat A on **4 of 12**. The
largest penalties are where the draft was wrong: Z1 (B fabricated a VAT answer) 52.8 s alone
against 126.2 s through the cascade, P1 113.3 s against 132.1 s. Full table: `score` output
plus `calls.jsonl`.

## Why P5 failed: the reviewer does not read, it re-solves

The registered mechanism was "the 27B's expense is GENERATING; with a draft it can mostly read
and emit only corrections." On this bank that is false for two reasons visible in the tokens:

1. **The answer is two lines.** A's median completion is 544 tokens, almost all of it
   reasoning; the emitted answer is ~20 tokens. There is no answer generation for a draft to
   save - only reasoning, and the reviewer keeps doing it.
2. **The reviewer re-derives, then reconciles.** C's median reasoning is 1,995 chars against
   A's 1,484 (+34%); D 1,556; even E, confirming a correct draft, 1,446 - the same as solving
   cold. The 27B treats the draft as a claim to check, and checking a claim on this bank costs
   what finding the answer costs. Where it disagrees (C on B's 7 wrong drafts, D on 12 planted
   ones) it spends more.

**The cascade can only pay where the final ANSWER is long relative to the reasoning** - a
drafted letter, a report section, a code file - so that accepting most of a draft skips real
generation. L3-hard is the opposite shape. That is the testable condition for any second
attempt, and it needs a long-output instrument this repo does not yet have.

## What P6/P7 establish, and its limit

A fluent wrong draft, in the workhorse's own format, carrying the pack's own trap values
(stale, premature, precedence-missed, fabricated), moved the 27B on **0 of 12** items at
`medium`. The one outcome that would have disqualified the design outright did not occur.

Limit: n=12, one run, temperature 0, one reviewer at one effort. "0 of 12" bounds the
anchoring rate below roughly 25% at 95% (rule of three), not at zero. The planted flaws are
the traps this bank already contains; a subtler flaw (a plausible arithmetic slip inside a
correct method) is untested.

## What this does not change

- The routing guide: the 27B from scratch remains the hard-route answer. Nothing to deploy.
- The workhorse's knowledge-work profile: 5/12, the same score as E41 on a new runtime
  and without a prompt cache.
- gpt-oss-120b as reviewer (deferred by the owner): the mechanism above predicts the same
  result for any reasoning reviewer on short-answer items, so that amendment is worth running
  only on a long-output instrument.
