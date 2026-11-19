# Release Notes - sparkbench-data-r5.13

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.13)

- **Findings:** 195 in FINDINGS.md, newest F195.
- **Claims:** 60 active in claims.yml.
- **New finding F194 (E167): on big multi-file changes the best local setup passes half of what a frontier model does.**
  Ten real changes of 150-2,400 lines across 3-9 files, each with the project's own tests in full view. GPT-6.1 Sol
  passed 10 of 10, at about two minutes a task and $1.95 in all. Production (Flash-Next on Halogen) passed 5, at about
  eleven minutes a task; Ornith 35B passed 3. The local models stopped and declared the work done while tests still
  failed, so more time would not have helped.
- **New finding F195 (E168): hide the tests and both local setups fall to 1 of 10.** Same ten changes, with only the
  developer's own note and a list of the names the change adds. Production fell from 5 to 1, Ornith from 3 to 1. Most
  of the local models' skill on big changes is building to a specification they are shown. The cloud model could not be
  scored on this version (its budget ran out after five tasks on an earlier version), so this does not say how far
  local trails the frontier with the tests hidden.
- **New finding F193: the graphics-memory deadlock is back on kernel 7.0.0-42.** A 75 GiB model load froze the GPU
  after an earlier load had crashed it the same day, and only a power cycle cleared it. F109's "newer kernels fixed
  it" now holds only for loads on a freshly rebooted machine.
- New evidence: `results/e167-results.md`, `results/e168-results.md`, `results/e166/`. The E167/E168 task banks and
  per-task records are withheld (WITHHELD.md): they quote private repositories.

## Changed claims (old -> new)

- Coding recommendation: "the best local setups match Sonnet 5.5 and Opus 5.5 on real repository work" (F183) ->
  holds for small issue-style fixes; large multi-file changes are frontier work (F194, F195).
- F109 (deadlock not reproduced on kernel 7.0): -> holds for clean-state loads only (F193).

## Retracted claims

- None.

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
