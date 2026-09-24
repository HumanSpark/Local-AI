#!/usr/bin/env bash
# File: tools/require_prereg.sh
# Purpose: Refuse to run a bench stage whose pre-registration does not exist yet.
# Project: sparkbench | Date: 2026-09-07
#
# Overview: CLAUDE.md requires predictions in results/experiments.md BEFORE a
# run. That rule was broken three times in one session - E118, E126, E127 - and
# every time by the same mechanism: stages were added to a QUEUE SCRIPT, and
# writing the script felt like the work, so the registration step was skipped.
# Experiments launched by hand were registered; experiments launched by a queue
# were not.
#
# F152's lesson applied to my own process: the defence has to be MECHANICAL
# rather than remembered. A queue stage calls this first and dies if its
# pre-registration is missing, so an unregistered run cannot reach the GPU.
#
# Usage:  require_prereg.sh E128  &&  <the actual run>
set -uo pipefail
EXP="${1:?usage: require_prereg.sh <experiment id, e.g. E128>}"
REG=/home/agent-spark/sparkbench/results/experiments.md

if ! grep -q "^## ${EXP} PRE-REGISTRATION" "$REG"; then
  echo "REFUSING TO RUN ${EXP}: no '## ${EXP} PRE-REGISTRATION' section in"
  echo "${REG}."
  echo "hint: predictions written after seeing results are not predictions."
  echo "Register the experiment, then re-queue it."
  exit 1
fi
echo "pre-registration found for ${EXP}"
