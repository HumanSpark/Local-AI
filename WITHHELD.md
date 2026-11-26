# Withheld from this package

Every path below is cited by a shipped finding, experiment or claim and is deliberately not shipped.
The completeness check accepts these citations only because they are listed here with a reason.

## Internal design documents (21)

Working design documents, briefs and plans. They record intent and internal planning, not
evidence, and are withheld from the public package by the owner's decision.

| Path | Cited by |
|---|---|
| docs/CAPABILITY-INDEX.md | FINDINGS.md |
| docs/HISTORY.md | results/e140-prereg.md |
| docs/briefs/2026-07-05-sparkbench-master-plan.md | experiments.md |
| docs/briefs/2026-07-08-upper-limit-candidates.md | experiments.md |
| docs/legal-assistant-blueprint.md | FINDINGS.md |
| docs/plans/2026-07-08-vulkan-memory-ceiling-investigation.md | FINDINGS.md |
| docs/plans/2026-07-09-repeatability-campaign-plan.md | FINDINGS.md |
| docs/plans/2026-07-09-upper-limits-reporting-plan.md | FINDINGS.md |
| docs/plans/2026-07-10-deadlock-cause-isolation.md | FINDINGS.md |
| docs/plans/2026-07-11-benchmarking-response-framing-and-answers.md | experiments.md |
| docs/plans/2026-07-12-coding-screen-10-realproject-results.md | FINDINGS.md |
| docs/plans/2026-07-12-local-quality-experiments.md | FINDINGS.md |
| docs/plans/2026-07-13-house-style-finetune-design.md | FINDINGS.md |
| docs/plans/2026-07-13-writing-quality-pipeline-design.md | FINDINGS.md |
| docs/plans/2026-07-16-production-serving-config-design.md | FINDINGS.md |
| docs/plans/2026-07-17-diarisation-investigation.md | results/diarisation/embedder-validation.md |
| docs/plans/2026-07-17-diarisation-landscape-research.md | results/transcription/e42-wer-model-size.md |
| docs/plans/2026-08-12-closed-record-reasoning-experiment.md | results/closed-record-prereg.md |
| docs/plans/2026-08-19-rd-programme-inference-as-resource-allocation.md | experiments.md |
| docs/plans/2026-08-28-inference-architecture-slice-1.md | experiments.md |
| docs/plans/2026-09-06-serving-reasoning-effort-proposal.md | experiments.md |

## Files git does not track (7)

Regenerable outputs, mostly verbose llama-server logs (hundreds of MB each), which the source
repository keeps out of git. The experiment's own results files, which the findings quote,
are shipped.

| Path | Cited by |
|---|---|
| results/e183/build.log | results/e183-prereg.md |
| results/raw/e113/worktrees/T3-multifile-optional-dep-aider.log | FINDINGS.md |
| results/raw/e146/M1/server.serverlog | FINDINGS.md |
| results/raw/e148/M3p/server.serverlog | results/e148-results.md |
| results/raw/e149/M4/server.serverlog | results/e149-results.md |
| results/raw/e91/e91-C-flashnext-low-l3.serverlog | results/e139-prereg.md |
| results/raw/e94/e94-residency-ctx262144-smart.serverlog | results/e100-prereg.md |

## Withheld because they contain private content

Not shipped, and not evidence the findings depend on for their numbers. Each prefix and why:

| Path prefix | Files withheld | Why |
|---|---|---|
| results/capability-index/ | 1 | monthly re-runs of the E154/E156 banks; same private-repository content |
| results/coding-screen/real-project/ | 34 | transcripts of coding tasks run against the owner's private repositories; they quote source code and commit metadata from repositories other than this one |
| results/e154-prereg.md | 1 | its amendments quote module, test and environment names from the owner's private repositories; the scores are in results/e154-results.md |
| results/e154/ | 2 | task prompts, per-task records and test output from the owner's private repositories (E154 bank) |
| results/e156-prereg.md | 1 | its amendments quote module, test and environment names from the owner's private repositories (F184's evidence); the scores are in results/e156-results.md |
| results/e156/ | 1 | task prompts, per-task records and test output from the owner's private repositories (E156 bank) |
| results/e158/ | 1 | per-task records and test output from the owner's private repositories (E158, on the E156 bank) |
| results/e159/ | 2 | per-task records and test output from the owner's private repositories (E159, on the E156 bank) |
| results/e160/ | 1 | raw answers and drafts that quote internal documents; the scores are in results/e160-results.md |
| results/e167-prereg.md | 1 | names files, tests and commits from the owner's private repositories; the scores are in results/e167-results.md |
| results/e167/ | 2 | task prompts, audits, per-task records and test output from the owner's private repositories (E167 bank) |
| results/e168-prereg.md | 1 | quotes commit notes and test names from the owner's private repositories; the scores are in results/e168-results.md |
| results/e168/ | 3 | task prompts built from private commit notes, per-task records and test output (E168 bank) |
| results/e171/raw/ | 2 | per-task records, harness and server logs from the owner's private repositories (E171, on the E167 bank) |
| results/e176/bank- | 1 | task subsets of the E154 bank (private repositories): prompts, commit ids and repo paths |
| results/e176/raw/ | 1 | per-task records and logs from the owner's private repositories (E176, coding banks) |
| results/raw/e108/claudecode- | 2 | captured Claude Code requests; each embeds the owner's private instruction files in full |

Cited by a shipped document:

| Path | Cited by |
|---|---|
| results/capability-index/setups.json | results/e158-results.md |
| results/e154-prereg.md | FINDINGS.md |
| results/e154/bank.jsonl | results/e176-prereg.md |
| results/e154/score.json | FINDINGS.md |
| results/e156-prereg.md | FINDINGS.md |
| results/e156/bank.jsonl | results/e158-prereg.md |
| results/e158/raw/window.log | results/e158-results.md |
| results/e159/raw/HF/harness.log | results/e159-prereg.md |
| results/e159/raw/HF/superseded/sparkforge-baab4031f.interrupted-20261112T1923Z.json | results/e159-prereg.md |
| results/e160/writing-judge.json | results/e160-results.md |
| results/e167-prereg.md | FINDINGS.md |
| results/e167/bank.jsonl | results/e167-results.md |
| results/e167/raw/window.log | results/e167-results.md |
| results/e168-prereg.md | FINDINGS.md |
| results/e168/bank.jsonl | results/e168-results.md |
| results/e168/gold-A2.log | results/e168-results.md |
| results/e168/raw/window.log | results/e168-results.md |
| results/e171/raw/HY/speed.json | results/e171-prereg.md |
| results/e171/raw/mem_guard.log | results/e171-results.md |
| results/e176/bank-e154-first5.jsonl | results/e176-prereg.md |
| results/e176/raw/LG/sparkforge-66de8e1d0.json | results/e176-prereg.md |

## Cited but not in the repository (4)

These paths are cited by a shipped document and exist nowhere: not in git, not on disk. They are
gaps in the record, listed so no citation dangles silently.

| Path | Cited by | What it is |
|---|---|---|
| results/coder-bakeoff.jsonl | FINDINGS.md | the per-arm result rows tools/coder-bakeoff/run_arm.sh appends (docs/HISTORY.md); never committed, so F103's requests-served counts rest on its own text and results/coder-bakeoff-toolprobe.tsv, not on this file |
| results/raw/e90/rerun.json | results/e90-aider-workflow.md | an --out path inside a quoted command line (e90-aider-workflow.md); no such file was kept |
| tools/__init__.py | experiments.md | a file the coding-screen task asked models to create (C01: 2 of 42 refused); never part of the repository |
| tools/run_negative_branch.py | experiments.md | the instrument for the E-series prose tier cited in experiments.md; it was never committed, so that tier's runs cannot be reproduced from this package |
