# Release Notes - sparkbench-data-r5.9

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.9)

- **Findings:** 189 in FINDINGS.md, newest F189.
- **Claims:** 60 active in claims.yml.
- **New finding F189 (E162): on client-shaped drafting, GPT-6.1 Sol beats production Flash-Next at every effort.**
  The tasks were ten realistic jobs for invented businesses: a proposal section, meeting actions, a complaint reply, a
  contract explainer and others. Five arms drafted them: production at low, medium and xhigh, Claude Sonnet 5.5 and
  GPT-6.1 Sol. Two blind judges, grok-4.7 and kimi-k3.1-pro, compared every pair in both orders.
  - GPT won 7 to 9 more tasks than it lost against every local effort, on both judges.
  - Claude beat low on both judges. Against medium one judge gave +1, and against xhigh the judges disagreed.
  - Medium and xhigh beat low, against the prediction.
  - The judges' reasons, two of them confirmed by hand, are unsupported commitments and missing context. Invented
    figures were not the problem: all 12 raw "invented figure" flags were false positives on review (euro-thousands
    conversions, labelled calculations, and a wrong weekday in our own prompt).
  - The pre-registered rule fired: client-facing drafting is frontier work, or a local draft a person edits.
- **Amendment 1 is disclosed.** Kimi returned 51 of 200 replies empty. Each was re-asked once with only the token cap
  raised, after the tallies had printed. First-pass and after-retry completion and costs are reported separately, and
  the conclusions hold on the first pass alone.
- **Coding harness: the task budget is now a hard cap, and every started task leaves a record** (HARNESS_VERSION
  2026-11-15.1, `docs/HARNESS-RULES.md` Rule 15). This prompted no re-run. In E158, Ornith 1.5 122B's tenth task
  stays marked missing and scored as a fail.
- **README:**
  - The chart caption now says a one-task difference is within noise (F183).
  - Ornith 122B's minutes note now says its tenth task was stopped at the 70-minute limit and scored as a fail.
- New evidence: `results/e162-prereg.md`, `results/e162-results.md`, `results/e162/score.json`,
  `results/e162/adjudication.json`, `results/e162/grade.json`, the five draft files and both judges' verdict files.

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
