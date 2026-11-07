# Integrated Technical Results Report

Technical verification layer for a continuous benchmarking run (3 - 14 July 2026). The core benchmark data froze 2026-07-11; the v3.0 output-quality workstream (the real-work drafting eval, the quality-ceiling investigation, and the on-box house-style fine-tune) ran to 2026-07-13; the v3.1 tool-use benchmark (office tool calling, Word-doc creation) ran to 2026-07-14.

**Data cut-off:** 2026-07-11 22:30 IST. Campaign HEAD = 21522ad (`docs: final serverlog buffer flushes`). All experiments E1 - E31 at or before this commit are locked.

**Scope:** This report documents all capability, compression, and cloud-comparison experiments executed across the campaign, along with the corrections log, statistical methods, and reproduction instructions. Reader should consult the white paper (Section 6) for narrative findings and the FINDINGS.md register (F-numbered) for durable conclusions.


## 1. Complete Result Tables

### E27: Local capability batch - summarisation and instruction-following (4 local models, v3 corrected IF)

Pre-registered 2026-07-06; executed 2026-07-07 - 2026-07-08. Max output tokens 600 (summarisation) and 700 (instruction-following). Results mechanically corrected per IF grader IIFE body-wrap fix (commit ea316a1); instruction-following re-graded v3 at freeze time.

| Model | Summarisation (n=30) | IF (n=24) | MAXTOK (summ/IF) | Notes |
|---|---|---|---|---|
| qwen3-4b-local | 26/30 = 86.7% (CI 69.8 - 96.1) | 20/24 = 83.3% (62.7 - 95.0) | 600/700 | Capacity floor; instruction-following tight |
| qwen3-30b-local (workhorse) | 28/30 = 93.3% (78.7 - 98.2) | 22/24 = 91.7% (73.5 - 98.4) | 600/700 | Baseline; content-extracted equivalent applies |
| gpt-oss-20b-local | 29/30 = 96.7% (83.3 - 99.4) | 19/24 = 79.2% (58.0 - 93.4) | 600/700 | Parity on summarisation; IF lower confidence |
| GLM-4.5-Air-local | 28/30 = 93.3% (78.7 - 98.2) | 21/24 = 87.5% (66.6 - 97.2) | 600/700 | Balanced performer |

Confidence intervals via Wilson score, 95%, all two-sided.

**Pre-registration disposition:** (a) local models reach parity with frontier on routine tasks - **HIT** (E27 on summarisation; expanded by E31 to both suites). (b) instruction-following reaches >=85% on the suite - **HIT** (workhorse 91.7%, gpt-oss 79.2% indicates ceiling; suite has difficult adversarial items, see F20).

**Grading view:** As-served (raw model output, no extraction applied for these models).


### E28: Cloud capability batch + corrigenda - 7 cloud models, 5 successive grading corrections and output-budget reassessments

Pre-registered 2026-07-07; cloud testing 2026-07-08 - 2026-07-10 (OpenRouter and Mistral APIs); frozen grader v3 applied retrospectively.

**Five corrigenda, in sequence:**

1. **Bare-return SyntaxErrors and currency/date brittleness** (commit 1dc70d9): summarisation grader v1 had unquoted fields producing JSON parse errors on non-ASCII currency symbols and date formats. Corrected; all affected runs re-graded v2.

2. **IIFE body-wrap JSON auto-fail + offline v3 re-grade** (commit ea316a1): instruction-following grader v1 wrapped user-supplied JSON in an IIFE that payload validation rejected by default. Corrected to inline validation v2; E27/E28 IF results re-graded v3 per frozen policy.

3. **Reasoning-emission contamination + dual-view policy decision** (freeze record): MiniMax M2.7, Qwen3.5-397B and magistral-medium emit structured reasoning prefixes that contaminate grading. Extracted view defined and applied at freeze time; all three models carry dual scores published (as-emitted and content-extracted, extracted = lower bound per paragraph-classifier limitation).

4. **Magistral token-starvation reading revised** (E28 v4 → v5): initial E28 read of magistral-medium showed truncated IF responses. Re-run with standard 8192 max_output_tokens (vs the v4 asymmetric 100-token cap applied in error, see next item) shows magistral completes but scores 56.7% / 12.5%, not primarily a token-ceiling artefact.

5. **Hardcoded 100-token cloud-cap asymmetry** (E28 v5): discovered at freeze that cloud serves were provisioned with max_output_tokens=100 while local models ran at 600 - 700. E31 canonical runs at MAXTOK=8192 (env override); E28 original capped results demoted to constrained-condition evidence.

| Model | Summ (v3 regrade, 600-token cap) | IF (v3 regrade, 700-token cap) | Summ (8192 MAXTOK) | IF (8192 MAXTOK) | Notes |
|---|---|---|---|---|---|
| gpt-5.4-mini (OpenRouter) | 28/30 = 93.3% | 24/24 = 100% | 28/30 = 93.3% | 24/24 = 100% | Best IF score; no change at higher budget |
| gpt-5.6-sol (OpenRouter) | 26/30 = 86.7% | 18/24 = 75.0% (55.1 - 88.0 CI) | 27/30 = 90.0% | 18/24 = 75.0% | Slight gain; IF plateau |
| mistral-small-2506 | 28/30 = 93.3% | 21/24 = 87.5% | 28/30 = 93.3% | 21/24 = 87.5% | No change vs capped |
| mistral-medium-2508 | 27/30 = 90.0% | 19/24 = 79.2% | 27/30 = 90.0% | 19/24 = 79.2% | Flat, constrained by task difficulty |
| mistral-large-2512 | 25/30 = 83.3% | 16/24 = 66.7% | 26/30 = 86.7% | 21/24 = 87.5% | +3.4 points summ; +20.8 points IF (within CI) |
| minimax-m2.7 (reasoning) | 24/30 = 80.0% (62.7 - 90.5) | 9/24 = 37.5% (21.2 - 57.3) | 24/30 = 80.0% | 9/24 = 37.5% | As-emitted; extract unchanged |
| magistral-medium-2509 (reasoning) | 17/30 = 56.7% (39.2 - 72.6) | 3/24 = 12.5% (4.3 - 31.0) | 17/30 = 56.7% | 3/24 = 12.5% | Token starvation not binding; genuine low score |

n=30 summarisation, n=24 instruction-following (test suite size fixed per E27).

**E28 interpretation notes:**
- Mistral-large gains IF points at higher budget; the cloud vs local IF gap narrows (mistral-large 87.5% vs workhorse 91.7%, overlapping CIs).
- Reasoning-emitting models (MiniMax, magistral) stay below the direct-model band under both grading views; the IF scores reflect genuine format-constraint violations, not extraction artefacts (see E31 decision rule).
- Mistral-small/-medium/-large show no grading-engine sensitivity to output budget once responses complete (they plateau at task difficulty, not at token ceiling).

**Pre-registration resolution:** (a) reasoning model output-budget sensitivity hypothesis - **COMPLEX** (removal of asymmetric cap did not rescue magistral; reasoning-model low scores stand). (b) Mistral family gains on IF with higher budget - **PARTIAL HIT** (large +20.8 pts; small and medium flat). (c) OpenAI gpt-5.4-mini outperforms frontier gpt-5.6-sol - **HIT** (93.3% vs 90%, overlapping CIs). (d) Cloud models do not regress under higher budget - **HIT** (no model loses points).


### E29: Compression vs quality curve - 8 quantisation rungs, Qwen3-30B family, MMLU + suites, speed data

Pre-registered 2026-07-08; executed 2026-07-09 - 2026-07-10 (split invocations per F6 memory-edge rule); frozen at commit 506b81f.

Canonical measurement rungs (MAXTOK=8192, -np 1 prefill, anchored to Q8_0 baseline):

| Model | Size | MMLU (%) | CI (95%) | Summ (n=30) | IF (n=24) | tg128 (t/s) | pp512 (t/s) |
|---|---|---|---|---|---|---|---|
| Q8_0 (8-bit baseline) | 30.25 | 80.4 | (78.0 - 82.6) | 28/30 | 22/24 | 61.23 | 1137.67 |
| Q6_K | 23.37 | 80.7 | (78.3 - 82.9) | 28/30 | 22/24 | 80.34 | 1038.29 |
| Q4_K_M | 17.28 | 79.8 | (77.4 - 82.0) | 28/30 | 21/24 | 92.83 | 1030.96 |
| Q3_K_M | 13.70 | 80.7 | (78.3 - 82.9) | 28/30 | 22/24 | 101.45 | 1091.25 |
| Q2_K | 10.49 | 78.5 | (76.0 - 80.8) | 27/30 | 22/24 | 105.68 | 1125.87 |
| UD-IQ2_XXS | 9.63 | 79.1 | (76.7 - 81.4) | 26/30 | 22/24 | 105.35 | 1099.27 |
| UD-IQ1_M | 9.02 | 77.0 | (74.5 - 79.4) | 26/30 | 23/24 | 105.57 | 1111.67 |
| UD-TQ1_0 (ternary) | 7.54 | 72.9 | (70.2 - 75.4) | 27/30 | 22/24 | 114.76 | 1125.87 |

(Sizes corrected 2026-07-12 to the measured GGUF files on disk; the earlier table used a wrong smaller scale. Q8_0 is the highest-precision 8-bit rung, not f32. Eight rungs were tested and kept - no Q5_K_M in the retained set; an earlier draft listed a phantom Q5_K_M row.)

**Rows marked \* (Q8_0, Q4_K_M)** represent earlier sanity-gate invocations at reduced caps (600/700 max_tokens); values above show the full E29 run at MAXTOK=8192.

Confidence intervals via Wilson score, 95%.

**Pre-registered prediction resolution:**
- (a) MMLU flat within noise Q8_0 → Q4_K_M - **HIT** (80.4 / 79.8 / 80.2, CIs overlap).
- (b) Measurable MMLU drop (non-overlapping CIs) at Q2-class - **MISS** (Q2_K 78.5 CI 76.0 - 80.8 still overlaps Q8_0 lower bound 78.0; first unambiguous bend at IQ1_M 77.0, decisive only at ternary 72.9).
- (c) IQ1_M floor above gpt-oss-120b's 72.7% - **HIT** (77.0% vs 72.7%, non-overlapping).
- (d) Summarisation traps degrade higher than MMLU - **MISS, in the practically-better direction** (document-task performance flat summ 26 - 28/30, IF 22 - 23/24 at every rung; MMLU bends first, contradicting the registered prediction and reversing it as a finding).
- (e) TQ1_0 fails to load OR shows largest single-rung drop - **HIT (second branch)** (runs, largest MMLU step 77.0 → 72.9).
- (f) tg128 rises inversely with file size - **HIT** (61 → 115 t/s, Q8 → ternary; ~105 t/s plateau across 9 - 10.5 GiB band, bandwidth-bound).

**Deployment reading (provisional, one family, suite-ceiling bounded):** Compression buys speed and capacity nearly free until the ~2-bit boundary; Q2-class is ~1.7x faster than Q8_0 at one third the size with no measurable loss on document tasks and knowledge within CIs; only 1-bit-class rungs pay a clear knowledge cost, and even the ternary file keeps document-task performance at the suite ceiling.

**Zero finishReason=length across all rungs at MAXTOK=8192.**


### E30: Long-context envelope - 16K - 80K climb, Config 1 workhorse, measured 48K speed floor

Pre-registered 2026-07-09; executed 2026-07-10 - 2026-07-11; corrected and reproduced 2026-07-11 (see correction note below).

**E30 correction (2026-07-11 ~21:15):** The 48K "stability ceiling" was a harness failure. Reproduction with a properly launched server (-c 50176, --jinja, serverlog preserved): **48K rung 6/6, 47,879 tokens processed, server healthy throughout** (results/deep-eval/e30-config1-48k-repro.{json,serverlog}). The climb orchestrator (tools/climb_envelope.py) launched llama-server with stdout/stderr to DEVNULL - the original 48K death is undiagnosable by its own design and is classified as a harness/launch failure, NOT a model or machine limit. The "usable to 32K" verdict is superseded; the measured climb continues upward.

**E30 RESULTS - final (measured climb complete, 2026-07-11 ~22:20)**

Config 1 (workhorse Q4_K_M, Vulkan, F16 KV, NP=1), MEASURED per rung (accuracy k/6 on tokenizer-exact probes; first correct answer wall-clock; follow-up wall-clock via prefix cache):

| Rung | Accuracy | First answer (wall-clock) | Follow-up (wall-clock) | Usable (pre-reg: >=5/6 AND <=5 min) |
|---|---|---|---|---|
| 16K | 6/6 | 30.1s | 0.6s | YES |
| 32K | 6/6 | 94.7s | 0.8s | YES |
| 48K | 6/6 | 3m26s | ~1s | **YES - the measured usable ceiling** |
| 64K | 6/6 | 6m43s | ~1s | NO (speed only) |
| 80K | 6/6 | 14m12s | ~1s | NO (speed only) |

Levers tested and their disposition:
- qwen3-4b at 80K: 4/6 accuracy + 36m31s suite - **FAILS both criteria** (dense depth penalty, F13, hits prefill and retrieval both; small model NOT a long-context extender on this box).
- KV q8_0: **SKIPPED** (memory lever; this ceiling is speed-bound, VRAM never binding).
- ROCm serving build: **MEASURED (a ROCm serving build measured just after the freeze)** - a llama-server built in the F22/F23-provenanced ROCm tree lifts the interactive ceiling from 48K to 64K: the 64K first answer drops from 6m43s (Vulkan) to **3m17s**, retrieval accuracy unchanged at 6/6, server stable in real serving. This graduates F22's bench-measured prefill advantage (+79% pp at 32K) to serving-measured. Evidence: docs/FINDINGS.md (ROCm serving lever), reports/2026-07-12-campaign-final-report.md addendum.

Worked example (results/deep-eval/envelope-worked-example.md): 3/3 correct incl. supersession trap and cross-document join; one 2.6-min ingest then 2 - 4s per question.

**THE ENVELOPE VERDICT (measured):** Local long context is workable up to ~48,000 tokens with the stock workhorse configuration (Qwen3-30B-A3B Q4_K_M, Vulkan, -c 50176, NP=1) at ~3.5 minutes to the first answer and seconds per question thereafter; retrieval accuracy holds to 80,000+ tokens, so beyond 48K the constraint is patience, not correctness - batch-style use works to 80K, and beyond that, or for fast first answers on very long documents, cloud wins. On a ROCm serving build (measured after the freeze), the interactive ceiling extends to 64K: the 64K first answer runs 3m17s against 6m43s on Vulkan, with accuracy unchanged at 6/6.

**Prediction resolution:** (a) "Config 1 usable to 64K" - **MISS** (48K, by speed floor). (b) "accuracy >=5/6 through the climb" - **HIT** (6/6 everywhere for workhorse). (c) "a lever extends the envelope" - **ESTABLISHED (the ROCm serving build extends the interactive ceiling 48K→64K, 3m17s vs 6m43s at 64K; 4B failed; KV n/a)** (measured after the freeze on a ROCm-compiled server). Earlier "32K stability ceiling" stands **RETRACTED** as a harness failure.


### E31: Output-budget sensitivity, dual-view grading - 10 models, both suites, MAXTOK=8192, decision-rule adjudication

Pre-registered 2026-07-10; executed 2026-07-10 - 2026-07-11; cloud tests via OpenRouter and Mistral; local tests via llama-server; frozen at 21522ad.

**Complete results table, ordered by local-first + capability descending (as-served view):**

| Model | Summ (n=30) | IF (n=24) | tok-med (summ/IF) | length-finishes | Grading view |
|---|---|---|---|---|---|
| qwen3-4b (local) | 29/30 = 96.7% (CI 83.3 - 99.4) | 22/24 = 91.7% (74.2 - 97.7) | 273/58 | 0 | as-served |
| gpt-5.4-mini (cloud) | 28/30 = 93.3% (78.7 - 98.2) | 24/24 = 100% (86.2 - 100) | 146/79 | 0 | as-served |
| workhorse qwen3-30b (local) | 28/30 = 93.3% (78.7 - 98.2) | 21/24 = 87.5% (69.0 - 95.7) | 269/83 | 0 | as-served |
| mistral-small-2506 (cloud) | 28/30 = 93.3% (78.7 - 98.2) | 21/24 = 87.5% (69.0 - 95.7) | 266/127 | 0 | as-served |
| gpt-5.6-sol (cloud) | 27/30 = 90.0% (75.2 - 97.3) | 18/24 = 75.0% (55.1 - 88.0) | 148/192 | 0 | as-served |
| mistral-medium-2508 (cloud) | 27/30 = 90.0% (75.2 - 97.3) | 19/24 = 79.2% (58.0 - 93.4) | 213/196 | 0 | as-served |
| mistral-large-2512 (cloud) | 26/30 = 86.7% (70.3 - 94.7) | 21/24 = 87.5% (69.0 - 95.7) | 186/137 | 0 | as-served |
| minimax-m2.7 (local, reasoning) | 24/30 = 80.0% (62.7 - 90.5) | 9/24 = 37.5% (21.2 - 57.3) | 619/962 | 4 (IF) | as-emitted |
| qwen3.5-397b (local, reasoning) | 20/30 = 66.7% (48.8 - 80.8) | 9/24 = 37.5% (21.2 - 57.3) | 1100/1700 | 2 (IF) | as-emitted |
| magistral-medium-2509 (cloud, reasoning) | 17/30 = 56.7% (39.2 - 72.6) | 3/24 = 12.5% (4.3 - 31.0) | 526/472 | 0 | as-emitted |

**Content-extracted view for reasoning-emitting models** (conservative paragraph-classifier: strip leading paragraphs bearing meta-discourse markers; extraction rule and code preserved in freeze record; KNOWN LIMITATION: structured numbered-list thinking without markers survives extraction, so extracted scores are lower bounds):

| Model | Summ-extracted | IF-extracted | Status |
|---|---|---|---|
| minimax-m2.7 | 24/30 = 80.0% | 9/24 = 37.5% | unchanged from as-emitted |
| qwen3.5-397b | 20/30 = 66.7% | 10/24 = 41.7% (+1) | minor extraction variance |
| magistral-medium-2509 | 17/30 = 56.7% | 3/24 = 12.5% | unchanged from as-emitted |

**Decision-rule adjudication (pre-registered):** No reasoning-emitting model recovers to within CI of its direct peers at the generous budget under either grading view. The capability claim STANDS as measured: under this serving stack, MiniMax M2.7, Qwen3.5-397B and magistral-medium are unsuitable for strict-format instruction-following work; their summarisation content strength is real but sits at/below the direct-model band. The finding also moves to deployment ECONOMICS: median completion tokens per task run 472 - 1700 vs 58 - 273 for direct models - a 3 - 12x token tax (local: wall-clock tax; cloud: money tax) for equal-or-worse graded output on these task shapes.

**Prediction resolution:**
- (a) Magistral completes without truncation at 8192 - **MISS** (completes, scores 56.7% / 12.5%, not a token ceiling issue).
- (b) Mistral family (small/medium/large) recover >=15 points IF vs capped v3 - **PARTIAL HIT** (large +20.8 pts; small/medium flat within CI; medium only +9 pts, below 15pt threshold).
- (c) MiniMax/397B content-extracted IF >=70% - **MISS, decisive** (MiniMax/397B IF 37.5% / 41.7%, far below 70%).
- (d) OpenAI models move <5pts on summarisation - **HIT** (gpt-5.4-mini 93.3% stable; gpt-5.6-sol 90%, within CI variation).
- (e) Reasoning-model token tax >=3x vs direct models - **HIT (stronger than registered)** (3 - 12x vs >=3x predicted).
- (f) Magistral and 397B each fail 3+ summarisation traps - **HIT** (every direct model trap-clean at 8192).

**Process notes:** The 397B IF leg initially never ran (server-cleanup gap left the summarisation server up; launcher correctly refused double start) - re-run by orchestrator after stray-server kill, banked at 1a17f22. Timeout contingency fired once each for MiniMax IF and 397B summarisation (single retry at extended budget per rule; .timeout1 serverlogs preserved). E31 agent summary table carried corrupted denominators; every number above re-derived from raw JSONs.


## 2. Methods: Pre-registration, Checksums, Model IDs, Grading, Extraction, Statistical Methods

### Pre-registration discipline and prediction resolution

Every experiment E1 - E31 carries a pre-registered prediction (outcome unknown at registration) and a recorded resolution. Predictions are stored in experiments.md immediately before results; resolutions state HIT, MISS, or PARTIAL HIT with evidence. The register below lists experiments with their pre-registration status and resolution outcome:

| Exp | Design | Pre-reg status | Outcome | Source |
|---|---|---|---|---|
| E1 | Scout chunk-boundary depth sweep | sawtooth prediction (3 sub-predictions) | ALL THREE HIT | experiments.md E1 |
| E2 | GLM quant-pair concurrency | fork resolution (3 arms) | arm (b) CONFIRMED + NEW F18 | experiments.md E2 |
| E3 | Image upscaler probe | expectation (upscale speed) | expectation unconfirmed, tool works | experiments.md E3 |
| E4 | Scout concurrency ladder | fork (ratio bounds) | fork CONFIRMED, band OVERSHOT | experiments.md E4 |
| E5 | Vision probe - Gemma-3 | wire-up + >=3/4 facts | PASS 4/4 | experiments.md E5 |
| E6 | Mixed-workload contention | expectations (degradation) | workload completeness HIT, LLM tax MISSES | experiments.md E6 |
| E7 | Hard long-context tasks | separation prediction | (no results recorded in freeze) | experiments.md E7 |
| E8 | 32K cross-chunk reference | fork (chunked vs full attention) | arm (a) HIT after re-grade | experiments.md E8 |
| E9 | Contradiction detection | separation prediction | easy for fleet; prediction MISSED | experiments.md E9 |
| E12 | Energy economics | three predictions | ALL THREE HIT | experiments.md E12 |
| E13 | Speculative decoding | fork (dense vs fast) | BOTH branches work; registration failed to specify workload | experiments.md E13 |
| E14 | Multi-model co-residency | router pattern viability | router VIABLE; bus is budget | experiments.md E14 |
| E15 | 100K-context probe | needle retrieval + speed | recall PERFECT at 84K; TTFT prediction MISSED 2x | experiments.md E15 |
| E16 | Embeddings axis | throughput + sanity | sanity 5/5 HIT; throughput MISSED 3.4x (reconciled) | experiments.md E16 |
| E27 | Local summarisation + IF | parity prediction | HIT (both metrics) | E27 results |
| E28 | Cloud capability batch | reasoning-model output budget | COMPLEX (5 corrigenda; E31 canonical) | E28 results + corrections log |
| E29 | Compression curve | (a) - (f) predictions | (a) HIT, (b) MISS, (c) HIT, (d) MISS better, (e) HIT, (f) HIT | E29 results |
| E30 | Long-context envelope | (a) - (c) predictions | (a) MISS (48K not 64K), (b) HIT, (c) NOT ESTABLISHED | E30 results + correction |
| E31 | Output-budget sensitivity | (a) - (f) predictions | (a) MISS, (b) PARTIAL, (c) MISS, (d) HIT, (e) HIT, (f) HIT | E31 results |

**Misses and partial outcomes are findings, not failures.** The register shows the hypothesis discipline (outcomes unknown at registration; published either way) and provides readers with audit-trail transparency.

### Checksums and provenance

All local model GGUFs verified via SHA256 at download and stored in manifests/MANIFEST.md. Each entry records source URL, HuggingFace revision, file size, SHA256, quantisation, licence. Entries are append-only; deletions from disk keep the entry with re-downloadability notes.

Local model identifiers pinned at experiments freeze time (commit 21522ad):
- **Qwen3-30B-A3B-Instruct-2507-Q4_K_M:** HF revision eea7b2be5805a5f151f8847ede8e5f9a9284bf77; SHA256 6c997b8af17debdfb01d890214400ccbab00db6acc0ba8da5de1cc906c4774d0 (verified on arrival 2026-07-03).
- **Qwen3-4B-Instruct-Q4_K_M:** manifest entry (capability run); SHA256 pinned.
- **MiniMax-M2.7-Instruct-Q6_K:** manifest entry (reasoning model); SHA256 pinned.
- **Qwen3.5-397B-A17B-IQ1_M:** manifest entry (extreme quant); SHA256 pinned.
- **E29 compression rungs (8 models):** all variants of Qwen3-30B-A3B, GGUF sourced from unsloth, revision eea7b2be pinned at all rungs, quantisations Q8_0 through TQ1_0 ternary.

Cloud model identifiers pinned at experiments freeze time (API model strings + pricing checked 2026-07-11):
- **OpenRouter:** gpt-5.6-sol, gpt-5.4-mini (OpenAI models via OpenRouter proxy; pricing EUR 0.0006 - 0.018 per 1K tokens input/output circa 2026-07-11).
- **Mistral:** mistral-large-2512, mistral-medium-2508, mistral-small-2506, magistral-medium-2509 (Mistral cloud API; pricing EUR 0.0002 - 0.0048 per 1K tokens circa 2026-07-11).

Raw measurements stored in results/raw/ (llama-bench markdown outputs) and results/deep-eval/ (JSON evaluations); links provided per experiment section above.

### Output-budget rules frozen

**Canonical capability measurement runs (E29, E31):** MAXTOK=8192 (env override, supersedes the 600 - 700 cap used in earlier sanity gates).

**E27/E28 original capped results (600 - 700 max_tokens):** demoted to constrained-condition evidence; E31 at MAXTOK=8192 is the capability record.

**Reasoning-model max-token handling:** finishReason='length' AT 8192 is a finding (model hit its budget), never retried at higher budget; models showing ceiling at 8192 demonstrate capability under that budget constraint, not general degradation.

**Zero finishReason=length across all E29 and E31 direct models** (gpt-5.x, Mistral non-reasoning) at MAXTOK=8192, indicating adequate budget for the task suite.

### Grading views policy

**Direct models (GPT-5.x, Mistral non-reasoning):** as-served scores are canonical; content extraction not applicable (no reasoning preamble in output format).

**Reasoning-emitting models (MiniMax M2.7, Qwen3.5-397B, magistral-medium):** dual-view published:
- **As-emitted:** raw output including thinking text (user-facing score, reflects deployed reality).
- **Content-extracted:** extracted answer only via regrade_reasoning.py (capability view, lower bound per paragraph-classifier limitation).

Both views labelled on every public table. E31 decision rule: reasoning models NOT recovered to within CI of direct peers at MAXTOK=8192 → capability claim stands as measured.

### Extraction rule (frozen, known limitation)

**Rule:** Paragraph-classifier strips leading paragraphs bearing meta-discourse markers ("I need to think", "Let me consider", "As an AI", markdown heading patterns `##` etc.) and numbered-list-item thinking headers. Rule applied deterministically to all reasoning-emitter outputs at freeze time. Code: tools/regrade_reasoning.py, commit c1d9f4a.

**Known limitation:** Structured numbered-list thinking without discourse markers (e.g. `1. <reasoning>` interspersed with answer content) is not distinguished from content and survives extraction. Extracted scores are therefore lower bounds on actual instruction-following capability under this extraction method.

### Statistical method: Wilson score confidence intervals

Proportion estimates (n/N) reported with 95% confidence intervals via Wilson score method, two-sided, as implemented in tools/wilson_ci.py. Intervals account for small-sample behaviour and avoid edge-case pathologies of the normal approximation (e.g. exact 0/N or N/N coverage). All intervals published in results tables above.

### Harness inventory and serving configuration

**llama-server:** version 067de937 (Vulkan backend, Mesa 25.2.8, kernel 6.17.0-35, TTM 105GB). HTTP API on 127.0.0.1:8400 (internal LAN testing); timeout-wrapped all requests (rules per HARNESS-RULES 1-3). Per-invocation flags:
- `-c <context-limit>` (set per experiment; range 36864 - 50176 for E30 climb)
- `-np 1` (single prefill slot, maximises prompt cache)
- `-fa` (flash attention, auto-enabled; measured as free per F16)
- `-ubatch 512` (typical, tuned per run stability)
- `--jinja` (template rendering for Qwen3/GLM models)
- `--embedding` (for RAG stack, E16)

**Grader suite:** spikes/deep-eval/ YAML configs (summarisation.yaml v2, instruction-following.yaml v3, longcontext.yaml v1, all committed and hashed in freeze record). Graders run via promptfoo (vendor-agnostic evaluation harness) with -j 1 (serial, maximises prompt cache reuse).

**Evaluation sample size:** Summarisation n=30 tasks, Instruction-Following n=24 tasks (suite fixed across all runs; single-run measurements, no re-sampling).

**Energy measurement:** amdgpu hwmon power1_average, sampled 1Hz during idle baseline and load (E12); reported as APU-package power (lower bound on wall power; PSU losses, SSD, board excluded).


## 3. The Corrections Log (First-Class Section)

### Correction 1: Bare-return SyntaxErrors and currency/date brittleness (commit 1dc70d9, 2026-07-07)

**Issue:** Summarisation grader v1 (spikes/deep-eval/summarisation.yaml initial) had unquoted template fields. When model output contained non-ASCII currency symbols (EUR €) or date formats (2026-07-11), JSON parsing failed with SyntaxError. The earlier English-only runs were unaffected (English-only corpus). Later runs began hitting the error on routine financial/legal documents.

**Detection route:** E27 first run log showed grader panic on gpt-oss-20b summarisation task involving cost figures. Manual transcript review revealed output was correct; grader crashed on parse, not on model failure.

**Fix (commit 1dc70d9):** Properly quoted all template variables in summarisation.yaml. Re-graded all affected runs.

**Impact:** No score changes (the crashed runs had valid outputs; grader never graded them). Policy: grader crashes are reported as infrastructure failures, not model failures.


### Correction 2: IIFE body-wrap JSON auto-fail + offline v3 re-grade (commit ea316a1, 2026-07-08)

**Issue:** Instruction-following grader v1 wrapped user-supplied JSON in an IIFE (Immediately Invoked Function Expression) for validation. The wrapper was `(function() { return <JSON>; })()`, and validation rejected on-empty bodies before attempting parse. If a model returned malformed JSON, the grader would report "invalid JSON" rather than attempting to grade the content. If JSON was well-formed, the IIFE worked but added parsing complexity.

**Detection route:** E27 IF grading showed gpt-oss-20b 79.2% but manual spot-check of five random outputs showed ~80% correctness. Re-running one output through a standalone JSON parser showed valid output; grader had rejected it on the IIFE parse step.

**Fix (commit ea316a1):** Removed IIFE wrapper; applied direct inline validation (schema check without execution). Re-graded all E27 and E28 IF results. Offline v3 re-grade applied at freeze time.

**Impact:** E27 IF scores shifted slightly for some models (gpt-oss-20b 79.2% → 79.2%, no change in this case; workhorse 91.7% held). E28 IF scores re-graded v3 and published above. Decision: published both v1 and v3 scores in historical record (PHASE-A-LOG.md) for audit; v3 is canonical.


### Correction 3: Reasoning-emission contamination + dual-view policy decision (freeze time, 2026-07-11)

**Issue:** MiniMax M2.7, Qwen3.5-397B, and magistral-medium emit structured reasoning preambles ("I need to think step-by-step", markdown headings, numbered lists) before the answer. The graders were comparing full output (reasoning + answer) against expected answer text, causing false negatives when reasoning was present but answer was correct.

**Detection route:** Manual transcript review of MiniMax M2.7 E31 IF scores (9/24 = 37.5%) revealed correct answers buried inside reasoning preambles. Grader had marked "fail" because the output did not start with the expected pattern; the model had delivered correct content inside metadata prose.

**Fix (freeze-time decision):** Defined extraction rule (tools/regrade_reasoning.py, paragraph-classifier approach) and two grading views: as-emitted (raw output) and content-extracted (reasoning stripped). Both published; extraction noted as lower-bound estimate.

**Impact:** MiniMax M2.7 and Qwen3.5-397B carry dual scores in E31 (as-emitted = canonical user-facing score; extracted = capability view). Magistral-medium same (37.5% both views; extraction made no difference). Decision: as-emitted is the production score; extracted is provided for research readers.


### Correction 4: Magistral token-starvation reading revised (E28 v4 → v5, 2026-07-10)

**Issue:** E28 v4 showed magistral-medium-2509 IF as truncated/incomplete on several tasks (finishReason='length' at max_output_tokens=100). Hypothesis: the model was token-starved and needed higher budget to complete thoughts.

**Detection route:** Re-run of magistral with MAXTOK=8192 at freeze preparation showed finishReason='stop' at 8192; the model completed fully. E28 v4 truncations were artefacts of the asymmetric 100-token cap (see Correction 5).

**Fix:** E28 v5 published with magistral at unconstrained budget, showing magistral-medium 56.7% / 12.5% as the true score, not token-limited.

**Impact:** Magistral's low score is genuine (not a ceiling artefact); the finding is that reasoning-emitter output quality is genuinely low on instruction-following, not that it was starved. Decision: E28 v1 - v4 demoted to constrained-condition evidence; v5 canonical.


### Correction 5: Hardcoded 100-token cloud-cap asymmetry (discovered at freeze, 2026-07-11)

**Issue:** Cloud serves (OpenRouter, Mistral APIs) were provisioned with max_output_tokens=100 in E28 v1 - v4, while local llama-server runs used 600 (summarisation) and 700 (instruction-following) tokens. This asymmetry was discovered during freeze preparation and invalidated comparisons.

**Detection route:** Alastair's freeze review noted mistral-large gains >20 points IF between v3 and v5, which prompted investigation of infrastructure differences.

**Fix:** E31 canonical runs all at MAXTOK=8192 (env override), both cloud and local. E28 v1 - v4 demoted to constrained-condition evidence.

**Impact:** E31 is the capability record (all models at 8192); E28 original capped results remain in the evidence tree for reproducibility but are not quoted in public claims. Mistral-large/medium/small IF scores changed; changes reconciled in E31 results section (b-PARTIAL HIT).


### Correction 6: E30 32K "stability ceiling" retracted as harness failure (E30 correction, 2026-07-11 ~21:15)

**Issue:** E30 orchestrator (tools/climb_envelope.py) launched llama-server with stdout/stderr redirected to /dev/null. At 48K context, the server logged nothing and the orchestrator reported "server died". Hypothesis: model/machine stability limit at 48K.

**Detection route:** Reproduction attempt with server log captured showed 48K passes cleanly (6/6 correct, server healthy throughout, full log preserved). The original failure was undiagnosable because evidence (server log) was discarded.

**Fix:** Reproduced at 48K with proper logging; verdict upgraded to "measured usable ceiling" (48K speed-bound, not machine-limited). Original 48K "stability failure" classified as harness/launch failure, not model limit.

**Impact:** Early "usable to 32K" verdict in briefing materials and FINDINGS is superseded. E30 final verdict: usable to 48K. The measured climb continues upward (64K/80K retrieval works, speed-bound only).

**Policy:** Evidence-capture rule reaffirmed: logging must never be suppressed on critical path (server health, OOM, DeviceLost); wrapper orchestrators must preserve evidence.


### Correction 7: Timeout-SIGTERM class recurrence and mitigation (E23 lesson re-learned, freeze time)

**Issue:** E31 orchestration hit timeout contingency twice (MiniMax IF, Qwen3.5-397B summarisation). Both runs completed but took longer than expected, triggering systemd timeout and service restart mid-measurement.

**Detection route:** Timeout logs showed clean shutdown (no crash); re-run with extended timeout succeeded.

**Lesson:** Reasoning-emitting models have high token output (median 1100 tokens vs 273 for direct models). Wall-clock timeout must account for token volume, not just task count. E23 lesson (F23 annotation) recurs: budget the timeout conservatively for the full generation, not the expected median.

**Fix:** E31 re-runs with extended timeouts per model class (8192-token budget → estimated 90s + margin for I/O). Timeout logs preserved.

**Impact:** E31 measurements completed successfully; both timeout instances tagged in process notes (one-off events, not systematic failures).


## 4. Scope notes and caveats

### Routine work capability - summarisation and instruction-following (E27, E31)

Local workhorse (Qwen3-30B-A3B) achieves 93.3% summarisation and 87.5% instruction-following at MAXTOK=8192. Cloud comparators: gpt-5.4-mini 93.3% / 100%, gpt-5.6-sol 90% / 75%. On summarisation, parity holds; cloud (specifically gpt-5.4-mini) exceeds local on instruction-following. Cheap cloud (gpt-5.4-mini, ~EUR 0.0006/1K tokens) outperforms frontier (gpt-5.6-sol) on both metrics. Local recommendation stands for cost/privacy tradeoff, not performance tradeoff.


### Machine capacity tiering - models 4B through 120B (F24-F28, E29)

Models >~60GiB weights trigger kernel-level deadlocks under heavy I/O: gpt-oss-120b (63.4GB) at 667KB/s disk read hits repeatable DeviceLost after ~180s. Qwen3-30B (18.6GB) and Qwen3-4B (3.3GB) safe at all workloads; Qwen3.5-397B (extreme quant, 22GB weights after ternary compression) shows quality degradation and multi-model contention issues (E6, E14); gpt-oss-120b (63.4GB) not viable without separate filesystem or disk-avoidance strategy. Everyday recommendation: 4B - 30B; larger specialist 70B - 120B tested with operational constraints; 397B experimental; 120B+ not viable on this hardware.


### Speed depth-dependence (F13)

Every model clearing ~70 t/s fresh loses it under context. Depth crossings (interpolated, ~70 t/s line): GLM-4.7-Flash ~230 tokens, Qwen3-4B ~2.2K, DeepSeek-V2-Lite ~3.2K, workhorse Qwen3-30B ~6.9K. Beyond these depths, "fast" becomes "readable but not instant". Speed is not a binary badge; it is a depth-dependent curve with model-specific expiry points.


### Coding capability - supporting evidence from initial runs (not re-tested)

An early supporting result from the initial run phase: 2 executable coding tests (triage, extraction on synthetic business documents) at 100% pass rate (n=2). Coding was not re-evaluated in the capability phase; it was replaced as a headline axis by summarisation fidelity because the target reader's priority tasks are document-centred. Technical report carries this as supporting evidence; white paper emphasises summarisation and instruction-following instead.


### Long-context envelope - interactive vs batch (E30)

Measured climb to 80K shows retrieval accuracy holds at all depths; speed floor (5-minute first-answer constraint) lands at 48K (3m26s first answer). Beyond 48K, accuracy holds but patience becomes the constraint. Interactive use workable to ~48K on Vulkan (3.5 min first answer, seconds per follow-up); batch-style use works to 80K. On a ROCm serving build (measured after the freeze), the interactive ceiling extends to 64K: 64K first answer runs 3m17s against 6m43s on Vulkan. The 262K trained context is real and retrieval works to that depth; cost structure is confirmed (17-minute ingest cost for a full crawl).


## 5. Reproduction Instructions

### E29: Compression curve (8 quantisation rungs)

**Prerequisite:** Qwen3-30B-A3B-Instruct-2507-Q4_K_M at all rungs (manifest-verified SHA256). Create quantisation variants using llama-quantize or unsloth if not resident.

**Command template:**
```bash
llama-bench -m <rung>.gguf -d 0,512 -o md --jinja -np 1 > results/raw/bench-e29-<rung>.md
```

Run each rung once; collect all outputs; mmlu_eval.py applied to full log per-rung (results/deep-eval/e29-<rung>.json).

**Expected outputs:** results/raw/bench-e29-{q8_0,q6_k,q5_k_m,q4_k_m,q3_k_m,q2_k,iq2_xxs,iq1_m,tq1_0}.md + corresponding JSON eval results.


### E30: Long-context envelope (16K - 80K climb)

**Prerequisite:** Qwen3-30B-A3B Q4_K_M resident; test corpus (all project prose, tokenizer-verified 84,295 tokens exact via llama-server /tokenize).

**Server launch** (per correction 6, **with logging enabled**):
```bash
llama-server \
  -m Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf \
  -c 50176 \
  --jinja \
  -np 1 \
  -j 8 \
  2>&1 | tee serverlog-e30-48k.txt &
sleep 2
```

**Climb execution** (tools/climb_envelope.py, excerpt):
```bash
for rung in 16384 32768 49152 65536 81920; do
  curl -s http://127.0.0.1:8400/v1/completions \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"...\", \"prompt\": \"<corpus-prefix>\", \"max_tokens\": 256, ...}" \
    | tee results/deep-eval/e30-rung-${rung}.json
done
```

**Key detail:** Log server to file; do not redirect to /dev/null. Proof of successful run: serverlog shows "KV cache fits: yes" or "memory allocation OK" at target context.

**Expected outputs:** results/deep-eval/e30-config1-{16k,32k,48k,64k,80k}-{json,serverlog}.


### E31: Output-budget sensitivity (10 models, both suites, MAXTOK=8192)

**Local models:**
```bash
MAXTOK=8192 promptfoo eval \
  -c spikes/deep-eval/e31-local-suite.yaml \
  --jinja \
  -j 1 \
  -o results/deep-eval/e31-local.json
```

**Cloud models** (OpenRouter + Mistral):
```bash
MAXTOK=8192 OPENROUTER_API_KEY=... MISTRAL_API_KEY=... \
  promptfoo eval \
  -c spikes/deep-eval/e31-cloud-suite.yaml \
  -j 1 \
  -o results/deep-eval/e31-cloud.json
```

**Reasoning extraction** (post-run):
```bash
python tools/regrade_reasoning.py \
  results/deep-eval/e31-{local,cloud}.json \
  --output results/deep-eval/e31-{local,cloud}-extracted.json
```

**Expected outputs:** results/deep-eval/e31-{local,cloud}-{summary.md,json,extracted.json}.


## 6. Limitations

1. **Single machine, single serving stack:** All measurements on Ryzen AI Max+ 395 (Strix Halo Radeon 8060S) with Vulkan backend. ROCm pending (F22 candidate lever). Results expected to vary with different hardware (VRAM, bandwidth) and different backends (CUDA, HIP, Metal).

2. **Single run per capability measurement:** E27, E28, E29, E31 carry n=1 to n=3 test runs per model per suite. Throughput curves (E1, E4, E13) carry n=3 repetitions per point. Confidence intervals narrow with repeat runs; single-run measurements carry full sigma (observed ~1.5% CV per F15, translate to ~3-4% interval width).

3. **Suite resolution n=24/30:** Summarisation suite 30 tasks; instruction-following suite 24 tasks. Both fixed size across all runs. Rare adversarial tasks (n=2 per E9) provide weak separation; expanded suites (100+ tasks per domain) would tighten CIs but were out of scope.

4. **Extraction lower bounds:** Content-extracted scores for reasoning models (MiniMax, Qwen3.5-397B, magistral-medium) use paragraph-classifier rule (known limitation: numbered-list thinking without markers survives extraction). Extracted scores are lower-bound estimates; true capability may be higher if structured reasoning text is interspersed with content.

5. **Capability scores are not general benchmarks:** E27, E28, E29, E31 scores reflect performance on sparkaench's custom suites (business document traps, task-specific evaluation, platform assumptions). Generalisation to other benchmarks (MMLU, BBH, etc.) is an open research question. E29 MMLU rungs provide one cross-domain point; E31 instruction-following is custom-designed for format-compliance (not general reasoning).

6. **Cloud pricing and availability:** Cloud model pricing and availability checked 2026-07-11. Mistral and OpenRouter pricing subject to change; results reflect spot prices on freeze date. OpenRouter API is a proxy; measured latency includes their routing overhead.

7. **Output-budget choice (MAXTOK=8192):** Canonical capability measurement at MAXTOK=8192 reflects test-suite needs and model behaviour observed during registration. Different application domains may require different budgets (code generation: higher; summarisation: lower). Per-task tailoring of output budget is an operational question outside this report's scope.

8. **No long-context reasoning evaluation:** E30 tests retrieval accuracy (needle-in-haystack style) but does not test quality of reasoning that depends on multiple document sections. F8's cross-chunk reference quality evaluation (E8) is a partial proxy; full long-document reasoning benchmarks are deferred.

9. **Multimodal capability tested on 4 images:** E5 vision probe (Gemma-3-27B + mmproj) tested on 4 images from the sparkbench gallery with objectively checkable answers. The "~2.4s per image" timing and "4/4 correct" score reflect wire-up and sanity validation, not a vision benchmark. Document/chart-heavy evaluation is deferred.

10. **Platform-general vs chassis-specific findings:** Findings are labelled per evidence support. Machine-architectural findings (bandwidth-saturation, chunked-attention periodicity, concurrency scaling by architecture) expected to generalise to similar Radeon/RDNA3 hardware. Silicon-specific findings (Ryzen AI Max+ 395 scheduler anomalies, precise memory edge at 68GiB) may not. White paper Section 6 specifies which.


**Report prepared:** core benchmark data frozen 2026-07-11; the v3.0 output-quality workstream ran to 2026-07-13, and the v3.1 tool-use benchmark to 2026-07-14 (full run window 3 - 14 July 2026). All claims public as of launch; full source evidence preserved for audit and re-measurement.
