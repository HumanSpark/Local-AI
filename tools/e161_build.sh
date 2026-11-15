#!/usr/bin/env bash
# File: tools/e161_build.sh
# Purpose: Build the two E161 engines - newest llama.cpp mainline (Vulkan) and tandem.cpp (HIP, gfx1151) - unprivileged.
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Phase `mainline` makes a detached worktree llama.cpp/wt/<sha7> at MAINLINE_SHA and builds llama-server,
# llama-bench and llama-imatrix with Vulkan (the E158 configuration). Phase `tandem` clones ewhacc/tandem.cpp into
# var/engines/tandem.cpp at TANDEM_SHA, makes a worktree at the base commit it names (BASE_COMMIT file), applies
# tandem.patch with `git apply --check` first, and builds llama-server and llama-imatrix with HIP for gfx1151 (the
# README documents gfx1100; gfx1151 is untested upstream, so a build or load failure is an E161 result, not a
# reason to change the arm). Logs go to results/e161/. Neither phase touches the GPU or production.
set -euo pipefail
ROOT=/home/bench/sparkbench
LC=$ROOT/llama.cpp
OUT=$ROOT/results/e161
mkdir -p "$OUT"
MAINLINE_SHA=${MAINLINE_SHA:-e574a17b0}
TANDEM_SHA=${TANDEM_SHA:-}
stamp() { printf '%s %s\n' "$(date -u +%FT%TZ)" "$*"; }

mainline() {
  local wt=$LC/wt/${MAINLINE_SHA:0:7}
  [ -d "$wt" ] || git -C "$LC" worktree add --detach "$wt" "$MAINLINE_SHA"
  stamp "mainline $(git -C "$wt" log -1 --format='%H %cs')"
  cd "$wt"
  cmake -B build -DGGML_VULKAN=ON -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF
  timeout 3600 cmake --build build -j 16 --target llama-server llama-bench llama-imatrix
  stamp "mainline built: $(ls build/bin/llama-server build/bin/llama-bench build/bin/llama-imatrix)"
}

tandem() {
  local src=$ROOT/var/engines/tandem.cpp
  [ -d "$src/.git" ] || timeout 300 git clone -q https://github.com/ewhacc/tandem.cpp.git "$src"
  if [ -n "$TANDEM_SHA" ]; then git -C "$src" checkout -q --detach "$TANDEM_SHA"; fi
  stamp "tandem.cpp $(git -C "$src" log -1 --format='%H %cs %s')"
  local base
  base=$(tr -d '[:space:]' < "$src/BASE_COMMIT")
  [ -n "$base" ] || { echo "FAIL: empty BASE_COMMIT. hint: read $src/README.md for the base commit" >&2; exit 1; }
  local wt=$LC/wt/tandem-${base:0:9}
  [ -d "$wt" ] || git -C "$LC" worktree add --detach "$wt" "$base"
  if ! git -C "$wt" diff --quiet; then
    stamp "worktree already patched (diff present) - not re-applying"
  else
    git -C "$wt" apply --check "$src/tandem.patch"
    git -C "$wt" apply "$src/tandem.patch"
    stamp "patch applied: $(git -C "$wt" diff --stat | tail -1)"
  fi
  cd "$wt"
  HIPCXX="$(hipconfig -l)/clang" HIP_PATH="$(hipconfig -R)" \
    cmake -B build -DGGML_HIP=ON -DGGML_HIP_GRAPHS=ON -DGPU_TARGETS=gfx1151 -DCMAKE_BUILD_TYPE=Release -DLLAMA_CURL=OFF
  timeout 5400 cmake --build build -j 16 --target llama-server llama-imatrix
  stamp "tandem built: $(ls build/bin/llama-server build/bin/llama-imatrix)"
}

case "${1:-}" in
  mainline) mainline ;;
  tandem) tandem ;;
  *) echo "usage: bash tools/e161_build.sh {mainline|tandem}   (env MAINLINE_SHA, TANDEM_SHA pin the commits)" >&2; exit 2 ;;
esac
