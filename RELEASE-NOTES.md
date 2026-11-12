# Release Notes - sparkbench-data-r5.4

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.4)

- **Findings:** 185 in FINDINGS.md, newest F185.
- **Claims:** 60 active in claims.yml.
- **Easier to browse; no finding, claim or evidence changed.** FINDINGS.md opens with an index of every
  finding (title, kind, date, experiment and status copied from each entry, linked to it), grouped by kind, and every
  finding has a link back to the index. New claims.md renders claims.yml as a table with clickable evidence links. New
  results/README.md lists every experiment by number with its write-up, pre-registration, results and data. tools/,
  docs/, eval-suites/ and tts-bench/ each gain a README listing their files with each file's own description.
- **experiments.md split.** At 1 MB it was too large to browse; each experiment now has its own file in experiments/
  (E1 to E134), and experiments.md is the index. Every line moved, none was edited, and every existing citation of
  experiments.md still resolves.
- **Internal file headers hidden.** The "File / Purpose / Overview" lines that opened most markdown files rendered on
  GitHub as large headings; they are now inside an HTML comment. Nothing was removed.
- **Repository metadata.** LICENSE (CC BY 4.0, for the data and documents) and tools/LICENSE (MIT) so GitHub shows the
  licence the README already stated; CITATION.cff for a "Cite this repository" button; a .gitattributes so GitHub no
  longer describes the repository as a Python project.
- **One chart in the README:** real coding fixes solved out of 10, drawn at build time from the C-CODING-HARD claims
  (F183, F185), in light and dark versions.
- **INDEX.md removed.** It was stale (it listed findings to F79 and experiments to E54) and the generated indexes above
  replace it.

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
