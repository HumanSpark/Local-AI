<!--
# File: docs/IMPROVEMENT-BANK.md
# Purpose: The bank of experiments that try to IMPROVE results on this machine, not just measure what we are handed.
# Project: sparkbench | Date: 2026-11-25
#
# Overview: Owner, 2026-11-25: "we have been doing a lot of benchmarking of what we've been handed ... what can we
# improve? ... make this a whole bank of experimentation to try and improve things, not just Ling." Each entry: the
# problem we measured, the change, the measure and its baseline, the cost, and a rank. An entry becomes a numbered
# experiment with a prereg when it runs; its row then links to the result. Ranked by expected value for a firm, then
# by cost. Evidence for each problem is the finding or experiment named.
-->

# Improvement bank

## Ranked queue

| # | Problem we measured | Change to try | Measure (baseline) | Cost | Status |
|---|---|---|---|---|---|
| 1 | Local coding: production solves 5/10 large changes; Claude solves 10/10 under its own working setup (E178) | Run production's model under a better agent setup (Claude Code-style tools and prompts, or Aider) instead of our minimal harness | hard bank pass_count (5/10) | ~4h GPU per setup, no download | queued |
| 2 | The local model is free per attempt but we give it one try | Several attempts per task, keep one that passes its visible tests (best-of-3), within the same wall-clock budget | hard bank pass_count (5/10) | ~8h GPU | queued |
| 3 | Local drafts lose on unsupported promises and missing facts (F189) | A self-check pass: "list every promise, figure and obligation; check each against the notes" before the final draft | blind judged wins on the 10 drafting jobs; judges can be Claude subagents, not paid API | ~1h GPU + subagent judges | queued |
| 4 | On a document pack the everyday setting once invented a figure (F186, F192) | Prompt that allows "not stated" and requires a source line per figure; or route figure questions to higher effort | document-pack score (25/26) and invented figures (1) | <1h GPU | queued |
| 5 | Ling writes fast but stalls in exploration and thinks for 50-100s a turn (F203) | Thinking off; lower temperature; both; then a bigger context | easy-bank pass_count (0 so far) | ~2h GPU | queued, after its easy bank finishes |
| 6 | Four HTR and five Ling tasks hit the 131K context limit | Larger context (HTR qualifies 262K with 8-bit KV) | hard bank pass_count on context-limited tasks | ~4h GPU, owner at the box (over 60 GiB) | queued |
| 7 | Inkling-2-Mini is 2-2.5x faster with its DSpark draft on Loom and CIRU, never tried on plain llama.cpp | DSpark draft on llama.cpp | decode tok/s (24-27 without) | ~20 min, 18 GiB | queued (scouting addendum) |
| 8 | Meeting notes: we measure transcription, not time to checked notes | Time a recording to checked notes with owners and deadlines, local pipeline against manual | minutes per hour of audio to an approved record (unmeasured) | needs a real call and a person | needs owner |
| 9 | Hidden tests: local solves 1/10 when it cannot see what "done" means (F195) | Ask the model to write its own tests first, then fix | hidden-test pass_count (1/10) | ~4h GPU | queued |
| 11 | HTR v0.2.4 wrote at 47.8 tok/s against Halogen's 62.5 (E177) | HTR v0.2.5 (24 Nov): 18 new kernels for this chip, same weights, no download; maker's figures +5.7% single-request decode, +28% at 4 users, prefill unchanged | client-timed speed (47.8 tok/s, 924 tok/s at 32K), then the hard bank (6/10) | ~1h speed + ~5h bank, owner at the box (load over 60 GiB) | queued |
| 12 | Local runs of recurring jobs lack the instructions a frontier session worked out | skill-distill: Claude turns one good session into task-specific instructions for production, tested until the local run matches (scouting/skill-distill) | match rate against the Claude reference on fresh inputs of the same job | Claude subscription + ~1-2h GPU per job | queued, pick the job |
| 10 | Production on Halogen: no recent version check | Newer Halogen release, same model, same prompts | decode and prefill (62.5 tok/s, 1,462 tok/s at 32K live) | ~30 min | watch for a release |

## Ideas parked, with the reason

- Fine-tuning on our own code: large effort, and the July house-style fine-tune taught tone, not correctness (F37).
- Choosing reasoning effort per question: tried in September; fixed low effort won (F162).
- A cheap-then-expensive model cascade: tried in September; safe but slower (F161).
- 8-bit conversation memory for speed on llama.cpp: never helped (F199).

## How an entry runs

1. Prereg with the baseline, the change, and a prediction naming its field.
2. The same bank, harness and grading as the baseline, so the change is the only difference.
3. A win changes a setup's status in `tools/experiments_registry.py` (and so the capability pages); a loss is recorded
   here as parked, with its finding.

## Queue order (owner, 2026-11-25)

"In general, we should be testing the fastest thing first in order to get results back faster." When several runs are
queued, the shortest expected run goes first, so a result arrives sooner and a broken setup shows in minutes. Two rules
outrank it: runs another depends on go first, and risky loads (over 60 GiB, able to wedge the box) go last in an
unattended window, so a wedge costs nothing already done. The coding-bank ladder (15 everyday fixes, then 10 bigger,
then 10 large) already runs fastest first.
