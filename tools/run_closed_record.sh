#!/usr/bin/env bash
# File: run_closed_record.sh
# Purpose: Run the closed-record matters against each local model via a managed llama-server
#          lifecycle.
# Project: sparkbench | Date: 2026-08-12
#
# Overview: Same lifecycle shape as run_eval_pilot.sh - start llama-server per model, health-poll
# with a timeout, run the matters, kill the server - but calls run_matters.py rather than
# promptfoo, because the matters are scored against sealed keys and not by assertions.
# -np 1 is deliberate and NOT overridable to 2 by accident: -c is the TOTAL context and
# llama-server divides it by the slot count, which is what silently truncated E10 (F20).
# Usage: tools/run_closed_record.sh <models-file>
#   models-file lines: label|/abs/path/model.gguf
# Optional env: NP (default 1), MAXTOK (default 2000), REPS (default 1), CTX (default 32768),
#               THINKING (default "default"), MATTERS_ONLY (default all),
#               REQ_TIMEOUT (default derived from MAXTOK)

set -u

MODELS_FILE="${1:?usage: run_closed_record.sh <models-file>  (lines: label|/path.gguf)}"
ROOT=/home/agent-spark/sparkbench
# The b10435 worktree build, NOT llama.cpp/build, which is a July binary.
# F63 measured the b9864 -> b10435 move at about +3.3% tg, so mixing builds
# across a comparison is a config confound (Rule 8). Overridable so a
# deliberate build comparison is still possible.
SERVER=${SPARKBENCH_SERVER_BIN:-$ROOT/llama.cpp/wt/b10435/build/bin/llama-server}
OUTDIR=$ROOT/results/closed-record
mkdir -p "$OUTDIR"

wait_healthy() {
    python3 - <<'PY'
import sys, time, urllib.request
for _ in range(180):
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
    if [ ! -f "$gguf" ]; then
        echo "FAIL: $label - no such gguf, skipping"
        continue
    fi
    # -v is required or the Rule 3 full-offload gate has no evidence to read,
    # and Rule 3 FAILS on zero evidence rather than passing.
    "$SERVER" -m "$gguf" -np "${NP:-1}" -c "${CTX:-32768}" --jinja --no-webui -v \
        --host 127.0.0.1 --port 8100 \
        > "$OUTDIR/$label.serverlog" 2>&1 &
    spid=$!
    if ! wait_healthy; then
        echo "FAIL: $label server unhealthy - skipping (log kept)"
        kill "$spid" 2>/dev/null; wait "$spid" 2>/dev/null
        continue
    fi
    # MATTERS_ONLY and REQ_TIMEOUT are optional and passed only when set, so
    # the unset case keeps run_matters.py's own defaults (all matters; timeout
    # DERIVED from max_tokens). Setting REQ_TIMEOUT below the derived floor is
    # legitimate - E44 caps on the clock deliberately - and run_matters.py
    # warns rather than overriding.
    only_args=()
    [ -n "${MATTERS_ONLY:-}" ] && only_args=(--only "$MATTERS_ONLY")
    timeout_args=()
    [ -n "${REQ_TIMEOUT:-}" ] && timeout_args=(--timeout "$REQ_TIMEOUT")
    # ORDER is passed only when set, so the unset case keeps run_matters.py's
    # historical sorted order and every earlier arm stays comparable. It exists
    # because F70 makes sequence position a variable rather than a detail.
    order_args=()
    [ -n "${ORDER:-}" ] && order_args=(--order "$ORDER")
    python3 "$ROOT/spikes/closed-record/run_matters.py" \
        --label "$label" --out "$OUTDIR/$label.json" \
        --max-tokens "${MAXTOK:-2000}" --reps "${REPS:-1}" \
        --thinking "${THINKING:-default}" \
        "${only_args[@]}" "${timeout_args[@]}" "${order_args[@]}" \
        || echo "FAIL: $label run errored"
    kill "$spid" 2>/dev/null
    if ! timeout 15 tail --pid="$spid" -f /dev/null 2>/dev/null; then
        kill -9 "$spid" 2>/dev/null
    fi
    wait "$spid" 2>/dev/null
    echo "--- $label done ---"
done < "$MODELS_FILE"

# The relay's own llama-server runs on :8400 and is not ours to reap, so this reports rather
# than asserting ALL-CLEAN on a bare process check.
# pgrep -f self-matches through the invoking shell, which reports a phantom
# occupant; -x on the binary name cannot.
if pgrep -x llama-server >/dev/null 2>&1; then
    echo "WARN: something is still listening on 8100"
else
    echo "PORT-8100-CLEAR"
fi
