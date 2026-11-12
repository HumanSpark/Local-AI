<!--
# File: experiments.md
# Purpose: Pre-registrations and results for post-briefing follow-up experiments (Scout sawtooth, GLM concurrency quant-pair).
# Project: sparkbench | Date: 2026-07-04
#
# Overview: Two targeted experiments green-lit by Alastair 2026-07-04
# ("plan then execute all of that"). Each carries its pre-registered
# prediction/fork BEFORE the run, per the standing discipline. Stack:
# llama.cpp 067de937 Vulkan, Mesa 25.2.8, kernel 6.17.0-35, TTM 105GB.
-->

# Experiments

The pre-registrations and results for 119 experiments, one file each in [experiments/](experiments/). Predictions were written down before each test ran; the misses are published beside the hits. Later experiments have their own files in [results/](results/).

| Experiment | Title |
|---|---|
| [E1](experiments/E1.md) | Scout chunk-boundary depth sweep (sawtooth mapping) |
| [E2](experiments/E2.md) | GLM-4.7-Flash quant-pair CONCURRENCY (F17 mechanism isolation) |
| [E3](experiments/E3.md) | Image upscaler probe (completes the 1080p/4K story) |
| [E4](experiments/E4.md) | Scout concurrency (4th architecture point on the F17/F18 ladder) |
| [E5](experiments/E5.md) | Vision probe - Gemma-3-27B multimodal (new capability axis) |
| [E6](experiments/E6.md) | Mixed-workload test (one box, whole office) |
| [E7](experiments/E7.md) | Eval suite v2 - hard long-context tasks (P2 follow-up) |
| [E8](experiments/E8.md) | 32K-context eval with cross-chunk reference (the Scout quality question) |
| [E9](experiments/E9.md) | adversarial contradiction detection (suite v3, arm 2) |
| [E10](experiments/E10.md) | long structured generation (suite v3, arm 3) |
| [E11](experiments/E11.md) | STT accuracy round-trip (quantified WER) |
| [E12](experiments/E12.md) | Energy economics (tokens per joule -> EUR per million tokens) |
| [E13](experiments/E13.md) | Speculative decoding (0.6B draft) |
| [E14](experiments/E14.md) | Multi-model co-residency (fast lane + quality lane) |
| [E15](experiments/E15.md) | 100K-context probe (does the marketing number survive?) |
| [E16](experiments/E16.md) | Embeddings axis (RAG stack feasibility) |
| [E17](experiments/E17.md) | end-to-end meeting-to-summary pipeline (nice-to-have, 2026-07-05) |
| [E18](experiments/E18.md) | Vulkan vs ROCm depth comparison (briefing Part 2, 2026-07-05) |
| [E19](experiments/E19.md) | Qwen3-235B-A22B UD-Q3_K_XL - largest model tested, first Q3-class quant point (2026-07-08) |
| [E20](experiments/E20.md) | MiniMax M2.7 UD-Q3_K_XL - upper-limits campaign, largest total-param MoE after Qwen3-235B (2026-07-09) |
| [E21](experiments/E21.md) | Nemotron 3 Super UD-Q5_K_M - upper-limits campaign, hybrid Mamba-Transformer MoE (2026-07-09) |
| [E22](experiments/E22.md) | Command A+ Q3_K_M - upper-limits campaign, highest active-param MoE in the batch (2026-07-09) |
| [E23](experiments/E23.md) | Devstral 2 123B UD-Q5_K_XL - upper-limits campaign, dense reference (2026-07-09) |
| [E24](experiments/E24.md) | Cohere Command A Q6_K - upper-limits campaign, second dense reference (2026-07-09) |
| [E25](experiments/E25.md) | Step 3.5 Flash Q3_K_L - upper-limits campaign, first StepFun-lab model (2026-07-09) |
| [E26](experiments/E26.md) | Qwen3.5-397B-A17B UD-IQ1_M - upper-limits campaign, largest model + most extreme quant (2026-07-09) |
| [E27](experiments/E27.md) | local capability batch - summarisation fidelity + instruction-following (2026-07-11, deeper-research campaign) |
| [E28](experiments/E28.md) | cloud capability batch - the data-residency spectrum's cloud side (2026-07-11) |
| [E29](experiments/E29.md) | compression-vs-quality curve - Qwen3-30B-A3B family, 8 rungs (2026-07-11) |
| [E30](experiments/E30.md) | long-context envelope - local usable limit + worked example (2026-07-11, Task 13) |
| [E31](experiments/E31.md) | output-budget sensitivity - ALL models, MAXTOK=8192 (2026-07-11, pre-registered before any run) |
| [E32](experiments/E32.md) | concurrency sweep, Qwen3.8-27B vs MoE workhorse (2026-08-15, pre-registered before any run) |
| [E33](experiments/E33.md) | executable coding eval - Qwen3.8-27B vs local coding incumbents (2026-08-15, pre-registered before any run) |
| [E35](experiments/E35.md) | does the flat SPEED curve come with a flat QUALITY curve? (2026-08-15, pre-registered before any run) |
| [E36](experiments/E36.md) | cloud reference arms - the quantisation isolator and the frontier gap (2026-08-15, pre-registered) |
| [E37](experiments/E37.md) | professional-services knowledge work, graded WITHOUT a judge (2026-08-15, pre-registered before any run) |
| [E38](experiments/E38.md) | the L2 tier - can anything in this pack actually stop Qwen3.8? (2026-08-15, pre-registered before any run) |
| [E39](experiments/E39.md) | the EXPERT coding tier - does anything here separate a generalist from a coder model? (2026-08-15, pre-registered before any run) |
| [E40](experiments/E40.md) | technical writing - can this box draft the work, and can it be trusted with the bad news? (2026-08-15, pre-registered before any run) |
| [E41](experiments/E41.md) | the scale sweep - does the answer survive being buried? (2026-08-15, pre-registered before any run) |
| [E42](experiments/E42.md) | the speed question - how much of Qwen3.8's cost is reasoning, and what does removing it cost? (2026-08-15, pre-registered before any run) |
| [E43](experiments/E43.md) | the closed-record legal matters - all thirteen, against an instrument that already discriminates (2026-08-15, pre-registered before any run) |
| [E44](experiments/E44.md) | what happens when the budget stops being the constraint? (2026-08-15, pre-registered before any run) |
| [E45](experiments/E45.md) | does Qwen3.8 fix the ONE place the routing guide says the workhorse is unsafe? (2026-08-15, pre-registered before any run) |
| [E46](experiments/E46.md) | does -c break temperature-0 determinism? (2026-08-16, pre-registered before any run) |
| [E47](experiments/E47.md) | is the E33 "truncation" story an EFFORT artifact? (2026-08-16, pre-registered before any run) |
| [E48](experiments/E48.md) | the long-context ladder - E41 saturated at 8% of trained context, so go the rest of the way (2026-08-16, pre-registered before any run) |
| [E49](experiments/E49.md) | separating -b from -ub - which flag actually moved the prefill wall? (2026-08-17, pre-registered before any run) |
| [E50](experiments/E50.md) | is the negative-branch defect a TOOL-CALL artefact or a REASONING defect? (2026-08-17, pre-registered before any run) |
| [E51](experiments/E51.md) | does the same question get the same ADVICE twice? (2026-08-17, pre-registered before any run) |
| [E52](experiments/E52.md) | can a model that fits a laptop do real document work? (2026-08-17, pre-registered before any run) |
| [E54](experiments/E54.md) | the L4 tier - an instrument built to be FAILED (2026-08-17, pre-registered before any run) |
| [E54b](experiments/E54b.md) | (2026-08-17): the repair works, and it FALSIFIES E54's own headline |
| [E55](experiments/E55.md) | the multi-turn tier - the first conversation this programme has ever measured (2026-08-17, pre-registered before any run) |
| [E56](experiments/E56.md) | the LONG-conversation tier - the honest gap E55 left (2026-08-17, pre-registered before any run) |
| [E57](experiments/E57.md) | the HELD-OUT deep tier - closing E56's own-answer confound (2026-08-19, pre-registered before any run) |
| [E58](experiments/E58.md) | can Qwen3.8 serve a TINY query quickly enough to be resident? (2026-08-19, pre-registered before any run) |
| [E59](experiments/E59.md) | is MTP speculative decoding OUTPUT-PRESERVING on this model? (2026-08-19, pre-registered before any run) |
| [E60](experiments/E60.md) | (E59 stage 2): does MTP make the chat tier fast enough to remove routing? (2026-08-19, pre-registered before any run) |
| [E61](experiments/E61.md) | can a different MoE close the hard-tier gap, or is the split DENSE vs SPARSE? (2026-08-19, pre-registered before any run) |
| [E62](experiments/E62.md) | does gpt-oss-120b's 12/12 REPRODUCE? (2026-08-19, pre-registered before the run) |
| [E63](experiments/E63.md) | does gpt-oss-120b hold up at DEPTH, or only in single turns? (2026-08-19, pre-registered before any run) |
| [E64](experiments/E64.md) | what does gpt-oss-120b cost on the REAL traffic mix? (2026-08-19, pre-registered before any run) |
| [E65](experiments/E65.md) | the frontier comparator, and L3-hard is now SATURATED (2026-08-19) |
| [E66](experiments/E66.md) | the frontier arm on the held-out depth design: 18/20, the SAME as gpt-oss (2026-08-19) |
| [E67](experiments/E67.md) | PREREGISTRATION: the H6 deterministic-date arm (2026-08-19) |
| [E68](experiments/E68.md) | PREREGISTRATION: does OFFERING an irrelevant tool cost accuracy? (2026-08-19) |
| [E69](experiments/E69.md) | AABR saturation check: the instrument discriminates, and the crossed net hides its own result (2026-08-19) |
| [E71](experiments/E71.md) | S-H2: the gpt-oss-120b load/decode soak (2026-08-19) |
| [E72](experiments/E72.md) | tighten the S-H2 bound, and make ok mean ANSWERED (2026-08-19) |
| [E73](experiments/E73.md) | C-H1 pilot: does the real-commit coding instrument DISCRIMINATE? (2026-08-19) |
| [E74](experiments/E74.md) | KA-H1: real knowledge work on real documents (2026-08-19) |
| [E75](experiments/E75.md) | selective review: can the system beat its best model? (2026-08-20) |
| [E76](experiments/E76.md) | the abstention suite: does review stop a model asserting what the sources do not support? (2026-08-20) |
| [E77](experiments/E77.md) | does KV precision change ANSWERS? (2026-08-28) |
| [E78](experiments/E78.md) | the L5 two-band bank: does the EVIDENCE band have any headroom at all? (2026-08-28) |
| [E79](experiments/E79.md) | can a deterministic tool close the band-R gap between the FAST model and the ACCURATE one? (2026-08-28) |
| [E80](experiments/E80.md) | can a router aim the tool, and is the aiming cheaper than the harm? (2026-08-28) |
| [E81](experiments/E81.md) | is it slot HISTORY, or is it PREFIX DISPLACEMENT? (2026-08-28) |
| [E82](experiments/E82.md) | bounding the order effect: ten shuffled orders (2026-08-28) |
| [E83](experiments/E83.md) | gpt-oss-120b C01/C06: the two cells the corrected coding total left unknown (2026-08-28) |
| [E84](experiments/E84.md) | KA-H2: the same questions up the whole context ladder, and the instrument defect that made that impossible (2026-08-28) |
| [E85](experiments/E85.md) | does q8_0 change the RELAY's answers, on the RELAY's build, at the RELAY's context? (2026-08-28, evening) |
| [E86](experiments/E86.md) | is E85's K05 flip POSITION-INDEPENDENT? And the literal repeat is abandoned as vacuous (2026-08-29) |
| [E87](experiments/E87.md) | q8_0 THROUGHPUT on the relay's own build, in a real bench window, with flash attention separated out (2026-08-29) |
| [E101](experiments/E101.md) | does min-p fix looping, or is looping just the reasoning-effort default? (2026-09-04) |
| [E102](experiments/E102.md) | does the GSQ-RCO IQ3_S quant hold Q4_K_M quality on the same model? (2026-09-04) |
| [E103](experiments/E103.md) | is ThinkingCap-Qwen3.6-27B a better smart slot than our incumbent? (2026-09-04) |
| [E104](experiments/E104.md) | the expert tier as the harder instrument, after L5 saturated (2026-09-04) |
| [E105](experiments/E105.md) | is Q4_K_M leaving capability on the table? The top of the quant ladder (2026-09-05) |
| [E106](experiments/E106.md) | is temperature 0 hamstringing the models, and is it hamstringing them UNEQUALLY? (2026-09-05) |
| [E107](experiments/E107.md) | does temperature increase FABRICATION on evidence work? (2026-09-05) |
| [E108](experiments/E108.md) | what does an agentic harness actually COST per conversation, and does it fit llama.cpp's grammar builder? (2026-09-05) |
| [E109](experiments/E109.md) | is the HARNESS a lever on OUTCOMES, on coding and on knowledge work? (2026-09-05) |
| [E110](experiments/E110.md) | where does the CONTROL score on the new bank? (2026-09-06) |
| [E111](experiments/E111.md) | does the THREE-ARM bank discriminate? (2026-09-06) |
| [E112](experiments/E112.md) | were E109's three non-returning items the CAP or the HARNESS? (2026-09-06) |
| [E113](experiments/E113.md) | the repaired aider task set, actually run (2026-09-06) |
| [E114](experiments/E114.md) | the harness arm, MEASURED at 24 items (2026-09-06) |
| [E115](experiments/E115.md) | is --reasoning-effort a DEFAULT or a HARD OVERRIDE? (2026-09-06) |
| [E116](experiments/E116.md) | what does effort COST on a short turn? (2026-09-06) |
| [E117](experiments/E117.md) | does the SERVER path score what the REQUEST path scored? (2026-09-06) |
| [E118](experiments/E118.md) | RAN WITHOUT A PRE-REGISTRATION. Process breach, declared. (2026-09-06) |
| [E119](experiments/E119.md) | does REQUEST POSITION change the output? (2026-09-06) |
| [E120](experiments/E120.md) | Nemotron on the abstention bank, the axis that decides it (2026-09-06) |
| [E121](experiments/E121.md) | the WORKHORSE at matched effort, against Nemotron (2026-09-07) |
| [E122](experiments/E122.md) | the cost side of a workhorse swap (2026-09-07) |
| [E123](experiments/E123.md) | reasoning_effort is INERT for both MoE candidates, and two of my claims were wrong (2026-09-07) |
| [E124](experiments/E124.md) | Nemotron on the core bank, the workhorse's actual job (2026-09-07) |
| [E125](experiments/E125.md) | what a user actually waits, for both workhorse candidates (2026-09-07) |
| [E126](experiments/E126.md) | and E127 - RAN WITHOUT PRE-REGISTRATION. Third and fourth occurrences. (2026-09-07) |
| [E127](experiments/E127.md) | OBSERVATION - Nemotron on l5: 21/24, and it declines correctly on every unanswerable item (2026-09-07) |
| [E128](experiments/E128.md) | can the PRODUCTION gateway take reasoning_effort per request? (2026-09-07) |
| [E129](experiments/E129.md) | the runtime upgrade, verified on the production gateway (2026-09-07) |
| [E130](experiments/E130.md) | tool calling after the runtime upgrade and the effort flag (2026-09-07) |
| [E131](experiments/E131.md) | the other two residents, item-for-item across the upgrade (2026-09-07) |
| [E132](experiments/E132.md) | the document banks on the new runtime, and what the medium default costs (2026-09-07) |
| [E133](experiments/E133.md) | R10 attributed: the RUNTIME breaks it, and q8_0 KV then silences it (2026-09-07) |
| [E134](experiments/E134.md) | E133's attribution is WRONG. Production was already failing R10 before the upgrade. (2026-09-07) |
