#!/usr/bin/env bash
# File: tools/run_e164.sh
# Purpose: Run E164 unattended - Qwen4 Max on the E160 suites via cloud_proxy, then E162 drafting, grade and one judge.
# Project: sparkbench | Date: 2026-11-17
#
# Overview: Follows results/e164-prereg.md. Starts tools/cloud_proxy.py on 127.0.0.1:8164 (ledger
# results/e164/raw/ledger.jsonl, ceiling $5.50), runs the seven suites with run_kw_suite's flags except --thinking
# default and --allow-busy-gpu, stops the proxy, then drafts arm Q ($1.00), grades, and judges Q against L, C and G with
# grok-4.7 ($3.00). Every step skips finished output, so a re-run resumes. Log: results/e164/run.log.
# Usage: setsid bash tools/run_e164.sh > /dev/null 2>&1 &
set -uo pipefail
REPO=/home/bench/sparkbench
OUT=$REPO/results/e164
RAW=$OUT/raw/Q
DRAFT=$OUT/drafting
LOG=$OUT/run.log
PORT=8164
URL=http://127.0.0.1:$PORT
mkdir -p "$RAW" "$DRAFT"
stamp() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" >> "$LOG"; }
stamp "=== E164 start; HEAD $(git -C "$REPO" rev-parse --short HEAD)"

python3 "$REPO/tools/cloud_proxy.py" --listen $PORT --model qwen/qwen4-max --ledger "$OUT/raw/ledger.jsonl" \
  --usd-ceiling 5.50 >> "$OUT/raw/proxy.log" 2>&1 &
proxy=$!
trap 'kill $proxy 2>/dev/null' EXIT
for _ in $(seq 30); do python3 -c "import urllib.request;urllib.request.urlopen('$URL/health',timeout=2)" 2>/dev/null && break; sleep 1; done

common=(--port $PORT --ctx 262144 --max-tokens 32768 --thinking default)
for suite in l5 pr1 writing mt-l4 mt-long tooluse h6-date; do
  out=$RAW/$suite.json
  if [ -s "$out" ]; then stamp "Q $suite: already done, skipped"; continue; fi
  stamp "Q $suite start"
  case "$suite" in
    l5|pr1) timeout 21600 python3 "$REPO/tools/run_ps_eval.py" --model qwen/qwen4-max --external --allow-busy-gpu \
              --label "Q-$suite" --tier "$suite" --out "$out" "${common[@]}" >> "$RAW/$suite.log" 2>&1 ;;
    writing) timeout 21600 python3 "$REPO/tools/run_writing_eval.py" --model qwen/qwen4-max --external \
              --label Q-writing --out "$out" "${common[@]}" >> "$RAW/$suite.log" 2>&1 ;;
    mt-l4|mt-long) timeout 21600 python3 "$REPO/tools/run_multiturn_eval.py" --model qwen/qwen4-max --external \
              --conversation "${suite#mt-}" --label "Q-$suite" --out "$out" "${common[@]}" >> "$RAW/$suite.log" 2>&1 ;;
    tooluse) timeout 21600 "$REPO/var/tooluse-venv/bin/python3" "$REPO/tools/tooluse_harness_v2.py" --base-url "$URL" \
              --label e164-Q --runs 3 --max-rounds 4 --max-tokens 32768 --thinking default >> "$RAW/$suite.log" 2>&1 \
              && cp "$REPO/results/tool-use/E33-results-e164-Q.json" "$out" ;;
    h6-date) timeout 21600 python3 "$REPO/tools/run_h6_date_arm.py" --model qwen/qwen4-max --allow-busy-gpu \
              --base-url "$URL" --tools on --tier l4-date --label Q-h6 --out "$out" --ctx 262144 \
              --max-tokens 32768 --thinking default >> "$RAW/$suite.log" 2>&1 ;;
  esac
  rc=$?
  stamp "Q $suite: rc=$rc $(tail -1 "$RAW/$suite.log" | cut -c1-160)"
  if grep -q 'ceiling reached' "$OUT/raw/proxy.log"; then stamp "STOP: suite ceiling reached"; break; fi
done
kill $proxy 2>/dev/null
stamp "suites spend: $(python3 -c "import json;print(round(sum(json.loads(l)['cost_usd'] for l in open('$OUT/raw/ledger.jsonl')),4))")"

for f in drafts-L.json drafts-C.json drafts-G.json judge-grok-4.7.json; do
  [ -e "$DRAFT/$f" ] || cp "$REPO/results/e162/$f" "$DRAFT/$f"
done
PY="python3 $REPO/tools/run_e162.py --out-dir $DRAFT"
$PY draft --arm Q --usd-ceiling 1.00 >> "$LOG" 2>&1; stamp "draft Q rc=$?"
$PY grade >> "$LOG" 2>&1; stamp "grade rc=$?"
$PY judge --judge x-ai/grok-4.7 --arms Q,L,C,G --usd-ceiling 3.00 >> "$OUT/judge-grok.log" 2>&1; stamp "judge rc=$?"
stamp "=== E164 done"
