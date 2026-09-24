#!/usr/bin/env bash
# File: tools/fix_router_runpath.sh
# Purpose: Repair the absolute RUNPATH in sparkrouter's llama-server build, then prove it by restarting.
# Project: sparkbench | Date: 2026-09-08
#
# Overview: The 2026-09-07 upgrade copied a build whose RUNPATH is ABSOLUTE and
# points at the tree it was built in (/opt/sparkrouter/llama.cpp-next/build/bin).
# The old build used $ORIGIN, which is relative and survives a copy. Deleting the
# source tree therefore left a binary that resolves its libraries through a path
# that no longer exists - invisible while the process runs, fatal at the next
# restart. A symlink currently stands in for the deleted path; this replaces that
# workaround with the real repair.
#
# WHY COPY-PATCH-RENAME AND NOT patchelf IN PLACE: the running gateway has these
# files memory-mapped. Rewriting a mapped file can hand the live process a SIGBUS.
# A rename leaves the running process on its old inode and points new starts at
# the patched file, so production is never at risk from the edit itself.
#
# THE VERIFICATION REMOVES THE SYMLINK FIRST, on purpose. Testing the patch with
# the workaround still in place would pass whether or not the patch worked - the
# same mistake that hid the original breakage, where a check run from the
# binary's own directory passed because the current directory satisfied it.
#
# Usage, on sparkmax as alastair:
#   sudo bash <this> repair

set -uo pipefail

BIN=/opt/sparkrouter/llama.cpp/build/bin
STAGE=/opt/sparkrouter/llama.cpp-next
RELAY=/usr/local/sbin/relay_bench_window.sh
STAMP=$(date +%Y%m%d-%H%M%S)
BACKUP=/opt/sparkrouter/llama.cpp/build-runpath-prepatch-${STAMP}

FILES="llama-server libllama-server-impl.so libllama.so.0.3.0 libllama-common.so.0.3.0 libmtmd.so.0.3.0 libggml.so.0.22.0 libggml-vulkan.so.0.22.0 libggml-cpu.so.0.22.0"

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
  echo "==> restoring pre-patch binaries"
  for f in $FILES; do
    [ -f "$BACKUP/$f" ] && cp -a "$BACKUP/$f" "$BIN/$f"
  done
  [ -e "$STAGE.disabled" ] && mv "$STAGE.disabled" "$STAGE"
  bash "$RELAY" down >/dev/null 2>&1; bash "$RELAY" up
}

[ "${1:-}" = "repair" ] || { echo "usage: sudo bash $0 repair"; exit 1; }
command -v patchelf >/dev/null || die "patchelf not installed"
[ -d "$BIN" ] || die "$BIN not found"

mkdir -p "$BACKUP" || die "could not create $BACKUP"
# This script runs under sudo, so mkdir creates a ROOT-OWNED directory and the
# agent account cannot clean it up afterwards - it needed a second sudo command
# on 2026-09-08. Hand it to the account that owns everything else here.
chown agent-spark:agent-spark "$BACKUP" 2>/dev/null || true
for f in $FILES; do
  [ -f "$BIN/$f" ] || die "$BIN/$f missing - refusing to patch a partial build"
  cp -a "$BIN/$f" "$BACKUP/$f" || die "backup of $f failed - nothing changed"
done
echo "==> pre-patch copies in $BACKUP"

echo "==> patching RUNPATH to \$ORIGIN (copy, patch, rename - never in place)"
for f in $FILES; do
  cp -a "$BIN/$f" "$BIN/$f.new" || die "copy $f failed"
  if ! patchelf --set-rpath '$ORIGIN' "$BIN/$f.new"; then
    rm -f "$BIN/$f.new"; die "patchelf failed on $f - nothing renamed, build untouched"
  fi
  mv "$BIN/$f.new" "$BIN/$f" || die "rename $f failed"
  printf '    %-32s %s\n' "$f" "$(objdump -x "$BIN/$f" 2>/dev/null | awk '/RUNPATH|RPATH/{print $2; exit}')"
done

# Remove the workaround BEFORE verifying, so the test proves the patch and not
# the symlink standing in for it.
if [ -e "$STAGE" ]; then
  mv "$STAGE" "$STAGE.disabled" || die "could not move $STAGE aside"
  echo "==> symlink workaround moved to $STAGE.disabled"
fi

echo "==> verifying from / - not from the binary's own directory"
if ! (cd / && "$BIN/llama-server" --version >/dev/null 2>&1); then
  echo "binary still cannot resolve its libraries"; restore; die "restored; gateway restarted on the pre-patch build"
fi
(cd / && "$BIN/llama-server" --version 2>&1 | head -1 | sed 's/^/    /')

echo "==> restarting the gateway - this is the proof"
BENCH_WINDOW_REASON="llama-server RUNPATH repair, restart proof (see tools/fix_router_runpath.sh)" \
  bash "$RELAY" down || die "could not stop the gateway; binaries are patched, start it with: $RELAY up"
bash "$RELAY" up || { echo "start FAILED"; restore; die "restored and restarted on the pre-patch build"; }

ok=0
for _ in $(seq 1 36); do
  if health; then ok=1; break; fi
  if ! pgrep -x llama-server >/dev/null; then break; fi
  sleep 5
done
[ "$ok" -eq 1 ] || { echo "health never returned"; restore; die "restored and restarted on the pre-patch build"; }
echo "    health OK"

serves || { echo "up but cannot answer"; restore; die "restored and restarted on the pre-patch build"; }

echo
echo "REPAIR PROVEN. The gateway restarted on a binary with a relative RUNPATH,"
echo "with the symlink workaround removed."
echo "Pre-patch copies kept at $BACKUP"
echo "Disabled workaround at $STAGE.disabled - both removable once you are happy."
