# File: model-survey.md
# Purpose: Running results log for the capability-assessment model survey (briefing v2, 2026-07-04).
# Project: sparkbench | Date: 2026-07-04
#
# Overview: One entry per model in the briefing's capture format, appended
# as each bench completes. Canonical spec unless noted: llama.cpp 067de937
# Vulkan RADV, Mesa 25.2.8, kernel 6.17.0-35, TTM 105GB, llama-bench
# `-d 0,4096,8192` (split invocations for >~60GiB weights per F6). Corridor
# predictions computed at pin time from artefact bytes (FINDINGS F10).
# Provenance for every artefact: manifests/MANIFEST.md.

## Baseline (Phase A, do not re-run - briefing reference data)

| Model | pp512 | tg128 | tg@8K | Notes |
|---|---|---|---|---|
| gpt-oss-120b MXFP4 | 545.65 | 53.44 | 48.35 | house reference baseline |
| Qwen3-30B-A3B Q4_K_M | 1140.72 | 92.28 | 67.06 | workhorse; concurrency: 193.5 agg @16 slots |
| Qwen3-Coder-30B Q4_K_M | 1108.96 | 93.05 | 67.09 | throughput-identical to workhorse |
| Qwen3.6-35B-A3B UD-Q4_K_XL | 982.86 | 58.71 | 55.14 | hybrid; flattest depth slope |
| GLM-4.5-Air Q4_K_M | 232.38 | 23.90 | 20.74 | memory-edge (F6) |
| GLM-4.7-Flash Q4_K_M | 922.24 | 70.93 | 50.50 | MLA; badge dies ~230 tokens |
| gpt-oss-20b MXFP4 | 1321.83 | 75.22 | 67.51 | concurrency knee ~4 slots (F17) |
| Qwen3-14B Q4_K_M | 621.66 | 24.34 | 21.19 | dense ~100% of naive |
| Qwen3-8B Q4_K_M | 1078.08 | 43.56 | 35.23 | dense at ceiling (Tier 2 #8: already done) |
| Llama-3.1-8B Q4_K_M | 1089.93 | 44.21 | 35.96 | dense constant family-clean |
| Qwen3-4B-2507 Q4_K_M | 2051.57 | 78.38 | 54.12 | fastest pp in matrix |
| DeepSeek-V2-Lite Q4_K_M | 1640.63 | 110.80 | 44.52 | fastest d0 tg; MLA depth cliff |

## Gaps and skips

- ROCm comparison (Part 2): SKIPPED - ROCm not installed (checked
  2026-07-04); entry 1 in DEFERRED-ROOT.md.
- Tier 3 (Qwen3-235B, DeepSeek-V3): not present on disk, not
  downloaded per briefing.
- Tier 2 #8 (Qwen3-8B): already benched in Phase A - reused above,
  not re-run.

## Survey entries (appended per model)

### Phi-4 (dense, 14.7B params, 14.7B active)

- Quant: Q4_K_M
- File: /opt/models/staging/phi-4-Q4_K_M.gguf (unsloth/phi-4-GGUF,
  rev 5110b777, manifest VERIFIED)
- File size: 8.89 GB (8.28 GiB per llama-bench)
- Memory usage: ~8.3 GiB weights, full Vulkan offload
- Flags: none (defaults)
- pp512: 611.88 t/s
- tg128: 24.40 t/s
- tg128 @ 4K context: 22.36 t/s
- tg128 @ 8K context: 20.62 t/s
- Corridor prediction: 220/8.89 x ~1.0 (dense) = 24.7 t/s
- Corridor ratio (actual/predicted): 0.99
- Notes: registered band 23.5-25.5 HIT. Runs on the llama graph
  (llama-bench reports "llama 13B", 14.66B params). Fifth dense
  point at ~99-100% of naive - the dense constant is now
  family-diverse (Qwen x3, Llama, Phi). Consulting answer for
  "modest hardware floor": 24 t/s = comfortable reading speed;
  Phi-4-mini (Tier 2) will probe the true floor. Declared
  condition: Scout + Tier-1 downloads active (3c rule);
  pp@8192 CV 4.4%, within gates.

### Mistral-Small-3.1-24B-Instruct-2503 (dense, 23.6B params, 23.6B active)

- Quant: Q4_K_M
- File: /opt/models/staging/Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf
  (unsloth, rev d63ca941, manifest VERIFIED)
- File size: 14.33 GB (13.34 GiB per llama-bench)
- Memory usage: ~13.4 GiB weights, full Vulkan offload
- Flags: none (defaults)
- pp512: 333.97 t/s
- tg128: 15.07 t/s
- tg128 @ 4K context: 14.42 t/s
- tg128 @ 8K context: 13.81 t/s
- Corridor prediction: 220/14.33 x ~1.0 (dense) = 15.4 t/s
- Corridor ratio (actual/predicted): 0.98
- Notes: registered band 14.5-16 HIT. Dense-at-ceiling n=6, family #4
  (Mistral). THE narrative number for the EU-sovereignty
  conversation: the strong European dense model reads at 15 t/s where
  the same-quant MoE workhorse does 92 - the dense penalty in one
  example. pp 334 is the true compute cost of dense (all 23.6B
  params per token; contrast Phi-4's 612 at 14.7B, workhorse's 1141
  at 3.3B active). Mild depth slopes (-8.4% tg by 8K). Declared
  condition: downloads active; pp CVs 3.5-4.8%, within gates. Quant
  ladder (Part 4) will reuse this artefact as its Q4_K_M rung.

### Gemma-3-27B-it (dense, 27.0B params, 27.0B active)

- Quant: Q4_K_M
- File: /opt/models/staging/gemma-3-27b-it-Q4_K_M.gguf (unsloth,
  rev 7cd0121f, manifest VERIFIED)
- File size: 16.55 GB (15.40 GiB per llama-bench)
- Memory usage: ~15.4 GiB weights, full Vulkan offload
- Flags: none (defaults)
- pp512: 248.43 t/s
- tg128: 12.56 t/s
- tg128 @ 4K context: 11.91 t/s
- tg128 @ 8K context: 11.65 t/s
- Corridor prediction: 220/16.55 x ~1.0 (dense) = 13.3 t/s
- Corridor ratio (actual/predicted): 0.94
- Notes: registered band 12.5-13.8 HIT at the floor edge. Native
  gemma3 graph. Ratio 0.94 is the low edge of the dense cluster
  (others 0.98-1.00) - noted, not attributed. SHALLOWEST dense depth
  slope (-7.2% tg by 8K): the 5:1 local:global SWA keeps KV reads
  light, as predicted at pin time. pp 248 = the true 27B-dense
  compute bill. Consulting answer: Gemma works fine on AMD, but at
  27B dense it is a 12 t/s reader, not a chat engine. Declared
  condition: downloads active; pp d0 CV 5.3%.

### Qwen3-32B (dense, 32.8B params, 32.8B active) - THE dense-vs-MoE comparison

- Quant: Q4_K_M
- File: /opt/models/staging/Qwen3-32B-Q4_K_M.gguf (unsloth,
  rev 931c8406, manifest VERIFIED)
- File size: 19.76 GB (18.40 GiB per llama-bench)
- Memory usage: ~18.4 GiB weights, full Vulkan offload
- Flags: none (defaults)
- pp512: 198.20 t/s
- tg128: 10.89 t/s
- tg128 @ 4K context: 10.30 t/s
- tg128 @ 8K context: 9.76 t/s
- Corridor prediction: 220/19.76 x ~1.0 (dense) = 11.1 t/s
- Corridor ratio (actual/predicted): 0.98
- Notes: registered band 10-12 HIT. **The survey's centrepiece
  result - same family, same generation, same quant, near-same file
  size as the MoE workhorse: Qwen3-30B-A3B does 92.28 tg / 1141 pp;
  Qwen3-32B dense does 10.89 tg / 198 pp. MoE advantage at matched
  scale: 8.5x generation, 5.8x prefill.** Phase A's 3.8x (vs 14B
  dense) understated the matched-size case. Physics: dense reads all
  18.4GB per token, the MoE ~2GB. Consulting answer to "MoE or
  dense?": MoE, by nearly an order of magnitude, and it is not
  close. Also the matrix's slowest prefill: an 8K-context document
  costs ~95s of prefill (86 t/s pp @8K) before the first token -
  dense 32B is a batch tool on this hardware, not interactive.
  Declared condition: R1-Distill download active.

### Llama-4-Scout-17B-16E (MoE, 107.8B params, 17B active)

- Quant: Q4_K_M (2 shards)
- File: /opt/models/staging/Llama-4-Scout-...-0000{1,2}-of-00002.gguf
  (unsloth, rev 72a6853f, manifest VERIFIED; briefing's bartowski URL
  was stale - substitution logged)
- File size: 65.36 GB (60.86 GiB per llama-bench)
- Memory usage: ~61 GiB weights, FULL Vulkan offload - fits with
  ~10 GiB device-local headroom; F6 split invocations used, no
  memory events across three legs
- Flags: none (defaults; split -d invocations per F6)
- pp512: 163.17 t/s
- tg128: 18.54 t/s
- tg128 @ 4K context: 16.64 t/s
- tg128 @ 8K context: 17.89 t/s
- Corridor prediction: 220/(0.604 B/param x 17B active) x 0.84
  (pure MoE) = ~18 t/s
- Corridor ratio (actual/predicted vs naive 21.4): 0.87 - pure-MoE
  class, llama4's chunked attention carries no extra arch tax at d0
- Notes: registered band 15-20 HIT. **Consulting answer to "Can I
  run Llama locally?": YES on a 128GB Strix Halo box - Meta's 109B
  Scout runs wholly on-GPU at 18.5 t/s reading speed** (and NO on
  32/64GB machines - it needs ~61GiB for weights alone).
  FINDING-shaped wrinkle: depth behaviour is NON-MONOTONIC - d8192
  (17.89 tg / 165 pp) beats d4096 (16.64 / 146), with 8K pp matching
  d0. Consistent with llama4 chunked attention (8192-token chunks):
  d8192 sits at a chunk boundary where the local window resets.
  Candidate mechanism, not attributed - a finer depth sweep would
  map the sawtooth. Quality caveat for client conversations: Scout's
  mixed reception vs Qwen is a quality question; this row only
  settles that it RUNS, comfortably.

### DeepSeek-R1-Distill-Qwen-32B (dense, 32.8B params, 32.8B active)

- Quant: Q4_K_M
- File: /opt/models/staging/DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf
  (unsloth, rev 1938d05c, manifest VERIFIED)
- File size: 19.85 GB (18.48 GiB per llama-bench)
- Memory usage: ~18.5 GiB weights, full Vulkan offload
- Flags: none (defaults)
- pp512: 223.96 t/s
- tg128: 11.05 t/s
- tg128 @ 4K context: 10.50 t/s
- tg128 @ 8K context: 10.00 t/s
- Corridor prediction: 220/19.85 x ~1.0 (dense) = 11.1 t/s
- Corridor ratio (actual/predicted): 1.00
- Notes: registered band 10-12 HIT, at ceiling. Confirms Qwen3-32B
  within 1.5% (qwen2 vs qwen3 graph - generation-independent).
  Reasoning-model reality check: 11 t/s x 1000+-token thinking
  traces = MINUTES per answer on this box. "Thinking" models at
  dense-32B scale are batch analysts here, not chat partners - the
  accessible reasoning option is a fast MoE with thinking mode
  (Qwen3-30B-A3B at 92 t/s), not the distill. Declared condition:
  no downloads active (last bench of the chain).

### Phi-4-mini (dense, 3.8B params, 3.8B active) - Tier 2, the floor

- Quant: Q4_K_M
- File: /opt/models/staging/Phi-4-mini-instruct-Q4_K_M.gguf (unsloth,
  rev 78eb92a4, manifest VERIFIED)
- File size: 2.49 GB (2.31 GiB per llama-bench)
- Memory usage: ~2.3 GiB weights, full Vulkan offload
- Flags: none (defaults)
- pp512: 2149.96 t/s (highest prefill in the matrix)
- tg128: 77.44 t/s
- tg128 @ 4K context: 63.13 t/s
- tg128 @ 8K context: 54.87 t/s
- Corridor prediction: 220/2.49 x ~0.9-1.0 = band 79-90
- Corridor ratio (actual/naive): 0.88
- Notes: registered band MISSED low by 2% (77.44 vs 79 floor) - and
  the miss refines a constant: 0.877 of naive matches Qwen3-4B's
  0.887, so SMALL-DENSE OVERHEAD ~0.88 is now n=2 and looks
  systematic below ~5GB artefacts (vs ~0.99 for 9-20GB dense).
  Floor answer: the smallest useful model clears the ~70 instant
  line fresh (badge dies ~2K depth, same pattern as the 4B), reads
  8K prompts at 917 t/s pp. Declared condition: Coder-32B download
  active.

### Qwen2.5-Coder-32B-Instruct (dense, 32.8B params, 32.8B active) - Tier 2

- Quant: Q4_K_M
- File: /opt/models/staging/Qwen2.5-Coder-32B-Instruct-Q4_K_M.gguf
  (unsloth, rev 638ed913, manifest VERIFIED)
- File size: 19.85 GB (18.48 GiB per llama-bench)
- Memory usage: ~18.5 GiB weights, full Vulkan offload
- Flags: none (defaults)
- pp512: 223.16 t/s
- tg128: 11.09 t/s
- tg128 @ 4K context: 10.53 t/s
- tg128 @ 8K context: 10.03 t/s
- Corridor prediction: 220/19.85 x ~1.0 (dense) = 11.1 t/s
- Corridor ratio (actual/predicted): 1.00
- Notes: registered band 10-12 HIT at ceiling. Statistically
  IDENTICAL to R1-Distill (11.05/10.50/10.00) - same Qwen2.5-32B
  body, third confirmation that fine-tune content never moves
  throughput. Coding story on this box: dense-32B coder = 11 t/s
  batch code reviewer; the interactive coding seat belongs to
  Qwen3-Coder-30B MoE at 93 t/s. Declared condition: Mixtral
  download active.

### Mixtral-8x7B-Instruct-v0.1 (MoE, 46.7B params, ~12.9B active) - Tier 2

- Quant: Q4_K_M (mradermacher re-conversion)
- File: /opt/models/staging/Mixtral-8x7B-Instruct-v0.1.Q4_K_M.gguf
  (rev 92bb790b, manifest VERIFIED)
- File size: 28.45 GB (26.49 GiB per llama-bench)
- Memory usage: ~26.5 GiB weights, full Vulkan offload
- Flags: none (defaults)
- pp512: 216.13 t/s
- tg128: 26.45 t/s
- tg128 @ 4K context: 24.60 t/s
- tg128 @ 8K context: 23.46 t/s
- Corridor prediction: 220/(0.609 x 12.9B) x 0.84 = ~23.5; band 21-27
- Corridor ratio (actual/naive ~28): 0.94
- Notes: registered band HIT near ceiling. TWO findings: (1) the
  original TheBloke Dec-2023 GGUF DOES NOT LOAD at 067de937 (MoE
  tensor layout changed) - "GGUF archives age, re-conversion
  required" is a real operational fact for anyone keeping model
  archives; artefact kept as evidence. (2) The classic big-expert
  top-2-of-8 MoE runs at ~0.94 of naive - ABOVE the modern
  fine-grained MoE cluster (0.84-0.86); simpler routing appears
  cheaper per byte on this stack. Still obsolete on merit: the
  workhorse is 3.5x faster on 40% less memory. Declared condition:
  ladder downloads active.

## PART 4 COMPLETE - Mistral-Small-24B quantization ladder (2026-07-04)

| Quant | File GB | tg128 | pp512 | Predicted tg | Speed vs Q4 | Size vs Q4 |
|---|---|---|---|---|---|---|
| Q4_K_M | 14.33 | 15.07 | 334 | 15.4 | 1.00x | 1.00x |
| Q5_K_M | 16.76 | 12.97 | 236 | 12.9 | 0.86x | 1.17x |
| Q6_K | 19.35 | 11.59 | 249 | 11.1 | 0.77x | 1.35x |
| Q8_0 | 25.05 | 8.83 | 283 | 8.6 | 0.59x | 1.75x |

- **Generation speed is EXACTLY inverse to file size** - every rung
  lands at 0.98-1.03 of its corridor prediction. The consulting
  soundbite: "quantization's speed cost IS the size ratio; the only
  open question is quality, and that is what evals are for."
  Near-lossless Q8 costs 41% of Q4's speed on the same model.
- pp wrinkle (recorded, not attributed): prefill does NOT follow the
  same line (Q4 334 > Q8 283 > Q6 249 > Q5 236) - dequant kernel
  paths differ per quant in compute-bound prefill.
- All three new rungs verified against upstream oids before use
  (hashed directly; the chain-level hash prints only at invocation
  end).

## TIER 2 COMPLETE (Qwen3-8B reused from Phase A) - summary above plus:
Phi-4-mini 77.44 (floor, small-dense 0.88), Coder-32B 11.09 (= R1
body), Mixtral 26.45 (vintage-GGUF finding + classic-MoE efficiency).

## TIER 1 COMPLETE - summary (2026-07-04)

| Model | Arch | tg128 d0 | tg @8K | pp512 | Band | Ratio |
|---|---|---|---|---|---|---|
| Llama-4-Scout 109B/A17B | MoE | 18.54 | 17.89 | 163 | HIT | 0.87 |
| Mistral-Small-24B | dense | 15.07 | 13.81 | 334 | HIT | 0.98 |
| Gemma-3-27B | dense | 12.56 | 11.65 | 248 | HIT | 0.94 |
| Phi-4 14.7B | dense | 24.40 | 20.62 | 612 | HIT | 0.99 |
| Qwen3-32B | dense | 10.89 | 9.76 | 198 | HIT | 0.98 |
| R1-Distill-32B | dense | 11.05 | 10.00 | 224 | HIT | 1.00 |

**Six unseen models, six registered-band hits, corridor ratios
0.87-1.00.** The pricing model (F10) predicts throughput of models it
has never seen from file size + architecture class alone. Headline:
Qwen3-32B dense vs Qwen3-30B-A3B MoE = 8.5x generation gap at matched
family/scale/quant. Meta's 109B Scout runs wholly on-box at reading
speed. Every dense model 24B+ is a batch tool, not a chat engine, on
this hardware.

## PRE-REGISTRATION - Qwen3.8-27B (2026-08-15, BEFORE any run)

Written before the bench executes, per the pre-registration rule. Two legs,
because the Qwen3.8 number is not corridor-comparable on its own: the stack
moved twice since the corridor constants were measured.

**Declared stack deviation (F57):** corridor constants were measured on
llama.cpp b9864 + kernel 6.17.0-35. This run is **b10435** (built 2026-08-15
in `llama.cpp/wt/b10435`, `-DGGML_VULKAN=ON -DLLAMA_CURL=OFF`) on kernel
7.0.0-28. The old b9864 `build/` was deliberately NOT overwritten, so both
binaries exist and the delta is measurable rather than absorbed. Mesa 25.2.8.

### Leg A (CONTROL, run first) - Qwen3-30B-A3B-Instruct-2507-Q4_K_M

Re-bench of an already-measured model, solely to price the build+kernel
delta. Phase A baseline (b9864 / kernel 6.17.0-35): **pp512 1140.72,
tg128 92.28, tg@8K 67.06**.

- **Prediction:** all three figures within **+/-5%** of baseline
  (tg128 87.7-96.9, pp512 1083.7-1197.8, tg@8K 63.7-70.4).
- **Disposition:** if Leg A lands in band, the stack delta is inside noise
  (F15 is +/-1.5% single-run) and Leg B may be compared to the corridor
  directly. If Leg A is OUT of band, the measured ratio becomes a stated
  correction applied to Leg B before any corridor claim - and that is a
  finding in its own right.

### Leg B - Qwen3.8-27B-Q4_K_M (dense 27.32B, DeltaNet hybrid)

Measured facts already read from the artefact: `general.architecture =
qwen35`, `n_layer = 64` (+1 MTP head, loaded as UNUSED and ignored),
`full_attention_interval = 4` so 3 of every 4 layers are linear attention,
GPU-resident weight buffer **15088.31 MiB** = 15.82 GB active bytes/token
(dense: every weight is active, no MoE estimate involved).

Naive ceiling: 220 GB/s / 15.82 GB = **13.91 t/s** before arch factor.

F10 offers two mutually exclusive arch factors, and this model discriminates
between them - which is the reason to run it:

- **Primary prediction (registered): tg128 d0 = 12.5-15.0** (arch factor
  0.90-1.08, i.e. the DeltaNet tax does NOT transfer). Reasoning: F10's
  DeltaNet-hybrid ~0.55 rests on n=1, and that one point was Qwen3.6-35B-A3B
  - a **MoE**, where "active bytes per token" is itself an estimate (~3B of
  35B). If that estimate was wrong, the 0.55 constant absorbed the error and
  mislabelled it as a DeltaNet penalty. A DENSE DeltaNet model has
  unambiguous active bytes, so it isolates the two.
- **Discriminating alternative: tg128 d0 = 6.9-8.4** (0.55 applies). If it
  lands here, the DeltaNet tax is real, transfers across dense/MoE, and F10's
  constant is confirmed rather than confounded.
- **Neither band (8.5-12.4)** = partial effect; needs a third explanation and
  must NOT be rounded into whichever band is closer.

- **pp512: deliberately NOT predicted**, same stance taken for Qwen3.6-35B-A3B
  - Vulkan DeltaNet prefill kernel maturity is the thing being measured, and a
  prediction would be theatre.
- **tg@8K: predict 0.88-0.95 of measured d0.** Dense comparators decayed to
  0.93 (Gemma-3-27B) and 0.90 (Qwen3-32B); the one hybrid was flattest at 0.94.

### Amendments

None. Any amendment must be recorded here BEFORE the affected run.

## RESULTS - Qwen3.8-27B (2026-08-15, run 01:44-01:49)

Stack: llama.cpp **b10435** (`9e40df63b`, build 770, `-DGGML_VULKAN=ON
-DLLAMA_CURL=OFF`), kernel **7.0.0-28**, Mesa 25.2.8, relay down under the
sparkrouter maintenance flag for the whole window. Raw:
`results/raw/bench-20260815-014413-qwen38-leg{A,B}-*.md`.

### Leg A (control) - Qwen3-30B-A3B-Instruct-2507-Q4_K_M

| Metric | Phase A baseline (b9864 / 6.17.0-35) | This run (b10435 / 7.0.0-28) | Delta | Registered +/-5% |
|---|---|---|---|---|
| pp512 | 1140.72 | 1132.55 +/- 9.93 | -0.72% | IN BAND |
| tg128 | 92.28 | 95.37 +/- 0.18 | **+3.35%** | IN BAND |
| tg@8K | 67.06 | 68.15 +/- 0.07 | +1.63% | IN BAND |

**Verdict: IN BAND on all three**, so Leg B is compared to the corridor as
registered.

**Flaw in my own pre-registration, recorded rather than quietly dropped:**
the disposition said an in-band Leg A meant the delta was "inside noise
(F15 is +/-1.5%)". Those are two different thresholds and I conflated them.
tg128's **+3.35% is in the registered +/-5% band but well outside F15's
+/-1.5% single-run noise**, and llama-bench's own error bar here is +/-0.19%.
So a small but REAL stack tailwind exists on generation - it is not noise.
Consequence for Leg B is stated in its section; the band verdict stands as
registered, because rewriting the disposition after seeing the number is
exactly the move the pre-registration rule exists to prevent.

### Leg B (subject) - Qwen3.8-27B-Q4_K_M (dense 27.32B, DeltaNet hybrid)

| Test | d0 | d4096 | d8192 |
|---|---|---|---|
| pp512 | 283.00 +/- 4.80 | 235.96 +/- 10.95 | 222.49 +/- 9.95 |
| tg128 | 12.64 +/- 0.00 | 12.38 +/- 0.00 | 12.19 +/- 0.00 |

**tg128 d0 = 12.64 -> registered primary band 12.5-15.0 HIT** (low edge).
Discriminating alternative 6.9-8.4 **REJECTED** by a factor of ~1.6.

Arch factor depends on which "active bytes" convention is used, so both are
stated rather than the flattering one being picked:

| Active-bytes basis | Bytes | Ceiling | Arch factor |
|---|---|---|---|
| GPU-resident weight buffer (as pre-registered) | 15.82 GB | 13.91 t/s | **0.909** |
| Whole file | 16.81 GB | 13.09 t/s | 0.966 |

Applying Leg A's measured +3.35% tg tailwind to put this on the old stack
gives ~12.23 t/s (factor 0.879), which would sit just BELOW the registered
band. Stated because it is the honest reading of the control; it does not
change the discrimination, which is decided by a gap of ~1.6x, not by a
band edge.

**F10's DeltaNet-hybrid 0.55 arch factor does NOT transfer to a dense
DeltaNet model.** The registered reasoning is supported: that constant came
from n=1 on Qwen3.6-35B-A3B, a **MoE** whose active-bytes-per-token is an
estimate, and it evidently absorbed that estimation error rather than
measuring a DeltaNet penalty. Qwen3.8-27B is dense, so its active bytes are
unambiguous, and it prices at 0.91-0.97 - i.e. **ordinary dense**.

**DEVIATION (a finding, per the rule): the depth slope was flatter than
predicted.** Registered 0.88-0.95 of d0 at 8K; measured **0.9644** (12.19 /
12.64), a decay of only -3.6%. Comparators from the same run and the
baseline table:

| Model | tg d8192/d0 | pp512 d8192/d0 |
|---|---|---|
| **Qwen3.8-27B (dense DeltaNet hybrid)** | **0.964** | **0.786** |
| Qwen3-30B-A3B (MoE, this run) | 0.715 | 0.491 |
| Qwen3.6-35B-A3B (MoE DeltaNet hybrid) | 0.939 | - |
| Gemma-3-27B (dense) | 0.928 | - |
| Qwen3-32B (dense) | 0.896 | - |

Consistent with the architecture: `full_attention_interval = 4` means only 1
layer in 4 grows a KV cache with depth, so depth cost is roughly quartered.
Prefill shows the same shape even more strongly (0.786 vs the control's
0.491). The hybrid's advantage is **depth-robustness, not peak speed**.

**pp512 = 283.00 was deliberately not predicted** (Vulkan DeltaNet prefill
kernel maturity was the open question). It lands ABOVE the dense
comparators of similar size - Gemma-3-27B 248, Qwen3-32B 198 - so there is
no DeltaNet prefill penalty on this stack. That closes the question the
Qwen3.6 entry left open.

### Practical read

At 12.64 t/s this is a batch/drafting tool, not a chat engine - the same
verdict every dense 24B+ model on this box gets. It is ~7.5x slower to
generate than the MoE workhorse (95.37). What it buys is a nearly flat
depth curve: by 8K the gap has narrowed from 7.5x to 5.6x, and its prefill
holds 79% of d0 where the workhorse holds 49%.

### Qwen3.8-27B tg128 repeatability triplet (2026-08-15 02:05, quiet box)

Run because the Leg B result hit its registered band on the LOW edge, and
F15 puts the true error bar between invocations at ~+/-1.5%.

| Invocation | tg128 | within-run sd |
|---|---|---|
| 1 | 12.62 | 0.04 |
| 2 | 12.60 | 0.02 |
| 3 | 12.60 | 0.02 |

Mean **12.607**, spread **0.16%** - an order of magnitude tighter than F15's
+/-1.5%, which was measured on the MoE workhorse. Worth noting as an
observation, not a claim: this dense hybrid appears markedly more repeatable
than the MoE, and expert-routing variance is the obvious candidate mechanism,
untested here.

**Leg B's 12.64 is CONFIRMED** (0.26% from the triplet mean, inside noise).
The registered band 12.5-15.0 stands as a HIT. The stack-corrected figure
(~12.20 after removing F63's +3.35% tailwind) still sits just below the band,
exactly as recorded when Leg B was written up - the triplet sharpens that
caveat rather than removing it.

**A void triplet preceded this one.** The 02:00:38 operator run collided with
a session-launched run; all three of its invocations were contended (30% /
100% / 17% of reps) and none are usable. Kept in results/raw as
`bench-20260815-020038-*` BECAUSE they are the evidence for F64, not because
they measure Qwen3.8.
