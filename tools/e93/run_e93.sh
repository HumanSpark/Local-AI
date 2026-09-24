#!/usr/bin/env bash
# File: run_e93.sh
# Purpose: Run E93 - does abliteration remove epistemic and professional refusal along with safety refusal?
# Project: sparkbench | Date: 2026-08-31
#
# Overview: One base/abliteration pair, three banks. The BASE arm on l4 is
# already measured - E91 arm B, same build, same day - so only E76 and PR1 need
# the base re-run. The abliterated model runs all three.
#
# Pre-registration: results/e93-prereg.md, written before any arm.
# Requires: the abliterated GGUF fetched, verified and manifested (Rule 4), and
# the `pr1` tier wired into run_ps_eval.py. Both are checked in preflight and
# this refuses rather than half-running.
#
# Paired with Qwen3.8-27B rather than the workhorse on a control property: the
# 27B scored over_claims 0/1 on l4 today and the workhorse 1/1. A base already
# at the floor cannot show degradation of the thing being measured.
#
# Usage: bash tools/e93/run_e93.sh [--dry-run] [--window-test]

set -uo pipefail

REPO=/home/agent-spark/sparkbench
BUILD="$REPO/llama.cpp/wt/daef7b6/build/bin/llama-server"
WINDOW=/usr/local/sbin/relay_bench_window.sh
RAW="$REPO/results/raw/e93"
LOG="$RAW/e93-run.log"

BASE=/opt/models/staging/Qwen3.8-27B-Q4_K_M.gguf
# Set once the fetch has landed and been manifested. Deliberately not guessed:
# preflight fails loudly rather than running against a path that does not exist.
ABL="${E93_ABL_MODEL:-/opt/models/staging/Huihui-Qwen3.8-27B-abliterated-Q4_K.gguf}"

DRY=0
WINDOW_TEST=0
for a in "$@"; do
    case "$a" in
        --dry-run)     DRY=1 ;;
        --window-test) WINDOW_TEST=1 ;;
        *) echo "usage: $0 [--dry-run] [--window-test]" >&2; exit 2 ;;
    esac
done

mkdir -p "$RAW"
stamp() { printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }

WINDOW_OPEN=0
restore_relay() {
    rc=$?
    if [ "$WINDOW_OPEN" -eq 1 ]; then
        stamp "restoring relay (exit rc=$rc)"
        sudo "$WINDOW" up 2>&1 | tee -a "$LOG" || true
        if pgrep -x llama-server >/dev/null 2>&1; then
            stamp "relay restored, VERIFIED: llama-server is running"
        else
            stamp "WARNING: relay NOT restored - run 'sudo $WINDOW up' by hand NOW"
        fi
    fi
    stamp "E93 finished, rc=$rc"
}
trap restore_relay EXIT

# arm <label> <model> <tier>
arm() {
    local label="$1" model="$2" tier="$3"
    local out="$RAW/e93-${label}-${tier}.json"
    stamp "--- ${label} / ${tier} ---"
    if [ "$DRY" -eq 1 ]; then stamp "DRY-RUN: would run ${label} ${tier}"; return 0; fi
    local t0 rc; t0=$(date +%s)
    SPARKBENCH_SERVER_BIN="$BUILD" python3 "$REPO/tools/run_ps_eval.py" \
        --model "$model" --label "e93-${label}" --out "$out" \
        --tier "$tier" --thinking low --ctx 16384 \
        --server-extra '-fa on -ctk q8_0 -ctv q8_0' 2>&1 | tee -a "$LOG"
    rc="${PIPESTATUS[0]}"
    stamp "${label}/${tier} rc=${rc} wall=$(( $(date +%s) - t0 ))s -> ${out}"
    [ "$rc" -eq 0 ] || stamp "WARNING: ${label}/${tier} exited ${rc}; continuing"
}

stamp "=== preflight ==="
[ -x "$BUILD" ] || { stamp "FATAL: build missing at $BUILD"; exit 1; }
[ -f "$BASE" ] || { stamp "FATAL: base model missing: $BASE"; exit 1; }
if [ ! -f "$ABL" ]; then
    stamp "FATAL: abliterated model not found at $ABL"
    stamp "  Fetch it first with tools/fetch_hf_model.sh, verify sha256, and add a"
    stamp "  manifests/MANIFEST.md entry BEFORE first use (Rule 4). Override the"
    stamp "  path with E93_ABL_MODEL=... if it landed under another name."
    exit 1
fi
# The pr1 tier must exist, or every pr1 arm dies one at a time inside the window.
if ! python3 -c "
import sys; sys.path.insert(0,'$REPO/tools')
import run_ps_eval as r
sys.exit(0 if 'pr1' in r.TIERS else 1)
" 2>/dev/null; then
    stamp "FATAL: the 'pr1' tier is not registered in run_ps_eval.py."
    stamp "  spikes/ps-eval/{corpus_pr1,questions_pr1}.py exist; wire the TIERS entry."
    exit 1
fi
grep -q "$(basename "$ABL")" "$REPO/manifests/MANIFEST.md" || {
    stamp "FATAL: $(basename "$ABL") has no MANIFEST.md entry. Rule 4: provenance"
    stamp "  is recorded BEFORE first use, not after."
    exit 1
}
stamp "preflight OK"

stamp "=== opening maintenance window ==="
if [ "$DRY" -eq 0 ]; then
    WINDOW_OPEN=1
    sudo "$WINDOW" down 2>&1 | tee -a "$LOG" || stamp "note: 'down' exit code ignored; verifying state instead"
    if pgrep -x llama-server >/dev/null 2>&1; then
        stamp "FATAL: llama-server still running after 'down' - refusing to take the box"
        exit 1
    fi
    stamp "window open, VERIFIED: no llama-server process holds the GPU"
fi

if [ "$WINDOW_TEST" -eq 1 ]; then
    stamp "=== --window-test: open and verified; closing via the EXIT trap ==="
    exit 0
fi

START=$(date +%s)

# PR1 first on BOTH arms: it carries the discriminating hypothesis, and running
# it first means a session that overruns still answered the question it was for.
arm BASE "$BASE" pr1
arm ABL  "$ABL"  pr1

# Then the epistemic-abstention axis.
arm BASE "$BASE" l4
arm ABL  "$ABL"  l4

stamp "=== E93 arms done in $(( $(date +%s) - START ))s; raw in $RAW ==="
stamp "NOTE: BASE l4 duplicates E91 arm B (same build, same day). Kept as an"
stamp "  in-experiment replicate - F96 says within-process reps are not"
stamp "  independent, but these are separate processes, so it is a real one."
