#!/usr/bin/env bash
# File: tools/run_e183_dspark.sh
# Purpose: E183 - Inkling-2-Mini UD-Q4_K_XL on stock llama.cpp b671865c7, no draft vs DSpark draft (3 and 7 tokens).
# Project: sparkbench | Date: 2026-11-26
#
# Overview: Opens ONE relay idle window (relay_bench_window.sh idle-down), then for each arm N0 (no draft),
# D3 (--spec-type draft-dspark, --spec-draft-n-max 3), D7 (same, n-max 7) starts llama-server on 127.0.0.1:8154
# (-c 65536 -np 1 -fa on -ngl 999, as E172 IM) and runs tools/e163_speed.py twice (r1, r2: repeat spread,
# memory speed-claims-need-spread). Between arms it waits for GTT to return to the window-open baseline (F198).
# Trap stops our engine, brings the relay up and proves it with the production probe. Prereg results/e183-prereg.md.
# Refuses to start if any container, llama-server, or sparkscene pipeline.py is running (owner standing rule).
set -uo pipefail
REPO=/home/bench/sparkbench
OUT=$REPO/results/e183/raw
LOG=$REPO/results/e183/raw/window.log
SRV=$REPO/var/engines/llama-b671865c7/build/bin/llama-server
GGUF=/opt/models/staging/inkling-2-mini-unsloth/Inkling-2-Mini-UD-Q4_K_XL.gguf_file   # A1: unsloth Mainline_Support variant, as E172 IM
DRAFT=${DRAFT:-/opt/models/staging/inkling-2-mini-unsloth/dspark-Inkling-2-Mini-Q8_0.gguf_file}   # A3: mainline draft
WINDOW=/usr/local/sbin/relay_bench_window.sh
PORT=8154
ARMS=${ARMS:-"N0 D3 D7"}
mkdir -p "$OUT"
stamp() { printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }

# Preflight: nothing else on the GPU (production-run check, owner 2026-11-26).
if [ -n "$(podman ps -q)" ] || pgrep -x llama-server >/dev/null || pgrep -f 'sparkscene.*pipeline.py' >/dev/null; then
  stamp "REFUSED: GPU busy (container, llama-server or sparkscene pipeline.py running). hint: wait for scene's GPU free"; exit 2
fi
for f in "$SRV" "$GGUF" "$DRAFT"; do [ -e "$f" ] || { stamp "REFUSED: missing $f"; exit 2; }; done
stamp "E183 start; kernel $(uname -r); livepatch: $(canonical-livepatch status 2>&1 | grep -m1 -i -E 'state|running|kernel' | xargs)"
stamp "llama.cpp $(git -C "$REPO/var/engines/llama-b671865c7" rev-parse HEAD)"

SERVER_PID=""; WINDOW_OPEN=0
gtt_mib() { echo $(( $(cat /sys/class/drm/card0/device/mem_info_gtt_used) >> 20 )); }
stop_engine() {
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null; SERVER_PID=""
  local i
  for i in $(seq 1 15); do pgrep -u "$(id -u)" -x llama-server >/dev/null || return 0; sleep 2; done
  stamp "llama-server ignored SIGTERM 30 s; SIGKILL"; pkill -9 -u "$(id -u)" -x llama-server; sleep 3
  pgrep -u "$(id -u)" -x llama-server >/dev/null && { stamp "FATAL: engine survived SIGKILL"; return 1; }
  return 0
}
gpu_settle() {
  local i g
  for i in $(seq 1 90); do
    g=$(gtt_mib)
    if [ "$g" -le $((GTT_BASELINE_MIB + 2048)) ]; then sleep 10; stamp "$1 settle: GTT ${g} MiB (baseline ${GTT_BASELINE_MIB})"; return 0; fi
    sleep 2
  done
  stamp "FAIL $1: GTT $(gtt_mib) MiB after 180 s (baseline ${GTT_BASELINE_MIB})"; return 1
}
verify_restored() {
  local t
  for t in $(seq 1 24); do
    if timeout 120 python3 "$REPO/tools/production_probe.py" --dry-run --only code >>"$LOG" 2>&1; then
      stamp "relay restored, VERIFIED by production probe (code)"; return 0; fi
    sleep 15
  done
  stamp "WARNING: production probe failing 6+ min after up. hint: sudo $WINDOW up; $WINDOW status"; return 1
}
cleanup() {
  [ "$WINDOW_OPEN" -eq 1 ] || return 0
  stop_engine
  sudo -n "$WINDOW" up 2>&1 | tee -a "$LOG"
  verify_restored
}
trap cleanup EXIT

sudo -n "$WINDOW" idle-down 2>&1 | tee -a "$LOG"; rc=${PIPESTATUS[0]}
[ "$rc" -eq 0 ] || { stamp "REFUSED: idle-down rc=$rc (relay busy?)"; exit 3; }
WINDOW_OPEN=1
sleep 15
GTT_BASELINE_MIB=$(gtt_mib); stamp "window open; GTT baseline ${GTT_BASELINE_MIB} MiB"

for arm in $ARMS; do
  gpu_settle "$arm" || continue
  case "$arm" in
    N0) extra=() ;;
    D3) extra=(-md "$DRAFT" --spec-type draft-dspark -ngld 999 --spec-draft-n-max 3) ;;
    D7) extra=(-md "$DRAFT" --spec-type draft-dspark -ngld 999 --spec-draft-n-max 7) ;;
    *) stamp "unknown arm $arm"; continue ;;
  esac
  mkdir -p "$OUT/$arm"
  slog="$OUT/$arm.serverlog"
  "$SRV" -m "$GGUF" "${extra[@]}" -c 65536 -np 1 -fa on -ngl 999 --jinja --host 127.0.0.1 --port "$PORT" --no-webui >"$slog" 2>&1 &
  SERVER_PID=$!
  stamp "$arm started pid $SERVER_PID: ${extra[*]:-no draft}"
  ready=0
  for i in $(seq 1 120); do
    kill -0 "$SERVER_PID" 2>/dev/null || break
    python3 -c "import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:$PORT/health',timeout=3).status==200 else 1)" 2>/dev/null && { ready=1; break; }
    sleep 3
  done
  if [ "$ready" -ne 1 ]; then stamp "FAIL $arm: not ready (see $slog)"; tail -5 "$slog" | tee -a "$LOG"; stop_engine; continue; fi
  # Full-offload gate (HARNESS-RULES): zero evidence = fail.
  grep -E -m3 "offloaded [0-9]+/[0-9]+ layers|draft|spec" "$slog" | tee -a "$LOG"
  for r in r1 r2; do
    timeout 1800 python3 "$REPO/tools/e163_speed.py" --label "E183-$arm-$r" --base "http://127.0.0.1:$PORT" \
      --thinking-off effort0 --out "$OUT/$arm/speed-$r.json" >"$OUT/$arm/speed-$r.log" 2>&1
    rc=$?
    stamp "$arm $r speed rc=$rc"
  done
  stop_engine
done
stamp "E183 arms done"
