<!--
# File: results/e175-prereg.md
# Purpose: Pre-registration for E175 - does gbench's chat-template pair catch a silently broken template on a real model?
# Project: sparkbench | Date: 2026-11-24
#
# Overview: Spike from the scouting review scouting/gbench/REPORT.md ("optional spike"); owner 2026-11-24: "do the
# spike when done. no cloud api calls". Two arms (stock template, template with the tool output silently dropped),
# four gbench cases each, on Qwen3.8-27B with raw llama-server. Written before any GPU work, while E173 renders.
-->

# E175 PRE-REGISTRATION - chat-template pair negative control

## In plain English

gbench suggests a cheap way to spot a broken chat template: ask the same question twice, once where the answer
arrives as a tool result and once as plain text. If only the plain version works, blame the template. Nobody has
shown this actually catches a broken template on a real model. We break one on purpose and see whether the check
goes red, and whether it stays green when nothing is broken. If it works, it becomes part of the nightly production
check.

## What is measured

- **Cases:** gbench @ d3e4283 (Apache-2.0), copied unchanged to `results/e175/cases/` with the licence:
  `template_tool_response` + twin, `template_multi_turn` + twin. sha256 prefixes: 8386086447c5333a, 0618bf5bb4a5f1db,
  435c589a4ad3d2ef, ebaad9f44eba4768.
- **Model:** Qwen3.8-27B unsloth UD-IQ4_XS (`/opt/models/staging/qwen3.8-27b-talus/`, MANIFEST E154 entry), same family
  as production. Substituted for the scouting report's Qwen3-4B, which was removed from disk 2026-08-17.
- **Engine:** llama.cpp `94f3af3d0` llama-server, `-c 8192 -ngl 999`, `--chat-template-file`, local 127.0.0.1:8471.
  Temperature 0, max_tokens 512, `enable_thinking: false` (both arms). No cloud calls.
- **Arms:**
  - `stock` = the template embedded in the GGUF (`results/e175/templates/stock.jinja`, 12827f24b742ea4e).
  - `broken-tool-content` = stock with one line deleted: `{{- content }}` inside the `tool` role branch (line 164), so
    the tool result is silently dropped and the template still renders (502e5106b763c640). Deleting the whole branch
    was rejected: it raises, which is a harness error, not the silent break the check exists to catch.
- **Scoring (gbench's rule):** case-insensitive `contains_all` of expected outputs, none of `expected_not_contains`,
  none of the Qwen template tokens listed in `tools/e175_template_pairs.py`. HTTP error or empty content with no tool
  call = `harness-error`, never `fail`.
- **Guards:** relay window idle-down, GTT settle before each server start (F198), page-cache eviction (F199). 13.3 GiB
  model, under the 60 GiB edge. Runs only after E173 finishes.

## Predictions (field: `status` in `results/e175/<arm>.jsonl`, per case)

1. **P1 (no false alarm):** `stock` - all four cases `pass`.
2. **P2 (catches the break):** `broken-tool-content` - `template_tool_response` is `fail` AND
   `template_tool_response_twin` is `pass`.
3. **P3 (control):** `broken-tool-content` - both `template_multi_turn` cases `pass` (no tool turn in them).

Known risk to P1, declared now: the template raises when tool-call `arguments` arrive as a JSON string, and the
gbench case sends a string. If llama-server does not parse it into an object first, `stock` returns HTTP 500 on
`template_tool_response` and scores `harness-error`: P1 falsified, and that is itself a finding for any probe we build.

## What would change a decision

- P1 + P2 hold: add the tool-response pair to `tools/production_probe.py` (leak list from the served community
  template, not the tokenizer).
- P2 falsified (broken arm still passes): the check is blind to this break on this model; do not adopt as-is.
- P1 falsified: the case as written does not run cleanly on llama.cpp; fix the case (object arguments) before any
  adoption, and record why.

## Amendments

(none yet)
