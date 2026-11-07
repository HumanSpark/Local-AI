# E33 RESULTS: Extensive tool-use benchmark (2026-07-14)

# File: results/tool-use/E33-results.md
# Purpose: Results of the extensive tool-use reliability benchmark. Pre-reg: E33-preregistration.md. Pilot: E32.
# Project: sparkbench | Date: 2026-07-14
#
# Overview: 4 models x 22 tasks x 5 runs = 440 task-runs, 6 tools, 7 categories, structural scoring, no API spend.
# Headline: out-of-the-box tool-use support on llama.cpp is wildly model-dependent (a serving-config finding), and
# the pilot's dramatic "Coder is much worse" verdict softens under rigorous measurement.

## Reliability comparison (success rate; N=5 per task)

| Model | Mean | Format leaks | doc | nondoc | chain | conditional | error | no_tool | ambiguous | Out-of-box tool use |
|---|---|---|---|---|---|---|---|---|---|---|
| **Qwen3-30B-A3B (workhorse)** | **91%** | **0/110** | 100 | 100 | 80 | 67 | 100 | 100 | 100 | works instantly |
| **gpt-oss-20b** | **88%** | **0/110** | 100 | 100 | 68 | 67 | 100 | 100 | 100 | works instantly |
| **Qwen3-Coder-30B (native)** | 82% | 5/110 | 100 | 67 | 80 | 67 | 100 | 90 | 60 | native XML format, ~5% leak |
| **Mistral-Small-24B** | 75%* | 0/110 | 100 | 100 | 0* | **100** | 100 | 100 | 70 | REFUSES (no tool template shipped) |

*Mistral's chain score is TEMPLATE-CONFOUNDED (see below); excluding chains its mean is **96%** - the strongest single-tool + conditional model tested.

## Findings

1. **Out-of-box tool-use support is a serving-config lottery (the core finding).** Same llama.cpp build, same
   --jinja: the workhorse and gpt-oss emit clean structured tool_calls immediately; Mistral-Small-3.1 SILENTLY
   REFUSES ("I'm unable to create files") because its GGUF ships no tool template - it worked only after I wrote
   and supplied a Mistral v7-tekken tool template; Qwen3-Coder emits its native <function=...> XML that partially
   leaks as unparseable text. "Capable model" does NOT imply "does tool use on your stack" - you must verify the
   template+parser per model. This is the decision-grade takeaway.

2. **The E32 pilot OVERSTATED Coder's weakness.** Pilot (8 tasks, 1 run, terse system prompt): ~50% leak, looked
   broken. Extensive (22 tasks, 5 runs, explicit system prompt): 82% success, only 5/110 leaks. Coder is competitive,
   just slightly less reliable than the workhorse and the only model with a residual leak rate + weaker no-tool
   discipline (over-calls on ambiguous, 60%). Lesson: single-run pilots exaggerate; reliability needs N runs.

3. **Conditional reasoning-in-call is broken for the Qwen family + gpt-oss, but NOT Mistral.** c2-not-urgent
   (balance EUR 300, so title should be normal): workhorse, gpt-oss, and Coder all scored 0/5 - they add "URGENT"
   UNCONDITIONALLY. Mistral scored 100% (correctly withheld it). Only the both-branch design exposed this: c1-urgent
   (balance > 5000) passed 5/5 for everyone, so a true-branch-only test would have FALSELY certified the capability.
   This is the campaign's benchmark-non-transfer lesson inside a single task.

4. **The workhorse is the best all-round tool-use model** (91%, 0 leaks, handles the full multi-round agentic flow
   out of the box), with gpt-oss a close clean second (88%). Mistral is the conditional-reasoning champion but its
   multi-tool chaining could not be fairly measured on this stack.

## Confounds (flagged, NOT reported as clean findings)

- **Mistral chains (0%):** on lookup+write / lookup+email tasks Mistral calls the FIRST tool then stops - the
  signature of a tool-RESULT format mismatch in the hand-written v7 template (Mistral's multi-round protocol needs
  9-char call-ids + a specific [TOOL_RESULTS] structure). This is a template limitation, not a demonstrated model
  limitation; Mistral single-tool + conditional results are clean and excellent.
- **m2-letter-remind (0% all 4 models):** the task names an "O'Connor" client not in the test DB, so all models
  sensibly call lookup_client first, get "no record", and stop. A task-design flaw, not a letter+reminder finding.
  Clean multi-tool combos (m1 lookup+write, m3 lookup+email+meeting, m4 doc+email) pass at 100% for the workhorse.

## Verdict

Local tool use / document creation is REAL and reliable on the right model served the right way - the workhorse
hits 91% across a broad suite with zero format leaks and produces real, complete .docx files. But the result is
gated by serving config as much as by the model, conditional reasoning inside a call is unreliable for most models,
and content still needs the human-review discipline of any draft. Model+serving choice must be made by measurement,
not by the "coder/tool" label.

Evidence: results/tool-use/E33-results-*.json (4 models); E33-preregistration.md; tools/tooluse_harness_v2.py;
Mistral template results/tool-use/mistral-v7-tool.jinja; Coder served native (results/tool-use/coder-native.log).
