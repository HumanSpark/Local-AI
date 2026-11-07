# File: INDEX.md
# Purpose: Annotated table of contents for all sparkbench results artefacts - the map for the publishable data package.
# Project: sparkbench | Date: 2026-07-04
#
# Overview: Every results file, what it measures, and where it is
# discussed. Grouped by campaign phase. File formats: .md = llama-bench
# markdown tables; .json = serve_bench per-config results (summary +
# per-request records) or promptfoo eval outputs; .log = timestamped
# sensor samples. Canonical narrative: reports/whitepaper/local-ai-for-a-small-firm.md
# (white paper) + reports/integrated-technical-results-v2.md (technical report / verify).

## Top-level results documents

| File | Contents |
|---|---|
| model-survey.md | Capability-survey log: per-model entries (capture format, corridor checks), Tier 1/2 summaries, quant ladder table |
| capability-probes.md | Non-LLM probes: whisper STT (+RTF), Piper TTS, FLUX image generation, resolution ceiling, 50-image gallery, upscaler |
| experiments.md | Pre-registrations AND results for experiments **E1-E54**. E1-E31 are the Phase A / capability campaign (sawtooth, quant-pair concurrency, upscaler, energy, spec decode, co-residency, 84K probe, embeddings, eval suites, frontier A/B, long-context envelope, output-budget sensitivity). **E32-E54 are the 2026-08-15-onward knowledge-work campaign**: the sealed-key tiers, the long-context ladder to 236,122 tokens, reasoning-effort routing, the legal matters, request-order stability, and the small-model arm. Tool-use experiments also live under results/tool-use/ |
| ps-eval tiers (in spikes/, results in experiments.md) | The sealed-key knowledge-work instruments, graded with **no LLM judge**. `spikes/ps-eval/` holds four: **L1** 20 questions (E37), **L2** 12 harder ones built to punish "the newest amendment wins" (E38), **L3** L2's questions buried in up to 119 distractor agreements (E41, E48), and **L4** statutory periods, engagement terms and adversarial "what is wrong with this contract", built on F60's walked-period mechanism (E54). Each tier has a `tools/validate_ps_eval*.py` driving synthetic respondents with required signatures |
| eval-pilot.md | Quality-eval pilot matrix, prediction resolutions, grader-artifact documentation |
| flux-gallery-prompts.txt | The 50 gallery prompts (filename\|prompt), reusable |
| router-multimodel.md | E34: llama.cpp router mode - two models resident on call (41.04 GiB at 48K, 0.04s switching), per-model presets, the models-max 2 safety cap (F40) |
| router-loadtest-prereg.md / router-loadtest.md | E35: pre-registration + results for load/unload/eviction and concurrent inference - models-max evicts before loading; concurrency is bandwidth-bound and 4.6:1 unfair to the MoE (F41) |
| router-concurrency-prereg.md / router-concurrency.md | E36: pre-registration + results for single-model concurrency under the router - free for throughput (within 0.7% of direct, F17's 2.66x reproduced), costs p95 tail (+46% at 16 slots); the prompt-sensitivity signal behind F43 |
| moe-diversity-prereg.md / moe-diversity.md | E37: pre-registration + results - 16 users asking DIFFERENT questions run 40% slower than 16 asking the same; dense control shows -0.1% (mechanism = MoE expert routing); corrects F17's 193.5 fleet figure to 109.40 (F43) |
| tool-use/jinja-default-control.md | The with/without-`--jinja` control that retracted F39's tool-use half (the flag defaults to enabled; no behavioural difference) |
| keyed-vs-pairwise.md | Keyed scoring vs blind pairwise judging on the same five E10 answers: 9/10 disagreement, plus the finding that every E10 answer was cut off by a harness ceiling - three by the CONTEXT window and two by max_tokens (widens and corrects F20) |
| closed-record.md | Closed-record professional reasoning (E38): ten sealed-key matters across four domains, three local models at 66-84%; the answer-format wording moving scores by 3 points in 10; three instrument defects the work found in itself |
| closed-record-prereg.md | Pre-registration for the closed-record run, committed before the first model loaded |
| INDEX.md | this file |

Related (outside results/): docs/PHASE-A-LOG.md (Phase A evidence log),
docs/FINDINGS.md (findings register **F1-F79**; the register is the working
record and `reports/2026-07-16-local-model-routing-guide.md` is the DEPLOYED
answer - go there first),
reports/integrated-technical-results-v2.md (compiled source of truth / verify layer),
manifests/MANIFEST.md (artefact provenance: repo, revision, size and sha256 for
every artefact fetched, including entries annotated as no longer on disk - the
register's job is to make things re-downloadable, not to inventory the disk).

**A numbering divergence a reader will otherwise trip over.** The rows above
for the router work call it E34-E37, and `results/experiments.md` numbers its
own entries independently, so an "E37" in this table is not the "E37" in that
file. The router experiments live in their own `router-*.md` files and are the
authority for their own numbers; experiments.md is the authority for its. This
is recorded rather than renumbered, because renumbering would break every
finding and commit message that cites either.

## results/phase-a-raw/ - Phase A + Steps 8-9 raw outputs (47 files)

| Pattern | Contents | Discussed in |
|---|---|---|
| bench-step5-gate.md, bench-step5-longctx.md | gpt-oss-120b house reference baseline (d0, d8192) | PHASE-A-LOG step 5 |
| bench-step6-qwen3-30b-a3b-2507*.md | Workhorse matrix row (d0 + longctx) | PHASE-A-LOG step 6 |
| bench-step6-qwen3-14b.md | Dense 14B matrix row | PHASE-A-LOG step 6 |
| bench-step6-glm45air*.md | GLM-4.5-Air (split invocations, F6) | PHASE-A-LOG step 6 |
| bench-step7-gptoss20b.md | gpt-oss-20b row | PHASE-A-LOG step 7 |
| bench-step7-qwen36-35b.md | Qwen3.6-35B hybrid row (F7) | PHASE-A-LOG step 7 |
| bench-step7-glm47flash.md / -mxfp4.md | GLM-4.7-Flash quant-isolation pair (F11) | PHASE-A-LOG step 7 |
| bench-step8-depths-*.md (6 files) | Six-model depth curves, -d 0..32768 (F13/F14) | PHASE-A-LOG step 8 |
| bench-step8-triplet-{1,2,3}.md | Repeatability triplet (F15) | step 8 end-state |
| bench-step8-3c-*.md (4 files) | Contamination experiment: quiet brackets + download/hash arms | step 8 3c entry |
| bench-step8-block2*-*.md (4 files) | Qwen3-4B / Qwen3-8B / Llama-3.1-8B / DeepSeek-V2-Lite (F12) | step 8 Block 2 |
| bench-step8-block3a-*.md (2 files) | ubatch sweeps (pp512 + amended pp2048) | step 8 3a entries |
| bench-step8-block3d-*.md (2 files) | FA-on f16 and q8_0 KV depth curves (F16) | step 8 3d entry |
| bench-step8-thermal.log | Per-leg amdgpu edge temps, whole window | step 8 methodology |
| bench-step9-ws*.json (10 files) | Workhorse concurrency sweep, slots 1-16 x {f16,q8} (F17) | Step 9 results |
| bench-step9-oss20b-ws*.json (3 files) | gpt-oss-20b concurrency (knee at 4) | Step 9 results |
| bench-step9-coder30b.md | Qwen3-Coder-30B canonical bench | Step 9 gap-filler |

## results/raw/ - survey + experiment raw outputs (76 files)

NOTE: step8/step9 files appear in BOTH raw dirs (identical copies -
an artefact of two preservation passes). The build script
deduplicates; checksums match.

| Pattern | Contents | Discussed in |
|---|---|---|
| bench-survey-*.md (12 files) | Tier 1+2 survey benches (phi4, mistral24b, gemma27b, qwen3-32b, r1-32b, phi4mini, coder32b, mixtral + mixtral-v2, scout-d{0,4096,8192}) | model-survey.md |
| bench-ladder-{q5km,q6k,q80}.md | Mistral-24B quant ladder rungs | model-survey.md Part 4 |
| bench-e1-scout-d*.md (6 files) | Scout chunk-boundary sawtooth sweep (-r 3) | experiments.md E1 |
| bench-e2-{q4,mxfp4}-ws*.json (6 files) | Flash quant-pair concurrency (F18 anti-scaling) | experiments.md E2 |
| bench-e4-scout-ws*.json (3 files) | Scout concurrency (best scaler) | experiments.md E4 |
| bench-e6-mixed-llm.json | LLM leg of the mixed-workload test | experiments.md E6 |
| bench-e12-ws{1,16}.json | Energy-economics serving windows | experiments.md E12 |
| bench-e13-*.json (5 files) | Spec-decode: 32B control, inert-draft, enabled-draft, workhorse draft legs (F21) | experiments.md E13 |
| bench-e14-*.json (3 files) | Co-residency: 4B solo + concurrent pair | experiments.md E14 |
| (step8/step9 duplicates) | see phase-a-raw table above | |

## results/eval-pilot/ - promptfoo outputs (23 JSONs + serverlogs)

| Pattern | Contents | Discussed in |
|---|---|---|
| {model}.json (5) | Pilot suite (17 tests) per model | eval-pilot.md |
| hardlong-{model}.json (5) | Hard long-context suite (6 multi-hop tests) | experiments.md E7 |
| e8-{model}.json (3) | 40.7K-token cross-chunk suite | experiments.md E8 |
| e9-{model}.json (5) | Contradiction-detection suite | experiments.md E9 |
| e10-{model}.json (5) | Structured-generation suite | experiments.md E10 |
| *.serverlog | llama-server -v logs per eval run (offload evidence, errors incl. the E8 context-overflow 400s) | E8 entry |
| pairwise/e10-pairwise-run2.json | 20 blind pairwise judgements (10 pairings x both label orders) under the Material-Outcome rubric | keyed-vs-pairwise.md |
| pairwise/e10-keyed-vs-pairwise.json | Keyed scores + per-pairing verdicts + the 9/10 disagreement | keyed-vs-pairwise.md |
| pairwise/e10-pairwise-run1-SUPERSEDED-prompt-hijack.json | First judging run, kept because its failure modes ARE the result: 6 of 20 calls answered the E10 question instead of judging it | keyed-vs-pairwise.md |

Test definitions and data: spikes/eval-pilot/ (promptfooconfig.yaml,
hardlong.yaml, e8-32k.yaml, e9-contradiction.yaml,
e10-generation.yaml, data/ - the invoice, log excerpts, 32K corpus).

## results/flux-gallery/ - 50 generated images (gitignored, 67MB)

1024x1024 PNGs, seeds 1001-1050, prompts in flux-gallery-prompts.txt.
Not in git; included in the package zip by the build script if
present on disk.

## Publication status

This index maps the evidence behind the reports. The curated result files
referenced from each report's Verify line are part of the published evidence
bundle. The full raw-data directory is retained for verification but is not part
of the public release until a named content and licensing review is signed off
(tracked in the Release 1.4 note); until then, cite the specific referenced
result files rather than the raw directory.

## results/deep-eval/ - Phase 2 capability + envelope outputs (2026-07-11/12)

| Pattern | Contents | Discussed in |
|---|---|---|
| e27-local-*.json, sanity-workhorse-*.json | E27 local capability suites (incl. v2/v3 grading generations) | experiments.md E27 + corrigenda |
| cloud-*-{summarisation,instruction-following,longcontext}.json (+ -v2) | E28 cloud batches (capped originals + fixed-grader re-runs) | E28 + corrigenda v1-v5 |
| e29-*.json / results/raw/mmlu-quant-ladder.* / results/raw/bench-quant-* | E29 compression curve (suites, MMLU ladder, bench legs) | E29 |
| e30-config*-*.json, envelope-worked-example.md, e30-worked-example-raw.json | E30 envelope rungs (Vulkan + 4B + ROCm lever) + worked example | E30 + correction + post-cut-off ROCm entry |
| e31-*.json, e31-cloud-summary.md | E31 budget-sensitivity, all 10 models | E31 |
| if-json-regrade-v3.md, reasoning-extraction-regrade.md, cloud-published-benchmarks.md | Grading corrections + vendor-citation compilation | E28 corrigenda; plan Task 9 |

## results/coding-screen/ - coding-model screen (2026-07-12) + local-vs-frontier gap (2026-07-13)

banking/ = synthetic-round transcripts/diffs per task-model;
real-project/2026-07-12/ = real-repo runs (sparky, sparkcore; v1-v5
generations preserved incl. failure records). Narrative:
docs/plans/2026-07-12-coding-screen-{01..10}-*.md. Registry: claims.yml;
migration matrix in docs/plans/.
gap/ = local-vs-frontier + failure-mode eval (F36, 2026-07-13): Qwen3-Coder,
GLM-4.7-Flash, opus-4.8 x 3 fixtures, per-run PASS/FALSE-COMPLETION/THRASH.
Harness: tools/{coding_harness,run_coding_gap,coding_gap_analysis}.py.

## results/real-quality/ - drafting-quality investigation (F34, F35; 2026-07-12/13)

Real solicitor/accountant tasks judged by an independent frontier judge
(claude-opus-4.8) on a usability rubric. baseline/ablation/ablation2/confirm =
the F34 model/prompting sweep; bigmodel/ = attended 120B writing test;
reasoning/ = reasoning-model trio; pipeline/ = draft->critique->revise->best-of-N
ablation; context/ = in-context gold-exemplar test (+ cached exemplars.json).
Findings F34 (model is the lever) + F35 (ceiling law: 4 training-free levers fail).
Harnesses: tools/{real_quality_run,quality_ablation,quality_confirm,big_model_test,
reasoning_model_test,quality_pipeline,context_test}.py. Design:
docs/plans/2026-07-13-writing-quality-pipeline-design.md.
