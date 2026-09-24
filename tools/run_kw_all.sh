#!/usr/bin/env bash
# File: tools/run_kw_all.sh
# Purpose: Run E74 (KA-H1) across three local arms and two packs, unattended, after the coding pilot releases the GPU.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: Queued behind tools/run_ch1_all.sh. It waits for BOTH the GPU and
# that script, rather than only for a free llama-server: the coding pilot has
# gaps between arms where no server is up, and starting here in one of them
# would put two consumers on the GPU (Rule 9) and create exactly the memory
# contention that is the documented deadlock trigger.
#
# ONE SERVER PER (ARM, PACK). Context is sized per pack instead of allocating
# the largest for everything: -c is the TOTAL and an over-allocated KV on a
# 59 GiB model walks toward the memory edge for no benefit.
#
# THE l PACK IS NOT RUN HERE. At 263,339 chars it needs roughly -c 131072, and
# gpt-oss-120b plus a KV cache that size is the >60 GiB regime that must be run
# attended. That is KA-H2's experiment, with its own preflight.

set -u
cd /home/agent-spark/sparkbench || exit 1

LOG_DIR=/tmp/claude-1001/-home-agent-spark-sparkbench/aa47a4e8-1bd9-429b-8927-a15c05a17c83/scratchpad
STAMP=$(date +%Y%m%d-%H%M)
SERVER=/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server
PORT=8125

declare -A MODEL=(
  [workhorse]=/opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf
  [qwen38]=/opt/models/staging/Qwen3.8-27B-Q4_K_M.gguf
  [gptoss]=/opt/models/staging/gpt-oss-120b-mxfp4-00001-of-00003.gguf
)
# F84's graduated operating point, applied only to the arm it was measured on.
declare -A EXTRA=( [workhorse]="" [qwen38]="--spec-type draft-mtp --spec-draft-n-max 4" [gptoss]="" )
declare -A CTX=( [s]=32768 [m]=65536 )

say() { printf '%s  %s\n' "$(date -Is)" "$*"; }

say "waiting for the coding pilot and the GPU"
waited=0
while pgrep -f "[r]un_ch1_all.sh" >/dev/null || pgrep -x llama-server >/dev/null \
      || pgrep -f "[s]oak_load.py" >/dev/null; do
    sleep 60
    waited=$((waited + 60))
    if [ $((waited % 900)) -eq 0 ]; then say "  still waiting, $((waited / 60))min"; fi
    if [ "$waited" -gt 43200 ]; then say "FATAL: still busy after 12h"; exit 2; fi
done
say "GPU free after $((waited / 60))min"

for arm in gptoss qwen38 workhorse; do
  for pack in s m; do
    ctx=${CTX[$pack]}
    out="results/raw/kw-${arm}-${pack}.json"
    say "=== ${arm} / pack ${pack} (-c ${ctx}) ==="

    # shellcheck disable=SC2086
    "$SERVER" -m "${MODEL[$arm]}" -c "$ctx" -np 1 --host 127.0.0.1 --port "$PORT" \
        --no-webui ${EXTRA[$arm]} > "${LOG_DIR}/kw-${arm}-${pack}-${STAMP}.serverlog" 2>&1 &
    spid=$!

    ready=0
    for _ in $(seq 1 300); do
        if ! kill -0 "$spid" 2>/dev/null; then say "  server EXITED during load"; break; fi
        if python3 -c "import urllib.request,sys
try:
    urllib.request.urlopen('http://127.0.0.1:${PORT}/health',timeout=5)
except Exception: sys.exit(1)" 2>/dev/null; then ready=1; break; fi
        sleep 3
    done

    if [ "$ready" -eq 1 ]; then
        say "  loaded; running items"
        python3 tools/run_kw_eval.py --label "$arm" --pack "$pack" --port "$PORT" \
            --ctx "$ctx" --out "$out" \
            > "${LOG_DIR}/kw-${arm}-${pack}-${STAMP}.log" 2>&1
        rc=$?
        say "  run exited ${rc}"
        tail -8 "${LOG_DIR}/kw-${arm}-${pack}-${STAMP}.log"
    else
        say "  SKIPPED - server never became healthy (infrastructure, not capability)"
    fi

    kill "$spid" 2>/dev/null
    sleep 5
    pkill -x llama-server 2>/dev/null
    sleep 10

    if [ -f "$out" ]; then
        git add "$out"
        git commit -q -m "results(e74): KA-H1 ${arm} on pack ${pack}" -- "$out" 2>/dev/null
        git push -q origin main 2>/dev/null && say "  banked and pushed"
    fi
  done
done

say "=== scoring all banked KA-H1 runs ==="
python3 tools/score_kw_eval.py results/raw/kw-*.json --out results/raw/kw-scores.json \
    2>&1 | tee "${LOG_DIR}/kw-scores-${STAMP}.log"
git add results/raw/kw-scores.json
git commit -q -m "results(e74): KA-H1 mechanical scores across arms" -- results/raw/kw-scores.json 2>/dev/null
git push -q origin main 2>/dev/null
say "=== E74 complete ==="
