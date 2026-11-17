#!/usr/bin/env bash
# File: tools/run_e165.sh
# Purpose: Run E165 unattended - the test audit's re-runs (tool use v3, mt-l4, mt-long, H6) on arms Q, KFL, KX, HS, LM.
# Project: sparkbench | Date: 2026-11-17
#
# Overview: Follows results/e165-prereg.md. Arm Q (cloud, no GPU) runs in the background through tools/cloud_proxy.py
# on 127.0.0.1:8165 (ledger results/e165/raw/ledger.jsonl, ceiling $1.50) with run_e164.sh's flags. The local arms run
# at the same time through tools/run_e154_arms.sh in one idle window, with E154_RAW=results/e165/raw and only the four
# re-run suites; that runner restores and verifies the relay on exit and banks each arm. Every suite skips a finished
# output file, so a relaunch resumes. Then tools/score_e165.py. Log: results/e165/run.log.
# Usage: setsid bash tools/run_e165.sh > /dev/null 2>&1 &
set -uo pipefail
REPO=/home/bench/sparkbench
OUT=$REPO/results/e165
RAWQ=$OUT/raw/Q
LOG=$OUT/run.log
PORT=8165
URL=http://127.0.0.1:$PORT
SUITES="tooluse mt-l4 mt-long h6-date"
mkdir -p "$RAWQ"
stamp() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
stamp "=== E165 start; HEAD $(git -C "$REPO" rev-parse --short HEAD)"

run_q() {
  python3 "$REPO/tools/cloud_proxy.py" --listen $PORT --model qwen/qwen4-max --ledger "$OUT/raw/ledger.jsonl" \
    --usd-ceiling 1.50 >> "$OUT/raw/proxy.log" 2>&1 &
  local proxy=$!
  for _ in $(seq 30); do python3 -c "import urllib.request;urllib.request.urlopen('$URL/health',timeout=2)" 2>/dev/null && break; sleep 1; done
  local common=(--port $PORT --ctx 262144 --max-tokens 32768 --thinking default) suite out rc
  for suite in $SUITES; do
    out=$RAWQ/$suite.json
    if [ -s "$out" ]; then stamp "Q $suite: already done, skipped"; continue; fi
    stamp "Q $suite start"
    case "$suite" in
      mt-l4|mt-long) timeout 21600 python3 "$REPO/tools/run_multiturn_eval.py" --model qwen/qwen4-max --external \
                --conversation "${suite#mt-}" --label "Q-$suite" --out "$out" "${common[@]}" >> "$RAWQ/$suite.log" 2>&1 ;;
      tooluse) timeout 21600 "$REPO/var/tooluse-venv/bin/python3" "$REPO/tools/tooluse_harness_v2.py" --base-url "$URL" \
                --label e165-Q --runs 3 --max-rounds 4 --max-tokens 32768 --thinking default >> "$RAWQ/$suite.log" 2>&1 \
                && cp "$REPO/results/tool-use/E33-results-e165-Q.json" "$out" ;;
      h6-date) timeout 21600 python3 "$REPO/tools/run_h6_date_arm.py" --model qwen/qwen4-max --allow-busy-gpu \
                --base-url "$URL" --tools on --tier l4-date --label Q-h6 --out "$out" --ctx 262144 \
                --max-tokens 32768 --thinking default >> "$RAWQ/$suite.log" 2>&1 ;;
    esac
    rc=$?
    stamp "Q $suite: rc=$rc $(tail -1 "$RAWQ/$suite.log" | cut -c1-160)"
    if grep -q 'ceiling reached' "$OUT/raw/proxy.log"; then stamp "STOP: Q ceiling reached"; break; fi
  done
  kill $proxy 2>/dev/null
  stamp "Q spend: \$$(python3 -c "import json;print(round(sum(json.loads(l)['cost_usd'] for l in open('$OUT/raw/ledger.jsonl')),4))")"
}

run_q &
qpid=$!
E154_RAW=$OUT/raw E154_KW_SUITES="$SUITES" E154_TU_PREFIX=e165 E163_SKIP_SPEED=1 E154_TAG=e165 \
  bash "$REPO/tools/run_e154_arms.sh" KFL KX HS LM >> "$OUT/local.log" 2>&1
stamp "local arms rc=$?"
wait $qpid
stamp "Q done"
python3 "$REPO/tools/score_e165.py" >> "$LOG" 2>&1
stamp "score rc=$?"
stamp "=== E165 done"
