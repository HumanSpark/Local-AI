<!--
# File: results/e178-results.md
# Purpose: Results of E178 - Anthropic models (Sonnet 5.5, Opus 5.5, Fable 5.2) on the hard coding bank as Claude Code subagents.
# Project: sparkbench | Date: 2026-11-25
#
# Overview: Prereg results/e178-prereg.md. Thirty runs (ten tasks x three models), graded by tools/e178_subagent_bank.py
# with the bank's own verify commands. Raw records: results/e178/raw/{sonnet,opus,fable}/TASK.json.
-->

# E178 RESULTS - Anthropic models on the ten large changes (2026-11-25)

## In plain English

All three Anthropic models solved all ten large real changes. Production on this machine solves five of the same
ten. Sonnet 5.5 was the fastest at a median of 3.3 min per change; Opus 5.5 and Fable 5.2 took about 7 min. For
comparison, GPT-6.1 Sol took 2.1 min and production 11.4 min. So on large, multi-step changes the gap is about
quality, not only speed: the frontier models finish every one, the local model half.

One caution sits with that: the Claude runs worked inside Claude Code, with its own tools and instructions, while
production worked in our minimal test loop. The tasks and grading are identical, but part of the gap may be the
working setup rather than the model. That is the first entry in the improvement bank (docs/IMPROVEMENT-BANK.md).

## Results

| Model | Solved | Median time per change | Fastest | Slowest | Median tool calls | Cost |
|---|---|---|---|---|---|---|
| Claude Sonnet 5.5 | **10/10** | 198s (3.3 min) | 46s | 456s | 13.5 | Claude Code subscription |
| Claude Opus 5.5 | **10/10** | 407s (6.8 min) | 230s | 789s | 21 | Claude Code subscription |
| Claude Fable 5.2 | **10/10** | 427s (7.1 min) | 187s | 1,042s | 16.5 | Claude Code subscription |
| GPT-6.1 Sol (E167) | 10/10 | 125s (2.1 min) | | | | USD 1.95 in total |
| Production, Flash-Next on Halogen (E167) | 5/10 | 685s (11.4 min) | | | | local |

Time is from launch to the agent's final message. The ten runs for each model ran at the same time, so their times
include some sharing of this machine (the tests run locally); production's runs were one at a time.

Per task (seconds, all passed):

| Task | Sonnet | Opus | Fable |
|---|---|---|---|
| clearmail-01d445d75 | 46 | 248 | 388 |
| clearmail-3d41463d0 | 96 | 368 | 586 |
| clearmail-7fe0a79c1 | 75 | 482 | 446 |
| another GPU job-390973aee | 145 | 230 | 187 |
| another GPU job-5ca87050b | 327 | 410 | 377 |
| sparkforge-22dee74e9 | 456 | 789 | 1,042 |
| sparkforge-625dcc2f8 | 156 | 288 | 321 |
| sparkforge-66de8e1d0 | 241 | 733 | 698 |
| workstation-dotfiles-a0d0e6f0d | 260 | 404 | 428 |
| workstation-dotfiles-ffaf96580 | 285 | 415 | 426 |

## Predictions

| # | Prediction (field: pass_count) | Result |
|---|---|---|
| P1 | Sonnet 5.5 >= 7/10 | **HELD** (10/10) |
| P2 | Opus 5.5 >= 8/10 | **HELD** (10/10) |
| P3 | Fable 5.2 >= 6/10 | **HELD** (10/10) |
| P4 | every Anthropic model beats production's 5/10 | **HELD** |

## What happened along the way

- Two Opus runs and two Fable runs compared their changes against the untouched code with a temporary `git stash`;
  every stash was restored before grading (checked with `git stash list` on each tree).
- One Opus run left a copy of the original code in `.baseline/` inside its tree; it was deleted before grading so the
  change count is the agent's own work.
- Several agents reported that parts of the projects' wider test suites cannot run on this machine (missing optional
  packages, files under `/mnt/storage`); the graded tests are the bank's, and none of those are among them.
- Agents noted unrequested gaps honestly (for example "nothing calls the new code yet" on the snooze feature); the
  bank grades the tests, not those gaps.

## Limits

One attempt per task. Different working setup from the local runs (declared in the prereg). Host execution, not
podman. Times include concurrency on this machine.

## What is stored

Each run's full code change is saved verbatim as `results/e178/transcripts/ARM/TASK.diff`, with its size and sha256 in
the committed record (`diff_file`, `diff_chars`, `diff_sha256`), and each agent's full conversation as
`TASK.agent.jsonl` beside it. Like the local runs' transcripts, that folder stays on this machine and out of git,
because it quotes the owner's private code.
