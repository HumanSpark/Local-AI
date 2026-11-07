#!/usr/bin/env bash
# File: tools/run_e154_arms.sh
# Purpose: Run E154 arms over the 15-task bank - Sonnet via OpenRouter under the $25 ledger, local engines in an idle window.
# Project: sparkbench | Date: 2026-11-04
#
# Overview: Splits results/e154/bank.jsonl into one task file per line, then for each arm runs
# tools/coding_harness.py --task on every task in bank order and writes results/e154/raw/<arm>/<task>.json.
# Arm S (anthropic/claude-sonnet-5.5) needs no GPU: OpenRouter key from the vault by exit code, provider pinned to
# Anthropic, thinking on, prompt cache on, CostLedger ceiling $25 (a BudgetExceeded stops the arm, it is not retried).
# Local arms H Q T27 TL open ONE idle window (relay_bench_window.sh idle-down), start each engine on 127.0.0.1:8154,
# wait for /v1/models, run the bank, stop the engine; the EXIT trap restores and VERIFIES the relay. After each arm the
# raw directory is committed and pushed (bank both sides). Prereg: results/e154-prereg.md (written before any arm).
#
# E156 (2026-11-05): arm O = Opus 5.5 (same route and body as S, own ledger); env E154_ISOLATE=podman runs every
# task in the harness's isolation container (F182); E154_TASK_TIMEOUT sets the per-task budget (default 1200 s);
# E154_LEDGER_DIR holds the cloud ledgers. All default to E154's behaviour, which the capability index relies on.
#
# E158 (2026-11-06): newer local candidates on the frozen E156 bank - OR35 Ornith-1.5-35B-A3B Q8_0, OR122 Ornith-1.5-122B
# Q5_K_M, TS45 Tess-4.5-27B Q8_0 + its MTP draft head, TS4 Tess-4-35B-A3B Q8_0 (no speculation: the card's draft-mtp
# runtime is a fork), all on upstream llama.cpp e14a779; RA Raon-1-mini Q8_0 on KRAFTON's fork fb89566 (arch raon1 is
# not upstream). Card sampling. After ready, GPU memory in use is logged as the offload evidence.
#
# Usage: tools/run_e154_arms.sh [--dry-run] ARM [ARM ...]    ARM in S O H Q QN T27 TL OR35 OR122 TS45 TS4 RA

set -u
REPO=/home/bench/sparkbench
WINDOW=/usr/local/sbin/relay_bench_window.sh
M=/opt/models/staging
ENG=$REPO/var/engines
# Overridable so tools/capability_index.sh reuses this runner on its own month directory and bank.
RAW=${E154_RAW:-$REPO/results/e154/raw}
BANK=${E154_BANK:-$REPO/results/e154/bank.jsonl}
NOBANK=${E154_NOBANK:-0}   # 1 = caller commits (the secret gate blocks raw transcripts; see tools/strip_task_transcripts.py)
LOG=$RAW/window.log
TASKDIR=${E154_TASKDIR:-$REPO/var/e154-tasks}
PORT=8154
URL=http://127.0.0.1:$PORT
HALO=$M/halogen-qwen3.8-flash-next-v2
HALO_IMAGE=ghcr.io/peonist-ai/halogen-flash-server@sha256:b53c96edc042b1d9570cda2771c5002527f94d6aca0c8704a4475aa621d355ff
LLAMA=$REPO/llama.cpp/wt/5851a8e/build/bin/llama-server
CODER=$M/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf
CODER_NEXT=$M/Qwen3-Coder-Next-Q4_K_M.gguf   # arm QN, prereg amendment 4
LLAMA_NEW=$REPO/llama.cpp/wt/e14a779/build/bin/llama-server   # E158, upstream 2026-11-06
LLAMA_RAON=$REPO/llama.cpp/wt/raon-fb89566/build/bin/llama-server   # E158 arm RA, KRAFTON fork
TALUS=$ENG/talus-v0.1.3/talus-v0.1.3-linux-x86_64-gfx1151
T27_CFG=$REPO/results/e154/talus-27b.json
TL_CFG=$REPO/results/e154/talus-laguna.json
LEDGER_DIR=${E154_LEDGER_DIR:-$REPO/results/e154}
ISOLATE=${E154_ISOLATE:-podman}  # fail closed: 'none' runs agent shell on the host (F182)
TASK_TIMEOUT=${E154_TASK_TIMEOUT:-1200}
ledger_for() { case "$1" in S) echo "$LEDGER_DIR/sonnet-ledger.jsonl" ;; O) echo "$LEDGER_DIR/opus-ledger.jsonl" ;; esac; }
SONNET_BODY='{"usage":{"include":true},"reasoning":{"max_tokens":8000},"max_tokens":16000,"provider":{"order":["Anthropic"],"allow_fallbacks":false}}'

DRY=0
ARMS=()
for a in "$@"; do
  case "$a" in
    --dry-run) DRY=1 ;;
    S|O|H|Q|QN|T27|TL|OR35|OR122|TS45|TS4|RA) ARMS+=("$a") ;;
    *) echo "unknown arg $a. hint: tools/run_e154_arms.sh [--dry-run] S H Q T27 TL"; exit 2 ;;
  esac
done
[ ${#ARMS[@]} -eq 0 ] && { echo "name at least one arm. hint: tools/run_e154_arms.sh S"; exit 2; }

mkdir -p "$RAW" "$TASKDIR"
cd "$REPO" || exit 1
stamp() { printf '[%s] %s\n' "$(date -Is)" "$*" | tee -a "$LOG"; }

# One task file per bank line, in bank order.
mapfile -t TASK_IDS < <(python3 -c "
import json
for line in open('$BANK'):
    t = json.loads(line)
    json.dump(t, open('$TASKDIR/' + t['id'] + '.json', 'w'))
    print(t['id'])
")
N_BANK=$(grep -c . "$BANK")
[ ${#TASK_IDS[@]} -eq "$N_BANK" ] && [ "$N_BANK" -gt 0 ] || { stamp "FATAL: split ${#TASK_IDS[@]} tasks from $N_BANK bank lines in $BANK"; exit 1; }

sampling() {  # vendor sampling per arm (Talus MODELS.md table; Qwen3-Coder card; Anthropic needs 1.0 with thinking)
  case "$1" in
    S|O) echo '{"temperature":1.0}' ;;
    H) echo '{"temperature":1.0,"top_p":0.95,"top_k":20,"min_p":0}' ;;
    Q) echo '{"temperature":0.7,"top_p":0.8,"top_k":20}' ;;
    QN) echo '{"temperature":1.0,"top_p":0.95,"top_k":40}' ;;   # Qwen3-Coder-Next card
    T27) echo '{"temperature":0.8,"top_p":0.95,"top_k":40,"min_p":0.05}' ;;
    TL) echo '{"temperature":1.0,"top_p":1.0,"top_k":20,"min_p":0}' ;;
    OR35|OR122) echo '{"temperature":0.6,"top_p":0.95,"top_k":20}' ;;   # Ornith cards: precise coding
    TS45|TS4) echo '{"temperature":1.0,"top_p":0.95,"top_k":20}' ;;     # Tess-4.5 card (Tess-4 card states none)
    RA) echo '{"temperature":1.0,"top_p":0.95,"top_k":20,"min_p":0,"presence_penalty":0}' ;;   # Raon card, coding
  esac
}

arm_args() {  # per-arm harness flags. TL: Talus's Laguna path refuses a request with no max_tokens (its default
  # max_new = context - prompt then fails its own "exceeds the context" check, 2026-11-04 smoke); 32768 never binds a turn.
  case "$1" in
    TL) printf '%s\n' --extra-body '{"max_tokens":32768}' ;;
  esac
}

SERVER_PID=""
WINDOW_OPEN=0
stop_engines() {
  # llama-server IGNORES SIGTERM once idle (2026-11-04: the Q smoke's server outlived its window by 30 min, so the
  # next idle-down refused and pgrep mistook it for the relay). Escalate to SIGKILL and prove our engines are gone.
  [ -n "$SERVER_PID" ] && kill "$SERVER_PID" 2>/dev/null
  SERVER_PID=""
  podman ps -q --filter name=e154- | xargs -r podman stop -t 20 >/dev/null 2>&1
  pkill -u "$(id -u)" -x 'llama-server|talus-server|talus-cli' 2>/dev/null
  local i
  for i in $(seq 1 15); do pgrep -u "$(id -u)" -x 'llama-server|talus-server|talus-cli' >/dev/null || break; sleep 2; done
  if pgrep -u "$(id -u)" -x 'llama-server|talus-server|talus-cli' >/dev/null; then
    stamp "engine ignored SIGTERM for 30 s; SIGKILL $(pgrep -u "$(id -u)" -x 'llama-server|talus-server|talus-cli' | xargs)"
    pkill -9 -u "$(id -u)" -x 'llama-server|talus-server|talus-cli' 2>/dev/null
    sleep 3
  fi
  if pgrep -u "$(id -u)" -x 'llama-server|talus-server|talus-cli' >/dev/null; then stamp "FATAL: our engine survived SIGKILL"; return 1; fi
  return 0
}
relay_serving() { sudo -n "$WINDOW" status 2>/dev/null | grep -q 'ACTIVE (serving)'; }
cleanup() {
  # Only a run that opened the window owns engines. A cloud-only run (S/O) must not pkill a concurrent local run's
  # engine when it exits (E156 runs cloud and local arms side by side).
  [ "$WINDOW_OPEN" -eq 1 ] && stop_engines
  if [ "$WINDOW_OPEN" -eq 1 ]; then
    sudo "$WINDOW" up 2>&1 | tee -a "$LOG"
    if relay_serving; then stamp "relay restored, VERIFIED: status reports the gateway ACTIVE (serving)"
    else stamp "WARNING: relay NOT serving after 'up' - run: sudo $WINDOW up, then $WINDOW status"; fi
  fi
}
trap cleanup EXIT

start() {
  local arm=$1 slog=$2
  local podman_gpu=(--device /dev/kfd --device /dev/dri --group-add keep-groups --ipc=host --ulimit memlock=-1:-1)
  case "$arm" in
    H)
      podman run -d --rm --name e154-H "${podman_gpu[@]}" -p "127.0.0.1:$PORT:8731" \
        -v "$HALO:/models:ro" "$HALO_IMAGE" >>"$slog" 2>&1
      (podman logs -f e154-H >>"$slog" 2>&1 &) ;;
    Q)
      "$LLAMA" -m "$CODER" -c 131072 -fa on -ngl 999 --jinja --host 127.0.0.1 --port "$PORT" --no-webui >"$slog" 2>&1 &
      SERVER_PID=$! ;;
    QN)
      "$LLAMA" -m "$CODER_NEXT" -c 131072 -fa on -ngl 999 --jinja --host 127.0.0.1 --port "$PORT" --no-webui >"$slog" 2>&1 &
      SERVER_PID=$! ;;
    T27) "$TALUS/bin/talus-server" --config "$T27_CFG" --host 127.0.0.1 --port "$PORT" >"$slog" 2>&1 & SERVER_PID=$! ;;
    TL) "$TALUS/bin/talus-server" --config "$TL_CFG" --host 127.0.0.1 --port "$PORT" >"$slog" 2>&1 & SERVER_PID=$! ;;
    OR35|OR122|TS45|TS4|RA)
      local bin=$LLAMA_NEW gguf extra=()
      case "$arm" in
        OR35) gguf=$M/ornith-1.5-35b-a3b/Ornith-1.5-35B-Q8_0.gguf ;;
        OR122) gguf=$M/ornith-1.5-122b/Ornith-1.5-122B-Q5_K_M.gguf ;;
        TS45) gguf=$M/tess-4.5-27b/Tess-4.5-27B-Q8_0.gguf
              extra=(-md "$M/tess-4.5-27b/mtp-Tess-4.5-27B-Q8_0.gguf" --spec-type draft-mtp -ngld 999) ;;
        TS4) gguf=$M/tess-4-35b-a3b/Tess-4-35B-A3B-Q8_0-MTP-Q4D-Q4H-PV64K.gguf ;;
        RA) bin=$LLAMA_RAON; gguf=$M/raon-1-mini-preview/raon-1-mini-preview-Q8_0.gguf ;;
      esac
      "$bin" -m "$gguf" "${extra[@]}" -c 131072 -fa on -ngl 999 --jinja --host 127.0.0.1 --port "$PORT" --no-webui >"$slog" 2>&1 &
      SERVER_PID=$! ;;
  esac
}

wait_ready() {
  local t id
  for t in $(seq 1 180); do
    id=$(python3 -c "import json,urllib.request;print(json.load(urllib.request.urlopen('$URL/v1/models',timeout=5))['data'][0]['id'])" 2>/dev/null) && { echo "$id"; return 0; }
    sleep 5
  done
  return 1
}

bank_arm() {  # commit + push one arm's raw results (bank both sides)
  local arm=$1
  [ "$NOBANK" = 1 ] && { stamp "arm $arm: banking left to the caller (E154_NOBANK=1)"; return 0; }
  git -C "$REPO" add "$RAW/$arm" "$LOG" 2>/dev/null
  local ledger; ledger=$(ledger_for "$arm")
  [ -n "$ledger" ] && git -C "$REPO" add "$ledger"
  git -C "$REPO" commit -q -m "data(e154): arm $arm raw results ($(ls "$RAW/$arm"/*.json 2>/dev/null | wc -l) task files)" -- "$RAW/$arm" "$LOG" $ledger \
    && git -C "$REPO" push -q && stamp "banked arm $arm: $(git -C "$REPO" log --oneline -1)" \
    || stamp "WARNING: banking arm $arm failed - commit by hand before the next session"
}

run_bank() {  # run_bank <arm> <model id> <endpoint> [extra harness args...]
  local arm=$1 model=$2 endpoint=$3; shift 3
  mkdir -p "$RAW/$arm"
  local id rc k=0
  for id in "${TASK_IDS[@]}"; do
    k=$((k + 1))
    if [ -s "$RAW/$arm/$id.json" ]; then stamp "$arm $k/$N_BANK $id: already done, skipped"; continue; fi
    timeout $((TASK_TIMEOUT + 600)) python3 tools/coding_harness.py "$model" --task "$TASKDIR/$id.json" --endpoint "$endpoint" \
      --timeout "$TASK_TIMEOUT" --isolate "$ISOLATE" --sampling "$(sampling "$arm")" --output "$RAW/$arm/$id.json" "$@" >>"$RAW/$arm/harness.log" 2>&1
    rc=$?
    stamp "$arm $k/$N_BANK $id: rc=$rc $(python3 -c "import json;r=json.load(open('$RAW/$arm/$id.json'));print(r['status'],'turns',r['turns'],'wall',round(r['wall_time']),'s cost',round(r['usage']['cost_usd'],4))" 2>&1 | tail -1)"
    if { [ "$arm" = S ] || [ "$arm" = O ]; } && grep -q BudgetExceeded "$RAW/$arm/harness.log"; then stamp "S: budget ceiling reached - arm stops here"; break; fi
  done
}

for a in "${ARMS[@]}"; do stamp "arm requested: $a"; done
[ "$DRY" -eq 1 ] && { stamp "dry run: ${#TASK_IDS[@]} tasks split to $TASKDIR"; exit 0; }

for arm in "${ARMS[@]}"; do
  if [ "$arm" = S ] || [ "$arm" = O ]; then
    [ "$arm" = S ] && cmodel=anthropic/claude-sonnet-5.5 || cmodel=anthropic/claude-opus-5.5
    ledger=$(ledger_for "$arm"); mkdir -p "$(dirname "$ledger")"
    ORK="$(python3 /opt/vault/tools/vault_get.py SPARKBENCH_OPENROUTER_API_KEY)" || { stamp "FATAL: vault read failed"; exit 1; }
    export ORK
    stamp "$arm start ($cmodel, isolate $ISOLATE); ledger spent so far \$$(python3 -c "import sys;sys.path.insert(0,'tools');from coding_harness import CostLedger;print(round(CostLedger('$ledger',25).spent(),4))")"
    run_bank "$arm" "$cmodel" https://openrouter.ai/api/v1 --api-key env:ORK \
      --usd-ceiling 25 --ledger "$ledger" --prompt-cache --extra-body "$SONNET_BODY"
    unset ORK
    bank_arm "$arm"
    continue
  fi
  if [ "$WINDOW_OPEN" -eq 0 ]; then
    stop_engines || exit 1   # clear our own leftovers first
    stamp "=== opening idle window ==="
    WINDOW_OPEN=1   # set BEFORE the call: a half-done idle-down must still be restored
    sudo "$WINDOW" idle-down 2>&1 | tee -a "$LOG"
    if pgrep -x llama-server >/dev/null; then stamp "FATAL: llama-server still running after idle-down"; exit 1; fi
    stamp "window open, VERIFIED: no llama-server; kernel $(uname -r); GPU busy $(cat /sys/class/drm/card0/device/gpu_busy_percent)%"
  fi
  slog=$RAW/$arm.serverlog
  stamp "$arm start"
  t0=$(date +%s)
  start "$arm" "$slog"
  if ! model=$(wait_ready); then stamp "FAIL $arm: not ready after 900 s"; stop_engines; continue; fi
  stamp "$arm ready in $(( $(date +%s) - t0 ))s, model '$model'; GPU memory in use: VRAM $(( $(cat /sys/class/drm/card0/device/mem_info_vram_used) >> 20 )) MiB, GTT $(( $(cat /sys/class/drm/card0/device/mem_info_gtt_used) >> 20 )) MiB (offload evidence)"
  mapfile -t extra < <(arm_args "$arm")
  run_bank "$arm" "$model" "$URL/v1" "${extra[@]}"
  stop_engines
  bank_arm "$arm"
done
stamp "=== arms done: ${ARMS[*]} ==="
