#!/usr/bin/env bash
# File: run_eval_pilot.sh
# Purpose: Run the eval-pilot promptfoo suite against each model via a managed llama-server lifecycle.
# Project: sparkbench | Date: 2026-07-04
#
# Overview: For each "label|gguf-path" pair passed on stdin or argv-file,
# starts llama-server (-np 1, -c 32768 EXPLICIT per the spec's
# safe-defaults review, --jinja), health-polls with a timeout (Rule 2),
# runs promptfoo with telemetry disabled, kills the server (SIGTERM ->
# SIGKILL), and writes results/eval-pilot/<label>.json alongside
# <label>.serverlog. Any model's failure is logged and the loop continues
# (briefing convention).
# Usage: tools/run_eval_pilot.sh <models-file>
#   models-file lines: label|/abs/path/model.gguf
# Optional env:
#   NP        parallel slots (default 1)
#   SUITE     promptfoo config to run (default promptfooconfig.yaml)
#   OUTPREFIX prefix for the output pair, so a re-run does not overwrite
#             stored results. Applied to BOTH the json and the serverlog,
#             which must stay paired - audit_ceiling.py joins them by name.
#
# WHY NP DEFAULTS TO 1 (changed 2026-08-12). -c is the TOTAL context and
# llama-server divides it by the slot count, so -np 2 -c 32768 gives each
# request only 16384 tokens. On 2026-07-04 that left E10's 16,140-token
# prompt with 244 tokens of headroom: three of five models decoded exactly
# 244 and the server logged truncated=1, which was then recorded as a
# capability result. One slot is the SAME total KV allocation and twice
# the usable context. These suites issue one request at a time, so the
# concurrency the second slot bought was never used.

set -u

MODELS_FILE="${1:?usage: run_eval_pilot.sh <models-file>  (lines: label|/path.gguf)}"
ROOT=/home/agent-spark/sparkbench
# Default is the b9864 build every prior eval ran on - unchanged, so existing
# callers keep their binary and past results stay reproducible. Override via
# env for models needing a newer build (Qwen3.8/qwen35 needs b10435). The
# build is part of the CONFIG a result names, so the caller states it (F39).
SERVER="${SERVER:-$ROOT/llama.cpp/build/bin/llama-server}"
export PATH=$HOME/.local/opt/node-v24.18.0-linux-x64/bin:$PATH
export PROMPTFOO_DISABLE_TELEMETRY=1 PROMPTFOO_DISABLE_UPDATE=1

wait_healthy() {
    python3 - <<'PY'
import sys, time, urllib.request
for _ in range(120):
    try:
        urllib.request.urlopen("http://127.0.0.1:8100/health", timeout=2); sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit("server never became healthy")
PY
}

while IFS='|' read -r label gguf; do
    case "$label" in \#*|"") continue;; esac
    echo "=== $label ($gguf) ==="
    # One stem for the pair, so the json and its serverlog can always be joined.
    stem="${OUTPREFIX:+${OUTPREFIX}-}$label"
    "$SERVER" -m "$gguf" -np "${NP:-1}" -c 32768 --jinja --no-webui \
        --host 127.0.0.1 --port 8100 \
        > "$ROOT/results/eval-pilot/$stem.serverlog" 2>&1 &
    spid=$!
    if ! wait_healthy; then
        echo "FAIL: $label server unhealthy - skipping (log kept)"
        kill "$spid" 2>/dev/null; wait "$spid" 2>/dev/null
        continue
    fi
    ( cd "$ROOT/spikes/eval-pilot" && \
      timeout 1800 promptfoo eval -c "${SUITE:-promptfooconfig.yaml}" --no-cache \
        -o "$ROOT/results/eval-pilot/$stem.json" 2>&1 | tail -6 )
    kill "$spid" 2>/dev/null
    if ! timeout 15 tail --pid="$spid" -f /dev/null 2>/dev/null; then
        kill -9 "$spid" 2>/dev/null
    fi
    wait "$spid" 2>/dev/null
    echo "--- $label done ---"
done < "$MODELS_FILE"
pgrep -x llama-server >/dev/null && echo "WARN: llama-server still running" || echo "ALL-CLEAN"
