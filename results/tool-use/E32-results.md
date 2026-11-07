# E32 RESULTS: Tool-use / office-document creation (2026-07-14)

# File: results/tool-use/E32-results.md
# Purpose: Results of the tool-use / Word-doc-creation benchmark (E32). Pre-registration: E32-preregistration.md.
# Project: sparkbench | Date: 2026-07-14
#
# Overview: Does a local model, given OpenAI-style tools, correctly CALL create_word_document to make a
# real .docx, select among tools, and chain steps? Tested the workhorse (Qwen3-30B-Instruct, live gateway)
# and the tool-call "specialist" (Qwen3-Coder-30B). 8 tasks each; two tools offered; calls executed for
# real via python-docx; a subset rendered to Word-styled PNGs (results/tool-use/png/).

## Scores (8 tasks: single-tool, grounded, two-tool, conditional, no-tool trap)

| Model | Valid call (of 7 tool tasks) | Correct tool selection (of 8) | Real .docx completed | No-tool trap | Conditional (07) |
|---|---|---|---|---|---|
| **Qwen3-30B-A3B (workhorse)** | **7/7** | **8/8** | **7/7** | PASS (answered in text) | **FAIL** (no URGENT in title) |
| **Qwen3-Coder-30B (specialist)** | 3/7 usable | 3/8 | 3/7 | FAIL (over-called a tool) | PASS (URGENT present) |

## Key findings

1. **The workhorse drives office tools reliably via the STANDARD OpenAI function-calling API.**
   It emitted clean structured `tool_calls` on every task that needed one, selected the right tool
   (including firing BOTH create_word_document AND add_reminder on the two-tool task), produced real,
   complete, professional .docx files, and did NOT over-call on the no-tool trap (answered in text).
   The Sparky "create a document" use case is feasible on the workhorse.

2. **DEVIATION from prediction P3 - the "specialist" is WORSE for standard integration.**
   Qwen3-Coder-30B is INCONSISTENT: on ~half the tasks it leaked its native `<function=create_word_document>
   <parameter=...>` XML syntax as PLAIN TEXT, which llama-server's OpenAI-compat layer does not parse into a
   tool_call - so a standard client gets no call and NO document is created. The content inside was fine; the
   FORMAT was not machine-usable. It also over-called on the no-tool trap. Lesson: pick a tool-use model by
   whether its calls PARSE on your serving stack, not by the "coder/tool" label. (This may be fixable with a
   Coder-specific chat template / tool-format flag; out of the box on this build it leaks.)

3. **Reasoning INSIDE the tool call is unreliable (confirms P5).** The workhorse missed the conditional
   ("if balance > EUR 5,000 put URGENT in the title"; balance was EUR 7,400) - the tool call was well-formed
   but the embedded logic was dropped. Getting the plumbing right is not the same as getting the judgement right.
   (Coder happened to get this one; single instance, not a reversal of the overall picture.)

4. **Content wrinkle: no format-awareness.** The model emits markdown (`**Parties:**`) into body_paragraphs,
   which Word renders as literal asterisks - it does not know the sink is a .docx. Cosmetic, but a real
   integration gap: a production tool would need to strip/convert markdown, or the model needs a system-prompt
   instruction that the body is plain text.

## Verdict

Tool use / Word-doc creation is REAL and works on the workhorse via the standard API - the report's gap
("we tested text generation, not tool-driven document creation") is now closed with a positive-but-caveated
answer. Caveats that carry the campaign's through-line (benchmark non-transfer): (a) reasoning inside tool
calls is unreliable, (b) content still needs the same human review as any draft (markdown artifacts,
faithfulness), (c) the tool-call "specialist" was LESS reliable here than the general workhorse - measure,
don't assume.

## Deviations from pre-registration
- P3 (Coder >= workhorse on call-validity): WRONG. Coder was less usable via the standard API (format leakage). Recorded as F38.
- P1 (workhorse >=80% valid single-tool): HIT (7/7 tool tasks).
- P4 (no-tool trap catches over-calling in >=1 model): HIT (Coder over-called).
- P5 (content/reasoning tracks the ceiling, tool use wraps it): HIT (conditional miss + markdown artifacts).

Evidence: results/tool-use/results-qwen3-30b.json, results-qwen3-coder-30b.json; rendered docs in
results/tool-use/png/qwen3-30b/; harness tools/tooluse_harness.py; renderer tools/render_docx.py.
