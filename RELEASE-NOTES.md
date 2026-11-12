# Release Notes - sparkbench-data-r5.5

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.5)

- **Findings:** 185 in FINDINGS.md, newest F185.
- **Claims:** 60 active in claims.yml.
- **README: speed and the machine.** Under the coding chart, a table adds each setup's engine and median minutes
  per task (from the E156 and E158 results tables). A second table shows one model, Qwen3.8-Flash-Next, on five
  engines: decode speed, prefill at 32K tokens and time to first token, from F180 (E153). A callout box states the
  machine's specification. Every figure in both tables is checked at build time against the results line it cites.
- No finding, claim or evidence file changed.

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
