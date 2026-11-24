#!/usr/bin/env bash
# File: tools/run_e173_renders.sh
# Purpose: Render the 15 scored E173 songs (3 music models x 5 frozen prompts) on audio.cpp Vulkan, one engine at a time.
# Project: sparkbench | Date: 2026-11-23
#
# Overview: Reads results/e173/prompts.json (frozen, sha256 in results/e173-prereg.md), opens ONE relay window
# (relay_bench_window.sh idle-down), measures the GTT baseline, then for each arm (YU, MM, AS) and song renders once
# with seed 7 via audiocpp_cli --metrics --log-file. F198: GTT must return to baseline before every start. GTT is
# sampled every 1 s per render. Every render's wall time, audio length, peak GTT and rc land in results/e173/renders.tsv.
# The EXIT trap restores the relay and proves it with the production probe. Stops at the first new /var/crash entry.
# Usage: tools/run_e173_renders.sh [ARM ...]   (default: YU MM AS)
set -u
REPO=/home/bench/sparkbench
A=/home/bench/audio.cpp/build/linux-vulkan-release/bin/audiocpp_cli
M=/opt/models/staging/audio-cpp
P=$REPO/results/e173/prompts.json
O=$REPO/results/e173/renders
mkdir -p "$O"
LOG=$REPO/results/e173/run.log
TSV=$REPO/results/e173/renders.tsv
WINDOW=/usr/local/sbin/relay_bench_window.sh
ARMS=("$@"); [ ${#ARMS[@]} -eq 0 ] && ARMS=(YU MM AS)
stamp() { echo "[$(date -Is)] $*" | tee -a "$LOG"; }
gtt() { echo $(( $(cat /sys/class/drm/card0/device/mem_info_gtt_used) >> 20 )); }
restore() {
  stamp "restoring relay"; sudo -n "$WINDOW" up >>"$LOG" 2>&1; stamp "relay up rc=$?"
  for _ in $(seq 1 24); do
    if timeout 120 python3 "$REPO/tools/production_probe.py" --dry-run --only code >>"$LOG" 2>&1; then
      stamp "relay restored, VERIFIED: production probe (code) passed"; return 0; fi
    sleep 15
  done
  stamp "WARNING: production probe still failing 6+ min after up - run: sudo $WINDOW up"
}
[ -x "$A" ] || { echo "ERROR: $A missing; hint: build audio.cpp v0.9.6 Vulkan (results/e173/audiocpp-vulkan-build.log)" >&2; exit 3; }
[ -s "$P" ] || { echo "ERROR: $P missing; hint: freeze prompts first (results/e173-prereg.md A1)" >&2; exit 3; }
trap restore EXIT
[ -s "$TSV" ] || printf 'arm\tsong\trc\twall_s\taudio_s\tpeak_gtt_over_base_mib\tstart_utc\n' >"$TSV"

crash0=$(ls /var/crash | wc -l)
stamp "E173 renders: arms ${ARMS[*]}; prompts sha256 $(sha256sum "$P" | cut -c1-16); audio.cpp $(git -C /home/bench/audio.cpp rev-parse --short HEAD)"
sudo -n "$WINDOW" idle-down >>"$LOG" 2>&1 || { stamp "FATAL idle-down failed"; exit 1; }
prev=$(gtt); same=0
for _ in $(seq 1 36); do sleep 5; g=$(gtt); d=$(( g > prev ? g - prev : prev - g )); [ $d -le 256 ] && same=$((same+1)) || same=0; prev=$g; [ $same -ge 2 ] && break; done
BASE=$prev; stamp "GTT baseline $BASE MiB"
settle() {
  for _ in $(seq 1 90); do [ "$(gtt)" -le $((BASE + 2048)) ] && { sleep 10; return 0; }; sleep 2; done
  stamp "FAIL settle: GTT $(gtt) MiB vs base $BASE"; return 1
}
field() { python3 -c 'import json,sys; s=json.load(open(sys.argv[1]))["songs"][int(sys.argv[2])]; print(s[sys.argv[3]])' "$P" "$1" "$2"; }

for arm in "${ARMS[@]}"; do
  for i in 0 1 2 3 4; do
    sid=$(field $i id); slug=$(field $i slug); style=$(field $i style); lyrics=$(field $i lyrics)
    tag="$arm-$sid-$slug"; out="$O/$tag.wav"
    if [ -s "$out" ]; then stamp "$tag exists, skipping"; continue; fi
    settle || exit 1
    case $arm in
      YU) args=(--family yue2 --model "$M/Yue2-3B-GGUF" --threads 8
                --session-option yue2.model_gguf=yue2-3b-bf16.gguf --session-option yue2.vae_gguf=yue2-vae-f32.gguf
                --lyrics "$lyrics" --request-option "style=English, $style" --request-option cot=off) ;;
      MM) args=(--family minimax_music3 --model "$M/MiniMax-Music3-GGUF"
                --session-option minimax_music3.language_model_gguf=language_model_bf16.gguf
                --session-option minimax_music3.rvq_depth_decoder_gguf=rvq_depth_decoder_bf16.gguf
                --session-option minimax_music3.flow_transformer_gguf=transformer_bf16.gguf
                --text "A song with $style." --request-option "lyrics=$lyrics"
                --request-option duration_sec=150 --request-option num_inference_steps=30) ;;
      AS) args=(--family ace_step --model "$M/ACE-Step1.5-GGUF/turbo" --task-route text2music
                --text "$style" --lyrics "$lyrics" --duration-seconds 120) ;;
      *) stamp "unknown arm $arm"; exit 2 ;;
    esac
    stamp "$tag start (GTT $(gtt))"
    ( while :; do gtt; sleep 1; done ) >"$O/$tag.gtt" &
    mon=$!
    t0=$(date +%s.%N); start=$(date -u +%FT%TZ)
    timeout 5400 "$A" --task gen --backend vulkan --seed 7 --metrics --log-file "$O/$tag.log" --out "$out" "${args[@]}" >"$O/$tag.stderr" 2>&1
    rc=$?
    t1=$(date +%s.%N)
    kill "$mon" 2>/dev/null; wait "$mon" 2>/dev/null
    peak=$(sort -n "$O/$tag.gtt" | tail -1)
    dur=none; [ -s "$out" ] && dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out")
    wall=$(echo "$t1 - $t0" | bc)
    printf '%s\t%s\t%s\t%.1f\t%s\t%s\t%s\n' "$arm" "$sid" "$rc" "$wall" "$dur" "$((peak - BASE))" "$start" >>"$TSV"
    stamp "$tag rc=$rc wall=${wall}s audio=${dur}s peakGTT=$((peak - BASE))MiB over base"
    [ "$(ls /var/crash | wc -l)" -ne "$crash0" ] && { stamp "NEW /var/crash entry - stopping"; exit 2; }
  done
done
stamp "E173 renders done"
