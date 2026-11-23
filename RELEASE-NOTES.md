# Release Notes - sparkbench-data-r5.16

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.16)

- **Clearer names; no finding, claim, number or piece of evidence changed.** Findings are the same 197 (newest F197)
  and claims the same 60 as r5.15.
- Where a page named a test setup only by a letter code from another experiment ("E43 arm B", "E89 arm A", "F 0.997,
  I 1.000, H 0.987"), it now uses a short name ("E43's `xhigh` run", "E89's prefill-parallelism test", "production
  0.997, Inkling 1.000, Hy-Memory 0.987"). Experiment pages that refer to other experiments' arms open with one line
  saying what those arms were.
- Engines named in FINDINGS.md (Halogen, Atlas, Talus, Strata, Loom, Engram) get a one-line plain description where
  they first appear.
- Changed files: FINDINGS.md; experiments/E44-E49, E51, E52, E76, E80, E81, E112-E114, E119; docs/HARNESS-RULES.md;
  reports/2026-11-evidence-entries-coding.md; results/e136-results.md, e142-results.md, e171-results.md.

## Changed claims (old -> new)

- (none. Production and its setting are unchanged.)

## Retracted claims

- (none.)

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
