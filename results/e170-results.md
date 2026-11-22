<!--
# File: e170-results.md
# Purpose: Results of E170 - which local model should run a nightly "propose memory entries" job.
# Project: sparkbench | Date: 2026-11-21
#
# Overview: Scores from tools/run_e170.py grade (results/e170/score.json) for arms F (production Flash-Next), H
# (Hy-Memory-30B-A3B Q8_0) and I (Inkling-2-Mini, our Q8_0 conversion) on the 50-task bank pre-registered in
# results/e170-prereg.md (commit 18eedfb, before any model call). Post-hoc views are labelled as such.
-->

# E170 RESULTS - memory extraction, three local models (2026-11-21)

## In plain English

We gave three local models fifty small memory-keeping jobs: read a conversation and write down what it says about
the person, or update an existing memory from a new conversation. Each job hid traps a memory system must not fall
for: a colleague's details, a "we might move to...", a suggestion the person turned down, a mistake corrected
mid-sentence.

All three were good at the reading job, too good for this test to separate them on accuracy. Inkling-2-Mini made no
mistakes at all, production made one, Hy-Memory made a few. The differences showed elsewhere. Inkling was about six
times slower than production and, on a quarter of the update jobs, thought until it ran out of room and gave no
answer. Hy-Memory was the fastest but stored suggestions the person had said no to, and padded memories with empty
entries.

By the rule written down before the test, the nightly job uses the production model: it was as accurate as the best
and much faster. The community report that Inkling Mini beats production at memory work did not reproduce here on
accuracy, and it lost on speed and reliability. This bank was too easy to show a ceiling, so the accuracy result is
"level", not "production wins".

## Scores (pre-registered fields)

| arm | extract F1 | P / R | trust errors (stale/colleague/hypo/rejected/promoted) | extract valid | update exact | update: no answer | update stale kept | median s/task |
|---|---|---|---|---|---|---|---|---|
| F production Flash-Next (low) | 0.997 | 1.000 / 0.993 | 0 (0/0/0/0/0) | 30/30 | 17/20 | 0 | 2 | 6.45 |
| H Hy-Memory-30B-A3B | 0.987 | 0.980 / 0.993 | 11 (0/0/0/11/0) | 30/30 | 8/20 | 1 (U11, ran to the 16,384 cap) | 0 | 3.04 |
| I Inkling-2-Mini | 1.000 | 1.000 / 1.000 | 0 (0/0/0/0/0) | 30/30 | 15/20 | 5 (U01, U03, U10, U14, U16: all thinking, empty reply) | 0 | 42.21 |

Wall times are indicative only: H and I ran on a sparkbench llama-server beside live production (prereg).

Production's misses, read by hand: X08 dropped a real EUR 1500 budget sitting next to a EUR 950 hypothetical; U04
stored "Fridays would be nice if my diary ever cleared" as the meeting day; U06 and U16 did not apply a day-rate
change.

## Predictions

| | prediction | result |
|---|---|---|
| P1 | at least one arm below 0.95 extract F1 | **FALSIFIED**: lowest is 0.987. The bank does not separate the top. |
| P2 | neither I nor H beats F by 0.05 F1 | HELD: I +0.003, H -0.010 |
| P3 | F has the fewest trust errors | HELD as a tie: F 0, I 0, H 11 |
| P4 | every arm valid JSON on >= 28/30 extract | HELD: 30/30 for all three |
| P5 | F gets the most updates exactly right | HELD: F 17, I 15, H 8 |

## Decision (rule stated in the prereg)

Arms with trust errors no higher than production's (0): F and I. Highest F1: I 1.000, F 0.997, within 0.03, so the
faster arm wins: **F, production Flash-Next (6.45 s against 42.21 s median)**. Both clear the 0.85 floor. The nightly
"propose memory entries" job is built on production.

## Post-hoc views (declared after the runs; not the scored result)

- **Blank placeholders.** H filled keys it did not know with `""` or `null` in most updates. Ignoring blank values,
  H's exact updates rise from 8 to 15 of 20. F stays 17, I stays 15.
- **Rejected suggestions.** All 11 of H's trust errors are rejected suggestions stored with status `suggestion`, none
  as `confirmed`. Milder than a confirmed false fact, but the person said no, so it should not be stored.
- **Inkling on what it answered.** I answered 15 of 20 updates and got all 15 exactly right. Its failure is not
  accuracy but finishing: 5 of 20 updates ran the whole 16,384-token budget (about 14.5 minutes each) in thinking.
  Diagnostic re-ask of U01 (not scored) below.

## Diagnostic: why Inkling ran out of room (U01 re-asked once, not scored)

The re-ask reproduced the failure exactly: 15,894 thinking tokens, empty reply (`results/e170/I-diag-U01.json`, with
the thinking text). The thinking is a **repetition loop over a real ambiguity in our bank**: the key `day_rate_eur`
is never defined. The bank states it as "we pay consultants EUR X a day", and Inkling asks whether that is the
user's own rate or what their company pays outside help, decides, reconsiders, and repeats four paragraphs 28 to 33
times each until the cap. 184 non-empty lines, 40 distinct.

This is a bank defect, and it touches every arm. Six of the 20 updates change or add the day rate (U01, U02, U04, U06,
U10, U16).
- **F:** all three inexact updates are day-rate tasks (U06 and U16 left the old rate in; U04's miss is the
  "Fridays" hypothetical).
- **I:** three of five runaways are day-rate tasks (U01, U10, U16).
- **I's other two runaways (U03, U14):** the day rate sits unchanged in the stored memory there. Whether the same
  question caused them is not confirmed: their thinking was not saved.

What it changes: the update scores partly measure how each model resolves an undefined key, not memory-keeping alone.
The decision does not change, because F and I tie on extraction and the rule's tie-break is speed. Two lessons carry
into the nightly job:
1. Every memory key needs a one-line definition in the prompt.
2. A reasoning model meeting a real ambiguity may loop rather than guess, so the job needs a thinking cap and a
   "could not decide" outcome.

## Context and limits

- The bank is templated and short (about 17 turns), so this measures following memory rules on clear text, not
  reading long or messy real conversations. A harder bank (real-length, noisy captures) is what would separate F and I.
- Inkling-2-Mini ships natively in NVFP4/MXFP8; arm I is our Q8_0 re-quantisation through llama.cpp support merged
  2026-11-20 (`29b52d398`). The GGUF records the 3-pass loop over layers 6-18 as published. Five raw replies were
  read by hand before scoring and were correct and well-formed, so the arm is not void, but a native-precision engine
  could behave differently on the runaway cases.
- Thinking Machines states Inkling 2 Mini trails Qwen3.8-27B on instructions with many constraints (ComplexConstraints
  33.4%). The bank's prompts are rule-heavy. Read after the prereg was frozen; noted, not used.
- GPU evidence for arm I: amdgpu GTT used rose from 34.9 GB to 64.0 GB at load (`results/e170/I-gpu-mem-before.txt`);
  this llama.cpp build no longer logs layer offload at default verbosity.
- Engine: llama.cpp `e412c6f46` (2026-11-21), Vulkan. Production: Halogen, `LOW DEFAULT LIVE` before and after arm F.

## Evidence

`results/e170/score.json` (per-task grades), `results/e170/out-{F,H,I}.json` (raw replies), `results/e170/run-*.log`,
`results/e170/{H,I}.serverlog`, bank `spikes/memory-tasks/bank.json` (seed 170), runner and grader
`tools/run_e170.py`, provenance `manifests/MANIFEST.md` (E170).
