<!--
# File: results/e164-results.md
# Purpose: Results of E164 - Qwen4 Max (OpenRouter, API-only) against production Flash-Next and the cloud references.
# Project: sparkbench | Date: 2026-11-17
#
# Overview: Scored against results/e164-prereg.md (P1-P10, amendment 1) by tools/score_e164.py, which writes
# results/e164/score.json. Raw suite results results/e164/raw/Q/<suite>.json; every cloud call with its billed cost in
# results/e164/raw/ledger.jsonl. Drafts, grade and verdicts in results/e164/drafting/. Finding F191.
-->

# E164 RESULTS - Qwen4 Max beats production on client drafting but trails both frontier references; its tool-use score is mostly a test defect (2026-11-17)

> **Corrected by E165 (2026-11-17, `results/e165-results.md`, F192):** the test audit fixed the tool-use, L5,
> conversation and writing defects noted below. Qwen4 Max's corrected scores: tool use 36/36, L5 24/24, writing 7/7,
> conversations 11/11 and 20/20, H6 6/6. The drafting result is unchanged. The tables below are the pre-registered originals.

## In plain English

Qwen4 Max is the first model in the family we run in production, and it is only available through the cloud. We gave
it the tests production passed this month and the ten client-drafting jobs we used to compare production with Claude
and GPT. Total cost: $3.44.

On drafting it beat production, but only by a little. A blind judge preferred Qwen4 Max on 4 of the 10 jobs and
production on 2, with 4 undecided. Against Claude Sonnet 5.5 it was level (4 to 5). GPT-6.1 Sol beat it clearly, 7 to 1.
So the new Qwen flagship sits between our local model and the best cloud model, closer to Claude than to GPT.

On the everyday tests it matched production: document questions, refusing what it should refuse, writing, long
conversations and date arithmetic. It also invented nothing in its drafts once every automatic flag was checked by
hand. Its one clearly lower score, on tool use (24 of 36 against 33), is mostly the test's fault. In 8 of the 12 failed
tasks the test asks for a letter to a client who is not in its pretend client database. Qwen4 Max looked the client
up, found nothing, and asked for the name and address, which the test's own instructions tell it to do. Two more
failures are a grading rule that marks a correct booking wrong because the model looked the client up first. We will
fix the test and re-score every model on it.

What it means: nothing changes in production, because Qwen4 Max cannot run on this box. It is a useful marker. When
open Qwen4 models arrive, we now know what their big sibling scores, and a local model that got close to it would beat
production on drafting.

## Arms and run

| arm | model | source | effort |
|---|---|---|---|
| Q | `qwen/qwen4-max` via OpenRouter (provider Alibaba) | this run, 2026-11-17 05:10-07:17Z | provider default |
| KFL / KX | production Flash-Next (Halogen), community + low / stock + xhigh | E160, banked | low / xhigh |
| L, C, G | production at low, Claude Sonnet 5.5, GPT-6.1 Sol | E162, banked | default |

Suites ran through `tools/cloud_proxy.py` (345 calls, 800,492 prompt, 78,935 completion tokens of which 43,845
reasoning; every call ended `stop` or `tool_calls`, none truncated). Amendment 1 (the proxy answers `/tokenize` and
`/props`) was committed at 761f38f before the five affected suites ran. Tool use ran in the first launch; the other
suites in a relaunch of the same script's suite section at 06:38Z, concurrent with the judge (different endpoints).

## Suites (E160's, graded unchanged)

| suite | Q | KFL | KX |
|---|---|---|---|
| hard document Q&A, L5 | 22/24 (adjudicated 23) | 23/24 | 23/24 |
| refuse / comply, pr1 (missed flags) | 12/12 (0) | 12/12 (0) | 12/12 (0) |
| writing to a brief | 6/7 | 6/7 | 7/7 |
| conversation, l4 | 10/11 | 9/11 | 8/11 |
| long conversation, 24K history | 19/20 | 18/20 | 15/20 |
| tool use, tasks passed (leaks) | 24/36 (0) | 33/36 (0) | 33/36 (0) |
| dates with a date tool, H6 | 6/6 | 6/6 | 6/6 |
| kw-eval | not run (prereg) | 24/26 | 26/26 |

- **L5 E07 is a grader false negative.** Q answered "No - the Site B (CO-2) cap is EUR 96,000, not EUR 250,000 ...
  the Framework default applies only where the Call-Off Order is silent." Expected: no. The L5 decline detector fires
  on "silent", so the answer is scored as a refusal. Adjudicated 23/24, level with production. R09 (statutory period)
  is lost by every arm.
- **Writing:** exec_summary dropped one required negative (F-A), raw grader result, not hand-checked.

### Tool use: why 12 tasks failed

| failed tasks | what happened | whose fault |
|---|---|---|
| m2, c2, c2b, c4, c4b, c5, c5b, c11 (8) | Client (O'Connor, Doyle, Hanlon, Reddan, Traynor) is not in the harness's 3-client database. The system prompt says "If you need a client's details, look them up first" and "If a request is missing information you need, ask a brief clarifying question". Q looked up, got "no client record found", and asked for name and address. It usually also stated the right title decision ("normal title, since it's under EUR 5,000"). | test conflict |
| n3 (and likely n2) | `kind: tool` passes only if the called tools EXACTLY equal the expected set. Q called `lookup_client` then `schedule_meeting` correctly ("Kelly case review", next Tuesday 11am, Kelly as attendee) and failed for the extra, instructed lookup. | grader defect |
| n1 | Looked up Byrne, then asked which documents are outstanding instead of sending a general chaser. | arguable caution |
| m4 | Passed 1 of 3 runs. | model, minor |

E163's Loom shortfall (28 vs 33) had the same shape. The suite is being audited and corrected (owner instruction,
2026-11-17); every arm will be re-scored where transcripts allow. Until then, 24/36 is the pre-registered score and
should not be read as a capability gap.

## Client drafting (E162 bank, grok-4.7 blind judge, both orders)

| pair | Q wins | other wins | undecided | net for Q |
|---|---|---|---|---|
| Q vs L (production, low) | 4 | 2 | 4 | **+2** |
| Q vs C (Sonnet 5.5) | 4 | 5 | 1 | -1 |
| Q vs G (GPT-6.1 Sol) | 1 | 7 | 2 | **-6** |

For scale, the same judge in E162: Sonnet over L +3, GPT over L +7, GPT over Sonnet +5.

**Mechanical checks, hand-adjudicated:** every flag on Q's drafts is a false positive. C05: EUR 37k, 623k and 52k are
correctly derived gross-profit figures (1,614 x 38.6% = 623; the fall is 37; Athlone's is 52), as Sonnet's identical
flags were in E162. C06: "8.55am until 2.55pm" is the source's 08:55-14:55 in 12-hour form; "Those documents need to be
sent again" is the resubmit fact the checker missed. C08: the trap regex matched "capped at 8%", not a CPI figure. C09:
"Larchmont ties us in for 12 months" is the minimum-commitment fact. Adjudicated: 0 invented figures, 0 trap hits, 0
dropped facts. Q's drafts took a median 29 s (cloud; not compared).

## Predictions

| | prediction (field) | result |
|---|---|---|
| P1 | `l5` >= 23 | **FAILED** raw (22); held after adjudicating E07 (grader false negative) |
| P2 | `pr1` = 12, `missed_flag` = 0 | HELD |
| P3 | `writing` >= 6 | HELD (6) |
| P4 | `mt-l4` >= 9, `mt-long` >= 18 | HELD (10, 19) |
| P5 | `tooluse` >= 33, `leaks` = 0 | **FAILED** (24; leaks 0). 8 failures are a test conflict, 1-2 a grader defect |
| P6 | `h6` = 6 | HELD |
| P7 | net Q over L >= +3 | **FAILED** (+2) |
| P8 | net G over Q >= +1 | HELD (+6) |
| P9 | net Q over C >= 0 | **FAILED** (-1, within noise) |
| P10 | total spend <= $8.00 | HELD ($3.44: suites $0.76, drafting $0.07, judge $2.61) |

## Limits

- One judge (grok-4.7). In E162 it agreed with Kimi on 67 of 100 pair-tasks; nets of 1-2 are within noise.
- Q ran at its provider default effort; production at low. Per-item tokens (median 168 vs 374) and wall times are
  reported, not compared.
- kw-eval was not run (no `/tokenize` on OpenRouter, ~$6 of prompt tokens).
- Two harness defects surfaced (L5 decline detector, tool-use exact-set rule and missing clients). They are recorded
  here and go to the test audit; nothing was re-graded inside this experiment.
- Fixed in passing: `run_e162.py judge` crashed tallying a file holding arms outside `--arms` (all 60 calls were
  already saved); it now tallies every arm present. The re-tally made no calls.
