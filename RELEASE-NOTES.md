# Release Notes - sparkbench-data-r5.7

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.7)

- **Findings:** 187 in FINDINGS.md, newest F187.
- **Claims:** 60 active in claims.yml.
- **README: the production setting.** A new section says what the machine serves since 13 November 2026
  (Qwen3.8-Flash-Next on Halogen, community chat template, reasoning effort low unless a request asks for more) and
  why, from F186 and F187. The coding chart's caption no longer says a lower effort "is being measured"; it points to
  F187. No finding, claim or evidence file changes.

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
