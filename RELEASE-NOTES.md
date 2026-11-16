# Release Notes - sparkbench-data-r5.11

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.11)

- **Findings:** 190 in FINDINGS.md, newest F190.
- **Claims:** 60 active in claims.yml.
- **F190 corrected: Loom's lower tool-use score is a behaviour difference, not a fault.** r5.10 said that on
  conditional tool tasks Loom "looked the client up and then stopped". That is what it did, but transcripts from an
  unscored re-run of the five tasks (3 runs each, Loom and Halogen) show why. The client lookup in those tasks returns
  "no client record found", and Loom asks the user for the details. In the reminder task it asks for today's date
  rather than guess one. The test's own instructions say to ask when information is missing, while its grader only
  counts the task done when the document or reminder is created. Halogen pressed on in the same situations. The
  scores (28 against 33 of 36) and every other F190 figure are unchanged.
- New evidence: `results/e163/raw/transcripts/LM.jsonl` and `HS.jsonl`, and the re-run's result files.

## Changed claims (old -> new)

- (none; F190's wording is corrected in FINDINGS.md.)

## Retracted claims

- (none.)

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
