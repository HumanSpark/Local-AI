#!/usr/bin/env bash
# File: tools/upgrade_router_llama_binary.sh
# Purpose: Swap sparkrouter's llama-server build to the newer one, with acceptance test and rollback.
# Project: sparkbench | Date: 2026-09-07
#
# Overview: Operator script, STEP 1 OF 2. It swaps the binary ONLY and changes
# no configuration, so the upgrade risk is isolated from the flag change. Step 2
# is tools/apply_reasoning_effort_medium.sh, which now pre-flights the binary and
# will pass once this has run.
#
# WHY TWO STEPS: on 2026-09-07 08:03 a compound change (add a flag the binary did
# not support) took the gateway down for 5m05s. Splitting them means each has one
# suspect.
#
# WHAT IS BEING SWAPPED
#   from  /opt/sparkrouter/llama.cpp/build       build  9865, commit 067de9371, 2026-07-03
#   to    /opt/sparkrouter/llama.cpp-next/build  build 10712, commit daef7b687, 2026-08-31
#
# Both were configured from the SAME cmake settings, read out of production's own
# CMakeCache.txt: Release, shared libs, ccache, Vulkan on, native on, curl off, no
# CUDA/HIP/RPC. Both bin/ directories hold 23 files. RUNPATH is $ORIGIN, so a
# build directory is relocatable and a swap is safe.
#
# STATICALLY VERIFIED BEFORE WRITING THIS: every flag the unit passes -
# --models-preset, --models-max, --jinja, --no-webui, --host, --port, -c, -fa,
# -ctk, -ctv, -ub - exists in the new build's help, and --reasoning-effort exists
# in the new and not the old. What CANNOT be checked without running it is preset
# parsing, model loading and template behaviour, which is what the acceptance test
# below is for.
#
# THIS IS A TWO-MONTH JUMP in the runtime serving three production models. It can
# change behaviour beyond the flag - chat templates and tool calling are the usual
# movers - and by F57's class it invalidates comparisons against figures measured
# on the old gateway.
#
# Usage, on sparkmax as alastair:
#   sudo bash <this> upgrade    - swap, restart, acceptance test, roll back on failure
#   sudo bash <this> rollback   - restore the previous build and restart

set -uo pipefail

ROOT=/opt/sparkrouter
CUR="$ROOT/llama.cpp/build"
NEXT="$ROOT/llama.cpp-next/build"
RELAY=/usr/local/sbin/relay_bench_window.sh
STAMP=$(date +%Y%m%d-%H%M%S)
KEEP="$ROOT/llama.cpp/build-pre-upgrade-${STAMP}"

die() { printf 'FATAL: %s\n' "$*" >&2; exit 1; }

health() {
  python3 - <<'PY'
import sys, urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:8400/health", timeout=10) as r:
        sys.exit(0 if r.status == 200 else 1)
except Exception:
    sys.exit(1)
PY
}

# A real request through the router, not just a liveness ping. A gateway that is
# up but cannot answer is the vacuous-success shape this fleet keeps meeting.
serves() {
  python3 - <<'PY'
import json, sys, urllib.request
body = {"model": "local_smart",
        "messages": [{"role": "user", "content": "Reply with the single word: ok"}],
        "temperature": 0, "max_tokens": 32}
try:
    req = urllib.request.Request("http://127.0.0.1:8400/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        d = json.loads(r.read().decode())
    txt = (d["choices"][0]["message"].get("content") or "").strip()
    print(f"  served: {txt[:60]!r}")
    sys.exit(0 if txt else 1)
except Exception as e:
    print(f"  serve FAILED: {type(e).__name__}: {e}")
    sys.exit(1)
PY
}

restore() {
  rm -rf "$CUR"
  mv "$KEEP" "$CUR" || die "ROLLBACK FAILED - $KEEP could not be restored. Gateway is DOWN."
  bash "$RELAY" down >/dev/null 2>&1; bash "$RELAY" up
}

case "${1:-}" in
upgrade)
  [ -x "$NEXT/bin/llama-server" ] || die "$NEXT/bin/llama-server not found - build it first"
  [ -d "$CUR" ] || die "$CUR not found"
  grep -q -- "--reasoning-effort" <("$NEXT/bin/llama-server" --help 2>&1) \
    || die "the new binary does not support --reasoning-effort; refusing a pointless upgrade"

  echo "current : $("$CUR/bin/llama-server" --version 2>&1 | head -1)"
  echo "new     : $("$NEXT/bin/llama-server" --version 2>&1 | head -1)"

  echo "==> stopping the gateway"
  BENCH_WINDOW_REASON="llama.cpp runtime upgrade in progress (067de9371 -> daef7b687) - see tools/upgrade_router_llama_binary.sh" \
    bash "$RELAY" down || die "could not stop the gateway; nothing has been swapped"

  # RUNPATH GUARD, added 2026-09-08 after this bit me. cmake bakes an ABSOLUTE
  # RUNPATH pointing at the build tree - /opt/sparkrouter/llama.cpp-next/build/bin
  # - not the $ORIGIN the old build used. Copy the directory elsewhere and the
  # binary still resolves its libraries through the ORIGINAL path, so deleting
  # the source tree leaves a binary that runs only from its own directory (the
  # trailing colon in RUNPATH adds cwd) and fails under systemd. The running
  # process survives on its mappings, so the breakage is INVISIBLE until the
  # next restart.
  rp=$("$(command -v objdump)" -x "$NEXT/bin/llama-server" 2>/dev/null | awk '/RUNPATH|RPATH/{print $2; exit}')
  case "$rp" in
    ""|'$ORIGIN'*) : ;;
    *) echo "WARNING: the new binary's RUNPATH is $rp"
       echo "         It is absolute and points at the build tree. After the swap the"
       echo "         source tree must NOT be deleted, or set it to \$ORIGIN first:"
       echo "           patchelf --set-rpath '\$ORIGIN' <each .so and the binary>"
       echo "         Continuing - this is a warning, not a refusal." ;;
  esac

  echo "==> swapping the build directory"
  mv "$CUR" "$KEEP" || die "could not move $CUR aside; nothing changed. Start the gateway with: $RELAY up"
  cp -a "$NEXT" "$CUR" || { mv "$KEEP" "$CUR"; bash "$RELAY" up; die "copy failed; original restored and gateway started"; }
  chown -R agent-spark:agent-spark "$KEEP" 2>/dev/null || true
  echo "    previous build kept at $KEEP"

  echo "==> starting the gateway"
  bash "$RELAY" up || { echo "start failed - rolling back"; restore; die "rolled back to the previous build"; }

  echo "==> acceptance: health"
  ok=0
  for _ in $(seq 1 24); do
    if health; then ok=1; break; fi
    if ! pgrep -x llama-server >/dev/null; then break; fi
    sleep 5
  done
  if [ "$ok" -ne 1 ]; then
    echo "health did not return - rolling back"; restore; die "rolled back to the previous build"
  fi
  echo "    health OK"

  echo "==> acceptance: a real request through the router"
  if ! serves; then
    echo "the gateway is up but cannot answer - rolling back"; restore; die "rolled back to the previous build"
  fi

  echo
  echo "UPGRADE COMPLETE. Previous build kept at $KEEP"
  echo "Next: sudo bash /home/agent-spark/sparkbench/tools/apply_reasoning_effort_medium.sh apply"
  ;;

rollback)
  last=$(ls -1dt "$ROOT"/llama.cpp/build-pre-upgrade-* 2>/dev/null | head -1)
  [ -n "$last" ] || die "no build-pre-upgrade-* directory found"
  echo "restoring $last"
  bash "$RELAY" down >/dev/null 2>&1
  rm -rf "$CUR"; mv "$last" "$CUR" || die "restore failed - gateway is DOWN"
  bash "$RELAY" up
  health && echo "health OK" || echo "WARNING: health not OK after rollback"
  ;;
*)
  echo "usage: sudo bash $0 {upgrade|rollback}"; exit 1 ;;
esac
