#!/usr/bin/env bash
# File: tools/e114_rerun_harness_timeouts.sh
# Purpose: E114 - re-run E109 arm B's three non-returning items on a quiet GPU with a longer cap.
# Project: sparkbench | Date: 2026-09-06
#
# Overview: E112 established that E109 arm B's three `transport_failed` items
# were an artefact of a 600 s cap and a shared GPU, not a harness limit - all
# three return and grade correct. That leaves F148 resting on a MEASURED 20 of
# 24 plus a reconstruction of what 24 of 24 would have been, and E112's own
# result says explicitly that three items graded alone cannot restate a 24-item
# headline.
#
# This is the run that can. Same 24 items, same grader, same harness, same
# model - the only changes against E109 arm B are the ones E112 justified: a
# 2,400 s cap instead of 600 s, and a quiet GPU.
#
# R05 IS THE ITEM TO WATCH. It failed E109 as `format_error` after 159.2 s with
# "Context length exceeded (1,781 tokens). Cannot compress further" - a Hermes
# compaction limit, not a cap. The serving config here is a near-reproduction
# (below), so if -c differs from E109's, R05 is the item whose outcome that
# difference would move. Its result is therefore evidence about the CONFIG as
# much as about the harness.
#
# SERVING CONFIG, stated because it is a deviation: the live
# /var/lib/sparkrouter/serving.conf is the one source of truth and is NOT
# READABLE by agent-spark, so this reproduces the flag set the repo's copy
# documents (-c 49152 --jinja --host 127.0.0.1 --no-webui) with the bench build
# and the E109 model. If the live file has drifted, this is a near-reproduction
# and not an exact one - a limit on what the result can claim, not a reason to
# skip it.
#
# The relay is deliberately down (owner, 2026-09-06), so port 8400 is free.

set -uo pipefail

REPO=/home/agent-spark/sparkbench
BIN=$REPO/llama.cpp/wt/b10435/build/bin/llama-server
MODEL=/opt/models/staging/Qwen3.8-27B-Q4_K_M.gguf
OUT=$REPO/results/raw/e114
SRV=$OUT/e114-server.serverlog
WORK=$OUT/docs

mkdir -p "$OUT" "$WORK"

if ss -ltn 2>/dev/null | grep -q '127.0.0.1:8400'; then
  echo "FATAL: something is already listening on 8400. hint: the relay may have been"
  echo "brought back up; do not bench through the relay (CLAUDE.md)."
  exit 1
fi

"$BIN" -m "$MODEL" -c 49152 --jinja --host 127.0.0.1 --port 8400 --no-webui -v \
  > "$SRV" 2>&1 &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null' EXIT

echo "server pid $SERVER_PID, waiting for health"
for _ in $(seq 1 150); do
  if curl_out=$(python3 -c "
import urllib.request,sys
try:
    sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8400/health', timeout=5).status==200 else 1)
except Exception:
    sys.exit(1)
"); then break; fi
  sleep 2
done

# Rule 3: the full-offload gate is asserted from the server log, and zero
# evidence is a FAIL, never a pass.
assigned=$(grep -cE 'layer +[0-9]+ assigned to device' "$SRV")
oncpu=$(grep -E 'layer +[0-9]+ assigned to device CPU' "$SRV" | wc -l)
if [ "$assigned" -eq 0 ]; then
  echo "FATAL: full-offload gate FAILED - no 'assigned to device' lines in $SRV"
  exit 1
fi
if [ "$oncpu" -ne 0 ]; then
  echo "FATAL: full-offload gate FAILED - $oncpu of $assigned layers on CPU"
  exit 1
fi
echo "full-offload gate OK: $assigned layers, 0 on CPU"

python3 "$REPO/tools/e109_harness_knowledge.py" \
  --harness hermes \
  --workdir "$WORK" \
  --out "$OUT/e114-armB-hermes-l5-full.json" \
  --timeout 2400
rc=$?
printf '%s E114 rc=%d\n' "$(date -Is)" "$rc"
exit "$rc"
