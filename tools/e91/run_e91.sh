#!/usr/bin/env bash
# File: run_e91.sh
# Purpose: Run E91 (Flash-Next vs incumbents, same build) inside a maintenance window, unattended.
# Project: sparkbench | Date: 2026-08-31
#
# Overview: Opens the sparkrouter maintenance window, runs four arms against
# two frozen banks (l4 and l3 n=9) on ONE build, closes the window again. The
# relay is restored by an EXIT trap on any path - success, failure, or Ctrl-C -
# because a session that leaves the LAN service down is worse than one that
# collects no data. Pre-registration: results/e91-prereg.md, written before any
# arm ran. Arm D is optional and skipped automatically if the clock has gone.
#
# Requires the narrow sudoers grant on relay_bench_window.sh (installed
# 2026-08-31); without it, phase `window` fails loudly and nothing else runs.
#
# Usage: bash tools/e91/run_e91.sh [--with-d] [--dry-run]

set -uo pipefail

REPO=/home/agent-spark/sparkbench
BUILD="$REPO/llama.cpp/wt/daef7b6/build/bin/llama-server"
# The PRIVILEGED copy, not the repo one. The sudoers grant names this exact
# path and names it WITHOUT a `bash` prefix, so it must be invoked as
# `sudo /usr/local/sbin/relay_bench_window.sh <phase>` or sudo will refuse and
# an unattended run will sit on a password prompt. The repo copy is the
# development source; this one is updated deliberately by root (see
# docs/SPARKROUTER-MAINTENANCE-HANDOFF.md).
WINDOW=/usr/local/sbin/relay_bench_window.sh
RAW="$REPO/results/raw/e91"
LOG="$RAW/e91-run.log"

WORKHORSE=/opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf
QWEN38=/opt/models/staging/Qwen3.8-27B-Q4_K_M.gguf
FLASHNEXT=/opt/models/staging/Qwen3.8-Flash-Next-UD-IQ4_XS-00001-of-00003.gguf

WITH_D=0
DRY=0
WINDOW_TEST=0
for a in "$@"; do
    case "$a" in
        --with-d)  WITH_D=1 ;;
        --dry-run) DRY=1 ;;
        # Exercises the open/verify/trap/restore path and NOTHING else, so the
        # risky part can be proved in ~30s instead of being discovered at hour
        # zero of a two-hour window. It exists because the 16:25 run opened the
        # window, misread a successful `down` as failure, and exited without
        # restoring - the trap logic is the thing that needs testing, not the
        # commands.
        --window-test) WINDOW_TEST=1 ;;
        *) echo "usage: $0 [--with-d] [--dry-run] [--window-test]" >&2; exit 2 ;;
    esac
done

mkdir -p "$RAW"

stamp() { printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }

# The relay goes back up on EVERY exit path. This is the single most important
# line in the file: an unattended run that dies at 02:00 must not leave the LAN
# service down until somebody notices.
WINDOW_OPEN=0
restore_relay() {
    rc=$?
    if [ "$WINDOW_OPEN" -eq 1 ]; then
        stamp "restoring relay (exit rc=$rc)"
        sudo "$WINDOW" up 2>&1 | tee -a "$LOG" || true
        # Same reasoning as `down`: `up`'s exit code is not trustworthy, so
        # confirm the service is actually back rather than reporting on it.
        if pgrep -x llama-server >/dev/null 2>&1; then
            stamp "relay restored, VERIFIED: llama-server is running"
        else
            stamp "WARNING: relay NOT restored - run 'sudo $WINDOW up' by hand NOW"
        fi
    fi
    stamp "run finished, rc=$rc"
}
trap restore_relay EXIT

preflight() {
    stamp "=== preflight ==="
    [ -x "$BUILD" ] || { stamp "FATAL: build missing at $BUILD"; exit 1; }
    "$BUILD" --version 2>&1 | head -2 | tee -a "$LOG"
    for m in "$WORKHORSE" "$QWEN38" "$FLASHNEXT"; do
        [ -f "$m" ] || { stamp "FATAL: model missing: $m"; exit 1; }
    done
    # Flash-Next is a 3-shard split; llama.cpp loads the set from shard 1, but
    # the siblings must be present or it fails deep into the load.
    for n in 00002 00003; do
        f="/opt/models/staging/Qwen3.8-Flash-Next-UD-IQ4_XS-${n}-of-00003.gguf"
        [ -f "$f" ] || { stamp "FATAL: Flash-Next shard missing: $f"; exit 1; }
    done
    stamp "all three models present; build OK"
}

# arm <label> <model> <tier> <effort> <extra-args...>
arm() {
    local label="$1" model="$2" tier="$3" effort="$4"; shift 4
    local out="$RAW/e91-${label}-${tier}.json"
    stamp "--- arm ${label} / ${tier} / effort=${effort} ---"
    if [ "$DRY" -eq 1 ]; then
        stamp "DRY-RUN: would run ${label} ${tier}"
        return 0
    fi
    local t0 t1
    t0=$(date +%s)
    SPARKBENCH_SERVER_BIN="$BUILD" python3 "$REPO/tools/run_ps_eval.py" \
        --model "$model" --label "e91-${label}" --out "$out" \
        --tier "$tier" --thinking "$effort" \
        --server-extra '-fa on -ctk q8_0 -ctv q8_0' \
        "$@" 2>&1 | tee -a "$LOG"
    local rc="${PIPESTATUS[0]}"
    t1=$(date +%s)
    stamp "arm ${label}/${tier} rc=${rc} wall=$((t1-t0))s -> ${out}"
    # A failed arm does NOT abort the session - the controls are worth having
    # even if the challenger dies, and vice versa. Recorded, not fatal.
    [ "$rc" -eq 0 ] || stamp "WARNING: arm ${label}/${tier} exited ${rc}; continuing"
}

preflight

stamp "=== opening maintenance window ==="
if [ "$DRY" -eq 0 ]; then
    # Set BEFORE the call, never after. If `down` half-succeeds - gateway
    # stopped, something later failed - the trap must still restore it. Setting
    # this afterwards is what left the LAN service down on the 16:25 run.
    WINDOW_OPEN=1
    sudo "$WINDOW" down 2>&1 | tee -a "$LOG" || stamp "note: 'down' exited non-zero; verifying state rather than trusting it"
    # DO NOT branch on that exit code. relay_bench_window.sh runs under
    # `set -euo pipefail` and its status() ends in `pgrep -x llama-server`,
    # which correctly exits 1 once the gateway is stopped - so a SUCCESSFUL
    # `down` exited non-zero for as long as the script has existed. Verify the
    # thing we actually care about instead: is the box free?
    if pgrep -x llama-server >/dev/null 2>&1; then
        stamp "FATAL: llama-server still running after 'down' - refusing to take the box"
        exit 1
    fi
    stamp "window open, VERIFIED: no llama-server process holds the GPU"
fi

if [ "$WINDOW_TEST" -eq 1 ]; then
    stamp "=== --window-test: window is open and verified; closing via the EXIT trap ==="
    exit 0
fi

START=$(date +%s)

# Arm A - workhorse. Cheap, and it is the ruler check that decides whether any
# cross-build comparison in this session is legitimate at all.
arm A-workhorse "$WORKHORSE" l4 default
arm A-workhorse "$WORKHORSE" l3 default --distractors 9

# Arm B - the incumbent, same build. The model to beat.
arm B-qwen38-low "$QWEN38" l4 low
arm B-qwen38-low "$QWEN38" l3 low --distractors 9

# Arm C - the challenger, effort matched to B.
arm C-flashnext-low "$FLASHNEXT" l4 low
arm C-flashnext-low "$FLASHNEXT" l3 low --distractors 9

# Arm D - optional. Skipped unless asked AND the clock still allows, because
# overrunning the window costs the LAN service, not just the experiment.
if [ "$WITH_D" -eq 1 ]; then
    ELAPSED=$(( $(date +%s) - START ))
    if [ "$ELAPSED" -lt 5400 ]; then
        arm D-flashnext-medium "$FLASHNEXT" l4 medium
        arm D-flashnext-medium "$FLASHNEXT" l3 medium --distractors 9
    else
        stamp "SKIPPING arm D: ${ELAPSED}s elapsed, over the 5400s budget"
    fi
fi

stamp "=== all arms done in $(( $(date +%s) - START ))s; raw JSON in $RAW ==="
stamp "score with: python3 $REPO/tools/e91/score_e91.py"
