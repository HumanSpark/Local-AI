#!/usr/bin/env bash
# File: banking_audit.sh
# Purpose: Verify the repo is fully banked to forge - no unpushed commits, no unbanked results/docs - before/after risky legs.
# Project: sparkbench | Date: 2026-07-11
#
# Overview: The E29 chain's final banking stage failed silently (results on
# disk, no commit, no entry). This gate makes that failure mode loud: fetches
# origin, reports ahead/behind, and lists any modified or untracked files
# under results/, reports/, docs/, manifests/, spikes/. Exit 0 = fully
# banked; exit 1 = unbanked state found (printed). Run before AND after
# every risky leg (envelope rungs, near-edge runs) per the both-sides rule.

set -u
cd /home/agent-spark/sparkbench || exit 2
git fetch -q origin || { echo "AUDIT-FAIL: fetch failed (hint: check forge reachability)"; exit 2; }
AHEAD=$(git rev-list --count origin/main..HEAD)
BEHIND=$(git rev-list --count HEAD..origin/main)
DIRTY=$(git status --porcelain -- results reports docs manifests spikes tools | grep -v '^??.*\.serverlog$' || true)
FAIL=0
[ "$AHEAD" != "0" ] && { echo "AUDIT-FAIL: $AHEAD unpushed commit(s)"; git log --oneline origin/main..HEAD | head -5; FAIL=1; }
[ "$BEHIND" != "0" ] && echo "AUDIT-NOTE: $BEHIND commit(s) behind origin (pull before committing)"
[ -n "$DIRTY" ] && { echo "AUDIT-FAIL: unbanked files:"; echo "$DIRTY" | head -20; FAIL=1; }
[ "$FAIL" = "0" ] && echo "AUDIT-PASS: fully banked (HEAD $(git rev-parse --short HEAD) = origin/main)"
exit $FAIL
