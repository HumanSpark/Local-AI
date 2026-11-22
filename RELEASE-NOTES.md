# Release Notes - sparkbench-data-r5.15

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.15)

- **Findings:** 197 in FINDINGS.md, newest F197.
- **Claims:** 60 active in claims.yml.
- **New finding F196 (E170): on memory-keeping jobs, production, Inkling-2-Mini and Tencent's Hy-Memory are all
  near-perfect.** Fifty invented memory jobs full of traps. Inkling made no mistakes, production one, Hy-Memory a few
  (it kept suggestions the person had turned down). Inkling was 6.5 times slower and gave no answer on 5 of 20
  updates, so production runs the nightly memory job. Caveat: that slowdown was our conversion on plain llama.cpp with
  no drafter, plus an undefined key in our own test, not the model alone; a fuller Inkling test is planned.
- **New finding F197 (E171): Tencent's Hy4-Flash (220B) runs stably on this machine but slowly, and an hour per task
  is too short for it.** Packed by the community Strata engine, it loaded in 38 seconds and ran all day without
  trouble. It wrote about 24 tokens a second, a third of its packager's figure. On the ten big coding changes it
  passed 3 to production's 5, and every task used its full hour. The two passed different tasks; production's
  passes all took more steps than Hy4 managed in an hour. Too slow for this budget, not shown to be less capable.
- New evidence: `results/e170-results.md`, `results/e170/`, `results/e171-results.md`, `results/e171/`. E171's
  per-task records are withheld (WITHHELD.md): they quote private repositories.

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
