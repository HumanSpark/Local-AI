#!/usr/bin/env bash
# File: tools/e90/verify_t3.sh
# Purpose: Acceptance gate for E90's T3 - the two fastapi-importing test modules must skip
#          cleanly instead of aborting collection, without losing any test.
# Project: sparkbench | Date: 2026-08-30
#
# Overview: Run inside a task worktree. Two conditions, both required:
#   1. `pytest tests/ --collect-only` exits 0 - no module ERRORs the collection.
#   2. Every `def test_*` present at HEAD is still present in both files.
# Condition 2 exists because condition 1 alone is satisfiable by deleting the tests: a
# fully-skipped module collects nothing and pytest exits 5, so "no tests collected" and
# "the tests were removed" are indistinguishable without it.
set -uo pipefail

FILES=(tests/test_auth_sidecar.py tests/test_kokoro_gateway.py)

out="$(python3 -m pytest tests/ --collect-only -q \
        --ignore=tests/test_sparkrouter_discovery.py 2>&1)"
rc=$?
printf '%s\n' "$out" | tail -8

if [ "$rc" -ne 0 ]; then
  echo "GATE 1 FAIL: collection of tests/ exited $rc (expected 0)"
  exit 1
fi
echo "GATE 1 OK: tests/ collects with no errors"

for f in "${FILES[@]}"; do
  before="$(git show "HEAD:$f" | grep -c '^def test_')"
  after="$(grep -c '^def test_' "$f")"
  if [ "$before" != "$after" ]; then
    echo "GATE 2 FAIL: $f had $before test functions at HEAD, now has $after"
    exit 1
  fi
  echo "GATE 2 OK: $f still defines $after test functions"
done

exit 0
