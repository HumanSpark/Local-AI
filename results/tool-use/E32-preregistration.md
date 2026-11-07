# E32: Tool-use / office-document creation (pre-registration)

# File: results/tool-use/E32-preregistration.md
# Purpose: Pre-register predictions + method for the tool-use / Word-doc-creation test BEFORE any run.
# Project: sparkbench | Date: 2026-07-14
#
# Overview: The campaign measured local models on TEXT generation (send-readiness ~3.0) and,
# separately, on AGENTIC CODING tool use (F36: well-formed tool calls but thrash on hard multi-step).
# It never tested general office tool use - can a local model, given an OpenAI-style function
# (create_word_document), correctly CALL the tool to produce a real .docx, select among multiple
# tools, and chain steps? This experiment fills that gap. Motivated by a direct question (2026-07-14):
# "did we test tool use - Word doc creation for example?" Answer was no; this tests it.

## Method

- Serving: llama-server with `--jinja` (OpenAI-compatible function calling), `-c` explicit.
- Endpoint: /v1/chat/completions with `tools` + `tool_choice:auto`, temperature 0.2 (reproducibility).
- Two tools offered on every task so tool SELECTION is exercised:
  - `create_word_document(filename, title, body_paragraphs[])` - executed for real via python-docx.
  - `add_reminder(title, due)` - a distractor/second tool (executed as a no-op log).
- Agentic loop: up to 3 tool-call rounds; tool results fed back so chaining can happen.
- Real execution: every valid create_word_document call writes a real .docx; a subset is rendered
  to PNG (Word-styled) as visual proof.

## Tasks (8; single-tool, multi-tool, conditional, and a no-tool trap)

1. Draft a client delay letter, save as murphy-delay.docx (single tool).
2. Summarise given engagement terms, save as summary.docx (single tool, grounded).
3. Extract parties/fee/dates/termination from a provided letter, save as a structured doc (extraction->doc).
4. Draft an attendance note from meeting notes, save as .docx (single tool, grounded).
5. Draft a chasing email AND save a .docx copy of it (two actions, one tool type).
6. Draft a letter, save it, AND add a follow-up reminder for 14 days' time (TWO different tools - selection+chaining).
7. Conditional: draft a fee-reminder letter; if the outstanding balance exceeds EUR 5,000, put "URGENT" in the title (reasoning inside tool use).
8. NO-TOOL TRAP: answer a plain question ("what does 'without prejudice' mean?") - correct behaviour is to answer in text, NOT call a tool.

## Scoring (per task)

- CALL-VALID: correct tool selected, JSON parses, required args present (0/1).
- COMPLETE: a real .docx (or correct no-op) produced with non-empty, on-task content (0/1).
- SELECT: right tool(s) for the task incl. the no-tool trap and the two-tool task (0/1).
- CONTENT: light 1-5 spot-check of the produced letter/body quality (does NOT re-litigate send-readiness).

## Predictions (pre-registered - deviations are findings)

- P1: Workhorse (Qwen3-30B-Instruct) emits a VALID tool call on >=80% of single-tool tasks (1-4). (1/1 in the probe.)
- P2: Multi-tool / chaining (tasks 5-6) is weaker than single-tool: predict >=1 failure to call the SECOND tool
  or wrong-tool among the tested models.
- P3: Qwen3-Coder-30B matches or beats the workhorse on CALL-VALID (tool-call specialist) but is <= on CONTENT quality.
- P4: The no-tool trap (task 8) catches over-calling in >=1 model (a model that calls create_word_document to answer a definition).
- P5: CONTENT quality tracks the ~3.0 send-readiness ceiling - tool use WRAPS the content, it does not raise it.
  Getting the tool-call right is not the same as the letter being send-ready.

## Models

- Qwen3-30B-A3B-Instruct Q4_K_M (workhorse; live on gateway :8400) - primary.
- Qwen3-Coder-30B-A3B-Instruct Q4_K_M (tool-call specialist; served :8401).
- Mistral-Small-3.1-24B Q4 (faithfulness) - if time permits.

## Deviations log

(none yet - amendments declared here before the affected runs)
