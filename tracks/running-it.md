# Running it (r5.19)

**The question:** How fast is it, how many people can share it, what does it cost, and what breaks?

**Why this kind of test:** Engines, concurrency, power and stress, each measured on this one machine.

**Current answer:** Halogen serves production; see the two speed measurements below for what each figure means. Concurrency has only been measured on the July engine.

## Speed: one model, five engines

Qwen3.8-Flash-Next on this machine, one request at a time, thinking off, 4 November 2026 ([F180](../FINDINGS.md#f180)).
Decode is generation speed on a code prompt; prefill is how fast a 32,000-token prompt is read before the first word.

| Engine | Decode, code (tok/s) | Prefill at 32K tokens (tok/s) | Time to first token at 32K |
|---|---|---|---|
| Halogen 0.18.23 | 86.0 | 1,755 | 18.7 s |
| gufo 0.29.0, MTP | 69.1 | 1,497 | 21.9 s |
| Talus v0.1.3 | 67.9 | 1,258 | 26.1 s |
| Strata 0.2.10, DFlash2 | 60.7 | 691 | 47.4 s |
| llama.cpp 5851a8e, Vulkan | 27.1 | 315 | 104.1 s |

<a id="two-speed-measurements"></a>
## Two speed measurements of production, and why they differ

| | 4 Nov 2026 engine comparison ([F180](../FINDINGS.md#f180)) | 24 Nov 2026 live timing ([F202](../FINDINGS.md#f202)) |
|---|---|---|
| Writing speed | 86.0 tok/s on code requests (58.3 on prose in the same run) | 62.5 tok/s on a short document prompt |
| First word after a 32,000-token prompt | 18.7 s | 22.4 s |
| Conditions | closed window, one client, no other requests | timed while production served normally; another request may have shared the engine |
| Prompts | 23 fixed requests (code, prose, JSON, agent, 8K, 32K) | seven document prompts (8K x3, 32K x3, one short) |
| Setting | Halogen 0.18.23 defaults, thinking off | production since 13 Nov (community template), thinking off for timing |

What changed between them: the kind of text (Halogen's speculative decoding gains most on code, so 86 is its best
case; prose ran at 58.3 in the same session, close to the live 62.5), the prompts, and whether anything else was using
the engine. Neither figure is wrong; quote each with its conditions.

## Claims on this track (27)

Status, tested and reviewed dates come from [claims.json](../claims.json); [GLOSSARY.md](../GLOSSARY.md#claim-status) explains the terms. Experiment-by-experiment write-ups (why each was run, what would have changed the plan, what was decided) are being added track by track.

| Claim | Statement | Status | Tested | Evidence |
|---|---|---|---|---|
| C-HARDWARE-SPEC-001 | Hardware is a GMKtec EVO-X2 (Ryzen AI Max+ 395, 128 GB unified memory): EUR 2,960 net, about EUR 3,680 cash outlay including Irish import VAT. | current | 2026-07-03 | [MANIFEST.md](../MANIFEST.md) |
| C-ARCH-MOE-ADVANTAGE | At the same size, quantisation and model family, the mixture-of-experts architecture generates about 8.5 times faster (and prefills about 5.8 times faster) than the dense equivalent - architecture matters more than size. | current | 2026-07-08 | [integrated-technical-results-v2.md](../integrated-technical-results-v2.md) |
| C-CLAIM-BONSAI-SPEED-001 | A public '~73 tok/s on Strix Halo' for Ternary Bonsai 2 27B does not reproduce: 34.16 tok/s was the best of nine configurations (PQ2_0 plus a DFlash2 drafter, code prompt), and the claim's own 10.1 GB memory figure matches the PTQ1_0 configuration, which decodes at 3.63 tok/s on this Vulkan stack. Plain Bonsai runs 22.22 tok/s in 8.07 GiB against the incumbent 27B's 12.33 in 16.78 GiB; answer quality was not measured, so no swap is recommended on speed alone. | current | 2026-09-23 | [results/e138-results.md](../results/e138-results.md) |
| C-CLAIM-ATLAS-MLPERF-001 | On MLCommons' own edge-agentic harness (Qwen3.6-27B, 206 of 1,007 turns, single stream) Atlas took 9,307 ms per turn (Atlas HEAD plus a one-line patch) and 9,453 ms (the MLPerf entry's shipped source) against 12,863 ms for the llama.cpp reference: paired ratios 0.724 and 0.735 on the same turns, inline accuracy within 0.03. The entry's published 7,059 ms was not reproduced (1.32-1.34x). The reference runs no speculation; with a DFlash drafter added and nothing else changed (E147), llama.cpp took 7,775 ms per turn at identical accuracy, and both Atlas builds were 1.20-1.22x slower than that open configuration (F172). Atlas's own DFlash mode with the same drafter lineage (E148) took 22,898 ms per turn, 2.46x its MTP mode, because the drafter accepted 0.064 tokens per 15-draft step past 4K context; the MLPerf-era source cannot serve that mode on HIP (F175). | current | 2026-09-25 | [results/e146-results.md](../results/e146-results.md) |
| C-CLAIM-ATLAS-DETERMINISM-001 | Atlas (HEAD 2d1aab8, Qwen3.8-27B NVFP4, MTP K=4) returned 3 distinct outputs to 10 identical temperature-0 requests in one process; llama.cpp returned 1 distinct output to the same test, with and without a drafter. Atlas's README decode claim of 28.3-28.6 tok/s on code prompts measured 27.18, confirmed. | current | 2026-09-25 | [results/e146-results.md](../results/e146-results.md) |
| C-CAPACITY-TIERING-001 | Everyday models (4-30 GB) are safe under all tested load; models over about 60 GB can deadlock under heavy concurrent disk I/O. | current | 2026-11-18 | [FINDINGS.md#f193](../FINDINGS.md#f193) |
| C-LONGCTX-FIRST-ANSWER-PROD | On production (Flash-Next on Halogen), the first word of an answer arrives about 5.5 seconds after an 8K-token prompt and 22.4 seconds after a 32K-token prompt (client-timed, live, 2026-11-24). | current | 2026-11-24 | [results/e177-results.md](../results/e177-results.md) |
| C-COST-MARGINAL-P1 | Marginal electricity cost per 1M output tokens: about EUR 0.09 single-user, EUR 0.04 batched (sustained 72.8 t/s basis). | qualified | 2026-07-04 | [experiments/E12.md](../experiments/E12.md) |
| C-POWER-DRAW-P1 | Measured package power: about 4 W idle, 81 W under single-user inference, 83 W at sixteen concurrent users, with peaks of 93-107 W; wall draw is roughly 10-25 W higher (estimated, not plug-meter measured). | qualified | 2026-07-04 | [experiments/E12.md](../experiments/E12.md) |
| C-COMPRESS-MMLU-FLAT | Knowledge (MMLU) stays flat within confidence intervals from the 8-bit baseline down to about 2-bit; the first clear drop is at 1-bit ternary. | qualified | 2026-07-12 | [FINDINGS.md#f30](../FINDINGS.md#f30) |
| C-COMPRESS-SUMM-FLAT | Document-task accuracy is unchanged across every quantisation rung down to the ternary floor (suite ceiling). | qualified | 2026-07-12 | [FINDINGS.md#f30](../FINDINGS.md#f30) |
| C-COST-BREAKEVEN-FRONTIER | The box pays back on running cost only against the frontier tier, above about 81 tasks per day; never against the cheap or EU cloud tiers at a small firm's volume. | qualified | 2026-07-12 | [tools/cost_model.py](../tools/cost_model.py) |
| C-COST-PER-TASK-RATIO | Per document task, local electricity is about 338 times cheaper than the frontier cloud tier, 51 times cheaper than cheap cloud, and 32 times cheaper than EU cloud. | qualified | 2026-07-12 | [tools/cost_model.py](../tools/cost_model.py) |
| C-COST-TCO-3YEAR | Three-year total cost of ownership: about EUR 3,683 local (hardware-dominated) against about EUR 85 (EU) to EUR 907 (frontier) for cloud at roughly 5,000 document tasks a year. | qualified | 2026-07-12 | [tools/cost_model.py](../tools/cost_model.py) |
| C-CLAIM-HALOGEN-PREFILL-001 | Halogen's published '~1,424 tok/s prefill at 32K' for Qwen3.8-Flash-Next measures 1,152 tok/s here (median of 3), scored reproduced-conditionally against a 1,000-1,210 band that allowed for this box's IOMMU mode; mainline llama.cpp on our GGUF does 216.5 tok/s, so a 32K request takes 33 s on Halogen and 162 s on llama.cpp. Its speculative decoding was byte-identical to serial on 4 of 4 prompts. Halogen could not serve our GGUF beside the resident TTS service: it repacks the file into 70 GiB of host RAM and was stopped twice by the 12 GiB memory guard. | qualified | 2026-09-24 | [results/e139-results.md](../results/e139-results.md) |
| C-SPEED-WORKHORSE-P1 | Workhorse fresh-context generation speed is about 92 tokens per second (baseline). | historical | 2026-07-04 | [experiments/E13.md](../experiments/E13.md) |
| C-CONCURRENCY-SMALL-TEAM-P1 | One box comfortably serves a small team of 3-5 with intermittent use, and about four concurrent users is its best point: aggregate throughput peaks there at roughly 121 tokens per second, giving each user about 39 tokens per second - faster than anyone reads. Beyond that it does not keep improving; at sixteen concurrent users aggregate FALLS to about 109 tokens per second and each user drops to about 8. A single user is unaffected. | historical | 2026-07-04 | [FINDINGS.md#f17](../FINDINGS.md#f17) |
| C-PREFILL-ROCM-VULKAN | On a ROCm serving build, prompt processing (prefill) reaches about 8.08 times the Vulkan speed at depth - the lever behind the extended interactive long-context ceiling. | historical | 2026-07-05 | [FINDINGS.md#f23](../FINDINGS.md#f23) |
| C-COMPRESS-SPEED-CURVE | A Q2-class build generates about 1.7 times faster than the 8-bit baseline (61 to 106 tokens/sec) at one-third the file size. | historical | 2026-07-08 | [integrated-technical-results-v2.md](../integrated-technical-results-v2.md) |
| C-COMPRESS-SIZE-RANGE | The workhorse file shrinks from 30.25 GiB at the 8-bit baseline (Q8_0) to 10.49 GiB at Q2-class and 7.54 GiB at 1-bit ternary. | historical | 2026-07-08 | [integrated-technical-results-v2.md](../integrated-technical-results-v2.md) |
| C-REASONING-TOKEN-TAX-CLOUD | Reasoning-emitter models generate roughly 3 to 12 times more tokens, for lower quality on structured output. | historical | 2026-07-12 | [FINDINGS.md#f32](../FINDINGS.md#f32) |
| C-OP-GUIDANCE-ROCM-LEVER | A ROCm serving build lifts the interactive long-context ceiling from 48,000 to 64,000 tokens (64K first answer 3m17s against 6m43s on Vulkan), measured just after the data freeze. | historical | 2026-07-12 | [FINDINGS.md#f31](../FINDINGS.md#f31) |
| C-REASONING-NONRECOVERY | Reasoning-emitter models did not recover to direct-model performance on structured output even at a generous 8,192-token budget - a pre-registered prediction that missed, published as measured. | historical | 2026-07-12 | [FINDINGS.md#f32](../FINDINGS.md#f32) |
| C-CONCURRENCY-MOE-SCALING | With sixteen people asking sixteen different questions at once, the MoE workhorse delivers about 1.53 times the throughput of a single user - not the 2.66 times a same-question benchmark suggests. Mixture-of-Experts models route each token to a few specialists, so when concurrent requests differ the machine must fetch far more of the model per step. Conventional dense models do not behave this way (no measurable penalty), and a single user is unaffected either way. | historical | 2026-07-17 | [FINDINGS.md#f43](../FINDINGS.md#f43) |
| C-LONGCTX-FIRST-ANSWER | First-answer latency climbs with document length: about 30 seconds at 16K tokens, 95 seconds at 32K, 3.5 minutes at 48K, and 14 minutes at 80K; follow-up questions return in seconds. | superseded | 2026-07-11 | [experiments/E30.md](../experiments/E30.md) |
| C-LONGCTX-USABLE | Interactive long-context ceiling is about 48,000 tokens on the Vulkan stack, extending to 64,000 on a ROCm serving build. | superseded | 2026-07-12 | [FINDINGS.md#f31](../FINDINGS.md#f31) |
| C-REASONING-TOKEN-TAX-LOCAL | Local reasoning-emitter models pay the same 3-12x token tax and are not suited to structured document work. | superseded | 2026-07-12 | [FINDINGS.md#f32](../FINDINGS.md#f32) |
