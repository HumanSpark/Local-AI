# File: reasoning-extraction-regrade.md
# Purpose: Document dual-view reasoning extraction and re-grading (E27 contamination resolution)
# Project: sparkbench | Date: 2026-07-11
#
# Overview: Reasoning-emitting models (local MiniMax, Qwen3.5-397B;
# cloud Mistral magistral) contaminate outputs with thinking/reasoning text.
# This document records: (1) contamination patterns observed, (2) extraction
# rules applied, (3) per-run extraction results, (4) dual-view score tables.

## Executive Summary

Three classes of reasoning model contaminate their outputs:

1. **Local thinking-prose models** (MiniMax, Qwen3.5-397B): output begins with
   "Thinking: ..." or "Thinking Process: ...", followed by verbose internal
   reasoning, followed by the actual structured answer.

2. **Mistral magistral (cloud, partial)**: outputs structured JSON array with
   thinking blocks AND text blocks; both types present. Incomplete answers
   (2 cases out of 54 test results).

3. **Mistral magistral (cloud, incomplete)**: outputs ONLY thinking blocks,
   never reached the text-generation phase. Model cut off mid-reasoning
   (finishReason='length'). Unextractable (52 cases out of 54 test results).

**Policy decision** (orchestrator, pre-implementation): publish BOTH views
for reasoning-emitting models:
- **As-emitted**: scores from grading raw output (what users of our serving config see)
- **Content-extracted**: scores from grading extracted answer (capability view)

---

## Extraction Rules

### Rule 1: Local Thinking-Prose Models (MiniMax, Qwen3.5-397B)

**Pattern:** Output starts with "Thinking: " or "Thinking Process: " marker.
Followed by N lines of internal planning/reasoning (often fragmented: short lines
separated by blank lines, meta-reasoning like "We need to...", "Let's draft: ...").
Then actual structured answer begins (quoted text, bullet points, numbered items,
or markdown formatting).

**Extraction boundary:** First line that matches ANY of these markers:
- Numbered items: `1.`, `2.`, `3.`, `4.`, `5.`
- Bullet points: `-`, `*`
- Quoted text: `"` (line starts with double-quote)
- Bold markdown: `**`
- Headings: `#`, `##`, `###`
- Alternative: line matching regex `^[A-Z][^:]*:\s*` (data line like "Parties: ...")
  with length > 20 chars (filters out short thinking fragments)

**Boundary determination:** loop through all lines after the "Thinking:" header,
skip empty lines, stop at the first line matching a marker. Everything before
that line is thinking; everything from that line onward is the answer.

**Failure mode detection:**
- If no marker found in first N lines (or entire output), return unextractable.
- If extracted answer is < 50 chars or < 10 words, return unextractable
  (too little content to be a real answer).

**Testing / validation:** boundary must be at line >= 0 (inclusive). Boundary
at line 0 is valid (thinking header is only line 0). Boundary at line N means
"answer starts at line N".

#### Observed patterns (evidence from E27 outputs):

**MiniMax summarisation** (30 tests): ALL 30 outputs have clear boundary.
- Typical thinking section: 10-15 lines, 900-1200 chars
- Typical answer section: 2700-3200 chars, 400-500 words
- Boundary marker: mostly `"` (quoted summary), occasionally first bullet `-`
- Extraction success rate: 100%

**Qwen3.5-397B instruction-following** (24 tests): ALL 24 outputs have clear boundary.
- Typical thinking section: 25-35 lines, 600-1200 chars
- Typical answer section: 2400-3000 chars, 350-500 words
- Boundary marker: mostly numbered lists `1.`, `2.`, occasionally `**` (bold)
- Extraction success rate: 100%

---

### Rule 2: Mistral Magistral Cloud - Partial Completion

**Pattern:** Output is a JSON array containing objects of type 'thinking' and/or
'type'. Example structure:
```json
[
  {
    "type": "thinking",
    "thinking": [...],
    "closed": true
  },
  {
    "type": "text",
    "text": "The actual answer here..."
  }
]
```

**Extraction rule:** Extract all 'text' objects (ignore 'thinking' objects).
Concatenate the 'text' field from all text objects. Result is the
content-extracted view.

**Failure modes:**
- If no 'text' objects at all -> magistral_incomplete (model cut off)
- If 'text' objects exist but all empty/whitespace -> unextractable
- If output is not a JSON array -> unextractable

**Observed patterns (evidence from E28 magistral):**

**Mistral magistral v2 summarisation** (30 tests):
- 28/30 outputs: ONLY thinking blocks, no text parts (incomplete)
- 2/30 outputs: have both thinking and text parts (partial)
- Completion status: finishReason='length' for all 30 (cut off)

**Mistral magistral v2 instruction-following** (24 tests):
- 24/24 outputs: ONLY thinking blocks (incomplete)
- Completion status: finishReason='length' for all 24

**Mistral magistral v2 longcontext** (18 tests):
- Similar pattern: mostly incomplete (only thinking blocks)

Conclusion: Mistral magistral v2 is severely token-starved in the test harness.
The model begins reasoning but never reaches the text-generation phase. The 2
partial completions in summarisation are statistical outliers. Re-grading v2
outputs is not meaningful when 93%+ are cut off mid-thinking.

---

### Rule 3: Magistral Incomplete (Unextractable)

**Pattern:** Output is ONLY thinking blocks. finishReason='length'. Model never
reached text generation.

**Extraction rule:** Mark as unextractable. Grade as-emitted only (which will be
very low, as the model produced no answer).

**Why unextractable:** The output is incomplete by design (model was cut off).
Extracting the partial thinking is not meaningful because:
1. The thinking is incomplete
2. The final answer never appears
3. There's no content boundary to extract

---

## Per-Run Extraction Results

### E27 Local Models

#### E27 MiniMax M2.7 Summarisation
- Input: results/deep-eval/e27-local-minimax-m27-summarisation.json
- Total tests: 30
- Extraction results:
  - local_thinking: 30
  - unextractable: 0
- **Extraction rate: 100%**

#### E27 Qwen3.5-397B Instruction-Following  
- Input: results/deep-eval/e27-local-qwen35-397b-instruction-following.json
- Total tests: 24
- Extraction results:
  - local_thinking: 24
  - unextractable: 0
- **Extraction rate: 100%**

#### E27 Qwen3.5-397B Summarisation
- Input: results/deep-eval/e27-local-qwen35-397b-summarisation.json (RUN IN PROGRESS)
- Status: awaiting completion
- Expected: 30 tests, 100% extraction rate (same pattern as IF suite)

### E28 Cloud Models

#### E28 Mistral Magistral v2 Summarisation
- Input: results/deep-eval/cloud-magistral-medium-v2-summarisation.json
- Total tests: 30
- Extraction results:
  - magistral_incomplete: 28
  - magistral_partial: 2
  - unextractable: 0
- **Partial completion rate: 6.7% (2/30)**
- **Note:** 93.3% of outputs are cut off mid-thinking. Re-grading is not
  meaningful for v1/v2 because the model rarely completed a full answer.

#### E28 Mistral Magistral v2 Instruction-Following
- Input: results/deep-eval/cloud-magistral-medium-v2-instruction-following.json
- Total tests: 24
- Extraction results:
  - magistral_incomplete: 24
  - unextractable: 0
- **Completion rate: 0% (0/24)**

#### E28 Mistral Magistral v1/v2 Longcontext
- (Similar pattern: predominantly incomplete)

---

## Re-Grading Methodology

**Process:**
1. For each reasoning-emitting model (MiniMax, Qwen397B local; magistral cloud):
   - Load stored results JSON (as-emitted view, original scores)
   - Extract reasoning content using rules above
   - For extracted view: re-run ALL assertions against extracted text only
   - Collect pass/fail counts for both views
2. Compile per-model tables: as-emitted k/n vs content-extracted k/n

**Assertion re-evaluation:**
The original assertions (icontains, javascript) are deterministic. Re-grading
means running the same assertions against the extracted text. Since the harness
stores the raw output and assertions together, re-grading is:
- **For icontains assertions:** search extracted text for the substring
- **For javascript assertions:** evaluate the JS expression with extracted text
  as the `output` variable

**Important constraint:** Re-grading does NOT change the grading logic or
assertion definitions. The same assertions, evaluated against extracted text,
produce the extracted-view scores.

---

## Interpretation Notes

### Why Dual Views?

**As-emitted view** answers: "What does a user see if they use our serving
config with these models?" This includes reasoning text if the model emits it.
For reasoning models in research/transparency use cases, this view documents
the model's actual behavior.

**Content-extracted view** answers: "How capable is this model at the underlying
task?" This isolates answer quality from the model's internal reasoning artifacts.

For models that emit thinking as prose (MiniMax, Qwen397B), the extracted view
shows whether the model actually knows the answer, independent of whether it
vocalizes reasoning.

For magistral (incomplete), the as-emitted scores ARE the honest view because
the model cut off before generating any answer. Extraction is not applicable.

### Stability of Extraction Rules

Both extraction rules are **deterministic** (non-statistical). Given the same
output, the extraction always produces the same extracted text. This makes
re-grading reproducible.

The boundary detection is **conservative**: if no clear marker is found, the
output is marked unextractable rather than guessing. This avoids silent errors
where thinking accidentally looks like an answer.

---

## Predicted Score Impact

*To be filled after re-grading runs complete.*

### MiniMax
- As-emitted vs content-extracted: expecting modest improvements (thinking
  text sometimes fails specific assertions like word counts or formats)
- Most facts/traps should pass in both views (answer content is the same)

### Qwen3.5-397B
- As-emitted vs content-extracted: expecting small to no improvement
  (the thinking is explicitly structured and rarely conflicts with assertions)

### Magistral
- As-emitted and content-extracted will be very similar (most outputs are
  incomplete, so there's no text to extract)
- Low scores in both views are genuine (incomplete generation, not
  thinking contamination)

---

## Next Steps

1. Wait for E27 397B summarisation run to complete
2. Extract content from all reasoning models (local + cloud)
3. Re-run promptfoo assertions against extracted outputs
4. Compile dual-view score tables
5. Update experiments.md with resolution and findings

