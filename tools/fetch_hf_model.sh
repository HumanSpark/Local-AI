#!/usr/bin/env bash
# File: fetch_hf_model.sh
# Purpose: Resumable, size-verified download of HF model file(s) to staging.
# Project: sparkbench | Date: 2026-07-03
#
# Overview: Generalisation of fetch_gpt_oss_120b.sh (third scripted fetch -
# abstraction earned per the three-times rule). Fetches one or more files
# from a HuggingFace repo's main revision into /opt/models/staging with curl
# resume (-C -). A file counts as done only when its byte count equals the
# authoritative size passed by the caller (pinned from the HF API at
# manifest time - see manifests/MANIFEST.md and the fleet rule
# download-integrity.md: completion = verified bytes, never exit code).
# Bounded retries; persistent failure exits nonzero and loud. Prints SHA256
# of all fetched files on completion for manifest verification. Usage:
#   sg models -c "tools/fetch_hf_model.sh <owner/repo> <file> <bytes> [<file> <bytes> ...]"
# (needs models-group write on staging; sh-compatible callers are fine
# because the shebang selects bash). Optional: set LIMIT_RATE (curl
# --limit-rate syntax, e.g. "6M") to cap this invocation's bandwidth -
# useful when running several fetches concurrently and wanting to leave
# headroom for other network use. Unset = uncapped (prior behaviour).
# Optional: set DEST (default /opt/models/staging) to fetch into a subfolder.

set -u

if [ "$#" -lt 3 ] || [ $(( ($# - 1) % 2 )) -ne 0 ]; then
    echo "usage: $0 <owner/repo> <filename> <expected-bytes> [<filename> <expected-bytes> ...]" >&2
    echo "Hint: pin expected byte sizes from the HF API (api/models/<repo>/tree/main) before fetching." >&2
    exit 2
fi

REPO=$1
shift
# REVISION pins a commit (default main). Needed when a repo re-uploads files under the same names mid-fetch:
# unsloth replaced Flash-Next UD-IQ4_XS/UD-Q4_K_XL on main on 2026-11-04 while E153 was fetching the old set.
BASE="https://huggingface.co/$REPO/resolve/${REVISION:-main}"
# DEST overridable for multi-folder diffusers repos, whose per-folder config.json
# files would collide when flattened into the staging root.
DEST=${DEST:-/opt/models/staging}

fetch() {
    # $1 = repo-relative path (subfolders allowed; destination is flattened
    #      to the staging root), $2 = authoritative size in bytes (HF API,
    #      pinned by caller)
    f=$1
    want=$2
    out=$DEST/$(basename "$f")
    tries=0
    while :; do
        size=$(stat -c %s "$out" 2>/dev/null || echo 0)
        if [ "$size" -eq "$want" ]; then
            echo "COMPLETE: $f ($size bytes)"
            return 0
        fi
        if [ "$size" -gt "$want" ]; then
            echo "FAILED: $f is LARGER than expected ($size > $want)." \
                 "Hint: corrupt or wrong-revision file - delete it and rerun; do not resume onto it."
            return 1
        fi
        tries=$((tries + 1))
        if [ "$tries" -gt 30 ]; then
            echo "FAILED after 30 attempts: $f at $size/$want bytes." \
                 "Hint: check Wi-Fi/link stability; rerun to resume from current offset."
            return 1
        fi
        curl -sfL -C - --retry 5 --retry-delay 5 ${LIMIT_RATE:+--limit-rate "$LIMIT_RATE"} -o "$out" "$BASE/$f" || true
        sleep 2
    done
}

FILES=""
while [ "$#" -ge 2 ]; do
    fetch "$1" "$2" || exit 1
    FILES="$FILES $DEST/$(basename "$1")"
    shift 2
done

echo ALL-FILES-COMPLETE
# shellcheck disable=SC2086  # word-splitting FILES is intended
sha256sum $FILES
