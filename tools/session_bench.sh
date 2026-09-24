#!/usr/bin/env bash
# File: session_bench.sh
# Purpose: Hold ONE maintenance window for a whole bench session and run arms back to back inside it.
# Project: sparkbench | Date: 2026-08-31
#
# Overview: Per-experiment runners each open and close their own window, which
# costs a relay stop and start between every experiment and lets the gateway
# come back up in the gaps. For a long unattended session that is pure waste:
# the owner's instruction on 2026-08-31 was to take the box for the session.
# So this opens the window ONCE, runs an ordered queue, and restores the relay
# only at the very end - including on crash or interrupt, via the EXIT trap.
#
# THE RELAY COMES BACK NO MATTER HOW THIS ENDS. The trap fires on normal exit,
# on `set -e` death, and on SIGINT/SIGTERM, and it verifies STATE afterwards
# rather than trusting the helper's exit code - a successful `down` exited
# non-zero for as long as that script existed.
#
# AN ARM THAT FAILS DOES NOT STOP THE QUEUE. Each arm's exit code is recorded
# and the next one runs, because a gate firing (rc 3 = Rule 13 truncation,
# rc 4 = Rule 14 transport) is a RESULT, not a reason to abandon the night.
# Arms whose pre-registration says "stop on this outcome" are ordered so that
# the stop costs nothing after them.
#
# Queue lives in a plain file, one arm per line, so it can be edited between
# sessions without touching this script:
#   <label>|<runner>|<args...>
# Blank lines and # comments are ignored.
#
# Usage:
#   bash tools/session_bench.sh tools/queue-2026-08-31.txt
#   bash tools/session_bench.sh --dry-run tools/queue-2026-08-31.txt

set -uo pipefail

REPO=/home/agent-spark/sparkbench
BUILD="$REPO/llama.cpp/wt/daef7b6/build/bin/llama-server"
WINDOW=/usr/local/sbin/relay_bench_window.sh
LOG="$REPO/results/raw/session-$(date +%Y%m%d-%H%M).log"
# Per-arm wall-clock ceiling. Was a hard 7200s, which is too tight for a
# long-context ceiling search: at 262,144 tokens a single prefill probe runs
# ~2,600s and three aliases need ~7,800s. Raised and made overridable so the
# timeout is never the thing that decides a result.
ARM_TIMEOUT="${SESSION_BENCH_ARM_TIMEOUT:-21600}"

DRY=0
QUEUE=""
for a in "$@"; do
    case "$a" in
        --dry-run) DRY=1 ;;
        -*) echo "usage: $0 [--dry-run] <queue-file>" >&2; exit 2 ;;
        *) QUEUE="$a" ;;
    esac
done
[ -n "$QUEUE" ] || { echo "usage: $0 [--dry-run] <queue-file>" >&2; exit 2; }
[ -f "$QUEUE" ] || { echo "FATAL: queue file not found: $QUEUE" >&2; exit 2; }

stamp() { printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }

WINDOW_OPEN=0
restore_relay() {
    rc=$?
    if [ "$WINDOW_OPEN" -eq 1 ]; then
        stamp "=== closing the session window (exit rc=$rc) ==="
        sudo "$WINDOW" up 2>&1 | tee -a "$LOG" || true
        if pgrep -x llama-server >/dev/null 2>&1; then
            stamp "relay restored, VERIFIED: llama-server is running"
        else
            stamp "WARNING: relay NOT restored - run 'sudo $WINDOW up' by hand NOW"
        fi
    fi
    stamp "session finished, rc=$rc"
}
trap restore_relay EXIT
# A killed session must still give the relay back.
trap 'exit 130' INT
trap 'exit 143' TERM

stamp "=== session queue: $QUEUE ==="
grep -vE '^\s*(#|$)' "$QUEUE" | while IFS= read -r line; do
    stamp "  queued: ${line%%|*}"
done

stamp "=== opening the session window (ONE window for the whole queue) ==="
if [ "$DRY" -eq 0 ]; then
    WINDOW_OPEN=1
    sudo "$WINDOW" down 2>&1 | tee -a "$LOG" || stamp "note: 'down' exit code ignored; verifying state instead"
    # A ZOMBIE IS NOT A RUNNING SERVER. `pgrep -x llama-server` matches a
    # defunct process, which holds no GPU and cannot be killed - so a crashed
    # arm whose parent never reaped it blocks every future bench with a gate
    # that is telling the truth about the process table and a lie about the
    # box. Observed 2026-08-31: pid 1808113, state Z, parent a stuck runner.
    LIVE=""
    for p in $(pgrep -x llama-server 2>/dev/null); do
        st=$(awk '/^State:/{print $2}' "/proc/$p/status" 2>/dev/null)
        [ "$st" = "Z" ] && { stamp "note: pid $p is a ZOMBIE llama-server - holds no GPU, ignored"; continue; }
        LIVE="$LIVE $p"
    done
    if [ -n "${LIVE// /}" ]; then
        stamp "FATAL: llama-server still LIVE after 'down' (pids:$LIVE) - refusing to take the box"
        exit 1
    fi
    stamp "window open, VERIFIED: no llama-server process holds the GPU"
fi

SESSION_START=$(date +%s)
N=0
FAILED=""
while IFS= read -r line; do
    case "$line" in ''|\#*) continue ;; esac
    N=$((N + 1))
    label="${line%%|*}"
    rest="${line#*|}"
    runner="${rest%%|*}"
    args="${rest#*|}"

    stamp "--- [$N] $label ---"
    if [ "$DRY" -eq 1 ]; then
        stamp "DRY-RUN: would run: python3 $runner $args"
        continue
    fi

    # SPLIT RESPECTING QUOTES, never by bare word-splitting. Unquoted $args
    # would hand `--server-extra` the value `"-fa` and scatter the rest as
    # stray arguments, because an unquoted expansion does not process quotes.
    # xargs applies the shell's own quoting rules; eval is avoided deliberately.
    mapfile -t ARGV < <(printf '%s' "$args" | xargs -n1 printf '%s\n')

    t0=$(date +%s)
    SPARKBENCH_SERVER_BIN="$BUILD" timeout "$ARM_TIMEOUT" python3 "$REPO/$runner" "${ARGV[@]}" 2>&1 | tee -a "$LOG"
    rc="${PIPESTATUS[0]}"
    wall=$(( $(date +%s) - t0 ))

    case "$rc" in
        0) stamp "[$N] $label rc=0 wall=${wall}s" ;;
        3) stamp "[$N] $label rc=3 wall=${wall}s - RULE 13 truncation gate: no score reported"
           FAILED="$FAILED $label(rc3)" ;;
        4) stamp "[$N] $label rc=4 wall=${wall}s - RULE 14 transport gate: items never answered"
           FAILED="$FAILED $label(rc4)" ;;
        124) stamp "[$N] $label rc=124 wall=${wall}s - TIMED OUT at ${ARM_TIMEOUT}s"
           FAILED="$FAILED $label(timeout)" ;;
        *) stamp "[$N] $label rc=$rc wall=${wall}s - UNEXPECTED"
           FAILED="$FAILED $label(rc$rc)" ;;
    esac
    # A gate firing is a result. Keep going.
done < <(grep -vE '^\s*(#|$)' "$QUEUE")

stamp "=== session done: $N arms in $(( $(date +%s) - SESSION_START ))s ==="
[ -n "$FAILED" ] && stamp "arms that did not exit 0:$FAILED" || stamp "every arm exited 0"
