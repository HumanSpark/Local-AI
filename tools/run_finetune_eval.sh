#!/usr/bin/env bash
# File: run_finetune_eval.sh
# Purpose: Phase 3 - eval the house-style fine-tuned Mistral-24B on the held-out 10 tasks
#          vs the SAME base at the SAME quant (Q8, so only the LoRA differs, not quant),
#          frontier-judged. The F37 verdict: does the on-box fine-tune move usability off ~3.0?
# Project: sparkbench | Date: 2026-07-13
set -u
cd /home/agent-spark/sparkbench
OUT=results/finetune
LOG=$OUT/eval.log
mkdir -p "$OUT"
say(){ echo "[$(date +%H:%M:%S)] $*" | tee -a "$LOG"; }
restore(){ say "RESTORE gateway"; systemctl --user start llama-gateway.service; sleep 3; systemctl --user is-active llama-gateway.service | tee -a "$LOG"; }
trap restore EXIT
FT=var/ft-models/mistral24b-housestyle.gguf
BASEHF=var/ft-models/Mistral-Small-3.1-24B-Instruct-2503
BASEGGUF=var/ft-models/mistral24b-base-q8.gguf

say "PAUSE gateway for Phase 3 eval"
systemctl --user stop llama-gateway.service; sleep 3; pkill -x llama-server 2>/dev/null||true; sleep 2

# Same-quant base for a fair comparison (Q8, matching the fine-tuned), no adapter.
if [ ! -f "$BASEGGUF" ]; then
  say "converting base -> Q8 GGUF (fair-comparison baseline)"
  var/ft-venv/bin/python llama.cpp/convert_hf_to_gguf.py "$BASEHF" --outfile "$BASEGGUF" --outtype q8_0 2>&1 | tail -2 | tee -a "$LOG"
fi

# LABEL suffixes each run (e.g. LABEL=-v3) so a re-run lands beside its predecessors rather
# than overwriting them - big_model_test.py refuses to clobber existing evidence regardless.
LABEL="${LABEL:-}"

say "=== EVAL fine-tuned (housestyle-ft$LABEL) -> $OUT ==="
python3 tools/big_model_test.py "$FT" "housestyle-ft$LABEL" "$OUT" 2>&1 | tail -4 | tee -a "$LOG"
pkill -x llama-server 2>/dev/null||true; sleep 3

say "=== EVAL base same-quant (base-q8$LABEL) -> $OUT ==="
python3 tools/big_model_test.py "$BASEGGUF" "base-q8$LABEL" "$OUT" 2>&1 | tail -4 | tee -a "$LOG"
pkill -x llama-server 2>/dev/null||true; sleep 3
say "PHASE 3 EVAL DONE"
