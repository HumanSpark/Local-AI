# E33: Extensive tool-use benchmark (pre-registration)

# File: results/tool-use/E33-preregistration.md
# Purpose: Pre-register the EXTENSIVE tool-use benchmark (E32 was the 8-task pilot). Predictions before runs.
# Project: sparkbench | Date: 2026-07-14
#
# Overview: E32 (pilot, 8 tasks, 1 run, 2 models) showed the workhorse drives office tools reliably via the
# standard function-calling API and that Qwen3-Coder leaked its native tool-call format as text. E33 turns
# that probe into a benchmark: 4 models, ~22 tasks across 7 categories, N=5 runs/task for RELIABILITY (the
# production question is how OFTEN it works, not whether it can once), 6 tools for real selection difficulty,
# error-recovery and ambiguity categories, structural scoring only (no API spend - decided 2026-07-14).

## Design

- Models (served one at a time, llama-server --jinja, -c explicit):
  - Qwen3-30B-A3B-Instruct Q4_K_M (workhorse; the E32 winner).
  - Qwen3-Coder-30B-A3B Q4_K_M - re-served, with /props checked for the detected chat format; if the default
    leaks the native <function=> XML, try a chat-template override before scoring (resolve the E32 confound fairly).
  - Mistral-Small-3.1-24B Q4_K_M (faithfulness leader).
  - gpt-oss-20b MXFP4.
- Tools (6): create_word_document (executed via python-docx), create_spreadsheet (executed), send_email,
  add_reminder, schedule_meeting, lookup_client (returns canned data so chains can consume a tool result).
- N = 5 runs per task per model, temperature 0.2. Report SUCCESS RATE per task (of 5) and per category.
- Incremental save (crash-safe): per-model JSON written as tasks complete.

## Task categories (~22 tasks)

1. Single-tool document (5): delay letter, plain-English summary, term extraction, attendance note, internal memo.
2. Single-tool non-document (3): chase email (send_email), diary reminder (add_reminder), book a meeting (schedule_meeting).
3. Multi-tool / chain (5): lookup client then write to them; letter + save + reminder; lookup + email + meeting;
   extract terms -> save doc -> email the summary; fee letter + fee spreadsheet.
4. Conditional / reasoning-in-call (3): URGENT-in-title if balance > EUR 5,000; letter-vs-email by urgency; VAT-in-total.
5. Error-recovery (2): lookup_client returns "no record found" - success = adapt (ask / report), NOT fabricate a client.
6. No-tool trap (2): a definition question and an opinion question - success = answer in text, call NO tool.
7. Ambiguous (2): under-specified request - success = ask a clarifying question rather than guess and call a tool.

## Scoring (per run -> aggregated to success rate)

- Each task has a kind-specific SUCCESS criterion (boolean). Reliability = successes / 5.
- Sub-metrics retained: call parses (structured tool_call, not leaked text), correct tool set, required args present,
  conditional satisfied where applicable.
- Headline per model: mean success rate across tasks; and the parse-rate (fraction of tool attempts that arrived as
  structured tool_calls vs leaked as text) - the E32 Coder failure mode.

## Predictions (pre-registered - deviations are findings)

- P1: Workhorse mean success rate >= 85% across all tasks; >= 95% on single-tool document tasks.
- P2: Reliability is NOT 100% for any local model - at least one task per model shows a split result across the 5 runs
  (tool use is stochastic at temp 0.2). The value of N=5 is exposing this.
- P3: Coder, re-served correctly, improves its PARSE rate vs the E32 pilot (~50%); whether it reaches the workhorse's
  reliability is the open question. If it still leaks after a correct template, that is a real model/stack finding.
- P4: Multi-tool chains (cat 3) and conditionals (cat 4) are the weakest categories for every model (reasoning-in-call
  and multi-step selection are harder than single calls).
- P5: The no-tool traps (cat 6) and ambiguous tasks (cat 7) catch OVER-CALLING in >=2 of the 4 models (models that
  fire a tool when the right move is to answer or ask).
- P6: Best local model by reliability is the workhorse or Mistral-24B, NOT a "coder" model - selection by measured
  parse+reliability, not by the tool/coder label (the E32 lesson, tested at scale).

## Deviations log
(none yet - amendments declared here before the affected runs)
