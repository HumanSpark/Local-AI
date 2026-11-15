# Release Notes - sparkbench-data-r5.8

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.8)

- **Findings:** 188 in FINDINGS.md, newest F188.
- **Claims:** 60 active in claims.yml.
- **New finding F188 (E161): MoE "expert helpers" do not pay on this machine.** Tandem-style schemes keep the
  busiest experts in fast graphics memory and have the CPU or a second card compute the rest. On this box's single
  shared memory pool every version was slower than keeping the model wholly on the graphics side. Moving experts to the
  CPU cost 10-32% of decode speed (llama.cpp `--n-cpu-moe` 4/12/24). tandem.cpp built and ran on this GPU, but its
  automatic cache never switched on (it reads the small BIOS carve-out as the free graphics memory). A 24 GiB cache set
  by hand came out 16% slower than the same engine without it, and nearly exhausted memory.
- **Routing skew:** the busiest fifth of Flash-Next's 512 experts per layer take about 70% of routing on code, documents
  and prose alike. Code uses a different hot set from documents and prose (overlap 0.18-0.19), while documents and
  prose share theirs (0.70). Mixed precision by hotness is therefore not pursued as planned.
- New evidence: `results/e161-prereg.md` (amendments 1-2, both declared before the runs they affect),
  `results/e161-results.md`, `results/e161/speed-*.json`, `results/e161/skew.json`. The skew corpora quote private
  repositories and the imatrix files are 1.1 GB each; neither ships.

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
