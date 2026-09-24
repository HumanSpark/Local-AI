# Release Notes - sparkbench-data-r5.0

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
all public prose and rendering are owned by the editorial layer and webby (see the Release-4.0 handoff spec).

## This release (r5.0)

- **Findings:** 166 in FINDINGS.md, newest F166.
- **Claims:** 45 active in claims.yml.
- **This release catches the public data up with the research: F47 to F166, 120 findings recorded after r4.6, and every
  experiment behind them.** Nothing in claims.yml changes value in r5.0 (see "Claims under review" below). Three build
  changes apply to this package and are declared in WITHHELD.md: it ships only files that git tracks, it withholds
  internal design documents, and it withholds two sets of files that contain private content (captured Claude Code
  requests, and coding transcripts that quote other repositories' source). Each is stated where it matters, not hidden.
- **Text-to-speech on this GPU (F47-F56, F133).** Engine architecture, not "AMD is slow", decides throughput: a 200x
  realtime-factor spread on one GPU (F47). vLLM does not run on gfx1151 (F48). Autoregression and model size compound to
  about 3000x (F49). Fish s2-pro returns HTTP 200 and a well-formed WAV containing 47 seconds of non-speech (F50).
  MegaTTS3 is Apache-2.0 and still cannot clone a voice locally, because the encoder is withheld (F52). Zonos builds and
  imports but cannot be brought up (F53). Zero-shot cloning has an accent-coverage limit that reference quality cannot fix
  (F54). The narrator was settled as VCTK p239 cloned by Chatterbox (F56). **F54's amendment and F52 record a
  retraction: "CosyVoice3 WORKING" was wrong, every one of its renders was garbled, and the fix that was tried is the
  likely cause. F55 then found it not viable.**
- **The platform underneath (F57-F58, F63-F64, F72, F106, F109-F111, F120, F129, F131, F135-F136, F138, F166).** The kernel
  drifted from 6.17 to 7.0 under a register that assumed one stack (F57), and the repo.radeon.com apt pin is
  load-bearing (F58). KV cache at q8_0 is free and 4-bit is a 5.6% cliff (F110). `-ub 2048` is worth 22.9% on real
  prefill (F111). The "~100K prefill wall" is a tunable, `n_ubatch`, and the finding was amended twice (F72).
  **F109 retracts the "~60 GiB" deadlock boundary: it does not exist on kernel 7.0.0-29, and neither does the contention
  trigger.** Prefill collapses with prompt length, so the context a box can hold is not the context anyone will wait
  for (F136). A maintenance window is not a clean box: TTS stays resident with 8 GiB of GPU memory (F166).
- **Knowledge work and model choice (F67-F69, F71, F73-F83, F89, F92-F94, F116, F118, F130, F140-F149, F153-F154).** Qwen3.8-27B
  beats the small workhorse on judged-free knowledge work by 6 of 20, all in the two hardest categories (F67).
  Reasoning effort is a routing axis with no middle setting on knowledge work (F69), and on coding it has an optimum
  in the middle (F71). A 3-task category produced a recommendation that inverts at 13 tasks (F73). Retrieval under
  scale is a measured strength (F74). What small models cannot do is walk a calendar (F80), and that is a fact about
  one model, not about the class (F118). Flash-Next matches the incumbent and never beats it, for 5.6x the memory
  (F116). Q4_K_M is the knee of the quantisation curve (F149). The knowledge-work banks saturate at the frontier: three
  models across a 40x price range score within one item (F153). DeepSeek-V4.1-Flash cannot be served on this box (F154).
- **Agentic coding (F97-F105, F107, F112-F115, F119, F147-F148, F152, F164).** Claude Code drives a local model with no
  translation shim (F97), and its harness floor of 44,912 tokens eliminates models before quality is asked (F98).
  The blocker for local agentic coding is tool-schema bytes in llama.cpp's grammar builder, not model capability
  (F103, F104). Aider drives both local models first try (F105) and is fast enough to be invisible (F112), but exits 0
  whether or not it did anything (F113, F152). F164 (experiment E143) tests the coding models a community chat
  recommended: four models tie on Aider passes and split the tasks in opposite ways, and the incumbent is 2x to 10x
  faster.
- **Speculative decoding and small-model designs (F84-F85, F160-F163).** MTP preserves the answer and not the completion
  (F84), and draft acceptance is a property of the workload (F85). A small model in front of the 27B does not pay: the
  draft-then-review cascade is safe and 30% slower (F161), the small model is most confident where it is wrong so it
  cannot gate (F162), and the 27B can gate itself safely but the gate costs what it saves (F163).
- **Vendor claims, tested (F120, F159, F165).** The community Strix Halo speed table verifies twice on our hardware
  (F120). A public "73 tok/s" for a 27B does not reproduce: 34.16 is the ceiling here (F159). Halogen's "~1,424 tok/s at
  32K prefill" measures 1,152, which is 81% of the claim and 5.3x llama.cpp, reproduced conditionally (F165).
- **Images (F155-F158).** Qwen-Image-2.1 runs on this box only with the gateway down and a tiled VAE decode (F155); image
  tools here exit 0 on a blank output (F158).
- **Method (F59-F60, F65-F66, F70, F79, F86, F88, F90-F91, F95-F96, F100, F117, F121-F128, F132, F134, F137, F139, F142,
  F145, F150-F151).** The lessons that cost the most: a saturated instrument cannot compare anything (F126, F142,
  F153), a deterministic grader can be reproducible and still wrong (F95), a pre-registration that names a concept
  instead of a field is not falsifiable (F65), a control must reproduce its own items before a cross-build
  comparison is licensed (F117), and one wrong defect report reached the edge of publication (F139).
- **New evidence:** the tracked raw evidence for the experiments the findings cite, and the pre-registration and results
  documents for the frontier-API, Bonsai, Halogen, cascade, gate and coding experiments (E135 to E143). Verbose
  server logs are not shipped (see WITHHELD.md); the JSON, markdown and summary files that the findings cite are.

## Changed claims (old -> new)

- (none. No claim in claims.yml changes value in r5.0. Its header still reads release 4.0 and data_freeze
  2026-07-17: that header has not tracked package versions since r4.0, and the claims themselves were last reviewed
  against the data on 2026-07-17.)

## Claims under review

Findings recorded after the claims were last reviewed bear on these published claims. Each stands as published
until the review is done; none is withdrawn here.

- **C-LONGCTX-USABLE, C-OP-GUIDANCE-ROCM-LEVER, C-PREFILL-ROCM-VULKAN, C-LONGCTX-FIRST-ANSWER:** F72 (the ~100K prefill
  wall is a tunable and the finding was amended twice), F111 (`-ub 2048` is worth 22.9% on real prefill), F129 (Vulkan
  did not fail under any controlled condition), F136 (prefill collapses with prompt length). This release does not
  re-measure the ROCm-over-Vulkan comparison under the tuned flags.
- **C-REASONING-TOKEN-TAX-LOCAL:** F67 and F69 (Qwen3.8-27B, a reasoning model, does document work well at low effort)
  and F140 (the reasoning-effort default is where the cost is). The claim says local reasoning models are not suited to
  structured document work; the later findings narrow that to a default-effort effect.
- **C-TOOLUSE-DOC-001, C-TOOLUSE-SERVING-001:** F76 (the tool-use instrument is five runs at temperature 0.2, so
  intermediate per-task scores do not reproduce between sessions), F93 and F94 (offering a tool is never free), F99
  (tool-calling must be measured under `tool_choice: auto`), F103 and F104 (tool-schema bytes are the serving limit).
- **C-CAPABILITY-PARITY-001:** F67 (a larger local model separates from the workhorse on judged work) and F86 (model
  evaluation and system evaluation are different measurements).
- **C-CONCURRENCY-SMALL-TEAM-P1:** F108 (`--cache-ram`, not slot count, is the multi-turn variable) and F135 (three models
  stay resident for the price of one context).
- **C-SPEED-WORKHORSE-P1:** F63 (the build and kernel move is worth about +3.3% token generation).

## Retracted and amended findings

- F52 and F54 (amendment): the CosyVoice3 "working" result. F55 supersedes it.
- F72: amended twice on the day after publication; the "cannot prefill ~100K" conclusion is withdrawn, the evidence is not.
- F109: retracts the "~60 GiB" deadlock size boundary and the contention trigger.
- F121 and F139: recorded cases where a harness scored a run that never happened, and where a summarised page produced a wrong
  defect report.

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
