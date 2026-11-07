# Release Notes - sparkbench-data-r5.2

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.2)

- **Findings:** 185 in FINDINGS.md, newest F185.
- **Claims:** 60 active in claims.yml.
- **Local coding on harder real repository work (E156, E158; F183-F185).** On 10 real multi-file fixes from the owner's
  repositories, scored by each project's own hidden tests in a sealed container: Qwen3.8-Flash-Next on Halogen 9/10, Ornith
  1.5 35B on llama.cpp 9/10, Qwen3.8-27B on Talus, Tess 4.5 27B and Raon-1 mini 8/10, Claude Sonnet 5.5 and Opus 5.5 8/10,
  Ornith 1.5 122B 6/10, Qwen3-Coder-30B 2/10. The best local setup takes a median 21.3 minutes per task against Sonnet's
  2.5. Tess 4 35B could not be loaded by upstream llama.cpp. Ten new claims (C-CODING-HARD-*).
- **F184 (method):** hidden tests demanded details five task prompts never stated; reading the first cloud failures found
  all five, automated prompt checks found none.
- **New evidence:** results/e154-results.md, results/e156-results.md, results/e158-results.md and the E158
  pre-registration. The per-task records, the task bank (results/e154/, results/e156/, results/e158/) and the E154 and
  E156 pre-registrations are withheld from this package: they quote the owner's private repositories. They stay in the
  sparkbench repository.
- **New evidence-page source:** reports/2026-11-evidence-entries-coding.md (F183-F185, the owner's six-part structure).
- **Report roles:** docs/REPORT-STANDARD.md - sparkbench drafts reader prose marked DRAFT, the owner rewrites, webby renders.
- **Public copy cleaned (2026-11-07 audit):** internal host names, home-directory and vault paths are replaced with
  neutral names (benchhost, lanhost, /home/bench, /opt/vault), and the synthetic test documents' contact details use
  reserved .invalid domains and unallocated +353 1 000 numbers, applied identically to the documents and the model
  answers that quote them. claims.yml evidence paths now name where each file sits in this package. The repository
  history was consolidated into one commit at r5.2.

## Changed claims (old -> new)

- **C-CODING-DEFAULT** (owner decision 2026-11-07): "Qwen3-Coder-30B is the recommended default (GLM-4.7-Flash as
  fallback)" -> "Qwen3.8-Flash-Next on Halogen is the recommended default, with Ornith 1.5 35B on llama.cpp as fallback".
  Source moved from docs/plans/2026-07-12-coding-screen-10-realproject-results.md to results/e158-results.md.

## Retracted claims

- (none.)

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
