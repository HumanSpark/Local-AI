#!/usr/bin/env bash
# File: tools/run_e179_htr025.sh
# Purpose: E179 speed leg - E177 speed leg unchanged except the HTR image (v0.2.5).
# Project: sparkbench | Date: 2026-11-25
#
# Overview: results/e179-prereg.md; copy of tools/run_e177_htr.sh (results/e177-prereg.md). Phase 1 (relay up): e163_speed against Halogen at 127.0.0.1:8433. Phase 2: one relay
# window - idle-down, page-cache eviction (F198 addendum), GTT baseline, start the pinned vllm-htr image with rootless
# podman (card hardening, keep-id so the container's UID 1000 can write its compile cache), wait up to 60 min for
# /v1/models (first start compiles), log GTT and free memory each minute while loading, run e163_speed (auto-off), stop
# the container. The EXIT trap stops the container, restores the relay and proves it with the production probe.
# A DeviceLost or OOM in the container log stops everything: reboot before further GPU work (F193).
set -u
REPO=/home/bench/sparkbench
OUT=$REPO/results/e179
RAW=$OUT/raw
LOG=$OUT/run.log
WINDOW=/usr/local/sbin/relay_bench_window.sh
IMG=ghcr.io/hawgauto/vllm-htr@sha256:daa6b2847bf9678e2de39b8b216105ffe13313e50db889f002f5f918e581d193
MODEL=/opt/models/staging/qwen3.8-flash-next-htr/Htr5Core
WS=$REPO/var/e179/htr-workspace
PORT=8177
NAME=e179-htr
mkdir -p "$RAW/HS" "$RAW/HT" "$WS"
stamp() { echo "[$(date -Is)] $*" | tee -a "$LOG"; }
gtt() { echo $(( $(cat /sys/class/drm/card0/device/mem_info_gtt_used) >> 20 )); }
mem() { free -m | awk '/^Mem/{print "used "$3" free "$4" cache "$6" MiB"}'; }
WINDOW_OPEN=0
cleanup() {
  podman rm -f "$NAME" >/dev/null 2>&1
  if [ "$WINDOW_OPEN" = 1 ]; then
    stamp "restoring relay"; sudo -n "$WINDOW" up >>"$LOG" 2>&1; local rc=$?; stamp "relay up rc=$rc"
    for _ in $(seq 1 24); do
      if timeout 120 python3 "$REPO/tools/production_probe.py" --dry-run --only code >>"$LOG" 2>&1; then
        stamp "relay restored, VERIFIED: production probe (code) passed"; return 0; fi
      sleep 15
    done
    stamp "WARNING: production probe still failing 6+ min after up - run: sudo $WINDOW up"
  fi
}
trap cleanup EXIT
stamp "E179 start: kernel $(uname -r)"

if [ ! -s "$RAW/HS/speed.json" ]; then
  stamp "phase 1: Halogen (production, live) speed"
  timeout 3600 python3 "$REPO/tools/e163_speed.py" --label HS-today --base http://127.0.0.1:8433 --thinking-off kwargs \
    --out "$RAW/HS/speed.json" >>"$RAW/HS/speed.log" 2>&1
  rc=$?; stamp "phase 1 rc=$rc"; [ $rc -eq 0 ] || exit $rc
fi

stamp "phase 2: HTR"
sudo -n "$WINDOW" idle-down >>"$LOG" 2>&1 || { stamp "FATAL idle-down failed"; exit 1; }
WINDOW_OPEN=1
python3 "$REPO/tools/evict_page_cache.py" /opt/models/staging >>"$LOG" 2>&1; stamp "evict rc=$? | $(mem)"
prev=$(gtt); same=0
for _ in $(seq 1 36); do sleep 5; g=$(gtt); d=$(( g > prev ? g - prev : prev - g )); [ $d -le 256 ] && same=$((same+1)) || same=0; prev=$g; [ $same -ge 2 ] && break; done
stamp "GTT baseline $prev MiB"
podman run -d --rm --init --pull=never --name "$NAME" \
  --device /dev/kfd --device /dev/dri --group-add keep-groups --userns=keep-id:uid=1000,gid=1000 \
  --pids-limit 8192 --shm-size 16g --ulimit core=0 --security-opt no-new-privileges:true \
  -e VLLM_NO_USAGE_STATS=1 -e DO_NOT_TRACK=1 \
  -p 127.0.0.1:$PORT:8000 \
  --mount "type=bind,src=$MODEL,dst=/model,readonly" --mount "type=bind,src=$WS,dst=/workspace" \
  "$IMG" /model --host 0.0.0.0 --port 8000 --max-model-len 40960 --max-num-seqs 1 \
  --max-num-batched-tokens 2048 --kv-cache-memory-bytes 4294967296 >>"$LOG" 2>&1 || { stamp "FATAL podman run failed"; exit 1; }
(podman logs -f "$NAME" >>"$RAW/HT/server.log" 2>&1 &)
t0=$(date +%s); ready=0
for i in $(seq 1 720); do
  if timeout 5 python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:$PORT/v1/models', timeout=4)" 2>/dev/null; then ready=1; break; fi
  if ! podman ps --format '{{.Names}}' | grep -qx "$NAME"; then stamp "FATAL container exited while loading"; break; fi
  if grep -qiE 'devicelost|out of memory|HSA_STATUS_ERROR|segmentation fault' "$RAW/HT/server.log" 2>/dev/null; then
    stamp "FATAL $(grep -iE 'devicelost|out of memory|HSA_STATUS_ERROR|segmentation fault' "$RAW/HT/server.log" | head -1 | cut -c1-160) - STOP; reboot before further GPU work (F193)"; exit 2; fi
  [ $((i % 12)) -eq 0 ] && stamp "loading $(( $(date +%s) - t0 ))s: GTT $(gtt) MiB | $(mem)"
  sleep 5
done
[ $ready -eq 1 ] || { stamp "FATAL not ready after $(( $(date +%s) - t0 ))s"; exit 1; }
stamp "HTR ready in $(( $(date +%s) - t0 ))s; GTT $(gtt) MiB | $(mem)"
timeout 3600 python3 "$REPO/tools/e163_speed.py" --label HT --base "http://127.0.0.1:$PORT" --thinking-off auto-off \
  --out "$RAW/HT/speed.json" >>"$RAW/HT/speed.log" 2>&1
rc=$?; stamp "phase 2 speed rc=$rc | GTT $(gtt) MiB | $(mem)"
stamp "E179 speed leg done"
