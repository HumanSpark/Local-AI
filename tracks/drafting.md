# Drafting (r6.4)

**The question:** Would a professional send what it writes?

**Why this kind of test:** Blind pairwise judging of client-style briefs by two judges from other companies; drafting quality has no answer key, so it is the hardest track to score.

**Current answer:** GPT-6.1 Sol clearly ahead; the local draft's losses were unsupported promises and omissions, which the automatic checks missed (15 Nov 2026, [F189](../FINDINGS.md#f189)).

## Claims on this track (5)

Status, tested and reviewed dates come from [claims.json](../claims.json); [GLOSSARY.md](../GLOSSARY.md#claim-status) explains the terms. Experiment-by-experiment write-ups (why each was run, what would have changed the plan, what was decided) are being added track by track.

| Claim | Statement | Status | Tested | Evidence |
|---|---|---|---|---|
| C-FINETUNE-VOICE-001 | A house-style fine-tune trained on the box on your own examples reliably teaches the model your firm's voice and register (a consistent tone lift across two runs, no loss of factual faithfulness), but does not raise the send-readiness score itself, and a five-times-larger training set did not change that. It is a voice-adaptation lever, not a way to remove the edit. | current | 2026-07-13 | [FINDINGS.md#f37-2](../FINDINGS.md#f37-2) |
| C-TRAINING-ONBOX-001 | The box can train a model, not only run one: a house-style adapter was trained end-to-end on the machine itself (generate examples, train, serve) with no cloud step and nothing leaving the building - the strongest form of owning your capability. | current | 2026-07-13 | [FINDINGS.md#f37-2](../FINDINGS.md#f37-2) |
| C-FRONTIER-DRAFTING-001 | On 10 drafting jobs for fictional firms, judged blind by two AI judges, GPT-6.1 Sol beat production by 7 to 9 jobs net at every effort, and Claude Sonnet 5.5 beat production's everyday setting by 3 to 7. Local losses were unsupported promises and omissions, not invented figures. | current | 2026-11-15 | [results/e162-results.md](../results/e162-results.md) |
| C-QUALITY-SENDREADY-001 | On a real-work send-readiness test (would a professional send the draft, graded 1-5 by an independent frontier model over ten solicitor/accountant tasks), the best local models rate about 3.0 - a usable first draft that needs a real edit - against the frontier's about 4.4. Getting facts right on a benchmark is not the same as being send-ready. | qualified | 2026-07-12 | [FINDINGS.md#f34](../FINDINGS.md#f34) |
| C-QUALITY-CEILING-001 | No stock model or training-free technique closed the send-readiness gap: bigger models, reasoning models, the model checking its own work, showing it good examples in the prompt, and pooling several models all left local drafting at about the same level. Raw capability, not configuration, is the limit. | qualified | 2026-07-13 | [FINDINGS.md#f35](../FINDINGS.md#f35) |
