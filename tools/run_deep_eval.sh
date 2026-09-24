#!/usr/bin/env bash
# File: run_deep_eval.sh
# Purpose: Run deep-eval promptfoo suites against local llama-server or cloud providers.
# Project: sparkbench | Date: 2026-07-11
#
# Overview: Orchestrates promptfoo evaluation suite execution with managed llama-server
# lifecycle for local runs or cloud API dispatch. Accepts provider-set directive
# (local:<gguf-path>, openrouter:<model-id>, mistral:<model-id>), manages server
# startup/health/cleanup, captures usage metrics, outputs JSON results. All subprocesses
# and HTTP calls have explicit timeouts (Rule 2, HARNESS-RULES). Temperature 0 only.
# Usage: tools/run_deep_eval.sh <suite.yaml> <provider-set> <label>
#   suite.yaml: path to promptfoo config file (basename used for output)
#   provider-set: local:/opt/models/staging/model.gguf | openrouter:model-id | mistral:model-id
#   label: result label (results/deep-eval/<label>-<suite>.json)

set -u

SUITE="${1:?usage: run_deep_eval.sh <suite.yaml> <provider-set> <label>}"
PROVIDER_SET="${2:?provider-set required (local:/path | openrouter:id | mistral:id)}"
LABEL="${3:?label required}"

ROOT=/home/agent-spark/sparkbench
SERVER=$ROOT/llama.cpp/build/bin/llama-server
SUITE_DIR=$(dirname "$SUITE")
SUITE_FILE=$(basename "$SUITE")
SUITE_NAME=$(basename "$SUITE" .yaml)
OUTPUT="$ROOT/results/deep-eval/$LABEL-$SUITE_NAME.json"

export PATH=$HOME/.local/opt/node-v24.18.0-linux-x64/bin:$PATH
export PROMPTFOO_DISABLE_TELEMETRY=1 PROMPTFOO_DISABLE_UPDATE=1

# Parse provider-set: "local:/path/to/model.gguf" or "openrouter:model-id" or "mistral:model-id"
PROVIDER_TYPE="${PROVIDER_SET%%:*}"
PROVIDER_ARG="${PROVIDER_SET#*:}"

wait_healthy() {
    python3 - <<'PY'
import sys, time, urllib.request
for _ in range(120):
    try:
        urllib.request.urlopen("http://127.0.0.1:8100/health", timeout=2)
        sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit("server never became healthy")
PY
}

run_local() {
    local gguf="$1"

    # Verify no other llama-server is running
    if pgrep -x llama-server >/dev/null; then
        echo "ERROR: llama-server already running - refusing to start another"
        return 1
    fi

    # Start server with explicit context window (-c 8192 default per spec;
    # CTX env overrides for long-prelude suites - NB: context is split across
    # -np slots, so long preludes also want NP=1)
    echo "Starting llama-server with $gguf (ctx ${CTX:-8192}, np ${NP:-2})..."
    "$SERVER" -m "$gguf" -np "${NP:-2}" -c "${CTX:-8192}" --jinja --no-webui \
        --host 127.0.0.1 --port 8100 \
        > "$ROOT/results/deep-eval/$LABEL.serverlog" 2>&1 &
    local spid=$!

    # Health poll with timeout (Rule 2)
    if ! wait_healthy; then
        echo "FAIL: server unhealthy - skipping"
        kill "$spid" 2>/dev/null; wait "$spid" 2>/dev/null
        return 1
    fi

    # Run promptfoo with the suite's providers (already configured for port
    # 8100). MAXTOK env: materialise an untracked temp copy with rewritten
    # max_tokens (E31 budget-sensitivity; gitignored pattern, removed after).
    local run_file="$SUITE_FILE"
    local local_tmp=""
    if [ -n "${MAXTOK:-}" ]; then
        local_tmp="$ROOT/$SUITE_DIR/.promptfoo-override-$$.yaml"
        python3 - "$ROOT/$SUITE_DIR/$SUITE_FILE" "$local_tmp" "$MAXTOK" <<'PY'
import sys, yaml
src, dst, maxtok = sys.argv[1], sys.argv[2], int(sys.argv[3])
with open(src) as f:
    suite = yaml.safe_load(f)
for p in suite.get("providers", []):
    p.setdefault("config", {})["max_tokens"] = maxtok
with open(dst, "w") as f:
    yaml.dump(suite, f, default_flow_style=False, sort_keys=False)
PY
        run_file=$(basename "$local_tmp")
    fi
    ( cd "$ROOT/$SUITE_DIR" && \
      timeout "${TIMEOUT_S:-1800}" promptfoo eval -c "$run_file" --no-cache \
        -o "$OUTPUT" 2>&1 | tail -10 )
    [ -n "$local_tmp" ] && rm -f "$local_tmp"

    # Kill server gracefully, then with SIGKILL if needed (Rule 2)
    kill "$spid" 2>/dev/null
    if ! timeout 15 tail --pid="$spid" -f /dev/null 2>/dev/null; then
        kill -9 "$spid" 2>/dev/null
    fi
    wait "$spid" 2>/dev/null

    # Verify cleanup
    if pgrep -x llama-server >/dev/null; then
        echo "WARN: llama-server still running after cleanup"
        pkill -x llama-server 2>/dev/null || true
    fi
}

run_cloud() {
    local provider_type="$1"
    local model_id="$2"

    # Source API keys
    if [ "$provider_type" = "openrouter" ]; then
        # sparkvault Phase 2 (2026-08-07): sparkbench's OWN OpenRouter key, narrowed at
        # the provider per Task 4, so revocation and spend are per-app. It is fetched
        # under SPARKBENCH_OPENROUTER_API_KEY but exported as OPENROUTER_API_KEY because
        # the suite config built below names that variable for the harness to read.
        #
        # This previously guarded `source ~/.config/openrouter.env` and fell through to
        # whatever OPENROUTER_API_KEY the shell happened to carry. That file does not
        # exist on sparkline, so the real source was always the ambient value from
        # ~/.env.shared - which Stage 5 deletes. vault_get.py exits non-zero on an absent
        # OR empty value, so there is no path here that yields an empty credential.
        OPENROUTER_API_KEY="$(python3 /opt/sparkvault/tools/vault_get.py SPARKBENCH_OPENROUTER_API_KEY)" || {
            echo "ERROR: could not read SPARKBENCH_OPENROUTER_API_KEY from the vault" >&2
            echo "hint: confirm the deployed vault is current -" >&2
            echo "      sudo bash /home/agent-spark/sparkvault-work/ops/vault_deploy.sh deploy" >&2
            return 1
        }
        export OPENROUTER_API_KEY
    elif [ "$provider_type" = "mistral" ]; then
        # Same treatment as the OpenRouter arm above, and for the same reason:
        # ~/.config/mistral.env does not exist on sparkline OR sparkmax (checked
        # 2026-08-21), so `source` was a no-op and the guard below reported a
        # missing FILE when the real authority is the vault. Exported as
        # MISTRAL_API_KEY because the suite config built below names that variable.
        MISTRAL_API_KEY="$(python3 /opt/sparkvault/tools/vault_get.py SPARKBENCH_MISTRAL_API_KEY)" || {
            echo "ERROR: could not read SPARKBENCH_MISTRAL_API_KEY from the vault" >&2
            echo "hint: confirm the deployed vault is current -" >&2
            echo "      sudo bash /home/agent-spark/sparkvault-work/ops/vault_deploy.sh deploy" >&2
            return 1
        }
        export MISTRAL_API_KEY
    fi

    # Build temporary provider override config in the suite directory (so file:// refs resolve correctly)
    local temp_config="$ROOT/$SUITE_DIR/.promptfoo-override-$$.yaml"
    python3 - "$SUITE" "$temp_config" "$provider_type" "$model_id" <<'PY'
import os, sys, yaml

suite_path, output_path, provider_type, model_id = sys.argv[1:5]

with open(suite_path) as f:
    suite = yaml.safe_load(f)

# max_tokens: MAXTOK env wins; else inherit the suite's own provider value
# (like-for-like with local runs); else 700. NEVER hardcode - a hardcoded
# 100 here silently truncated every Mistral cloud response (E28 v5).
_suite_maxtok = 700
try:
    _suite_maxtok = int(suite["providers"][0]["config"].get("max_tokens", 700))
except Exception:
    pass
maxtok = int(os.environ.get("MAXTOK", _suite_maxtok))

# Build the new provider config based on type
if provider_type == "openrouter":
    api_base = "https://openrouter.ai/api/v1"
    api_key_env = "OPENROUTER_API_KEY"
elif provider_type == "mistral":
    api_base = "https://api.mistral.ai/v1"
    api_key_env = "MISTRAL_API_KEY"
else:
    sys.exit(f"Unknown provider type: {provider_type}")

suite["providers"] = [
    {
        "id": f"openai:chat",
        "config": {
            "apiBaseUrl": api_base,
            "apiKeyEnvar": api_key_env,
            "model": model_id,
            "temperature": 0,
            "max_tokens": maxtok
        }
    }
]

with open(output_path, "w") as f:
    yaml.dump(suite, f, default_flow_style=False, sort_keys=False)

sys.exit(0)
PY

    # Run promptfoo with temp config (use absolute path for config and output)
    echo "Running promptfoo against $provider_type:$model_id..."
    ( cd "$ROOT/$SUITE_DIR" && \
      timeout "${TIMEOUT_S:-1800}" promptfoo eval -c "$temp_config" --no-cache \
        -o "$OUTPUT" 2>&1 | tail -10 )

    rm -f "$temp_config"
}

# Main execution
case "$PROVIDER_TYPE" in
    local)
        echo "=== LOCAL: $LABEL ($PROVIDER_ARG) ==="
        run_local "$PROVIDER_ARG"
        ;;
    openrouter)
        echo "=== OPENROUTER: $LABEL ($PROVIDER_ARG) ==="
        run_cloud "openrouter" "$PROVIDER_ARG"
        ;;
    mistral)
        echo "=== MISTRAL: $LABEL ($PROVIDER_ARG) ==="
        run_cloud "mistral" "$PROVIDER_ARG"
        ;;
    *)
        echo "ERROR: unknown provider type: $PROVIDER_TYPE"
        exit 1
        ;;
esac

if [ -f "$OUTPUT" ]; then
    echo "Results: $OUTPUT"
    exit 0
else
    echo "FAIL: no output file created"
    exit 1
fi
