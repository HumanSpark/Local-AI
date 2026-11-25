# Documents (r5.18)

**The question:** Can it work from what you give it?

**Why this kind of test:** Supplied sources make answers checkable: every figure in an answer either appears in the source or does not.

**Current answer:** 25/26 on a 26-question document pack (17 Nov 2026, after the grader correction); the miss was a figure the documents never state, which the model worked out instead of saying it was not there ([F192](../FINDINGS.md#f192)).

## Claims on this track (10)

Status, tested and reviewed dates come from [claims.json](../claims.json); [GLOSSARY.md](../GLOSSARY.md#claim-status) explains the terms. Experiment-by-experiment write-ups (why each was run, what would have changed the plan, what was decided) are being added track by track.

| Claim | Statement | Status | Tested | Evidence |
|---|---|---|---|---|
| C-LONGCTX-ACCURACY | Retrieval accuracy holds (6 of 6 needle probes) out to 80,000-plus tokens; beyond the interactive ceiling the constraint is speed, not correctness. | current | 2026-07-12 | [FINDINGS.md#f31](../FINDINGS.md#f31) |
| C-QUALITY-GROUNDED-001 | Local output is strongest - close to send-ready, facts exact - on grounded tasks like extracting terms and summarising a document, which is precisely the confidential document work the box is for; it is weakest on open-ended drafting, where faithfulness is the limit and human review catches it. | current | 2026-07-12 | [FINDINGS.md#f34](../FINDINGS.md#f34) |
| C-CAPABILITY-PARITY-001 | On fact-checkable document benchmarks (summarisation, extraction) local was competitive with the tested cloud comparator; a harder send-readiness test tells the fuller story (see C-QUALITY-SENDREADY-001). | qualified | 2026-07-06 | [results/frontier-eval.md](../results/frontier-eval.md) |
| C-RELIABILITY-12K-P1 | Every model in the fleet scored at least 83% on 12,000-token document work; accuracy holds even on the smaller models. | historical | 2026-07-04 | [FINDINGS.md#f19](../FINDINGS.md#f19) |
| C-LOCAL-SUMM-001 | Local workhorse (Qwen3-30B-A3B) scored 93.3% on the document-summarisation suite. | historical | 2026-07-11 | [experiments/E31.md](../experiments/E31.md) |
| C-LOCAL-IF-001 | Local workhorse scored 87.5% on the structured instruction-following suite. | historical | 2026-07-11 | [experiments/E31.md](../experiments/E31.md) |
| C-LOCAL-SUMM-4B | The small local model (Qwen3-4B) scored 96.7% on the summarisation suite. | historical | 2026-07-11 | [experiments/E31.md](../experiments/E31.md) |
| C-CLOUD-SUMM-FRONTIER | Frontier cloud (gpt-5.6-sol) scored 90.0% on the summarisation suite; cheap cloud (gpt-5.4-mini) 93.3%. | historical | 2026-07-11 | [experiments/E31.md](../experiments/E31.md) |
| C-CLOUD-IF-FRONTIER | Frontier cloud (gpt-5.6-sol) scored 75.0% on instruction-following; cheap cloud (gpt-5.4-mini) 100%. | historical | 2026-07-11 | [experiments/E31.md](../experiments/E31.md) |
| C-CLOUD-CHEAP-IF-BEST | The cheap cloud tier (gpt-5.4-mini) scored 100% on the instruction-following suite, ahead of the frontier's 75% - but this suite is a saturated format-compliance floor that does not separate capable models; on real drafting the frontier (gpt-5.6-sol) is clearly best. Read as 'the cheap tier clears the floor', not 'the cheap tier is better'. | historical | 2026-07-11 | [experiments/E31.md](../experiments/E31.md) |
