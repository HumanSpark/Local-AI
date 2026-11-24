<!--
# File: results/e175-results.md
# Purpose: Results of E175 - gbench's chat-template pair against a stock and a silently broken template on Qwen3.8-27B.
# Project: sparkbench | Date: 2026-11-24
#
# Overview: Scores results/e175-prereg.md against results/e175/{stock,broken-tool-content}.jsonl. Run 2026-11-24
# 00:53:55-00:56:00Z, local only (no cloud calls), relay restored and probe-verified 00:56:00Z.
-->

# E175 RESULTS - chat-template pair negative control

## In plain English

The check works. With the model's own template, all four questions were answered correctly. With a copy of the
template that silently dropped tool results, the tool question failed and its plain-text twin still passed, which is
exactly the signal that says "blame the template, not the model". The broken run did not crash or print garbage: the
model politely said the lookup "didn't return any information" and suggested the order ID might be wrong. That is
the dangerous kind of failure, because it reads like a sensible answer, and it is the reason to put this check into
the nightly production probe.

## Results (status per case)

| Case | stock | broken-tool-content |
|---|---|---|
| template_tool_response | pass | **fail** (missing QX7R2M, delayed) |
| template_tool_response_twin | pass | pass |
| template_multi_turn | pass | pass |
| template_multi_turn_twin | pass | pass |

Broken-arm answer to the tool case, verbatim opening: "I'm sorry, but I wasn't able to retrieve the status for order
ORD-4417 — the lookup didn't return any information." finish_reason `stop`, no tool call, no template tokens leaked.
Wall time 0.65-7.47 s per request. Raw: `results/e175/*.jsonl`, server logs `results/e175/*.serverlog`, `run.log`.

## Predictions

- **P1 HELD.** stock: 4/4 pass.
- **P2 HELD.** broken: `template_tool_response` fail, its twin pass.
- **P3 HELD.** broken: both multi-turn cases pass.
- Declared risk did not occur: llama-server accepted gbench's JSON-string tool arguments and rendered the stock
  template without error.

## Limits

One model (Qwen3.8-27B IQ4_XS on llama.cpp), one kind of break (tool content dropped), one request per case at
temperature 0. It shows the pair CAN catch a silent template break; it does not show it catches every kind. Production
serves Flash-Next on Halogen with the community template, which this run did not touch.

## Decision (per the prereg)

P1 + P2 held: add the tool-response pair to `tools/production_probe.py`, with the leak list taken from the served
community template. Not done in this commit.
