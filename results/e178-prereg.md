<!--
# File: results/e178-prereg.md
# Purpose: Pre-registration for E178 - Anthropic models (Sonnet 5.5, Opus 5.5, Fable 5.2) on the hard coding bank, run as Claude Code subagents.
# Project: sparkbench | Date: 2026-11-25
#
# Overview: Written before any task runs. Fills the frontier page's one Anthropic gap: the hard bank (E167's ten large
# changes, tests visible) was only run with GPT-6.1 Sol in the cloud. Owner, 2026-11-25: run it here with subagents on
# his Claude Code usage, not paid API calls, with all three models available.
-->

# E178 PRE-REGISTRATION - Anthropic models on the hard coding bank, as subagents (2026-11-25)

## In plain English

Production solved 5 of these ten large real changes, GPT-6.1 Sol all 10. We give the same ten tasks, the same task
text and the same grading to three Anthropic models: Sonnet 5.5, Opus 5.5 and Fable 5.2.

## Setup

- Tasks: `var/e167-tasks/` (the E167 bank, sha256 prefix `925b63296a2fd720`), tests visible, one attempt per task.
- Tree: `tools/e178_subagent_bank.py prepare` materialises the base commit as a fresh one-commit repo (the fix is not
  reachable), with the test files and `.graded_tests.sh` written exactly as the harness does.
- Agent: one Claude Code subagent per task (Agent tool, model sonnet / opus / fable), told to work only inside its
  tree. Grading: `tools/e178_subagent_bank.py verify` restores the test files and runs the bank's verify command.
- Grader control (before any arm): on clearmail-7fe0a79c1 an untouched tree fails (rc 4) and the reference fix passes.
- **Declared differences from the harness runs (E167, E176, E177):** the working setup is Claude Code's own tools and
  prompts, not our harness loop; no 3,600 s cut-off is enforced (wall time is recorded from launch to finish); the
  agent's commands and the verify run on the host, not in podman (the repos are the owner's own code). So this
  compares the same tasks and grading under a different scaffold; it is a frontier reference, not a like-for-like arm.

## Predictions (field: pass_count from results/e178/raw/ARM/*.json)

- **P1:** Sonnet 5.5 >= 7/10.
- **P2:** Opus 5.5 >= 8/10.
- **P3:** Fable 5.2 >= 6/10.
- **P4:** every Anthropic arm beats production's 5/10.
