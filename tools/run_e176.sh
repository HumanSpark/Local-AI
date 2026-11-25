#!/usr/bin/env bash
# File: tools/run_e176.sh
# Purpose: Run E176 end to end - verify the Ling-3.2-air shards, speed leg, then the E167 bank as arm LG.
# Project: sparkbench | Date: 2026-11-24
#
# Overview: results/e176-prereg.md. Checks both Q3_K_M shards against the manifest sha256 (refuses on mismatch), runs
# tools/run_e176_speed.sh (stops E176 on any non-zero rc: DeviceLost means reboot first, F193), then
# tools/run_e154_arms.sh LG with E167's bank settings (3,600 s/task, podman). Each leg restores and verifies the relay.
set -u
REPO=/home/bench/sparkbench
D=/opt/models/staging/ling-3.2-air
cd "$REPO" || exit 1
stamp() { echo "[$(date -Is)] $*" | tee -a results/e176/run.log; }
check() {
  local got; got=$(sha256sum "$D/$1" | cut -d' ' -f1)
  [ "$got" = "$2" ] || { stamp "FATAL sha256 $1 = $got, manifest says $2; hint: re-fetch"; exit 3; }
  stamp "sha256 OK $1"
}
check Ling-3.2-air-Q3_K_M-00001-of-00002.gguf e071f035602ea1353d8d1808c4bd206bc0b1892ed2257b4c8c19629aa56830f0
check Ling-3.2-air-Q3_K_M-00002-of-00002.gguf c634a2a299518de0fc14ee5eb70606abd49f835c5fbc3980a60ec227795a8a2a
stamp "speed leg start"
tools/run_e176_speed.sh; rc=$?
stamp "speed leg rc=$rc"
[ $rc -eq 0 ] || exit $rc
stamp "bank leg start (arm LG, E167 bank)"
E154_BANK=results/e167/bank.jsonl E154_RAW=results/e176/raw E154_LEDGER_DIR=results/e176 E154_TASKDIR=var/e176-tasks \
  E154_TASK_TIMEOUT=3600 E154_ISOLATE=podman E154_TAG=e176 tools/run_e154_arms.sh LG; rc=$?
stamp "bank leg rc=$rc"
exit $rc
