# File: 2026-11-evidence-entries-coding.md
# Purpose: Evidence-page entries for the November 2026 local coding results, written from the sources only, for the r5.2 data package.
# Project: sparkbench | Date: 2026-11-06
#
# Overview: These are the forensic entries for the /local-ai/ Evidence page, in the structure the owner's 2026-09-22
# rewrite brief set (webby docs/plans/2026-09-22-local-ai-rewrite-brief.md): Finding / Why we tested it / Result /
# What it means / Limits / Raw evidence. Evidence entries are sparkbench's to write (owner decision 2026-11-06); they
# are not buyer prose. Every number is a claim in tools/build_claims_json.py or a figure in the cited results file.
# E158 entry F185 added 2026-11-07. Sources: results/e156-results.md, results/e156-prereg.md, results/e158-results.md,
# results/e158-prereg.md, docs/FINDINGS.md F183-F185.

# Evidence entries: local coding on real repository work (November 2026)

## In plain English

These entries are the audit trail behind the November 2026 coding results. In short: on 10 real fixes from our own
projects, the best setups running on this machine solved as many as Claude Sonnet 5.5 and Opus 5.5 did, while taking
about eight times longer. Each entry says what we tested, what happened, what it justifies saying, and where it stops.

## F183 - On harder real repository work, the best local setups solved as many tasks as Sonnet 5.5 and Opus 5.5

**Finding.** On 10 real fixes from our own repositories, Qwen3.8-Flash-Next on Halogen (local) solved 9, Qwen3.8-27B
on Talus (local) solved 8, and Claude Sonnet 5.5 and Claude Opus 5.5 (cloud) solved 8 each. Qwen3-Coder-30B, our
earlier local coding recommendation, solved 2.

**Why we tested it.** An earlier test (E154, 15 smaller tasks) could not separate the strongest setups: Sonnet and the
best local setup both solved all 15. The owner's goal for unattended work is "slow but very smart", so we needed tasks
hard enough that the cloud models do not solve all of them.

**Result.**

| Setup | Solved (of 10) | Median minutes per task | Cost for the 10 tasks |
|---|---|---|---|
| Qwen3.8-Flash-Next on Halogen (local) | 9 | 21.3 | none per task |
| Qwen3.8-27B on Talus (local) | 8 | 23.6 | none per task |
| Claude Sonnet 5.5 (cloud) | 8 | 2.5 | USD 2.82 |
| Claude Opus 5.5 (cloud) | 8 | 5.3 | USD 7.75 |
| Qwen3-Coder-30B on llama.cpp (local) | 2 | 2.5 | none per task |

Each task was a change of several files and hundreds of lines, given to the same coding harness, with a 60-minute
budget. It was scored pass or fail by the project's own hidden tests run in a fresh sealed container. All seven
predictions written before the runs held.

**What it means.** On this kind of work, the best local setup now finishes about as many tasks as the cloud models,
at about 8.6 times Sonnet's median time and no per-task cost. It suits work that can be queued and left to run.
Qwen3-Coder-30B is no longer a sound local coding default: it stopped early on most tasks (median 19 turns) rather than
running out of time.

**Limits.**
1. Ten tasks, one attempt each. A one or two task gap is not evidence of a ranking.
2. One task (99cb03e95), solved by both local leaders and failed by both cloud models, has tests that check the wording
   of the code around one call. Without it the scores are 8, 7, 8 and 8, so it is not read as a local advantage.
3. The tasks come from three of the owner's own repositories. This is not a measure of general coding ability.
4. The task prompts state every new name the tests call, so they are closer to a specification than a bug report.
5. Each result is a model plus its engine and settings, not the model alone.
6. Task prompts were corrected four times during the run (see F184). Every setup was scored on the final prompts.

**Raw evidence.** `results/e156-results.md`; predictions `results/e156-prereg.md`; per-task records
`results/e156/raw/<setup>/<task>.json`. Claims `C-CODING-HARD-LOCAL-BEST-001`, `C-CODING-HARD-LOCAL-27B-001`,
`C-CODING-HARD-CLOUD-SONNET-001`, `C-CODING-HARD-CLOUD-OPUS-001`, `C-CODING-HARD-INCUMBENT-001`,
`C-CODING-HARD-TIME-001`.

## F184 - Hidden tests can demand details a task description never states; reading the first failures found five, automated checks found none

**Finding.** Three of the 10 tasks had requirements in their tests that the task description did not state. Reading
why the cloud models failed found all five such gaps. The automated checks we ran on the tasks beforehand found none.

**Why we tested it.** A model that fails a task may be wrong, or the task may be unfair. Before comparing setups we
needed to know the failures were about the models.

**Result.** The five gaps were patch targets and result keys (one task), a list of allowed variable names (one task),
and a list type, whole-module imports and the meaning of an empty set (one task). Each was corrected before any local
setup reached that task. Runs made on the old wording are kept and marked superseded. They are not scored.

**What it means.** For any new task bank:
1. Run one strong cloud model first.
2. Read every failure against its test.
3. Correct the task before the other setups reach it.

Automated checks on task wording are not enough on their own.

**Limits.** This is a lesson about building the test, drawn from one bank of 10 tasks. It does not say how common such
gaps are in other banks.

**Raw evidence.** `results/e156-prereg.md` amendments 1 to 4; superseded runs in `results/e156/raw/S/superseded/` and
`results/e156/raw/O/superseded/`.

## F185 - Newer local coding models matched the best local result but did not beat it

**Finding.** On the same 10 real fixes, Ornith 1.5 35B solved 9, level with Flash-Next. Tess 4.5 and Raon-1 mini solved
8, level with Sonnet 5.5 and Opus 5.5. Ornith 1.5 122B solved 6. A fifth model, Tess 4, could not be loaded.

**Why we tested it.** People in the local-AI community suggested newer models built for coding. We needed to know
whether any of them beat Flash-Next before changing the local coding default.

**Result.**

| Setup (all local) | Solved (of 10) | Median minutes per task |
|---|---|---|
| Ornith 1.5 35B on llama.cpp | 9 | 30.4 |
| Tess 4.5 27B on llama.cpp | 8 | 43.4 |
| Raon-1 mini preview on KRAFTON's llama.cpp fork | 8 | 20.0 |
| Ornith 1.5 122B on llama.cpp | 6 | not comparable (one task killed at 70 minutes with no record) |
| Tess 4 35B | did not load | - |

Same tasks, prompts, harness, 60-minute budget and sealed-container scoring as F183. Five predictions were written
before the runs. Three held. Two failed: we expected the 122B model to score at least as well as the 35B, and Raon-1
mini to score 6 or fewer.

**What it means.** Two local setups now share the top score of 9. On the owner's decision, Flash-Next is the local
coding default and Ornith 1.5 35B the fallback. A larger model was not better here: Ornith 122B scored lowest and ran
slowest. One task has been failed by every local model tried; only Sonnet has solved it.

**Limits.**
1. Ten tasks, one attempt each. A one or two task gap is not evidence of a ranking.
2. Each result is a model plus its engine and settings. Ornith 122B ran at a smaller quantisation (Q5_K_M), and its
   score was not separated from that.
3. Raon-1 mini is a preview model on a vendor fork of the engine.
4. Tess 4's file needs its maker's own engine fork. The failure to load is about that pairing, not the model.
5. Every limit of F183 applies: the owner's own code, prompts close to a specification, one weak test.

**Raw evidence.** `results/e158-results.md`; predictions `results/e158-prereg.md`; per-task records
`results/e158/raw/<setup>/<task>.json`; runner log `results/e158/raw/window.log`. Claims `C-CODING-HARD-ORNITH35-001`,
`C-CODING-HARD-TESS45-001`, `C-CODING-HARD-RAON-001`, `C-CODING-HARD-ORNITH122-001`, `C-CODING-DEFAULT`.
