# Release Notes - sparkbench-data-r5.3

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.3)

- **Findings:** 185 in FINDINGS.md, newest F185.
- **Claims:** 60 active in claims.yml.
- **F183 amended (addendum 2026-11-12): the condition the 9/10 was measured at.** Flash-Next on Halogen ran at
  reasoning effort `xhigh`: the harness sent none, and the model's stock chat template defaults a missing effort to `xhigh`.
  That is why it spends a median of 59,437 output tokens and 21.3 minutes per task. A lower effort per request is
  possible and is now being measured (E159, pre-registration results/e159-prereg.md, included). The 9/10 stands for `xhigh`;
  whether `medium` or `low` keep it is not yet known.
- **New provenance:** MANIFEST.md records the E155 quality-ceiling models (GLM-5.3-Flash UD-IQ2_XXS, DeepSeek-V4.1-Flash
  Coder IQ2_XXS), pinned and sha256-verified. E155 has no result yet (4 of 10 tasks run for one arm before an interruption);
  no claim depends on it.
- **Tooling:** tools/run_e154_arms.sh gains the E159 effort arms and a deadline guard; tools/relay_bench_window.sh now
  closes a bench window correctly when production serves through Halogen alone (it previously left the gateway's health
  check reporting maintenance).

## Changed claims (old -> new)

- (none. C-CODING-DEFAULT is unchanged; its evidence is now qualified by the F183 addendum.)

## Retracted claims

- (none.)

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
