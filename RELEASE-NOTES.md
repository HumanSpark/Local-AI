# Release Notes - sparkbench-data-r5.6

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.6)

- **Findings:** 187 in FINDINGS.md, newest F187.
- **Claims:** 60 active in claims.yml.
- **New finding F187 (E159): on coding, lower reasoning settings are within noise of the maximum.** On the same
  ten real fixes, Qwen3.8-Flash-Next scored 8/10 at maximum thinking, at medium, at the community chat template's
  default and at community template + low; stock template + low scored 7. Community template + low took 5.8 minutes
  per fix against 19.1, with about a third of the thinking (17,802 tokens against 50,114). F183's 9/10 was measured at
  the stock template's unchosen maximum; its 2026-11-12 addendum now points here.
- **New finding F186 (E160): community template + low as the production setting, tested on eight kinds of work.** Against
  maximum thinking, it scored level or better on hard document questions (23 v 23 of 24), refuse-or-comply (12 v 12),
  conversations (9 v 8, 18 v 15), tool use (33 v 33 of 36) and dates with a tool (6 v 6). Writing was within noise
  (6 v 7 on the automatic check; a blind Opus 5.5 judge gave 1 win, 4 ties, 2 losses). It fell short on answers from a
  large document pack (24 v 26): one miss is a grading artefact, the other a percentage the documents never state. The
  battery took 20.6 minutes against 49.9. Three of eleven preregistered predictions failed; the results file reads each.
- New evidence: `results/e159-results.md`, `results/e160-results.md`, `results/e159-prereg.md`, `results/e160-prereg.md`.
  The per-task records quote the owner's private repositories (E159) and internal documents (E160 answers), so the raw
  directories are withheld as for E154-E158; the results files carry every score.

## Changed claims (old -> new)

- (none.)

## Retracted claims

- (none.)

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
