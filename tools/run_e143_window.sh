#!/usr/bin/env bash
# File: tools/run_e143_window.sh
# Purpose: Run every E143 arm (chat-recommended coding models through Aider) in one gateway window, in pre-registered order.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: Opens the maintenance window (sudoers-granted /usr/local/sbin/relay_bench_window.sh),
# then for each arm in order D, A, C, B: serves the model solo on llama.cpp daef7b6 with E113's
# exact flags, passes the full-offload gate, runs tools/aider_task_runner.py three times against the
# probe proxy, stops the server, and commits + pushes that arm's results (bank both sides). The
# relay is restored on EVERY exit path by the EXIT trap - window logic is E91's, including the
# rule not to branch on `down`'s exit code. A watcher kills the server if MemAvailable stays under
# 3 GiB, because a RAM exhaustion here has reset the box before (E136). Registered in
# results/e143-prereg.md. Usage: tools/run_e143_window.sh [--dry-run] [--window-test] [arm...]

set -uo pipefail

REPO=/home/agent-spark/sparkbench
BIN="$REPO/llama.cpp/wt/daef7b6/build/bin/llama-server"
WINDOW=/usr/local/sbin/relay_bench_window.sh
M=/opt/models/staging
RAW="$REPO/results/raw/e143"
LOG="$RAW/window.log"
TASKS="$REPO/tools/aider-tasks.json"
REPEATS=3
ARM_TIMEOUT_S=7200

declare -A MODEL=(
  [D]="$M/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf"
  [A]="$M/Qwen3.8-27B-Q4_K_M.gguf"
  [C]="$M/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf"
  [B]="$M/Qwen3.8-Flash-Next-UD-IQ4_XS-00001-of-00003.gguf"
)
declare -A EXPECT_BYTES=([C]=22360456160)

DRY=0
WINDOW_TEST=0
ARMS=()
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    --window-test) WINDOW_TEST=1 ;;
    D|A|C|B) ARMS+=("$a") ;;
    *) echo "usage: $0 [--dry-run] [--window-test] [D A C B]" >&2; exit 2 ;;
  esac
done
[ "${#ARMS[@]}" -gt 0 ] || ARMS=(D A C B)

mkdir -p "$RAW"
stamp() { printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }

SERVER_PID=""
PROBE_PID=""
WATCH_PID=""
WINDOW_OPEN=0

stop_all() {
  for p in "$WATCH_PID" "$PROBE_PID" "$SERVER_PID"; do
    [ -n "$p" ] && kill "$p" 2>/dev/null
  done
  [ -n "$SERVER_PID" ] && wait "$SERVER_PID" 2>/dev/null
  SERVER_PID=""; PROBE_PID=""; WATCH_PID=""
  # Only our own PIDs are killed. A blanket `pkill -x llama-server` here would take down the
  # PRODUCTION gateway whenever the trap fires before the window is open (e.g. preflight fails).
  sleep 5
}

restore_relay() {
  rc=$?
  stop_all
  if [ "$WINDOW_OPEN" -eq 1 ]; then
    stamp "restoring relay (exit rc=$rc)"
    sudo "$WINDOW" up 2>&1 | tee -a "$LOG" || true
    # `up`'s exit code is not trustworthy either; confirm the service is back.
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
  [ -x "$BIN" ] || { stamp "FATAL: build missing at $BIN"; exit 1; }
  command -v aider >/dev/null 2>&1 || { stamp "FATAL: aider not on PATH"; exit 1; }
  for arm in "${ARMS[@]}"; do
    [ -f "${MODEL[$arm]}" ] || { stamp "FATAL: arm $arm model missing: ${MODEL[$arm]}"; exit 1; }
    if [ -n "${EXPECT_BYTES[$arm]:-}" ]; then
      got=$(stat -c %s "${MODEL[$arm]}")
      [ "$got" -eq "${EXPECT_BYTES[$arm]}" ] || { stamp "FATAL: arm $arm size $got != ${EXPECT_BYTES[$arm]}"; exit 1; }
    fi
  done
  for n in 00002 00003; do
    [ -f "$M/Qwen3.8-Flash-Next-UD-IQ4_XS-${n}-of-00003.gguf" ] || { stamp "FATAL: Flash-Next shard $n missing"; exit 1; }
  done
  python3 "$REPO/tools/aider_task_runner.py" --tasks "$TASKS" --workdir "$RAW/worktrees-precheck" --check-preconditions \
    >>"$LOG" 2>&1 || { stamp "FATAL: task preconditions invalid - refusing to run"; exit 1; }
  stamp "preflight OK: arms ${ARMS[*]}, build present, preconditions valid"
}

mem_watch() {
  local low=0
  while sleep 2; do
    avail_kb=$(awk '/MemAvailable/{print $2}' /proc/meminfo)
    if [ "$avail_kb" -lt 3145728 ]; then low=$((low + 1)); else low=0; fi
    if [ "$low" -ge 3 ]; then
      echo "[$(date -Is)] MEM GUARD: MemAvailable ${avail_kb} kB for 6 s - killing llama-server" >>"$LOG"
      pkill -x llama-server
      return
    fi
  done
}

run_arm() {
  local arm=$1 model="${MODEL[$1]}" out="$RAW/$1" t0
  mkdir -p "$out"
  stamp "--- arm $arm: $(basename "$model") ---"
  if [ "$DRY" -eq 1 ]; then stamp "DRY-RUN: would serve and run arm $arm"; return 0; fi
  t0=$(date +%s)
  "$BIN" -m "$model" -c 49152 --jinja --host 127.0.0.1 --port 8400 --no-webui -v >"$out/server.serverlog" 2>&1 &
  SERVER_PID=$!
  mem_watch & WATCH_PID=$!
  local ok=0
  for _ in $(seq 1 450); do
    kill -0 "$SERVER_PID" 2>/dev/null || break
    if python3 -c "
import urllib.request,sys
try: sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8400/health',timeout=5).status==200 else 1)
except Exception: sys.exit(1)"; then ok=1; break; fi
    sleep 2
  done
  if [ "$ok" -ne 1 ]; then
    stamp "arm $arm VOID: server never became healthy in 900 s (see $out/server.serverlog)"
    stop_all; return 1
  fi
  local assigned oncpu
  assigned=$(grep -cE 'layer +[0-9]+ assigned to device' "$out/server.serverlog")
  oncpu=$(grep -cE 'layer +[0-9]+ assigned to device CPU' "$out/server.serverlog")
  if [ "$assigned" -eq 0 ] || [ "$oncpu" -ne 0 ]; then
    stamp "arm $arm VOID: full-offload gate FAILED (assigned=$assigned, on CPU=$oncpu)"
    stop_all; return 1
  fi
  stamp "arm $arm: full-offload gate OK ($assigned layers, 0 on CPU); load took $(( $(date +%s) - t0 ))s"
  python3 "$REPO/tools/aider_probe.py" --port 8499 --upstream http://127.0.0.1:8400 \
    --log "$out/probe.jsonl" >"$out/probe.log" 2>&1 &
  PROBE_PID=$!
  sleep 3
  local mid
  mid=$(python3 -c "
import json,urllib.request
print(json.load(urllib.request.urlopen('http://127.0.0.1:8400/v1/models',timeout=30))['data'][0]['id'])")
  [ -n "$mid" ] || { stamp "arm $arm VOID: no model id from /v1/models"; stop_all; return 1; }
  stamp "arm $arm: served model id $mid"
  for r in $(seq 1 "$REPEATS"); do
    kill -0 "$SERVER_PID" 2>/dev/null || { stamp "arm $arm: server died before repeat $r - remaining attempts VOID"; break; }
    if [ $(( $(date +%s) - t0 )) -gt "$ARM_TIMEOUT_S" ]; then
      stamp "arm $arm: over ${ARM_TIMEOUT_S}s, stopping before repeat $r"; break
    fi
    python3 "$REPO/tools/aider_task_runner.py" --tasks "$TASKS" --workdir "$out/worktrees/r$r" \
      --probe-log "$out/probe.jsonl" --model "openai/$mid" --out "$out/r$r.json" --timeout 1800 \
      >"$out/r$r.log" 2>&1
    stamp "arm $arm repeat $r rc=$? -> $out/r$r.json"
  done
  dmesg 2>/dev/null | grep -ciE 'amdgpu.*(fault|timeout|reset)' | sed "s/^/arm $arm dmesg amdgpu fault lines: /" | tee -a "$LOG"
  stop_all
  stamp "arm $arm done in $(( $(date +%s) - t0 ))s"
  bank_arm "$arm"
}

# Bank the arm's results before the next, larger arm can wedge the box. Best effort: a push
# failure is logged, never fatal, and only explicit paths are staged (shared-tree rule).
bank_arm() {
  local arm=$1
  git -C "$REPO" add "results/raw/e143/$arm/r"*.json "results/raw/e143/$arm/probe.jsonl" "results/raw/e143/window.log" 2>/dev/null
  git -C "$REPO" commit -q -m "chore(e143): bank arm $arm raw results (Aider x3 repeats, probe log, server log)" \
    -- "results/raw/e143/$arm" "results/raw/e143/window.log" >>"$LOG" 2>&1 || stamp "note: nothing to commit for arm $arm"
  git -C "$REPO" push -q origin main >>"$LOG" 2>&1 || stamp "WARNING: push failed after arm $arm - results are committed locally"
}

preflight

stamp "=== opening maintenance window ==="
if [ "$DRY" -eq 0 ]; then
  # Set BEFORE the call: if `down` half-succeeds the trap must still restore (E91 scar).
  WINDOW_OPEN=1
  sudo "$WINDOW" down 2>&1 | tee -a "$LOG" || stamp "note: 'down' exited non-zero; verifying state rather than trusting it"
  if pgrep -x llama-server >/dev/null 2>&1; then
    stamp "FATAL: llama-server still running after 'down' - refusing to take the box"
    exit 1
  fi
  stamp "window open, VERIFIED: no llama-server process holds the GPU"
fi

if [ "$WINDOW_TEST" -eq 1 ]; then
  stamp "=== --window-test: window open and verified; closing via the EXIT trap ==="
  exit 0
fi

START=$(date +%s)
for arm in "${ARMS[@]}"; do
  run_arm "$arm" || stamp "WARNING: arm $arm did not complete; continuing with the next"
done
stamp "=== all arms done in $(( $(date +%s) - START ))s; raw results in $RAW ==="
