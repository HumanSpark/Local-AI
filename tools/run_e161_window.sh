#!/usr/bin/env bash
# File: tools/run_e161_window.sh
# Purpose: Run E161 in one idle window: routing-skew imatrix runs, then the six speed arms, restoring production on exit.
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Opens the relay idle window (sudo -n relay_bench_window.sh idle-down, the E154 runner's mechanism, which
# stops Halogen) and refuses to start unless GPU memory reads as free. Phase 1 (skew): mainline llama-imatrix on each
# corpus in results/e161/corpus/ (code, docs: --chunks 120; prose: all its chunks, amendment 1) to
# results/e161/imatrix-<c>.gguf. Phase 2 (speed): each arm's llama-server on 127.0.0.1:8161, timed by
# tools/e153_speed.py (var/ft-venv python) on CODE,PROSE,JSON,P8K into results/e161/speed-<arm>.json; server logs to
# results/e161/<arm>.serverlog. A failing arm is logged and the run moves on (a T arm load failure is a result).
# The EXIT trap stops every engine and runs `up`, then reports whether the relay serves again.
# Usage: bash tools/run_e161_window.sh [arm ...]   (default: skew M0 M4 M12 M24 T0 T1)
set -uo pipefail
ROOT=/home/bench/sparkbench
OUT=$ROOT/results/e161
LOG=$OUT/window.log
WINDOW=/usr/local/sbin/relay_bench_window.sh
MODEL=/opt/models/staging/qwen3.8-flash-next-udiq4xs/Qwen3.8-Flash-Next-UD-IQ4_XS-00001-of-00003.gguf
ML=$ROOT/llama.cpp/wt/e574a17/build/bin
TL=$ROOT/llama.cpp/wt/tandem-f5222f25c/build/bin
PY=$ROOT/var/ft-venv/bin/python3
PORT=8161
COMMON=(-m "$MODEL" -c 65536 -np 1 -fa on -ctk q8_0 -ctv q8_0 --jinja -ngl 99 -t 16 --host 127.0.0.1 --port "$PORT")
ARMS=("$@")
[ ${#ARMS[@]} -eq 0 ] && ARMS=(skew M0 M4 M12 M24 T0 T1)
mkdir -p "$OUT"
stamp() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a "$LOG"; }
gpu_gib() { echo $(( ($(cat /sys/class/drm/card0/device/mem_info_gtt_used) + $(cat /sys/class/drm/card0/device/mem_info_vram_used)) / 1073741824 )); }

WINDOW_OPEN=0
SERVER_PID=""
stop_engine() {
  if [ -n "$SERVER_PID" ]; then
    kill "$SERVER_PID" 2>/dev/null
    for _ in $(seq 30); do kill -0 "$SERVER_PID" 2>/dev/null || break; sleep 1; done
    # llama-server can ignore SIGTERM when idle (E154 note): escalate rather than leave it holding the GPU.
    kill -9 "$SERVER_PID" 2>/dev/null
  fi
  SERVER_PID=""
}
cleanup() {
  stop_engine
  pkill -x llama-imatrix 2>/dev/null
  if [ "$WINDOW_OPEN" -eq 1 ]; then
    sudo -n "$WINDOW" up 2>&1 | tee -a "$LOG"
    # Production is Halogen (an idle unit to the window script), so prove it end to end: the no-root probe must
    # print LOW DEFAULT LIVE, i.e. Halogen answers with the community template and the guard's low default.
    local ok=0
    for _ in $(seq 40); do
      if python3 /opt/sparkrouter/ops/halogen_effort_check.py >> "$LOG" 2>&1; then ok=1; break; fi
      sleep 15
    done
    if [ "$ok" -eq 1 ]; then stamp "production restored, VERIFIED: halogen_effort_check LOW DEFAULT LIVE"
    else stamp "WARNING: production NOT verified 10 min after 'up' - run: sudo $WINDOW up, then python3 /opt/sparkrouter/ops/halogen_effort_check.py"; fi
  fi
}
trap cleanup EXIT

serve_and_time() {  # serve_and_time <arm> <binary> [extra args...]
  local arm=$1 bin=$2; shift 2
  if [ ! -x "$bin" ]; then stamp "$arm: SKIPPED, no binary $bin"; return; fi
  stamp "$arm: starting $(basename "$(dirname "$(dirname "$(dirname "$bin")")")") $* "
  "$bin" "${COMMON[@]}" "$@" > "$OUT/$arm.serverlog" 2>&1 < /dev/null &
  SERVER_PID=$!
  timeout 3000 "$PY" "$ROOT/tools/e153_speed.py" --arm "$arm" --url "http://127.0.0.1:$PORT" \
    --buckets CODE,PROSE,JSON,P8K --out "$OUT/speed-$arm.json" 2>&1 | tee -a "$LOG" | tail -12
  local rc=${PIPESTATUS[0]}
  kill -0 "$SERVER_PID" 2>/dev/null || stamp "$arm: server exited early - see $arm.serverlog tail: $(tail -3 "$OUT/$arm.serverlog" | tr '\n' ' ')"
  stamp "$arm: speed client rc=$rc; peak GPU now $(gpu_gib) GiB"
  stop_engine
  sleep 5
}

skew() {
  local c n chunks
  for c in code docs prose; do
    [ -s "$OUT/corpus/$c.txt" ] || { stamp "skew: corpus $c missing - run python3 tools/e161_corpus.py"; return 1; }
    chunks=120; [ "$c" = prose ] && chunks=-1
    stamp "skew: imatrix on $c (--chunks $chunks)"
    timeout 3600 "$ML/llama-imatrix" -m "$MODEL" -f "$OUT/corpus/$c.txt" -c 512 --chunks "$chunks" -ngl 99 -fa on -t 16 \
      -o "$OUT/imatrix-$c.gguf" > "$OUT/imatrix-$c.log" 2>&1 < /dev/null
    n=$?
    stamp "skew: $c rc=$n; $(grep -m1 -o 'computing over [0-9]* chunks[^,]*' "$OUT/imatrix-$c.log")"
  done
}

stamp "=== E161 window: arms ${ARMS[*]} ==="
stamp "kernel $(uname -r); livepatch: $(canonical-livepatch status 2>/dev/null | grep -m1 -i 'patch state' | tr -s ' ')"
WINDOW_OPEN=1   # set BEFORE the call: a half-done idle-down must still be restored
sudo -n "$WINDOW" idle-down 2>&1 | tee -a "$LOG"
sleep 10
g=$(gpu_gib)
if [ "$g" -gt 12 ]; then stamp "FATAL: GPU still holds $g GiB after idle-down; not starting"; exit 1; fi
stamp "window open, VERIFIED: GPU holds $g GiB"
T0=$(date +%s)
for a in "${ARMS[@]}"; do
  case $a in
    skew) skew ;;
    M0) serve_and_time M0 "$ML/llama-server" ;;
    M4) serve_and_time M4 "$ML/llama-server" --n-cpu-moe 4 ;;
    M12) serve_and_time M12 "$ML/llama-server" --n-cpu-moe 12 ;;
    M24) serve_and_time M24 "$ML/llama-server" --n-cpu-moe 24 ;;
    T0) serve_and_time T0 "$TL/llama-server" ;;
    T1) serve_and_time T1 "$TL/llama-server" -cmoe --moe-cache-mib auto -lm none ;;
    T2) serve_and_time T2 "$TL/llama-server" -cmoe --moe-cache-mib 24576 -lm none ;;  # amendment 2
    *) stamp "unknown arm $a" ;;
  esac
done
stamp "=== E161 done in $(( $(date +%s) - T0 ))s ==="
