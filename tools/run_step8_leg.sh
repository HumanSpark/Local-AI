#!/usr/bin/env bash
# File: run_step8_leg.sh
# Purpose: Run one Step 8 llama-bench leg with amdgpu thermal capture before/after.
# Project: sparkbench | Date: 2026-07-03
#
# Overview: Wraps a single llama-bench invocation for the Step 8 unattended
# window (PHASE-A-LOG.md step 8 pre-registration). Resolves the amdgpu hwmon
# node by name (hwmon numbering is not stable across boots), appends edge
# temperature + timestamp to the thermal log before and after the run, writes
# the bench markdown to the given output file, and propagates llama-bench's
# exit code so a DeviceLost surfaces loudly (canary gate fires on it).
#
# Usage:   run_step8_leg.sh <label> <output.md> <llama-bench args...>
# Example: run_step8_leg.sh triplet-1 llama.cpp/bench-step8-triplet-1.md \
#            -m /opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf -o md

set -euo pipefail

# Default is the b9864 build every prior result was measured on - unchanged, so
# existing callers keep their binary. Override via env when a model needs a
# newer build (Qwen3.8/qwen35 arch needs b10435); the build is part of the
# CONFIG a result names, so the caller states it explicitly (F39).
BENCH_BIN="${BENCH_BIN:-/home/agent-spark/sparkbench/llama.cpp/build/bin/llama-bench}"
THERMAL_LOG="/home/agent-spark/sparkbench/llama.cpp/bench-step8-thermal.log"

if [ "$#" -lt 3 ]; then
    echo "ERROR: need <label> <output.md> <llama-bench args...>" >&2
    echo "hint: see usage example in the file header of $0" >&2
    exit 2
fi

label="$1"; shift
out="$1"; shift

if [ ! -x "$BENCH_BIN" ]; then
    echo "ERROR: llama-bench not executable at $BENCH_BIN" >&2
    echo "hint: build per PHASE-A-LOG step 3 (cmake -DGGML_VULKAN=ON)" >&2
    exit 3
fi

amdgpu_temp() {
    # Millidegrees C, or NA - a missing sensor is loggable, not fatal.
    local h
    for h in /sys/class/hwmon/hwmon*; do
        if [ "$(cat "$h/name" 2>/dev/null)" = "amdgpu" ]; then
            cat "$h/temp1_input" 2>/dev/null && return 0
        fi
    done
    echo "NA"
}

echo "$(date -Is) ${label} START temp_mC=$(amdgpu_temp)" >> "$THERMAL_LOG"
rc=0
"$BENCH_BIN" "$@" > "$out" || rc=$?
echo "$(date -Is) ${label} END rc=${rc} temp_mC=$(amdgpu_temp)" >> "$THERMAL_LOG"
exit "$rc"
