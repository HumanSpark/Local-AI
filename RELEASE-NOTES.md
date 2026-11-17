# Release Notes - sparkbench-data-r5.12

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.12)

- **Findings:** 192 in FINDINGS.md, newest F192.
- **Claims:** 60 active in claims.yml.
- **New finding F191 (E164): Qwen4 Max, the first Qwen4 model, tested through the cloud.** It is not available
  to run locally. On ten client-drafting jobs a blind judge put it slightly ahead of production (4 wins to 2), level with
  Claude Sonnet 5.5 (4 to 5) and clearly behind GPT-6.1 Sol (1 to 7). It invented no figures. It is the yardstick for
  open Qwen4 models when they ship. Total cost $4.08.
- **New finding F192 (E165): our everyday test suites were marking models down for following their own instructions.**
  The tool-use test asked for letters to seven clients missing from its pretend database while telling the model to
  look clients up and to ask when information is missing; models that asked were failed. The conversation test told the
  model that anything contradicting the record loses to the record, then marked it wrong for not applying a "correction
  for the file". An answer key was wrong, and three graders marked correct answers wrong. Every model lost marks,
  production included. Corrected, all five tested setups pass 36 of 36 tool tasks, and every one applies a correction
  without accepting the false claims the test also plants. Each fix carries a regression check shown to fail on the old
  code. Original and corrected scores are published side by side in `results/e165-results.md`.
- New evidence: `results/e164/`, `results/e165/`, `results/e164-results.md`, `results/e165-results.md` and their
  pre-registrations.

## Changed claims (old -> new)

- F190 (Loom): "passed 28 of 36 tool tasks against Halogen's 33" -> both pass 36 of 36 on the corrected test.
- F186/F187 (production setting): unchanged; the corrected scores leave the comparison within noise.
- Suite scores published in r5.6-r5.11 for tool use, the two conversation tests, L5, writing and kw-eval understate
  every model; read them beside E165's corrected columns.

## Retracted claims

- F190's tool-use clause (r5.10, reworded in r5.11): Loom has no tool-use shortfall. It was the test.

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
