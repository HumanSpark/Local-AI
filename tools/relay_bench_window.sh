#!/usr/bin/env bash
# File: relay_bench_window.sh
# Purpose: Open a maintenance window on sparkrouter, run the Qwen3.8 bench legs, close it again.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: bench cannot do this itself - /var/lib/sparkrouter is
# 0750 spark-infer:spark-infer and llama-gateway.service is a systemd USER
# unit under spark-infer, so both the advisory maintenance flag and the unit
# stop need root. Everything else (the bench itself) runs unprivileged as
# bench and is NOT in this script's privileged path.
#
# Uses only the mechanism sparkrouter documents for this: the advisory
# maintenance flag described in README.md invariant 5/5b, set the same way
# ops/gate_b.sh sets it, so the gateway reports 503 "maintenance" with a
# reason instead of looking like an unexplained outage.
#
# Phases (idempotent - re-run the same command after any partial failure):
#   run      down, bench, up - the normal path, restores on ANY exit
#   down     open the window only (flag + stop), leave it open
#   up       close the window only (start + clear flag)
#   status   report current state, change nothing
#
# Restart=on-failure is set on the unit, so the service MUST be stopped via
# systemctl - killing the process would just respawn it.
#
# ⚠ THE SERVING UNIT IS RESOLVED, NEVER NAMED. Since 2026-09-01 production serves from
# llama-gateway-router.service, not llama-gateway.service, and the two CONFLICT - so acting on
# the wrong one does not merely fail, it stops the right one. This script hardcoded the legacy
# name and was measured on 2026-09-04 reporting the serving unit "inactive" while listing the
# four llama-server PIDs that were plainly running. `down` would then have SET THE MAINTENANCE
# FLAG, failed to free the GPU, and hit its own "still running after stop" branch - leaving
# /health claiming maintenance over a fully occupied GPU, the worst of the available states.
# ops/llm_runtime_check.sh in sparkrouter took the same fix on 2026-08-29; this script postdates
# that and never received it.

set -euo pipefail

# Sourcing this file defines its functions and runs NO phase, so the serving-unit resolution can
# be exercised against stubbed systemctl answers without root. Executing behaves exactly as
# before. Added 2026-09-04 with the resolution fix: a guess between two conflicting units is
# worth proving rather than asserting.
_relay_sourced() { [ "${BASH_SOURCE[0]}" != "$0" ]; }

# Ordered most-specific first: the router is what serves today, the plain unit is the rollback
# shape kept for it. Resolution is by liveness, never by which name is written here.
UNIT_CANDIDATES=(llama-gateway-router.service llama-gateway.service)
SI_USER=spark-infer
RUNTIME=/var/lib/sparkrouter
FLAG="$RUNTIME/maintenance"
# `up` runs when NOTHING is active, so liveness cannot answer which unit to start. `down`
# records what it stopped and `up` reads it back. Guessing between two conflicting units is
# exactly the hazard this whole change exists to remove.
UNIT_STATE="$RUNTIME/bench-window.unit"
# Halogen solo (2026-11-07 onward): NO llama-gateway unit serves - sparkrouter-halogen is an idle unit
# below. `down` then records this sentinel, so `up` knows there is no serving unit to start and still
# clears the flag. Before 2026-11-12 it recorded nothing, `up` refused, and /relay/health stayed 503
# "maintenance" after every window until the flag was removed by hand.
NO_SERVING_UNIT=none
# `idle-down` (2026-11-04, owner's call): an idle-box bench needs the WHOLE GPU, and the relay is not the
# only tenant. These spark-infer user units hold GPU memory too (chatterbox-gateway ~5.7 GB on
# 2026-11-04; E153's same-file Halogen arm was killed by the memory guard with it resident). Only the
# ones ACTIVE at `idle-down` are stopped, and each is recorded so `up` restarts exactly those.
# sparkrouter-halogen (2026-11-07): the smart/code tiers' Flash-Next on Halogen pins ~62 GiB; left
# resident, no large-model bench fits. Stopped and restored like the others when active.
IDLE_UNITS=(chatterbox-gateway.service flux-gateway.service sparkrouter-halogen.service)
IDLE_STATE="$RUNTIME/bench-window.idle-units"
BENCH=/home/bench/sparkbench/tools/bench_qwen38.sh
BENCH_TRIPLET=/home/bench/sparkbench/tools/bench_qwen38_triplet.sh
BENCH_KVQUANT=/home/bench/sparkbench/tools/bench_kv_quant.sh
BENCH_USER=bench
LOG=/tmp/sparkbench-qwen38-bench.log

usage() {
    echo "usage: sudo bash /home/bench/sparkbench/tools/relay_bench_window.sh {run|triplet|kvquant|down|idle-down|up|status}" >&2
    exit 2
}

if _relay_sourced; then
    # No phase, no root, no service account needed. A test replaces as_si after sourcing; if it
    # forgets, as_si fails loudly rather than quietly resolving against the real box.
    PHASE=""
    SI_UID=""
else
    [ "$#" -eq 1 ] || usage
    PHASE="$1"

    if [ "$(id -u)" -ne 0 ]; then
        echo "ERROR: must run as root." >&2
        echo "hint: sudo bash /home/bench/sparkbench/tools/relay_bench_window.sh $PHASE" >&2
        exit 1
    fi

    # /home/owner is 0750, so any runuser into a service account inherits a cwd
    # it cannot enter. Every path below is absolute, so this is safe.
    cd /

    SI_UID="$(id -u "$SI_USER")" || { echo "ERROR: no such user $SI_USER" >&2; exit 1; }
fi
export_env=(XDG_RUNTIME_DIR="/run/user/$SI_UID" DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$SI_UID/bus")

as_si() { runuser -u "$SI_USER" -- env "${export_env[@]}" "$@"; }

unit_active() { as_si systemctl --user is-active --quiet "$1"; }

# The unit currently SERVING, or non-zero if none is.
active_unit() {
    local u
    for u in "${UNIT_CANDIDATES[@]}"; do
        if unit_active "$u"; then echo "$u"; return 0; fi
    done
    return 1
}

# Which unit `up` should start. Evidence in order of strength: what `down` recorded, then the
# single ENABLED candidate. If neither answers, REFUSE - naming both is more useful than
# starting the one that conflicts with whatever the operator actually stopped.
unit_for_up() {
    local recorded enabled=() u
    recorded="$(as_si cat "$UNIT_STATE" 2>/dev/null || true)"
    if [ -n "$recorded" ]; then echo "$recorded"; return 0; fi
    for u in "${UNIT_CANDIDATES[@]}"; do
        if as_si systemctl --user is-enabled --quiet "$u" 2>/dev/null; then enabled+=("$u"); fi
    done
    if [ "${#enabled[@]}" -eq 1 ]; then echo "${enabled[0]}"; return 0; fi
    # Zero enabled is the configured state of a box that serves through no llama-gateway unit
    # (Halogen solo): nothing would start at boot either, so there is nothing for `up` to start.
    # Only TWO enabled is ambiguous - those conflict, and a guess can stop the right one.
    if [ "${#enabled[@]}" -eq 0 ]; then echo "$NO_SERVING_UNIT"; return 0; fi
    echo "ERROR: cannot tell which serving unit to start - no record at $UNIT_STATE and" >&2
    echo "       ${#enabled[@]} of ${#UNIT_CANDIDATES[@]} candidates are enabled." >&2
    echo "hint: start the one you actually stopped, as $SI_USER:" >&2
    for u in "${UNIT_CANDIDATES[@]}"; do echo "        systemctl --user start $u" >&2; done
    return 1
}

status() {
    echo "--- sparkrouter window status ($(date -Is)) ---"
    local serving
    if serving="$(active_unit)"; then
        echo "  serving unit    : $serving : ACTIVE (serving)"
    else
        # Say which units were CHECKED. "inactive" against one hardcoded name is what made the
        # 2026-09-04 reading look like a stopped gateway beside four running llama-servers.
        echo "  serving unit    : NONE ACTIVE of: ${UNIT_CANDIDATES[*]}"
    fi
    if [ -e "$FLAG" ]; then
        echo "  maintenance flag: SET -> $(cat "$FLAG" 2>/dev/null)"
    else
        echo "  maintenance flag: clear"
    fi
    # `|| true` is deliberate: pgrep exits 1 when nothing matches, which is the
    # CORRECT state right after `down`. Under `set -euo pipefail` that aborted
    # status() mid-line and made a SUCCESSFUL `down` exit non-zero - harmless
    # interactively, fatal to any script that branches on it (E91, 2026-08-31).
    echo -n "  llama-server processes: "; { pgrep -x llama-server | tr '\n' ' '; } || true; echo
    local u
    for u in "${IDLE_UNITS[@]}"; do
        if unit_active "$u"; then echo "  idle unit       : $u : ACTIVE"; else echo "  idle unit       : $u : inactive"; fi
    done
}

window_down() {
    echo "==> setting advisory maintenance flag"
    # Written AS spark-infer so ownership matches everything else in the
    # runtime zone; root-owned files there are a footgun for the service.
    as_si install -d -m 0750 "$RUNTIME"
    # The reason is a CONSUMED SIGNAL, not a comment: sparkrouter's charter
    # commits to health states of serving / maintenance (flag set, reason
    # included) / down, so SparkCore policy can tell "down for a bench run" from
    # "crashed". A hardcoded reason therefore lies to a consumer rather than
    # merely reading oddly.
    #
    # It used to name one specific 2026 bench - "sparkbench Qwen3.8-27B bench run
    # in progress (see results/model-survey.md pre-registration)" - and was still
    # claiming that on 2026-09-07 during a serving-config change that had nothing
    # to do with a bench. Say who, when and how to clear it, and let the caller
    # override with BENCH_WINDOW_REASON.
    local reason="${BENCH_WINDOW_REASON:-}"
    if [ -z "$reason" ]; then
        reason="maintenance window opened by ${SUDO_USER:-${USER:-unknown}} at $(date -Is) via relay_bench_window.sh - gateway intentionally stopped; restore with 'relay_bench_window.sh up'"
    fi
    # Reason passed as an ARGUMENT, never interpolated into the bash -c string:
    # it carries a timestamp, a username and apostrophes, and nesting it inside
    # the quoted command is the quoting bug this fleet keeps meeting.
    as_si bash -c 'printf "%s\n" "$1" > "$2"' _ "$reason" "$FLAG"
    local unit
    if ! unit="$(active_unit)"; then
        # Two cases look identical here: a second `down` on an open window (a record already
        # exists - keep it, it names the unit that really was stopped) and Halogen solo, where
        # no llama-gateway unit serves at all (no record - write the sentinel so `up` can close).
        if [ -z "$(as_si cat "$UNIT_STATE" 2>/dev/null || true)" ]; then
            as_si bash -c 'printf "%s\n" "$1" > "$2"' _ "$NO_SERVING_UNIT" "$UNIT_STATE"
        fi
        echo "==> no serving unit is active (${UNIT_CANDIDATES[*]}) - nothing to stop"
        return 0
    fi
    # Record BEFORE stopping: after the stop, liveness can no longer answer this question.
    as_si bash -c "printf '%s\n' '$unit' > '$UNIT_STATE'"
    echo "==> stopping $unit"
    as_si systemctl --user stop "$unit" || true
    # Poll rather than assume - the unit has RestartSec=5.
    for _ in $(seq 1 30); do
        pgrep -x llama-server >/dev/null 2>&1 || break
        sleep 1
    done
    if pgrep -x llama-server >/dev/null 2>&1; then
        echo "FAIL: llama-server still running after stop: $(pgrep -x llama-server | tr '\n' ' ')" >&2
        echo "hint: check 'systemctl --user status $unit' as $SI_USER; something outside the unit may have started it" >&2
        return 1
    fi
    echo "==> window OPEN (gateway down, flag set)"
}

# Stop the other GPU tenants, after window_down has stopped the relay. Records BEFORE stopping, for the
# same reason window_down does: afterwards liveness can no longer say what was running.
idle_down() {
    local u stopped=()
    for u in "${IDLE_UNITS[@]}"; do
        unit_active "$u" && stopped+=("$u")
    done
    if [ "${#stopped[@]}" -eq 0 ]; then
        echo "==> no idle unit is active (${IDLE_UNITS[*]}) - nothing else to stop"
        return 0
    fi
    # Units passed as ARGUMENTS, never interpolated into the bash -c string (see window_down).
    as_si bash -c 'printf "%s\n" "${@:2}" > "$1"' _ "$IDLE_STATE" "${stopped[@]}"
    for u in "${stopped[@]}"; do
        echo "==> stopping $u"
        as_si systemctl --user stop "$u" || true
        if unit_active "$u"; then
            echo "FAIL: $u still active after stop" >&2
            echo "hint: systemctl --user status $u, as $SI_USER; 'up' restarts everything recorded in $IDLE_STATE" >&2
            return 1
        fi
    done
    echo "==> idle window OPEN (relay and ${stopped[*]} down)"
}

# Restart exactly the units idle_down recorded. No record = a plain window: nothing to do.
idle_up() {
    local u units
    units="$(as_si cat "$IDLE_STATE" 2>/dev/null || true)"
    [ -n "$units" ] || return 0
    for u in $units; do
        echo "==> starting $u"
        as_si systemctl --user start "$u" || true
        for _ in $(seq 1 60); do
            unit_active "$u" && break
            sleep 1
        done
        if ! unit_active "$u"; then
            echo "FAIL: $u did not come back active." >&2
            echo "hint: journalctl --user -u $u -n 50, as $SI_USER. Record kept at $IDLE_STATE so a re-run of 'up' retries it." >&2
            return 1
        fi
    done
    as_si rm -f "$IDLE_STATE"
}

window_up() {
    local unit
    # The TTS/image units first: they are what a listener notices, and their failure must stop the
    # maintenance flag from being cleared just as a relay failure does.
    idle_up || return 1
    unit="$(unit_for_up)" || return 1
    if [ "$unit" = "$NO_SERVING_UNIT" ]; then
        echo "==> no serving unit to start (none was serving at down; Halogen solo) - idle units restored above"
        echo "==> clearing maintenance flag"
        as_si rm -f "$FLAG"
        as_si rm -f "$UNIT_STATE"
        echo "==> window CLOSED (idle units serving, flag clear)"
        return 0
    fi
    echo "==> starting $unit"
    as_si systemctl --user start "$unit" || true
    for _ in $(seq 1 60); do
        unit_active "$unit" && break
        sleep 1
    done
    if ! unit_active "$unit"; then
        echo "FAIL: $unit did not come back active." >&2
        echo "hint: journalctl --user -u $unit -n 50, as $SI_USER. Maintenance flag left SET on purpose so the gateway reports maintenance rather than a mystery outage." >&2
        return 1
    fi
    echo "==> clearing maintenance flag"
    as_si rm -f "$FLAG"
    as_si rm -f "$UNIT_STATE"
    echo "==> window CLOSED (gateway serving, flag clear)"
}

do_bench_window() {
        local script="$1"
        [ -x "$script" ] || { echo "ERROR: bench script not executable at $script" >&2; exit 1; }
        status
        window_down
        # Restore on ANY exit - success, bench failure, or Ctrl-C.
        trap 'echo "==> restoring relay (trap)"; window_up || echo "WARNING: relay restore FAILED - run the up phase manually" >&2' EXIT INT TERM
        echo
        echo "==> running $(basename "$script") as $BENCH_USER (unprivileged); log: $LOG"
        echo "==> this takes a while; the script reports each leg as it finishes"
        echo
        rc=0
        runuser -u "$BENCH_USER" -- bash "$script" 2>&1 | tee "$LOG" || rc="${PIPESTATUS[0]}"
        chown "$BENCH_USER" "$LOG" 2>/dev/null || true
        echo
        if [ "$rc" -ne 0 ]; then
            echo "BENCH FAILED (rc=$rc) - see $LOG. Relay will still be restored." >&2
        else
            echo "BENCH OK - full output in $LOG"
        fi
        return "$rc"
}

_relay_sourced && return 0

case "$PHASE" in
    status)  status ;;
    down)    window_down; status ;;
    idle-down) window_down && idle_down; status ;;
    up)      window_up;   status ;;
    run)     do_bench_window "$BENCH" ;;
    triplet) LOG=/tmp/sparkbench-qwen38-triplet.log; do_bench_window "$BENCH_TRIPLET" ;;
    kvquant) LOG=/tmp/sparkbench-kvquant.log; do_bench_window "$BENCH_KVQUANT" ;;
    *) usage ;;
esac
