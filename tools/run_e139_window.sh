#!/usr/bin/env bash
# File: run_e139_window.sh
# Purpose: Run every E139 arm in one unattended GPU window, in pre-registered order.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: Refuses to start unless the GPU is demonstrably free: no llama-server, no running
# container, and amdgpu GTT used under 4 GiB (the gateway must already be down via
# `sudo bash tools/relay_bench_window.sh down` - Rule 9). Then runs, each via
# tools/e139_speed.py with a per-arm mem_guard at 12 GiB:
#   H0     halogen 0.13.8 (by digest), own checkpoint + quality sidecar, image defaults - block 1
#   H0-id  same, HALOGEN_PROMPT_CACHE=0 - block 2, serial vs MTP byte compare
#   H0s    same as H0 with the overlay-speed sidecar - labelled extra
#   G0     halogen on our unsloth UD-IQ4_XS GGUF + mtp.hgn head - engine-vs-engine on one file
#   L0     mainline llama.cpp daef7b6 llama-server on the same GGUF - E91's build and KV types
#   bench  the image's own `bench` and `sweep` modes on H0's checkpoint - recorded, NOT scored
# Each step logs its rc and the window carries on past a failed arm. Arms and predictions:
# results/e139-prereg.md. Usage: tools/run_e139_window.sh [arm...]  (default: all, in order)

set -uo pipefail

ROOT=/home/agent-spark/sparkbench
OUT=$ROOT/results/e139
M=/opt/models/staging
HALO=$M/halogen-qwen3.8-flash-next
GGUF=Qwen3.8-Flash-Next-UD-IQ4_XS-00001-of-00003.gguf
IMAGE=ghcr.io/peonist-ai/halogen-flash-server@sha256:6e626c979d536ab1edb07898e278be6686afd353758ea268817457f801d687dd
MBIN=$ROOT/llama.cpp/wt/daef7b6/build/bin
GUARD_SH=$ROOT/qwen-image/mem_guard.sh
LOG=$OUT/window.log
ARMS=("${@:-H0 H0-id H0s G0 L0 bench}")
ARMS=(${ARMS[*]})

cd "$ROOT" || exit 1
mkdir -p "$OUT"
say() { printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }

GUARD=""
guarded() {  # guarded <label> <guard-target> <command...> - run under mem_guard, record rc, never abort
    local label=$1 target=$2; shift 2
    "$GUARD_SH" "$target" 12 >> "$OUT/mem_guard.log" 2>&1 &
    GUARD=$!
    say "START $label"
    "$@" >> "$OUT/$label.stdout" 2>&1
    local rc=$?
    say "END   $label rc=$rc"
    kill "$GUARD" 2>/dev/null; GUARD=""
    # `timeout` SIGTERMs python, which skips its finally: free the GPU here or the next arm is contended.
    if [ "${target#proc:}" = "$target" ]; then
        podman ps -q --filter "name=^${target}\$" | xargs -r podman stop -t 10 > /dev/null
    else
        pkill -x "${target#proc:}"
    fi
    return 0
}

# Positive check that the GPU is free, not just that a name is absent.
gtt=$(( $(cat /sys/class/drm/card0/device/mem_info_gtt_used) / 1073741824 ))
running=$(podman ps -q | wc -l)
if pgrep -x llama-server > /dev/null || [ "$running" -ne 0 ] || [ "$gtt" -ge 10 ]; then
    say "REFUSED: GPU not free (llama-server=$(pgrep -xc llama-server), containers=$running, GTT used ${gtt} GiB)." \
        "hint: sudo bash $ROOT/tools/relay_bench_window.sh down"
    exit 2
fi
say "window open: baseline GTT+VRAM $(( ($(cat /sys/class/drm/card0/device/mem_info_gtt_used) + $(cat /sys/class/drm/card0/device/mem_info_vram_used)) / 1048576 )) MiB (Chatterbox TTS resident, amendment 2), kernel $(uname -r), livepatch '$(canonical-livepatch status 2>/dev/null | grep -m1 -i 'kernel:' | xargs)'," \
    "iommu $(cat /sys/kernel/iommu_groups/0/type), GTT used ${gtt} GiB, arms ${ARMS[*]}"
# Armed only AFTER the GPU-free check: a refusal means the gateway may be up, and this trap's blanket
# pkill of llama-server would kill production.
trap 'kill $GUARD 2>/dev/null; pkill -x llama-server; podman ps -q --filter name=e139- | xargs -r podman stop -t 10' EXIT

sp() {  # sp <label> <e139_speed args...> - bounded at 1 h; called inside guarded, so a function is fine
    local l=$1; shift
    timeout 3600 python3 -u tools/e139_speed.py --label "$l" --out "$OUT/speed-$l.json" "$@"
}

for arm in "${ARMS[@]}"; do case $arm in
H0)    guarded speed-H0 e139-H0 sp H0 --engine halogen -v "$HALO:/models:ro" ;;
H0-id) guarded speed-H0-id e139-H0-id sp H0-id --engine halogen --identity \
           -v "$HALO:/models:ro" -e HALOGEN_PROMPT_CACHE=0 ;;
H0s)   guarded speed-H0s e139-H0s sp H0s --engine halogen -v "$HALO:/models:ro" \
           -e HALOGEN_CK_OVERLAY=/models/qwen38-flash-next-w4b.overlay-speed.hgn ;;
G0)    guarded speed-G0 e139-G0 sp G0 --engine halogen -v "$M:/models:ro" \
           -v "$HALO/tokenizer:/tokenizer:ro" -e "HALOGEN_CHECKPOINT=/models/$GGUF" \
           -e HALOGEN_MTP_HEAD=/models/halogen-qwen3.8-flash-next/qwen38-flash-next-mtp.hgn ;;
G0m)   guarded speed-G0m e139-G0m sp G0m --engine halogen -v "$M:/models:ro" \
           -v "$HALO/tokenizer:/tokenizer:ro" -e "HALOGEN_CHECKPOINT=/models/$GGUF" \
           -e HALOGEN_MTP_HEAD=/models/halogen-qwen3.8-flash-next/qwen38-flash-next-mtp.hgn \
           -e HALOGEN_MAX_TOK=16384 ;;
L0)    guarded speed-L0 proc:llama-server sp L0 --engine llama \
           --server-bin "$MBIN/llama-server" --model "$M/$GGUF" ;;
bench) for mode in "bench serial,mtp 256 low 3" "sweep -p 8192,32768 -n 128"; do
           name=builtin-${mode%% *}
           # shellcheck disable=SC2086  # mode is deliberately word-split into the image's argv
           guarded "$name" "e139-$name" timeout 3600 podman run --rm --name "e139-$name" \
               --device /dev/kfd --device /dev/dri --group-add keep-groups --ipc=host \
               --ulimit memlock=-1:-1 -v "$HALO:/models:ro" "$IMAGE" $mode
       done ;;
*)     say "unknown arm $arm"; exit 2 ;;
esac; done
say "WINDOW DONE - close it with: sudo bash $ROOT/tools/relay_bench_window.sh up"
