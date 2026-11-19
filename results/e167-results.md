<!--
# File: results/e167-results.md
# Purpose: Results of E167 - ten large real coding changes with the tests visible, frontier vs the two best local setups.
# Project: sparkbench | Date: 2026-11-18
#
# Overview: Scores the arms of results/e167-prereg.md (bank sha256 925b63296a2fd720) against P1-P6 from the raw
# task files in results/e167/raw/<arm>/. GS ran first (10/10, gate fired); A1 kept H and OR35 running as a
# "local against a frontier ceiling" reading; NM was deferred (not run).
-->

# E167 RESULTS - harder coding bank, visible tests (2026-11-18)

## In plain English

We gave three setups the same ten real changes from our own projects, each with the project's own tests to pass.
The best cloud model (GPT-6.1 Sol) passed all ten, at about two minutes a task and $1.95 in total. The best local
setup (Qwen3.8 Flash-Next on Halogen) passed five, at about eleven minutes a task. The other local setup (Ornith
35B) passed three, at about half an hour a task, and ran out of working memory on three of the tasks it failed.
On big multi-file changes, the box is now clearly behind a frontier model even when the answer key's tests are
in full view. The gap is in getting it right, not only in speed: letting the local models run longer would not
have closed it, because both stopped on their own and declared the work done, apart from Ornith's three memory
overflows.

## Scores

| arm | pass_count | run_count | wall_median_s | total hours | cost |
|---|---|---|---|---|---|
| GS (GPT-6.1 Sol, cloud) | **10** | 10 | 125 | 0.31 | $1.95 |
| H (Flash-Next, Halogen) | **5** | 10 | 685 | 2.87 | local |
| OR35 (Ornith-1.5-35B Q8_0) | **3** | 10 | 1,925 | 5.54 | local |
| NM (Nemotron) | not run (deferred, A1) | 0 | - | - | - |

| task | GS | H | OR35 |
|---|---|---|---|
| clearmail-3d41463d0 | pass | pass | pass |
| clearmail-7fe0a79c1 | pass | pass | pass |
| clearmail-01d445d75 | pass | fail | fail |
| sparkforge-22dee74e9 | pass | pass | fail |
| sparkforge-66de8e1d0 | pass | pass | fail (context overflow) |
| sparkforge-625dcc2f8 | pass | fail | fail |
| workstation-dotfiles-a0d0e6f0d | pass | fail | fail (context overflow) |
| workstation-dotfiles-ffaf96580 | pass | pass | pass |
| another GPU job-390973aee | pass | fail | fail (context overflow) |
| another GPU job-5ca87050b | pass | fail | fail |

Every H run and 7 of 10 OR35 runs ended with `stop_reason: model-done`: the model declared the work finished
with graded tests still failing, well inside the 3,600 s limit (longest H task 2,648 s). OR35's other three ended
`model-error`: llama.cpp refused the request at 131,127 of 131,072 context tokens (iterations 38-53). Several
failures are collection errors: the test module imports a name the model never created.

## Predictions

| # | prediction | field values | verdict |
|---|---|---|---|
| P1 | GS.pass_count <= 8 | 10 | **FALSIFIED** (gate fired; A1) |
| P2 | GS.pass_count >= 3 | 10 | held |
| P3 | max(H, OR35) >= GS - 2 | 5 vs 8 | **FALSIFIED** |
| P4 | \|H - OR35\| <= 2 | \|5 - 3\| = 2 | held (at the bound) |
| P5 | NM <= max(H, OR35) | not run | VOID (NM deferred, A1) |
| P6 | H.wall_median_s >= 5 x GS.wall_median_s | 685 vs 625 (5.5x) | held |

## What it means

- **P3 is the finding.** On E156 (small issue-style changes) the best local setups scored 9/10, with Sonnet and Opus at
  8/10. On changes of 150-2,400 lines over 3-9 files, with the specification executable and visible,
  the best local setup solves half of what a frontier model solves. The "slow but very smart" goal is not met
  by giving the current local leaders more time: they stop early, not late.
- **H beats OR35 and is 2.8x faster** (median 685 s vs 1,925 s). That supports keeping Flash-Next on Halogen in
  production. P4 holds only at its bound, and a 2-task gap is within the noise stated in the prereg limits.
- **OR35's context ceiling is a config limit, not only a model limit.** 3 of its 7 failures hit the 131,072-token
  window. A larger `-c` would turn those three into scored attempts. It would not guarantee passes: H, with no
  overflow, failed two of the same three tasks.
- **Limits.** One sample per task at non-zero temperature; ten tasks from four repos; kernel 7.0.0-43-generic.
  Visible tests measure building to an executable specification. E168 (hidden tests) measures working out what
  to build.

## Provenance

- Bank `results/e167/bank.jsonl` sha256 prefix `925b63296a2fd720`. Harness 2026-11-18.1, podman isolation.
- Local arms ran from the frozen runner copy `var/e167-frozen/run_e154_arms.sh` (sha256 prefix ae0235a29d562c44)
  in one relay idle window. The relay was restored at 2026-11-18T20:10:39Z, verified by the production probe
  (`results/e167/raw/window.log`).
- Raw task files: `results/e167/raw/{GS,H,OR35}/*.json`. H and OR35 records are stripped by `tools/strip_task_transcripts.py`; the full transcripts and diffs are kept on disk in gitignored `results/e167/transcripts/` with sha256 in each record (secret-gate false positives: a fake URL-credential test string and a local variable named token; the runner stdout `local-run.out` echoes them and is kept there too), as E154 amendment 5.
