# Release Notes - sparkbench-data-r5.1

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
all public prose and rendering are owned by the editorial layer and webby (see the Release-4.0 handoff spec).

## This release (r5.1)

- **Findings:** 178 in FINDINGS.md, newest F178.
- **Claims:** 50 active in claims.yml.
- **Five vendor and community claims tested on the box, and five claims added for them (E138, E139, E143, E145, E146, E147, E148-E151; F159, F164,
  F165-F172, F175-F178).** A public "73 tok/s" for Ternary Bonsai 2 measures 34.16 at best (F159). Halogen's "1,424 tok/s prefill at 32K" measures
  1,152, 5.3x llama.cpp, and the engine cannot serve our GGUF beside the resident TTS service (F165, F166). On MLCommons' own edge-agentic
  harness Atlas takes about 27% less time per turn than the llama.cpp reference, and its published Strix Halo latency is not reproduced
  (F168-F170); the vendor page's figures do not match the MLCommons entry it cites (F170). Seven recommended coding models tie with the
  incumbent through Aider (F164, F167). With a drafter added and nothing else changed, llama.cpp beats both Atlas builds on the
  MLPerf metric (F172); Atlas's own DFlash mode is 2.46x slower than its MTP mode here and the MLPerf-era source cannot serve it on HIP (F175).
  Three single-variable arms then retired the drafter's attention pattern, the vendor's own context-cap explanation and the prefix cache
  as causes (F176-F178); the DFlash collapse on this hardware is left unexplained and the investigation closed.
- **F171 qualifies F164 and F167:** every failure on task T3 across eight models carries exactly the task's seed diff, so the models' edits
  never reached the file while the transcripts claimed completion. The "opposite task profiles" are partly a harness artefact.
- **F172 qualifies F169:** the MLPerf reference implementation plus a speculative drafter (E147) takes 7,775 ms per turn against the
  reference's 12,863 and Atlas's 9,307-9,453, at identical accuracy. Atlas is faster than the reference, not than the open engine
  configured with the speculation Atlas itself uses.
- **New evidence:** results/e143 to results/e146 raw trees (Aider per-attempt records, the E146 harness reports minus their 12 MB
  conversation logs, speed-client JSONs), results/e146-gates.md, the Atlas one-line patch results/e146/w4a16-nvfp4.patch.
- **New report source:** reports/2026-09-25-vendor-claims-on-your-own-box.md and its one-pager, for the public page.

## Changed claims (old -> new)

- (none. Five claims added under new ids; no existing value changes.)

## Retracted claims

- (none.)

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
