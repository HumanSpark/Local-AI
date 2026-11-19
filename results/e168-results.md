<!--
# File: results/e168-results.md
# Purpose: Results of E168 - the ten E167 coding changes with the tests hidden, scored for the two local arms against P1-P5.
# Project: sparkbench | Date: 2026-11-19
#
# Overview: Scores the arms of results/e168-prereg.md (local arms on the A2 bank, sha256 prefix 35efc8ac52e8bbde)
# from the raw task files in results/e168/raw/<arm>/. GS ran 5 of 10 on the earlier A1 bank before the cloud cap
# stopped it, so per A2 its score is partial and P3/P4 are void. Compares each local arm with its own E167 score.
-->

# E168 RESULTS - same ten changes, tests hidden (2026-11-19)

## In plain English

We gave the two best local setups the same ten real changes as last time. This time they did not see the tests.
They got only the developer's own note and a list of the names the change adds. Both passed one task out of ten:
the same task, a mail-triage change. With the tests in view (E167) they had passed five and three. Hiding the
tests cost the better local setup four of its five passes. So most of what the local models can do on big
changes depends on being shown exactly what "done" means. Working that out for themselves is where they fall down.

We cannot say how a frontier model does on this exact test. The cloud model ran out of budget after five tasks, on
an earlier version of the bank, and passed one of those five. The owner chose not to spend more. So this result
says how far the local models drop when the tests are hidden. It does not say how far they trail the frontier.

## Scores

| arm | pass_count | run_count | wall_median_s | total hours | E167 pass_count (tests visible) |
|---|---|---|---|---|---|
| GS (GPT-6.1 Sol, cloud) | 1 (A1 bank, partial) | 5 | - | - | 10 |
| H (Flash-Next, Halogen) | **1** | 10 | 950 | 4.05 | 5 |
| OR35 (Ornith-1.5-35B Q8_0) | **1** | 10 | 2,007 | 5.36 | 3 |

| task | H | OR35 | E167 H / OR35 |
|---|---|---|---|
| clearmail-01d445d75 | fail | fail (context overflow) | fail / fail |
| clearmail-3d41463d0 | fail (275/276 tests) | fail | pass / pass |
| clearmail-7fe0a79c1 | **pass** | **pass** | pass / pass |
| another GPU job-390973aee | fail (collection) | fail (context overflow) | fail / fail |
| another GPU job-5ca87050b | fail (collection) | fail (collection) | fail / fail |
| sparkforge-22dee74e9 | fail (105/111) | fail | pass / fail |
| sparkforge-625dcc2f8 | fail (collection) | fail (context overflow) | fail / fail |
| sparkforge-66de8e1d0 | fail (100/106, model-error) | fail (context overflow) | pass / fail |
| workstation-dotfiles-a0d0e6f0d | fail | fail | fail / fail |
| workstation-dotfiles-ffaf96580 | fail | fail | pass / pass |

Stop reasons:
- **H:** 8 runs ended `model-done`: the model declared the work finished with graded tests still failing. 1 ended
  `model-error` and 1 `unproductive`.
- **OR35:** 6 runs ended `model-done` and 4 ended `model-error`. All 4 errors were llama.cpp refusing a prompt over
  the 131,072-token context, the same failure as E167 (3 there).
- **Both:** both another GPU job tasks failed at test collection. The hidden tests import a module or name that the
  model never created.

## Predictions

| # | prediction | field values | verdict |
|---|---|---|---|
| P1 | GS.pass_count <= 8 | 1 (run_count 5, A1 bank) | held - **partial** (A2) |
| P2 | GS.pass_count >= 4 | 1 (run_count 5, A1 bank) | **FALSIFIED - partial** (A2; 2 of its 4 failures were partly bank defects, removed in A2) |
| P3 | E167 - E168 per local >= 10 - GS | no comparable GS score | VOID (A2) |
| P4 | max(H, OR35) < GS | no comparable GS score | VOID (A2) |
| P5 | \|H - OR35\| <= 2 | \|1 - 1\| = 0 | held |

## What it means

- **The finding is the within-arm drop**, which the prereg called a within-task comparison:
  - H fell from 5 to 1. Three of the four tasks it lost were near misses: 275 of 276, 105 of 111 and 100 of 106
    graded tests passing.
  - OR35 fell from 3 to 1.
  - With ten tasks and one sample each, a 1-2 task difference is noise. A 4-task drop on the same tasks is not.
- **P5 holds trivially.** Both arms scored the floor, so the two are level only because neither solved anything
  but the easiest task. H is still 2.1x faster (median 950 s against 2,007 s).
- **OR35's 131,072-token window is now the most common way it stops** (4 of 10). As in E167, a larger `-c` would
  turn those runs into scored attempts. That is a configuration test, not a capability one.
- **For the "slow but very smart" goal:** neither local setup works out an unstated specification on changes of
  this size. Both stop on their own well inside the hour. Giving them more time would not help, because they are
  not running out of time.
- **Limits.** One sample per task at non-zero temperature. The A2 rule (drop tests that grade exact wording, mock
  calls or source text) was written after seeing GS's failures, and it was applied to all ten tasks before any
  local run. GS's partial score comes from the A1 bank and is not comparable.

## Provenance

- **Bank:** `results/e168/bank.jsonl`, A2, sha256 prefix `35efc8ac52e8bbde`, gold 10/10
  (`results/e168/gold-A2.log`). Harness 2026-11-18.1, podman isolation.
- **Runner:** both local arms ran from the frozen runner copy `var/e167-frozen/run_e154_arms.sh` in one relay idle
  window, 2026-11-18 20:13Z to 2026-11-19 05:39Z. At 05:39:39Z the relay was restored, verified by the production
  probe (`results/e168/raw/window.log`).
- **Raw task files:** `results/e168/raw/{H,OR35}/*.json`, stripped by `tools/strip_task_transcripts.py`. The full
  transcripts are kept on disk in gitignored `results/e168/transcripts/`, with sha256 in each record.
