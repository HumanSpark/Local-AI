#!/usr/bin/env bash
# File: tools/run_e162.sh
# Purpose: Run all of E162 unattended in the prereg's order: local drafts against production, cloud drafts alongside, grade, judges.
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Asserts the production setting (halogen_effort_check LOW DEFAULT LIVE) before L and after X, drafts L, M, X
# one request at a time through model-guard while C and G draft on OpenRouter in the background, then grades and runs both
# judges in parallel. Every step is resumable (tools/run_e162.py skips finished work), so a re-run continues. Log:
# results/e162/run.log. Usage: setsid bash tools/run_e162.sh > /dev/null 2>&1 &
set -uo pipefail
ROOT=/home/bench/sparkbench
OUT=$ROOT/results/e162
LOG=$OUT/run.log
PY="python3 $ROOT/tools/run_e162.py"
mkdir -p "$OUT"
stamp() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
check() {
  python3 /opt/sparkrouter/ops/halogen_effort_check.py >> "$LOG" 2>&1
  local rc=$?
  stamp "effort check ($1) rc=$rc"
  return $rc
}
stamp "=== E162 start; kernel $(uname -r); halogen image $(grep -o 'sha256:[0-9a-f]*' /opt/sparkrouter/systemd/sparkrouter-halogen.service)"
check before-L || { stamp "FATAL: production is not LOW DEFAULT LIVE; L would not measure production"; exit 1; }
$PY draft --arm C >> "$LOG" 2>&1 &
pc=$!
$PY draft --arm G >> "$LOG" 2>&1 &
pg=$!
for a in L M X; do
  $PY draft --arm "$a" >> "$LOG" 2>&1
  rc=$?
  stamp "draft $a rc=$rc"
done
check after-X
wait "$pc"; rc=$?; stamp "draft C rc=$rc"
wait "$pg"; rc=$?; stamp "draft G rc=$rc"
$PY grade >> "$LOG" 2>&1
rc=$?
stamp "grade rc=$rc"
$PY judge --judge x-ai/grok-4.7 >> "$OUT/judge-grok.log" 2>&1 &
p1=$!
$PY judge --judge moonshotai/kimi-k3.1-pro >> "$OUT/judge-kimi.log" 2>&1 &
p2=$!
wait "$p1"; rc=$?; stamp "judge grok rc=$rc"
wait "$p2"; rc=$?; stamp "judge kimi rc=$rc"
stamp "=== E162 done"
