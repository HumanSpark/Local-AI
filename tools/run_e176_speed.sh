#!/usr/bin/env bash
# File: tools/run_e176_speed.sh
# Purpose: E176 speed leg - llama-bench on Ling-3.2-air Q3_K_M at depths 0/8192/32768 on two llama.cpp builds.
# Project: sparkbench | Date: 2026-11-24
#
# Overview: results/e176-prereg.md. Same safety shape as tools/run_e174_kv.sh: one relay window, page-cache eviction,
# GTT baseline and settle before every invocation, one llama-bench call per depth (run_step8_leg.sh, thermal capture),
# f16 KV, -fa on, -ngl 999, -r 3. Builds: 94f3af3d0 (the build E174 measured Flash-Next on, so speed compares
# like-for-like) then ae6a7ad2c (newest upstream). Flash-Next is NOT reloaded (104 GiB, over the F193 line). Stops at
# the first non-zero rc; the EXIT trap restores the relay and proves it with the production probe.
set -u
REPO=/home/bench/sparkbench
OUT=$REPO/results/e176
LOG=$OUT/speed.log
GGUF=/opt/models/staging/ling-3.2-air/Ling-3.2-air-Q3_K_M-00001-of-00002.gguf
WINDOW=/usr/local/sbin/relay_bench_window.sh
stamp() { echo "[$(date -Is)] $*" | tee -a "$LOG"; }
EVICT() { python3 "$REPO/tools/evict_page_cache.py" /opt/models/staging >>"$LOG" 2>&1; local rc=$?; stamp "evict rc=$rc | $(free -m | awk '/^Mem/{print "used "$3" free "$4" cache "$6" MiB"}')"; }
gtt() { echo $(( $(cat /sys/class/drm/card0/device/mem_info_gtt_used) >> 20 )); }
restore() {
  stamp "restoring relay"; sudo -n "$WINDOW" up >>"$LOG" 2>&1; local rc=$?; stamp "relay up rc=$rc"
  for _ in $(seq 1 24); do
    if timeout 120 python3 "$REPO/tools/production_probe.py" --dry-run --only code >>"$LOG" 2>&1; then
      stamp "relay restored, VERIFIED: production probe (code) passed"; return 0; fi
    sleep 15
  done
  stamp "WARNING: production probe still failing 6+ min after up - run: sudo $WINDOW up"
}
[ -s "$GGUF" ] || { echo "ERROR: $GGUF missing; hint: wait for the fetch (results/scout-ling32/fetch.log)" >&2; exit 3; }
mkdir -p "$OUT"
trap restore EXIT
stamp "E176 speed start: kernel $(uname -r)"
sudo -n "$WINDOW" idle-down >>"$LOG" 2>&1 || { stamp "FATAL idle-down failed"; exit 1; }
EVICT
prev=$(gtt); same=0
for _ in $(seq 1 36); do sleep 5; g=$(gtt); d=$(( g > prev ? g - prev : prev - g )); [ $d -le 256 ] && same=$((same+1)) || same=0; prev=$g; [ $same -ge 2 ] && break; done
BASE=$prev; stamp "GTT baseline $BASE MiB"
for build in 94f3af3d0 ae6a7ad2c; do
  export BENCH_BIN=$REPO/var/engines/llama-$build/build/bin/llama-bench
  [ -x "$BENCH_BIN" ] || { stamp "FATAL $BENCH_BIN missing"; exit 3; }
  for depth in 0 8192 32768; do
    ok=0
    for _ in $(seq 1 90); do [ "$(gtt)" -le $((BASE + 2048)) ] && { ok=1; break; }; sleep 2; done
    [ $ok -eq 1 ] || { stamp "FAIL settle before $build d$depth: GTT $(gtt) MiB"; exit 1; }
    EVICT
    sleep 10
    tag="$build-d$depth"
    stamp "$tag start"
    timeout 3600 "$REPO/tools/run_step8_leg.sh" "e176-$tag" "$OUT/bench-$tag.md" \
      -m "$GGUF" -ngl 999 -fa on -p 512 -n 128 -r 3 -d "$depth" -o md 2>"$OUT/bench-$tag.stderr"
    rc=$?
    stamp "$tag rc=$rc"
    grep -iE 'devicelost|out of memory|error' "$OUT/bench-$tag.stderr" | head -3 | tee -a "$LOG"
    [ $rc -eq 0 ] || { stamp "STOP: non-zero rc at $tag - reboot before any further GPU load (F193)"; exit $rc; }
  done
done
stamp "E176 speed done"
