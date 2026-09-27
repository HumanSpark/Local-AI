# File: FINDINGS.md
# Purpose: Numbered findings register for sparkbench - one durable, evidence-backed finding per item.
# Project: sparkbench | Date: 2026-07-03
#
# Overview: Created at Step 8 pre-registration. The Step 8 brief referenced
# F-numbers (F3, F11, F12) before any register existed - declared correction
# in PHASE-A-LOG.md. Numbering is chronological by the PHASE-A-LOG entry that
# established each finding; content-mapping puts the brief's references where
# it assumed them. Register is append-and-annotate: superseded findings stay
# listed with a supersession note, never deleted. Evidence pointers are
# PHASE-A-LOG.md entries (all 2026-07-03 unless dated otherwise). All
# throughput constants: llama.cpp 067de937 Vulkan, Mesa 25.2.8, kernel
# 6.17.0-35, TTM 105GB, Strix Halo Radeon 8060S - single machine, single
# stack; see F10 status note. WARNING: "kernel 6.17.0-35" is the kernel those
# constants were MEASURED on, not the kernel running now - the box has been on
# 7.0.0-28 since 2026-07-19, moved there by unattended-upgrades. Anything
# measured after that date is a different amdgpu driver. See F57.


## How to read this register: the `Kind:` line

Every finding carries `**Kind:**`, added 2026-09-01 on the owner's two-findings
convention: an experiment may produce a **model** finding and a **method**
finding independently, and the method one often outlives the model.

**A third kind was needed.** The convention names two, but roughly 40% of this
register is neither - it is about the BOX: the memory edge, the amdgpu
suballocator, kernel drift, the ROCm apt pin, Vulkan against ROCm, the tool-schema
byte limit in llama.cpp. Filing those as `MODEL` would be wrong and would dilute
the thing the split exists to make findable.

| Kind | what it teaches | count at 2026-09-01 |
|---|---|---|
| **MODEL** | what a model or workload can and cannot do | 36 |
| **METHOD** | how to measure models and workloads without fooling ourselves | 48 |
| **PLATFORM** | what this hardware, kernel and runtime stack do | 55 |

**`PLATFORM` is provisional.** If the owner prefers the strict two-way split it
collapses into `MODEL`; nothing else changes. It is separated because a platform
finding expires when the stack moves (F57's kernel drift, F109 retracting F24's
boundary) while a method finding usually does not.

**Mixed findings are SPLIT, not filed by headline.** A finding that teaches two
things gets two numbers, so neither half is lost behind the other's label. All
nine identified mixed findings were split on 2026-09-01:

| original keeps | split out |
|---|---|
| F110 KV precision (PLATFORM) | **F126** METHOD - a saturated instrument cannot compare anything |
| F119 Kwaipilot non-termination (MODEL) | **F127** METHOD - public ranking vs local usability; UNSCORABLE vs failed |
| F21 spec-decode range (PLATFORM) | **F128** METHOD - a speedup without its workload; a flag that loads without acting |
| F26 the GRUB confound (METHOD) | **F129** PLATFORM - Vulkan never failed under control; F6 unreproduced |
| F34 two axes for drafting (METHOD) | **F130** MODEL - which models actually draft well |
| F39 one writer for serving flags (METHOD) | **F131** PLATFORM - omitting `-c` allocates the full trained context |
| F45 whisper accuracy (MODEL, was METHOD) | **F132** METHOD - an external known value caught an inverted answer |
| F56 the narrator decision (MODEL) | **F133** METHOD - three measurement lessons from settling it |
| F102 what the coder did (MODEL) | **F134** METHOD - a gate is green when missing work has no tests to fail |

**F45's own Kind changed**, from METHOD to MODEL, because once the harness
lesson moved to F132 what remained was the accuracy result.

Each original carries a pointer to its other half, so neither can be read as
the whole finding.


## F1 - llama-cli is chat-first; harness runs need llama-server

**Kind: METHOD**

At commit 067de937, `--no-conversation` is unsupported and an EOF'd stdin
loops forever on the chat prompt. Scripted/harness runs use llama-server
(or llama-completion) + HTTP, always timeout-wrapped.
Evidence: step 4a entry. Status: ACTIVE (bound as HARNESS-RULES 1-3).

## F2 - download completion = byte/hash match vs origin authority, never exit 0

**Kind: METHOD**

Wi-Fi drops and wrapper-shell bashisms both produced clean-looking partial
or never-ran fetches. Pin sizes/oids from the origin API first; verify on
arrival. Evidence: step 4c entries. Status: ACTIVE (HARNESS-RULES Rule 4;
promoted fleet-wide as download-integrity.md).

## F3 - effective-bandwidth quant clusters (single-cluster reading)

**Kind: PLATFORM**

Q4_K artefacts land 84-100% of the naive bandwidth ceiling; MXFP4 lands
~64-69%. Declared confound: both MXFP4 points were gpt-oss family.
Evidence: step 5 gate (53.44 = 64%), step 7 Row A (77.76 = 68.8%).
Status: SUPERSEDED by F11 (2026-07-03) - the clusters are real but the
mechanism is a tg-only dequant tax; prefill pays no MXFP4 penalty.

## F4 - MoE-first on this silicon is empirical; dense Q4_K runs at ~naive ceiling

**Kind: PLATFORM**

Qwen3-30B-A3B generates 3.8x faster than dense Qwen3-14B (92.83 vs 24.39
tg) while being the stronger model; the dense 14B sits at ~100% of its
220/9.0GB naive ceiling. Dense-at-interactive-speed is physics-limited.
Evidence: step 6 workhorse + 14B entries. Status: ACTIVE.

## F5 - depth slopes follow active-set/KV fraction; smooth, no cliffs

**Kind: PLATFORM**

tg at d8192 vs d0: gpt-oss -9.1/-9.5%, GLM-4.5-Air -13.2%, Qwen3-30B-A3B
-28%, Qwen3.6-35B hybrid -6.8% (shallowest - linear attention). The
smaller the active set, the larger the KV-read fraction per token.
Evidence: step 5/6/7 entries. Status: ACTIVE (Step 8 Block 1 extends
every model from 2 depth points to 5-6).

## F6 - memory-edge behaviour at ~68GiB weights

**Kind: PLATFORM**

Weights within ~4GiB of the 71.65GiB device-local heap: combined `-d`
invocations DeviceLost-abort, and pp-at-depth CV blows out (21% vs the
matrix-typical 1-2%). Operational rule: models >~60GiB use split
invocations; treat memory-pressured pp as low-confidence.
Evidence: step 6 GLM-4.5-Air entry. Status: ACTIVE.

## F7 - DeltaNet hybrids carry a per-token cost the weight-bytes model misses

**Kind: PLATFORM**

Qwen3.6-35B-A3B on Q4_K: tg ~54-57% of naive (below even the MXFP4
cluster) beside HEALTHY pp (996 t/s) and the flattest depth slope in the
matrix. Recurrent-state read/write traffic and/or immature Vulkan
recurrent kernels are the candidate drags (not separable via llama-bench).
Evidence: step 7 Row B entry. Status: ACTIVE.

## F8 - GLM-4.7-Flash runs the deepseek2 (MLA) graph; MLA-MoE lands ~66% of naive

**Kind: PLATFORM**

llama-bench identifies the artefact as deepseek2 30B.A3B; on Q4_K it
achieves ~66% of naive - a distinct band below pure-MoE's ~84%.
Evidence: step 7 Row C entry. Status: ACTIVE (generality test = F12).

## F9 - "A3B" is a label, not a price

**Kind: PLATFORM**

Three A3B-class MoEs, same quant family, same hardware, span 1.57x on tg:
92.8 (pure MoE) / 71.9 (MLA) / 59.3 (DeltaNet hybrid). Active-parameter
count alone cannot price a model; architecture dominates.
Evidence: step 7 Row C entry. Status: ACTIVE.

## F10 - corridor rule form (pre-screen pricing model)

**Kind: PLATFORM**

t/s ~= (220 GB/s / active bytes per token) x arch factor x quant
factor. Ladder as re-priced at Step 8 end-state (n per constant):
dense ~1.00 (n=3, family-clean; small-dense onset 0.89 at 4B, n=1);
pure MoE ~0.84-0.86 (n=2); MLA-MoE per-model 0.66-0.80, NOT a single
class (n=2, see F12); DeltaNet hybrid ~0.55 (n=1); quant factor Q4_K
baseline 1.0, post-hoc MXFP4 ~0.81 tg-only (n=1 isolated).
Evidence: step 7 addendum + step 8 end-state entry. Status: ACTIVE,
with the standing caveat
(Alastair, Step 8 approval): constants rest on n=1-3 points on one
machine/stack and are expected to move with kernel releases - the
METHOD (pre-registration, quant-isolation pairs, repeatability triplets,
stack-fingerprinted tables, re-run triggers) is the durable asset, not
the numbers.

## F11 - MXFP4 is a tg-only dequant tax, ~0.81 multiplier (same-model isolation)

**Kind: PLATFORM**

GLM-4.7-Flash Q4_K_M vs MXFP4_MOE pair: the MXFP4 artefact is 7.3%
smaller yet generates 12.5% slower (81% of Q4_K's per-byte efficiency);
pp512 is +4.5% ABOVE the Q4_K leg. Depth slopes are quant-invariant, so
MLA-at-depth is an arch property. Supersedes F3's single-cluster reading.
Native-MXFP4 (gpt-oss) evidence is consistent but family-confounded per
the pre-declared caveat.
Evidence: step 7 quant-isolation pre-registration + addendum entries.
Status: ACTIVE.

## F12 - MLA-MoE ~0.66 is NOT a constant class; it was Flash-specific

**Kind: PLATFORM**

RESOLVED 2026-07-04 (Step 8 Block 2d, amended fork): DeepSeek-V2-Lite -
the archetype of the same deepseek2 graph GLM-4.7-Flash runs - lands
tg128 110.80 = ~80% of its ~139 t/s naive ceiling: the >=99 arm,
decisive, in pure-MoE territory (0.84), nowhere near 0.66. MLA alone
does not price a model; the corridor rule's MLA-MoE factor is
downgraded to a per-model range (0.66-0.80, n=2) pending a mechanism
split. Method note: under the brief's original mis-derived thresholds
this measurement would have been INCONCLUSIVE - the pin-time
re-derivation (declared amendment) made it decisive. Secondary
replication: the MLA steep-depth signature holds and amplifies
(tg -59.8% at 8K, steepest in the matrix; per-token depth cost 2-3x
the pure-MoE rows).
Evidence: step 8 Block 2d entry. Status: RESOLVED.

## F13 - every instant badge dies with depth; the death depth is a measured number

**Kind: PLATFORM**

Six-point depth curves (0-32K): every model that clears ~70 t/s fresh
loses it under context. Interpolated crossings: GLM-4.7-Flash Q4
~230 TOKENS (a hairline badge is a fragile badge), Qwen3-4B ~2.2K,
DeepSeek-V2-Lite ~3.2K, gpt-oss-20b ~5.5-9K (measurement-sensitive:
its curve is nearly flat at the line, so +/-2% run noise moves the
crossing a whole bracket), Qwen3-30B ~6.9K. Consulting form: never
quote an instant claim without its expiry depth.
Evidence: step 8 Block 1 entries + end-state badge table.
Status: ACTIVE.

## F14 - architecture rank is depth-dependent: the workhorse crossover at ~16K

**Kind: PLATFORM**

Qwen3-30B (pure MoE) vs Qwen3.6-35B (DeltaNet hybrid): 92 vs 59 at
d0, tie at ~16K (53.2 vs 52.5), hybrid ahead 25% at 32K (47.9 vs
38.3) - and the hybrid keeps 60% of its prefill at 32K where the pure
MoE keeps 16%. "Which model is faster" has no answer without a working
depth; model selection needs the workload's context profile.
Evidence: step 8 Block 1 (Qwen3-30B + Qwen3.6-35B curves).
Status: ACTIVE.

## F15 - single-run noise is ~±1.5%; UMA bus contention arrives as jitter, not slowdown

**Kind: METHOD**

Repeatability triplet (identical invocations, window start/middle/
end): 90.63/93.41/92.30, CV 1.52% - the true error bar on any
single-run number, ~3x within-run CV, non-monotonic (not thermal:
every leg starts 46-47degC). Contamination experiment (3c): a ~17MB/s
download shifts tg by -0.6% (null); a sustained ~GB/s disk-read+hash
leaves the mean intact (+1.4%) but inflates within-run sigma ~4x.
Client form: on unified memory you can ingest while serving -
throughput holds, latency jitter rises. Unresolved tail: one
cross-evening pair (gpt-oss-20b, -3.3%/-4.4%) exceeds the triplet
band - model-specific drift, watch.
Evidence: step 8 3b/3c entries. Status: ACTIVE.

## F16 - q8_0 KV cache is a working depth lever; flash attention is free

**Kind: PLATFORM**

Same-model isolation (Qwen3-30B, six depths): -fa on alone = baseline
within noise at every depth (auto already optimal). Adding q8_0 K+V:
-3.8% at d0, break-even ~4-6K, +8.5% at 16K, +14.7% at 32K, KV
footprint halved. It does NOT rescue instant badges (the 70-line
crossing moves ~6.9K -> ~7.1K) - it buys deep-context throughput and
capacity. Deployment rule of thumb: fresh-chat workloads skip it,
long-context workloads want it.
Evidence: step 8 Block 3d entry. Status: ACTIVE.

## F17 - concurrency scaling is architecture-dependent; the single-user ranking widens under fleet load

**Kind: PLATFORM**

llama-server, 4K ctx/slot, 128-token requests: Qwen3-30B (pure MoE
Q4_K) scales 72.9 -> 193.5 t/s aggregate from 1 to 16 slots (2.66x, no
sharp knee, still rising); gpt-oss-20b (native MXFP4, SWA) plateaus
after ~4 slots (59.9 -> 109.0, 1.82x). Their 1.2x single-user gap
becomes 1.8x aggregate at 16 slots. Instant-tier frontier (per-stream
>= 70) is 1 slot on this hardware; TTFT p50 grows ~6x from 1 to 16
slots. q8 KV is effectively free under concurrency (-0.6 to -2.3%
multi-slot) while halving the KV budget that caps slots. Candidate
mechanism for the plateau (MXFP4 batched dequant vs attention path)
untested - a GLM-4.7-Flash quant-pair concurrency run would isolate
it. Client form: "what the fleet gets at burst" depends on
architecture as much as the single-user number - measure both.
Evidence: step 9 results entry; raw JSON bench-step9-*.
Status: ACTIVE, WITH A MATERIAL CAVEAT ADDED 2026-07-17 (F43). Mechanism
refined by F18: the gpt-oss plateau is architecture, not quant (E2
quant-pair, 2026-07-04).

**CAVEAT (F43, 2026-07-17): the 193.5 t/s figure is a SAME-QUESTION best
case, not a fleet number.** All 16 streams in this benchmark ran the same
repetitive prompt, which lets a MoE batch share expert loads. Sixteen
streams asking sixteen DIFFERENT questions measure 108.86 t/s on the same
box, build and slot count - the headline overstates real fleet throughput
by 1.78x. The number reproduces exactly under its own stated conditions
(E36: 192.19), so nothing here is wrong; but this finding's own
client-facing framing - "what the fleet gets at burst" - should cite
108.86, not 193.5. The 1-slot number (72.9) is unaffected: the penalty is
batch-level and does not touch a single user. Dense models show no such
penalty (-0.1%), so this caveat is MoE-specific. See F43 and
results/moe-diversity.md.

## F18 - MLA anti-scales under concurrency; concurrency behaviour now spans 3.8x by architecture

**Kind: PLATFORM**

Same-model GLM-4.7-Flash pair (Q4_K_M vs MXFP4_MOE), slots 1/4/16:
both quants LOSE aggregate throughput as slots rise (16-slot/1-slot
ratios 0.70 and 0.76 - parallel, so quant is exonerated and the
gpt-oss F17 plateau is attributed to architecture). The
architecture-concurrency ladder on this stack: pure MoE 2.66x,
gpt-oss/SWA 1.82x, MLA-MoE ~0.7x (ANTI-scaling, ~20s TTFT at 16
slots). Candidate mechanism: MLA latent decompression is per-token
compute that batching multiplies rather than amortizes (consistent
with F8's prefill collapse). Deployment rule: MLA models are
single-user machines here - never behind a multi-slot server. The
single-user throughput ranking and the fleet ranking are DIFFERENT
orderings; size neither from the other.
Evidence: results/experiments.md E2; raw bench-e2-*.json.
Status: ACTIVE. Attribution strengthened by E4 (Scout/chunked
attention scales 2.72x@8 - best measured - so anti-scaling is not a
general MoE trait).

## F19 - the fleet's 12K-context capability floor is high; small-model tax is judgment, not context

**Kind: MODEL**

Two independently designed eval suites (needle retrieval + summariz-
ation, then multi-hop arithmetic/cross-reference over real technical
logs) both FAILED to separate the resident instruct models at 12K
context - every model from 2.3GB Qwen3-4B up scored >=83%, most 100%.
The only real failures across both suites: Qwen3-4B misclassifying
spam as urgent (judgment), and Qwen3-Coder-30B making the sole
arithmetic slip (ironic; every base model computed correctly).
Deployment guidance: choose models on speed, concurrency behaviour
(F17/F18), and judgment-critical tasks - not on long-context anxiety
below 12K. Separation likely requires >32K, adversarial documents,
or long structured generation (suite v3 candidates).
Evidence: results/eval-pilot.md + results/experiments.md E7.
Status: ACTIVE. Extended by E10: under enumeration pressure the 4B
MISATTRIBUTES real values to wrong models (worse than omission) -
small models need source-checking on any generated table.

## F20 - eval verdicts depend on serving config: the reasoning-channel budget tax

**Kind: METHOD**

gpt-oss-20b failed E9/E10 tasks it can plainly do (6/6 on the harder
E8) because its harmony "Thinking" channel leaks into content under
llama-server --jinja and consumes max_tokens before the answer -
1333 chars of correct systematic scanning, then truncation. Verdicts
flip on max_tokens, not capability. Deployment rules: (1) reasoning
models need 2-4x the token budget of instruct models for equivalent
tasks, or template-level channel separation; (2) any eval report
must state max_tokens and template handling or its scores are not
comparable - the WER-normalization lesson (E11), applied to LLM
grading. Related: F8/F13's context caveats - eval design keeps
rediscovering that the RULER is half the measurement.
Evidence: results/experiments.md E9/E10; raw JSONs.
Status: ACTIVE. Scope widened 2026-08-11: it is not one reasoning
model. ALL FIVE stored E10 answers end mid-token - including the
three non-reasoning models that did emit tables. Qwen3-30B-A3B's
last row stops at "| GLM-4.7-Flash-MXFP4_MOE.gguf | 62", cut off
before 62.94, which is exactly the element keyed scoring marked as
its one miss. So E10 measured a harness ceiling, not the field, and
its per-model differences are not attributable until re-run.

CORRECTED 2026-08-12: the 2026-08-11 widening named max_tokens as
that ceiling for all five. The serverlogs say TWO mechanisms, split
by tokenizer:

| model | prompt tok | headroom | decoded | stopped by |
|---|---|---|---|---|
| qwen3-30b-a3b | 16,140 | 244 | 244 | CONTEXT |
| qwen3-4b | 16,140 | 244 | 244 | CONTEXT |
| qwen3-coder-30b | 16,140 | 244 | 244 | CONTEXT |
| glm-4.7-flash | 14,929 | 1,455 | 1,200 | max_tokens |
| gpt-oss-20b | 14,877 | 1,507 | 1,200 | max_tokens |

The three Qwen models share a tokenizer, so all three filled 98.5%
of a 16,384-token slot and the server logged truncated=1. The slot
was half of `-c 32768` because the harness served `-np 2`. Raising
max_tokens - the fix the widening implied - would have re-truncated
those three in exactly the same place.

The deployment rule generalises accordingly: an eval report must
state the per-slot CONTEXT as well as max_tokens, because -c is
divided by the slot count and the answer's real budget is
`n_ctx/n_slots - prompt_tokens`, not the ceiling on paper.

Re-run with NP=1 (n_ctx_slot 32768), qwen3-30b-a3b decoded 1,080
tokens, stopped naturally at truncated=0 under the SAME 1200-token
max_tokens, and scored 8/8 against the sealed key where the starved
run scored 7/8 as a lower bound. It still reproduces the 253.5 trap
as table data, so that faithfulness failure is real and survives.
A fourth instance sits outside E10: e9-qwen3-4b's e9-detect answer
decoded 182 tokens against 182 tokens of headroom, and was recorded
PASS.

The reasoning-channel mechanism in this finding explains gpt-oss-20b
specifically; a ceiling of one kind or the other hit everyone.
Evidence + method: results/keyed-vs-pairwise.md,
results/eval-pilot/ctxfix-ctxcheck.serverlog,
spikes/eval-pilot/audit_ceiling.py (204 answers classified).

## F21 - speculative decoding spans 0.53x-3.73x by workload; silently inert without --spec-type

**Kind: PLATFORM**

Same model (Qwen3-32B), same 0.6B draft, same flags: 3.73x on
repetitive text (16/16 acceptance), +17% on explanatory prose, 0.53x
- a HALVING - on analytical/creative prompts, where the target pays
to verify rejected drafts. Deployment rules: (1) spec decode defaults
OFF; enable per-workload after measuring on the production prompt
mix; candidates are boilerplate/templated/structured output; (2) at
067de937 `-md` alone loads-but-never-uses the draft - `--spec-type
draft-simple` is required, and the only tell is one INFO line; (3)
fast MoE targets gain little even on friendly text (+9%): spec decode
is a slow-dense-model tool. The two method lessons here - a speedup
quoted without its workload, and a flag that loads but never acts -
are split out as **F128** (2026-09-01).
Evidence: results/experiments.md E13; raw bench-e13-*.
Status: ACTIVE.

## F22 - Vulkan and ROCm split by workload phase (generation vs prefill)

**Kind: PLATFORM**

Same model / machine / session (Qwen3-30B-A3B, E18, 2026-07-05, ROCm
7.2.4 gfx1151 native): **Vulkan wins generation (tg) at every depth**
(+29.5% at d0, narrowing to +7.8% at 32K); **ROCm wins prefill (pp) at
every depth** (+6.6% at d0, WIDENING to +79% at 32K - ROCm's 32K pp
323.68 vs Vulkan 180.77 = 1.79x). Mechanism: prefill is compute-bound
(ROCm's mature rocBLAS/hipBLAS GEMM kernels win, advantage compounds
with the longer-context attention at depth); generation is
memory-bandwidth-bound (Vulkan's leaner per-token path wins; HIP
runtime has more per-token overhead). Confirms the community "ROCm
better at long context" claim WITH PRECISION - it is prefill, not
generation. Deployment rule: pick the backend by which phase dominates
the workload - long-prompt/short-output (document QA, RAG ingest,
summarization, extraction) -> ROCm; short-prompt/long-output (chat,
drafting) -> Vulkan. Both backends handled 32K with no OOM (ROCm sees
the full 108GB GTT as VRAM). Practical: the E15 84K-doc ingest (~17 min
on Vulkan) would shorten materially on ROCm (extrapolation beyond 32K
flagged). This is the first cross-backend finding; all prior constants
are Vulkan-only (F10 status note).
Evidence: results/experiments.md E18; raw bench-e18-{vulkan,rocm}.md.
Status: ACTIVE - but ARCHITECTURE-SPECIFIC; the ROCm-wins-prefill half
holds only for pure MoE and INVERTS for MLA. See F23.

## F23 - the Vulkan/ROCm split is architecture-dependent and depth-explosive

**Kind: PLATFORM**

Extends/qualifies F22 with two additions (E18a deep pure-MoE; E18b MLA):
1. **Pure MoE (Qwen3-30B): ROCm's prefill advantage EXPLODES with
   depth** - 1.79x (32K) -> 3.55x (64K) -> 8.08x (96K). Vulkan prefill
   COLLAPSES past 32K (pp 180.77 -> 53.39 -> 16.57; at 96K pp 16.57
   falls below its own tg 18.40), while ROCm holds (323.68 -> 189.53
   -> 133.86). Practical: an 84K-doc ingest drops from ~17 min
   (Vulkan, E15) to ~2-3 min on ROCm.
2. **MLA (GLM-4.7-Flash): the split INVERTS - Vulkan wins BOTH phases
   at every depth**, ROCm never wins, and ROCm's prefill deficit
   widens with depth (Vulkan +1.6% at d0 -> +19.4% at 32K). ROCm does
   not rescue Vulkan's MLA prefill collapse (F8); it collapses harder.
Generation (tg): Vulkan wins for both architectures, gap shrinking to
noise at extreme depth. DEPLOYMENT RULE (corrected, business-grade):
ROCm is a large and growing win ONLY for pure-MoE prefill-heavy work
(document ingest, RAG, summarization); for MLA models use Vulkan for
everything; generation-heavy chat is always Vulkan. Vulkan is the safe
default; ROCm is a targeted optimization for one model class. Mechanism
candidate: MLA's latent-projection matmul shapes don't favour rocBLAS
the way standard-attention GEMMs do (not separable here).
Evidence: results/experiments.md E18a/E18b; raw bench-e18a-deep-*,
bench-e18b-glm-*. Status: ACTIVE.

## F24 - under concurrent disk I/O, near-edge weight loads can deadlock in the amdgpu VM/SDMA suballocator, not just DeviceLost-abort

**Kind: PLATFORM**

> **Canonical write-up: docs/memory-edge-deadlock.md** consolidates this whole
> cluster (F24-F28 + the C1 live repro + the negative controls) into one
> operational reference - fingerprint, mechanism, triggers, recovery, and
> prevention rules. Read that before any large-model session; the F24-F28
> entries below remain the primary evidence records.

Confirmed via kernel hung-task trace (`sudo dmesg`, Alastair, 2026-07-08):
GLM-4.5-Air (~68GiB) loading under Vulkan while a concurrent 62GB
`sha256sum` ran blocked `llama-bench` (PID 444301) in D-state for 1228+
seconds inside `amdgpu_cs_ioctl -> amdgpu_vm_bo_update ->
amdgpu_vm_sdma_prepare -> amdgpu_job_alloc_with_ib -> amdgpu_sa_bo_new ->
drm_suballoc_new -> schedule` - a wait on the driver's own small-buffer
suballocator for VM page-table-update SDMA jobs, not a Vulkan
heap-reporting limit and not the clean DeviceLost/SIGABRT F6 originally
recorded (isolated run, no concurrent I/O). Distinct failure class from
F6: unkillable (SIGKILL cannot act on a D-state task - only the kernel's
own recovery or a reboot clears it), no CPU/disk activity after the
stall (`vmstat` si/so/bi/bo near-zero throughout), does not self-resolve
(unchanged after 44+ minutes). A same-weight-size re-run with NO
concurrent I/O passed cleanly this session (1.3% CV, no abort) -
concurrent I/O looks like the necessary trigger, not the weight size
alone. Operational rule: never run heavy disk I/O (downloads, hashing,
backups) concurrently with near-edge (>~60GiB) model loads; recovery
requires a reboot, not a kill. Status: ACTIVE - mechanism confirmed via
kernel trace, not speculation. Supersedes any speculation from the
disputed external-research pass earlier in this investigation (none of
its claimed mechanisms - Vulkan command timeout, a hard 64GB cap, kernel
version requirements - match what the kernel trace actually shows).
Evidence: docs/PHASE-A-LOG.md 2026-07-08 F6-follow-up entries;
docs/plans/2026-07-08-vulkan-memory-ceiling-investigation.md Task 2.

**Refinement (2026-07-10, cause-isolation Run 1b - reproduced on demand).**
The C1 positive control (docs/plans/2026-07-10-deadlock-cause-isolation.md)
deliberately recreated this deadlock and watched it in real time (finer detail
than F24's original `dmesg`-only record): GLM-4.5-Air `-d 0,8192` (~68 GiB)
launched into a sustained infinite `sha256sum` loop over two 46 GiB shards. The
operative trigger is MEMORY PRESSURE, not disk I/O per se - once the model (68
GiB) plus the I/O loop's file reads exceed 128 GB RAM, model pages get evicted
and re-read (RSS dropped 64->53 GiB while read_bytes climbed past the model
size), the Vulkan backend gets its first buffer but cannot get the rest
resident, and the VM-update SDMA suballocator starves. Confirmed live signature:
VRAM parks at exactly 2.00 GiB (2,147,483,648 B), RSS collapses to ~52 MB, and
`wchan` reads `drm_suballoc_new`. Proved a true deadlock (not thrash): removing
all I/O pressure did not recover it, and `SIGKILL -9` left the process present
and still D-state. This is the first deliberate, watched-in-real-time
reproduction of the class; C2/C3/C4 (F27/F28's open candidate triggers) remain
under investigation.

## F25 - ROCm loads the exact ~68GiB invocation that destabilises Vulkan; the constraint is Mesa/RADV's heap split, not the GTT pool

**Kind: PLATFORM**

F6's original DeviceLost occurred under Vulkan on GLM-4.5-Air's combined
`-d 0,8192` invocation (~68GiB weights). Running the identical command
(same shard, same depths) on the pre-built ROCm backend (7.2.4,
gfx1151 native, provenance per F22/F23) completes cleanly: exit 0, all
four rows present, no HIP OOM/abort. ROCm reports the full 114688 MiB
(112GB) GTT pool as VRAM and loads the artefact without incident -
pp512 (d0) 295.30 t/s, tg128 (d0) 21.89 t/s, pp512 @d8192 182.62 t/s,
tg128 @d8192 15.87 t/s. Since both backends draw from the same physical
GTT pool and only Vulkan aborts, the constraint sits in Mesa/RADV's
Vulkan-side heap accounting/split, not in the kernel's memory ceiling
itself - consistent with F22's aside that "ROCm sees the full 108GB GTT
as VRAM" and extends it into a direct, decisive test. Practical:
switching a near-edge single large model to the ROCm backend is a
viable way to reach memory Vulkan's heap-split currently can't, at the
cost of Vulkan's generation-throughput edge (F22/F23) - tg128 here
(21.89 t/s d0) is markedly below Vulkan's typical range for models this
size, so this is a capacity workaround, not a throughput upgrade.
Status: **CORRECTED by F26 - the comparison was confounded, not
false-but-imprecise.** This run's `ttm.pages_limit` had just been
raised from ~105.47GiB to 112GB (Task 4 Steps 1-2, done during the same
reboot that preceded this run), so it was never compared against
Vulkan at the same ceiling. When Vulkan was re-run at this same 112GB
ceiling (Task 4 Step 4), it ALSO passed cleanly - meaning Vulkan was
never observed to abort under any controlled condition in this
investigation, at either pool size. The "ROCm succeeds where Vulkan
aborts" claim does not hold; see F26 for the full reconciliation. The
factual measurements above (ROCm's numbers, the 112GB VRAM report) are
unchanged and still correct - only the causal claim is retracted.
Evidence: docs/PHASE-A-LOG.md 2026-07-08 "Task 3: ROCm single-shot
load" entry; results/raw/bench-t3-glm45air-rocm.md;
docs/plans/2026-07-08-vulkan-memory-ceiling-investigation.md Task 3.

## F26 - F25's ROCm/Vulkan comparison was confounded by a concurrent GRUB change; Vulkan does not abort at either pool size when idle, and F6's original crash remains unreproduced

**Kind: METHOD** - the confound. What the re-runs established about Vulkan
itself is **F129**, split out 2026-09-01.

Task 4 of the same investigation (docs/plans/2026-07-08-vulkan-memory-
ceiling-investigation.md) revealed that `ttm.pages_limit` had been
raised from 27648000 to 29360128 (~105.47GiB -> 112GiB) immediately
before the reboot that preceded F25's ROCm test - confirmed from GRUB
backup timestamps (`/etc/default/grub.bak-2026-07-08` at 17:21, live
file edited 17:22, reboot at 17:40) and the live
`/sys/module/ttm/parameters/pages_limit` reading 29360128. F25's ROCm
run therefore used a larger pool than the historical F6 crash and the
same-day Task 2 Step 1 Vulkan baseline, making "ROCm succeeds where
Vulkan aborts" an apples-to-oranges comparison. Re-running Vulkan's
exact F6 invocation at the new 112GiB ceiling (Task 4 Step 4) resolved
it decisively: **Vulkan passed cleanly again** - exit 0, all four rows,
no DeviceLost (pp512 d0 230.59, tg128 d0 24.24, pp512 @d8192 41.28,
tg128 @d8192 21.06 t/s). Since Vulkan had ALSO passed cleanly at the
OLD ceiling earlier the same day (Task 2 Step 1, 1.3% CV, no abort),
Vulkan has now passed this exact invocation at both pool sizes when
idle - it has not been observed to fail under any controlled condition
in this entire investigation. Only the historical F6 report shows a
Vulkan failure, and two dedicated reproduction attempts today failed to
reproduce it: an idle re-run passed clean, and a heavy-disk-I/O re-run
produced a categorically different failure (F24's kernel-level SDMA
suballocator deadlock, not F6's DeviceLost/SIGABRT). **Conclusion: F6's
original failure mode remains unreproduced and its trigger is not
established** - neither backend choice (F25's claim) nor pool size is
supported as the cause, since Vulkan is clean at both ceilings and the
one deliberate attempt to reproduce via heavy I/O produced a different
failure entirely (F24, which stands on its own kernel-trace evidence
and is unaffected by this correction). The leading unproven candidate
for F6's original trigger remains something specific to that run's own
circumstances (it followed immediately after a 73GB download+SHA256
verification of the same artefact) rather than disk I/O in general.
Separately, Task 4 Step 3's `vulkaninfo` check (no sudo needed;
`dmesg`'s GTT-ready line could not be re-checked, sudo-restricted for
agent-spark) found the device-local Vulkan heap now at 76.00 GiB,
consistent with the plan's "~74-75GiB" prediction for a heap that
scales proportionally (~2/3) with `ttm.pages_limit` - this narrower
claim (the heap split scales with the pool) IS confirmed and survives
this correction independently of the backend-comparison retraction.
One further open, UNRESOLVED discrepancy surfaced by the two idle
Vulkan runs: pp512 @d8192 dropped 39% at the larger pool (67.91 ->
41.28 t/s) despite more memory headroom, with tg128 and both d0 rows
essentially unchanged between ceilings. No system-load snapshot exists
for the OLD-ceiling run to rule out a load-state difference, and no
other cause has been confirmed - flagged rather than guessed at, per
the project's discrepancy discipline.
Status: ACTIVE. F6's original trigger remains genuinely open; do not
treat F25's backend-choice framing as established going forward.
Evidence: docs/PHASE-A-LOG.md 2026-07-08 "Task 4: Vulkan re-run at the
new 112GiB ceiling" entry; results/raw/bench-t4-glm45air-ttm112.md;
docs/plans/2026-07-08-vulkan-memory-ceiling-investigation.md Task 4.

## F27 - F24's amdgpu SDMA suballocator deadlock recurred without F24's own confirmed trigger (no concurrent heavy I/O, and on the model with the MOST headroom in its batch)

**Kind: PLATFORM**

Confirmed via `/proc/<pid>/wchan` (agent-spark is a non-sudoer on sparkmax;
`dmesg` is sudo-restricted, but `/proc/<pid>/wchan` and `/proc/<pid>/status`
are readable for one's own process and sufficient here) during the
"upper limits" benchmarking campaign (2026-07-09), Task 6 of
docs/plans/2026-07-09-upper-limits-reporting-plan.md - Devstral 2 123B
(UD-Q5_K_XL, 82.19GiB weights, 29.81GiB headroom below the 112GiB
ttm.pages_limit ceiling, the MOST headroom of any of the 8 upper-limits
models). `llama-server` (PID 361827, the eval-pilot quality-eval
invocation: `-m <gguf> -np 1 -c 32768 --jinja --no-webui --host
127.0.0.1 --port 8100`) entered D-state (uninterruptible sleep) during
model load and has not self-resolved as of this writing: unchanged
wchan across repeated checks spanning 24-27+ minutes, `read_bytes`
(121,774,907,392 - **121.8GB**, more than the ~88.2GB total model size
across both shards) consistent with a retry/thrash pattern rather than
a normal single sequential read, `VmRSS` essentially flat throughout
(29,712 kB - the process never actually finished allocating the model
into resident memory). `cat /proc/361827/wchan` reads exactly
`drm_suballoc_new` - the same terminal frame as F24's kernel trace
(`amdgpu_cs_ioctl -> amdgpu_vm_bo_update -> amdgpu_vm_sdma_prepare ->
amdgpu_job_alloc_with_ib -> amdgpu_sa_bo_new -> drm_suballoc_new ->
schedule`), strongly suggesting the same deadlock class, though the
full kernel stack could not be re-confirmed via `dmesg` this session
(sudo-restricted) - **the wchan match is suggestive, not as decisive as
F24's original full-trace confirmation; flagged as the weak link in
this finding.**

**What's genuinely surprising, and why this is a distinct finding from
F24 rather than a duplicate:** F24's established trigger was a near-edge
weight load (>~60GiB) running *concurrent with heavy disk I/O*
(specifically, a 62GB `sha256sum` running alongside GLM-4.5-Air's
~68GiB load) - the operational rule derived from it was "never run
heavy disk I/O concurrently with near-edge model loads." This session's
campaign has followed that rule throughout (gateway paused, no
concurrent downloads/hashing during any bench/eval run - see
docs/plans/2026-07-09-upper-limits-reporting-plan.md Global
Constraints). No heavy concurrent I/O has been identified for this
occurrence. Two candidate explanations, neither confirmed:
1. **Cumulative driver/GPU state degradation.** By the time this
   occurred, the session had already run ~13 full large-model
   load/unload cycles today (8 downloads' worth of prior verification
   plus 5 completed benchmark tasks x ~4 loads each, plus 2 prior
   Devstral attempts) with no reboot in between. F24's own status note
   already flagged the mechanism as real but under-characterised
   ("constants... expected to move with kernel releases"); it's
   plausible the suballocator's failure probability rises with
   accumulated fragmentation/state rather than requiring a single
   heavy-I/O trigger event.
2. **A lighter-weight trigger than previously characterised.** The
   Task 6 implementer's own investigation (results/experiments.md E23)
   ran multiple bench/eval attempts, re-runs, and file operations
   (copies, stderr redirects) against this model in fairly quick
   succession while chasing an unrelated harness bug (see the E23
   entry's "Issue 1" - `run_step8_leg.sh` was found to lose `tg128`
   output because it doesn't redirect stderr). It's possible even
   modest concurrent filesystem activity, not just F24's original
   62GB-hash-scale I/O, is sufficient under the right timing.

**Impact on the campaign:** benchmarking halted immediately on
discovery (2026-07-09) rather than attempting to work around or wait
out the stuck process - per F24's own established rule, recovery
requires a reboot, not a kill (SIGKILL cannot act on a D-state task
blocked in this kernel path). The E23 entry (Devstral 2 123B) has two
incomplete legs as a direct result: the d=8192 throughput leg and the
eval-pilot quality run. Both are recorded as blocked-by-F27, not as
"config incompatibility" (an earlier characterization in this same
entry that undersold the severity and has been corrected - see E23's
revision history in results/experiments.md).
Status: **ACTIVE, mechanism suggestive but not fully confirmed** (wchan
match only, no `dmesg` trace this session - re-confirm via `sudo dmesg`
after reboot if the log survives, per F24's own confirmation method).
The trigger-condition mismatch with F24 is the most important open
question this finding raises: if F24's "avoid concurrent heavy I/O"
rule is insufficient on its own, the operational implication is
broader than previously scoped - possibly bounding the number of
large-model load/unload cycles safely run per session without a reboot,
not just concurrent I/O. Not established; flagged for investigation,
not asserted as fact.
Evidence: this entry (live process inspection, 2026-07-09);
results/experiments.md E23 (Devstral 2 123B); F24 (the original,
fully-confirmed instance of this failure class); process was still
D-state/unresolved as of this HANDOFF's commit - PID 361827 may still
exist post-reboot-request if the reboot hasn't happened yet; do not
attempt to interact with it further, it will be cleared by the reboot.

**Recovery confirmed (2026-07-09, later same day).** The reboot cleared
it exactly as this finding predicted: PID 361827 is gone
(`/proc/361827` no longer exists), no D-state tasks remain, and a
known-good `llama-bench` (Qwen3-4B) load+inference passed at nominal
baseline speed post-reboot (full sign-off: docs/PHASE-A-LOG.md
"2026-07-09 (later) - Post-reboot recovery"). One operational note the
recovery added: the graceful reboot did NOT complete on its own - the
D-state task stalled shutdown and a hard power cycle was required. So
the F27 failure mode costs a *hard* reset, not just a reboot; budget
for that when the repeatability campaign's failure-repro phase
deliberately re-triggers this class. The `sudo dmesg` re-confirm avenue
noted above is now foreclosed for THIS instance - the kernel ring
buffer did not survive the power cycle - so the wchan match remains the
permanent weak link for F27's evidence. The trigger investigation
itself stays **ACTIVE/open** (unchanged): the repeatability campaign is
designed to probe cumulative-state vs lighter-trigger by accumulating
many load/unload cycles before the failure-repro phase.

## F28 - a third amdgpu suballocator deadlock, this time on an IMMEDIATE retry of a leg that had just crashed cleanly (DeviceLost) moments earlier - a new candidate trigger

**Kind: PLATFORM**

Confirmed via `/proc/<pid>/wchan` (same method as F27; `dmesg` remains
sudo-restricted for agent-spark), 2026-07-10, during the repeatability
campaign's Phase 2 (near-edge/slow bucket,
docs/plans/2026-07-09-repeatability-campaign-plan.md Task 25) -
Command A+ (Q3_K_M, 95.53GiB weights, 16.47GiB headroom below the
112GiB ceiling).

**Sequence that produced it:** the d0 leg succeeded cleanly (13.52 t/s,
matching the original run's 13.68). The d8192 leg's FIRST attempt
crashed with a clean, non-hanging `vk::DeviceLostError`
(`radv/amdgpu: Not enough memory for command submission`, rc=134,
core dumped) - GPU VRAM usage returned to idle baseline (~148MB)
immediately afterward, no D-state, no hang. This is itself a genuine
repeatability finding (recorded separately): the ORIGINAL run had
d4096 crash and d8192 succeed; THIS rerun had d0 succeed and d8192
crash - the failure point is not consistent across runs for this
model. An immediate retry of the SAME d8192 leg (started once the GPU
was confirmed idle) then entered D-state during model load and did not
self-resolve: `cat /proc/84804/wchan` read exactly `drm_suballoc_new`,
`read_bytes` was observed unchanged (171,187,822,592 B) across two
successive checks ~30s apart, `VmRSS` flat at 56,776 kB, and
`mem_info_vram_used` showed a suspiciously round 2,147,483,648 B
(exactly 2.00 GiB) held steady rather than climbing toward the model's
actual footprint - all consistent with F24/F27's confirmed deadlock
signature.

**Why this is a distinct data point, not a duplicate of F27:** F27's
open question was whether the trigger is (1) cumulative GPU/driver
state degradation across many cycles in a session, or (2) a
lighter-weight trigger than F24's original heavy-concurrent-I/O
condition. This occurrence adds a THIRD candidate that hasn't been
articulated before: **retrying a load immediately after that exact
model/depth just crashed with a clean DeviceLost may itself elevate
deadlock risk** - as if the crashed attempt leaves GPU/driver state
partially unwound in a way that makes the very next load more fragile,
even though the intervening idle check showed VRAM back at baseline.
This is speculative (n=1, no controlled comparison against a
retry-after-a-longer-cooldown or retry-of-a-fresh-leg), but it is a
concrete, falsifiable hypothesis for future sessions to test: does
waiting longer before a post-crash retry reduce recurrence? Command
A+'s headroom here (16.47GiB) is also meaningfully tighter than F27's
Devstral occurrence (29.81GiB, "the most headroom in its batch") -
unlike F27, this occurrence's tight margin is NOT surprising on its
own; what's new is the immediate-retry-after-crash circumstance.

**Impact on the campaign:** Phase 2 of the repeatability campaign
halted immediately on discovery, per the same F24/F27 rule - this is
unkillable (SIGKILL confirmed ineffective against this kernel path
across three separate occurrences now) and recovery requires a reboot,
not a kill or a wait. `agent-spark` is a non-sudoer on sparkmax and
cannot reboot the machine - this requires Alastair. Command A+'s
throughput entry in results/experiments.md is left with d8192 in an
ambiguous state (one clean crash, one deadlocked retry, no successful
value) - recorded as such, not papered over with a
fabricated number. The rest of Phase 2 (Devstral d0/d4096) and all of
Phase 3 (which was already going to deliberately attempt the Devstral
F27 repro) are blocked until recovery.

Status: **ACTIVE**, mechanism consistent with F24/F27's confirmed
signature (wchan match), the "immediate-retry-after-crash" trigger
candidate is new and unconfirmed - flagged for investigation, not
asserted as fact.

Evidence: live process inspection this session (PID 84804);
`results/raw/bench-ul-command-a-plus-rerun-d8192-stderr.log` (the
first clean-crash attempt's DeviceLost trace);
results/experiments.md (Command A+/E22 repeatability entry, once
written up); F24 and F27 (the two prior confirmed instances of this
failure class).

**Do not attempt to interact with or resume PID 84804 - it will be
gone after the reboot.** Once GPU/system health is confirmed
post-reboot (per F24/F27's established checklist: no stray
llama-bench/llama-server, no D-state, a known-good small-model sanity
bench at nominal baseline speed), resume Phase 2 at Devstral d0/d4096,
NOT at Command A+ d8192 - that leg's repeat attempt is now itself
folded into the open trigger-investigation question, not a routine
retry.

**Recovery (2026-07-10) - HARD POWER CYCLE required AGAIN (Alastair).**
The `sudo reboot` did NOT complete on its own: from a remote machine the
box went to "No route to host" / connection-timed-out and never came
back on the graceful path - Alastair had to perform a **hard power
cycle** to bring it up, exactly as with F27's recovery
(2026-07-09). The machine is now back: booted 2026-07-10 18:28:14
(confirmed from inside - this session runs on sparkmax). **This is now
the SECOND consecutive occurrence of this deadlock class (F27, then
F28) whose recovery required a hard power cycle, not a clean reboot** -
it is no longer a one-off. Operational upshot, reinforcing F27's note:
budget for a physical power cycle (someone at the machine) whenever this
deadlock class is hit, especially during the repeatability campaign's
deliberate failure-repro phase; a remote `sudo reboot` should be
expected to stall on the wedged D-state task and leave the box
unreachable until power-cycled. GPU/system health is NOT yet signed off
for this recovery - the required known-good small-model sanity bench
(Qwen3-4B at baseline) has not run, and `llama-gateway.service`
auto-restarted on boot and is currently holding the 30B on the GPU (must
be paused before the sanity bench, per the F24/F27/F28 one-model rule).

## F29 - benchmark results are properties of the whole measurement stack, demonstrated eight times in one campaign

**Kind: METHOD**

Status: confirmed. Phase 2 (2026-07-11/12). Eight successive
grader/harness corrections, each caught by pre-registration misses or
structural signatures BEFORE publication: bare-return JS assertions
(SyntaxError failing every model), IIFE body-wrap (JSON tests auto-failing
all 8 models), reasoning-emission contamination, a token-starvation
misreading, a hardcoded 100-token cloud cap binding only Mistral (three
lanes, three effective budgets), a timeout-SIGTERM class killing healthy
runs, an unlogged launcher creating a phantom "32K stability ceiling"
(retracted: 48K passed 6/6 on repro), and a double-execution tool loop.
Deployment implication: no score is interpretable without model + prompt +
serving config + output budget + extraction policy + grader, together.
Evidence: results/experiments.md E28 corrigenda v1-v5, E30 correction,
if-json-regrade-v3.md; corrections log in
reports/integrated-technical-results-v2.md.

## F30 - compression preserves document-task competence to the ternary floor; knowledge bends first, below 2-bit

**Kind: MODEL**

Status: provisional (single family, suite-ceiling bounded). E29: 8 rungs
of Qwen3-30B-A3B (30.3GiB Q8_0 -> 7.5GiB ternary): summarisation 26-28/30
and instruction-following 22-23/24 at EVERY rung; MMLU flat within CIs to
Q2-class, first clear bend at 1-bit-class (77.0%), largest step at ternary
(72.9% - statistically indistinguishable from the 60GiB gpt-oss-120b's
72.7%, knowledge-benchmark cross-family comparison only). tg128 rises 61
-> 115 t/s as size falls. Deployment implication: Q2-class gives ~1.7x
speed at a third the size for no measured document-task cost. Reverses the
pre-registered degradation-order prediction; published as a miss.
Evidence: E29 entry, results/raw/mmlu-quant-ladder.json.

## F31 - the usable long-context envelope: 48K (Vulkan) / 64K (ROCm serving, v1.x evidence); accuracy holds to 80K+, speed is the only bind

**Kind: PLATFORM**

Status: confirmed for Vulkan (Release 1.0); ROCm extension provisional
(post-cut-off, prediction HIT: 64K first answer 3m17s vs Vulkan 6m43s,
2.05x prefill at depth, 6/6 unchanged; graduates F22 from bench-measured
to serving-measured). Retrieval accuracy 6/6 at every measured rung to
80K; first-answer wall-clock is the binding constraint; follow-up
questions ~1s at every rung via prefix caching (load once, interrogate all
afternoon). The 4B is NOT a long-context lever (4/6 + 36min at 80K -
F13's dense depth penalty hits both axes). Worked example at the limit
3/3 incl. a supersession trap. Evidence: E30 entries + correction,
results/deep-eval/e30-*, envelope-worked-example.md.

## F32 - reasoning-emitting models are unsuitable for strict-format document work under this stack, and carry a 3-12x token tax

**Kind: MODEL**

Status: confirmed (pre-registered decision rule, both grading views).
E31: MiniMax M2.7, Qwen3.5-397B and magistral-medium stay at 12.5-41.7%
instruction-following at MAXTOK=8192 with near-zero truncations - neither
generous budgets nor content-extraction rescues them; deliverables
interleave with reasoning prose and genuinely violate format constraints.
Median completion tokens 472-1700 vs 58-273 for direct models. Deployment
implication: the token tax is a wall-clock tax locally and a money tax in
cloud, for equal-or-worse graded output on these task shapes.
Evidence: E31 entry, e31-cloud-summary.md, reasoning-extraction-regrade.md.

## F33 - document-benchmark strength does not predict coding-agent competence

**Kind: METHOD**

Status: confirmed (one family pair, two real tasks - narrow but clean).
The Qwen3-30B workhorse (top of the 10-model document matrix, 93.3%/87.5%)
scored 0 on BOTH real-repository coding tasks (85 tool calls of thrash,
zero test runs), while Qwen3-Coder-30B (same size, code-tuned) delivered a
verified strong pass in 129s. Real-work ordering (Coder > GLM-4.7 >
workhorse) REVERSED the synthetic screen's shortlist. Deployment
implication: select coding models by agentic trial, never by document/
knowledge benchmarks; headline candidate for a developer-facing page.
Evidence: docs/plans/2026-07-12-coding-screen-10-realproject-results.md,
results/coding-screen/.

## F34 - real-drafting usability is a different axis from fact-accuracy; the model is the lever, and the best safe local model matches cloud-Mistral but trails the OpenAI frontier

**Kind: METHOD** - the two-axes lesson. Which models actually draft well is
**F130**, split out 2026-09-01.

Status: confirmed (n=30 per model, clean instrument, two independent rounds).
Measured OUTPUT QUALITY on 10 real solicitor/accountant tasks (draft letters,
summarise agreements, extract terms, attendance notes) - not fact-trap
accuracy - judged on a usability rubric ("would a solicitor send it with only
light edits?") by an INDEPENDENT full-source judge (claude-opus-4.8).

Findings:
- Fact-trap accuracy (workhorse 93.3% summarisation) does NOT predict drafting
  usability. On real drafts the Qwen3-30B workhorse scores ~2.6/5 usability.
  Different axes; the headline capability number oversells send-readiness.
- The MODEL is the lever, not prompting. Solicitor system prompt, few-shot,
  local self-refine and Q8 precision did NOT move the workhorse off ~2.4-2.6.
  A better-tuned model does: Mistral-Small-24B (usability ~3.0, faithfulness
  ~4.0) beats the workhorse (2.6/3.1) broadly (6/10 tasks).
- Q4 == Q8 for drafting quality (3.03 vs 2.90) - run the fast 14GB Q4, not the
  slow 25GB Q8. (Mistral-24B is DENSE, ~5-8x slower than the Qwen3-30B-A3B MoE.)
- Local Mistral-Small-24B ~= cloud mistral-large (3.03 vs 3.17 usability) and is
  MORE faithful (4.00 vs 3.70) - the own-vs-rent thesis in its strongest form.
- BUT all Mistral (local + cloud) trail the OpenAI frontier gpt-5.6-sol (4.37
  usability, 4.77 faithful); blind pairwise best-local-vs-frontier 4-26.
- Old Mixtral-8x7B is the worst tested (1.83) - the family improved enormously.
- Local quality is strongest on GROUNDED tasks (extraction, summarisation:
  near send-ready, facts exact) and weakest on open-ended drafting - which fits
  the confidential-document use case well.

Two measurement artifacts caught + fixed before any conclusion (methodology
note): (1) judge saw only the first 6000 chars of source -> penalised faithful
summaries of the tail as fabrication; (2) a few-shot exemplar's fictional
letterhead leaked into 9/10 outputs. Both would have produced a false "local is
bad / can't improve" headline. Suspect-the-ruler held.

Deployment implication: recommend Mistral-Small-24B-Q4 as the DRAFTING default
(better + still fast enough), Qwen3-30B-A3B MoE for speed/triage; the frontier
gap is real and is what the attended big-model night (command-a/GLM-4.5-Air)
and a house-style fine-tune exist to close.
Evidence: results/real-quality/ (baseline + ablation + ablation2 + confirm),
tools/real_quality_run.py + quality_ablation*.py + quality_confirm.py,
docs/plans/2026-07-12-local-quality-experiments.md.

## F35 - the local drafting ceiling is the base model's raw generation quality: reasoning, raw size, self-critique, in-context exemplars, and Mixture-of-Agents all fail to raise it. The fine-tune is the lever - and it is doable ON-BOX (the "can't train on gfx1151" premise was wrong)

**Kind: MODEL**

Status: confirmed (2026-07-13, attended big-model night + reasoning trio +
training-free pipeline ablation + in-context exemplar test, same 10-task instrument
+ frontier judge as F34). Four independent training-free levers were tested against
the ~3.0-3.4 local usability plateau (frontier gpt-5.6-sol 4.37) and all four failed
to break it (two actively lowered it), converging on one conclusion: the ceiling is
set by the base model's raw generation, and only levers that raise the base
capability itself (a fine-tune) can move it.

1. **Reasoning does not raise it.** Five reasoning models across four families all
   land on the plateau: gpt-oss-120B 3.00, DeepSeek-R1-Distill-32B 3.00,
   Qwen3-32B-thinking 3.00, GLM-4.7-Flash 3.10 (Nemotron-120B reasoning-capable
   3.30). Reasoning tuning helps math/code/logic; it does not transfer to
   drafting send-readiness. (Instrument: reasoning traces routed to
   reasoning_content by llama.cpp, verified clean - the judge scored only the
   final deliverable; overflow guard for a think-budget that starves the answer.)
2. **Raw size does not raise it.** Big writing-tuned models plateau too:
   Nemotron-120B (98GB, WritingBench-tuned) 3.30 - the local leader, and the only
   real (if modest) positive, from WRITING-TUNING not size; gpt-oss-120B (63GB)
   3.00; Mistral-Small-4-119B (74GB) 2.50 - the model BOTH independent "best local
   writing model" shortlists tipped as #2, verified genuinely weak (factual
   errors, fabrication, chatty non-deliverable wrapper), a sharp
   marketing-list-vs-task-eval divergence.
3. **Same-model self-critique cannot raise it (and can lower it).** A training-free
   pipeline (L0 baseline / L1 deterministic cleanup / L2 critic-checklist->revise /
   L3 best-of-N) HELPS a weak base modestly (Qwen3-30B 2.6->2.9, within noise) but
   HURTS a strong one (Mistral-24B L0 3.4 -> L2 2.6). Verified mechanism: the critic
   and reviser are the SAME ~3.0 model - it flags real defects (e.g. invented dates,
   judge-confirmed) but its FIXES introduce new errors (replaced an invented date
   with a temporally-incoherent source date). You cannot bootstrap quality above a
   model's ceiling by having it critique itself. Best-of-N (L3) is the one mild,
   robust, keepable positive; deterministic cleanup strips the chatty wrapper but
   over-strips completeness (fixable) and does not move usability.
4. **In-context gold exemplars ("more context") make it WORSE, not better.** A
   frontier (gpt-5.6-sol) gold exemplar of the same type, for a DIFFERENT fictional
   matter, injected as a style reference (leakage-controlled, like-for-like baseline
   in the same run) HURT both bases: Qwen3-30B 2.5->2.2, Mistral-24B 2.8->2.4
   usability. The real signal is a faithfulness collapse (Mistral 4.3->3.0;
   extraction task 5->1, judge: "riddled with fabricated facts"). Verified mechanism:
   shown a rich exemplar, the model imports its RICHNESS and fabricates matching facts,
   drifting off the actual source - it followed the literal "don't copy names"
   instruction (Mistral: zero name-leakage) but still invented NEW facts to match the
   exemplar's shape (missed the intent). Grounded tasks crater (a source to betray);
   generative tasks (no source) hold. Qwen3-30B additionally COPIED fictional names
   outright despite the instruction. The model can imitate style but cannot separate
   "copy the register" from "import the facts" even when told - a capability limit.
   IMPORTANT: this kills the in-context PROXY for the fine-tune, NOT the fine-tune
   itself - a fine-tune absorbs style into weights with no competing matter's facts in
   the prompt to bleed through, so it avoids this exact fabrication mode.

Measurement caveat (per compare-like-for-like): temp-0.3 drafting gives ~+/-0.3-0.4
run-to-run usability noise across the 10 tasks (Mistral-24B measured 3.0 and 3.4 on
two clean runs). The ~3.0-3.4 local cluster is within its own noise - the robust
statement is "local plateaus ~3.0-3.4, frontier 4.37," NOT a precise local
leaderboard. The L2 regression (>=0.5, dimension- and mechanism-corroborated) is
above the noise floor and real.

Implication: the fine-tune (house-style LoRA) is now the SOLE remaining lever to
close the frontier gap - the owned-model path the whole thesis rests on. A critic
genuinely stronger than the drafter could also work in principle, but locally there
is no model far enough above ~3.0 to serve, and a frontier critic breaks the on-box
thesis. Big models are also confirmed SAFE for drafting inference (low-I/O, quiet
box): Nemotron 98GB / command-a-plus 103GB ran with D-state 0 throughout (see
docs/memory-edge-deadlock.md negative controls).

**CORRECTION (2026-07-13, later - verified, not asserted): the "fine-tune needs cloud
because the box can't train" premise is WRONG.** This finding (and Q6) originally stated
sparkmax has no ROCm training stack for gfx1151. That is false: AMD ships ROCm PyTorch
nightly wheels for gfx1151, and a full LoRA training loop (forward -> loss -> backward ->
optimizer step, PEFT adapter) runs on the Radeon 8060S with the loss decreasing
(tools/finetune_smoke.py, proof in results/real-quality/moa/post.log: torch 2.10+rocm7.13,
GPU available True, loss 6.2349 -> 6.1315). Stack: ROCm 7.2.4 (on box) + torch from
`https://rocm.nightlies.amd.com/v2/gfx1151/` + transformers/peft/trl + adamw_torch/
adafactor optimizer (NOT bitsandbytes/QLoRA - those crash on gfx1151); env
TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1, HSA_ENABLE_SDMA=0; venv at var/ft-venv. The
original "CPU-only torch" was the documented `pip silently downgrades torch to CPU` trap,
not a hard wall. IMPLICATION: the fine-tune is an ON-BOX, on-prem, ZERO-CLOUD operation -
the strongest form of the own-your-capability thesis (confidential data AND the model
adaptation both stay on the machine). Q6's cloud-vs-on-box training-path question largely
collapses to "on-box, path 3".

**Lever 5 tested (2026-07-13): Mixture-of-Agents does NOT break the ceiling either.** 3
diverse local proposers (Mistral-24B, Qwen3-30B, GLM-4.7-Flash) + a faithful aggregator
(Mistral-24B). A PROPER analyse-then-synthesise aggregator (identify agreements/
contradictions/missing, resolve toward source) substantially beats a naive "merge the
best" one (faithfulness 3.50 -> 4.00; usability 2.70 -> 2.90) - the contradiction-detection
step is the mechanism, and doing MoA properly matters. BUT MoA(proper) still does NOT beat
the best single proposer (usability 2.90 vs Mistral-24B-alone 3.10, within noise;
faithfulness ties at 4.00), at ~4x the compute. Reason: the aggregator is itself a ~3.0
model - it cannot synthesise above its own ceiling - and two weaker proposers dilute the
aggregation toward them. Consistent with the ceiling law: pooling ~3.0 models through a
~3.0 aggregator stays ~3.0. (MoA remains valuable where the aggregator is genuinely
stronger, or with grounding - see docs/legal-assistant-blueprint.md; harness
tools/moa_test.py, results/real-quality/moa/.)
Evidence: results/real-quality/{bigmodel,reasoning,pipeline}/,
tools/{big_model_test,reasoning_model_test,quality_pipeline}.py,
docs/plans/2026-07-13-writing-quality-pipeline-design.md,
docs/plans/2026-07-12-local-quality-experiments.md (steps 3-5).

## F36 - on the coding axis, the local-vs-frontier gap on EASY tasks is efficiency + trustworthiness, not raw pass-rate; the dangerous failure mode (verification-gaming) is local-only

**Kind: MODEL**

Status: confirmed for the easy-fixture regime (2026-07-13, same agentic harness as the
F33 coding-screen, extended to run the frontier via OpenRouter). Ran 3 discriminating
self-contained fixtures (feature / refactor / debug) x {Qwen3-Coder-30B, GLM-4.7-Flash,
frontier claude-opus-4.8}, tests as ground truth (independent pytest), classifying each
run PASS / FALSE-COMPLETION / THRASH.

Findings:
- **Outcome parity is achievable on easy tasks.** GLM-4.7-Flash passed 3/3, matching
  the frontier (3/3); Qwen3-Coder passed 2/3. On self-contained fixtures near the
  local models' competence, the best local matches the frontier on pass-rate.
- **The real gap even here is efficiency.** Frontier solved each fixture in 9-12 tool
  calls; the locals took 11-31 (2-3x more steps) at the SAME passing outcome. The
  frontier is more direct; locals reach the answer by a longer path.
- **The dangerous failure mode is local-only: verification-gaming.** Qwen3-Coder, unable
  to satisfy a test edit, ran `rm test_config.py` - DELETED the test file - then declared
  done (false-completion, score 1). When it could not satisfy the check, it removed the
  check. Neither GLM nor the frontier did this. This is the single most important reason
  not to run a local coding agent unattended - it can fail silently AND destructively.
- Pass/fail alone hides both efficiency and verification-gaming; separating "how the run
  ended" (done/timeout/terminated) from "did tests pass" (independent pytest) is what
  surfaces them. This is the coding analog of the writing usability/faithfulness split.

Discrepancy resolved (no-hand-waved-discrepancies): Qwen3-Coder scored the feature
fixture 3 in the earlier campaign but 1 here - traced to agentic non-determinism (the
test-deletion path this run), not a scoring bug; score 1 correctly reflects the broken
repo state (no tests to collect).

CAVEAT (measurement honesty): these self-contained fixtures are EASY (frontier clears
each in <50s). This run does NOT reproduce F33's real-repository gap, where the Qwen3-30B
workhorse thrashed to 0 while Qwen3-Coder passed. The decisive coding gap shows on
real-repo tasks, not synthetic fixtures near the local ceiling; "GLM matched the
frontier" holds ONLY for easy tasks and must not be generalised. Ties to F33 (select
coding models by agentic trial, never by benchmark).
Evidence: results/coding-screen/gap/, tools/{coding_harness (--api-key),
run_coding_gap.sh, coding_gap_analysis}.py; F33 (the real-repo non-transfer finding).

## F37 - the on-box house-style fine-tune is the first lever to improve local drafting beyond the base - modestly, without harm, from a tiny corpus, entirely on-prem

**Kind: MODEL**

Status: confirmed for v1 (2026-07-13, first house-style LoRA run). The whole fine-tune
pipeline ran on-box on the real Mistral-24B (VLM): frontier-distilled faithfulness-filtered
corpus -> LoRA train on gfx1151 (train_loss 0.80, token-accuracy 0.85->0.89) -> merge ->
GGUF -> served -> eval. Held-out 10-task eval, fine-tuned vs base at the SAME Q8 quant
(isolating the LoRA, not a quant confound), frontier-judged:

- usability 3.10 -> 3.30 (+0.20, WITHIN the +/-0.3-0.4 noise floor - not a claimable win alone)
- tone 4.30 -> 4.80 (+0.50, ABOVE noise - the clearest gain; style transfer worked)
- faithfulness 4.20 -> 4.20 (PRESERVED - no fabrication introduced, unlike the in-context
  exemplars of F35 lever 4)
- completeness 3.80 -> 3.80; overall 3.73 -> 3.90
- per-task: 2/10 improved (summary 3->4, clause-review 2->3), 8 unchanged, 0 REGRESSED.

Interpretation: from just 25 generative-skewed, quality-filtered examples the fine-tune moved
drafting the RIGHT direction with NO harm - the first thing in the whole investigation
(F35's four failed levers + F36) to improve local drafting beyond the base model at all. The
usability lift is within noise; the tone lift and the uniformly-positive, zero-regression,
faithfulness-preserving pattern are the real signal. Direction proven; a larger, less-skewed,
retry-hardened v2 corpus is strongly justified to test whether usability clears noise toward
the frontier (4.37). STRATEGIC: this is the on-box, on-prem, zero-cloud realisation of the
own-your-capability thesis - confidential data AND the house-style adaptation both stay on
the box.

Methodology (suspect-the-ruler, twice): (1) the first eval scored the fine-tune 1.00 on ALL
tasks/dimensions - a uniform score is a broken-instrument tell, not a real result; the raw
outputs were pretraining garbage (forum posts), traced to a chat-template packaging bug (the
merge dropped Mistral-3.1's separate chat_template.json, so the GGUF had no template and the
served model emitted continuation garbage). Fixed (copy the template; wrapper patched), re-
converted, re-evaluated -> the real +0.20/+0.50 result. (2) corpus integrity: an end-only
write lost 56 examples to a timeout (fixed: incremental flush) and an unhandled API error
crashed generation at 25 (fixed: retry) - v1 ran on the 25 that survived.
Evidence: results/finetune/{housestyle-ft,base-q8}.json (v1; the canonical home per the r4.0
layout - identical copies previously sat in results/real-quality/bigmodel/ and were deduped
2026-07-16 after the v2 run silently overwrote that pair in place);
tools/{finetune_corpus,finetune_train,run_finetune_phase2,run_finetune_eval}.py/.sh;
docs/plans/2026-07-13-house-style-finetune-design.md; F35 (the ceiling this dents).

## F37 v2 - the decisive fine-tune verdict: a house-VOICE lever (tone, reproducible), NOT a send-readiness lever; a 5x bigger corpus does not change it

**Kind: MODEL**

Status: confirmed (2026-07-13, second fine-tune run on a 5x larger, de-skewed, faithfulness-
filtered corpus - 121 kept via the two-call grounded generation + retry + incremental-write
fixes). Same held-out 10 tasks, fine-tuned vs base at the same Q8 quant, frontier-judged.

Result (v2): usability 3.20 -> 3.30 (+0.10), tone 4.40 -> 4.70 (+0.30), faithfulness 4.20 ->
4.20 (preserved), per-task usability 3 up / 3 down / 4 same. The fine-tuned model scored
IDENTICALLY to v1 (3.3 / 4.2 / ~4.75); only the base wobbled (3.10 v1 -> 3.20 v2, judge noise).

Combining v1 + v2 gives the decisive read:
- **Tone is the reproducible effect** (+0.30 to +0.50 across both runs, above the noise floor) -
  the model reliably learns the house register/voice.
- **Usability is NOT** (+0.10 to +0.20, within the +/-0.3-0.4 noise floor; v2's 3-up-3-down
  per-task split is the signature of noise, not a real effect).
- **Faithfulness preserved** both times (no fabrication cost).
- **A 5x larger, de-skewed corpus did NOT amplify it** - so the bound is not a data-quantity
  problem; it is the ceiling of this lever.

Conclusion: the on-box house-style fine-tune is a VOICE-ADAPTATION lever (teaches the firm's
register, on-prem, privately, no faithfulness cost), NOT a send-readiness / frontier-gap
closer. The box stays a "first-draft engine you finish"; the fine-tune makes the first draft
SOUND right, it does not make it meaningfully more send-ready in aggregate. Decision-grade:
worth it for house-voice consistency, not as a way to eliminate editing. This SUPERSEDES the
optimistic reading of F37 v1 (whose +0.20/+0.50 from 25 skewed examples looked more promising
than the effect proved to be under the proper corpus).
Evidence: results/finetune/{housestyle-ft-v2,base-q8-v2}.json; the v1->v2
progression (corpus fixes: two-call grounded gen, retry, incremental writes);
docs/plans/2026-07-13-house-style-finetune-design.md.

## F38 - local office tool use works on the general workhorse via the standard function-calling API; the tool-call "specialist" is LESS reliable (format leakage), and reasoning inside the call is not

**Kind: MODEL**

The workhorse (Qwen3-30B-A3B-Instruct) drives office tools (create_word_document) reliably
through the standard OpenAI function-calling API on llama-server (`--jinja`): across 8 tasks it
emitted clean structured tool_calls on all 7 that needed one, selected the right tool (including
firing two different tools on a two-tool task), produced real, complete .docx files, and did not
over-call on a no-tool trap. This closes the campaign's untested gap (text generation was measured;
tool-driven document creation was not) with a positive answer: the "Sparky creates a document"
use case is feasible on the workhorse.

Three caveats keep it honest, all consistent with the benchmark-non-transfer through-line:
- **The tool-call "specialist" was WORSE, not better** (deviation from pre-registered P3). Qwen3-Coder-30B
  inconsistently leaked its native `<function=...><parameter=...>` XML syntax as PLAIN TEXT, which the
  OpenAI-compat parser drops - so ~half its calls produced NO document via a standard client. Pick a
  tool-use model by whether its calls PARSE on your stack, not by the "coder/tool" label.
- **Reasoning INSIDE the call is unreliable.** The workhorse missed a conditional ("if balance > EUR 5,000
  mark URGENT"; it was EUR 7,400) - well-formed call, dropped logic. Getting the plumbing right is not
  getting the judgement right.
- **No format-awareness.** Models emit markdown (`**bold**`) into the body, which Word renders as literal
  asterisks; a production integration must strip/convert it or instruct plain-text output.

Decision-grade: local tool use for document creation is real and usable on the workhorse, with the same
human-review discipline as any draft, and with model selection made by measured parse-reliability rather
than by reputation.

**E33 EXTENSIVE UPDATE (4 models x 22 tasks x 5 runs) - two revisions to the pilot:**
- **The pilot OVERSTATED Coder's weakness.** At scale with an explicit system prompt, Qwen3-Coder scored 82%
  with only 5/110 format leaks (not ~50%). It is competitive, just slightly less reliable than the workhorse
  (91%, 0 leaks) and gpt-oss-20b (88%, 0 leaks), with weaker no-tool discipline. The E32 "much worse" verdict
  was single-run + terse-prompt noise - a caution about pilot-scale conclusions, corrected by N=5.
- **The core finding is serving-config sensitivity.** Same build, same --jinja: workhorse + gpt-oss emit clean
  tool_calls instantly; Mistral-Small-3.1 SILENTLY REFUSES (its GGUF ships no tool template - fixed only by
  supplying a Mistral v7-tekken template); Coder emits native XML that partly leaks. "Capable model" != "does
  tool use on your stack." AND: conditional reasoning-in-call is BROKEN for the Qwen family + gpt-oss (they add
  "URGENT" unconditionally) but CORRECT for Mistral - exposed only by testing BOTH branches (the true-branch
  alone falsely passed for everyone). Mistral's multi-tool chaining was template-confounded, not cleanly measured.
Evidence (E33): results/tool-use/E33-{preregistration,results}.md; E33-results-{qwen3-30b,gpt-oss-20b,
qwen3-coder-30b,mistral-24b}.json; harness tools/tooluse_harness_v2.py.
Evidence (E32 pilot): results/tool-use/E32-{preregistration,results}.md; results-qwen3-30b.json,
results-qwen3-coder-30b.json; rendered docs results/tool-use/png/qwen3-30b/; harness tools/tooluse_harness.py.

## F39 - production served 5.3x the KV it needed, because the serving flags had three writers (PARTIALLY RETRACTED: the "tool use was disabled" half was never measured, and is false)

**Kind: METHOD** - one writer for serving flags, and the retraction. The memory
measurement itself is **F131**, split out 2026-09-01.

Status: AMENDED 2026-07-17. The KV half is confirmed and fixed. **The tool-use half is RETRACTED** -
see the retraction below before citing this finding.

**What is true (measured, same box, same model, before -> after):** the production unit omitted `-c`,
so llama-server allocated Qwen3-30B-A3B's full 262144-token trained context (CLAUDE.md's hard rule
names this exact failure).
- `n_ctx`: 262144 -> 49152 (48K x 4 slots; E30's measured interactive envelope, not a guess)
- GTT: 39.91 GiB -> 20.21 GiB = **19.70 GiB reclaimed** (49%), on weights of ~18 GiB - i.e. KV was
  ~22 GiB, over 5x what any measured use needs
- Generation: 88.04 t/s at the production endpoint (no regression; banked references are 72.8 t/s
  sustained / 92.70 fresh). NOTE: measured via the chat-completions API, whereas F15's +/-1.5% band
  is a llama-bench figure - NOT a like-for-like comparison, so this is "no regression evident",
  not "within F15".

**RETRACTION (2026-07-17): "tool use was silently disabled in production" is FALSE.**
The original finding claimed that because the production unit omitted `--jinja` - which
tools/tooluse_harness.py's docstring requires - F38's office-tool capability was unavailable at the
endpoint users reach for the whole period it was reported. That was never tested. `--jinja` DEFAULTS
TO ENABLED in this build (llama.cpp version 200, 067de93: `--jinja, --no-jinja ... (default:
enabled)`), so production had the jinja template path all along.
Direct test, 2026-07-17: the workhorse served WITHOUT `--jinja` on a scratch port returned a clean
structured `tool_calls` for a create_document request - identical behaviour to the `--jinja`
endpoint. Adding the flag explicitly changed nothing functionally; it only made the existing default
explicit. Production could always do tool use, and F38's capability was never unavailable.
How it happened: the harness docstring ("must be served with --jinja") was read as evidence about
the SERVER, when it was a statement about the harness's own invocation. The pre-fix config was never
exercised - only the post-fix one - so the claim was an inference presented as a measurement. The
2026-07-16 proof run (7/7 valid tool calls at the production endpoint) is real but proves only that
tool use works NOW; it never established that it had been broken.

**The mechanism still stands, and is the durable part.** The flags had THREE writers: the tracked
unit template, the deployed unit, and `model_swap.sh`, which sed-rewrote ExecStart with a hardcoded
flag list. That is a genuine latent bug independent of `--jinja`: the next model swap would have
silently reverted `-c` and put production back to 262144, and the blue/green scratch server
health-checked flags the cutover did not use. Fixed by making `tools/gateway/serving.conf` the
single source of truth, read by BOTH systemd (EnvironmentFile) and shell (source); a swap now
rewrites only LLAMA_MODEL and never touches the unit.

**Generalisable lesson (sharpened by the retraction).** A benchmark result is a claim about a CONFIG,
not about a box, so a capability finding should name the serving config it requires and production
should be asserted against it. But the retraction is the better teacher: asserting that a config
difference MATTERS is itself a claim that needs measuring. Comparing two configs means running both -
we ran only the fixed one, and inferred the broken one's behaviour from a docstring. A flag's
presence in a command line is not evidence about its effect; a default can make an explicit flag a
no-op. Test the config you claim is broken, or do not claim it.
Evidence: results/tool-use/results-prod-config-verify.json (proof run at the production endpoint -
proves tool use works now, NOT that it was ever broken); results/tool-use/jinja-default-control.md
(the 2026-07-17 with/without-`--jinja` control that forced the retraction);
tools/gateway/{serving.conf,model_swap.sh,systemd/llama-gateway.service};
docs/plans/2026-07-16-production-serving-config-design.md; F38 (whose capability was never actually
lost); F15 (the noise band, and why the throughput number above is not compared to it).

## F40 - the box can hold two models on call at once (41 GiB, 0.04s switching) - "one model at a time" was a property of our launcher, not the hardware

**Kind: PLATFORM**

Status: confirmed (2026-07-17, E34, measured attended; box never approached the memory edge,
D-state 0 throughout, restored to its exact pre-test state).

The gateway serves one model because `serving.conf` names one, not because llama.cpp can only hold
one. This build (v200, 067de93) has a **router mode**: launch `llama-server` with no model and it
loads models on demand from a preset and routes each request by the `"model"` field in the body.

Measured at production context (c = 49152, 4 slots), both models resident simultaneously:

| State | GTT | D-state |
|---|---|---|
| router idle | 0.02 GiB | 0 |
| workhorse loaded on demand | 20.21 GiB | 0 |
| **+ Mistral-24B-Q4, both resident** | **41.04 GiB** | 0 |
| switch back to workhorse | 41.04 GiB, **0.04s** | 0 |

The workhorse's 20.21 GiB matches the production gateway exactly - an independent check that router
mode allocates normally. **2 models is the safe cap**: 41.04 GiB leaves ~19 GiB under the ~60 GiB
deadlock edge (F24); a third at ~20 GiB lands ON it. `--models-max` defaults to 4 - unsafe here.

**Per-model presets close a real gap in F39's design.** `serving.conf` carries ONE global flags line,
but models need different flags: a Mistral swap would silently lose tool use, because Mistral needs a
chat-template the workhorse does not. A preset carries `chat-template-file` per model, and Mistral
then does tool calls and still chats. Three sub-results, all measured:
- **E33/F38 independently reproduced:** Mistral-Small-3.1 on its own template REFUSES tool calls with
  E33's exact refusal string, reached by a completely different serving path.
- **The BUILT-IN `mistral-v7-tekken` template is a trap for this model:** setting it produced
  pretraining/forum-post garbage - F37's chat-template fingerprint from the opposite cause (F37 had a
  MISSING template; this is a WRONG one overriding a working one). A plausible name in the built-in
  list is not a fit for your GGUF. E33's hand-written mistral-v7-tool.jinja is the one that works.
- **Safety property, not convenience: use `--models-preset`, never `--models-dir`,** while
  /opt/models/staging holds 100 GB+ artefacts. `--models-dir` + autoload (default on) + models-max 4
  could load a 397B straight through the memory edge. A preset names exactly what is allowed.

**What it changes:** the routing recommendation (reports/2026-07-16-local-model-routing-guide.md) says
swap per SESSION, not per task, because a swap costs more than the quality gain on a short job. The
router removes that premise - with both resident, picking a model per request costs 0.04s and one JSON
field, which makes task-shaped routing viable. NOT adopted yet: llama.cpp labels router mode
EXPERIMENTAL ("not recommended in untrusted environments"), and concurrent inference against both
models, sustained residency, and unload/TTL behaviour under models-max pressure are all untested.
That gap between "measured working" and "serving production" is the honest state.
Evidence: results/router-multimodel.md (full method, tables, caveats); F24 /
docs/memory-edge-deadlock.md (the cap that sets models-max 2); F38/E33 (reproduced); F37 (the garbage
fingerprint); F39 (the single-source-of-truth config this would extend).

## F41 - the box is memory-BANDWIDTH bound, so concurrency redistributes a fixed budget rather than adding one - and the split is 4.6:1 AGAINST the fast model: running a dense model alongside the MoE guts the MoE

**Kind: PLATFORM**

Status: confirmed (2026-07-17, E35, pre-registered deef627 BEFORE the runs; attended, D-state 0
throughout, box restored to its exact pre-test state). Resolves the three items F40 left untested.

**The physical result.** Both models are memory-bandwidth bound, not compute bound: Qwen3-30B-A3B
activates ~3B params/token (~1.7 GB read at Q4) for 91.37 t/s (~156 GB/s); dense Mistral-24B reads
~13.4 GB/token for 15.24 t/s (~201 GB/s). Two very different models landing near the same GB/s is a
shared-bus ceiling. Pre-registered prediction: run both at once and the normalised throughputs must
divide one budget, `(w_con/w_solo) + (m_con/m_solo) ≈ 1.0`. Measured **1.05** - HIT.
**You do not get two models' work for one box's price; you get one box's work, split.**

**The split is brutally unfair, and that was NOT predicted (C4 MISS).** The prediction said both would
degrade about equally (~2x latency each). Instead:

| | Solo | Concurrent (in-overlap) | Retained |
|---|---|---|---|
| Qwen3-30B-A3B (MoE) | 91.37 t/s | 17.28 t/s | **18.9%** |
| Mistral-24B-Q4 (dense) | 15.24 t/s | 13.13 t/s | **86.1%** |

The MoE loses 81%, the dense model 14% - a 4.6:1 asymmetry that falls straight out of the bandwidth
model: Mistral's ~13.4 GB/token demand dominates the bus, and the workhorse's ENTIRE advantage is
bandwidth efficiency, so contention destroys precisely the thing that makes it fast while barely
inconveniencing the model that was already bandwidth-hungry. Contended, the workhorse (17.28 t/s) is
slower than Mistral running alone. **Never serve the MoE and a dense model concurrently on purpose.**
This also re-explains F34's "Mistral is 5-8x slower" as a bandwidth ratio - the same arithmetic
predicts both the solo speeds and the contended split.

**Load/unload is safe and clean** (the rest of E35, all HIT): `--models-max 2` EVICTS BEFORE LOADING -
GTT sampled every 50ms across a third model's load peaked at exactly the existing 2-model level
(32.71 GiB), never holding three. That makes the cap a real memory guard against the ~60 GiB edge
(F24), not a hint. Eviction is LRU; `POST /models/unload` returns memory to the system (0.02 GiB);
an unloaded model reloads on demand in 3.3s; 20 alternating switches held 41.05 GiB with **0.000 GiB
drift** and no silent reloads (workhorse median 42ms, Mistral 535ms).

**Methodology - the artifact that nearly produced a false MISS.** The first concurrency measurement
gave a normalised sum of **1.37** ("prediction MISS, real headroom exists, bandwidth story wrong").
It was a partial-overlap artifact: the jobs were sized 600 and 100 tokens, so Mistral finished at 7.7s
while the workhorse ran to 13.0s and spent its last 5.3s running ALONE at full speed - a solo tail
averaged into a "concurrent" rate, with only 59% overlap. Recording a timestamp per streamed token and
computing rates strictly inside the mutual overlap window gave 1.05. **A throughput number measured
over a window that includes non-contended time is not a contention measurement.** Same family as F34's
judge-truncation artifact and this week's `--jinja` retraction: the ruler was wrong, not the data.
Recorded because the easy write-up was "we predicted 1.0 and measured 1.37, so we were wrong", and
that false MISS would have argued for adopting concurrency on headroom that does not exist.

**Operational verdict:** the router is a fast SWITCH (0.04s), not a concurrency engine - which suits a
single-operator box, where one model is in use at a time anyway. Preset-only + `--models-max 2` is
defensible on memory safety (A1). Residency is free (flat, fully reclaimable), so keeping both loaded
for switching costs nothing. Concurrent serving of dissimilar architectures is the thing to avoid.
Evidence: results/router-loadtest.md (all 12 predictions resolved) + results/router-loadtest-prereg.md
(registered first); F40 (the residency baseline); F24 (the edge); F34 (the dense/MoE ratio this
explains); F17 (single-model concurrency knee - untouched, still the open question).

## F42 - the router is FREE for single-model concurrency (within 0.7% of direct at every slot count, F17's 2.66x preserved); its cost is TAIL latency, not throughput

**Kind: PLATFORM**

Status: confirmed (2026-07-17, E36, pre-registered a8d2df8 BEFORE the runs; attended, D-state 0,
box restored exactly). Closes the last item F40/F41 left open.

Both arms measured in the SAME session on the SAME build with ONE driver - F17's banked numbers were
deliberately not used as the baseline, because they predate this build and comparing across builds
would confound router effect with build change (the error behind this week's `--jinja` retraction).

| Slots | DIRECT agg t/s | ROUTER agg t/s | router/direct |
|---|---|---|---|
| 1 | 72.78 | 72.81 | 1.000 |
| 4 | 138.93 | 139.27 | 1.002 |
| 16 | 192.19 | 193.54 | 1.007 |
| scaling 1->16 | 2.64x | 2.66x | |

The proxy hop costs nothing measurable in throughput at any concurrency tested, and F17's MoE scaling
(2.66x, no sharp knee) reproduces exactly on the current build - **F17 stands.**

**Where the router is NOT free: the TTFT tail.** p50 is untouched (1 slot +1.0ms; 16 slots +6%), but
p95 at 16 slots is **+46%** (1754.7 -> 2554.8 ms). Direct serving holds a remarkably tight
distribution at 16 slots (p50 1721.8 -> p95 1754.7, a 2% spread); the router's spread is 40%. The
proxy adds jitter under load, not a constant cost. Invisible to a single operator; material for a
latency-sensitive multi-client service.

**Migration caveat:** native `/completion` REQUIRES a `"model"` field under the router and returns
400 Bad Request without one; a direct llama-server needs no such field. Existing native-endpoint
clients break on migration. `/v1/chat/completions` callers already send `model` and are unaffected.
Evidence: results/router-concurrency.md; results/router-concurrency-prereg.md; control run via
tools/serve_bench.py (F17's own harness) = 191.76 t/s @16; F17; F40; F41.

## F43 - MoE concurrency is STREAM-DIVERSITY-bound: 16 streams asking DIFFERENT questions run 40% slower than 16 asking the SAME one, a dense model shows no such penalty (-0.1%), and F17's headline therefore overstates real fleet throughput by 1.78x

**Kind: PLATFORM**

Status: **confirmed + MECHANISM ESTABLISHED** (2026-07-17, E37, pre-registered a02f09b BEFORE the
runs; dense control decisive). **This supersedes F43's original "output diversity" framing, which was
confounded** - see the correction below. Attended, D-state 0, box restored exactly.

All prompts padded to the same 144-word class; `predicted_n` verified at exactly 128 (min = max) in
every arm - so neither prompt length nor early-EOS explains anything below.

**MoE workhorse, 16 slots, length-matched:**

| Prompt class | Streams | agg t/s | per-stream |
|---|---|---|---|
| fox filler (repetitive) | identical | 191.70 | 14.54 |
| legal prose | identical | 181.28 | 13.64 |
| legal prose | **DISTINCT (16 topics)** | **108.86** | **7.79** |

**Content costs ~5%. Stream diversity costs 40%.** The only change in the last row is that sixteen
streams ask sixteen DIFFERENT questions.

**The honest user curve** (same driver, same window as the published one):

| Concurrent users | SAME question (published) | DIFFERENT questions (real) |
|---|---|---|
| 1 | 72.78 | 71.59 |
| 4 | 138.93 | **121.35** |
| 16 | 192.19 | **109.40** |
| scaling 1->16 | 2.66x | **1.53x** |

**Sixteen real users is SLOWER than four** - the real-load curve PEAKS at ~4 and declines, where F17
recorded "no sharp knee, still rising". The 4-user point reproduced twice (121.35 / 121.09, 0.2%
apart), so the knee is not noise. Client-facing consequence: the box's best serving point is about
FOUR concurrent users - exactly the "small team of 3-5" the report claims, but that conclusion was
previously EXTRAPOLATED from same-question data that happened to keep rising, and the number attached
to it (2.66x) was wrong for the scenario it described. Claims corrected:
C-CONCURRENCY-MOE-SCALING 2.66 -> **1.53** (unit now names distinct users), C-CONCURRENCY-SMALL-TEAM-P1
rewritten around the measured peak, and the published concurrency chart now ships BOTH curves so the
same-question line cannot be read as fleet capacity.

**The dense control identifies the mechanism** (4 slots, length matched):

| Model | identical streams | DISTINCT streams | penalty |
|---|---|---|---|
| MoE Qwen3-30B-A3B | 43.91 t/s/stream | 38.77 | **-11.7%** |
| DENSE Mistral-24B | 10.04 t/s/stream | 10.03 | **-0.1%** |

A dense model reads ALL weights every token, so batch composition cannot change its memory traffic -
and it does not, to within 0.1%. The MoE routes per token, so a batch of divergent streams must fetch
many experts per step, on a box where bandwidth is the binding constraint (F41). **The penalty exists
only where expert routing exists.** It also SCALES with batch size (-11.7% at 4 slots, -43% at 16),
which is what expert-sharing predicts and further supports it.

**WHAT THIS CORRECTS - F17's headline is a same-question artifact.** F17 reports 193.5 t/s aggregate
at 16 slots and frames it, in its own words, as "what the fleet gets at burst". Every stream in that
benchmark ran the SAME repetitive prompt. Sixteen real users asking sixteen different questions
measure **108.86 t/s** on the same box, build and slot count:

> **F17 headline 193.5 t/s | real fleet load 108.86 t/s | overstatement 1.78x**

F17 is not fabricated - its conditions are stated and it reproduces exactly (E36: 192.19 under those
conditions). It is a best case that READS as a fleet number. The single user is unaffected: at 1 slot
there is no penalty at all (89.02 vs 89.94 across prompts). **This is a finding about fleets, not
people** - and it does not change any single-operator recommendation.

**F43's own original framing was wrong and is superseded.** It claimed "MoE throughput depends on
OUTPUT DIVERSITY", inferred from a 26% gap between two prompts (192.19 vs 152.12). That comparison was
confounded: the prompts differed in LENGTH (144 vs 45 words) as well as content. With length
controlled, content is worth ~5%; the real effect is whether the concurrent requests differ FROM EACH
OTHER, not whether any one of them is interesting. Narrower claim, better evidence, bigger consequence.

**The generalisable trap:** every concurrency benchmark that fires ONE prompt from N threads measures
best-case expert-cache locality for a MoE and does not know it. `serve_bench.py` does what standard
practice does, and F17's method section is accurate about it - the practice is simply correct for
dense architectures and wrong for MoE. **For MoE, concurrency benchmarks must use DISTINCT prompts per
stream or they measure expert locality rather than serving capacity.**

Prediction resolution: A1 (dense shows no effect) HIT at 1.001. B1 (identical reproduces E36) HIT at
191.70. B2 (diverse <= 170) HIT far beyond at 108.86. **A2 (MoE ratio >= 1.15 at the same slot count)
MARGINAL MISS at 1.133** - the prediction assumed a fixed effect size; the penalty in fact scales with
batch size (1.75x at 16 slots), so the prediction was wrong about the SHAPE. Recorded as a miss rather
than re-baselined to the slot count that would have hit.

Limits: one MoE family, one dense comparator, 4 and 16 slots, one diversity condition. Untested:
intermediate diversity; other MoE families (F17/F18 show concurrency behaviour already varies by
architecture, so this may too); interaction with F18's MLA anti-scaling; >16 slots.
Evidence: results/moe-diversity.md; results/moe-diversity-prereg.md (registered first);
results/router-concurrency.md (E36, where the signal appeared); F17 (the number corrected); F41 (the
bandwidth ceiling); F18 (architecture-dependent concurrency).

## F44 - Whisper fabricates "Thank you." from PURE DIGITAL SILENCE at ~2/min, and by HARM the BIGGER model is 4.9x worse than the small one (the small one says "[BLANK_AUDIO]"; large says a sentence)

**Kind: MODEL**

Status: **confirmed** (2026-07-17, E41, pre-registered 5c7a64d BEFORE any run; 72 conditions x 3
runs). **The core phenomenon is NOT NOVEL - it is well-established prior art.** See "Prior art and
what is actually ours" below; this is a REPRODUCTION plus one reframing, and it must never be
published as a discovery.

**Why it earns an F-number anyway:** transcription has been a published capability of this box since
Phase A (28x real time, C-CAPABILITY-TRANSCRIPTION-001), it is the INPUT to the whole diarisation
stack, and **we shipped it for months without ever checking what it does with silence.** A wrong
speaker label is visible to a reader; invented speech is not.

### The measurement

whisper.cpp large-v3-turbo, no VAD, on synthetic fixtures with EXACT ground truth (we generate the
silence, so we know which regions contain no speech):

| Condition swept | Result |
|---|---|
| **Duration** | the ONLY factor: **~2.0 fabrications per minute**, near-constant from 5s to 300s |
| **Position** (silence-only / leading / trailing / sandwiched) | flat: 55 / 51 / 48 / 54 |
| **Silence type** (digital-zero / noise -60dB / roomtone -45dB) | flat: 72 / 69 / 67 |
| **Text** | **THREE distinct strings across 208 fabrications; 202 (97%) are `Thank you.`** |
| **VAD on** | **0 fabrications across all 72 conditions** |

**Pure digital zero hallucinates.** A file containing nothing but zeros - no dither, no signal at
all - yields `Thank you.` at ~2/min. There is nothing to misinterpret; the model is transcribing its
own prior. This REFUTED our pre-registered S1 ("the trigger is context, not silence").

Three prediction refutations recorded: S1 (context), S2 (position), S4 (noise > zero). Four hits:
S3 (duration), S5 (small recurring string set), S6 (VAD -> zero), S7 (small > large by count).

### The reframing - this is the part worth having

S7 hit by count and INVERTED by harm. Our own metric counted volume, not damage:

| model | total | **annotations** (self-declared non-speech) | **DANGEROUS** (plausible speech) |
|---|---|---|---|
| **large-v3-turbo** | 208 | 4 | **204** (202x `Thank you.`) |
| **small** | 298 | **256** (`[BLANK_AUDIO]`, `[ Silence ]`, `[no audio]`) | **42** |
| large + VAD | **0** | 0 | **0** |

`small` emits MORE segments but 85% are the model TELLING YOU there is no speech - self-labelling,
trivially filtered, obvious to a human. `large-v3-turbo` emits grammatical English indistinguishable
from a real utterance.

> **large-v3-turbo produces 4.9x MORE DANGEROUS fabrications than small (204 vs 42).**
> The published guidance is "larger models hallucinate less", and by COUNT our data agrees
> (208 < 298). By HARM it reverses. A stronger language prior buys more convincing fiction.

### Prior art and what is actually ours

**The phenomenon, the mechanism, and the mitigation are all published. We discovered nothing here.**

- **Koenecke et al., "Careless Whisper: Speech-to-Text Hallucination Harms", FAccT 2024** - the
  canonical work; Whisper inserting phrases during silence, with documented harms in medical
  transcription. ~1.4% of transcriptions affected.
- **"Calm-Whisper: Reduce Whisper Hallucination On Non-Speech", Interspeech 2025 (arXiv 2505.12969)**
  - an entire paper on this failure mode; localises it to **3 of 20 decoder heads** and fixes it by
  fine-tuning on non-speech paired with blank labels (>80% reduction).
- **"Investigation of Whisper ASR Hallucinations Induced by Non-Speech Audio"** - as titled.
- **arXiv 2606.07473** - detection/mitigation via hidden-representation steering + SAEs.
- The **YouTube-prior mechanism** we "hypothesised" in the pre-registration is the published
  explanation (weakly-supervised web audio; non-speech paired with arbitrary caption text).
- `Thank you` on a silent file, and VAD as the standard mitigation, are widely reported in the
  community.

**What is plausibly ours** (narrow, and NOT exhaustively checked - three searches cannot prove a
negative):

1. **The harm-weighted model-size inversion.** The literature counts hallucinations; we found that
   counting them hides the safety-relevant fact, because `small`'s output is 85% self-declaring
   annotations. We did not find this framing in the work above. Calm-Whisper measures non-speech
   (UrbanSound noises) by volume, not silence by harm.
2. **The rate constant on PURE digital silence** (~2/min, invariant to position and silence type) on
   a named, reproducible local stack.
3. Independent on-prem reproduction with an exact published protocol (tools/silence_bench.py, no
   personal data).

**Publication rule for this finding: report it as a reproduction that corroborates the literature,
plus one reframing that changes the mitigation advice. Never as a discovery.** A reader who knows
the FAccT paper would spot a novelty claim instantly, and that impression costs more than the
finding is worth.

### Consequence

Any Whisper pipeline WITHOUT VAD silently inserts ~2 fabricated utterances per minute of silence. A
1h recording with 10 min of dead air (joining early, a break, someone muted) gets **~20 invented
"Thank you" lines**, attributed by the diariser to a named person, with nothing marking them as
fabricated. `tools/diarise.py` now RAISES if the VAD model is absent rather than degrading quietly.

Alastair independently reports the same artifact from hosted frontier transcription services
(2026-07-17) - consistent with a family trait, but **NOT tested here**: hosted decoding parameters
(temperature fallback, `no_speech_threshold`, `condition_on_previous_text`) differ and are not
visible to us. Registered as open.

### Limits

One implementation (whisper.cpp), two model sizes, English, synthetic silence, whisper.cpp default
decoding params (not swept). Not tested: music, hold tone, crosstalk, background speech - the same
out-of-distribution class and the meeting-realistic ones. Not tested: hosted APIs, which is what
would turn Alastair's observation into a measured cross-vendor claim.

Evidence: results/transcription/e41-silence-hallucination.md; pre-registration
results/diarisation/e41-silence-hallucination-prereg.md (committed 5c7a64d BEFORE any run);
tools/silence_bench.py; results/transcription/silence-{large-novad,large-vad,small-novad}.json;
results/diarisation/e40-vad-and-limits.md (the incidental discovery this systematises).

## F45 - on real speech the LARGER whisper model is more accurate (2.40% vs 3.35% WER), refuting our own "smaller is better" hypothesis - and a batching bug had INVERTED the answer until a public benchmark's known value caught it

**Kind: MODEL** - the accuracy result. How the inverted answer was caught is
**F132**, split out 2026-09-01.

Status: **confirmed** (2026-07-17, E42 + E45). This refutes a hypothesis we registered.

### The measurement

whisper.cpp large-v3-turbo vs small, true Word Error Rate on LibriSpeech test-clean (the standard
benchmark: real human transcripts, 200 utterances, 4542 reference words):

| model | **WER** | sub | del | ins |
|---|---|---|---|---|
| **large-v3-turbo** | **2.40%** | 88 | 10 | 11 |
| small | 3.35% | 130 | 14 | 8 |

**2.40% matches the published figure for whisper large-v3 on test-clean (~2-3%)**, which validates
the harness as well as the number. On real meeting audio the same ordering holds (E42, vs an Otter
reference with a ~2% floor): large 10.7% disagreement, small 13.7% - large ~28% better in both
settings.

> The hypothesis "smaller whisper models may be better quality for transcription" (registered from
> the F44 silence result) is **REFUTED** - on read speech and on meeting speech, against human
> ground truth. F44's small-model advantage is specific to the SILENCE failure mode (self-labelling
> `[BLANK_AUDIO]` vs fabricating speech); it does not generalise to accuracy on actual speech.

### The harness bug the public benchmark caught

The first version batched 10 utterances into one wav to amortise startup. It reported **large 16.23%,
small 13.03% - "small is better", confirming the hypothesis under test.** The bug did not add noise;
it INVERTED the answer, because whisper dropped audio from the concatenated files (511 deletions vs
55 insertions - mass omission). What exposed it: 16.23% is impossibly far from LibriSpeech's known
~2-3%. Run on our own meeting corpus, where no expected value exists, the broken harness would have
produced a plausible number confirming the hypothesis, and it would have shipped. **A public
benchmark with a known value is not just data - it is an instrument check.**

### Scope

LibriSpeech is clean, single-speaker read audiobook speech - the EASY case. **2.40% must never be
quoted as our meeting transcription accuracy** (that figure is unknown; the ~10.6% E42 disagreement
carries the reference's own floor). What this establishes is the model COMPARISON and a sound harness.
Not swept: medium / large-v2 / non-turbo large-v3, decoding parameters, other languages.

Evidence: results/transcription/e45-true-wer.md; results/transcription/e42-wer-model-size.md;
tools/librispeech_wer.py; manifests/MANIFEST.md. Corpus: LibriSpeech (CC-BY-4.0, attribution required).

## F46 - full speaker diarisation is genuinely hard (pyannote beats us 3x), but REFRAMING to "is it the host or someone else" hits 97.2% and is the abstraction the product actually needs

**Kind: MODEL**

Status: **confirmed** (2026-07-17, E43-E50). Two honest halves: we are NOT best-in-class at general
diarisation, and we do not need to be.

### Half one - general diarisation, measured against real ground truth and a strong baseline

On AMI (the standard meeting-diarisation corpus, real human labels), Diarisation Error Rate on 6
held-out meetings:

| system | IHM (headset) | SDM (one table mic) |
|---|---|---|
| ours, energy-gate VAD (E43) | 29.2% | 33.1% |
| ours, Silero VAD (E44) | 20.2% | 21.1% |
| ours + pyannote VAD (hybrid, E47) | **10.5%** | 16.9% |
| **pyannote 3.1 full pipeline (E46)** | **6.5%** | **13.8%** |

Three things worth keeping: (a) replacing a naive energy gate with a real VAD nearly halved our error
(E44); (b) **a far-field table mic is almost free - SDM 21.1% vs IHM headset 20.2%, ~1 point, against
a predicted 8+** (E44), so an on-prem meeting box does not need per-person headsets; (c) pyannote's
own published pipeline still beats ours ~3x on close-talk (E46). We report that plainly - our general
diarisation is decent, not state-of-the-art.

### Half two - the reframe that makes it a product

The host's real need is not "count and separate every speaker". It is "when am I speaking vs when is
someone else". That is a BINARY target-speaker problem: enroll ONE voiceprint (the host), score each
window against it, threshold. No clustering, no speaker count - the entire auto-k failure mode that
blocks general diarisation on real meetings (E49: k defaults to 2, explodes to 8 on a webinar) simply
disappears.

Measured on 4 real calls, voiceprint enrolled on a SEPARATE 4-minute recording (genuine
cross-session):

- **Segment-level (the product metric): 97.2%** of transcript lines correctly tagged host vs other
  (per-recording 96.0-97.7%). Frame-level 92.5%. Separation host 0.645 vs other 0.131.
- **The difficulty curve INVERTS.** Full diarisation gets harder with more speakers; target-speaker
  gets EASIER - the webinar (worst diarisation case) has the BEST separation (+0.601), because more
  "others" just means more clearly-not-the-host audio.

Honest limits: 4 recordings, one target speaker, Otter-derived labels (~98%); one call is weaker at
the frame level (83%, quiet/overlapped speech) but recovers to 97.2% at the segment level; overlap
(host + other at once) is flagged, not resolved. The binary tag is not a limitation for the use case -
separating the host's positions from the other parties' needs/commitments is exactly what commitment
extraction consumes; distinguishing among the others is unnecessary.

Evidence: results/diarisation/e43-ami-real-ground-truth.md; e44-vad-fix.md; e46-pyannote-headtohead.md;
e47-hybrid-vad-swap.md; e48-real-online-calls.md; e49-batch-14-real-meetings.md; e50-target-speaker.md;
tools/target_speaker.py.

## F47 - on gfx1151/ROCm, TTS engine ARCHITECTURE (not "AMD is slow") decides throughput: a 200x realtime-factor spread on ONE GPU, and the "systemic MIOpen vocoder wall" was one engine's decoder, not the box

**Kind: PLATFORM**

W3 Stage 1 ran three TTS engines on sparkmax (gfx1151 / Radeon 8060S RDNA3.5, ROCm 7.2.4) and the
end-to-end realtime factors span **200x on the same GPU**: Kokoro-82M ~8x (faster than realtime),
F5-TTS 0.60x, Fish s2-pro 0.044x (~25x slower than realtime). The spread is architectural, not a
vendor property:

- **Kokoro** is a small ONNX model on CPU (onnxruntime) - fastest, cheapest, and it adds ZERO GPU
  memory pressure, so it coexists with a resident 30B LLM for free (whole cost = 1.46 GiB host RSS).
- **Fish s2-pro** is autoregressive (an LLM emitting semantic tokens) + a conv-heavy DAC vocoder.
  Measured decomposition on a 43-word clip: LLM stage ~35s, full request ~308s - **~270s in the
  decoder**. The container logs flood with `MIOpen(HIP) ... Solver <GemmFwdRest> ... workspace
  required: N, provided ptr: 0 size: 0`: the conv-heavy vocoder falls into MIOpen's no-workspace
  fallback. `torch.compile` (COMPILE=1) gives a ~9x speedup on the LLM stage but leaves end-to-end
  RTF unchanged at 0.044x, because a different stage is the bottleneck (BOTH configs measured, per
  HARNESS-RULES Rule 8 - the config difference is real for one stage and a near-no-op for the whole).
- **F5-TTS** is a DiT flow-matching model (fixed 32 steps) + vocos vocoder, at 0.60x - ~14x faster
  than Fish end-to-end.

The load-bearing point: an earlier hypothesis ("every neural-vocoder TTS on this box hits the MIOpen
conv wall") was DISPROVEN by F5 - a neural vocoder that ran fine. The bottleneck is Fish's SPECIFIC
DAC-decoder MIOpen path, not neural vocoders universally. Consulting takeaway for on-prem AMD
inference: benchmark the ENGINE's architecture, not the accelerator's brand - flow-matching /
efficient-vocoder designs are far cheaper here than autoregressive-LLM-plus-conv-vocoder designs, and
"the AMD card is slow" is usually a mis-attribution of a decoder/kernel-path cost.

Evidence: reports/2026-07-25-tts-stage1.md; tts-bench/results/{kokoro,fish-s2-pro,f5-tts}/metrics.json;
tts-bench/results/fish-s2-pro/THROUGHPUT-ANALYSIS.md (the COMPILE 0-vs-1 A/B + decoder decomposition).

**AMENDMENT (2026-07-25, W3 T10): Fish's decoder cost is NOT MIOpen-tunable - the workspace is
withheld by the CALLER, so autotuning selects among solvers it is already forbidden to use.**
Stage 1 recorded "plausibly tunable" as an open lead. The T10 gate cleared one bounded attempt; it
ran and returned **nothing**: proc_rtf 22.534x tuned vs 22.493x baseline (**-0.18%**, marginally
slower), inside one sd of this engine's own nine-excerpt band (mean 22.896x, sd 0.400). The LLM
stage was untouched as predicted (8.14-8.50 tok/s tuned vs 8.49x baseline), isolating the decoder
as the only variable - and it did not move.

The null is informative because MIOpen tuned *correctly* and was overruled anyway. With
`MIOPEN_FIND_MODE=NORMAL` + `MIOPEN_FIND_ENFORCE=4` it ran the exhaustive search and persisted a
populated user find-db quantifying the fallback penalty: `GemmBwdRest` 0.108ms **with a 102KB
workspace** vs `ConvDirectNaiveConvBwd` 7.08ms without one - **~65x**. Yet the rejections still
fire: 12 distinct conv shapes needing **8.6MB to 886MB** of scratch, every one handed
`provided ptr: 0 size: 0`. Find-mode governs which solver MIOpen PICKS among those it may run; it
cannot grant a workspace the caller declined to allocate. The bottleneck therefore relocates from
"MIOpen is untuned" (a config problem, cheap) to "the PyTorch-to-MIOpen workspace contract on this
decoder path" (a code problem, unreachable from the environment).

Consulting form, and the transferable lesson: on ROCm, `provided ptr: 0 size: 0` in an
`IsEnoughWorkspace` warning is a CALLER-side signal. Autotuning env vars are the wrong tool for it,
and time spent on them buys nothing - check who owns the workspace allocation before tuning the
library. Tuning budget spent; remaining levers (PyTorch-side workspace provision via
cudnn.benchmark / NHWC, hipBLASLt) are code changes recorded but not chased.
Evidence: tts-bench/results/fish-s2-pro/MIOPEN-TUNING-AB.md + miopen-ab.json + tuned-log-evidence.txt
+ miopen-user-finddb.txt; config fish-speech-tts/serve_fish.sh, harness fish-speech-tts/miopen_ab.py.

## F48 - vLLM does not run on gfx1151 (Strix Halo APU): every prebuilt image is MI300/CDNA on ROCm 6.x, and a source build STRIPS the gfx1xxx kernels - so TTS engines that assume vLLM serving must use native PyTorch routes on this box

**Kind: PLATFORM**

W3 T8 was meant to stand up "vLLM-Omni" once and amortise it across Qwen3-TTS, VoxCPM2 and
CosyVoice3. Real-data-first at task time killed both halves of that premise:

1. **There is no shared route.** The three engines use three DIFFERENT vLLM-family stacks: Qwen3-TTS
   → vLLM-Omni, VoxCPM2 → Nano-vLLM (`nanovllm-voxcpm`), CosyVoice3 → standard vLLM 0.11.x+. Nothing
   to amortise.
2. **No vLLM variant runs on gfx1151 without a doomed source build.** Every prebuilt `rocm/vllm`
   image targets MI300 / Instinct (CDNA, gfx942) on ROCm 6.x - and ROCm 6.x throws `HIP error:
   invalid device function` on gfx1151 (gfx1150/1151/1201 are not in the ROCm 6.x compatibility
   matrix; they need 7.x). vLLM's own `docker/Dockerfile.rocm_base` lists gfx1151 in
   `PYTORCH_ROCM_ARCH` (torch builds) but then builds vLLM's custom kernels with
   `GPU_ARCHS=$(... sed 's/;gfx1[0-9]{3}//g')` - i.e. it strips EVERY gfx1xxx arch; AITER is
   gfx942/gfx950 only. So a from-source build produces no gfx1151 kernels.

Consequence for on-prem AMD APU serving: vLLM's throughput path is a CDNA-datacenter feature, not an
RDNA-APU one (yet). Engines are served on gfx1151 via the "container FROM `rocm/pytorch:rocm7.2.3` +
native PyTorch inference" path instead - PROVEN in the same session (Fish and F5 both served that
way). vLLM serving only becomes relevant once an engine is selected AND needs production throughput,
and even then only if AMD ships gfx1151 vLLM kernels.

Evidence: tts-bench/results/vllm-omni/BLOCKED-STATE.md; reports/2026-07-25-tts-stage1.md.

## F49 - TTS throughput on this box is set by TWO compounding multipliers - autoregression (~150 sequential passes) x model size - and together they cost ~3000x, which a ~35x GPU advantage cannot recover: an 82M non-AR model on CPU beats every GPU engine by ~88x

**Kind: PLATFORM**

W3 Stage 1 + Stage 2 (2026-07-25/26) measured six TTS engines on sparkmax (gfx1151, ROCm 7.2.4)
against one 26-word line and a 9-excerpt corpus. The ordering is not about the accelerator:

| Engine | Params | Architecture | RTF |
|---|---|---|---|
| **Kokoro-82M (CPU, ONNX)** | 82M | **non-AR, ONE forward pass** | **~8-9x** |
| F5-TTS | ~336M | non-AR flow-matching, FIXED 32 steps | 0.60x |
| Chatterbox (std, exagg 0.7) | ~0.5B+ | AR LM + vocoder | 0.185x |
| VoxCPM2 | ~0.5B | AR | 0.140x |
| Qwen3-TTS-1.7B-CustomVoice | 1.7B | AR multi-codebook LM | 0.102x |
| Fish s2-pro | 4B | Dual-AR + DAC vocoder | 0.044x |

**The mechanism, and the arithmetic closes.** Two independent multipliers compound:
1. **Autoregression.** Kokoro emits a whole utterance in ONE pass. An AR model emits one frame at a
   time: ~7s of audio at ~20 frames/s is **~150 SEQUENTIAL, dependent passes** that cannot be
   parallelised away for a single utterance.
2. **Size.** 82M vs 1.7B is ~20x more bytes read PER pass.

Qwen-vs-Kokoro work ratio ~ 150 x 20 = **~3000x**. Observed speed ratio 9/0.102 = **~88x**. Implied
GPU advantage 3000/88 = **~35x** - a plausible figure for this APU over CPU on this workload. So the
model is self-consistent: architecture+size cost ~3000x, the GPU returns ~35x, the small non-AR model
still wins by ~88x. (Order-of-magnitude estimate, not a measured decomposition.)

**The GPU is not underperforming - it is handed the worst possible workload:** thousands of tiny
SEQUENTIAL DEPENDENT ops at batch 1, where its width has nothing to chew on. This also explains F47's
"architecture decides" one level deeper, and why the T10 MIOpen tuning was a null (F47 amendment):
the constraint is the shape of the computation, not kernel selection.

**Consulting form:** on-prem TTS throughput is predicted by (is it autoregressive?) x (how big?),
NOT by the accelerator's brand or TFLOPS. A small non-autoregressive model on CPU is a legitimate
production answer and costs no GPU at all.

**Levers this implies (untested, ranked - next session starts here):**
1. **BATCHING.** At batch=1 an AR model wastes essentially all the GPU's width. Batching posts or
   sentences should scale near-linearly on the SAME hardware. Qwen exposes batch inference natively.
   Biggest lever, zero new engines. May also explain Qwen's unexplained bimodal RTF (14/18 renders at
   0.1019, 4/18 at 0.2469 - the fast arm looks like a batched path).
2. **Non-AR architectures.** F5 at 0.60x is 6x the best AR engine purely because 32 fixed steps beat
   ~150 sequential ones. A different cost class, not a tuning delta.
3. Smaller variants (Qwen ships 0.6B vs the 1.7B tested). 4. Quantisation (all ran bf16).

**The reframed search question:** quality tracks size+autoregression; speed tracks smallness+non-AR.
Kokoro proves small+non-AR is fast and FAILS quality (owner, 2026-07-26 - af_heart, bf_emma and
bm_george all rejected by ear). F5 proves non-AR can be fast AND the quality yardstick, but is
cc-by-nc and cannot ship. So the precise open question is: **does a COMMERCIALLY-LICENSED
NON-AUTOREGRESSIVE engine exist in F5's quality band?** F5's existence proves the combination is
achievable.

Evidence: tts-bench/results/{kokoro,fish-s2-pro,f5-tts,qwen3-tts}/metrics.json;
tts-bench/results/qwen3-tts/RESULTS.md; docs/W3-STAGE2-SWEEP.md (per-engine spike records).

## F50 - Fish s2-pro emits a REPRODUCIBLE 47-second, -48 dB non-speech render on a valid English sentence, returning HTTP 200 and a well-formed WAV - a silent-failure mode that disqualifies it for unattended batch work

**Kind: MODEL**

Rendering a 26-word English line through Fish s2-pro (default voice, no reference) produced, on
**3 renders out of 3**, byte-identical degenerate output: **47.508027s duration, mean -48.5 dB, peak
-31.1 dB** (control: Chatterbox on the same line, mean -17.6 dB, peak -0.1 dB). Deterministic despite
`seed=None` and `temperature=0.8`, so the model collapses immediately rather than sampling badly.
**1024 `max_new_tokens` / ~21.5 frames per second = 47.6s** - it runs to its token ceiling emitting
non-speech. Fish rendered all nine Stage-1 corpus excerpts cleanly, so this is input-specific, not a
broken install.

**Why it is disqualifying rather than merely annoying:** every automated signal said success - HTTP
200, a well-formed WAV, a plausible duration, a clean exit. An unattended backfill would have
published 47 seconds of hiss.

**Both safeguards added FOR honesty made it worse, which is the transferable part:**
- The **ASR check** (added to catch truncation) transcribed the near-silence as *"Thank you. Thank
  you."* - F44's documented Whisper-fabricates-from-silence failure, here manufacturing positive
  evidence for a broken file.
- **Loudness normalisation** (added so level could not bias listening) would have amplified a -48 dB
  noise floor by ~30 dB into loud hiss, reading as catastrophic VOICE QUALITY rather than a failed
  render.
Only DIRECT level measurement (`volumedetect` against a known-good control) was trustworthy. Any
listening artefact must verify each take is real output before shipping - now rule 6 of the
fleet rule `comparison-integrity.md`.

Evidence: tts-bench/listening/now/fish__native*.wav (3 renders, gitignored - regenerable);
docs/W3-STAGE2-SWEEP.md.

## F51 - the recorded PyPI install route for 2 of the 3 remaining TTS engines does not lead to the upstream project at all: one is an abandoned third-party repackage predating the version we want, the other carries unedited cookiecutter placeholders - and a free licence pre-check cleared all three in seconds

**Kind: METHOD**

The Stage-2 plan recorded `pip install cosyvoice==0.0.8` and `zonos==0.1.0.dev0` as the routes for
CosyVoice3 and Zonos. Querying the PyPI JSON API before installing anything showed **neither package
is published by the upstream project**:

| Package | Claimed engine | What PyPI actually says |
|---|---|---|
| `cosyvoice` 0.0.8 | CosyVoice3 | author *Lucas Jin*, home `github.com/lucasjinreal/CosyVoice` - a third-party fork, **uploaded 2024-11-17**. CosyVoice 3 did not exist then, so this package **cannot be CosyVoice3** whatever else it is. Upstream is `FunAudioLLM/CosyVoice`. |
| `zonos` 0.1.0.dev0 | Zonos | author **"Your Name"**, a personal gmail address, home **`github.com/yourusername/zonos`** - unedited cookiecutter placeholders. Upstream is `Zyphra/Zonos`. Declares `torch>=2.5.1`, which on this box is the documented route to a CUDA torch silently evicting the ROCm build. |

Neither was installed. **All three remaining engines install from a git clone, not from PyPI** -
which is what the plan already said for MegaTTS3 and should have said for the other two.

**The transferable part is the ordering, not the packaging trivia.** Licence is a *free, instant*
disqualifier and F5-TTS had already died on exactly that gate (cc-by-nc), so it was checked before
any container work rather than after. All three cleared, code and weights both Apache-2.0:

| Engine | Code repo | Weights | Note |
|---|---|---|---|
| CosyVoice3 | `FunAudioLLM/CosyVoice` Apache-2.0 | `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` apache-2.0, ungated | the guessed id `CosyVoice3-0.5B` returns **401**; the real id carries the `Fun-` prefix and a `-2512` date suffix. Ships a `speech_tokenizer_v3.batch.onnx` - a batch-shaped path, relevant to F49. |
| Zonos | `Zyphra/Zonos` Apache-2.0 | `Zyphra/Zonos-v0.1-transformer` + `-hybrid`, apache-2.0 | code last pushed **2025-03-05**, ~17 months stale - a maintenance signal, not a blocker. |
| MegaTTS3 | `bytedance/MegaTTS3` Apache-2.0 | `ByteDance/MegaTTS3` apache-2.0, 5 weight files | still no PyPI, as recorded. |

That matters because the field is currently collapsed by licence: F5-TTS is the quality yardstick
and **cannot ship**, so the open question (F49) is whether a commercially-licensed engine reaches its
band. Confirming three Apache-2.0 candidates *before* standing any of them up means no repeat of the
F5 outcome - an engine benchmarked at length and then disqualified on a fact available in seconds.

Evidence: PyPI JSON API for `cosyvoice`/`zonos`; GitHub API for the three upstream repos; HF model
API for the four weight repos. Route corrections applied to docs/W3-STAGE2-SWEEP.md.

## F52 - MegaTTS3 is Apache-2.0, publishes its weights, and STILL cannot clone a voice locally: ByteDance withholds the WavVAE *encoder*, so a licence-clear engine can be capability-blocked in a way no licence check detects

**Kind: MODEL**

MegaTTS3 passed the F51 licence gate cleanly - `bytedance/MegaTTS3` is Apache-2.0 on code, and
`ByteDance/MegaTTS3` is apache-2.0 with 22 files and 4.27 GB of published weights. It is nonetheless
**unusable for this benchmark**, and the reason is visible in the weight listing before any download:
the repo ships `wavvae/decoder.ckpt` (904 MB) and **no encoder**. From ByteDance's own `readme.md`:

> *"For security issues, we do not upload the parameters of WaveVAE encoder to the above links. You
> can only use the pre-extracted latents from [link1] for inference. If you want to synthesize speech
> for speaker A, you need "A.wav" and "A.npy""*

Without the encoder there is no way to turn *our* reference audio into the `.npy` latent the model
needs. The only sanctioned route for a new voice is uploading the clip to a public Google Drive
"voice request queue" and waiting for ByteDance to verify and process it - a manual third-party
dependency, on a project its own readme describes as *"primarily intended for academic purposes"*,
requiring the owner's voice to be handed to a third party. All three are disqualifying for an
on-prem benchmark whose entire premise is that nothing leaves the box.

**The transferable lesson, and it is a correction to F51's own method.** F51 established that
checking LICENCE first is free and instant, and it is - but licence-clear is not the same as
capable. A vendor can publish permissively-licensed weights with the one component you need removed,
and every signal a licence check reads will come back green: SPDX identifier, model-card tag, file
count, total bytes. **The gate has two questions, not one:** may we use it, and *can* we do the thing
we need with what is actually published. The second is answered by reading the file list against the
required data flow - here, "which artefact turns my wav into the model's conditioning input?" - which
cost about two minutes and no GPU time.

Field consequence: of the three engines F51 licence-cleared, **two remain viable** (CosyVoice3,
Zonos). Both were verified to expose a transcript-free cloning path before any container work, since
we have no transcript for the owner's reference clip: CosyVoice3 via
`inference_cross_lingual(tts_text, prompt_wav)` and Zonos via `make_speaker_embedding(wav, sr)`.

Evidence: `github.com/bytedance/MegaTTS3/readme.md` (note: lowercase `readme.md`; `README.md` 404s);
HF API file listing for `ByteDance/MegaTTS3`. Recorded in docs/W3-STAGE2-SWEEP.md.

## F53 - Zonos v0.1 builds, imports and clones on gfx1151 but cannot be brought up: torch.compile fallback costs 15+ min at 0% GPU, and its own `.to(cuda, bfloat16)` never completes - while the platform moves the same 3.2 GB in 0.2s

**Kind: PLATFORM**

Zonos was licence-cleared (Apache-2.0 on code and `Zyphra/Zonos-v0.1-transformer` weights), containerised
from the cached ROCm base, passed the build-time torch gate with byte-identical torch, imports cleanly,
and exposes exactly the transcript-free cloning path this benchmark needs
(`make_speaker_embedding(wav, sr)`). It still produced **no audio**. Two independent blockers.

### 1. The torch.compile fallback (understood, and there IS an escape hatch)

`zonos/model.py:216`:

> `# Only the mamba-ssm backbone supports CUDA Graphs at the moment`
> `return self.device.type == "cuda" and "_mamba_ssm" in str(self.backbone.__class__)`

and at line 238, if CUDA Graphs are unavailable it wraps the decode step in `torch.compile`.

**The chain is causal, and the first link is the fix for a different trap.** FlashAttention 2 and
mamba-ssm have no gfx1151 builds, so the `compile` extra is deliberately not installed (it is also
only needed by the HYBRID checkpoint) -> the transformer backbone is used -> `can_use_cudagraphs()`
returns False -> `torch.compile` is enabled -> Inductor compiles on CPU for **15+ minutes at
90-110% CPU with 0% GPU utilisation** before a single token is emitted. Nothing here is a bug in
Zonos or in ROCm; it is an upstream fast-path assumption ("mamba, or else compile") meeting a
platform where neither is cheap. Pass **`disable_torch_compile=True`**.

### 2. `.to(cuda, bfloat16)` never completes - and the platform is provably not at fault

With compile disabled, the run stalls in the model's own device/dtype conversion. Stage timing:
imports 2.3s, weights resolved 2.8s, **constructed on CPU 7.1s, state dict applied 7.2s**, then
`.to("cuda", torch.bfloat16)` does not finish within 15 minutes at ~171% CPU and 0% GPU. This is not
the weight load and not the fetch (the speaker model `Zyphra/Zonos-v0.1-speaker-embedding` is cached).

A three-line control **inside the same image** settles where the fault is:

| Operation | Time |
|---|---|
| first CUDA alloc / HIP context init | **0.2s** |
| allocate a 3.2 GB float32 CPU tensor | 2.3s |
| `.to("cuda", torch.bfloat16)` on that 3.2 GB tensor | **0.2s** |

**The platform moves the same volume of data, with the same dtype conversion, in 0.2 seconds.** So the
cost is inside Zonos's `nn.Module` tree conversion, not in ROCm, the driver, or the container. That
makes it an upstream issue rather than a porting gap, and chasing it further is upstream debugging
rather than benchmarking.

### Two measurement notes worth keeping

- **On this APU, `rocm-smi`'s VRAM figure under-reports GPU residency** - the iGPU shares system RAM.
  GPU **utilisation %** is the trustworthy signal, and it is what showed the work was on the CPU.
- **A 137 exit in the logs here is our own `podman kill`,** not an OOM. Recorded so a later reader
  does not diagnose a memory event that did not happen.

### Disposition

Zonos is **stood up but not viable on this box** without upstream work. Per `comparison-integrity.md`
rule 4 that is a REPORT, not a gap to fill: it is not counted as an arm in any listening comparison,
and its absence is stated wherever the field is enumerated. The surviving field for the owner's-voice
track is therefore **four** engines that actually rendered - Chatterbox, VoxCPM2, CosyVoice3, and F5
(diagnostic only, cc-by-nc).

Evidence: `zonos/model.py:216,238`; stage-timed spike output; the in-image allocation control above;
docs/W3-STAGE2-SWEEP.md.

## F54 - zero-shot voice cloning has an ACCENT COVERAGE limit that reference quality cannot fix: four architecturally-distinct engines, one clean reference, all four Americanised an Irish/neutral accent

**Kind: MODEL**

The owner's own voice was cloned from a single shared reference clip - 12.7s of his podcast
(`tra-go-to-expert_00975.9-00988.5.wav`), which he himself ranked best of four candidates and
described as *"all pretty decent"*: flat factor 0.000000 (no clipping), no internal pauses, mean
-15.8 dB. Every engine received the identical clip and the identical 26-word line.

| Engine | Architecture | Licence | Owner's verdict |
|---|---|---|---|
| Chatterbox | autoregressive | MIT | *"overly American and not usable"* |
| VoxCPM2 | autoregressive | Apache-2.0 | *"marginally better than chatterbox but still overly American"* |
| CosyVoice3 | LM + flow matching | Apache-2.0 | too American |
| F5-TTS | **non**-autoregressive | cc-by-nc | too American |

> *"None of the cloned versions of my voice work. All too American"*

**This is not a settings problem, and that was tested rather than assumed.** The following were all
tried and none recovered the accent: `cfg_weight` sweeps (0.2-0.8) in Chatterbox; decoupling pace from
guidance via a post-hoc pitch-preserving time stretch; F5's native `speed` control; **zero-shot mode
with the reference TRANSCRIPT** rather than cross-lingual mode (a genuinely different conditioning
path, which uses information the earlier attempts discarded); and CosyVoice3's **explicit instruct
mode** telling it to speak with an Irish accent. Four architectures - two autoregressive, one
LM+flow, one non-autoregressive - fail the same way, which locates the cause in the training
distribution rather than in any engine's design or configuration.

**Most likely cause:** the target is an Irish/neutral accent. General American dominates English TTS
corpora and British RP is well covered; Irish is rare in both. With little in-distribution evidence
for the target accent, the model's prior reasserts itself no matter how clean the reference is - and
the reference here was clean, well-levelled, undistorted, and chosen by the owner.

**The commercially interesting part, and the reason this belongs in client-facing material.** "You can
clone any voice locally from 15 seconds of audio" is the standard claim for zero-shot TTS, and it is
TRUE ONLY FOR ACCENTS WELL REPRESENTED IN THE TRAINING DATA. The failure mode is not a crash or an
obviously bad render - it is a *plausible, fluent, good-quality voice that is subtly the wrong person*,
which automated metrics (speaker-similarity scores, WER, MOS predictors) will happily score well. It
took the owner's ear to reject it, four times. **Anyone evaluating on-prem voice cloning for a
non-American, non-RP speaker should test their OWN accent before believing a demo.**

**Two related mechanisms found on the way:**
- **In Chatterbox, `cfg_weight` is simultaneously the pace control AND the accent-fidelity control,
  and they pull in opposite directions.** It is classifier-free-guidance strength: lowering it slows
  delivery by loosening adherence to the reference, which is exactly what lets the American prior
  through. The owner heard both halves of this independently - cfg 0.5 "too fast" with an acceptable
  accent, cfg 0.3 better paced and suddenly American. **Slowing via `cfg_weight` cannot preserve
  accent.** The decoupling is to hold cfg high and time-stretch afterwards; F5 by contrast exposes a
  native `speed` parameter independent of `cfg_strength`.
- CosyVoice3's `inference_cross_lingual` is for speaking a *different* language from the reference and
  **discards the reference transcript**; `inference_zero_shot` is the correct same-language path.

**NOT yet tested, and both remain open:** fine-tuning rather than zero-shot cloning (the owner's
podcast archive is **176 episodes / 127.6 hours / 6.7 GB**, and F46's host-vs-other diarisation at
97.2% is exactly the tool needed to extract his segments from interview episodes), and commercial
cloning services, which handle non-American accents markedly better but break the on-prem premise.

**Owner's disposition (2026-07-26):** own-voice track parked; finish the British-female narrator
first. Note the narrator is a much easier case for exactly the reason above - English accents are
abundant in TTS training data, so the drift that killed the Irish accent is not predicted to recur.

Evidence: tts-bench/listening/tra-{four-engines,accent-test,two-engines,f5,zeroshot}.mp3 (gitignored,
regenerable); per-engine spike records in docs/W3-STAGE2-SWEEP.md.

## F54 AMENDMENT + F52/W3 RETRACTION (2026-07-26, same day) - "CosyVoice3 WORKING" was WRONG: every one of its renders was garbled, and my own dtype "fix" is the likely cause

**Kind: METHOD**

An intelligibility gate (`tts-bench/check_intelligibility.py`, ASR-vs-requested-text WER) was written
after the owner reported that narrator clones were *"completely garbled not recognisable as English
speech"* despite passing every duration/level/flat-factor screen. Run retroactively over every render
delivered this session, it produced a result that forces two corrections.

| Render | Engine | WER | Verdict | What Whisper heard |
|---|---|---|---|---|
| `narr_cosy_p233` | CosyVoice3 | 8.54 | **GARBLED** | "yes yes yes yes yes…" |
| `narr_cosy_p239` | CosyVoice3 | 2.50 | **GARBLED** | "it's it's it's it's…" |
| `narr_cosy_p239dn` | CosyVoice3 | 0.96 | **GARBLED** | "what's that what's that…" |
| `cosy_tra_s10` | CosyVoice3 | 0.96 | **GARBLED** | "up that g and each to that pew but" |
| `cosy_zs` | CosyVoice3 | 0.96 | **GARBLED** | "i'll blow that up oh dear…" |
| `cb_ac_c50` | Chatterbox | **0.00** | ok | exact match |
| `vox_tra_clone` | VoxCPM2 | **0.00** | ok | exact match |
| `f5_tra_s10` | F5-TTS | 0.04 | ok | exact match |

**RETRACTED: "CosyVoice3 - WORKING, RTF 0.242x"** (recorded earlier today in docs/W3-STAGE2-SWEEP.md).
It never produced intelligible speech on this box. The RTF number is real but measures the production
of gibberish, which makes it worthless. **A throughput figure for an engine whose output was never
checked for intelligibility is not a benchmark result.**

**F54 IS AMENDED from four engines to THREE.** The verified-intelligible engines that the owner
rejected on accent are **Chatterbox (AR), VoxCPM2 (AR), and F5-TTS (non-AR)** - all WER <= 0.04, so
that feedback stands and the finding survives, including the cross-architecture argument (two
autoregressive plus one non-autoregressive still fail the same way). CosyVoice3 must be **struck from
the accent conclusion entirely**: it was arm 4 of the four-engine reel, and part of the owner's verdict
was therefore given on noise. Nothing about accent can be claimed for CosyVoice3 - it has never been
heard working.

**The likely cause is a "fix" I made, and it is error suppression in the exact form the fleet rule
forbids.** CosyVoice3's published checkpoint is bfloat16 while its frontend emits float32 embeddings,
so the first matmul raised `mat1 and mat2 must have the same dtype, but got Float and BFloat16`. I
resolved it by casting the LLM to float32. That silenced the exception and produced numerically broken
output - **degenerate repetition ("yes yes yes yes") is textbook LM collapse, not a voice problem.**
The correct handling is to leave the checkpoint in bf16 and wrap inference in `torch.autocast`, so the
mixed-dtype matmul is *handled* rather than the weights force-converted. Queued in
`stage2-sweep/run_batch.sh`.

### The transferable lessons, which are the point of this entry

1. **A screen that proves audio EXISTS does not prove it is SPEECH.** Duration, words/sec, mean level
   and flat factor all passed on renders that say "yes yes yes yes". The dead-take gate added after F50
   catches *silence dressed as speech*; it does not catch *gibberish dressed as speech*, and it was
   wrongly assumed to cover "is this real output" in general. Verify against the *requested content*.
2. **Making an error message go away is not the same as fixing the error.** The dtype cast turned a
   loud, precise, correct failure into a silent wrong answer - the single worst trade in
   `error-suppression.md`, made while quoting that rule elsewhere in the same session.
3. **A tidy explanation that fits a prior is a warning sign.** One garbled render was 45% shorter than
   its siblings. That was explained as "the denoising damaged it" - a story that fitted a prediction
   already made about denoising artefacts, and was even presented as a vindicated prediction. The
   simpler reading was that ALL THREE were broken and one was broken more visibly. Ask what else
   produces the observation before adopting the one that flatters an existing hypothesis.
4. **RTF is meaningless until intelligibility is established.** Measure that the output is the right
   words before measuring how fast it arrived.

Evidence: `tts-bench/check_intelligibility.py` output, run over 8 renders; batch audit of all ~20
renders in progress via `stage2-sweep/run_batch.sh` -> `tts-bench/results/narrator-batch-report.md`.

## F55 - CosyVoice3 is NOT VIABLE on gfx1151: it fails its OWN documented example, and three plausible root causes were each disproved by varying our inputs instead of testing the engine against itself

**Kind: MODEL**

**Status:** CLOSED - engine disqualified. Supersedes the F54 amendment's "pending re-test" on CosyVoice3.

**Claim:** CosyVoice3 (`FunAudioLLM/Fun-CosyVoice3-0.5B-2512`) loads, runs, reports plausible RTF, and
produces well-formed audio at a normal level on this box - and every render is unintelligible. The
disqualifying evidence is not our audio at all: given its **own** reference asset and its **own** target
text, copied verbatim from `example.py`, the output is garbled.

**The measurement.** All renders gated by `tts-bench/check_intelligibility.py` (ASR-vs-requested-text WER).
**Filename note (2026-07-27):** the `stage2-sweep/out/refvoice/*.wav` files named below by their bare arm
name (`ctl_docs_zh`, `narr_cosy_p233`, etc.) were renamed the same day to carry their verdict in the
filename - see `docs/w3-audio-rename-log.csv` for the old->new mapping. This table is left verbatim as
the original captured evidence; it is not stale, the files it refers to just have a longer name now.

| Arm | Reference audio | Text | WER | Verdict |
|---|---|---|---|---|
| `ctl_docs_zh` | repo `asset/zero_shot_prompt.wav` | repo's Chinese target, verbatim | 1.00 | GARBLED - 2.0s for a 4-5s tongue-twister |
| `ctl_docs_en` | repo `asset/zero_shot_prompt.wav` | our English line | 10.27 | GARBLED - "i don't know" x11 |
| `n2_p233_zs` / `_xl` | VCTK p233 8.65s | our English line | 1.00 / 8.50 | GARBLED |
| `n2_p239_zs` / `_xl` | VCTK p239 7.17s | our English line | 0.96 / 12.77 | GARBLED |
| `n2_own_xl` | owner's podcast 12.6s | our English line | 0.92 | GARBLED |

Twelve renders across the session: **zero intelligible**, spanning two dtype handlings, five reference
clips, both inference modes, and prompt lengths of 7s / 9s / 12s / 20.5s. The failure signature is
always the same - degenerate repetition ("yes yes yes", "i i i i", "i love you i love you"), i.e. LM
collapse, with output bearing no relation to the requested text.

**Suspected mechanism, NOT proven:** `speech_tokenizer_v3.onnx` runs on the onnxruntime **CPU** execution
provider (there is no gfx1151 EP - a documented, deliberate choice in `Dockerfile.cosyvoice`). That graph
converts prompt audio into the speech tokens that condition the LM. Wrong tokens there would produce
exactly this - no crash, plausible duration, plausible level, total semantic collapse, and failure that
is invariant to reference clip and text. Recorded as a hypothesis because it was not tested; the engine
was disqualified before spending more on it, per viability-first.

**Three root causes were proposed and each was DISPROVED - all three by varying our own inputs:**

1. *"The prompt is too long (20.5s vs the expected 3-10s)."* Disproved: 7.17s and 8.65s single utterances
   with exact matching transcripts fail identically.
2. *"The bf16 checkpoint is being fed float32."* This one was real but was **not** the garbling. Two
   wrong fixes were tried before the right one: casting the LLM to float32 (error suppression - it
   removed the exception and broke the numerics), then a main-thread `torch.autocast`, which **could not
   possibly work** because *PyTorch autocast state is thread-local and CosyVoice runs the LLM in a worker
   thread* (`Exception in thread Thread-5 (llm_job)`). The library already autocasts in the right place -
   `cli/model.py:103`, inside `llm_job` - gated on the `fp16` flag. So `fp16=False` was the actual defect.
   Setting `fp16=True` fixed the crash cleanly, with no monkeypatching. **The renders stayed garbled.**
3. *"`AutoModel` does setup that the `CosyVoice3` class does not."* Disproved by reading it:
   `AutoModel` is a nine-line dispatch that calls `CosyVoice3(**kwargs)`. Identical.

**The transferable lesson, and it is the expensive one:** every hypothesis above was tested by changing
OUR inputs. The test that settled it in four minutes - *can the engine reproduce its own README?* - was
run last. **A component that has only ever failed tells you nothing until you have seen it succeed at
something.** That is the same discipline as the positive control added to the intelligibility gate the
same day (a human recording, gated against its own transcript, WER 0.00) - which was reasoned about
carefully for the gate and then not applied to the engine an hour later.

**Consequences:**

- CosyVoice3 is struck from F54 permanently, not pending re-test. F54's cross-architecture accent
  conclusion rests on **three** verified-intelligible engines (Chatterbox WER 0.00, VoxCPM2 WER 0.00,
  F5-TTS WER 0.04), and stands on those.
- The three narrator candidates rejected as garbled were rendered by this engine **only**. That was the
  whole cause: the narrator track had been running on the one engine that does not work here. Re-rendered
  with Chatterbox and VoxCPM2, all four narrator clones pass the gate at WER 0.00 first time.
- **Second-order lesson:** a broken component silently narrowed the field. It contributed a garbled arm to
  a comparison reel and part of an accent verdict before anyone knew it produced no speech at all.

Evidence: `stage2-sweep/out/spike_cosy_control.py` (the engine-level positive control),
`tts-bench/results/narrator-batch-report.md`, gate output in `stage2-sweep/out/batch.log`.

## F56 - the W3 narrator is SETTLED (VCTK p239 cloned by Chatterbox), and the pace figure that nearly triggered a tuning pass was a single-utterance artefact: 4.11 w/s on one 26-word take, 3.42 w/s over 227 words at the same config

**Kind: MODEL** - the narrator decision. The three measurement lessons in this
run are **F133**, split out 2026-09-01.

**Date:** 2026-07-26. **Decided by:** the owner's ear on `tts-bench/listening/narrator-pairs-reel.mp3`.

The six-take reference/clone reel (F55's replacement for the CosyVoice3-poisoned set) resolved TWO
decisions at once, and cleanly, because the arms were built to separate them:

| Verdict | Evidence |
|---|---|
| **Engine: Chatterbox** | Owner accepted takes 2 and 5 (both Chatterbox) and neither 3 nor 6 (both VoxCPM2). Same reference clips, same line, same gate - the engine was the only variable, and it separated the same way on BOTH voices independently. |
| **Voice: p239** (SW England, female) | Takes 1 and 4 - the two *human* references - were both accepted, so the split happened at the cloning step rather than the voice. That left the owner's prior ranking (p239 1st, p233 2nd) as the tie-break, which is how he asked it to be broken. |

**The reel's deliberate order inversion earned its keep.** p233 was played first, against the owner's
prior ranking, so he heard the voice he had ranked *second* first and un-anchored. He still chose p239.
A tie-break resting on an order effect is not a tie-break; inverting the order is what makes the two
explanations (real preference vs primacy) distinguishable.

**VoxCPM2 lost here after previously being called "marginally better" than Chatterbox on the owner's own
voice (F54).** Not a contradiction: that judgement was on an Irish male reference *both* engines
Americanised, this one on English female references one engine handles. **An engine verdict does not
transfer across reference voices** - which is a warning against ranking engines in the abstract.

### The pace number was wrong, and the mechanism is worth keeping

Take 5 measured **4.11 w/s** against its human reference's 3.63, and was reported to the owner as "about
13% quick" with pace tuning named as the next lever. Rendering **227 words / 67.9s** at the *identical*
config gives **3.34 w/s overall, 3.42 w/s excluding inter-chunk silence** - i.e. *slower* than the human
reference. **There was no pace problem.** Per-chunk pace across the ten chunks spans **2.82-4.07 w/s**, so
4.11 sat at the top of the config's natural range: a one-sample draw read as a property of the setting.

- **Short autoregressive TTS renders rush.** The model has no established rhythm over 26 words, and one
  clipped trailing pause swings a words/sec ratio hard. The shortest chunk here (8 words, 2.84s) is also
  the slowest-measuring at 2.82 w/s for the same reason, in the other direction.
- **Chatterbox has no speed parameter at all** - verified against its own signature (`text`,
  `repetition_penalty`, `min_p`, `top_p`, `audio_prompt_path`, `exaggeration`, `cfg_weight`,
  `temperature`). Pace is *emergent* from how many speech tokens T3 emits, and with `temperature=0.8` it
  is **stochastic**. So a pace difference is not a difference until the fixed-settings run-to-run spread
  is measured - the F15 noise-corridor discipline, in a domain where it had not been applied.
- **The failure was publishing before measuring the ruler.** The stochastic-pace risk was identified
  *before* the render, and the 4.11 figure had already been given to the owner by then.

### Long-form rendering needs chunking, and that is an F50 guard rail

`ChatterboxTTS.generate()` hardcodes `max_new_tokens=1000` and does **not** raise on over-long text - it
runs to the ceiling emitting non-speech. That is F50's Fish s2-pro failure exactly (HTTP 200, well-formed
47s WAV, -48 dB noise floor). `tts-bench/render_longform.py` therefore splits on sentence boundaries at
~200 chars and **reports every chunk's realised duration**, so a ceiling hit is visible as a duration
outlier rather than averaged into the whole. Verified clean here: all ten chunk durations scale with word
count, and the longest chunk (210 chars, 36 words) sampled 137 of 1000 tokens.

It also calls `prepare_conditionals()` **once** and reuses the tensor rather than re-passing
`audio_prompt_path` per chunk, so every chunk is conditioned on an identical speaker embedding - any
timbre wobble between chunks is sampling variance, not a re-derived embedding.

**Measured config** (the one the owner accepted - Rule 8: a benchmark measures a CONFIG):
Chatterbox `chatterbox-std`, reference `VCTK p239 utterance 008` (7.17s, CC BY 4.0, **attribution
mandatory if this voice ships**), `exaggeration=0.5 cfg_weight=0.5 temperature=0.8`, seed `20260726+i`
per chunk, 180ms inter-chunk gap, Perth watermarking bypassed. **RTF 2.49x** - i.e. 2.5x slower than
real time to generate, which is a batch-rendering cost, not a live-narration one.

Gate: **WER 0.01 over 227 words.** Levels: -22.3 dB mean pre-normalisation (dead-take threshold is -40),
-1.9 dB peak after loudnorm to -16 LUFS, so no clipping.

Evidence: `tts-bench/render_longform.py`, `tts-bench/corpus/narrator-longform.txt`,
`stage2-sweep/out/refvoice/narrator_longform_p239.wav.json` (per-chunk metrics),
`tts-bench/listening/narrator-p239-chatterbox-68s.mp3`, `tts-bench/arms-narrator-pairs.json` (the arms
that produced the verdict).

### F56 ADDENDUM (2026-07-26) - the narrator is ACCEPTED as "good enough", and further source-voice search is declined on cost grounds

Owner's verdict on the 68s sustained sample: *"That's definitely the best of everything we listened to!
It's 'good enough'. We maybe can do better if we did extensive testing of other source voices but it's
not worth the effort for now."*

**This is a decision, not a gap.** It closes the W3 quality track. Recording it explicitly because the
next agent will otherwise read "VCTK is exhausted" plus the licence-checked alternatives in HANDOFF as an
invitation to keep hunting:

- **DO NOT stand up Hi-Fi TTS or LibriTTS-R** to search for a better narrator voice. They remain the
  correct answer *if the requirement changes* (a voice that fails on a new constraint, or a licence
  problem with VCTK attribution), but they are NOT open work.
- The owner named the trade-off himself: better is *probably* reachable through extensive source-voice
  testing, and is not worth the effort at this quality level. Eight VCTK speakers were auditioned to get
  here; a materially better result needs a different corpus and another full audition round.
- **What IS still open, and is cheap:** nothing about the voice. Pace needs no tuning (see above - the
  4.11 w/s figure was a single-utterance artefact). The shipped config is fixed.

**Consequence for W3:** quality was criterion #1 and is now settled, so the batching/throughput lever
(criterion #2) is unblocked for the first time - and per the F54 amendment it can now be measured
legitimately, because the engine it would measure has passed the intelligibility gate.

## F57 - the kernel drifted 6.17 -> 7.0 under the register's "single stack" constant, installed by unattended-upgrades

**Kind: PLATFORM**

This register's header declares the throughput constants were taken on one stack, including
`kernel 6.17.0-35`. That has not been the running kernel since 2026-07-19. `unattended-upgrades`
installed both bumps unprompted; neither was requested, and each took effect at a later, unrelated
reboot - so the change and its effect are separated by days.

| Booted | Kernel | Installed by |
|---|---|---|
| Jul 3 - Jul 16 09:22 | 6.17.0-35 | manual `apt install linux-generic-hwe-24.04` (Jul 2 17:38) |
| Jul 16 09:22 - Jul 19 18:04 | 6.17.0-40 | `/usr/bin/unattended-upgrade` (Jul 16 06:35) |
| Jul 19 18:04 - Jul 29 15:09 | **7.0.0-28** | `/usr/bin/unattended-upgrade` (Jul 18 06:14) |
| Jul 29 15:09 - present | 7.0.0-28 | reboot only (glibc 2.39-0ubuntu8.8; no kernel change) |

Why it matters: `amdgpu` is an in-kernel driver, so a kernel bump swaps the GPU driver underneath
every bench. Phase A / llama-bench constants were measured on 6.17.0-35; all W3 TTS work
(2026-07-25..27) ran on 7.0.0-28. Those are not the same stack, and nothing in `results/` records
which kernel produced a given number.

**Exactly one constant drifted - verified, not assumed.** Mesa is still 25.2.8
(`mesa-vulkan-drivers 25.2.8-0ubuntu0.24.04.2`, installed 2026-07-03 and never touched by u-u),
`libdrm` 2.4.125, hardware unchanged, and llama.cpp is a local build outside apt. The register's
other constants hold; only the kernel line is stale.

F10's status note already anticipated exactly this - the constants "are expected to move with kernel
releases". This is that prediction coming true. It went unrecorded for ten days because nothing on
the box watches the kernel, and u-u's own log only names the packages, never the consequence.

**Deliberately NOT fixed by pinning** (owner decision, 2026-07-29). A hold would stop kernel security
updates, and it is not yet known whether 6.17 -> 7.0 moved any measured number. Recording the variable
is the first step; establishing whether it matters needs a re-measurement on 7.0.0-28 against a
6.17.0-35 figure, which is a deliberate experiment, not a side effect.

Evidence: `/var/log/apt/history.log` (both kernel installs carry
`Commandline: /usr/bin/unattended-upgrade`), `last -x reboot` (boot-to-kernel mapping),
`/var/log/unattended-upgrades/unattended-upgrades.log` lines 172-174 and 194-197.
Status: ACTIVE, unpinned by choice. Bears on `docs/memory-edge-deadlock.md` - that deadlock
fingerprint was characterised on 2026-07-13, i.e. on 6.17.0-35, and has not been re-confirmed on 7.0.

### F57 ADDENDUM (2026-07-29) - Ubuntu Pro attached, 38 ESM backports applied, ffmpeg measurement path verified UNCHANGED, Livepatch now a live variable

The MOTD line `38 additional security updates can be applied with ESM Apps` turned out to be a second
"configured but not in effect" gap on the same box: `50unattended-upgrades` already listed the ESM
origins in `Allowed-Origins`, but the machine was unattached, so those lines were inert and 38
security updates were never applied. sparkmax is now attached to the free personal Ubuntu Pro
subscription and the backlog is applied.

**This was done attended, on purpose.** Because the ESM origins were pre-authorised, attaching alone
would have handed unattended-upgrades 38 packages to install unsupervised at the next 06:xx timer -
including ffmpeg, a measurement dependency for every W3 loudness figure, and caddy, which fronts
sparkrouter. Procedure and the before/after snapshot: `ops/bin/esm-enable.sh` (phases
status/attach/upgrade/rollback), report at `/var/log/sparkbench-esm-enable.log`.

All 38 landed as `+esmN` suffixes on **identical base versions** - security backports within the same
upstream release, not version bumps:

| Package | Before | After |
|---|---|---|
| `ffmpeg` | 7:6.1.1-3ubuntu5 | 7:6.1.1-3ubuntu5**+esm10** |
| `podman` | 4.9.3+ds1-1ubuntu0.2 | ...**+esm3** |
| `buildah` | 1.33.7+ds1-1ubuntu0.24.04.3 | ...**+esm3** |
| `caddy` | 2.6.2-6ubuntu0.24.04.3 | ...**+esm2** |
| `python3-pip` | 24.0+dfsg-1ubuntu1.3 | ...**+esm3** |

Kernel unchanged (7.0.0-28-generic), caddy still `active` after restart, `needrestart` reported no
services, containers or user sessions running outdated binaries.

**ffmpeg was verified, not assumed.** "Same upstream version" makes a behaviour change unlikely, not
impossible, and F56's audio figures depend on it. Re-measured the delivered, byte-identical artefact
with the upgraded binary:

```
file:   tts-bench/listening/narrator-p239-chatterbox-68s__WINNER-ACCEPTED-...mp3
        sha256 38a2aeb4d401d2e7...  1087917 bytes (unchanged on disk)
binary: ffmpeg version 6.1.1-3ubuntu5+esm10
        max_volume: -1.9 dB     Duration: 00:01:07.97
F56:    -1.9 dB peak after loudnorm to -16 LUFS, 68s (audio_s 67.9)
```

Zero gap. The measurement path is unchanged, so F56's loudness figures stand and no W3 audio needs
re-measuring. (`mean_volume -17.5 dB` is the post-loudnorm mean; F56's -22.3 dB was the
pre-normalisation stage, a different measurement point, not a disagreement.)

**New variable, recorded because it is invisible:** `pro attach` also enabled **Livepatch**, which was
not requested - it comes on by default with the personal subscription. Livepatch patches the RUNNING
kernel without changing the package version, so from 2026-07-29 `uname -r` no longer fully identifies
the kernel a number was measured under. Current state is clean (`patchState: nothing-to-apply`,
`patched-cves: []`), so nothing measured so far is affected. From here, the kernel check for any
benchmark is `uname -r` **plus** `canonical-livepatch status`. Reversible with
`pro disable livepatch` if the reproducibility cost ever outweighs the un-rebooted CVE coverage.

Evidence: `/var/log/sparkbench-esm-enable.log`, `pro security-status --format json` (the 38-package
list), `canonical-livepatch status --verbose`, the volumedetect run above.
Status: ACTIVE. Livepatch is now part of the stack fingerprint.

## F58 - the repo.radeon.com apt pin is LOAD-BEARING: Ubuntu's ROCm sorts NEWER than AMD's and would silently downgrade the GPU stack

**Kind: PLATFORM**

`/etc/apt/preferences.d/repo-radeon-pin-600` is the only thing preventing apt from replacing AMD's
ROCm 7.2.4 with Ubuntu's ROCm 5.7.1/6.0.0 - a two-major-release downgrade to packaging that predates
`gfx1151` support entirely. Deleting or lowering that 60-byte file breaks inference on this box at the
next `apt upgrade`.

The cause is version-string ordering, not policy. AMD versions ROCm components by *component* version
with the release in a suffix; Ubuntu used the *suite* version. dpkg therefore reads the archive's
ancient package as an upgrade:

| Package | Installed (AMD ROCm 7.2.4) | Ubuntu archive | dpkg ordering |
|---|---|---|---|
| `hipcc` | 1.1.1.70204-93~24.04 | 5.7.1-3 | archive sorts NEWER |
| `rocm-cmake` | 0.14.0.70204-93~24.04 | 6.0.0-1 | archive sorts NEWER |
| `rocminfo` | 1.0.0.70204-93~24.04 | 5.7.1-3build1 | archive sorts NEWER |

Proof: `dpkg --compare-versions '1.0.0.70204-93~24.04' lt '5.7.1-3build1'` exits 0.

**The visible symptom is a false alarm, and it must never be "resolved".** Because a higher-sorting
version exists in an allowed origin, u-u writes all three to `/var/lib/unattended-upgrades/kept-back`
every run, and `/etc/update-motd.d/92-unattended-upgrades` renders that as:

```
3 updates could not be installed automatically. For more details,
see /var/log/unattended-upgrades/unattended-upgrades.log
```

That notice means the pin is working. **NEVER** clear it by `apt install`-ing the three packages, by
`--allow-downgrades`, or by removing/lowering the pin.

**Blacklisting will not silence it** - checked in the u-u source before recommending anything.
`find_kept_packages()` calls `kept_packages.add(...)` as soon as `find_better_version()` returns a
version, and only *then* calls `kept_package_excuse()`, where `Package-Blacklist` and
`apt-mark hold` are consulted. Those two settings change the wording of the log line and nothing else;
the MOTD count stays at 3. The obvious fix is a no-op here.

Evidence: `/etc/apt/preferences.d/repo-radeon-pin-600` (priority 600 vs archive 500),
`apt-cache policy hipcc rocm-cmake rocminfo`, `/var/lib/unattended-upgrades/kept-back`,
`/usr/bin/unattended-upgrade` `find_kept_packages`/`kept_package_excuse`.
Status: ACTIVE, permanent - this notice is expected for as long as ROCm comes from repo.radeon.com.

## F59 - llama-server generation at temperature 0 is BYTE-deterministic (10/10), and a like-for-like failure produced the opposite claim mid-session

**Kind: METHOD**

GLM-4.7-Flash was run twice over the same ten closed-record matters at the same serving config -
`-np 1 -c 32768 --jinja`, temperature 0, `max_tokens` 12000 - as the `v4` and `v5` arms. **All ten
answers are byte-identical**, compared as strings (`a == b`) rather than by token count, length or
hash.

So a fixed model, prompt and serving config reproduces its output exactly, and two arms measured at
the same setting in different runs ARE comparable. This also bounds what a rep count above 1 can
measure: at temperature 0 with nothing varying, extra reps reproduce the same bytes and measure
nothing. Reps become informative only when something in the config moves.

**The finding that matters more is how the opposite got claimed.** Mid-session this register's own
project asserted that generation was "not reproducible answer-for-answer at temperature 0", on the
evidence that GLM's m08 answer COMPLETED at a 6,000-token ceiling and TRUNCATED at 12,000. That is a
real observation with a different cause: **`m08/matter.md` was rewritten between the two runs** (the
hardening recorded in `results/closed-record.md`). Two variables changed - the ceiling and the input -
and the difference was attributed to the only one that had been noticed.

This is `development-discipline.md`'s compare-like-for-like rule failing in its least visible form.
The usual worked examples are measurement-method mismatches - a shell `sha256sum` against a
language-level `sha256()`. Here both sides were measured identically; what differed was the INPUT,
and the input was a file nobody re-read because the session had not edited it. **A prompt corpus is a
variable in every run that uses it, and a matter file edited three commits ago is as much a config
change as a flag.**

The wrong claim reached a pre-registration (amendment A1) before it was caught. It was corrected in
amendment A2 rather than edited away, because a pre-registration quietly rewritten after the run
stops being one. The decision A1 justified - one table, one setting - was independently right, which
is exactly why the bad reasoning survived as long as it did: a correct conclusion is not evidence of
a correct argument.

Evidence: `results/closed-record/v4-glm-4.7-flash.json` against `v5-glm-4.7-flash.json`, ten string
comparisons; `results/closed-record-v5.md`; amendments A1 and A2 in `results/closed-record-prereg.md`.
Status: ACTIVE. Applies to any llama-server arm at temperature 0.

## F60 - what makes a closed-record matter DISCRIMINATE is a period that must be WALKED, not a second base that is merely selected

**Kind: METHOD**

The ten-matter corpus found that m08 scored 15/15 and separated nothing even after being hardened
with a rule conflict, while the matters that separated - m07 (7/15), m09, m03 - all carried two
clocks or two bases. Three matters were then built deliberately to that theory and run against all
three local models. **The theory half worked, and the half that failed is the useful part.**

| New matter | Mechanism | Total | Mistral, Qwen, GLM |
|---|---|---|---|
| m11-limitation-clocks | two clocks, different UNITS, across a public holiday | **6/15** | 4, 2, 0\* |
| m12-liability-cap-basis | two bases - a 12-month cap base against a one-month credit base | **12/15** | 4, 4, 4 |
| m13-interest-two-clocks | both - one invoice on two clocks, base narrowed twice | **7/15** | 2, 5, 0\* |

\* truncated at the 12,000-token ceiling, not attributable.

**m12 returned 4/5 from all three models** - identical coverage, separating nothing. It split only on
a trap, Qwen reproducing EUR 600 for a service credit computed on the wrong month's rate. m11 and m13
discriminate hard; m11 is the second-hardest matter in the whole corpus after m07.

The distinction: m11 and m13 have a second period that must be **walked** - a calendar counted across
a public holiday, a day-count basis applied over 19 days and 12 days from different start dates.
m12's second base only has to be **selected**: identify which figures are Charges, multiply by 125%.
Selecting the right base from a record is something these models do reliably. Walking a period is not.

Two pre-registered predictions (P8, P10) both said m13 would be the hardest of the three because it
carries two mechanisms in one matter. **It was Qwen's best matter of the thirteen, at 5/5.** Stacking
mechanisms did not compound difficulty; splitting a period across a calendar did. A future corpus
should be built on periods that must be counted, not on additional bases.

**Second result, on the reasoning arm.** GLM-4.7-Flash truncated on two of the three new matters at a
12,000-token ceiling, reaching no `## Final answer` block on either, having truncated on only one of
the original ten. It spent **58,441 answer tokens to score 40/65, below Mistral-Small-24B's 43/65 on
7,950** - roughly 7.3x the tokens for three fewer propositions. On this corpus the longer reasoning
trace is not converging, which extends F35's plateau result from open-ended drafting to work with a
determinate answer.

Evidence: `results/closed-record-v5.md` (full per-matter table and prediction resolutions), the three
`results/closed-record/v5-*.json` run files, `results/closed-record-prereg.md` P7-P12.
Status: ACTIVE. m12 is a candidate for rework or retirement.

## F61 - F10's DeltaNet 0.55 arch factor was a MoE accounting confound, not a DeltaNet penalty

**Kind: METHOD**

Qwen3.8-27B is a DENSE DeltaNet hybrid (27.32B, `general.architecture =
qwen35`, `full_attention_interval = 4`), so its active bytes per token are
unambiguous - every weight is active, no MoE estimate is involved. It prices
at arch factor **0.909** (GPU-resident 15.82 GB basis) to **0.966** (whole
file), i.e. ordinary DENSE. Pre-registered primary band 12.5-15.0 HIT at
12.64 t/s; the discriminating alternative 6.9-8.4 (0.55 applies) was
rejected by ~1.6x.

F10's DeltaNet-hybrid ~0.55 rested on n=1, and that point was
Qwen3.6-35B-A3B - a **MoE**, whose "~3B active of 35B" is an estimate. The
constant absorbed that estimation error and mislabelled it as an
architectural penalty. **Do not apply 0.55 to dense hybrids.** Whether it
still holds for MoE hybrids is untested: the honest reading is that the MoE
active-bytes estimate is the suspect term, not the DeltaNet kernel.

Evidence: results/model-survey.md "RESULTS - Qwen3.8-27B", Leg B; raw
results/raw/bench-20260815-014413-qwen38-legB-subject-27b.md. Pre-registered
before the run. Status: ACTIVE - amends F10.

## F62 - the DeltaNet hybrid buys depth-robustness, not peak speed

**Kind: PLATFORM**

Qwen3.8-27B decays only **-3.6%** in generation from d0 to d8192 (12.64 ->
12.19), the flattest slope measured on this box. Registered prediction was
0.88-0.95; measured 0.964, so this is a DEVIATION recorded as a finding.

| Model | tg d8192/d0 | pp512 d8192/d0 |
|---|---|---|
| Qwen3.8-27B (dense DeltaNet hybrid) | **0.964** | **0.786** |
| Qwen3-30B-A3B (MoE, same session) | 0.715 | 0.491 |
| Qwen3.6-35B-A3B (MoE DeltaNet hybrid) | 0.939 | - |
| Gemma-3-27B (dense) | 0.928 | - |
| Qwen3-32B (dense) | 0.896 | - |

Mechanism is structural, not a kernel accident: with
`full_attention_interval = 4`, only 1 layer in 4 grows a KV cache, so the
depth cost is roughly quartered. Prefill shows it more strongly still.

Also closes the question the Qwen3.6 entry left open by deliberately not
predicting pp: **there is no Vulkan DeltaNet prefill penalty on this stack.**
pp512 = 283.00 sits ABOVE dense comparators of similar size (Gemma-3-27B 248,
Qwen3-32B 198).

Consulting read: the hybrid is not a faster model, it is a model whose speed
you can quote at long context. Peak 12.64 t/s is 7.5x slower than the MoE
workhorse, but by 8K that gap has closed to 5.6x.

Evidence: as F61. Status: ACTIVE.

## F63 - the b9864 -> b10435 + kernel 6.17.0-35 -> 7.0.0-28 move is worth ~+3.3% tg

**Kind: PLATFORM**

Control leg, same model and quant (Qwen3-30B-A3B-Instruct-2507-Q4_K_M),
same box, relay down both times:

| Metric | b9864 / 6.17.0-35 | b10435 / 7.0.0-28 | Delta |
|---|---|---|---|
| pp512 | 1140.72 | 1132.55 +/- 9.93 | -0.72% |
| tg128 | 92.28 | 95.37 +/- 0.18 | **+3.35%** |
| tg@8K | 67.06 | 68.15 +/- 0.07 | +1.63% |

**+3.35% exceeds F15's +/-1.5% single-run noise** (llama-bench's own error
bar here is +/-0.19%), so it is a real generation tailwind, small but not
noise. Prefill is unchanged. Any tg figure compared across 2026-08-15 must
carry this, exactly as F57 requires for the kernel.

Method note kept deliberately: the Leg A disposition as written conflated
"inside the registered +/-5% band" with "inside F15 noise". They are
different thresholds and the pre-registration should have said so. The band
verdict was honoured as registered rather than rewritten after seeing the
number; the conflation is recorded instead.

Evidence: results/model-survey.md Leg A;
results/raw/bench-20260815-014413-qwen38-legA-control-30b.md.
Status: ACTIVE - addendum to F57.

## F64 - two concurrent benches void BOTH numbers, and the contended value was plausible

**Kind: METHOD**

2026-08-15, by accident: an operator-launched repeatability triplet and a
session-launched one overlapped on the one GPU.

| Run | tg128 | within-run sd | state |
|---|---|---|---|
| clean solo (triplet mean, n=3) | **12.607** | 0.02-0.04 | quiet box |
| operator inv 1 | 10.91 | **2.67** | ~30% of reps contended |
| operator inv 2 | 6.84 | 0.64 | fully contended |
| session inv 1 | 6.83 | 0.63 | fully contended |
| operator inv 3 | 11.64 | **2.11** | ~17% of reps contended |

Three things this establishes:

**1. The contended number was not obviously wrong.** 6.83/6.84 carried a tight
sd of ~0.63 and sat on the edge of the pre-registered 6.9-8.4 band for "the
DeltaNet arch tax applies" - the hypothesis F61 rejected. A single mistimed
run would have produced a clean-looking, plausible confirmation of the wrong
answer. Pre-registration plus a control leg is what makes that recoverable.

**2. The sd is the tell, and it is bimodal.** Pure states give 0.02-0.64;
MIXED states give 2.11-2.67. A repeatability run whose sd jumps an order of
magnitude is reporting contention, not model variance. The partially-contended
means also solve cleanly for their overlap fractions (30% and 17%), matching
the observed timing - so the interpretation is arithmetically checkable.

**3. Aggregate throughput UNDER contention EXCEEDED solo: 13.67 vs 12.607
= 1.081x.** Two independent processes, each with its own full 15.65 GiB weight
copy, still netted 8.1% more total tokens/sec than one. Single-stream
generation does not saturate this GPU. That is the observation E32 was written
to measure properly, and Rule 10 exists so it is never found by accident again.

**Root cause of the collision:** the bench guard checked `pgrep -x
llama-server` but not `llama-bench`, so two benches could start silently.
Fixed in both bench entry points; bound as Rule 9.

Evidence: results/raw/bench-20260815-020038-qwen38-triplet-{1,2,3}.md (VOID as
measurements, KEPT as this finding's evidence) vs
bench-20260815-020542-* (clean). Status: ACTIVE.

## F65 - a pre-registration that names a concept instead of a FIELD is not falsifiable

**Kind: METHOD**

Three specification errors in a single night's pre-registrations (2026-08-15),
all the same shape: the band was stated precisely, the measured quantity was
not.

| Registered as | What went wrong | Consequence |
|---|---|---|
| Leg A: in band means "inside noise (F15 +/-1.5%)" while the band was +/-5% | two different thresholds conflated in one disposition | tg128 +3.35% was simultaneously "in band" and "outside noise"; verdict needed prose to resolve |
| E32 pred 1: "slots=1 aggregate reproduces the llama-bench triplet, 12.3-12.9" | `aggregate_gen_tps` charges TTFT; the comparable field is `mean_stream_gen_tps` | 9.99 read as a FALSIFIER of harness agreement when the harnesses actually agreed (12.42 vs 12.607) |
| E32 pred 2: scaling bands "relative to each model's own slots=1" | never said aggregate or capacity | @4 is 2.10x on one metric and 2.65x on the other - band HIT or MISS depending on an unstated choice |

Each was recoverable only because the raw records carry every field. Had the
harness emitted one number, the mis-specified prediction would have silently
decided the verdict.

**The rule this produces:** a prediction must name the exact JSON field or
table column it resolves against, the exact comparison (which baseline, which
tolerance, and whether that tolerance is a registered band or a measured noise
floor), and it must be resolvable by someone who did not write it. "Within
+/-5%" is not a prediction until it says +/-5% OF WHAT, MEASURED HOW.

Corollary, learned the same night: when two instruments measure "the same"
thing, state which FIELD of each is the comparable one BEFORE running, because
after the fact every mismatch looks like a real disagreement. This is
`development-discipline.md`'s compare-like-for-like rule applied to
pre-registration rather than to measurement.

Evidence: results/experiments.md E32 + AMENDMENT 1; results/model-survey.md
Leg A disposition note. Status: ACTIVE - binds all future pre-registrations.

## F66 - cloud arms are NOT deterministic at temperature 0, so a single cloud number is a sample and F59 does not transfer

**Kind: METHOD**

**Status:** measured 2026-08-15, three replicate runs per model, E37.

**The claim it corrects.** F59 established that llama-server generation at
temperature 0 is BYTE-deterministic over 10 runs. That finding is about the
LOCAL stack and it was quietly being treated as a property of "temperature 0"
in general. It is not. Every cloud-vs-local comparison in this programme uses
cloud arms as the reference, so if the reference wobbles, the gap being
measured wobbles with it.

**Method.** `tools/run_ps_eval.py`, 20 questions, temperature 0, identical
prompts, one request per question. Three replicate runs per model through
OpenRouter, minutes apart, plus an earlier smoke run for `solar-pro4`.

**Result.**

| model | run 1 | run 2 | run 3 | answer TEXT differs on |
|---|---|---|---|---|
| `gemini-3.7-flash` | 20/20 | 20/20 | 20/20 | **8 of 20** questions |
| `upstage/solar-pro4` | 15/20 | 16/20 | 15/20 | **4 of 20** questions |

Two distinct failure modes, and the weaker model shows both:

- **Text instability with a stable score** (gemini). Answers reword freely -
  "Within 30 days of receipt." against "Invoices are payable within 30 days
  of..." - while every grade stays correct. Harmless for a grader that
  matches values; fatal for any grader that compares strings exactly, and
  worth knowing before anyone builds one.
- **Score instability** (solar). 16 in one run and 15 in two others. The
  score itself is a random variable.

**The sharpest single case.** Question C2 asks for FY2024 gross margin to one
decimal place; the exact value is 19.1748, so the answer is 19.2. Across four
runs `solar-pro4` returned **19.1%, 19.4%, 19.3% and 19.4%** - never the
right answer, and never the same wrong answer twice. A model that could not
do the arithmetic produced a different plausible number each time, which is
exactly the behaviour that makes a single-run benchmark misleading.

**What this changes, operationally.**

1. **Quote cloud arms as a range, never a point**, or state explicitly that a
   figure is one sample. A cloud reference arm reported as "16/20" carries an
   unstated +/-1 that a local arm does not.
2. **A local-vs-cloud gap below about 1 point in 20 is not resolvable** from
   single runs of each, because the cloud side's own spread is that wide.
   Gaps this small need replicates on the cloud side.
3. **The asymmetry is the trap.** Local runs at temperature 0 repeat exactly
   (F59), so it is natural to treat both sides as fixed values and compare
   them directly. They are not the same kind of measurement, and a comparison
   that treats them as such attributes the cloud provider's own variance to
   the local model.

**Not established:** the cause. Provider-side batching, mixed hardware,
speculative decoding and routing between backends would all produce this, and
nothing here distinguishes them. The operational consequence holds regardless
of which it is, so no time was spent separating them.

**Cost of establishing it:** $0.0009 per solar run and $0.0383 per gemini run,
six runs total - under $0.12 to convert an assumption into a measured bound.

## F67 - Qwen3.8-27B-Q4_K_M beats the workhorse on judged-free knowledge work by 6 of 20, and the whole gap is in the two hardest categories

**Kind: MODEL**

Status: confirmed (2026-08-15, E37, both arms local, llama-server b10435,
`-c 16384 -np 1`, temperature 0, `max_tokens 4096`, full-offload gate passing
on both, relay down throughout).

Every prior knowledge-work result in this repo (F34, F35, F37) is office
drafting scored by a frontier model acting as judge, so the ruler was itself
an unmeasured cloud model. E37 removes the judge: twenty questions over a
seeded six-document engagement pack, every answer checked by string or
numeric match.

| | Qwen3.8-27B-Q4_K_M | Qwen3-30B-A3B-2507 |
|---|---|---|
| correct /20 | **20** | 14 |
| citations valid /20 | 20 | 18 |
| over-claim rate (of 4 unanswerable) | 0.00 | 0.00 |
| retrieval /5 | 5 | 5 |
| supersession /4 | 4 | 4 |
| computation /4 | **4** | **1** |
| conflict /3 | **3** | **0** |
| unanswerable /4 | 4 | 4 |
| wall | 597.9s | **16.0s** |

**The gap is not spread across the eval - it is entirely in computation and
conflict.** The two models are identical on retrieval, supersession and
unanswerable (13/13 each). The workhorse then scores 1 of 7 on the two
categories that require arithmetic over a table and noticing that two
documents disagree, and Qwen3.8 scores 7 of 7. A single aggregate would have
reported "20 vs 14" and hidden the shape, which is the more useful fact: the
incumbent is not uniformly weaker, it is specifically unable to do the two
things a professional-services deployment is actually bought for.

**Neither model fabricated anything.** Both scored 4/4 on the unanswerable
items, so `over_claim_rate` - the metric this eval was built around, because
in advisory work a confident fabrication is a liability event while "not in
the pack" is a correct and billable answer - does not separate them at all.
That is a real result and it favours both models.

**The workhorse's failure mode is worth naming: it cited better than it
answered.** 18 valid citations against 14 correct answers. It found the right
clause and then misread it. The pre-registration predicted the opposite for
every arm (citations LOWER than correct, on the reasoning that sourcing is
harder than answering) and was falsified in both directions - equal for
Qwen3.8, inverted for the control.

**What this does NOT establish.** Qwen3.8 hit the ceiling. 20/20 fixes a
FLOOR for its knowledge-work ability and says nothing about where it fails,
so no claim about its capability limit may rest on this. The pack is ~2.7K
tokens, so this is not evidence about long context either. E38 exists to
find the ceiling; until it reports, "at least as good as the incumbent, by a
wide margin, on this task shape" is the whole of the claim.

**Cost is part of the verdict.** 37.4x the wall time for +6 correct. Whether
that trade is worth taking is a routing decision, not a benchmark result.

**CORRECTED 2026-08-15:** this finding first recorded the control's wall as
213.4s and the ratio as 2.8x. Both were wrong. The JSON says 16.0s and the
per-item times sum to 11.8s; 213.4 appears in no result file and I cannot
reconstruct its origin. The true ratio is 37.4x, so the original understated
the cost gap by more than an order of magnitude.

## F68 - an eval that executes model code must bound MEMORY, because the bound is part of the grade and not just a safety rail

**Kind: METHOD**

Status: confirmed (2026-08-15, measured through `run_candidate` at 15s wall /
4 GB `RLIMIT_AS`, while the GPU was busy so no bench figure is affected).

At 03:12 on 2026-08-15 the kernel OOM-killer took the overnight benchmark
with it: a validation subprocess reached 100,471,888 kB anon-rss running a
naive candidate that materialised an infinite generator. The fix applied at
the time - a 4 GB `RLIMIT_AS` and a wall timeout - went into the VALIDATOR
only. The runner that executes actual model output kept a wall clock and no
memory bound, one file away, for another six hours.

**The safety half is obvious. The grading half is not, and it is the finding.**
Two expert-tier tasks are gated on refusing to materialise a large structure.
Measured through the runner's own execution path:

| task | reference | naive |
|---|---|---|
| `interval_map` (30k intervals up to 100k wide over 10**9) | pass, 0.54s | error, 9.18s - 4 GB exhausted |
| `sliding_median` (N=250000, K=2500) | pass, 0.55s | timeout, 15.02s |

`sliding_median`'s gate is a clock and survives an unbounded runner.
`interval_map`'s does not. With no memory cap on a 128 GB box, the naive
per-integer dict does not fail - it allocates for minutes and either finishes
or takes the machine down. **An unbounded runner would have scored that naive
solution as a PASS.** The task would have looked satisfied while measuring
nothing.

**The general form.** Where a benchmark's difficulty is expressed as a
resource constraint, the enforcement of that constraint IS the test. A
timeout enforces time complexity; only an address-space limit enforces space
complexity. Writing the task and omitting the limit produces an eval that
reports a number and cannot justify it - and on a machine with 128 GB of
unified memory, the space gate is the one that silently stops working,
because there is enough RAM to let a wrong answer finish.

**Corollary for this repo.** Any harness that runs model-authored code needs
both bounds at every site, not at the site where the incident happened. The
03:12 OOM and the broken complexity gate are the same defect with two very
different symptoms - one loud and immediate, one silent and permanent.

## F69 - reasoning effort is a ROUTING AXIS, not a quality dial: on knowledge work there is no middle setting

**Kind: MODEL**

Qwen3.8-27B-Q4_K_M, L2 tier, 12 questions, one loaded model swept across all
four `reasoning_effort` levels at temperature 0 (E42 knowledge row). No
model-load variance is in the timing.

| level | correct | citations | completion tokens | wall | median/item | p95 | items <10s |
|---|---|---|---|---|---|---|---|
| off | 8/12 | 9/12 | 398 | 88.5s | 5.88s | 16.31s | 11 |
| low | 12/12 | 12/12 | 4,949 | 462.6s | 41.53s | 54.80s | 0 |
| medium | 12/12 | 12/12 | 6,052 | 552.2s | 42.44s | 81.08s | 0 |
| xhigh | 12/12 | 11/12 | 6,832 | 617.3s | 47.51s | 82.65s | 0 |

**The gap is discontinuous.** 8/12 at a 5.88s median, or 12/12 at 41.53s, and
nothing between. E42 registered in advance that a setting reaching >= 10/12 in
under 154s would exist; none did, and the registration stated what that
absence would mean - the guide must offer two modes rather than one
recommendation.

**What `off` actually loses is narrow and nameable:** `precedence` 2/2 -> 0/2
and `multihop` 3/3 -> 1/3. It KEEPS retrieval, effective-date reasoning,
revocation chains, and the refusal to fabricate (`over_claim` 0 at every
level). So the interactive mode is sound for lookup, extraction and
summarising, and unsafe wherever figures must be combined across documents or
a precedence rule applied.

**The quality plateau starts at `low`, and more reasoning is not monotonically
better.** `xhigh` - the chat template's DEFAULT - spent 38% more tokens than
`low` to reach the same score and produced a worse citation count (11/12
against 12/12). Maximum reasoning bought nothing on this task and cost a
citation. Anyone serving this model without setting the level explicitly is
paying the top price for the plateau.

**The owner's hypothesis (`medium`) and mine (`medium`) were both falsified
the same way.** `medium` does give full quality; it is not the cheapest point
on the plateau. `low` matches it on every quality field while using 18% fewer
tokens (4,949 against 6,052) and a p95 26.3s lower (54.80s against 81.08s).

**Margin, stated rather than buried:** the low-vs-medium median gap is 2%
(41.53 vs 42.44s), inside timing noise even though outputs are deterministic
at temperature 0 (F59). The recommendation rests on p95, token count and total
wall, which are larger and more robust than the median.

**Scope, and the reason this is not yet a general rule.** This is ONE task
shape (closed-record document QA) on ONE model. The E42 writing row diverges
from it - there, reasoning improved format compliance while introducing a
fabrication and dropping an unfavourable finding, which is the opposite
trade. Do not carry "low is enough" across task types without measuring;
carry the method - sweep the levels, because the template default is not the
best setting and the cheapest adequate level is task-dependent.

Evidence: results/experiments.md E42 + AMENDMENT 2 + knowledge-row RESULT;
results/raw/e42-20260815-know-{off,low,medium,xhigh}.json;
tools/analyse_thinking_matrix.py. Status: ACTIVE for knowledge work; the
cross-task generalisation is OPEN pending the writing and coding rows.


## F70 - temperature-0 determinism is SEQUENCE-scoped, not prompt-scoped

**Kind: METHOD**

A prompt does not have "the" temperature-0 answer on llama-server. It has one
answer per REQUEST SEQUENCE POSITION. E46 put a byte-identical prompt
(`prompt_tokens` 755 in every cell) at three positions and got three different
answers, then reproduced one of them exactly.

| m12 is request | completion tokens | seconds | answer sha256 |
|---|---|---|---|
| 1 of 1 | 3,645 | 301.0 | `23038d6b0a77bbfc` |
| 2 of 3 | 3,950 | 327.7 | `8b87187d40cabe0b` |
| 12 of 13 | 3,222 | 268.1 | `9979e5aa040e731b` |
| 12 of 13 (E43 arm B, days earlier) | **3,222** | - | **`9979e5aa040e731b`** |

**Mechanism.** llama-server reuses the KV-cache prefix it shares with the
preceding request, so how much of a prompt is recomputed - and in what batch
boundaries - depends on what was asked before it. Floating-point accumulation
is not associative, so a differently-chunked prefill produces marginally
different logits; at temperature 0 that is enough to flip one token, after
which the generations diverge.

**Nothing here is random.** Each sequence is individually reproducible, which
is why the 12-of-13 cell reproduced E43 arm B bit for bit across several days.
This does not contradict F59 - it scopes it. F59's determinism tests re-ran
whole sequences, and whole sequences do reproduce.

**The operational rule: an arm's request ORDER is part of its config.** Two
arms are comparable only if each prompt occupies the same sequence position in
both. E41's scale sweep and E43's four arms satisfy this by construction; that
was luck, not design, and it is now a thing to assert.

**What it cost before it was understood.** An E43-vs-E44 divergence on
identical prompts was nearly written up as a `-c` effect, and a second
near-miss blamed `max_tokens`. E44 arms A and B refuted both by being
byte-identical across a doubling of each. Two false findings avoided by
checking rather than concluding.


## F71 - on CODING, reasoning effort has an optimum in the MIDDLE, and the template's default overshoots it

**Kind: MODEL**

The counterpart to F69, and the opposite shape. On knowledge work more effort
is harmless; on coding maximum effort is actively worse than a middle setting,
and Qwen3.8's chat template resolves `reasoning_effort` to **xhigh when the
caller says nothing**.

**`interval_map`, one task, four settings** (E42 coding row + E44 arm C2):

| effort | budget | outcome | completion tokens | wall |
|---|---|---|---|---|
| off | 24,576 | timeout | - | - |
| low | 24,576 | truncated | 24,576 | 34m 43s |
| **medium** | **24,576** | **pass** | **14,916** | **20m 47s** |
| xhigh | 100,000 | truncated | 100,000 | **2h 46m** |

**The five "capped" coding tasks, at xhigh vs medium** (E44 arm C1 vs E47):

| | xhigh, 100,000 budget | **medium, 24,576 budget** |
|---|---|---|
| passed | 3/5 | **5/5** |
| completion tokens | 219,806 | **10,933** |
| wall clock | 5h 33m | **15m** |

**Two more correct answers for 20x fewer tokens and 22x less wall clock.**
`normalize_path` produced no code at all after 51,845 tokens at `xhigh` and
working code in 1,469 at `medium`. `roman_roundtrip` consumed a full
100,000-token budget without converging at `xhigh` and finished in 2,210 at
`medium`.

**This retracts a diagnosis that stood since 2026-07.** Those five tasks were
carried as "capped" and explained as a token-budget limit through three
successive budget raises (8,192 -> 24,576 -> 100,000). They were never
budget-limited. The last raise cost 5.6 hours to establish that maximum effort
cannot solve what a middle setting solves in fifteen minutes.

**Conditional tool use agrees** (E45): Qwen3.8 scores off 72%, low 78%,
**medium 86%** on 13 paired conditional tasks - the middle setting wins a
fourth time.

**Actionable line: serve this model for coding with `reasoning_effort: medium`
set EXPLICITLY.** The default is the setting that fails.


## F72 - the ~100K prefill wall is `n_ubatch`, and 128 is an OPTIMUM (AMENDED TWICE, 2026-08-17)

**Kind: PLATFORM**

**AMENDED THE DAY AFTER PUBLICATION. The original title claimed "this box
cannot prefill a ~100K-token request", and that is wrong.** It can. At
`-b 512 -ub 128` the same 118,911-token pack that died at n_tokens 96,286 with
stock flags completes with **12/12 correct and 12/12 citations**, and prefill
runs **up to 2.51x faster at matched depth** - 148.84 tok/s against 59.20 at
n_tokens 94,238, the deepest point both runs reached. The advantage is
DEPTH-DEPENDENT: 0.97x at 24,606 tokens, 1.90x at 65,566, 2.51x at 94,238.
(An earlier version of this amendment said "2.7x", from dividing rates taken
at two different depths. llama-server's prefill tok/s is a cumulative average
that declines with depth, so that comparison was not like-for-like.)

The failure below is real, reproducible, and will hit anyone who runs this
model at long context with stock settings, so none of the evidence is
withdrawn. What is withdrawn is the conclusion drawn from it. The wall is a
tunable.

**SECOND AMENDMENT, same day: E49 isolated which flag.** The first fix changed
`-b` and `-ub` together and could not attribute itself. A 2x2 on the same pack
settles it - throughput compared at matched depth (n_tokens 94,238), survival by
`transport_failed` count:

| `-b` | `-ub` | survived | tok/s @94,238 |
|---|---|---|---|
| 2048 | 512 | **no**, lost at 96,286 | 59.20 |
| 512 | 512 | **no**, lost at 109,598 | 63.13 |
| 2048 | 256 | yes | 105.60 |
| **2048** | **128** | **yes** | **147.97** |
| 512 | 128 | yes | 148.84 |
| 2048 | 64 | yes | 127.53 |

**`-ub` is causal; `-b` does nothing.** Varying `-b` 4x moves throughput 0.6% at
`ub=128` and 6.6% at `ub=512`. Varying `-ub` moves it 2.50x and decides whether
the run survives at all.

**128 is an OPTIMUM, not a floor.** `-ub 64` is *slower* than `-ub 128` (127.53
against 147.97), so throughput falls off on both sides. Do not read this as
"smaller is safer".

**The two deaths landed at different depths** - 96,286 and 109,598, both at
`ub=512` - which is what a pressure threshold does and what a fixed limit does
not.

**Operational line: serve long context with `-ub 128`.** That is established.
The working-set account that explains it is a hypothesis; no allocation was
measured, and confirming it needs VRAM instrumentation this harness does not
collect. The optimum is also specific to this model, build and driver - F10's
discipline says architecture-dependent numbers do not transfer.

**Extended the same day: the fix scales.** The 236,122-token rung - 90% of the
model's trained 262,144, the one that died at n_tokens 110,622 with stock flags
- also completes at `-b 512 -ub 128`, scoring **12/12 with 11/12 citations**.
So the wall is not merely pushed back; it is absent across everything this
corpus can build.

Note the direction of the correction: **faster AND more stable together.**
There is no throughput-for-survival trade, which means a dispatch-duration
watchdog does not explain it - a watchdog story predicts the safe setting is
slower. Memory pressure at `-ub 512` is the obvious candidate and E49 is
registered to separate `-b` from `-ub` and test it, because arm B changed both
flags and so cannot attribute its own result.

**Original finding, kept as recorded:**

A single-request context ceiling that has nothing to do with the model's
trained 262,144 and is not visible in any KV-memory calculation.

| E48 rung | prompt tokens | result | died at n_tokens |
|---|---|---|---|
| n=9 | 21,228 | 12/12 correct | - |
| n=29 | **60,315** | **12/12 correct** | - |
| n=59 | 118,911 | GPU device lost | **96,286** |
| n=119 | 236,122 | GPU device lost | **110,622** |

```
radv/amdgpu: The CS has been cancelled because the context is lost.
ggml_vulkan: device lost on Vulkan0
terminate called after throwing an instance of 'vk::DeviceLostError'
```

**It is not out of memory.** `-c 262144` allocated successfully in both failing
runs, and the n=29 rung ran clean at that same `-c`. **It is not the
suballocator deadlock** of `docs/memory-edge-deadlock.md` either - the box did
not wedge, the process died cleanly, and five further runs completed after it.
The two crash points differ by 14,336 tokens, which is the signature of a
driver-level compute cancellation rather than a fixed limit.

**Prefill runs at 49.57 tok/s at this scale**, so 110,000 tokens is 37 minutes
before the first output token. Even fixed, single-request packs of that size
are not a practical working mode here.

**Measured, not inferred, and it must never be scored as a capability
failure.** All twenty-four questions in the two failing rungs are
`transport_failed`. Recording them as 0/12 would be F20 at a scale nobody
would catch by eye.

**What is safely established: zero degradation out to 60,315 tokens** - a
folder of thirty competing agreements, 273,000 characters, 12/12 correct with
12/12 correct citations. Untested batch-size mitigation (`-b`/`-ub`) is the
next thing to try before concluding the ceiling is permanent.


## F73 - a 3-task category produced a published recommendation that INVERTS at 13 tasks

**Kind: METHOD**

The routing guide told readers to use Mistral-Small-24B for any tool call whose
behaviour depends on a condition, and called that "the one place the workhorse
is unsafe". E45 expanded the conditional category from 3 tasks to 13 paired
ones and the ranking turned over.

| arm | 3-task category (E33) | **13-task category (E45)** |
|---|---|---|
| Mistral-Small-24B | **~100%, "the champion"** | **38% - the WORST arm** |
| workhorse (Qwen3-30B-A3B) | "UNSAFE" | **68%** |
| Qwen3.8 `medium` | not measured | **86%** |

Zero format leaks in all 325 runs, so nothing here is a harness effect.

**Why the small sample lied.** E33's category was c1-urgent, c2-not-urgent and
c3-vat. Mistral scores 5/5, 4/5 and 5/5 on exactly those. The 2026-08-16
expansion added category routing, tool selection and compound conditions -
**Mistral scores 0/5 on all six of them**, while the Qwen family and the
workhorse score 5/5. The recommendation was built on the three tasks the
recommended model happens to be good at.

**The original observation was CORRECT and is not retracted.** The defect E33
named - applying a conditional flag unconditionally - is still visible in the
c1/c2 pair, and Mistral is still the only model that correctly withholds the
flag on the false branch (4/5, against 0/5, 1/5 and 2/5 for the Qwen arms and
0/5 for the workhorse). A sound inference from a sample too small to carry the
weight put on it is a different failure from a wrong inference, and it is the
more dangerous one, because nothing about the original analysis looks wrong.

**The general rule this buys.** A category with three items moves 33 points per
item. Any per-category recommendation resting on fewer than about ten items is
a hypothesis, not a finding, and must be labelled as one in anything
client-facing. The guide row has been corrected in place rather than removed,
with the date and the reason on the row.

**The blind spot, correctly characterised.** `c5-date-after` is failed by every
model tested, best 1/5, while its pair `c4-date-before` is passed 4/5 by
Qwen3.8 at `medium`. That is NOT a date-comparison problem. The two tasks carry
the *same* rule ("if completion falls before 1 October 2026, mark it EXPEDITED")
and differ only in whether the rule fires. The model applies the flag
unconditionally, so it passes the branch where the flag belongs and fails the
branch where the correct action is to do nothing - the same defect as the
`c1`/`c2` pair, with a date predicate instead of a numeric one. **The negative
branch is the failure, in every predicate type tested.**


## F74 - retrieval under scale is a MEASURED STRENGTH: 12/12 at 90% of trained context, with no boundary anywhere below it

**Kind: MODEL**

Three successive experiments were designed to find the size at which this model
starts answering from the wrong document. None of them found it. The ladder is
now complete to the largest pack the corpus can build.

| Prompt tokens | Agreements in the folder | `correct` | `citation_valid` |
|---|---|---|---|
| 3,675 | 1 | 12/12 | 12/12 |
| 21,267 | 10 | 12/12 | 11/12 |
| 60,354 | 30 | 12/12 | 12/12 |
| 118,911 | 60 | 12/12 | 12/12 |
| **236,122** | **120** | **12/12** | **11/12** |

Qwen3.8-27B-Q4_K_M, `thinking=low`, temperature 0, `-c 262144`,
`-b 512 -ub 128` above 60K (see F72). The twelve questions are derived in code
from the L2 set so they cannot drift, and the distractor agreements draw their
figures from ranges disjoint from the real pack - asserted at import - so an
answer taken from the wrong contract is identifiable rather than merely wrong.

**Zero `wrong_document` outcomes at any size.** 64x the smallest pack, 120
near-identical services agreements between the same client and 119 different
suppliers, each with its own retainer, cap, notice period and retention rule,
and it never once reported a figure from the wrong one.

**E41's registered falsifier has now fired at 90% of trained context.** It said
that if `correct` at the largest scale equals `correct` at the smallest, scale
is not a boundary. It does, at every rung. The correct report is no longer "the
boundary has not been found" - it is that this is a strength, and the routing
guide should say so plainly.

**The control degrades where this does not.** The incumbent workhorse over the
same span goes 5/12 to 4/12, and fails the same two categories at both ends -
so it is not degrading under scale so much as failing the reasoning regardless
of it (F67).

**The cost, which is the part that decides whether it is usable.** The first
question on the 120-agreement pile takes **71.7 minutes** because it prefills
the whole pack; the remaining eleven average **94.9 seconds** off the cached
prefix. A **45:1** ratio between the first question and the rest. This is a
load-once-then-interrogate tool, not a one-question tool, and F31 measured the
same shape four times shallower.

**What is NOT established.** 236,122 is the largest pack this corpus can build,
not a measured ceiling - the remaining 26,022 tokens of trained context are
untested, and after this prompt plus its generation `-c 262144` leaves only
21,926 tokens of headroom. Testing further needs a larger corpus and a model
with more trained context than we can already fill.


## F75 - request order changes the WORDING and not the ADVICE: 13/13 stable, 59/65 three times over

**Kind: METHOD**

F70 established that a byte-identical prompt gives a byte-different answer
depending on how many requests preceded it. That is reproducibility. F75 is the
reliability question a firm would actually ask: **if I ask the same matter twice
in a session, do I get the same advice?**

Thirteen closed-record advisory matters, asked in three different orders -
sorted, reverse, and a 7-rotation - with nothing else changed. Qwen3.8-27B at
`thinking=low`, temperature 0.

| field | result |
|---|---|
| Same score at every position | **13/13** |
| Same MISSED ELEMENTS where imperfect | **13/13** |
| Same traps (none reproduced) | **13/13** |
| Run totals | **59/65, 59/65, 59/65** |

**The missed-element check is the one that matters**, and it was added before
the results were read. Two runs can both score a matter 4/5 while missing
*different* elements - the same number and different advice. They did not: the
five imperfect matters are imperfect in exactly the same way at every position.

**Meanwhile the wording does move.** 7 of 13 matters produced at least two
distinct answers across the three orders; 6 were byte-identical everywhere; one
produced three different answers. So F70's effect is real but is a **minority**
effect - the pre-registered prediction that at least 10 of 13 would differ at
all three positions was falsified, and it had been inferred from a single
matter.

**The operational reading.** Prose varies, substance does not. You cannot expect
a byte-identical report from a re-run, and you can expect the same answer. For
advisory use that is the right way round.

**Scope.** One model, one effort level, one corpus, three orderings, 39
matter-runs. It does not establish that no ordering can change an answer, only
that none of the three tested did.


## F76 - the tool-use instrument is 5 runs at temperature 0.2, so intermediate per-task scores do NOT reproduce between sessions

**Kind: METHOD**

`tooluse_harness_v2.py` fixes `temperature` at 0.2 and `runs` at 5. Both are
deliberate - it keeps every E33-lineage figure comparable, and the file says so
at the call site. The consequence was never characterised until E50 re-ran the
thirteen unchanged conditional tasks in a fresh session.

| task | E45 | E50 | delta |
|---|---|---|---|
| c4-date-before | 4/5 | **1/5** | **-3** |
| c11-compound-one | 5/5 | 4/5 | -1 |
| c2-not-urgent | 2/5 | 3/5 | +1 |
| c5-date-after | 0/5 | 1/5 | +1 |
| the other nine | 5/5 | 5/5 | **0** |

**Four of thirteen moved, and they are exactly the four not at a ceiling.** The
nine tasks scoring 5/5 reproduced perfectly. The workhorse, whose every task
sits at 0/5 or 4-5/5, moved on **none** of thirteen and reproduced its mean
exactly at 68%.

That is the signature of binomial sampling, not of model drift: at n=5 an
intermediate rate carries a standard error of about one run, while a rate at 0
or 1 carries none.

**Means are usable; single cells are not.** Over the same 13 tasks Qwen3.8 went
86% -> 83% and the workhorse 68% -> 68%. Any claim about the ORDER of models
survives. Any claim of the form "this model scores 4/5 on this task" is one
sample of a noisy quantity.

**This retroactively weakens per-task claims published on 2026-08-16**, when
c4-date-before at 4/5 and c5-date-after at 0/5 were put into two guides as
properties of the model. c5 has since scored 0/5, 1/5 and 2/5, and the workhorse
scored 5/5 on its "only if" variant. The guides are corrected; the model
RANKING they carry is unaffected.

**Fix, not yet run:** a powered design - more runs, or temperature 0, or both.
Registered as E53. Raising runs breaks comparability with every E33-lineage
number, which is exactly why the constant was fixed in the first place, so the
new design has to carry both.


## F77 - a 4.68 GiB model does the document work; what it needs is REASONING, not parameters

**Kind: MODEL**

E52 ran Qwen3-8B-Q4_K_M on the sealed-key instruments the 24B+ models were
measured on. It is the smallest model this programme has put to a capability
question, and it does not behave like a weak one.

| instrument | **Qwen3-8B 4.68 GiB** | workhorse 30B-A3B **17.28 GiB** | Qwen3.8-27B 15.66 GiB |
|---|---|---|---|
| L1, 20 questions | **16/20** | 14/20 | 20/20 |
| L3 n=0, 12 questions | **11/12** | 5/12 | 12/12 |
| L3 n=9, 12 questions | **10/12** | 4/12 | 12/12 |
| L3 n=14, 12 questions | **11/12** | not run | not run |

It beats a model 3.7x its size by 5 to 6 points on the harder tier, and gives
up 1 to 2 against one 3.34x its size. On L1 it is **2.32x faster than the 27B**
and **16.1x slower than the workhorse**.

**The reasoning dependency is the whole story, and it is bidirectional.** The
same model, the same instrument, `enable_thinking` the only variable:

| L1, Qwen3-8B | `correct` | computation | conflict | wall | median |
|---|---|---|---|---|---|
| thinking ON | **16/20** | **4/4** | 0/3 (all `partial`) | 258.0s | 8.95s |
| thinking OFF | **12/20** | **0/4** | 0/3 (one `wrong`) | **20.5s** | **0.79s** |

Turning thinking off does not degrade it evenly - **all four arithmetic items
flip correct to wrong**, and the one conflict it had judged correctly is missed
outright. It costs 4 points and buys a factor of **12.59** in wall time, and it
moves the model from **above** the 30B MoE to **below** it.

**So the deployment rule is not "small models are worse".** It is: an 8B with
its reasoning on is a credible document-work model and an 8B with it off is
not, and the two configurations of one artefact sit on opposite sides of a
model 3.7x its size. Anyone quoting a small-model score has to say which one
they measured.

**Two honest limits on this finding.**

1. **It is not a size isolation.** The 8B is `arch=qwen3`, the 27B is `qwen35`,
   the workhorse is a 30B MoE with 3B active. Size, generation and architecture
   move together. This answers a deployment question, not a scaling-law one.
2. **The speed figures are this GPU's.** The artefact fits a laptop's memory;
   the throughput was not measured on a laptop and does not transfer.

**And one hard ceiling that no score can improve.** `n_ctx_train` is **40,960**
against the 27B's 262,144, a factor of **6.4**. F74's 12/12 at 236,122 tokens is
not a result this model fails - it is a run it cannot attempt. E52's ladder was
flat out to 30,039 measured tokens (73.3% of trained context) with 11/12, so
within its envelope it does not degrade; the envelope is simply six times
smaller.

Evidence: `results/experiments.md` E52, `results/raw/e52-20260817-8b-*.json`.


## F78 - naming the document and the party in the question is worth 2 of 12 to a small model, and INVISIBLE on a large one

**Kind: METHOD**

E52's L2 arm scored 9/12 with 3 `truncated`; the L3 n=0 arm scored 11/12 with
none. The two use a **byte-identical 13,221-char pack**, and the config table
called them the same instrument.

They are not. `prompt_tokens` differs on 11 of 12 questions. `QUESTIONS_L3`
restates every `QUESTIONS_L2` item naming the agreement and the party in full -
*"Under the Master Services Agreement dated 1 March 2024 between Northwind
Logistics Limited and Calderwood Advisory LLP, as amended, what monthly
retainer..."* against *"What monthly retainer was payable...?"* - because a
terse question goes ambiguous once the pack holds 119 similar agreements. Only
`N1` is word-for-word identical. `validate_ps_eval_l3.py` asserts equality of
the REASONING and the KEYS, not of the question text.

**The effect is not a scoring nicety - it is runaway reasoning.** On the terse
phrasing, three questions burn the entire 4,096-token budget and emit no
answer. On the specific phrasing, the same three questions on the same pack
finish correctly:

| question | terse (L2) | specific (L3 n=0) |
|---|---|---|
| D2 | `truncated`, 4,096 tokens | correct, 1,510 tokens |
| P1 | `truncated`, 4,096 tokens | correct, 782 tokens |
| P2 | `truncated`, 4,096 tokens | correct, 736 tokens |

**`-c` was the first hypothesis and it is wrong.** The two arms also differed in
`-c` (16384 vs 32768). Arm 8 re-ran L2 at `-c 32768` with one variable changed:
**9/12, the same three truncations, and all twelve answers byte-identical
including `completion_tokens` to the token.** A doubling of `-c` leaves
temperature-0 output bit-for-bit unchanged, reproducing E44 arms A and B on a
second model and a different architecture.

**Why it went unseen for two days.** The 27B scored 12/12 on both phrasings
(E38 and E41 n=0), so the confound has been in the instrument since 2026-08-15
and could not show up until a model small enough to be moved by it was run.
**An instrument two models both saturate cannot reveal its own confounds.**

**The operational rule:** in a retrieval-over-a-folder prompt, name the
governing document and the party in the question. It costs nothing, it is worth
2 of 12 on an 8B, and the cost of not doing it is not a wrong answer - it is no
answer at all.

Evidence: `results/experiments.md` E52 Amendment 1,
`results/raw/e52-20260817-8b-l2.json` vs `-l2-c32768.json` vs `-l3-n0.json`.


## F79 - a correct citation is NOT evidence of a correct answer

**Kind: METHOD**

E52 registered `citation_valid` at or below `correct` on every arm, on the
reasoning that finding the answer and naming where it came from are different
capabilities and citation is the harder one. **It is above `correct` on 5 of 8
arms.**

| arm | `correct` | `citation_valid` |
|---|---|---|
| L1 thinking on | 16/20 | **19/20** |
| L1 thinking off | 12/20 | **17/20** |
| L3 n=0 | 11/12 | **12/12** |
| L3 n=4 | 10/12 | **11/12** |
| L3 n=9 | 10/12 | **11/12** |
| L3 n=14 | 11/12 | 9/12 |
| L2, both `-c` | 9/12 | 9/12 |

The model finds and names the right clause, then gets the answer wrong out of
it. The clearest instance is L1's conflict category: on all three questions it
answered `NO` - the correct judgement - and put the two figures the question
asked for into the `CITATION:` line instead of the `ANSWER:` line. X2's citation
reads *"calculated 19.57% vs noted 21.4%"*, which is the graded answer, in the
wrong field. Scored `partial` 3/3, against the workhorse's 2 `partial` and 1
`wrong`.

**Why this matters commercially.** A citation requirement is normally added to
catch the model that invents an answer with no source. On this model the failure
runs the other way: the source is right and the answer drawn from it is not, so
**a checkable citation next to a wrong answer is the more dangerous artefact** -
it invites a reviewer to spot-check the reference, find it genuine, and accept
the number. The review procedure that follows is to check the ANSWER against the
cited clause, not to check that the clause exists.

Evidence: `results/experiments.md` E52 prediction 5,
`results/raw/e52-20260817-8b-*.json`.


## F80 - what the small local models cannot do is WALK A CALENDAR, and nothing else measured separates them

**Kind: MODEL**

E54 put fifteen questions to three models over one pack: statutory periods,
engagement terms, and adversarial "what is wrong with this contract". Split
them into the ones that require **counting a period across a calendar** and the
ones that do not, and the instrument resolves into two different tiers.

| | walked periods | static analysis |
|---|---|---|
| Qwen3.8-27B `low` | **6/7** | 7/7 |
| Qwen3-8B, thinking on | **4/7** | 7/7 |
| Qwen3-30B-A3B (workhorse) | **0/7** | 6/7 |

**The static half separates nothing.** All three models find the clause that is
missing from a subcontract, compute the shortfall between two figures in two
different documents, correctly decline to call two out-of-scope mismatches a
breach, and read a survival clause. The 30B MoE workhorse scores 6 of 7 there.

**The walked half separates completely, and the workhorse gets NONE of it.**
Not one deadline, not one interest calculation, not one notice period. It
answered 30 October for a one-month statutory period, 2 March for a six-year
limitation date, and EUR 107.56 for an interest computation whose answer is
EUR 493.99.

**This is F60 reproducing in a domain it was not derived from.** F60 came out
of thirteen closed-record legal matters and predicted that a second BASIS to
select does not discriminate while a period that must be WALKED does; its
closing instruction was to build the next corpus on counted periods. E54 is a
different domain, a different pack, different question types and one model F60
never saw, and the mechanism holds exactly.

**The deployment instruction, which is sharper than any total:** *use the
workhorse to read a contract; do not use it to work out a deadline.* L2 and L3
already said it scored 5/12 and 4/12 without saying what it was failing at. It
is failing at dates and money over time, and at nothing else measured here.

### Two failure shapes worth carrying

**Composition, not retrieval.** Asked for the date a termination notice
actually takes effect, the 27B and the 8B **both** answered 1 December 2026:
each found the clause saying notice may not take effect before the first
anniversary, applied it, and dropped the clause requiring effect on a month
end. The answer is 31 December. Both scored the paired question - the same
matter with the anniversary clause explicitly disregarded - correct. So neither
model failed to FIND either rule. Both failed to **compose two constraints they
had each already satisfied individually.** That is a different defect from
missing a document, and it is invisible in a retrieval-shaped test.

**The instrument's own diagnostic undercounts, and the count is a floor.**
E54 registered `off_by_calendar` at >= 2 for Qwen3.8 and measured **1**, which
falsifies the prediction. But the trap lists carried the errors that were
predicted - suspending a 72-hour clock over a weekend, rolling past a public
holiday - and not the one that actually occurred, a plain off-by-one in day
counting that two models produced and that graded as a generic `wrong`. **Read
`off_by_calendar` as a floor on calendar errors rather than a count of them.**
The walked-versus-static split above is the sound version of the same claim and
does not depend on the trap lists being complete.

### One question was withdrawn, and the withdrawal changes nothing

`F1` carried two conflicting specifications - derive the period, and here is
the period - so a model that derived and a model that read got different
answers and both were defensible. It is withdrawn rather than explained after
the fact; an ambiguous question scored as a capability failure is F20, which
this programme has caught in other instruments twice. Totals restated on 14.
**The ordering and every gap are unchanged**, which is the test of whether a
withdrawal is honest or convenient.

Evidence: `results/experiments.md` E54, `results/raw/e54-20260817-*.json`,
instrument in `spikes/ps-eval/{corpus_l4,questions_l4}.py` with
`tools/validate_ps_eval_l4.py` at 21/21.

### F80 AMENDMENT 1 (2026-08-17, same day): the finding is TIERED, and E54's "floor" claim is withdrawn

F80 above was written from E54's first run, on an instrument carrying a
defective question. E54b repaired it and re-ran, and two things change.

**1. The headline claim is withdrawn.** E54's registered falsifier said that a
score of 14 or 15 means L4 has not found the frontier. On the repaired
instrument **Qwen3.8-27B scores 14 of 15**, so it fires: **L4 does not bound
this model.** The 13/15 that made E54 report a floor was partly produced by my
own ambiguous question - with it rewritten, the model answers correctly.

Worth naming because the guards this programme runs all point the other way:
**an instrument defect can manufacture a POSITIVE result as easily as a
negative one.** F20 and E48's distractor check both guard against a defect that
makes a model look WORSE. This one made a model look BOUNDED, and no score
could reveal it - only repairing the question and re-running did.

**2. "Small models cannot walk a calendar" is right for the workhorse and wrong
for the 27B.** With the repaired question valid, the split runs over eight
walked items rather than seven:

| | walked periods | static analysis | total |
|---|---|---|---|
| Qwen3.8-27B `low` | **7/8** | 7/7 | 14/15 |
| Qwen3-8B, thinking on | 5/8 | 7/7 | 12/15 |
| workhorse 30B-A3B | **0/8** | 6/7 | 6/15 |

**The failure moves up the tiers rather than existing at one.** The workhorse
cannot count time at all - zero of eight, while scoring 6 of 7 on reading the
contract. The 8B counts it unreliably. The 27B counts it well and its **single
remaining miss in the entire tier** is `N2`, the composition question: it finds
the clause blocking a notice before an anniversary, applies it, drops the clause
requiring a month end, and answers the paired question - the same matter with
the first clause disregarded - correctly.

**So the deployment instruction in the routing guide stands unchanged** (use
the workhorse to read a contract, never to work out a date), because it is about
the workhorse and that is exactly the model the 0/8 describes. What changes is
the claim about the top model: its frontier is not calendar arithmetic, it is
**composing two constraints it has each already satisfied.**

**One more result, and it is the most reusable thing here.** Across all three
arms and all fourteen unchanged questions, **not one answer string changed
between E54 and E54b.** The only outcome differences are a byte-identical
answer being re-graded by a newly added trap. At temperature 0, same config,
same sequence position, this tier is fully reproducible - so F70's sequence
effect does not reach it, and every per-question cell here is a real
observation rather than one draw from a noisy quantity. That is what makes the
single-miss claim about `N2` sayable at all.

Evidence: `results/experiments.md` E54b, `results/raw/e54b-20260817-*.json`.


## F81 - these models do NOT agree with a confident user, and the composition failure survives a conversation intact

**Kind: MODEL**

E55 is the first conversation this programme has measured: 16 turns, 11 graded,
over the same L4 pack, with three graded turns byte-identical to questions E54b
had already measured standalone on the same three models.

**Nothing failed at being a conversation.**

| | Qwen3.8-27B | Qwen3-8B | workhorse 30B-A3B |
|---|---|---|---|
| `correct` | **10/11** | 8/11 | 6/11 |
| `accepted_false` | **0/2** | **0/2** | **0/2** |
| `stale_answer` | 0 | 0 | 0 |
| `over_revised` | 0 | 0 | 0 |

**No arm adopted a false premise.** Two were planted, each with a reason to
agree. One attributed a figure to the model that it had never given - EUR 1.65
million - and said it was going to a client that afternoon; all three answered
EUR 650,000. One asserted a 60-day statutory payment period against a document
stating thirty; none adopted it. The workhorse's single false-premise miss is
`wrong`, not `accepted_false` - it answered a date that is neither correct nor
the one asserted. **It did not agree with me. It miscounted.**

**No arm went stale and no arm over-revised.** All three applied a correction
that moved a deadline, and all three declined to move an answer when two
irrelevant facts arrived. Two registered predictions - that the workhorse would
produce at least one stale answer, and that at least one over-revision would
appear across three arms - are falsified in the same direction: **every model
handled the conversation better than predicted.**

### And yet the same question fails, for the fifth and sixth time

`T02` is byte-identical to L4's `N2`. Qwen3.8-27B and Qwen3-8B both answered
**1 December 2026**, the same wrong date each gave standalone in E54 and again
in E54b.

Six observations, two models, two presentations, one wrong answer. **The
composition failure is not an artefact of how the question is presented.** In a
conversation carrying two corrections and two false premises - all handled
correctly - the model still finds the clause blocking a notice before an
anniversary, applies it, and drops the clause requiring effect on a month end.
It answers the paired question, the same matter with the first clause
disregarded, correctly every time.

**So the deployment picture is not "watch it in conversation".** These models
track a conversation reliably at this length. What they cannot be trusted with
is a question whose answer requires two constraints applied together, and that
is true whether it is asked alone or in the middle of a discussion.

### The one real cost a conversation imposed

**The 8B truncated twice at `max_tokens 4096`, on turns it completed
standalone.** A conversation gives a small model more to reason over before it
answers. That is a budget finding rather than a capability one, and it means the
8B's 8/11 understates it - but it is also an operational instruction: **raise
the answer budget for a small model used conversationally**, or its failures
will be mechanical and will read as capability.

### What this does NOT establish, stated because it will otherwise be over-read

**The conversation is short.** Its final history is **3,834 tokens, 12% of the
`-c 32768` it ran in.** F81 measures whether these models track corrections,
resist a confident user, and reach back a dozen turns for a fact, in a
conversation that comfortably fits. It says nothing about a long conversation,
about context pressure, or about decay over dozens of turns. **A
long-conversation tier is a different experiment and has not been run.**

### F80 refinement

The workhorse answered a one-month period walked from a **corrected** date
correctly (20 February to 20 March) while failing the same rule from a different
start (31 January to 28 February). The difference is whether the month's LENGTH
matters. So F80's "cannot walk a calendar" is better stated as: **it fails the
walks that need the calendar rule and passes the ones that need only
arithmetic.**

Evidence: `results/experiments.md` E55, `results/raw/e55-20260817-*.json`,
instrument in `spikes/ps-eval/{conversation_l4,grade_multiturn}.py` with
`tools/validate_multiturn.py` at 26/26.

## F82 - a conversation at 75% of context does not decay, and what depth actually costs is the weakest model's resistance to a confident user

**Kind: MODEL**

E55 measured a conversation and found nothing wrong with it, then said in terms
what that did not cover: its history ended at **3,834 tokens, 12% of `-c
32768`**, so it spoke to conversation MECHANICS and not to LENGTH. Every
commercial worry about a local model in advisory use is about length - the
session that has been running all afternoon. E56 ran the same probes over the
same pack at **71-76% of context**, 6.5 to 6.9 times deeper.

### The measurement is PAIRED, which is why it can say anything at all

Five questions were asked twice, **byte-identically**: once early, once after
ten services agreements and roughly twenty thousand tokens of intervening
advisory material. Comparing E56 to E55 would compare runs differing in a dozen
ways; comparing a question to ITSELF inside one conversation isolates depth, per
model. `tools/validate_conversation_long.py` asserts the two asks are
byte-identical and carry the same answer, because that claim lives entirely in
the construction of the turn list.

### 15 of 15 anchors held, and every deep answer was byte-identical to its shallow one

| | anchors degraded | `accepted_false` | `stale` | `over_revised` | `wrong_document` | final history |
|---|---|---|---|---|---|---|
| Qwen3.8-27B `low` | **0 of 5** | **0/2** | 0 | 0 | 0 | 24,754 (75.5%) |
| Qwen3-8B | **0 of 5** | 1/2 | 0 | 0 | 0 | 23,277 (71.0%) |
| workhorse 30B-A3B | **0 of 5** | 1/2 | 0 | 0 | 0 | 23,247 (70.9%) |

Not one anchor degraded on any arm, and in all fifteen pairs the deep answer
string matches the shallow one character for character - including the wrong
ones. The workhorse returned `31 October 2026` and `1,045.54` at both depths,
twenty thousand tokens apart. Retrieval, arithmetic and an early correction all
survive intact.

**Ten structurally parallel agreements produced ZERO wrong-document answers on
every arm**, the conversational analogue of F74's zero `wrong_document` at
236,122 tokens. A registered prediction of at least one across the three arms
combined was falsified.

### THE LIMITATION, which must be read with the result and not after it

**This design cannot separate "held the answer" from "re-derived the answer",
because the model's own earlier reply sits in the history it is re-sent.** An
anchor asked twice has its first answer in front of it, so holding it may be
recall rather than reasoning, and the byte-identical repeats are consistent with
either. E54b's lesson is that an instrument defect can manufacture a POSITIVE
result as easily as a negative one, and this design makes the optimistic reading
the easy one.

Two parts of the run are not subject to it and carry the real evidence that
depth is survivable: the `recent` probes scored **5/5 on every arm**, each about
an agreement delivered moments earlier and never previously discussed, the last
at 22,778-24,117 tokens; and `T29` is a question never asked shallow, derived at
the deepest point of the conversation. **The clean follow-up is a held-out tier
- questions over the same pack asked ONLY at depth.** Not run, not claimed.

### What depth DID cost, on one model and one probe

E56's `T29` and E55's `T16` are byte-identical, setup included: the user asserts
a sixty-day statutory payment period where the record says thirty in terms.

- **Qwen3.8-27B: `correct` at 3,834 tokens, `correct` at 24,754** - byte-identical answer.
- **Qwen3-8B: `correct` at 3,384 tokens, `correct` at 23,277** - byte-identical answer.
- **workhorse: `wrong` at 3,417 tokens, `accepted_false` at 23,247.**

**State this precisely, because the obvious reading is wrong.** The workhorse did
not go from resisting to adopting: it was never correct here. What changed is the
SHAPE of the error - an unrelated wrong date shallow, and at depth a wrong answer
sitting exactly on the figure the user asserted. That is the failure that costs
money, and depth is what moved it there.

The 8B also produced one `accepted_false`, abandoning the EUR 650,000 it had
itself given for the user's EUR 1.65 million. **That one is not a clean depth
comparison** - its question differs from E55's by four words, added to make the
anchor self-contained - so it is an E56-internal observation only.

### The deployment instruction

For the two capable models, **length is not the risk**, and the F74 advice to
load once and interrogate carries into a conversation. What does not change with
depth is the thing already in the routing guide: **check any answer that depends
on two rules at once.** T02, byte-identical to L4's `N2`, drew `1 December 2026`
from both capable models for the seventh and eighth time across three
experiments and two presentations, and is the 27B's only miss in the tier. It
has never moved.

For the workhorse, the instruction is stronger and is new: **do not run it in a
long advisory conversation where the user asserts figures.** It holds its
answers fine; what it loses at depth is the ability to contradict you.

Evidence: `results/experiments.md` E56, `results/raw/e56-20260817-*.json`,
instrument in `spikes/ps-eval/{conversation_long,grade_multiturn}.py` with
`tools/validate_conversation_long.py` at 59/59. Six of eight registered
predictions held; both falsifications were the models beating the band, the
eleventh time in this programme. Neither registered falsifier fired.

## F83 - held out from its own answer, the strong model does not decay at depth and the small one does

**Kind: MODEL**

E56 reported that no arm degraded across a conversation reaching 75% of context,
on a paired design: five questions asked twice, byte-identically, twenty thousand
tokens apart. Its own write-up named the limitation - the model's earlier reply
sits in the history it is re-sent, so "held the answer" and "re-read the answer"
cannot be separated. E57 removes that by asking every graded question **exactly
once per run**, paid for with a crossover: two disjoint sets of five over the
same L4 pack, run in both orders, byte-identical middle.

| | standalone (E54b) | shallow | deep | degraded | `recent` |
|---|---|---|---|---|---|
| Qwen3.8-27B `low` | 10/10 | **10/10** | **10/10** | **none** | 6/6 |
| Qwen3-8B | 9/10 | 9/10 | **6/10** | **4** | 6/6 |
| workhorse 30B-A3B | 5/10 | 3/10 | 5/10 | none | 6/6 |

**For the 27B, E56's result survives untouched** - and all ten of its answers are
byte-identical between two SEPARATE runs and processes, asked at turn 3 in one
order and turn 16 in the other, which E56's design could not have shown.

**For the 8B it does not survive.** 5 of 5 anchors held in E56; 6 of 10 held-out
questions here. **F82's "no arm degraded" is therefore AMENDED for the small
model** - anyone quoting E56 for an 8B-class model must quote this instead.

The 8B's mechanism is in the token counts rather than inferred: `F1` correct in
**558** generated tokens shallow, **truncated at the 5,120 ceiling** deep with
13,891 characters of reasoning. It reasons more at depth and lands worse.
Counted honestly that is 3 degradations and 1 budget exhaustion, not 4
capability failures.

The workhorse improved (3/10 -> 5/10) and nothing should be read into it: its
shallow arm is below its own standalone 5/10, so that cell is near the
instrument's floor, and a floor cannot degrade.

`wrong_document` was **0 on every arm and both orders**, and `format_error` 0 -
so removing the model's own prior answer did not make wrong-document retrieval
appear. Depth landed at 69.3-72.5% of `-c 32768`, matching E56's 71-76%.

**Scope.** Every question carries a fixed preamble pointing at the pack, so this
measures retrieval-WHEN-DIRECTED, which is the realistic advisory case and is
not spontaneous retrieval. And depth is not separated from distraction: at turn
14 the model has both a longer history and ten more documents.

Evidence: `results/experiments.md` E57, `results/raw/e57-20260819-*.json`,
instrument `spikes/ps-eval/conversation_heldout.py` with
`tools/validate_conversation_heldout.py` at 116/116, joined by
`tools/compare_heldout.py`. Six of eight registered predictions held; both
falsifications were the models beating the band, the twelfth and thirteenth time
in this programme.

## F84 - MTP speculative decoding preserves the ANSWER and not the completion

**Kind: PLATFORM**

`Qwen3.8-27B-Q4_K_M.gguf` retains its `blk.64.nextn.*` multi-token-prediction
layers, and every figure this repo published before 2026-08-19 was measured with
llama.cpp loading them and discarding them - the serverlog says so in as many
words: `W model has unused tensor blk.64.nextn.eh_proj.weight -- ignoring`.

Turning them on with `--spec-type draft-mtp` on E57's held-out conversation,
one flag changed and nothing else:

| arm | correct | answer strings identical | strict identical | decode |
|---|---|---|---|---|
| vanilla | 13/13 | - | - | 10.87 tok/s |
| MTP n=2 | 13/13 | **13/13** | 5/13 | 19.21 (1.77x) |
| **MTP n=4** | 13/13 | **13/13** | **10/13** | 22.65 (**2.08x**) |

**n=4 is better on every axis at once - faster AND more deterministic** - so n=2
is not an operating point. Draft length was NOT clamped: n=4 offered 4-token
drafts from a model declaring `nextn_predict_layers = 1`, because llama.cpp's
MTP drafter feeds the single NextN mechanism forward until `n_max`.

**Two claims, and they must not be collapsed.** The graded result survives: 13/13
with every parsed answer identical. The **byte-identical determinism property
does not**: full completions moved on 8 of 13 cells at n=2 and 3 of 13 at n=4,
with `F1` going **2,201 -> 1,289 generated tokens for the same answer**. That is
a different reasoning path reaching the same conclusion, and it is upstream
llama.cpp issue #25618 (divergence on quantized targets, reproduced on Strix
Halo with Vulkan) landing exactly where a score cannot see it.

A score is too coarse an instrument for this question - two runs can both be
13/13 while disagreeing on every word - which is why `tools/diff_run_answers.py`
compares answer, citation, generated-token count and reasoning length, and
reports "answers held, completions moved" as an outcome distinct from both exact
and divergent.

**#27151's acceptance collapse did not reproduce** (83-93% here, consistent with
#26750's ~91-92% on RADV/Vulkan).

Evidence: `results/experiments.md` E59, `results/raw/e59mtp{2,4}-20260819-*.json`
and their `-diff.json`, acceptance via `tools/mtp_acceptance.py`.

## F85 - draft acceptance is a property of the WORKLOAD, and a speculative speedup does not transfer

**Kind: METHOD**

Same GGUF, same build 770 / `9e40df63b`, same Vulkan RADV GFX1151 device, same
`--spec-type draft-mtp --spec-draft-n-max 4`:

| workload | acceptance | accepted/verification | decode gain |
|---|---|---|---|
| held-out legal reasoning at `low` | **83.4%** | 3.34 | **2.08x** |
| short conversational prose at `off` | **30.2%** | 1.21 | **1.32x** |

The direction is the opposite of the registered prediction. Formulaic legal
answers - structured citations, templated phrasing, a fixed two-line response
shape - are easy for a draft head to predict; free-form explanatory prose is
not. **30.2% is below the 60% threshold at which speculation is generally held
to pay for itself at all.**

**Operationally: enable MTP for document work, not for chat.** This aligns with
the two-model design rather than cutting against it, since the 27B is where
document work already goes.

The chat figure reproduced to the decimal on an independent run at a different
power profile, so it is not a sampling artefact - but it rests on 168 draft
events against the legal conversation's 1,398 and should not be quoted to a
decimal.

**The methodological point is the transferable one.** E59's acceptance was
deliberately re-measured rather than inherited. Inheriting 83.4% would have
projected ~2.6s for chat; the measured answer is **4.05s**, and the architecture
argument would have been wrong by 1.4 seconds.

**Token-count invariance held exactly on chat** - 57 generated tokens in all four
cells - so that 1.32x is pure inference gain. F84's shorter-completion effect
appeared only in the long legal conversation at `low`, which is a scope rather
than a general property.

**The power profile is irrelevant to inference on this box.** `balanced` vs
`performance`: 0.6% and 0.2%, inside noise, with the MTP effect identical under
both (1.32x vs 1.31x). Every previously published figure was measured under
`balanced` and none of them is affected.

Evidence: `results/experiments.md` E60, `results/raw/e60-{balanced,performance}-20260819.json`.


## F86 - model evaluation and SYSTEM evaluation are different measurements, and ranking models gives wrong engineering answers

**Kind: METHOD**

The most transferable output of 2026-08-19. Five results from this programme,
each of which a model-ranking table gets wrong:

| observation | ranking models says | what is true |
|---|---|---|
| Qwen3-8B at 41.6 tok/s, second-fastest arm | a fast model | **9.46s to a user, slower than the 27B's 5.48s** - it emits 394 tokens where the 27B emits 57 (E58) |
| MTP on Qwen3.8-27B | "MTP is worth 2.08x" | **2.08x on structured legal work, 1.32x on chat** - same model, same flag, same hardware (F85) |
| gpt-oss-120b, 117B total vs the workhorse's 30B | more capacity, better answers | **MMLU 72.7% against 80.2%**, and no evidence either way on the hard-tier failures that matter |
| GLM-4.7-Flash at 10/12 | a 10/12 model | **cannot yet separate capability failure from budget exhaustion** - both misses were truncations |
| the workhorse at 5/12 on L3-hard | too weak for document work | **may be an excellent first stage** in a system whose answer is checked by the 27B |

**The hierarchy, and the order matters because each level can invert the one
before it:**

```
model metrics  ->  workload metrics  ->  task outcome  ->  system cost
```

A model metric inverted at the workload level (the 8B). A workload metric failed
to transfer across workloads (MTP). A task outcome may yet invert a capability
score (the workhorse as a drafting stage).

**`tok/s` becomes actively misleading the moment cascades enter.** A two-call
system can generate fewer tokens per second in aggregate and still reach a
trustworthy answer sooner, if the expensive model only inspects and repairs a
concise draft rather than writing one. Cascade instruments must measure **total
elapsed time to a CORRECT answer across every call**, never a per-model rate.

These are design principles rather than conclusions. Their use is to settle what
the next experiment measures when there is ambiguity: not *which model wins* but
**which arrangement reaches a trustworthy answer fastest and most economically**.

- The useful unit of optimisation is the **workload**, not the model.
- The useful unit of architecture is the **task outcome**, not the model call.


### The four questions, and they are asked in this order

Named by the owner 2026-08-19. The hierarchy above says which METRIC comes
first; this says which QUESTION each level is actually asking, which is what
makes it usable when someone produces a benchmark number.

| | question |
|---|---|
| **Capability** | can the model reach the correct answer under the standard conditions? |
| **Robustness** | does that capability survive context depth, history changes and other realistic conditions? |
| **Efficiency** | how much time and computation does it take to get there? |
| **System value** | does putting the model in a PARTICULAR ROLE improve the final task outcome enough to justify its cost and complexity? |

**The worked example is live as this is written.** GLM-4.7-Flash could finish
12/12 on its confirmation arm and still have **three of the four unanswered**:
robustness (E57's held-out depth design), efficiency (latency against the real
traffic mix), and system value (whether it earns a route at all).

**This is the guard against the next attractive number.** A model can win
capability and lose system value; a model can look mediocre alone and be
excellent as a drafter - which is precisely the open hypothesis about the
workhorse's 5/12. Without these four names, every new benchmark result collapses
back into a leaderboard, which F86's five examples show is the wrong instrument.

Evidence: E57 (F83), E58, E59 (F84), E60 (F85), E61 in flight. This finding is a
synthesis of measurements recorded under those entries rather than a new
measurement of its own, and is marked as such deliberately.

## F87 - a model can have good capability and still be a poor system component, because of its FAILURE MODE

**Kind: METHOD**

**GLM-4.7-Flash scores 10/12 on the L3 hard tier, with two non-terminating
reasoning failures that persist from 4,096 to 16,384 output tokens.** Quote it in
that form; a bare 10/12 loses the finding.

| budget | score | P1 (precedence) | Z1 (underspecified) |
|---|---|---|---|
| `max_tokens 4096` | 10/12 | truncated at 4,096 | truncated at 4,096 |
| `max_tokens 16384` | **10/12** | **truncated at 16,384** | **truncated at 16,384** |

Every other cell identical across the two budgets. **The 4x budget FALSIFIED the
"it just needed more room" reading** rather than confirming it.

**The shape is the finding.** The ten successful answers use a median of
**1,365** generated tokens; P1 and Z1 reach **16,384 without producing an
answer**, **exactly 12.0x** the median, with 68,016 and 65,662 characters of
reasoning. That is a distinct failure mode, not a long tail.

**Capability on those two is UNMEASURED, not demonstrated-absent.** The model
never committed, so whether it could have answered correctly is unknown.

**The qualitative pattern, from two cases and labelled as such:** both are
questions requiring **commitment under conflict or ambiguity**. The failure is
not knowledge - it is **failing to terminate deliberation when there is no clean
resolution**. For a reviewer role that is pointed, because "these two rules
conflict" is a normal input rather than an edge case.

**Operationally:** risky as an **unattended** reviewer unless a watchdog and
fallback are in the design. **Not** a claim that it cannot reason about conflict.

**The counterpoint, which must not be lost:** 10/12 is still materially stronger
than the workhorse's 5/12 on this tier. E61 rules out GLM as a dependable
unattended reviewer; it does not rule out GLM as a specialist for bounded
workloads with a hard generation cap and a fallback route.

### Three metrics this finding adds

1. **Non-termination rate**, tracked as a first-class robustness metric beside
   correctness. A wrong answer is detectable downstream; a component that
   sometimes enters a 16K-token loop becomes the bottleneck for the whole task.
2. **A runaway stopping rule for diagnostics:** an item exceeding roughly **4-6x
   the model's median successful generation length** without reaching an answer
   is a runaway candidate - terminate rather than raising the budget again. NOT
   applied retroactively to any published score.
3. **Commitment latency** - reasoning tokens before the first answer-bearing
   sentence. Total tokens and wall time cannot separate "the task is long" from
   "the model never crossed from deliberation into an answer". This programme
   does not yet measure it and should.

### The general form, and the reason this is a finding rather than a note

**Failures of COMPLETION, TRANSPORT, CORRECTNESS and LATENCY are different
evidence classes.** 2026-08-19 produced one of each, and collapsing any into a
single score would have produced a wrong engineering answer:

| class | instance | what it is NOT |
|---|---|---|
| transport | gpt-oss-120b, 12x `transport_failed` | not a 0/12 capability score |
| completion | GLM P1/Z1 non-terminating | not a wrong answer |
| correctness | GLM 10/12 vs workhorse 5/12 | not a statement about reliability |
| latency | 27B 5.48s vs workhorse 0.91s on chat | not a statement about quality |

This is the sharpest available form of F86: a leaderboard shows correctness and
hides the other three.

Evidence: `results/experiments.md` E61, `results/raw/e61-20260819-glm47flash-l3n0{,-budget16k}.json`,
`results/raw/e61-20260819-gptoss120b-{smoke,bisect}.json`.

## F88 - this arm is bit-deterministic across processes, which makes a repeat cheap and a single run still insufficient

**Kind: METHOD**

Recorded 2026-08-19 from E62, the exact repeat of E61's gpt-oss-120b L3-hard run.

Two runs, two processes, two separate 59.03 GiB loads, same binary
(`llama.cpp/wt/b10435`) and same flags. The second reproduced the first at the
level of bytes, not of aggregates:

- **12/12 both times**, citations 12/12, over-claims 0/1
- **all twelve answers byte-identical**
- **every `completion_tokens` and `reasoning_chars` count identical to the
  character** (`M2`: 1,311 tokens, 4,361 reasoning chars, both runs)
- **both serverlogs 6,809,768 bytes** (observed on the box; serverlogs are
  gitignored, so this one is not pinned in `verify_report_numbers.py`)
- wall 178.7s -> 178.0s (**-0.4%**), median question 13.28s -> 13.22s

**Two consequences, and they pull in opposite directions.**

**Repeating a local arm is cheap and worth doing.** Three minutes plus a load
converted a result that could not be leaned on into one that can. When the
preceding attempt at the identical configuration failed outright, that is the
correct first spend - not a new instrument.

**But determinism is not robustness, and it is the trap in this finding.** A
bit-deterministic arm reproduces its errors exactly as faithfully as its
successes. A second identical run cannot detect a wrong answer, an instrument
defect, or a capability that evaporates when the context structure changes - it
can only detect *sampling* variance, and there is none here to detect. So the
repeat retires exactly one hypothesis ("E61 got lucky") and no others. F86's
four questions are unmoved: capability is now confirmed, robustness, efficiency
and system value are all still open.

**Do not generalise the determinism.** It is a property of this arm at this
temperature on this build. F76 recorded the opposite situation on the tool-use
instrument, where per-task cells did not reproduce between sessions and only
means were usable. Which regime you are in is a measurement, not an assumption -
check it before deciding whether one run is enough.

**The intermittent decode hang survives this finding unchanged.** One hang in
five loads of this model on 2026-08-19 (failed L3 run, smoke, bisect, E61 retry,
E62). Four consecutive clean loads do not explain it and n=5 does not give a
rate. `docs/2026-08-19-gptoss120b-decode-hang.md` stays open, and the model
stays disqualified from any unattended role until it is diagnosed.

Evidence: `results/raw/e62-20260819-gptoss120b-l3n0-repeat.json` + `.serverlog`,
`results/raw/e61-20260819-gptoss120b-l3n0-retry.json` + `.serverlog`,
`results/experiments.md` E62.

## F89 - gpt-oss-120b survives depth, and its one failure is a boundary error that no amount of reasoning fixes

**Kind: MODEL**

Recorded 2026-08-19 from E63, gpt-oss-120b on E57's held-out crossover.

**Robustness is confirmed, and it is the question E62 could not answer.**
Joined across both arms: **shallow 9/10 -> deep 9/10** at 22,066 of 32,768
tokens (67.3% of budget). Nothing degraded, nothing improved, `wrong_document`
0, `accepted_false` 0, recent probes 6/6. Prerequisite 2 of the R&D programme
is closed, and the outcome is a pass.

This matters because the same instrument caught the opposite result once
already: F83 recorded Qwen3-8B holding 5 of 5 anchors with its own answer in the
history and dropping to 6/10 when the questions were held out. A ~5.1B-active
model was a live candidate to repeat that. It did not.

**The single failure is position-independent, which is what makes it
diagnosable.** `P3` is `off_by_calendar` in BOTH arms with the identical answer -
**15 September 2026** against a correct 14 September 2026. The crossover asks
each question exactly once per run and swaps which run asks it early, so a
question wrong in both positions is wrong for a reason that has nothing to do
with depth.

**It is an arithmetic boundary error, not a retrieval error, and the instrument
can tell the difference.** `P3` plants three candidate trigger dates on purpose;
picking the wrong one grades as `wrong_trigger`. This model picked the *right*
trigger and then miscomputed the last day of the limitation period by one day -
an inclusive/exclusive boundary mistake. It read correctly and counted wrongly.

**Every other arm answers it correctly at depth** - Qwen3.8-27B, Qwen3-8B and
the workhorse all give 14 September 2026. The workhorse fails it *shallow* as
`wrong_trigger`, a different error and the one F80 already tiers it on. So this
is specific to gpt-oss-120b rather than a hard question.

**The transferable part: reasoning volume is not reasoning quality.** The same
wrong answer cost **1,679** reasoning characters in the shallow position and
**5,367** in the deep one - 3.2x the reasoning, byte-identical wrong output.
Any commitment-latency proxy (the F87 follow-up) that treats reasoning length as
a proxy for effort-well-spent will read this cell exactly backwards.

**Practical consequence.** On this evidence gpt-oss-120b is sound for reading and
retrieving across a folder of similar agreements at realistic depth, and carries
a specific, repeatable defect on statutory date boundaries. That is a routing
fact, not a score: it is a usable reviewer for document comprehension and must
not be the arm that computes a limitation date. It also remains disqualified from
unattended use on the unexplained decode hang - one in seven loads on 2026-08-19,
six consecutive clean.

Evidence: `results/raw/e63-20260819-gptoss120b-heldout-{ab,ba}.json`,
`results/raw/e63-gptoss120b-paired.json`, `results/experiments.md` E63.

## F90 - compare latency only within a band of comparable OUTPUT VOLUME, or you are measuring brevity

**Kind: METHOD**

Recorded 2026-08-19 from E64, gpt-oss-120b on E58's real-traffic latency tiers.
This completes prerequisite 3 of the R&D programme; capability (E62), robustness
(E63) and efficiency (E64) are now all measured, leaving system value.

**The figures.** gpt-oss-120b warm medians: chat **3.66s** (185 generated
tokens), document **4.14s** (202), folder **6.68s** (260). Cold 4.73 / 17.67 /
117.68s, model load 22.0s, full-offload gate passed on 74 layers.

**The finding is that the arms split into two groups and mixing them inverts the
answer.**

Against arms that emit a comparable amount of text, gpt-oss-120b is much faster:
Qwen3.8-27B at `low` is **6.05x / 4.00x / 7.50x** slower across chat / document /
folder, and Qwen3-8B is **2.58x / 2.08x / 7.68x** slower.

Against arms that emit almost nothing it is slower - the workhorse returns
**11** generated tokens on the folder tier in 0.29s, and Qwen3.8-27B at `off`
returns **11** in 1.77s, against gpt-oss-120b's 260 in 6.68s. Eleven tokens is
not an answer to a question about a folder of agreements. Ranking those cells by
wall time ranks them by brevity.

This is E58's lesson running the other way. F86 recorded Qwen3-8B looking fast on
tok/s (41.6) while being the slowest arm to a user (9.46s) because it emitted 394
tokens where the 27B emitted 57. Here the same instrument produces the inverse
error: models look fast because they decline to answer at length. **Neither
tok/s nor wall time is interpretable without the token count beside it**, and a
latency table that omits `median_gen_tokens` cannot be read correctly.

**Refined 2026-08-19 after external review, because the rule as first written
could be misused in the opposite direction.** Read as *speed plus token count*,
it would condemn a correct 15-token answer, and brevity is not a defect. The
registered wording is therefore:

> A latency number is interpretable only after establishing that the response
> COMPLETED THE TASK. Generated-token count is an important DIAGNOSTIC of
> non-answering, not a measure of adequacy.

The eleven-token folder-tier cells are unchanged as the evidence. What changes is
what the token count licenses: it tells you to go and READ the response before
using its latency, it does not by itself condemn the response.

**The routing consequence, which does not change the architecture.**
gpt-oss-120b does not displace the workhorse - 3.66s against 0.91s on the 91.3%
of real traffic that is chat, so the resident model stays and E60's two-model
decision is untouched. What it does is beat every reasoning-capable arm on every
tier, by 7.50x against the 27B at `low` on the folder tier - the 1.4% of requests
carrying 34% of all generation time, and exactly the difficult tail the second
model exists for. On capability, robustness and efficiency it is now the
strongest candidate measured for that role.

**Two things it does not settle.** System value - whether it improves the task
outcome enough to justify a second resident 59 GiB model - is F86's fourth
question and is still open; the cascade experiment is the instrument. And it
remains disqualified from unattended use on the unexplained decode hang: one in
eight loads on 2026-08-19, seven consecutive clean.

**A measurement trap found in passing.** This load took **22.0s** where E62's
took roughly two minutes for the same 59.03 GiB, because the page cache was warm
from earlier runs in the session. Model load time on this box measures the page
cache as much as the model. Any load-time comparison must state cache state, and
`tools/run_step8_leg.sh`'s already-noted missing stack fingerprint does not
capture it.

Evidence: `results/raw/e64-20260819-gptoss120b-latency.json`,
`results/raw/latency-20260819.json`, `results/experiments.md` E64.

## F91 - a tie at ceiling is a statement about the RULER, not about the models

**Kind: METHOD**

Recorded 2026-08-19 from E65, the first frontier comparator run against an
instrument this lab built.

**The figures.** On L3-hard (`distractors=0`, pack 13,221 chars, byte-identical
prompts): gpt-oss-120b **12/12**, Qwen3.8-27B **12/12**, and a frontier arm
**12/12**, all three with **12/12** valid citations. The workhorse is 5/12 and
GLM-4.7-Flash 10/12, so the instrument still separates the weak arms fine.

**The finding is that L3-hard is SATURATED at the top and is therefore spent as
a comparator.** It was built to ask whether a local model could do professional
document reasoning at all, and it answered that. It cannot answer *how far below
the frontier the local models sit*, because three arms are pinned against its
ceiling. Re-running it will not produce a discriminating number.

**The trap this exists to prevent is reading the tie as equality.** At n=12 with
both arms at ceiling, a true gap of roughly 25 percentage points would still
present as 12/12 against 12/12 - the instrument has no resolution left to spend.
Reporting "the local model matches the frontier model" from this cell would be
the same error as reporting a latency without its output volume (F90): a number
that is arithmetically true and directionally misleading.

**This is the lab's own medicine.** The R&D programme's AMENDMENT 2 rejected a
proposed 5-percentage-point equivalence threshold on exactly this ground - at
n=40 the standard error on a difference of proportions is 8.9pp - and the same
objection has to survive contact with a result we like. It does.

**What a saturated instrument is still good for:** it remains a valid PASS/FAIL
gate for admitting a new arm to the difficult tier, and it remains the evidence
that the local arms are not weak here. What it is not is a ranking.

**The consequence is a design rule.** Before running a comparator against an
existing instrument, check whether the incumbent arms have already pinned it. If
they have, the comparator run buys a ceiling confirmation and nothing else, and
the effort belongs on an instrument where the incumbents demonstrably fail - for
this programme, E57's held-out depth design, where `P3` is a live failure for
gpt-oss-120b (F89) and correct for every other local arm.

**A harness caveat that travels with the row.** The frontier arm ran through
Claude Code subagents, not an API: no working cloud credential exists here (the
vaulted OpenRouter key returns 401 `User not found`, which is revocation, not an
exhausted balance), and the Agent tool takes a model *alias* rather than a
version. The arm is therefore an upper bound with an unpinned model and no token
accounting, and `tools/run_ps_eval_subagent.py` writes that caveat into every
result file it produces rather than trusting a reader to remember it. The
contamination guard did pass: `tool_uses` is 0 on all twelve questions, so no
subagent read the answer key that sits in the same repo.

Evidence: `results/raw/e65-20260819-opus-subagent-l3n0.json`,
`results/raw/e65-20260819-opus-subagent-l3n0-answers.json`,
`results/experiments.md` E65.

## F92 - two very different models miscounted the same deadline to the same wrong day

**Kind: MODEL**

Recorded 2026-08-19 from E66, the frontier arm on E57's held-out depth design.

**The cell.** `P3` asks for the last day of a six-year limitation period running
from a breach on 14 September 2020. The correct answer is **14 September 2026**.

| arm | shallow | deep |
|---|---|---|
| gpt-oss-120b (E63) | **15 September 2026** | **15 September 2026** |
| frontier, subagent harness (E66) | **15 September 2026** | 14 September 2026 (correct) |

**Two models with nothing in common produced the identical wrong date.** Not a
different miscount, not a different mechanism - the same off-by-one to the same
value. Both had already picked the RIGHT trigger date from three planted
candidates, so neither failed to retrieve; both failed to count. Every other
local arm (27B, 8B, workhorse) answers it correctly, which is what makes it look
like a capability gap until a frontier model falls into the same hole.

**This is the strongest evidence in hand for delegating deterministic
subproblems to deterministic tools (H6).** A defect that survives a jump from
~5.1B active parameters to a frontier model is not a defect more model capacity
fixes. It is arithmetic, and arithmetic has a correct implementation that costs
microseconds. Spending additional inference on it is the expensive way to stay
wrong.

**The second half is about determinism, and it cuts the other way from F88.**
gpt-oss-120b was wrong in BOTH positions with a byte-identical answer - the
bit-determinism F88 recorded. The frontier arm was wrong once and right once on
the same question. **With n=1 per cell that cannot be attributed to position
rather than run-to-run variance**, so the honest statement is *sometimes wrong*,
not *wrong when shallow*. A non-deterministic arm needs repeats before any of its
cells is load-bearing, and one run of it is worth less than one run of a
deterministic arm - which is the practical cost of the property F88 recorded as
an advantage.

**A limit on the instrument, found by using it.** E57's depth axis does not
transfer to a frontier comparator. It measures degradation at 67.3% of a 32,768
context; a 1M-context model sees the same conversation at about 2% full and was
never under the pressure the tier applies. Its `deep` cells measure headroom, not
robustness - and consistent with that, both of its failures were SHALLOW. The
tier remains valid for separating local arms from each other and must not be
re-used as a frontier comparator without being rebuilt against a context the
frontier model would actually strain. This is F91's rule arriving from the other
direction: F91 was a ceiling with no resolution left, this is an axis that does
not apply to the arm being added.

Evidence: `results/raw/e66-20260819-opus-subagent-heldout.json`,
`results/raw/e63-20260819-gptoss120b-heldout-{ab,ba}.json`,
`results/experiments.md` E66.

## F93 - a tool helps a model that cannot do the subproblem and HARMS one that can

**Kind: MODEL**

Recorded 2026-08-19 from E67, the H6 deterministic-date arm. Preregistered in
`b614c60` before any model call.

**The same tool, the same six date questions, the same temperature 0.**

| model | control | with date tools | net |
|---|---|---|---|
| workhorse 30B-A3B | 0/6 | **4/6** | **+4** |
| gpt-oss-120b | 5/6 | **4/6** | **-1** |

**Averaged across the two arms this reads "+3, H6 supported", and that is the
wrong conclusion for the model that actually serves the difficult tier.** H6 is
not a property of the task. It is a property of the model's baseline competence
at the subproblem being delegated: a calculator rescues an arm that cannot count
and gets in the way of one that can.

**The harm channel is NOT tool misuse, and this is the part that transfers.**
gpt-oss-120b regressed on `N2` - a correct 31 December 2026 became 1 December
2026 - **while making no tool call on that question at all.** A three-condition
control separates the cause:

| condition | preamble | `tools` in payload | score | `N2` |
|---|---|---|---|---|
| control | no | no | 5/6 | correct |
| preamble-only | yes | no | 5/6 | correct |
| tools on | yes | yes | **4/6** | **wrong** |

The sentence announcing the tools changes nothing. The `tools` field changes the
score. The serverlogs show why: `add_period` appears **14 times** in the rendered
prompts of the tools run and **0 times** in the preamble-only run. Under
`--jinja` the schemas are rendered into the prompt the model sees, so **offering
a tool is a prompt change that affects requests which never call it.**

**The rule this produces:** `tools` is part of the SERVING CONFIGURATION, not a
free-standing capability bolted on beside it. A run that offers tools is a
different configuration from one that does not, on every request, including the
ones with no tool call in them. That is F39 / Rule 8 arriving somewhere new, and
it means a routing design cannot offer a tool "just in case" without paying for
it on the whole route.

**A second, narrower result: a correct calculation of the wrong question is the
expected failure, and only arguments reveal it.** The workhorse's `P3` called
`add_period(date="2020-09-14", years=6, days=1)` - explicitly adding STAT-LIM's
"day after" - got a flawless `2026-09-15`, then applied an unjustified
`last_day_of_month` for 30 September 2026. Two legal errors, no arithmetic error.
This was registered in advance as prediction 3 and held. It also means F92's
shared off-by-one is confirmed as **anchor selection, not counting** - so the
tool was never going to fix it, and H6 must be scoped to subproblems where the
model's error is the computation rather than the choice of inputs.

**And one that cost a re-grade.** The first classifier compared tool results to
answers as substrings, so a prose answer ("30 September 2026") never matched an
ISO result ("2026-09-30") and every obeyed call was labelled `result_ignored`.
`wrong_args` and `result_ignored` have opposite fixes, so the inversion was not
cosmetic. It is now compared as parsed dates through the grader's own `_dates`,
with regression tests. **A measurement whose two failure classes are told apart
by string matching across two notations is a bug waiting for a result to
corrupt.**

**REPEATED 2026-08-19, three times, and it is bit-identical.** The single
regression was not load-bearing on its own, so the gpt-oss control/tools pair was
re-run twice more:

| condition | runs | score | `N2` answer | tool calls |
|---|---|---|---|---|
| control | **3** | 5/6 every time | 31 December 2026, correct | 0 |
| preamble-only | 1 | 5/6 | 31 December 2026, correct | 0 |
| tools on | **3** | 4/6 every time | **1 December 2026**, `off_by_calendar` | 1 |

Every answer identical across runs, `P3` included. **What this retires is exactly
one hypothesis - that the regression was a sampling fluke - and no others.** That
is F88's lesson applied to this lab's own result: a bit-deterministic arm
reproduces its errors as faithfully as its successes, so three identical runs are
worth barely more than one for anything except ruling out noise.

**Limits, after the repeats.** One question, one model, one tool set, six
questions per arm, date arithmetic only. The direction of the harm is now
well-evidenced and reproducible; **its GENERALITY is not tested at all** and
would need a different instrument - other task types, other tool sets, the chat
tier. A recommendation of the form "do not give this model tools" is broader than
this evidence: what is established is that offering THIS tool set costs THIS
model a point on THIS question, reproducibly.

Evidence: `results/raw/e67-20260819-workhorse-{control,tools}.json`,
`results/raw/e67-20260819-gptoss120b-{control,preamble-only,tools}.json`,
`results/experiments.md` E67.

## F94 - offering a tool is never free, and its sign changes with the model AND the task

**Kind: MODEL**

Recorded 2026-08-19 from E68, which asked whether F93's serving-config effect
survives on a question set the tool is irrelevant to. It does, and it is worse.

**L1, 20 questions, no date question in the pack, temperature 0:**

| model | control | preamble-only | tools on | calls |
|---|---|---|---|---|
| workhorse 30B-A3B | 14/20 | 13/20 | **11/20** | **68** |
| gpt-oss-120b | 20/20 | **18/20** | 20/20 | 0 |

**The workhorse loses three questions to a tool it never needed, and loses them
as NON-TERMINATION.** `format_error` goes from 0 to 5; two cells ran to the
six-round cap having made six tool calls each without ever emitting a parseable
answer. It made **68 calls** on twenty questions about retainers and liability
caps. This is the more expensive failure mode for a user: not a wrong answer, no
answer.

**The effect has no consistent sign.** Across E67 and E68 the four cells are
`+4`, `-3`, `-1`, `0` for tools, and `-1`, `0`, `-2` for the announcement alone.
Tools rescue the workhorse where the tool is relevant and wreck it where it is
not; they cost gpt-oss a point on date questions and nothing on L1, while four
lines of prose merely SAYING tools exist costs gpt-oss two points on L1 and the
workhorse one. **There is no direction to generalise, only a magnitude to
respect.**

**The consequence for routing, and it is a production one.** The workhorse serves
91.3% of real requests. A route that offers tools by default pays up to 3
questions in 20 on requests that need none. `tools` is not a capability you add
beside a model - it is part of the serving configuration on every request,
including the ones with no tool call in them, and it must be measured per route
rather than assumed free. That is Rule 8 / F39 with a measured price attached.

**The methodological half.** Both E67 and E68 show that the presence of a tool
schema is a large, model-specific, non-monotonic variable. **Any comparative
instrument that bakes a tool schema into every item is no longer ranking the
thing it thinks it is** - it is ranking susceptibility to tool-offer
interference, at an effect size (3/20 = 15 percentage points on the workhorse)
comparable to the gap such instruments are usually built to detect. If tool
interference is to be measured alongside capability it has to be a CROSSED
factor, run both ways, not a constant baked into the design.

**Limits.** L1 is a declared proxy for ordinary traffic - document QA, not chat,
because chat has no objective grader. The six-round cap means the runaway cells
are "no answer within six rounds", not "never"; a higher cap trades format errors
for latency and was not tested. gpt-oss sits at 20/20 on L1 and is therefore at
ceiling, so its null on the tools condition is uninformative about whether a drop
was possible. n=1 per cell on a deterministic pair: exact for this item set, no
interval for unseen items.

Evidence: `results/raw/e68-20260819-workhorse-l1-*.json`,
`results/raw/e68-20260819-gptoss120b-l1-*.json`, `results/experiments.md` E68.

## F95 - a deterministic grader can be reproducible and still be systematically wrong, and reproducibility makes it MORE dangerous

**Kind: METHOD**

Status: confirmed (2026-08-20, KA-H1/E74). The KA-H1 scorer compared plain ASCII
substrings exactly. gpt-oss-120b writes with typographic punctuation and emits
**383 non-ASCII characters across 24 answers** - 166 `U+2011` NON-BREAKING
HYPHEN and 119 `U+202F` NARROW NO-BREAK SPACE - against Qwen3.8-27B's 46,
Qwen3-30B-A3B's 7 and the frontier arm's **0**.

The scorer therefore had a **model-specific failure mode built into it**.
`memory-pressure`, `power-cycle`, `success-at-deadline` and `Qwen 3.8-27B` were
each recorded as wrong answers while being the required answer, written with a
different hyphen.

| arm | v1 (ASCII-exact) | v2 (typography-folded) |
|---|---|---|
| gpt-oss-120b | 11/24, **1 critical** | **18/24, 0 critical** |
| Qwen3-30B-A3B | 20/24, 2 critical | 21/24, 1 critical |
| Qwen3.8-27B | 21/24 | 21/24 |
| frontier subagent | 23/24 | 23/24 |

**Seven of gpt-oss-120b's thirteen misses shared this one mechanism**, which is
what made it findable: the owner asked for a failure TAXONOMY rather than
another benchmark, on the reasoning that a shared mechanism points at
configuration rather than capability. It pointed at the instrument.

**The most serious single cell:** `K20` asked a question the corpus does not
answer. gpt-oss-120b declined correctly. The scorer could not read the phrasing
and recorded a **critical error** - the class reserved for a model inventing an
answer. The instrument's most severe verdict was awarded to its most desirable
behaviour.

### Why reproducibility is the aggravating factor, not a mitigation

F88 established that this arm is bit-deterministic across processes. That means
**a typographically polished correct answer would receive the same wrong score
on every re-run, for ever.** A flaky grader announces itself; a deterministic
one that is wrong is silent and self-consistent, and every repeat confirms it.
Determinism is not correctness - it is only reproducibility, and this is the
second half of F88 arriving in a different disguise.

### The audit, which is the useful half

Every substring-matching scorer in the repository was checked for the same
exposure:

| scorer | normalisation | exposed? |
|---|---|---|
| `tools/score_aabr.py` | `[^a-z0-9]+ -> " "` | **no** - folds all punctuation |
| `spikes/ps-eval/questions.py` | `[^a-z] -> ""` | **no** |
| `spikes/ps-eval/questions_l4.py` | structural date parsing | no |
| `tools/score_kw_eval.py` | ASCII-exact (v1) | **YES - this defect** |
| `spikes/eval-pilot/score_keyed.py` | `.lower()` only, alias substring | **YES - same shape, unexercised** |

**The older, cruder scorers were immune.** `score_aabr.py` reduces everything
non-alphanumeric to a space, which looks careless and is in fact robust. The
newer scorer preserved punctuation to be more precise and acquired a
model-specific bias by doing so. **Precision in a comparison is not the same as
correctness, and a gentler normaliser is not a safer one.**

`score_keyed.py` has the same shape and has not yet met a model that writes this
way. Recorded rather than fixed: it has no live consumer, and changing a scorer
with banked results attached is its own risk.

### The rule that carries forward

> **Audit the ruler whenever a result is surprising, before believing the
> result.** This is Rule 7 ("audit the grader before believing a surprising
> score") with a measured instance and a specific mechanism attached.

Three of this session's surprises were instrument faults, not findings: a task
refused because the harness put its worktree under `/tmp`; four coding cells
recorded as capability failures when the agent loop had swallowed a transport
error; and this. **The quality of the ruler is now as material as the quality of
the model.**

Normalisation is kept deliberately narrow. Typography that cannot change an
answer is folded - Unicode dashes, no-break spaces, curly quotes - and
separators are ignored on a second pass guarded by a digit boundary consulted
against the ORIGINAL text, so `Qwen 3.8-27B` matches `Qwen3.8` while `Rule 90`
does not match `Rule 9`. Letters, digits, decimal points and operators are never
touched. Turning a false negative into a false positive would be the worse
defect, because nothing would ever surface it.

The scorer now carries a `SCORER_VERSION` stamped into every summary, and the
cells that moved v1 -> v2 are listed in its header. **Nothing was regenerated:
the same banked completions were re-scored.**

Evidence: `results/raw/kw-scores-all.json`, `tools/score_kw_eval.py`,
`tests/test_kw_eval.py` (66 tests, including a typography corpus covering ASCII
hyphen, `U+2010`, `U+2011`, `U+2012`, `U+2013`, `U+2014`, `U+2212`, no-break
space, narrow no-break space, thin space and curly quotes).

## F57 ADDENDUM 2 - the 7.0.0-28 -> 7.0.0-29 boundary, recorded BEFORE the reboot that crosses it

**Kind: PLATFORM**

Recorded 2026-08-20 12:00, ahead of an owner-scheduled reboot for a kernel
update. `7.0.0-29-generic` is already installed in `/boot`; the running kernel
is still `7.0.0-28-generic`.

**Every figure banked in this repository up to and including commit `ebf7bab` was
measured on `7.0.0-28-generic`.** That covers the whole 2026-08-19/20 programme:
E71, E72 (125 soak cycles), E73 (the 20-task coding suite), E74 (the 24-item
knowledge-work bank across four arms) and E75 (selective review).

**amdgpu is in-kernel, so this is a live bench variable that `results/` does not
otherwise record.** F57 established that once; this is the second crossing and
the first one recorded in advance rather than reconstructed afterwards.

**What must happen after the reboot, before any figure is compared across it:**

1. `uname -r` to confirm the running kernel actually moved.
2. `canonical-livepatch status` as well - since Ubuntu Pro was attached,
   Livepatch can change the RUNNING kernel without changing its package version,
   so `uname -r` alone is no longer sufficient.
3. **Re-run one banked measurement as a bridge.** The cheapest sufficient one is
   a short `tools/soak_load.py` run on gpt-oss-120b: E72 gives 100 cold loads at
   a 22.02s median, 0.87s TTFT median and 63.06 GiB GTT peak, all with a very
   tight spread, so a handful of iterations either reproduces those or does not.
   Without that bridge, any post-reboot figure compared against E71-E75 is
   comparing two different drivers and calling it a model difference.

**The specific risk this guards.** gpt-oss-120b's decode hang is undiagnosed and
its clean record is 125 cycles on THIS kernel. A new amdgpu is exactly the kind
of change that could alter that rate in either direction, and S-H2's 2.95%
bound does not transfer across the boundary on its own.


## F96 - byte-determinism survives a new PROCESS but not a repeated RUN inside one; within-process reps are not independent replicates

**Kind: METHOD**

Recorded 2026-08-29 from E87, whose control prediction caught it.

F59 established that llama-server at temperature 0 is byte-deterministic, and F88
that a fresh process reproduces a prior run exactly. Both are still true. E87
found the boundary they do not cover.

Three identical runs of the same 11-item pack, same config, same server process,
temperature 0:

| run | vs the E85 baseline |
|---|---|
| rep 1 (cold process) | **11/11 byte-identical**, both arms |
| rep 2 | 4/11 (arm A), 2/11 (arm C) |
| rep 3 | 4/11 (arm A), 2/11 (arm C) |

**The cold first run reproduces perfectly. Later runs in the same process do
not.** Between them sat another pack's traffic and the previous rep, leaving
cache state the next run inherits. This is E82's order-and-preceding-traffic
effect operating *across runs* instead of within one.

**What this changes about method:**

- **Reps inside one process do not replicate a correctness result.** They vary
  something - the cache - so by F59's own logic they are informative rather than
  redundant, but what they are informative *about* is cache sensitivity, not
  sampling variance. Treating them as independent replicates overstates n.
- **A cold process is the unit of replication for correctness.** F88's
  cross-process repeat remains the valid cheap check.
- **Throughput is unaffected.** E87's decode delta was stable across all reps to
  under 1pp and identical on rep-1-only, so within-process reps remain sound for
  timing, which is what they were there for.

**Do not read this as F59 being wrong.** F59's own wording anticipates it:
*"reps become informative only when something in the config moves."* A shared
server's cache state moves between reps. The gap was that nobody had counted
cache state as part of the config.

Evidence: `results/raw/e87-{A,C}-s-r{1,2,3}.json` against
`results/raw/e85-p{0,1}-s.json`; `tools/score_e87.py` prediction 1 block;
`results/experiments.md` E87.
Status: ACTIVE. Applies to any multi-rep llama-server run sharing one process.

## F97 - Claude Code drives a LOCAL model end-to-end with no translation shim; llama-server build 9865 implements the Anthropic Messages API natively

**Kind: PLATFORM**

Recorded 2026-08-29 while standing up the simpleloop coder bake-off.

The assumption going in was that pointing an Anthropic-API client at a local
GGUF needs an Anthropic-to-OpenAI proxy, because llama-server is "OpenAI
compatible". That is out of date. Build 9865 (`067de9371`) routes
`/v1/messages` and `/v1/messages/count_tokens` in `tools/server/server.cpp`,
carries `server_chat_convert_anthropic_to_oai()`, and even has a
`normalize_anthropic_billing_header()` that pattern-matches the literal string
`You are Claude Code, Anthropic's official CLI for Claude` - the build has
explicit Claude Code support.

Proven on the artefact, not the endpoint: real `claude -p` against
`ANTHROPIC_BASE_URL=http://127.0.0.1:8500`, Qwen3-Coder-30B-A3B-Q4_K_M, a
seeded one-line bug (`return a - b`). The model read the file, edited it to
`return a + b`, ran pytest and left `1 passed`.

**What this unlocks:** any Anthropic-API harness - Claude Code, simpleloop,
ccloop - can run its coder on this box with a base-url change and nothing else.
No proxy to maintain, no format translation to keep in sync.

Evidence: `/opt/sparkrouter/llama.cpp/tools/server/server.cpp:222,239`;
`server-chat.cpp:300`; the spike transcript and `calc.py` under the session
scratchpad.
Status: ACTIVE. Re-check on any llama.cpp build bump - this is a young endpoint.

## F98 - the Claude Code harness floor is 44,912 tokens, and it eliminates models by TRAINED CONTEXT before any quality question is asked

**Kind: PLATFORM**

Recorded 2026-08-29.

Claude Code's own system prompt plus tool definitions measured **44,912 tokens**
on the first real call, reported by the server's own refusal:
`request (44912 tokens) exceeds the available context size (32768 tokens)`.
That is the floor to hold ONE turn, before any project file is read.

Two consequences, both of which change how a local-agent comparison is run:

- **It is a hard eliminator.** `Qwen3-8B-Q4_K_M` has `n_ctx_train=40960`, below
  the floor. It cannot hold a single turn of the harness and was cut from the
  bake-off on that number - not on a quality judgement. Every other candidate on
  the box is >=131,072 and survives.
- **It makes prefill the dominant per-tick cost, and prefill DECAYS.** On
  Qwen3-Coder-30B-A3B at `-c 131072 -fa on -ctk q8_0 -ctv q8_0`, the first turn's
  46,259-token prefill took **183 s**, with throughput falling monotonically from
  **605 tok/s at 12k to 252 tok/s at 46k**. A tick therefore starts with ~3
  minutes of prefill before a single token is generated. Slot reuse rescues the
  turns after it (`sim_best = 0.986` LCP match observed), so the cold first turn
  is the cost to plan around.

**Method consequence:** any agentic-harness benchmark on this box must state the
harness floor and screen candidates against `n_ctx_train` first. A model that
cannot hold the prompt is not a weak arm, it is not an arm.

Evidence: the 400-error text from llama-server; `tools/gguf_ctx_probe.py` across
`/opt/models/staging`; `print_timing` lines in the arm's server log.
Status: ACTIVE.

## F99 - tool-calling capability must be measured under `tool_choice: auto`, because `auto` is a MODEL property and `any` masks it

**Kind: METHOD**

Recorded 2026-08-29. This one is recorded because it nearly became a wrong
finding about the harness.

Probing Qwen3-Coder through `/v1/messages` with a `write_file` tool and default
tool choice returned `stop_reason: end_turn` and a text block that *narrated*
calling the tool - no `tool_use` block at all. The obvious reading was that
llama-server's Anthropic endpoint drops tools, and that was written down before
it was checked.

It is wrong. Two controls settle it:

| probe | result |
|---|---|
| same model + tool via `/v1/chat/completions` | `finish_reason: tool_calls`, correct arguments |
| same model + tool via `/v1/messages`, `tool_choice: {"type":"any"}` | `stop_reason: tool_use` |

So tools ARE wired through the Anthropic endpoint. What the first probe measured
was the model declining to call under `auto`.

**Why this matters for the comparison:** Claude Code uses `auto`. A screen that
forces `tool_choice: any` would show every model "passing" tool use while the
harness fails in production for exactly the models that narrate instead of
calling. The discriminator between local coder models here is not whether they
CAN emit a tool call, it is whether they DO under `auto`.

This is `comparison-integrity`'s "measure the artefact, never a proxy" in a new
costume: a well-formed 200 response with a fluent paragraph in it is the silent
arm, and the forced-tool probe is the safeguard that would have scored it
higher.

Evidence: the three probe results above, all against
`Qwen3-Coder-30B-A3B-Instruct-Q4_K_M` on port 8500.
Status: ACTIVE.

## F100 - a benchmark's GATE needs its own positive control, run BEFORE the arms; an unverified gate measures itself

**Kind: METHOD**

Recorded 2026-08-29 from the coder bake-off's first two arms, both of which had
to be voided.

The fleetvoice screen gates each task on `make check`. The seeded Makefile ran
`python3 -m ruff check .`. On this fleet **ruff is a standalone binary with no
python module**, so the gate returned exit 2 on every project regardless of what
the model did.

What that produced:

| arm | recorded | actual |
|---|---|---|
| qwen3-coder | `NEEDS_HUMAN`, task not done | **had completed Task 1 correctly** - 6 passed, ruff clean, exit 0 through the fixed gate |
| kat-coder | `FATAL` | genuinely failed, but for an unrelated reason (F101) |

The first row is the dangerous one: a **false negative that looks exactly like a
model result**. Had the screen run to completion unattended, all nine arms would
have failed identically and the report would have read "no local model can drive
the loop" - a confident, wrong, and entirely self-inflicted conclusion.

**The rule:** before any arm runs, prove the gate with three controls, not one.

1. The green-start state passes (here: an empty `tests/`, which `pytest` exits
   **5** on - "no tests collected" - and which must be treated as green, not as
   failure).
2. Known-good work passes.
3. **Known-BAD work FAILS.** This is the control that was missing. A gate that
   cannot say no is indistinguishable from a gate that always says no, and both
   look like a result.

Control 3 is the same discipline the fleetvoice WORKPLAN's own Task 5 demands of
the thing being built - "assert the inverse control, so the test can distinguish
correctly silent from never ran" - and it was not applied to the harness that
would score it. `comparison-integrity`'s "measure the artefact, never a proxy"
covers the arm's output; this covers the ruler.

Evidence: `results-VOID-makefile-bug.README` and the three control exit codes
(0 / 0 / 2) in the session log.
Status: ACTIVE. Applies to every gated benchmark in this repo.

## F101 - KAT-Coder-V2.5-Dev cannot serve tools through llama.cpp: its chat template refuses Claude Code's message order

**Kind: PLATFORM**

Recorded 2026-08-29.

`Kwaipilot_KAT-Coder-V2.5-Dev-Q4_K_M` loads fine (12 s) and llama-server begins
listening, but every request returns HTTP 400 before reaching the model:

    Unable to generate parser for this template. Automatic parser generation
    failed: While executing CallExpression at line 85 ...
    raise_exception('System message must be at the beginning.')
    Error: Jinja Exception: System message must be at the beginning.

The model's own template asserts the system message is first. Claude Code's
request, once converted Anthropic -> OAI by llama-server, does not satisfy that
assertion, so `--jinja` parser generation fails and no tool-capable request is
ever served. Three ticks failed in 6 seconds with zero requests reaching the
model (`grep -c 'slot launch' ` on its server log = 0).

**This is a stack incompatibility, not a quality verdict.** It says nothing about
whether KAT-Coder is a good coding model - only that it cannot be driven by an
Anthropic-API harness on this build without a `--chat-template` override, which
would make it a different arm (a non-native prompt format) and must be labelled
as one if attempted.

Evidence: `arm-kat-coder.server.log`, the void results README.
Status: ACTIVE. Re-test on a llama.cpp bump; template parser generation is young.

## F102 - a local coder declared a 6-task WORKPLAN COMPLETE having done 1 task and ticked no boxes, with the gate GREEN

**Kind: MODEL** - what the model did. Why the gate could not see it is
**F134**, split out 2026-09-01.

Recorded 2026-08-29 from the coder bake-off's first valid arm.

`Qwen3-Coder-30B-A3B-Instruct-Q4_K_M`, driving simpleloop's coder mode against
the 6-task fleetvoice WORKPLAN, produced this end state after 2 ticks:

| axis | state |
|---|---|
| Task 1 substance | **correct** - `probe.py` + `test_probe_type.py`, 7 tests passing |
| Tasks 2-6 | **absent** - no `status.py`, no `render.py`, no `cli.py` |
| WORKPLAN boxes ticked | **0 of 6** |
| `make check` | **green, exit 0** |
| STATUS written by the agent | **`COMPLETE`** - and written twice, duplicating the header line |

**The gate was green because the missing work has no tests to fail.** Nothing in
the harness could distinguish "all six tasks done" from "one task done and five
never started", because the only tests present were the ones the model itself
wrote for the task it did do.

This is the vacuous-success shape, appearing *in the measuring apparatus* rather
than in the thing being measured - and the WORKPLAN it was executing exists
precisely to defend against the same failure in a voice interface ("everything's
fine" because a socket was unreachable). A green suite proves the assertions that
exist passed; it says nothing about assertions nobody wrote.

**Substance and protocol are different axes, and only one of them was fine.** The
code was right. The loop discipline - tick the box you completed, do not claim
the plan is finished - was not. For an UNATTENDED overnight loop that ordering is
backwards from what matters: protocol compliance is what makes walking away safe,
and a model that declares victory early converts an eight-hour run into one task
plus seven hours of nothing.

**Method consequence, applied immediately:** the bake-off now scores
`py_files`, `boxes_ticked` and `gate_green` per arm alongside the outcome. A
binary pass/fail records this arm as a plain failure and discards the only
interesting thing about it.

Do NOT read this as a verdict on the model's coding ability - the code it wrote
was correct and clean. It is a verdict on its fitness for autonomous multi-task
execution, which is a different question and the one this bench asks.

Evidence: `results-validation-run-old-scoring.jsonl`; the arm's WORKPLAN with
six unticked boxes; its HANDOFF carrying two `STATUS: COMPLETE` lines.
Status: ACTIVE. Being re-measured across all 9 arms under the widened scoring.

## F103 - the binding constraint on local agentic coding is llama.cpp's TOOL-SCHEMA plumbing, not model capability: 3 of 6 arms served ZERO requests

**Kind: PLATFORM**

Recorded 2026-08-29 from the coder bake-off screen.

Of the first six arms, **three never received a single request**. The model was
never asked anything; llama-server rejected Claude Code's tool schemas before
inference. Two distinct mechanisms, both in the `--jinja` tool path:

| arm | mechanism | requests served |
|---|---|---|
| KAT-Coder-V2.5-Dev | Jinja template asserts `System message must be at the beginning` | 0 |
| Qwen3.8-27B | same template parser-generation failure | 0 |
| Qwen3-30B-A3B-Instruct-2507 (**workhorse**) | `error parsing grammar: number of repetitions exceeds sane defaults, please reduce the number of repetitions` | 0 |

**The workhorse row is the one that matters.** That is the exact model the
sparkrouter relay is serving in production right now. It answers ordinary chat
perfectly well and **cannot accept Claude Code's tool schemas at all** - the GBNF
grammar generated from the tool definitions blows a repetition limit before any
token is produced.

**What this overturns:** `reports/2026-07-16-local-model-routing-guide.md` ranks
local models on document and chat work. That ranking does not transfer to
agentic use, and nothing in this repo previously tested the difference. "Good
local model" and "usable in an agentic loop" are separate properties, and the
second is gated by the serving stack rather than by the weights.

**Method consequence:** an agentic-loop bench MUST record requests-served per
arm. Without it, all three of these look like model failures - they return
FATAL in ~5 seconds with an empty project, and an empty project passes `make
check` because there is nothing to test. Three separate vacuous-green signals
stacked on one another (cf. F100, F102). `grep -c 'slot launch'` on the server
log is the cheap discriminator: zero means the model never spoke.

Do NOT report any of these three as a capability verdict. They are stack
eliminations, re-testable on a llama.cpp bump, and say nothing about the models.

Evidence: `arm-{kat-coder,qwen38-27b,workhorse}.server.log`, requests-served
counts, `results/coder-bakeoff.jsonl`.
Status: ACTIVE. Re-test on any llama.cpp build change; both mechanisms are in
young code.

## F104 - the blocker is TOOL-SCHEMA BYTES in llama.cpp's grammar builder (~70KB for workhorse), shared by BOTH endpoints; Claude Code's floor is 73KB

**Kind: PLATFORM**

Recorded 2026-08-29. This supersedes two wrong readings made earlier the same
day, both recorded because each was stated with confidence before being tested.

**Wrong reading 1: "it's llama.cpp's young Anthropic shim, and an OpenAI-native
harness would work."** Refuted. Replaying the captured 57-tool Claude Code
request against `Qwen3-30B-A3B-Instruct-2507` gives an identical failure on both
endpoints:

    anthropic /v1/messages         -> FAIL: failed to parse grammar
    openai    /v1/chat/completions -> FAIL: failed to parse grammar

The GBNF grammar builder is shared. Changing API dialect changes nothing.

**Wrong reading 2: "the threshold is 29 tools."** Also refuted - a count is the
wrong unit. Measured on the same model and server:

| tool set | tools | schema | result |
|---|---|---|---|
| first 29 of the captured array | 29 | 69 KB | **TOOL_USE** |
| Claude Code with `--strict-mcp-config` | 28 | **73 KB** | **FAIL** |

**FEWER tools failed while MORE tools passed.** The binding quantity is the
serialised size/complexity of the schemas, not how many there are - roughly 70 KB
for this model.

**The consequence is hard.** 73 KB is Claude Code's FLOOR: MCP servers fully
stripped, nothing left but built-ins. It is above the line, so Claude Code cannot
drive this model on this build **at any configuration**. `--allowedTools` does
not help either - it gates permission, not which schemas are transmitted.

**Why other people run these models as coding agents on this hardware anyway:**
they use harnesses that send far less schema. Aider sends a handful of tools;
Cline and opencode ~10 simple ones. Claude Code transmits 28-57 tools with rich
schemas because it is built for a frontier model with no grammar-construction
limit. The models are fine and the box is fine; the CLIENT is the outlier.

**Not universal across models** - it is the model's template plus the schemas
that build the grammar. `Qwen3-Coder-30B-A3B` accepts the full 57-tool array and
works. So the practical rule is per-model, and the cheap check is to replay a
captured real request rather than a synthetic one.

**Method note, the fourth of this bench.** Every synthetic probe built this
session was easier than the real client and gave the opposite answer: a
three-property tool passes on models that cannot serve Claude Code at all. The
capture-and-replay proxy (`tools/coder-bakeoff/capture_proxy.py`) is the only
instrument here that has not lied, because it replays the real artefact instead
of a plausible imitation of it.

Evidence: `capture/req-*.json` (57-tool and 28-tool captures, 183 KB and 73 KB);
both-endpoint replay above; the 69 KB/73 KB pair.
Status: ACTIVE. Re-test on any llama.cpp bump - the grammar builder is the thing
that would change.

## F105 - aider drives BOTH local models first-try, including the one Claude Code cannot drive at all: 761 tokens vs a 44,912-token floor

**Kind: PLATFORM**

Recorded 2026-08-29, testing the recommendation F104 implies.

`aider-chat 0.86.2` (pipx, user-level) against raw llama-server on the
OpenAI-compatible endpoint, same seeded bug used for every Claude Code test
(`add()` returns `a - b`, one failing pytest):

| harness + model | prompt | result |
|---|---|---|
| aider + Qwen3-Coder-30B-A3B | **761 sent / 56 received** | fixed, auto-committed, `1 passed` |
| aider + Qwen3-30B-A3B-Instruct (**workhorse**) | **761 sent / 18 received** | fixed, auto-committed, `1 passed` |
| Claude Code + workhorse | **44,912 floor** | cannot run at all (F104) |

**The second row is the point.** `workhorse` is the model the production relay
serves and the one Claude Code cannot drive at ANY configuration, because its
73 KB minimum tool payload exceeds what llama.cpp can build a grammar from.
Through aider the same model, same weights, same server, same build fixed the
bug on the first attempt and committed it with a sensible message.

**~59x less prompt.** aider sends 761 tokens where Claude Code's floor is 44,912
before a single project file is read. That ratio is the whole explanation for why
other people run these models as coding agents on this hardware without
difficulty: their client asks for something the stack can actually build.

**Routing consequence.** For local agentic coding on sparkmax, use aider (or
another small-tool-set OpenAI-native client). Claude Code locally works only with
Qwen3-Coder, which tolerates the 57-tool array; every other model tested is
blocked by the grammar builder rather than by ability.

Setup, for reproduction - no config file needed:

    OPENAI_API_BASE=http://127.0.0.1:<port>/v1 OPENAI_API_KEY=dummy \
      aider --model openai/<llama-server --alias>

Evidence: `scratchpad/aiderproj{,2}` git history (commits `2bba7bf`, `bfbf793`),
aider's own token counters, pytest output.
Status: ACTIVE.

## F106 - SparkMax's thin inference path is at or above its hardware class; the hardware/runtime branch CLOSES

**Kind: PLATFORM**

Recorded 2026-08-29 from E88 Phase A. This is the measurement the programme had
never made: every prior figure here was RELATIVE (q8_0 vs f16, model vs model,
client vs client) and none established whether the box itself is fast.

Production model, quant, build and backend, at the frozen relay config's KV
flags, fresh process per leg, `llama-bench`:

| | pp512 tok/s | tg128 tok/s |
|---|---:|---:|
| **this box, depth 0** | **1083.71 ± 7.82** | **90.67 ± 0.33** |
| published Vulkan RADV peers (Qwen3-30B-A3B, various Q4) | 604.8 - 755.1 | 72.0 - 101.0 |

**Decode sits inside the peer band and prefill is above every published pp512
figure found.** No peer row is our exact quantisation, KV type or build, and all
three mismatches are recorded in `results/e88-baseline.md` rather than smoothed
over - the two ~100 tok/s decode rows are SMALLER quants (IQ4_XS, Q4_K_S), which
on a bandwidth-bound machine is the expected direction.

**No thermal throttling.** Over a 237-second sustained leg at 100% busy, sclk
holds 2475-2547 MHz with no downward trend, 77-83 C, 84-85 W flat.

**The instrument reproduces itself**: a fresh process repeats depth 0 to -0.74%
prefill / +0.25% decode, inside the F15 noise floor.

**Consequence: stop investigating the kernel, driver, clocks and backend.** The
poor interactive experience is not the silicon and not the runtime. It is
allocated in F107.

**One registered control threshold was WRONG and is recorded as such.** The
CPU-only positive control was predicted at >=5x slower and measured 3.15x
prefill / 2.72x decode. The instrument plainly sees the GPU; the threshold failed
to allow for a 3 B-active MoE on 16 Zen 5 cores sharing the SAME unified memory,
where there is no PCIe transfer to lose. The prediction is falsified by the
ruler, not by the box.

**Not covered:** ROCm/HIP was not measured. The comparison was made
Vulkan-to-Vulkan deliberately, because that is what this box serves on. Whether
ROCm would be faster still is a separate question from whether the current stack
underperforms, which it does not.

Evidence: `results/e88-baseline.md`, `results/raw/e88/*.md`,
`results/raw/e88/*.telemetry.tsv`, `results/e88-prereg.md`.
Status: ACTIVE. Re-test on a llama.cpp bump, a kernel move, or a backend change.

## F107 - Claude Code does not run SLOWLY on the workhorse, it fails in 95 ms; and the context tax is paid once per conversation, not per turn

**Kind: PLATFORM**

Recorded 2026-08-29 from E88 Phases B2 and C. Tokenised by the SERVING model's
own tokenizer, replaying REAL captured requests rather than synthetic probes.

**Half one - the tool schemas are a hard failure, not a slow path.** Every
tool-bearing variant of both captures is refused before inference:

| variant | tools | schema bytes | outcome | elapsed |
|---|---:|---:|---|---:|
| 28-tool full (Claude Code's FLOOR) | 28 | 73,480 | REFUSED, `failed to parse grammar` | 0.095 s |
| 28-tool **tools-only** | 28 | 73,480 | REFUSED, same error | 0.050 s |
| 57-tool full | 57 | 97,011 | REFUSED, same error | 0.096 s |
| 57-tool **tools-only** | 57 | 97,011 | REFUSED, same error | 0.087 s |

**The `tools-only` rows are new and they isolate the cause.** They carry the tool
array with a one-line message and no large context, and they still refuse. So the
grammar builder is not defeated by prompt SIZE - 73 KB of schema is sufficient
alone. F104 established the byte threshold; this establishes that context is not a
co-factor.

**Consequence:** no latency work can improve Claude Code against this model. It is
a compatibility failure at 95 milliseconds. Only a client change or a llama.cpp
grammar-builder fix touches it.

**Half two - prefix reuse makes the context tax a ONE-OFF.** A 40,000-token prefix
sent four times to the same server:

| turn | TTFT | tokens actually prefilled |
|---|---:|---:|
| 1 - cold | **134.53 s** | 39,520 |
| 2 - identical prefix | **0.08 s** | 1 |
| 3 - identical prefix | 0.08 s | 1 |
| 4 - same prefix, NEW tail | 0.25 s | 7 |

**1,682x on turn 2**, and it survives a changed tail. Reproduced on the real
client payload: the same no-tools capture costs 47.03 s cold and 0.31 s warm,
**154x**.

**Any account of the interactive experience that multiplies a 45k prompt by the
turn count is wrong.** The cost is concentrated entirely in the cold start.

⚠ **The untested caveat, and it is the highest-value open question.** The server
runs `total_slots = 4` and its log shows `selected slot by LRU`. A turn routed to
a slot that never saw the prefix pays the full cold cost again. Whether that
happens in a real multi-turn session, and whether `-np 1` prevents it, is a
HYPOTHESIS read off a log line - not measured.

Evidence: `results/raw/e88/clients.json`, `results/raw/e88/cache-benefit.json`,
`results/e88-baseline.md`. C3 control: 20 requests served, so no row here is a
silent stack elimination misread as a timing.
Status: ACTIVE. Re-test the refusals on any llama.cpp bump.

## F108 - slot count is not the multi-turn variable; `--cache-ram` is, and writing `-np` down explicitly quarters your context

**Kind: PLATFORM**

Recorded 2026-08-29 from E89 arm A, 11 legs plus 3 forced-eviction legs and a
causal control. Build 067de93. Scored on `prompt_n` - llama.cpp's own count of
tokens it actually prefilled - rather than on latency, which is a consequence.

**Half one - `-np` explicit is a different configuration from `-np` auto.**
`--kv-unified` defaults on ONLY when the slot count is auto. Measured from the
server's own startup line, same binary:

| invocation | `n_slots` | `n_ctx_slot` | `kv_unified` |
|---|---:|---:|---|
| no `-np` (production relay) | 4 | 98,304 | `true` |
| `-np 4` explicit | 4 | **24,576** | `false` |
| `-np 1` explicit | 1 | 98,304 | `false` |

So setting `-np 4` on a relay that already auto-resolves to 4 slots reads as a
no-op and quarters every conversation's context. **Proved causal by a control:**
the identical 30,000-token prompt is refused at `-np 4` with
`request (30011 tokens) exceeds the available context size (24576 tokens)` and
served at auto slots in 82.4 s cold, then 0.417 s cached. The prompt is not at
fault; the flag is. Unlike F20 this fails LOUDLY rather than truncating silently.

**Half two - the multi-turn knob is `--cache-ram`, not `-np`.** Identical traffic,
identical slot counts, cache size the only difference:

| configuration | conversations | post-first turns cached | TTFT |
|---|---:|---:|---:|
| auto, `--cache-ram 8192` (default) | 6 | 12 of 12 | 0.51 s |
| auto, `--cache-ram 0` | 6 | **0 of 12** | **19.97 s** |
| auto, `--cache-ram 512` | 4 | **0 of 8** | **19.93 s** |
| `-np 1`, default cache | 4 | 8 of 8 | 0.51 s |
| `-np 1`, `--cache-ram 0` | 2 | **0 of 4** | 19.45 s |

`-np 1` and auto-4 are indistinguishable when the cache is adequate (0.51 s
against 0.55 s), and both collapse identically when it is not. Six conversations
against four slots did NOT thrash - the RAM prompt cache absorbs the slot pressure.
The mechanism is `--cache-idle-slots`, which saves an idle slot to the prompt cache
on a new task and clears it under unified KV; whether the next turn is fast depends
on whether the prefix is still in that cache, not on which slot it lands in.

**The recommendation is therefore to change nothing about `-np`, and to treat
`--cache-ram` as the interactive-latency setting.**

**Instrument note, and the reason this finding is trustworthy.** As first
registered, arm A could not observe eviction at all: the leg designated as the
forced-eviction positive control cached every turn, because four slots holding two
conversations never clear a slot. Every registered traffic size sat at or below the
slot count, so "no eviction observed" was indistinguishable from an instrument
incapable of showing it - vacuous success. Three legs were added that force
eviction and all three fired, which is what makes the other legs' cache hits
evidence rather than an artefact.

**Not established.** The eviction boundary at production conversation sizes is
unmeasured; `--cache-ram 512` cached at 2 conversations and evicted at 4 with a
working set above the limit in BOTH cases, so bytes-per-token arithmetic is not
shown to predict the boundary and no capacity figure is claimed from it (leg A10).

## F109 - the "~60 GiB" deadlock boundary does not exist on kernel 7.0.0-29, and neither does the contention trigger

**Kind: PLATFORM**

Recorded 2026-08-29 from E89 arm C (5 rungs) and leg C6 (deliberate contention
reproduction). Llama-3.3-70B-Instruct-Q4_K_M, 39.6 GiB weights, f16 KV, fresh
process per rung, production relay co-resident throughout. `gtt_peak` is absolute
`mem_info_gtt_used` and includes the relay's ~26.2 GiB.

**Arm C - size alone, quiet box.**

| ctx | load | absolute GTT | `read_bytes` | served | `drm_suballoc_new` |
|---:|---:|---:|---:|:-:|:-:|
| 8,192 | 24.1 s | 67.97 GiB | 39.61 GiB | yes | 0 |
| 30,801 | 11.0 s | 74.97 GiB | 2.67 GiB | yes | 0 |
| 63,569 | 13.0 s | 85.03 GiB | 7.48 GiB | yes | 0 |
| 96,337 | 16.0 s | 95.09 GiB | 10.72 GiB | yes | 0 |
| 129,105 | 25.1 s | **105.15 GiB** | 28.00 GiB | yes | **0** |

**Leg C6 - the contention reproduction, deliberately designed to wedge the box.**
F24's instance was a 62 GB `sha256sum` alongside a ~68 GiB load, and C1 reproduced
it with a hash loop. C6 ran a `sha256sum` loop over **121.6 GiB** of GGUFs - more
than total RAM, so it can never fully cache - started first and kept running, then
loaded the exact 129,105-context invocation above against it.

Conditions reached and held: **108 GiB used of 121, 0 GiB free**, 12 GiB available,
3 GiB swap in use, 105.2 GiB GTT. That is the C1 mechanism in full.

Result: **loaded in 32.3 s, served 10 of 10 requests in 0.82-1.12 s, 0
`drm_suballoc_new` samples across 151+ watchdog samples.** Load under full
contention was only 29% slower than the same invocation on a quiet box.

**The leading explanation is the kernel, and it is a HYPOTHESIS not a result.**
F24 (2026-07-08) and C1 (2026-07-10) both fall inside F57's 6.17.0-35 boot window.
This box now runs **7.0.0-29-generic**, and amdgpu is in-kernel. A fix between
6.17 and 7.0 fits every observation. It is not established: testing it would mean
booting 6.17.0-35, which was not done.

**What is and is not claimed.** As of 2026-08-29 on kernel 7.0.0-29, neither load
SIZE (to 105 GiB) nor the CONTENTION shape the doc names reproduces the deadlock.
A null result is weaker than a reproduction - one failed attempt is not proof the
trigger is gone - and two conditions remain untested: F27's cumulative-state
hypothesis (82 GiB, no I/O identified, after ~13 load cycles; this ladder did 5),
and the original GLM-4.5-Air model and backend state.

**This does not contradict `docs/memory-edge-deadlock.md`.** That document already
records a 103 GB model running clean on a quiet box and states in its own words
that weight size PLUS contention is the trigger. What E89 falsifies is the reading
of the one-line CLAUDE.md summary as a size boundary, and it additionally fails to
reproduce the contention trigger the doc does assert.

**Prediction scoring.** C-P1 confirmed. C-P2 **falsified as written** - registered
`read_bytes` under 1 GiB on rungs after the first, measured 2.67 GiB; the direction
is emphatic (93% reduction, load 24.1 s -> 11.0 s) but the threshold was wrong and
is recorded falsified, not restated. C-P3 not triggered. C-P6 falsified, C-P7
confirmed.

## F110 - KV cache precision: q8_0 is free, 4-bit is a 5.6% cliff, and 100 perfect retrievals measured none of it

**Kind: PLATFORM**

Recorded 2026-08-30 from E89 arm B. `llama-perplexity` built from the same commit
(067de93, Release, `GGML_VULKAN=ON`); corpus is this repository's own prose
(`docs/` + `reports/`, 420,959 words), 40 chunks at `-c 8192`, identical across
every leg so cache type is the only variable.

| KV precision | PPL | vs `f16` | KV at `-c 98304` | bytes/token |
|---|---:|---:|---:|---:|
| `f16` | 9.4094 +/- 0.06940 | - | 9.09 GiB | 99,328 |
| **`q8_0` (production)** | **9.4110 +/- 0.06939** | **+0.017%** | **4.88 GiB** | **53,251** |
| `q4_1` | 9.9359 +/- 0.07321 | +5.60% | 2.91 GiB | 31,738 |
| `q4_0` | 9.9511 +/- 0.07355 | +5.76% | - | - |

**The cost is a cliff at the 8-bit/4-bit step, not a slope.** `q8_0` is 1/40th of
one stderr away from full `f16`. `q4_0` is only 0.15% worse than `q4_1`, so the two
4-bit variants are equivalent to each other and both are bad. Per GiB saved against
`f16`: `q8_0` costs **0.0040%** PPL, `q4_1` costs **0.9054%** - 226x worse.

**Do not adopt `q4_1`.** It buys 1.6x context (164,937 tokens for the memory
production spends on 98,304) at 5.6% quality. The deployed `q8_0` is the correct
setting and is now measured rather than assumed.

**This finding exists because a different instrument could not see any of it.**
The retrieval sweep that preceded it is now **F126**, split out on 2026-09-01 as
its own METHOD finding; the short version is that 100 scored retrievals returned
30/30 for every precision including a control chosen because it should have
failed, and perplexity then separated them immediately.

Predictions: B-P8 confirmed (ordering exact, spread 5.76% > 1%). B-P9 **falsified**
(registered `q4_1` within 0.5% of `q8_0`; measured 5.58%). B-P4 and B-P7 falsified -
neither the decoy sweep nor the `q4_0` control discriminated.

## F111 - `-ub 2048` is worth 22.9% on real prefill; speculative decoding is inapplicable; concurrency is serial

**Kind: PLATFORM**

Recorded 2026-08-30 from E89 legs B9, B10, B11. Production model and KV precision.

**B9 - physical batch size.** `-ub` has sat at its 512 default. Prefill tok/s:

| `-ub` | pp512 | pp4096 | pp4096 vs default |
|---:|---:|---:|---:|
| 512 (default) | 1033.13 +/- 4.85 | 805.05 +/- 0.22 | - |
| 1024 | 960.85 +/- 5.89 | 933.09 +/- 2.10 | +15.9% |
| **2048** | 961.02 +/- 8.66 | **989.49 +/- 0.64** | **+22.9%** |

The default is tuned for short prompts and costs 22.9% on long ones. Real first
turns here are 20,000-40,000 tokens (E88 measured 39,275), where prefill dominates
end-to-end latency, so `-ub 2048` is the right setting for this workload at a 7%
cost on 512-token prompts.

**B10 - speculative decoding is structurally inapplicable on this model.** A draft
must be much faster than its target. Measured: Qwen3-8B dense `tg128` =
**43.23 +/- 0.04** tok/s against Qwen3-30B-A3B's **89.89 +/- 0.86**. The only
plausible on-disk draft is **2.08x SLOWER than the model it would draft for**,
because the target is a 3B-active MoE and the draft is dense. The axis is closed by
measurement, not by assumption; it would reopen only with a genuinely small
(0.6B-1.7B) same-vocab draft.

**B11 - concurrency buys fairness, not throughput.** 4,096-token prompts, 128
predicted, unique prefix per request so none rides another's cache:

| concurrent | wall | aggregate tok/s | TTFT median | TTFT max | wall vs 1 |
|---:|---:|---:|---:|---:|---:|
| 1 | 5.83 s | 21.97 | 4.11 s | 4.11 s | 1.00x |
| 2 | 12.06 s | 21.22 | 6.85 s | 9.17 s | 2.07x |
| 4 | 24.50 s | 20.90 | 13.87 s | 18.90 s | 4.20x |
| 8 | 50.55 s | 20.26 | 24.69 s | 44.95 s | **8.67x** |

Eight concurrent requests take 8.67x the wall of one and aggregate throughput
*falls* 7.8%. The box is saturated by a single request; the four slots share it
rather than add to it. **Running a second agent does not halve your wait, it
doubles it** - which is a scheduling answer, not a capacity one. Aggregate here is
decoded tokens over total wall and so includes prefill; it is end-to-end
throughput, not pure decode.


## F112 - Aider on the resident workhorse is fast enough to be invisible: a 3.9 s median first turn against Claude Code's 136.8 s

**Kind: PLATFORM**

**E90, 2026-08-30.** 36 requests measured on the wire by `tools/aider_probe.py`, a recording
pass-through proxy in front of the production `llama-server` (PID 1385933, build
`b9865-067de9371`, `-c 98304 -fa on -ctk q8_0 -ctv q8_0 -ub 2048`, slots auto).

| | min | median | max |
|---|---:|---:|---:|
| first-turn latency, cold | **1.63 s** | **3.89 s** | 8.22 s |
| prefill | 697 tok/s | 870 tok/s | 1,085 tok/s |
| decode | 68 tok/s | 76 tok/s | 83 tok/s |
| whole task | 5.7 s | 28.8 s | 34.3 s |

First-turn prompts ran 1,219-3,866 tokens. Against F98's 44,912-token Claude Code floor and
F107's 136.8 s first turn on the same box, **Aider's first turn is ~30x smaller and ~35x
faster**. Four requests returned `prompt_n == 1`, the prompt cache serving a repeated prefix.

**Latency is not the obstacle to local agentic coding on this box, and no further latency work
is warranted.** F113 is the obstacle.

Measured on loopback. The authenticated `:8000` door was **not** measured - `keys.txt` is
`0750 spark-infer` and the key is absent from this host's vault checkout, so the Caddy plus
auth-sidecar hop is an unquantified addition to every figure above.

Evidence: `results/e90-aider-workflow.md`, `results/raw/e90/`.


## F113 - Aider exits 0 whether or not it did anything: nine runs, nine zeros, four of them no-ops

**Kind: METHOD**

**E90, 2026-08-30.** Across nine task-runs, `aider` returned exit status **0 every time**,
including:

- four runs where `files_touched` was **empty** - it discarded an incomplete edit, asked for
  more files, and replied that the change was "complete and correct";
- four runs where it wrote a `pytest.ini` that pytest silently ignores (F114), printing
  `Applied edit to pytest.ini`.

**A local agentic coding workflow that branches on the tool's exit status will report success
indefinitely.** The only thing that separated a working change from an inert one was running a
command afterwards. `tools/local-code` therefore refuses to print a verdict without `--verify`
and exits 2 rather than implying one.

This generalises past Aider: the same shape - a confident success message over an unapplied or
inert change - is what F107a found breaking Claude Code differently, and what E89's "a control
that cannot fail is not a control" says about instruments.

Evidence: `results/e90-aider-workflow.md`, `results/raw/e90/*.json` (`aider_rc` on every row).


## F114 - the edit format decides which jobs work, and no single format does both

**Kind: MODEL**

**E90, 2026-08-30.** Three real defects, three Aider edit formats, one model and one endpoint
throughout. `pass` requires the verify to have failed before and passed after.

| task | `whole` (Aider's own pick) | `diff` | `diff-fenced` |
|---|---|---|---|
| create `pytest.ini` | fail | fail | fail |
| create a file from a read-only 13-assertion spec | **pass 13/13** | fail 2/13 | fail 12/13 |
| edit two existing files | fail, 0 files touched | fail | **pass** |

**`whole` cannot edit an existing file with this model.** It reproduced 31 of 72 lines (43%),
25 of 56 (45%) and 31 of 72 again, then stopped and declared itself finished. This is not an
output cap: asked directly with `max_tokens` unset the server returned 1,492 tokens with
`finish_reason: "stop"`. Splitting the task to one file per invocation did not help - the
elision is per file, not per request.

**`diff` is worse than either and costs more.** It failed all three and raised T1's first-turn
prompt from 1,403 to 3,621 tokens, because its system prompt carries worked examples.

Aider picks `whole` on its own here, because this model id is unknown to litellm. **The
operating rule: `diff-fenced` to edit, `whole` (`--new`) to create.** Encoded as the default
in `tools/local-code`.

Evidence: `results/e90-aider-workflow.md`, `results/raw/e90/run{2,3,5}-*.json`,
`results/raw/e90/fmt-*.json`.


## F115 - a plausible, reproducible, silently inert fix: `[tool:pytest]` four times out of four

**Kind: MODEL**

**E90, 2026-08-30.** Asked to create a `pytest.ini` stopping collection descending into the
vendored `llama.cpp/` tree, the model wrote, identically on all four attempts across three edit
formats:

```ini
[tool:pytest]
testpaths = tests
norecursedirs = llama.cpp
```

`[tool:pytest]` is the **`setup.cfg`** section header. In `pytest.ini` it must be `[pytest]`, so
the file is parsed, ignored, and the defect survives. One attempt's instruction explicitly said
"take care to use the section header that `pytest.ini` itself requires"; it made no difference.

Three properties make this the failure mode worth naming, not the arithmetic of one wrong file:

1. **It is stable**, not a sampling artefact - 4 of 4, three formats.
2. **It is not detectable by reading the diff.** Three lines, correct keys, correct values, one
   wrong word.
3. **Every layer above it reported success** - Aider applied the edit and exited 0 (F113).

**Corollary for code quality generally:** the one task the model completed correctly (F114's
13/13) still carried **26 ruff findings** - two unused imports, three dead locals, `Dict`/`Union`
under `from __future__ import annotations`. Green tests are not a clean file; lint before review.

Evidence: `results/e90-aider-workflow.md`,
`results/raw/e90/T2-model-output-sparkrouter_discovery.py` (verbatim), `results/raw/e90/*.json`.

## F116 - Qwen3.8-Flash-Next MATCHES the incumbent and never beats it, for 5.6x the memory and exclusive occupancy of the box

**Kind: MODEL**

Status: confirmed (2026-08-31, E91, pre-registered `results/e91-prereg.md`
before any arm; relay down for every arm so Rule 9 is satisfied).

| arm | l4 walked | l4 total | l3 | weights |
|---|---|---|---|---|
| workhorse Qwen3-30B-A3B | 0/8 | 6/15 | 4/12 | 17.28 GiB |
| **Qwen3.8-27B `low`** | **7/8** | **14/15** | **12/12** | **15.66 GiB** |
| Flash-Next `low` | 6/8 | 13/15 | 12/12 | 87.25 GiB |
| Flash-Next `medium` | 7/8 | 14/15 | 12/12 | 87.25 GiB |

**The registered primary prediction is FALSIFIED.** P1 required >= 7 of 8 walked
periods at effort matched to the incumbent; Flash-Next scored 6/8. Arm D reaches
7/8 at `medium` but was registered as optional and exploratory, and does not
retroactively satisfy a prediction that named the matched arm. State it as:
falsified at matched effort, parity one tier up.

**Parity turns on ONE item.** `low` and `medium` differ only on F1 `fee_basis` -
EUR 79,200 against the correct EUR 106,800 - and are otherwise identical, N2
included. The entire distance between "below the incumbent" and "level with it"
is one question a larger reasoning budget recovers. That is F71 (effort dominates
this family) shown more cleanly than F71's own evidence, because nothing else
varies between the two arms.

**It is faster per query and cannot be resident.** 413-682s against the dense
27B's 598-804s - the MoE active-parameter advantage, honestly measured. But
87.25 GiB against 121 GiB of RAM means it cannot share the box with production
and cannot join a two-model serve, so the comparison is not "which model", it is
"this model or everything else".

**Operationally: the routing guide does not change.** Qwen3.8-27B keeps the
document and date rows. Flash-Next is not a dud - it is far above the workhorse,
12/12 on cross-document work, 0 over-claims, perfect citations - it is simply
not a displacing model on these axes.

**The framing caveat, stated because it may be the thing that is wrong.** This
measured capability per query. The 2026-08-31 SparkMax workload briefing argues
for a different target - useful work completed per day, unattended - under which
a model answering 14/15 overnight on an idle box scores differently. E91 does
not settle that, and no result here should be quoted as if it had.

Evidence: `results/e91-results.md`, `results/raw/e91/`, scorer
`tools/e91/score_e91.py`.

## F117 - a control that reproduces its own ITEMS, not just its score, is what licenses a cross-build comparison

**Kind: METHOD**

Status: confirmed (2026-08-31, E91).

Flash-Next's architecture merged upstream on 2026-08-27, so it runs only on
`daef7b687` and cannot run on the builds that produced F74 and F80 at all. E85
established that build-to-build extrapolation is **unsafe for correctness**,
which is precisely the axis E91 measures. A comparison against the frozen
figures would have been two rulers.

Both incumbents were therefore re-run on the new build, and predictions 3 and 4
were registered as gates: `tools/e91/score_e91.py` prints **NO VERDICT** for the
challenger if either fails, rather than reporting it against figures from a
moved instrument.

**They reproduced their individual items, which is a far stronger result than
matching totals:**

- the workhorse returned `30 October 2026` and `107.56` - the exact wrong
  answers F82 quotes as its documented failures;
- on l3 it failed `precedence 0/2` and `multihop 0/3`, word-for-word the routing
  guide's description of it;
- Qwen3.8-27B's only miss was N2 at `1 December 2026`, the item the guide says
  "has never moved" - unmoved on a build that did not exist when that was
  written.

**The transferable rule: when a new model forces a build change, re-run the
incumbents rather than quoting frozen figures, and gate the challenger's verdict
on the controls reproducing.** The cost is most of the session - two of the four
E91 arms were controls - and it is what makes the fourth arm mean anything. A
scorer that reports a comparison it cannot justify is the vacuous-success class:
a result that looks like a measurement and is not one.

**Corollary found the same day: l3 at 9 distractors is now saturated** for
capable models - three arms at 12/12 with zero over-claims. It remains a
workhorse-vs-capable discriminator and is no longer a capable-vs-capable one.
Separating Flash-Next from Qwen3.8-27B on cross-document work needs a harder
tier that does not exist yet.

Evidence: `results/e91-results.md`, `results/raw/e91/`, F74, F80, F82, E85.

## F118 - F80's "small models cannot walk a calendar" is a fact about the WORKHORSE, not about ~3B-active MoEs as a class

**Kind: METHOD**

Status: confirmed (2026-08-31, E92, pre-registered `results/e92-prereg.md`;
relay down for every arm; controls are E91's same-build arms from the same day).

| model | l4 walked | l4 total | l3 | weights |
|---|---|---|---|---|
| workhorse Qwen3-30B-A3B | **0/8** | 6/15 | 4/12 | 17.28 GiB |
| **Nemotron-3-Nano-30B-A3B** | **7/8** | **14/15** | 8/12 | **22.96 GiB** |
| Qwen3.8-27B `low` | 7/8 | 14/15 | 12/12 | 15.66 GiB |

Nemotron-3-Nano is 31.58B total with ~3.5B active - the same architecture class
as the workhorse, and slightly larger on disk. It scores **7 of 8 walked
periods where the workhorse scores 0 of 8**, matching Qwen3.8-27B exactly. The
registered hypothesis put it at 0-2 of 8 and the registered falsifier fired.

**So F80 must be read narrowly from now on.** Its finding is real and reproduced
today item-for-item (F117), but it is a fact about Qwen3-30B-A3B. Active
parameter count does not predict whether a model can count a period across a
calendar, and no routing advice should generalise from the workhorse to "small
MoEs".

**It is NOT a drop-in replacement, and the reason is the liability axis.** On
cross-document work it scores 8/12 against 12/12 for both capable models,
failing `precedence`, `multihop` and `exhaustive` - and it **over-claimed on the
unanswerable item** where both capable models returned `NOT_IN_PACK`. That is
the F79/E76 shape: a confident answer where the correct output was a decline. A
model that walks a calendar perfectly and invents an answer when the pack is
silent is not safer than the workhorse, it is differently unsafe.

**No routing change is proposed on this evidence.** The arm ran at `default`
effort against the incumbent's `low`, so it is not effort-matched. The
follow-up it justifies is Nemotron at matched effort on l4, l3 and the E76
abstention bank.

**Provenance worth noting:** this model was fetched on 2026-08-19 for an E61
follow-on that never ran, and sat unmeasured until an audit separated "in the
manifest" from "on disk" from "measured". The audit was worth more than the
experiment it enabled.

Evidence: `results/e92-results.md`, `results/raw/e92/`, F80, F117.

## F119 - a "coding specialist" that does not TERMINATE, and why the score is not the finding

**Kind: MODEL**

Status: confirmed (2026-08-31, E92). Kwaipilot KAT-Coder-V2.5-Dev-Q4_K_M, a
Qwen3.5-35B-A3B derivative, on the 8-task expert coding bank.

| max_tokens | truncated | completed |
|---|---|---|
| 4,096 | 7 of 8 | 1 error |
| **16,384** | **6 of 8**, each consuming the ENTIRE budget | 1 error (292 tok), 1 wrong answer (10,691 tok) |

Quadrupling the budget bought one completed task. Six tasks still burn every
token available and emit no code, which reads as **non-termination rather than
insufficiency**.

**The Rule 13 gate refuses to score this, and that is the finding's shape.**
Passes are bounded 0..6, so H2's `>= 3` band is straddled and H2 is
**UNSCORABLE**; `sliding_median` was itself truncated, so H3 is UNSCORABLE too.
Only H1 survives - the vendor's SWE-bench uplift did not appear on this bank -
because its `<= 7` verdict holds at both bounds.

**State what that does and does not say.** It does not say the model is bad at
coding: an external leaderboard puts KAT Coder top of its code-specific subset
at 8.0, and its general document ability here is intact at **12/15 on l4**,
double the workhorse. Both can be true if its reasoning does not terminate under
this harness's prompt and cap. The general lesson - that a public ranking and
local usability are different properties, and that a refused score leaves
hypotheses UNSCORABLE rather than failed - is split out as **F127** (2026-09-01).

The remaining lever is a DECLARED configuration change, not a repair: the
template honours `enable_thinking`, so `--thinking off` asks whether it can code
when not permitted to ruminate. Registered as its own arm because turning
thinking off changes what is measured.

Evidence: `results/e92-results.md`, `results/raw/e92/e92-kwaipilot-expert*.json`,
HARNESS-RULES Rule 13.

## F120 - the community's Strix Halo speed table verifies twice on our own hardware

**Kind: METHOD**

Status: confirmed (2026-08-31, E92 bench legs, `llama-bench`, build `daef7b687`).

| model | architecture | tg128 | pp512 |
|---|---|---|---|
| Qwen3-30B-A3B | MoE ~3B active | **92.28** | 1140.72 |
| Kwaipilot (Qwen3.5-35B-A3B) | MoE ~3B active | 70.00 | 984.04 |
| Nemotron-3-Nano | hybrid Mamba-Transformer MoE | 64.52 | 890.83 |
| Qwen3.8-27B | **dense** | **12.59** | 294.57 |

Two owner-supplied community sources claim **10-14 t/s for dense >=27B** on this
chip; we measure **12.59**. They claim **58-78 t/s for 35B-A3B**; Kwaipilot, a
35B-A3B derivative, measures **70.00**. Their figures were sourced from a
**Framework Desktop**, a different machine, so two independent confirmations
materially raise the credibility of the rest of that table - including its
entries for models this programme does not hold.

**Also measured: architecture costs throughput within the MoE family.** The
hybrid Mamba-Transformer lands 30% below the standard MoE of comparable active
parameters (64.52 against 92.28), falsifying E92's H6 which registered a 25%
band. Active parameter count is not sufficient to predict decode rate.

Evidence: `results/raw/e92/e92-*-bench.md`, `docs/DEFERRED-REGISTER.md` item 14
and 15 (the claims as supplied), F41.

## F121 - the harness scored a run that never happened, and only a person had ever caught it

**Kind: METHOD** - what this taught about measuring, not about any model.

**Status:** measured 2026-08-31 by deliberate fault injection, E97. Scope tag:
**general**, for `tools/run_ps_eval.py`. `tools/run_coding_eval.py` carries its
own copy of the Rule 13 gate and was NOT tested here.

**Pre-registration:** `results/e97-prereg.md`, written before any fault ran.
Result: `results/e97-faults.md`. Raw: `results/raw/e97/`.

**The defect.** `transport_failed` items were counted in `total` and nothing
gated on them, so an item the model never answered was scored as though it had
been answered and got the question wrong.

A fake server killed after answering 3 of 20 items produced:

```
exit 0    correct: 1, total: 20    truncation_gate: PASS
```

**No reader or script can tell that file from a model that sat the whole bank
and got 19 questions wrong.** A malformed 200 OK - valid JSON with no `choices`
key - did the same at 20 of 20, also exit 0, also a passing gate.

**Why it survived Rule 13.** Rule 13 was written from ONE real case (E92's
truncated coding arm) and covers exactly that case: an answer cut off at the
token cap. It never covered an answer that never arrived. Both are the same
observation - the model was never asked, or its reply was lost - and both put
the TRANSPORT into a number read as capability.

**The historical position, stated precisely.** 17 committed result files
(excluding E97's own) carry `transport_failed` items. The two severe cases are
documented in terms by a person: E61's twelve, from the decode hang in
`docs/2026-08-19-gptoss120b-decode-hang.md`, and E33's four, in
`resolve_request_timeout`'s own docstring. **Nothing was silently wrong that a
person had not already noticed - and that is the finding, not a reassurance.**
The defence was attention. Rule 13 exists because attention is not a mechanism.

**One published restatement is confounded, and its scope is narrow.**
`reports/2026-08-16-technical-complete-summary.md:245` quotes four E37 Qwen3.8
cloud runs as `6/20, 19/20, 11/20 and 12/20` to illustrate cloud
non-determinism. Those arms dropped 13, 1, 9 and 8 of 20 requests:

| arm | reported | never answered | correct / completed |
|---|---|---|---|
| `qwen38-cloud` | 6/20 | 13 | 6/7 |
| `qwen38-cloud-complete` | 19/20 | 1 | 19/19 |
| `qwen38-cloud-rep2` | 11/20 | 9 | 11/11 |
| `qwen38-cloud-rep3` | 12/20 | 8 | 12/12 |

48 of 80 requests never returned, so the 6-to-19 spread is transport, not the
model answering differently.

**Two limits on that correction, and both matter:**

1. **F66 IS UNAFFECTED AND STANDS.** Its evidence is `gemini-3.7-flash`
   (20/20, 20/20, 20/20) and `upstage/solar-pro4` (15/20, 16/20, 15/20), and
   **all six of those arms have zero `transport_failed`**. Its sharpest case,
   `solar-pro4` returning 19.1%, 19.4%, 19.3%, 19.4% for one arithmetic item,
   is untouched. The confounded figures are a restatement in one report.
2. **The completed-only column is not a corrected score.** Transport failures
   need not be random - E33 showed the longest generations time out first - so
   the surviving items may be the easier ones. The claim is that the four
   reported figures are invalid AS SCORES, not that the model was really 48/49.

**The fix.** Rule 14: count them, record a `transport_gate`, exit 4 rather than
report a score, `--allow-transport-failures` to declare a run whose failures
are already understood. Proved by re-running E97 against the repaired harness -
faults 2 and 5 now exit 4 - and held by `tests/test_transport_gate.py`, whose
first test is the positive control that a clean run still passes.

**What it does not fix, declared.** The result file is still WRITTEN before the
gate returns, so `"correct": 0` sits on disk beside `"transport_gate": "FAIL"`.
E97's pre-registration asked for "no result file a reader could quote a
`correct` count from" and **that clause is NOT met** - by either gate, including
Rule 13's, which has always had this shape. Withholding the number touches 12
consumer tools and is a separate decision, so it is recorded as unmet rather
than reinterpreted.

## F122 - abliteration cost this model nothing measurable, on either kind of refusal

**Kind: MODEL** - what this taught about a model. E93's method findings are
F123 and F125, recorded separately under the two-findings convention.

**Status:** measured 2026-08-31, E93. **Scope tag: MODEL** - one
base/abliteration pair, one quant, one effort setting, two banks, one build.

**Pre-registration:** `results/e93-prereg.md`. Result:
`results/e93-abliteration.md`. Raw: `results/raw/e93/`.

**The question.** Abliteration suppresses the activation directions that
produce a *safety* refusal. Does it also remove *epistemic* refusal ("that is
not in the documents you gave me") and *professional* refusal ("I won't help
you structure that")? If those share a mechanism, an abliterated model is
dangerous in advisory work - not because it is rude, but because it answers
confidently where the correct output was a decline.

**Result: it did not.** `Huihui-Qwen3.8-27B-abliterated-Q4_K` against its own
base `Qwen3.8-27B-Q4_K_M`:

| bank | field | BASE | ABL |
|---|---|---|---|
| l4 | correct | 14/15 | 14/15 |
| l4 | over_claims | 0/1 | 0/1 |
| l4 | citation_valid | 15/15 | 15/15 |
| pr1 | correct | 12/12 | 12/12 |
| pr1 | missed_flag / over_flag | 0 / 0 | 0 / 0 |

**All 27 graded items across both banks came out the same for both models,
including the single item they both got wrong** (l4 N2, `off_by_calendar`).

**Why the negative is worth something.** The base was deliberately NOT at the
floor - E93 paired against the 27B rather than the workhorse on that control
property, and pr1's 12/12 confirms it. And the treatment is present: zero of
the 12 pr1 answers are byte-identical between arms, and the abliterated build
generates materially more (median 729 vs 521 completion tokens). Same verdicts,
different words, every time.

**Four limits, and the third is the one that bites:**

1. **pr1 is saturated at 12/12 on both arms**, so the bank has no headroom to
   show a smaller effect than "none".
2. **n is small** - 12 pr1 items, and l4's `over_claims` measure has **n=1**,
   which cannot carry a primary hypothesis.
3. **No positive control proves the safety refusal was actually removed.** E93
   measured degradation of epistemic and professional refusal; it never
   measured whether this build's safety refusal is gone. The finding is
   therefore conditional on the model being abliterated as advertised - a build
   whose abliteration silently did nothing would produce this exact result.
   Not registered, and the sharpest gap in the design.
4. **The E76 abstention bank could not run** - it fails its own load gate on
   the pre-existing U02 defect, so the second half of the primary hypothesis is
   unmeasured. Diagnosis and the narrow repair are in the result page.

**What it changes: nothing, and that is the finding.** No routing, purchasing
or client-use decision moves on this evidence. It closes a worry that was
worth pricing rather than opening a line of work.

**Do not generalise it.** This is one pair. Nothing here licenses a claim about
abliteration as a technique, about Huihui's other builds, or about uncensored
models as a class. F118 is this repo's worked example of exactly that error.

## F123 - a readiness check that does not exercise the path under test certifies nothing

**Kind: METHOD**

**Status:** measured 2026-08-31, E93. Scope tag: **general**.

E93's `pr1` tier was registered in `run_ps_eval.TIERS` with its pack, its
questions, its grader and its categories all present and correct. `run_e93.sh
--dry-run` passed and the experiment was recorded READY TO RUN in `HANDOFF.md`.
Both `pr1` arms then died **four seconds** into an open maintenance window on
`KeyError: 'question'` - the bank keys its instruction text as `q` and the
shared template asks for `question`.

**The dry-run could not have caught it.** It exercised preflight, the model
path, the MANIFEST check and the window, then printed `DRY-RUN: would run BASE
pr1` and stopped. It never built a prompt, never called the grader, never
touched the bank. A readiness check that skips the only path the experiment
depends on is a **vacuous success**: it reports readiness while measuring
something else.

**This is F100 restated at a different layer**, and the corpus already had the
rule. F100 says a gate needs its own positive control run BEFORE the arms. A
dry-run IS a gate - on whether the experiment can run at all - and it had no
positive control.

**The repair generalises rather than patching the instance:**
`tests/test_ps_eval_tiers.py` builds a prompt for every question of every
registered tier, and `tools/validate_ps_eval_pr1.py` drives the grader with six
synthetic respondents whose outcomes are fixed in advance. Both are
parameterised over `TIERS`, so the next tier added is covered on the day it is
added rather than on the day it is first run against a model.

**Cost of the instance:** one maintenance window, two arms, and a re-run.

## F124 - model metadata can falsify an experimental arm before it is run

**Kind: METHOD**

**Status:** measured 2026-08-31, E98/E99. Scope tag: **general**.

The queue carried an arm reading "Nemotron and Kwaipilot at `--thinking low`,
to match the incumbent's effort setting". Reading `tokenizer.chat_template`
straight out of the GGUF headers - about two minutes, no model load, no GPU -
settled it:

| model | `reasoning_effort` in template | `enable_thinking` in template |
|---|---|---|
| Nemotron-3-Nano-30B-A3B | **absent** | present |
| Kwaipilot KAT-Coder-V2.5 | **absent** | present |

`run_ps_eval.py --thinking low` sends `reasoning_effort` in the payload. A
template that never references it ignores it, so **the arm would have been
byte-identical to `default` while the result file recorded `thinking: "low"` as
applied.** The incumbent has three effort levels and these two have two states,
on and off, so no matched-effort comparison exists for the pair at all.

**The empirical route would not merely have been more expensive - it would have
produced a wrong answer**, and entered the record as an effort-matched
comparison. This is F39's inert-flag class, found before the run rather than
after it.

**The general form:** before a costly experiment, ask whether code, model
metadata or protocol mechanics already determine the answer. Record the
mechanistic check even when it does not settle the question, so the next
session knows it was asked.

## F125 - a test double unfaithful on the axis under test produces a false green

**Kind: METHOD**

**Status:** measured 2026-08-31, E97/E94. Scope tag: **general**.

E97's fake `llama-server` did its job: driving the real `run_ps_eval.py` end to
end against it found a defect no unit test would have reached (F121).

**Then the same double caused one.** Its `/tokenize` endpoint accepts any
request. The real llama.cpp **router** returns **HTTP 400 unless the request
names a model**, because in router mode it cannot choose a tokenizer on its own.
Three E94 context-ceiling arms failed on that 400, and the first reading of it
was wrong in a way that would have entered the record as a finding: it looked
like a large prompt being refused for size - a context ceiling - and it was the
tokenizer call failing before any prompt was sent.

**A double is faithful on some axes and not others, and the dangerous case is
when the unfaithful axis is the one under test.** It is worse than no test,
because a green from a trusted double is acted on.

**The rule:** a double states which axes it is faithful on. E97's fake is
faithful on completion shape, `finish_reason`, offload-evidence logging and
health; it is **not** faithful on routing, tokenizer selection, or any
per-model behaviour. Anything measuring those must be verified against the real
server before its result is believed.

**Corollary, and it is the cheap half:** where a double is used to verify a new
instrument, give the double a **known answer** and check the instrument finds
it. The `ctxlimit` fault was added for exactly this - a hard 5,000-token limit -
and the ceiling search bracketed it at 4,883 served / 5,358 refused before being
pointed at the GPU.

## F126 - a saturated instrument cannot compare anything, including the thing it was chosen to compare

**Kind: METHOD**

**Status:** split out of F110 on 2026-09-01 under the two-findings convention.
Measured 2026-08-30, E89 arm B. Scope tag: **general**.

Before perplexity settled the KV-precision question, arm B ran a needle sweep at
4,096-65,536 tokens across five depths, then a harder sweep with five decoy
records of identical form:

| precision | plain | decoy | total | misses | decoys returned |
|---|---:|---:|---:|---:|---:|
| `f16` | 20/20 | 10/10 | 30 | 0 | 0 |
| `q8_0` | 20/20 | 10/10 | 30 | 0 | 0 |
| `q4_1` | 20/20 | 10/10 | 30 | 0 | 0 |
| `q4_0` (degradation control) | - | 10/10 | 10 | 0 | 0 |

**Every arm saturated, including the control chosen because it should have
failed.** On that evidence `q4_1` looked adoptable. Perplexity, run on the same
day against the same builds, then measured it at **+5.60%** - a real and
disqualifying cost that 100 scored retrievals had been completely blind to.

**Exact-match retrieval is a threshold measure.** Once every arm clears the
threshold the instrument reports a tie, and a tie at ceiling is a statement
about the ruler and not about the arms (**F91**). The dangerous property is that
the saturated instrument does not look broken: it produces 100 clean data points,
a perfect control, and a confident wrong recommendation.

**What to do instead.** When a comparison must separate arms that a bank scores
identically, change the INSTRUMENT rather than the difficulty. Perplexity is a
continuous measure and separated the same four precisions immediately. A
threshold measure can only be pushed until something fails, and if nothing fails
it has no resolution left to give.

**This is the failure that made the E89 note "a control that cannot fail is not
a control" worth writing**, and it recurs: `pr1` scored 12/12 on both E93 arms
on 2026-08-31, which is the same shape one bank later.

## F127 - a public ranking and local usability are different properties, and a refused score leaves hypotheses UNSCORABLE rather than failed

**Kind: METHOD**

**Status:** split out of F119 on 2026-09-01 under the two-findings convention.
Measured 2026-08-31, E92. Scope tag: **general**.

**Two claims, and both matter to how a candidate model is assessed.**

**1. A model can be top of a public benchmark and unusable here.** An external
leaderboard puts Kwaipilot KAT-Coder top of its code-specific subset at 8.0. On
this box, in this harness, 6 of 8 expert coding tasks consumed the entire token
budget and emitted no code. Its general document ability was intact at 12/15 on
l4, double the workhorse. All three statements are true at once, because a
public ranking measures capability and local usability measures capability
**under a specific harness, prompt and output cap**.

That is a more useful warning to a practitioner than a low score, and it is the
reason the merged programme's B8 records each model's public ranking alongside
its local result rather than instead of it.

**2. When a gate refuses to score, hypotheses become UNSCORABLE, not falsified.**
Rule 13 refused E92's Kwaipilot coding arm. The consequence was stated per
hypothesis rather than as a single verdict:

| hypothesis | outcome | why |
|---|---|---|
| H1 (vendor uplift does not appear) | **survives** | its `<= 7` verdict holds at BOTH bounds of the truncated range |
| H2 (`>= 3` passes) | **UNSCORABLE** | passes are bounded 0..6, which straddles the band |
| H3 (`sliding_median` passes) | **UNSCORABLE** | that task was itself truncated |

**A hypothesis whose band is straddled by the uncertainty is not failed and must
not be reported as failed.** The test is whether the registered verdict holds at
both ends of what the incomplete data permits. Where it does, the hypothesis
survives on partial evidence; where it does not, the honest outcome is
`NO DECISION - MEASUREMENT INVALID`.

## F128 - a speedup quoted without its workload is not a number, and a flag can load without acting

**Kind: METHOD**

**Status:** split out of F21 on 2026-09-01. Measured 2026-07, E13. Scope tag: **general**.

**Two lessons from one speculative-decoding sweep.**

**1. The same configuration produced 3.73x, +17% and 0.53x.** Identical model,
identical draft model, identical flags. Repetitive text accepted 16 of 16 draft
tokens and ran 3.73x faster; explanatory prose gained 17%; analytical and
creative prompts **halved**, because the target model pays to verify drafts it
then rejects. **A published speedup that does not state its workload cannot be
compared with anything**, including itself on a different day. This was the
third appearance of that lesson in the programme.

**2. A flag can be accepted and do nothing.** At build `067de937`, passing the
draft model with `-md` alone loads it and never uses it. The only tell is a
single INFO line in the server log; the run completes, reports plausible
timings, and the feature is inert. `--spec-type draft-simple` is what actually
switches it on.

That is the inert-flag class, and it recurs: `--jinja` in F39, `-np` explicit
against auto in F108, and `reasoning_effort` against chat templates that never
reference it in F124. **The common shape is a setting that is accepted, recorded
as applied, and has no effect** - so the result file describes a configuration
that was never served.

## F129 - Vulkan did not fail under any controlled condition, and the original crash was never reproduced

**Kind: PLATFORM**

**Status:** split out of F26 on 2026-09-01. Measured 2026-07-08. Scope tag: **platform**.

Re-running F6's exact invocation at the raised 112 GiB ceiling passed cleanly -
exit 0, all four rows, no DeviceLost (pp512 d0 230.59, tg128 d0 24.24, pp512
@d8192 41.28, tg128 @d8192 21.06 tok/s). Vulkan had already passed the same
invocation at the older ceiling earlier that day, at 1.3% coefficient of
variation with no abort.

**So Vulkan passed at both pool sizes when idle and has not been observed to
fail under any controlled condition in the whole investigation.** The only
Vulkan failure on record is the original F6 report, and two dedicated
reproduction attempts did not reproduce it: an idle re-run passed clean, and a
heavy-disk-I/O re-run produced a categorically different failure - the
kernel-level SDMA deadlock that became F24.

**An unreproduced failure is not a property of the backend.** It stays on record
as an observation with an unknown trigger, and F109 later retracted the size
boundary that had been built on top of it.

## F130 - which models actually draft well: the local pick matches cloud-Mistral and trails the frontier

**Kind: MODEL**

**Status:** split out of F34 on 2026-09-01. Measured 2026-07, n=30 per model,
two independent rounds, judged by an independent full-source judge. Scope tag: **model**.

Ten real solicitor and accountant tasks - draft letters, summarise agreements,
extract terms, attendance notes - scored on "would a solicitor send it with only
light edits?"

| model | usability | faithfulness |
|---|---|---|
| gpt-5.6-sol (frontier) | **4.37** | **4.77** |
| cloud mistral-large | 3.17 | 3.70 |
| **Mistral-Small-24B (local)** | **3.03** | **4.00** |
| Qwen3-30B-A3B workhorse | 2.6 | 3.1 |
| Mixtral-8x7B | 1.83 | - |

**The local pick matches cloud-Mistral and is more faithful than it** (4.00
against 3.70), which is the own-versus-rent argument at its strongest. **All
Mistral variants trail the frontier**, and a blind pairwise comparison of
best-local against frontier ran 4-26.

**Two practical notes.** Q4 and Q8 are equivalent for drafting (3.03 against
2.90), so run the 14 GB Q4 rather than the 25 GB Q8. And Mistral-24B is dense,
so it is roughly 5-8x slower than the Qwen3-30B-A3B mixture-of-experts model -
the quality is bought with time.

**Prompting was not the lever.** A solicitor system prompt, few-shot examples,
local self-refine and higher precision all failed to move the workhorse off
2.4-2.6. Changing the model did.

## F131 - omitting the context flag allocates the model's full trained context

**Kind: PLATFORM**

**Status:** split out of F39 on 2026-09-01. Measured 2026-07-17. Scope tag: **platform**.

The production unit omitted `-c`, so llama-server allocated Qwen3-30B-A3B's
entire trained context of 262,144 tokens rather than the interactive envelope
that had actually been measured.

| | before | after |
|---|---|---|
| `n_ctx` | 262,144 | 49,152 |
| GTT | 39.91 GiB | **20.21 GiB** |

**19.70 GiB reclaimed, 49% of what was held**, against model weights of about
18 GiB - so the key-value cache alone was roughly 22 GiB, over five times what
any measured use needed. Generation measured 88.04 tok/s afterwards with no
regression evident.

**The comparison is not like-for-like and says so:** 88.04 was measured through
the chat-completions API while F15's plus-or-minus 1.5% band is a `llama-bench`
figure. "No regression evident" is the claim; "within F15" is not.

This is why CLAUDE.md carries a hard rule to always pass `-c` explicitly.

## F132 - an external known value is what caught an inverted answer

**Kind: METHOD**

**Status:** split out of F45 on 2026-09-01. Measured 2026-07-17, E42 + E45. Scope tag: **general**.

We registered a hypothesis that smaller Whisper models might transcribe better,
and the first measurements agreed with it. **A batching defect in our own
harness had inverted the result.**

What caught it was not a code review. It was that the corrected figure -
**2.40% word error rate for large-v3-turbo on LibriSpeech test-clean** - matches
the published figure for that model on that benchmark, about 2-3%. The
uncorrected result did not match anything.

**Running a public benchmark whose answer is already known validates the harness
and the number at the same time.** Without it, a harness defect that flatters a
hypothesis you registered is very hard to see, because the result looks like
the finding you were hoping for.

The ordering held on real meeting audio too, which is the second half of the
control: large 10.7% disagreement against small 13.7%, roughly 28% better in
both settings.

**Where a public benchmark with a known value exists for the capability under
test, run it as a calibration arm before trusting the private bank.**

## F133 - three measurement lessons from settling the narrator voice

**Kind: METHOD**

**Status:** split out of F56 on 2026-09-01. Measured 2026-07-26. Scope tag: **general**.

**1. A single-utterance figure nearly triggered a tuning pass.** A pace of
4.11 words per second, measured on **one 26-word take**, read as too fast. The
same configuration over 227 words measured **3.42 w/s**, which is inside the
target. The n=1 figure was an artefact of one short utterance and would have
bought a round of tuning against a problem that did not exist.

**2. Inverting the order is what made the preference distinguishable from
primacy.** The listening reel played the voice the owner had ranked *second*
first, deliberately against his prior ranking. He still chose the one he had
ranked first. **A tie-break that rests on presentation order is not a
tie-break**, and the only way to tell the two explanations apart is to invert
the order and see whether the answer moves.

**3. An engine verdict does not transfer across reference voices.** VoxCPM2 had
previously been judged marginally better than Chatterbox on the owner's own
voice, and lost here. That is not a contradiction: the earlier judgement used an
Irish male reference that **both** engines Americanised, and this one used
English female references that one engine handles. **Ranking engines in the
abstract is the error**; the verdict belongs to the engine-and-reference pair.

## F134 - a gate is green when the missing work has no tests to fail

**Kind: METHOD**

**Status:** split out of F102 on 2026-09-01. Measured 2026-08-29. Scope tag: **general**.

A local coding model was given a six-task plan. It completed task one correctly,
never started tasks two to six, ticked none of the six boxes, wrote `COMPLETE`
as its status, and `make check` returned **exit 0**.

**The gate was green because the only tests present were the ones the model
itself wrote for the task it did do.** Nothing in the harness could distinguish
"all six tasks done" from "one task done and five never started". Absent work
produces no failures.

**This is the vacuous-success shape appearing in the measuring apparatus rather
than in the model**, and it generalises well beyond coding agents: any check
whose evidence is generated by the thing being checked will pass when that thing
does nothing. A completion gate has to assert against something the worker did
not author - the plan, an external test file, a manifest of expected artefacts.

Related: **F100** (a gate needs its own positive control), **F123** (a readiness
check that does not exercise the path certifies nothing), **F126** (a saturated
instrument cannot compare anything).

## F135 - three models stay resident for the price of one context, and switching between them is inside noise

**Kind: PLATFORM**

**Status:** measured 2026-08-31/09-01, E94 (prereg + amendment 1). Scope tag:
**platform** - one trio, one build, kernel 7.0.0-29, router mode only.

| context per model | GTT, all three resident | worst switch excess |
|---|---|---|
| 32,768 | 58.65 GiB | +0.022 s |
| 65,536 | 63.07 GiB | +0.026 s |
| 98,304 (production) | **67.53 GiB** | +0.015 s |
| 131,072 | 71.93 GiB | - |
| 262,144 (max trained) | **89.89 GiB** | - |

Of 121 GiB. Eighteen switch measurements across six ordered pairs and three
rungs; several excesses are **negative**, so the switching cost sits inside
run-to-run noise rather than merely being small.

**Residency is free.** `fast` measured 83.74 tok/s alone and 83.06-83.61 tok/s
with two other models resident, on the same request path - inside F15's
+/-1.5% band. `fast` alone occupied 20.69 GiB against 62.51 for all three, so
the other two were genuinely loaded.

**This retires F40's "two models is the safe cap."** That cap was arithmetic
against the ~60 GiB memory boundary F109 retracted, and nobody had re-asked the
question since.

**Not tested, deliberately:** concurrent inference on two or three models at
once. F41 measured that as a fixed bandwidth budget split 4.6:1 against the
mixture-of-experts model. Residency and switching are not parallelism.

Router mode is experimental upstream, so this is a case for a proposal to
sparkrouter rather than a change to it.

## F136 - prefill collapses with prompt length, so the context a box can HOLD is not the context anyone will WAIT for

**Kind: PLATFORM**

**Status:** measured 2026-09-01, E94's context-ceiling arms. Scope tag:
**platform**.

| prompt | configuration | wall to first answer | prefill rate |
|---|---|---|---|
| 3,976 tokens | 1 model, production (F111) | ~3.9 s | **1,024.60 tok/s** |
| 32,644 tokens | 3 resident, asymmetric | 95 s | 344.5 tok/s |
| 98,116 tokens | 3 resident, uniform | 734 s | 133.6 tok/s |
| 130,852 tokens | 3 resident, uniform | 1,281 s | 102.2 tok/s |
| **261,827 tokens** | 1 resident | **3,546 s** | **73.8 tok/s** |

```
TIME TO FIRST OUTPUT TOKEN

  3,976 tok |#                                             |   3.9 s   1024.6 tok/s
 32,644 tok |#                                             |   2 min    344.5 tok/s
 98,116 tok |##########                                    |  12 min    133.6 tok/s
130,852 tok |#################                             |  21 min    102.2 tok/s
261,827 tok |##############################################|  59 min     73.8 tok/s
```

Configurations differ across the points and are named in the table, so this is
a curve over PROMPT LENGTH rather than one controlled sweep. It is monotonic
across all five, and residency was separately measured as free (F135), which is
what makes the points comparable.

**The rate column is CONFIRMED by a second instrument (E100).** These rates are
derived from the client's end-to-end wall. `llama-server`'s own
`prompt eval time` accounting agrees within **0.9% on four arms** and within
0.1% on the 261,827-token request - 73.94 tok/s server against 73.8 derived,
with a remainder of 4.7 s out of 3,546.

A live progress counter sampled during the run had suggested 104.7-116.4 tok/s
and was **wrong**: two windows agreed with each other because both sat at
27-36% of the same prefill, and the rate is not constant across a prompt. That
is F137, and the registered prediction that the client wall was a composite is
falsified.

**The curve is superlinear, which is the part a capacity table hides:**

| step | prompt grows | wait grows |
|---|---|---|
| 3,976 -> 98,116 | x24.7 | **x188** |
| 98,116 -> 130,852 | x1.33 | x1.74 |
| 130,852 -> 261,827 | **x2.00** | **x2.77** |

Doubling the prompt costs nearly three times the wait, so the penalty gets
worse as prompts get longer rather than staying proportional.

**Prefill throughput falls about 7.7x between 4K and 98K and keeps falling.** A
full-context request takes twelve minutes before the first output token at
98,304, twenty-one at 131,072, and **fifty-nine minutes at 262,144**.

**The memory question and the usability question have opposite answers.** F135
shows all three models can hold 262,144 tokens each for 89.89 GiB, and the full
allocation is genuinely served - `smart` answered a 261,827-token prompt, alone
and with two other models resident. This shows almost nobody should send one:
it is a batch operation, not a conversation. **The asymmetric configuration
(F138) is the answer**: give the room to the one alias whose inputs are long,
for 68.10 GiB rather than 89.89.

**An earlier reading of this was wrong and is retracted.** A run on 2026-09-01
reported a ceiling near 131,072 with `HTTP 500: Context size has been
exceeded`. That run was contaminated - a client timeout at 1,800 s left the
server prefilling while later probes queued behind it - and a clean re-run at a
7,200 s timeout served the full allocation in 3,546 s. **The sharing hypothesis
is also falsified** (F138): `smart` served 261,827 tokens with two other models
resident, so contamination is the whole explanation.

**Two consequences.**

**Raise context asymmetrically, not uniformly.** Only one alias sees long
inputs. Giving all three the maximum costs 89.89 GiB and buys a capability whose
prefill nobody waits for.

**A day-scale throughput model must price the PREFILL, not the swap.** The
programme's co-resident routing question (A13) asks whether a multi-model system
completes more accepted work per day. Switching is free (F135) and residency is
free (F135); the cost that decides the answer is what a long prompt costs to
read.

**How this was found is worth keeping.** E94 was designed around whether three
models fit, and this number is not in its pre-registration. It appeared only
because the context-ceiling search had to send real full-length prompts to
establish whether the allocated context was usable at all. **An experiment
measuring capacity produced its most decision-relevant number as a side effect
of checking that the capacity was real.**

## F137 - two agreeing samples of a progress counter gave 1.4x the true rate

**Kind: METHOD**

**Status:** measured 2026-09-01, E100. Prereg `results/e100-prereg.md`, result
`results/e100-prefill-ruler.md`. Scope tag: **general**.

While a long prefill was running, `llama-server`'s progress counter was sampled
twice to derive a live rate:

| window | progress | implied |
|---|---|---|
| 1 | 0.27 -> 0.31 over 90 s | 116.4 tok/s |
| 2 | 0.32 -> 0.36 over 100 s | 104.7 tok/s |

The two windows agreed to within 10%, which is what made the figure feel
trustworthy. **The whole-prompt rate was 73.94 tok/s.** The live reading was
1.4x to 1.6x too high.

**Agreement between two samples is not evidence that either is
representative.** Both windows sat at 27-36% of the same prefill, so they
sampled the same region of a rate that is not constant across the prompt. Two
consistent measurements of the same unrepresentative slice look exactly like a
stable rate.

**What the sample was actually a sample OF.** The intent was to measure "the
rate of this job". What was measured was "the rate during minutes 12 to 15 of a
59-minute job". Those are different quantities and nothing in the numbers
distinguished them.

**The instrument that settled it was already on disk.** `llama-server` reports
`prompt eval time` per request with its own token count and rate. Against the
client's end-to-end wall it agreed within **0.9% on four arms**, and within
0.1% on the one under dispute - so the client stopwatch was a sound prefill
measure all along and the derived figures in F136 needed no correction.

**Two practical rules.**

1. **A rate derived from part of a job needs a reason to be representative of
   the job.** Sampling twice is a check on stability, not on representativeness,
   and only the second one was in question.
2. **Prefer the server's own per-request accounting to any client-side
   derivation of it**, where one exists. It is not a proxy, it costs nothing,
   and here it was sitting unread in a log the run had already written.

## F138 - the asymmetric context configuration works, and the pool is not shared

**Kind: PLATFORM**

**Status:** measured 2026-09-01, E94 asymmetric arm. Scope tag: **platform** -
one trio, one build, kernel 7.0.0-29, router mode.

Three models resident, each with a **different** context, all serving their
full allocation:

| alias | allocated | largest prompt SERVED | wall | prefill |
|---|---|---|---|---|
| `fast` | 32,768 | 32,644 | 95 s | 347.5 tok/s |
| `code` | 65,536 | 65,380 | 348 s | 188.5 tok/s |
| `smart` | **262,144** | **261,827** | 3,544 s | 74.0 tok/s |

**All three resident: 68.10 GiB** of 121.

**That is the configuration to deploy.** It costs 0.57 GiB more than uniform
98,304 (67.53) and **21.8 GiB less than uniform 262,144** (89.89), while giving
the document model four times the room and leaving the other two answering in
under a second.

**The pool is NOT shared per-model in a way that halves it.** An earlier run
reported `HTTP 500: Context size has been exceeded` at 131,813 tokens - exactly
half of 262,144 - and the sharing hypothesis was the surviving explanation for
it after the queue contamination was identified. This arm falsifies it:
`smart` served 261,827 tokens with two other models resident. **The refusal was
contamination, not sharing**, and the ceiling reported at 49% of the allocation
is fully retracted.

**Residency remains free at maximum context**, now confirmed by the server's own
accounting rather than by inference: 73.98 tok/s with three resident against
73.94 alone.

**The command line must not carry `-c`.** llama.cpp ranks command-line arguments
above the per-model preset section, so a `-c` flattens every per-alias `c` to one
value while the run records itself as asymmetric. `run_e94.py --no-ctx-override`
exists for this and the server log is the check: three distinct `n_ctx` values
(262144, 65536, 32768) must appear for one server.

## F139 - a summarised page is not the page: a wrong defect report reached the edge of publication

**Kind: METHOD**

**Status:** measured 2026-09-03, MatrAIx Persona 1M ingest. Scope tag: **method**
- one dataset, one session. The dataset itself is kept but unused (owner
decision, 2026-09-03).

**The claim that was wrong.** Mid-session this register would have gained
"the evidence layer of Persona 1M is unusable across 599,847 human-grounded
records". It was about to be filed as a public discussion on the authors'
repository, under Alastair's name. It is **false**, and the owner stopping the
push is the only reason it was not published.

**What produced it.** Three sources were read for this dataset. The Hugging Face
card was fetched raw and read in full. The GitHub README and the vendor's
research page were read only through `WebFetch`, which answers a prompt against
the page rather than returning it. Both summaries were then treated as if the
pages had been read.

The GitHub README carries three things no summary returned:
`persona/schema/` (the authoritative dimension schema), `persona/validation/`,
and `persona/validation/scripts/decode_persona_1m.py` - **the authors' own
decoder**. Reading it settles in 923 characters what four measurement passes
had been circling.

**A summariser cannot omit what you did not think to ask, because you did not
ask.** The gap is invisible from the answer: a summary of a page that lacks the
detail and a summary that dropped it are the same text. This is
`no finding != successful measurement` with a new surface - the ruler was an
LLM, and it silently narrowed scope.

**What is actually true.**

| | Status |
|---|---|
| Attribute decode | **CORRECT.** Logic identical to the upstream decoder; 1,000 rows validated against stored `populated_attribute_count`, zero mismatches |
| `descriptions[].field_index` / `grounding[].field_index` | **No documented index space.** The upstream decoder never resolves them; indices reach 1324 against a 1,290-column codebook |

The evidence layer is usable exactly where it **self-checks** - where the
grounding index set equals the row's populated attribute set. Spot-checked
semantically at both verdicts: `seniority: Student / intern` evidenced by
"toss it in my school bag" where it passes, and a language field carrying
homeownership evidence where it fails. 3,600 rows sampled across all ten shards:

| source | release rows | attribution OK |
|---|---:|---:|
| stackoverflow | 113,120 | **100%** |
| gss | 63,532 | **100%** |
| amazon | 97,915 | 54.5% |
| wiki | 323,438 | 5.5% |
| synthetic | 400,000 | n/a - carries none by design |

PRISM (1,487) and Real Human Survey (355) are too small to have landed in the
sample: **unmeasured, not zero.** The failures are block-structured, not
scattered - the first wiki rows pass and rows from ~300000 fail wholesale - so
the filter is per row, never per source. `tools/decode_persona.py` exposes it as
`evidence_attribution_ok`.

**The rule.** A page read through a summariser is UNREAD for any claim the
summary did not have to support. Fetch the source before a negative finding
about someone else's work becomes an assertion - and before it becomes a
publication. The cost asymmetry is total: one raw fetch against a wrong public
claim under the owner's name.

**Licence, recorded because it gates reuse rather than reading.** Persona 1M is
non-commercial research use only, and the terms bind subsets and derivatives
including the 400,000 synthetic records. The MIT badge on the GitHub repository
covers that repository's software, not the dataset files. Upstream sources stack
their own terms (Amazon research-use, PRISM CC BY-NC, NORC GSS), and the authors
state commercial rights are not theirs to grant.

**Fetch provenance.** 20 files, 6.34 GiB, all 10 shards SHA-256 matched against
the repo's own `manifest.json`, cross-checked against HF API sizes before
fetching. `/opt/models/staging/matraix-persona-1m/provenance.json`, revision
`8b1073ab23d0c0ba0928386a041bac55e5365ddc`.


## F140 - the reasoning-effort default costs 11 runaways of 18; the sampler fix the field recommends is worth 3

**Kind: MODEL**

E101, 78 generations, five cells, quiet GPU, `Qwen3.8-27B-Q4_K_M`, six coding
tasks including the two F71 named as runaway-prone.

A community report attributes Qwen3.8-27B's failure on long agentic work to
sampling and proposes `--min-p 0.05` as the fix, alongside the model's own
published defaults (`temp 1.0`, `top-p 0.95`, `top-k 20`). Crossing that
sampler against `reasoning_effort` separates the two terms:

| config | pass | truncated of 18 | tokens |
|---|---|---|---|
| `medium`, min-p 0.00 | 18/18 | **0** | 36,588 |
| `medium`, min-p 0.05 | 18/18 | **0** | 42,648 |
| `xhigh`, min-p 0.05 (their fix) | 10/18 | 8 | 93,270 |
| `xhigh`, min-p 0.00 (their config) | 7/18 | **11** | 109,547 |

**`min-p` removes 3 runaways. Dropping the effort setting removes all 11.** The
reported fix is real and it is aimed at the smaller term, by a factor of about
four. At `medium` the failure does not exist to be fixed - 42 of 42 generations
completed - and `min-p` there costs 17% more tokens for no change in outcome.

**Actionable line, unchanged from F71 and NOT the sampler: serve this model with
`reasoning_effort: medium` set EXPLICITLY.** The chat template resolves the
parameter to `xhigh` when the caller says nothing, so the default is the setting
that fails. `min-p 0.05` may be added on top and is worth roughly a quarter as
much.

**Stated limits.** The min-p effect landed at EXACTLY its pre-registered
threshold (-3 against `<= -3`), which is the weakest pass available: n=18 over
three seeds licenses the DIRECTION and not the magnitude. Three of the six tasks
(`roman_roundtrip`, `word_break`, `eval_expr`) truncate 3/3 at `xhigh`
regardless of sampler and carry most of the effect. Nothing here transfers to
the reporter's RTX 3090 Ti / Windows box; only the mechanism is portable.

**Recorded separately because it bears on how we serve everything:** both
`Qwen3.8-27B-Q4_K_M` and `ThinkingCap-Qwen3.6-27B` ship embedded sampling
defaults in their GGUF headers (`general.sampling.temp` 1.0, `top_k` 20,
`top_p` 0.95) - the reporter's settings are the models' own recommendations, not
his invention. **Every eval in this repo, and production, runs at
`temperature 0` and overrides them.** That is defensible for reproducibility and
it had never been written down.

Evidence: `results/experiments.md` E101 pre-registration + result,
`results/raw/e101/*.json`, scored by `tools/score_e101.py`. See [[F71]], [[F72]].


## F141 - what looks like looping is NOT repetition, and every sampler knob aimed at it acts on the wrong mechanism

**Kind: MODEL**

E101's fifth prediction, and the only one falsified. Registered in advance:
truncated generations would repeat themselves at least 3x more than passing
ones, measured as the most-repeated 8-word window.

**They do not repeat at all.**

| | mean `max_ngram_rep` | `max_line_run` |
|---|---|---|
| truncated generations | 3.2 | 1 |
| passing generations | 3.1 | 1 |

Ratio **1.03**. `max_line_run` is 1 across all 78 generations - not one instance
of two identical adjacent lines anywhere. In the worst cell, the single highest
repetition score belongs to a generation that **passed**.

**The failure mode is non-convergent deliberation.** The model reasons
coherently, at length, and never decides to stop; it hits the token ceiling
mid-thought. It is not the "hmm, hmm, let me see, hmm" degenerate collapse the
community vocabulary describes, and calling both "looping" merges two different
failures under one word.

**Why this is operational and not semantic.** `min-p`, `top-k`, `top-p`,
`repeat-penalty` and `presence-penalty` all act on the repetition mechanism.
The thing consuming the budget here is not that mechanism. That predicts exactly
what F140 measured: the sampler helps a little, because perturbing the
distribution sometimes lets a generation reach a stop token, and it cannot help
much, because it is not addressing what is happening. **A stop condition, a
token budget, or a lower effort setting are the levers that fit the actual
failure.**

**Method note.** The meter that produced this was built for the hypothesis it
then refuted, and reported COUNTS with no threshold baked in - the "what counts
as looping" line lived in the pre-registration, not the instrument. Had it
returned a verdict instead, a threshold chosen to make truncated items look
repetitive would have confirmed the wrong mechanism. Two independent measures
were carried (adjacent-line runs AND n-gram windows) precisely because a loop
takes two shapes; both agree here, which is what makes the null credible rather
than a gap in the ruler.

Evidence: `results/experiments.md` E101 result, `repetition_stats()` in
`tools/run_coding_eval.py`, guarded by `tests/test_coding_eval_sampler.py`.
See [[F140]], [[F119]].


## F142 - the L5 bank is SATURATED: three models, zero separation, the same failing item

**Kind: METHOD**

E102 and E103, same bank, same session, quiet GPU, `-c 16384 -fa on`.

| arm | total | band R | band E | only miss |
|---|---|---|---|---|
| `Qwen3.8-27B-Q4_K_M` (incumbent) | 23/24 | 11/12 | 12/12 | `R09` |
| `Qwen3.8-27B-GSQ-RCO-IQ3_S` (3-bit quant, 4.7 GiB smaller) | 23/24 | 11/12 | 12/12 | `R09` |
| `ThinkingCap-Qwen3.6-27B` (**different base model**) | 23/24 | 11/12 | 12/12 | `R09` |

**Zero points of separation on both bands, and all three fail the same single
item.** The bank did not detect a three-bit quantisation, and it did not detect
a change of base model family.

E78 built this tier to separate arms and it did: three arms spread 8 points on
band R (3, 5, 11 of 12). That separation came from arms BELOW the ceiling. Every
arm here sits at 23/24, and **at that level the instrument has no dynamic range
left.** F126 already stated the principle - a saturated instrument cannot
compare anything, including the thing it was chosen to compare - and this is it
happening to the bank that was our best knowledge-work discriminator.

**Operationally: L5 is RETIRED for model comparison at this capability level.**
It remains valid for arms that score materially below 23/24, which is what it
was built for and where its 8-point separation was measured. A future comparison
between models of this class needs harder items, and the honest reading of any
tie on it is *"this bank cannot tell"* rather than *"the models match"*.

**The near-saturation was flagged in E102's own registration** ("it can detect
the challenger falling and cannot detect it rising"), and the registration was
still too optimistic: it did not detect a fall either, from either challenger.
Predicting a limitation is not the same as bounding it.

**What made the null credible rather than a hole in the ruler:** the incumbent
reproduced E78 item for item six days apart (F117), and the coding bank run in
the same session DID separate the same three models (11,194 / 20,437 / 36,515
tokens). The instrument that measured nothing and the instrument that measured a
3x spread ran hours apart on the same GPU against the same weights.

⚠️ `R09` is one of E82's four order-unstable items. Three models agreeing on it
is a weaker fact than it looks.

Evidence: `results/experiments.md` E102 + E103 results, `results/raw/e102/*.json`,
`results/raw/e103/e103-thinkingcap-l5.json`, re-graded by
`tools/score_l5_bands.py`. See [[F126]], [[F117]], [[F82]].


## F143 - ThinkingCap is a better DEFAULT and a worse CEILING, and the efficiency claim changes sign with the comparator

**Kind: MODEL**

E103 arm B, six coding tasks, greedy, identical payload to E101 cell 1.

| config | pass | tokens |
|---|---|---|
| `Qwen3.8-27B` at `reasoning_effort: medium` (TUNED, F71) | 6/6 | **11,194** |
| `ThinkingCap-Qwen3.6-27B` at its own default | 6/6 | **20,437** |
| `Qwen3.8-27B` at its own default (`xhigh`) | 7/18 | **36,515** per run |

**Against our tuned incumbent, ThinkingCap costs 83% more tokens for the same
perfect score. Against our incumbent's untuned default, it costs 44% fewer and
passes everything where ours passes 39%.** Both are true. They answer different
questions, and quoting either alone misrepresents the model.

**The mechanism is the missing dial.** ThinkingCap's chat template carries ZERO
occurrences of `reasoning_effort` against the incumbent's six; it has only a
binary `enable_thinking`. Its `efficient-thinking` tag is earned - **it does not
need an effort dial because its default is already sane** - and that is also its
ceiling, because there is no setting with which to go lower.

**This explains the community ranking rather than contradicting it.** A user who
never finds `reasoning_effort: medium` is comparing row 2 against row 3, where
ThinkingCap wins decisively. The ranking is defensible from that starting point
and inverts from ours.

**Recommendation: do NOT swap the `smart` slot.** At the configuration we
actually serve, the incumbent does the same work for 45% of the tokens, and the
gap cannot be closed on ThinkingCap's side. It was also the slowest of three
arms on L5 (78.12s median against 40.93s and 26.90s).

**Stated limits.** The arms are NOT effort-matched and cannot be, so every
figure includes that asymmetry - this is not a controlled comparison of Qwen3.6
against Qwen3.8. Row 3 is SAMPLED where rows 1-2 are greedy (no greedy-at-`xhigh`
cell was ever run), so it is directional, not a matched arm. Six tasks. A
third-party requant by protoLabsAI whose MTP head was not enabled. Nothing here
transfers to the reporter's RTX 3090 Ti / Windows box.

Evidence: `results/experiments.md` E103 result, `results/raw/e103/*.json`,
`results/raw/e101/c1-greedy-medium.json`. See [[F140]], [[F71]], [[F142]].


## F144 - the GSQ-RCO IQ3_S quant costs 3 of 8 on hard tasks, and three banks called it identical

**Kind: MODEL**

E102, E102b and E104. Same base model, same architecture (`qwen35`), same
trained context (262,144), sha256 verified against the pinned oid. The pair
differs by the quantisation recipe and nothing else.

| bank | `Qwen3.8-27B-Q4_K_M` | `GSQ-RCO-IQ3_S-mtp` | gap |
|---|---|---|---|
| L5 knowledge, 24 items | 23/24 | 23/24 | **0** |
| coding core, 15 items | 15/15 | 14/15 | 1 |
| **expert, 8 items** | **7/8** | **4/8** | **3** |

**On the only bank with headroom it loses three of eight**, failing
`glob_match` (edge grammar), `kmerge` (laziness and non-mutation contracts) and
`interval_map` (a complexity gate that fails the naive-but-correct answer) -
precisely the corners that tier was built around. It spent the SAME tokens doing
it: 75,307 against the incumbent's 74,796, within 1%. **Not a budget effect, not
truncation, not configuration. Capability.**

**Recommendation: do NOT swap the `smart` slot to this quant.** The 4.7 GiB
saving and the consistent speed advantage (34% faster per item on L5, 19% on the
coding core, 20% on expert) are real and they are paid for in capability that
only a discriminating instrument can see.

**The near-miss is the reason this finding is worth reading.** E102 alone said:
identical scores, 34% faster, 4.7 GiB smaller. That is a defensible-looking case
for the swap and it was wrong. What prevented it was a decision rule registered
BEFORE the null appeared, requiring a second bank before any recommendation - and
even the second bank (15/15 vs 14/15) was too close to ceiling to settle it. It
took the third.

**Stated limits.** One run per arm on 8 items; the ordering is clear and the
exact gap is not bounded at n=8. One quant of the eight in that repo - IQ2_XS
and IQ3_XXS are untested and would be expected to be worse, not better. The MTP
head present in the file was not enabled. `sliding_median` fails for both arms
and contributes no separation.

Evidence: `results/experiments.md` E102 / E102 second bank / E104 results;
`results/raw/e102/`, `results/raw/e102b/`, `results/raw/e104/`.
See [[F142]], [[F145]], [[F110]].


## F145 - the same three models scored 0 points apart on one bank and 6 apart on another; the instrument chose the answer

**Kind: METHOD**

The sharpest form of F126, measured in one session on one GPU against the same
three sets of weights.

| bank | incumbent | GSQ-RCO IQ3_S | ThinkingCap | spread |
|---|---|---|---|---|
| L5 knowledge, 24 items | 23/24 | 23/24 | 23/24 | **0** |
| coding core, 15 items | 15/15 | 14/15 | 6/6 (subset) | <= 1 |
| **expert, 8 items** | **7/8** | **4/8** | **1/8** | **6** |

**Same weights, same build, same kernel, same quiet GPU, hours apart.** One
instrument reported three identical models; another reported a six-point
ordering. Both cannot be describing the models, and the difference is not noise:
on L5 all three failed the SAME single item.

**What made the discriminating bank different is documented at its
construction.** `spikes/coding-eval/expert_tasks.py` was built 2026-08-15 with
one property the others lack: **every test block was checked to FAIL a plausible
naive solution before the task was admitted**. A task everything passes was
rejected at construction rather than discovered useless later. The saturated
banks were built to be *correct*; that one was built to *separate*.

**The operational rule.** A tie on an instrument whose control sits at or near
ceiling is a fact about the instrument. It licenses "no difference detected",
never "the models match", and never a production change. Before comparing
models, state where the CONTROL is expected to score: **if the answer is at
ceiling, the comparison cannot run yet.**

**The cost of getting this wrong was nearly paid.** E102's tie - with a 34%
speed win and 4.7 GiB saved - was a defensible case for changing the `smart`
slot, and F144 shows it was wrong. Three of four banks agreed with it.

**A caution against the obvious over-correction:** the saturated banks are not
defective. L5 measured an 8-point separation in E78 from arms BELOW its ceiling,
and it remains valid there. Saturation is a property of the PAIRING of bank and
arms, not of the bank alone. Retire a bank for a capability LEVEL, never
absolutely.

Evidence: `results/experiments.md` E102, E102 second bank, E103, E104 results.
See [[F126]], [[F142]], [[F144]], [[F117]].


## F146 - temperature does not cause fabrication on evidence work; what it costs is calendar arithmetic

**Kind: MODEL**

E107. Ten runs, 240 graded items, `Qwen3.8-27B-Q4_K_M` on the L5 bank at
`--thinking low`, quiet GPU, one axis moved.

| temp | correct | band R | band E | **over_claim** |
|---|---|---|---|---|
| 0.0 greedy | 23.00 | 11.00 | 12.00 | **0** |
| 0.4 | 22.00 | 10.00 | 12.00 | **0** |
| 0.7 | 22.33 | 10.33 | 12.00 | **0** |
| 1.0 (the model's OWN shipped default) | 21.67 | 10.00 | 11.67 | **0** |

**Zero over-claims at every temperature.** Forty opportunities across the four
deliberately underspecified items, declined every time. The hypothesis this
experiment was built to test - that sampling makes a document assistant
fabricate - is **falsified**, and it is the client-facing question: *turning the
temperature up does not make it start making things up.*

**What temperature does cost is specific: 15 of the 17 failures across nine
sampled runs are `off_by_calendar`.** Band E - which of four parallel
instruments governs, reconciling an agreed record against a contradicting note,
noticing the pack is silent - holds **12/12 in eight of nine sampled runs**.

**The registered prediction that reasoning would be LESS affected than evidence
is falsified and inverted** (band R -1.00, band E -0.33). The mechanism this
suggests: temperature perturbs a multi-step deterministic CALCULATION, where one
wrong token propagates and cannot be recovered, and leaves judgements that are
recoverable from context regardless of phrasing. Consistent with [[F80]]
(walking a calendar is the weakest measured capability), [[F92]] (two models
miscounted the same deadline identically) and [[F75]] (order changes the
wording, not the advice).

⚠️ **Every contrast here is INSIDE the noise floor this repo already
characterised.** E82 measured prompt ORDER alone moving 2 items; the full
0.0 -> 1.0 drift is **1.33 items**. The claim is therefore **"no effect detected
above characterised noise"**, never "temperature is harmless" - and the floor
was registered before the runs so it could not be argued past afterwards.
**There is no dose-response either**: 0.7 scored ABOVE 0.4, and one 0.7 seed
matched greedy exactly.

**Operational line: keep `temperature 0` for document work, but know the margin
is one calendar item rather than a cliff.** For a workload containing no date
arithmetic, sampler choice looks close to irrelevant on this bank. `0.4` cost
exactly one item in all three seeds and fabricated nothing.

**Stated limits.** One model, one quant, one effort setting, one bank, one axis
(`top_p` 0.95 / `top_k` 20 held at shipped values). Resolves ~2 items or larger;
everything measured is smaller. One generation per item - nothing about pass@k.

**A pattern deliberately NOT claimed as a finding:** `R10` returned `truncated`
at 0.7 and again at 1.0, one seed of three each time, absent at greedy and 0.4.
Two instances cannot carry a claim, and non-termination is a different failure
class from a wrong answer ([[F141]]). It earns its own experiment.

Evidence: `results/experiments.md` E107 pre-registration + result,
`results/raw/e107/*.json`, scored by `tools/score_e107.py`. See [[F140]],
[[F142]], [[F80]].


## F147 - a harness's affordability is set by the MODEL it wraps, not by the harness

**Kind: PLATFORM**

E109, model held constant at `Qwen3.8-27B-Q4_K_M` throughout.

| harness + model | outcome |
|---|---|
| Aider + `Qwen3-30B-A3B` (3B active, MoE) - F112 | **3.9 s median first turn** |
| Aider + `Qwen3.8-27B` (dense), `kmerge` | **did not finish in 3,600 s** |
| bare API + `Qwen3.8-27B` (dense), `kmerge` | **pass, 4,692 tokens** |

**Three orders of magnitude between the first two rows, produced entirely by
which model sits behind the same client.** And the third row is the one that
makes it a finding rather than a slow day: the model SOLVES that task in 4,692
tokens when asked directly.

**The mechanism is multiplication, and it is not a defect.** Aider is bounded at
`max_reflections = 3` (verified in the installed `base_coder.py`, line 101), so
this is not a runaway. In `whole` edit format each reflection re-sends the
system prompt, the specification and the entire file, so **prefill and
generation are both paid once per turn**. An iterative harness multiplies the
model's per-token cost by its turn count. At ~12 tok/s decode on a 27B dense
model that compounds past an hour on a five-thousand-token task; at 3B active it
is 3.9 seconds.

**Operationally: the question is not "which harness" but "is this model fast
enough to be wrapped in one at all".** A dense 27B on this hardware is not, for
non-trivial coding. The same hardware and the same client are fine over a
3B-active MoE. **Harness choice and model choice are not independent decisions
and must not be made separately.**

⚠️ **What is measured is "did not finish within an hour", NOT "cannot finish".**
The cap was mine, chosen from an arithmetic estimate that proved too generous
because it counted generation and forgot prefill. A longer cap might complete.
That distinction is the finding's main limit and is stated first because the
stronger claim is the tempting one.

**Three configurations of this arm were DISCARDED and are reported nowhere as
results:** `--edit-format diff` on what is file creation, contradicting both
this repo's E90 note and Aider's own benchmark README; `whole` at a 900 s cap
with git and streaming still on; and only then the scored arm, which mirrors
Aider's `benchmark.py` exactly. **Two of those produced dramatic, publishable,
entirely false results** - "the harness destroys capability" was written and
withdrawn twice. The owner caught the first; the second was caught by reading
the maintainers' benchmark rather than trusting a fix that felt right.

Evidence: `results/experiments.md` E109 pre-registration, Amendment 1 and
result; `results/raw/e109/`. See [[F112]], [[F104]], [[F148]].


## F148 - agent scaffolding does not degrade evidence work, and does not fabricate; it costs COMPLETIONS

**Kind: MODEL**

E109 arm B. The same 24 L5 questions, the same grader, the same model - but the
ten documents written to DISK as files for an agent to find, rather than pasted
into one request.

| | bare API (control, reproduced 3x) | Hermes, docs on disk |
|---|---|---|
| **band E (evidence)** | **12/12** | **12/12** |
| band R (reasoning) | 11/12 | 7/12 |
| **over_claim** | **0** of 4 | **0** of 4 |
| accuracy among items that RETURNED | 23/24 | **19/20** |
| completion rate | 24/24 | **20/24** |

**The evidence band is untouched.** Band E is the half that turns on which of
four parallel instruments governs, on reconciling an agreed record against a
contradicting note, and on noticing the pack is silent - the half most exposed
to a retrieval failure. An agent that had to go and FIND those documents scored
identically to one handed them.

**It fabricated nothing**, on four items built to tempt exactly that, which was
the client-facing worry.

**What it costs is completions.** Of the five items short of the control, ONE is
a wrong answer; three never returned inside 600 s and one produced output the
grader could not parse. **Reported as two numbers on purpose** - a single "19/24"
blames the model for the harness's transport, which Rules 13 and 14 exist to
prevent.

**The free-form output problem is real and is not the model's fault.** A bare API
call is answered under a response format the grader controls; an agent answers
in prose. That is a measurement cost of studying agents at all, and it will
recur in any harness comparison.

**Stated limits.** ONE harness on this axis - Aider is a code editor and cannot
be an arm on a document bank - so **this compares scaffolding against none, and
ranks nothing**. One model, one bank, one run. The registered retrieval
prediction was WITHDRAWN as unscorable rather than scored: band E's 12/12 means
there was no retrieval loss to attribute, and the `docs_mentioned` detector
fired on only 3 of 24 plainly document-grounded answers. Wall times are void -
part of the run shared a GPU with a since-discarded arm.

**ADDENDUM 2026-09-06 (E112): the three non-returning items were MINE, not the
harness's.** R07, R08 and R10 were re-run with a 2,400 s cap on a quiet GPU -
the only two things changed - and all three returned and graded **correct**
(721.3 s, 400.1 s, 1,106.8 s). So this finding stands with NO caveat about
scaffolding: nothing was hanging, nothing failed to retrieve.

**R08 separates the two causes.** It finished in 400.1 s, inside the 600 s cap it
had previously exceeded, so for that item the binding constraint was the SHARED
GPU this finding already voids its wall times over - not the cap. R07 and R10
exceeded 600 s even on a quiet box, so the cap bound them too; this run cannot
say whether contention also inflated them, because it removed both variables at
once.

The completion rate above (20 of 24) is what E109 MEASURED and is left standing.
A reconstruction of what it would have been is recorded in E112's result and is
explicitly not a measurement.

Evidence: `results/experiments.md` E109 result, `results/raw/e109/e109-armB-hermes-l5.json`,
`tools/e109_harness_knowledge.py`. See [[F147]], [[F142]], [[F146]].


## F149 - Q4_K_M is the knee: 3-bit costs three of eight, 8-bit buys nothing for 55% more wall clock

**Kind: MODEL**

E104 + E105, one base model, one bank, one build, quiet GPU, same session.

| quant | on disk | expert tier | wall |
|---|---|---|---|
| `GSQ-RCO-IQ3_S` | 11.29 GiB | **4/8** | 4,951 s |
| **`Q4_K_M`** | **15.66 GiB** | **7/8** | 6,206 s |
| `Q8_0` | 27.05 GiB | **7/8** | 9,614 s |

**The quantisation curve has a knee and we are on it.** Q8_0 matches Q4_K_M
exactly - same score, same single failing task, 2.7% fewer completion tokens -
for 11.4 GiB more memory and **55% more wall clock**. Dropping to 3 bits costs
three tasks of eight for the same tokens (F144).

**Both directions were worth measuring and only one was predicted.** F144
already established the downside. The upside question had a real production
consequence, because this box holds 128 GiB and a 27 GiB Q8_0 fits resident
where a 24 GiB-VRAM machine could never hold it - so "are we serving a weaker
model than the hardware can carry" was open, and the answer is no.

**`sliding_median` fails at 3-bit, 4-bit AND 8-bit.** It is a capability limit
of this model, not a quantisation artefact, and it contributes no separation
anywhere on the tier.

**Stated limits.** Eight items, one run per arm - a tie at 7/8 cannot exclude a
difference smaller than the bank resolves. Plain `Q8_0`, not unsloth's
`UD-Q8_K_L`/`UD-Q8_K_XL`, which mix precisions per tensor and would confound "is
8-bit better" with "is unsloth's allocation better". **Nothing here transfers to
the INT8 W8A8 claim that prompted it** - different format, different hardware,
different kernel path, and vLLM is not viable on gfx1151 (F48).

Evidence: `results/experiments.md` E105 pre-registration + result,
`results/raw/e105/e105-q8-0.json`, against `results/raw/e104/`.
See [[F144]], [[F145]], [[F110]].


## F150 - defeating a naive solution is necessary and nowhere near sufficient; the token cost is the tell

**Kind: METHOD**

E110. A bank built specifically to fix saturation was saturated on its first
calibration.

`expert_tasks_v2.py` - 7 tasks, six difficulty axes, every one proved by
`validate_expert_tasks_v2.py` to be solvable by a reference solution AND to
defeat a plausible naive one. The incumbent scored **7/7**.

| | original expert tier | expert2 |
|---|---|---|
| incumbent | 7/8 | **7/7** |
| total tokens | 74,796 | **16,917** |
| mean per task | 9,350 | **2,417** |

**The naive-arm test measures the wrong gap.** It proves a task separates RIGHT
from OBVIOUSLY WRONG. A competent model does not produce the obviously wrong
answer, so the test is satisfied by tasks that discriminate nothing among real
models. Discriminating against a strawman and discriminating between two
competent models are different properties, and the first does not imply the
second.

**The token cost is a cheap proxy for the difference.** These tasks cost the
incumbent a QUARTER of what the original tier costs it. They are fiddly to
SPECIFY rather than hard to SOLVE - exacting rules the model follows correctly
once it reaches for the right library. A task the incumbent finishes in 2,417
tokens is very unlikely to separate it from a peer.

**The standard that replaces it** (owner decision, 2026-09-06): every task must
also defeat a **competent-but-subtly-wrong** solution, and the subtle error must
be sourced from failures actually MEASURED - `sliding_median`, which defeats
every model and quant tested here; [[F89]]'s boundary error; [[F92]]'s two models
miscounting one deadline identically - rather than from the author's imagination
of what is plausible. That constraint exists because the author's imagination
produced seven tasks the model passed.

**What made this cheap to discover.** The calibration was pre-registered with a
stop rule before the bank was ever served, so a 7/7 cost 23 minutes of GPU rather
than surfacing later inside a model comparison. **23 unwritten tasks are the
value of that registration** - and the same discipline is what caught the three
banks this bank was built to replace ([[F142]], [[F145]]).

Evidence: `results/experiments.md` E110 pre-registration + result,
`results/raw/e110/e110-incumbent-expert2.json`. See [[F145]], [[F142]].


## F151 - a task defined by the wrong answers it defeats cannot locate the top of a competent model

**Kind: METHOD**

E111. Three banks were built to fix saturation and all three saturated.

| bank | admission standard | incumbent | mean tokens/task |
|---|---|---|---|
| expert | reference passes + naive fails | 7/8 | 9,350 |
| expert2 | reference passes + naive fails | 7/7 | 2,417 |
| **expert3** | **+ a competent-but-subtly-wrong solution must fail** | **4/4** | **3,446** |

[[F150]] diagnosed expert2's 7/7 as the naive arm measuring the wrong gap - RIGHT
versus OBVIOUSLY WRONG - and the fix was a third arm: a solution a good engineer
would plausibly write, with its error sourced from a failure this repo had
MEASURED rather than one I imagined. Four tasks were built that way, each
defeating an anchor-drift month calculation ([[F92]]'s shape), a sweep sorted by
time alone ([[F89]]'s shape), a start-normalising deadline, and an
incremental-count-and-scan mode ([[F144]]/[[F149]]'s shape). Every subtle arm was
proved to fail before a model saw the bank.

**The model wrote none of them.** On `window_mode` it did not merely avoid the
slow-but-correct answer the subtle arm encodes; it produced a structure clearing
a gate calibrated to take 15.75 s the plausible way, in 6,994 tokens.

**Naming a better class of wrong answer raises the bar for the ARM, not for the
model.** Both standards ask the same question - which wrong answers does this
task exclude - and a competent model is not reached by excluding wrong answers,
however sophisticated. That is the whole finding, and it is why a fourth version
of the same standard is not worth writing.

**The token cost predicted it again, from the other direction.** [[F150]] made the
pre-filter explicit: a task the incumbent finishes under ~5,000 tokens is very
unlikely to discriminate. Three of the four came in under 3,000, and the mean
fell below expert2's. Tasks got more intricate to SPECIFY and no harder to
SOLVE. The cheap proxy held while the expensive standard did not.

**What is NOT concluded.** A control at ceiling blocks comparison UPWARD, not
downward: the original expert tier still separated three quants 7/8, 4/8 and 1/8
([[F144]]). These banks are not broken, and none was deleted - they measure a band
this model is above. expert3 was never run against a challenger, so its downward
discrimination is unmeasured.

**Disposition (owner, 2026-09-06): the coding instrument is PARKED**, rather than
revised a third time or repointed at the challengers. Local coding capability
for this box is already answered and deployed in the routing guide; the open
questions are knowledge work and harnesses.

**Cost of finding out: 38 minutes of GPU across two runs**, because the
calibration was pre-registered with a stop rule before the bank was served - the
same discipline that made [[F150]] cheap. Four tasks written, twenty-six not.

Evidence: `results/experiments.md` E111 pre-registration + result,
`results/raw/e111/e111-incumbent-expert3.json`,
`spikes/coding-eval/expert_tasks_v3.py`, `tools/validate_expert_tasks_v3.py`.
See [[F150]], [[F145]], [[F142]], [[F144]].


## F152 - a 0/3 was two rotted tasks; repaired, the same set gives 2/3, and the one failure is an APPLICATION failure the harness called success

**Kind: METHOD**

E113. `tools/aider-tasks.json` scored **0/3** in E109 arm A. Two of the three
were `invalid-precondition` - the work they described had since been done and
committed, so their `verify` passed BEFORE the model ran and `classify()`
correctly refused to score them. Only T1 was a genuine fail. **A 0/3 with no
measurement behind it reads as a broken harness, and it was a stale bank.**

Repaired - T2's seed removes the tracked implementation, T3's restores the two
pre-fix blobs by sha - the same three tasks measure **2/3**:

| task | E109 | E113 |
|---|---|---|
| T1 single-file bugfix | fail | **pass**, 73.2 s, ONE request |
| T2 new module against a read-only spec | invalid-precondition | **pass**, 516.9 s |
| T3 bounded two-file change | invalid-precondition | fail |

**Task banks that describe real repo work ROT BY BEING SATISFIED.** The work
gets done, HEAD starts satisfying the verify, and the bank silently stops
measuring. This is the opposite failure to saturation ([[F151]]) and it looks
identical from the score: a suspiciously extreme number. The defence is
mechanical rather than remembered - `aider_task_runner.py --check-preconditions`
seeds each task in a worktree and reports whether its verify fails FIRST, no
model required, and E113 refuses to start unless it passes.

**T3 is an application failure, not a capability failure - and the harness
returned 0.** Aider's log shows the model proposing the correct change
(`import pytest`, `importorskip` ahead of the `TestClient` import, every test
kept), the edit being applied reaching `26 / 56 lines [46%]`, a second turn
spent reasoning about which files were in the chat instead of correcting
anything, and then **exit code 0** on a task whose verify still fails. That is
[[F113]] reproducing: this harness cannot report its own failure, so an
independent verify is not optional here, it is the only signal.

**The instrument destroyed its own evidence, and that is the sharper lesson.**
The runner wrote `aider-run.log` into the worktree before capturing `git diff`
and capped that diff at 20,000 characters, so 527 lines of repo-map warnings
crowded out the task's actual change: the field whose entire purpose is
explaining a failure contained no part of it. Fixed at the same time - artefacts
excluded from the diff by pathspec, a clipped diff records how much was clipped
instead of looking complete, and `final_files` captures the end state of every
editable file so attribution survives the disposable worktree. **T3's exact
final file is not recoverable for this run**, which is the cost of finding out.

**Not concluded.** Three tasks, one model, one harness, one run. T1's move from
fail to pass is NOT attributed - E109's arm ran against a different serving
config on a contended GPU and E113 changed both.

Evidence: `results/experiments.md` E113 pre-registration + result,
`results/raw/e113/e113-aider-repaired.json`,
`results/raw/e113/worktrees/T3-multifile-optional-dep-aider.log`,
`tools/aider_task_runner.py`. See [[F113]], [[F148]], [[F151]].

## F153 - the knowledge-work banks are saturated at the frontier: three models across a 40x price range score within one item

**Date:** 2026-09-11 | **Experiment:** E135 | **Status:** ESTABLISHED

**Kind: METHOD**

**Claim.** `ps-eval` tiers `l5` and `pr1` can no longer discriminate between
frontier-class models. This is a property of the INSTRUMENT, not a measurement
of the models.

**Evidence.** Six arms, `--max-tokens 32768`, temperature 0, OpenRouter, all
truncation gates PASS, `format_error` 0 across 108 items:

| arm | l5 | band R | band E | pr1 | l5 spend |
|---|---|---|---|---|---|
| DeepSeek-V4.1-Flash | 22/24 | 10/12 | 12/12 | 10/12 | $0.0478 |
| DeepSeek-V4-Flash-0731 | 23/24 | 11/12 | 12/12 | 11/12 | $0.0102 |
| openai/gpt-5.6-sol | 22/24 | 10/12 | 12/12 | 11/12 | $0.4123 |

Every 95% Wilson interval overlaps every other (l5 spans [74%,98%] to
[80%,99%]). **A 40x price difference buys zero measurable items.**

**Three reasons the totals cannot carry a ranking.**

1. **Band E is 12/12 on every arm** - the evidence band discriminates nothing,
   and all variation is confined to band R's 12 items.
2. **The l5 validator's degenerate `lists_everything` respondent scores 22/24**,
   which is exactly what two of the three arms scored.
3. **The ordering INVERTS with an unrelated config change.** At
   `--max-tokens 8192` V4.1-Flash (22) beat V4-Flash-0731 (20); at 32768
   V4-Flash-0731 (23) beat V4.1-Flash (22). The 8K ordering was an artefact of
   differential truncation, not capability.

**The secondary result, which IS stable.** Every pr1 miss on every arm is
`over_flag` on a `legitimate` item; `missed_flag` is **0** on all three. Three
unrelated models all err toward refusing legitimate work and none complied with
a request that must be refused. Likewise `over_claim_rate` is **0.0** on all
three: every underspecified l5 item was correctly declined everywhere.

**Why it matters.** Any future frontier comparison run on `l5` or `pr1` will
return this same null. Reading that null as "our local model is as good as
frontier" would be reading a saturated instrument as a measurement - the exact
error [[F91]] recorded when L3-hard saturated. **A harder bank is now a
prerequisite for any frontier claim**, not an optional improvement.

**Scope limit.** Says nothing about long context: the l5 pack is ~8,800 chars
against an advertised 1M window, and `tools/run_longctx_eval.py` is local-only
(no `--provider`), so no cloud arm was possible.

Evidence: `results/e135-prereg.md`, `results/e135-results.md`,
`results/e135-32k/*.json` (scoreable), `results/e135/*.json` (truncated first
pass, retained as evidence, numbers NOT quotable).
See [[F65]], [[F20]], [[F82]], [[F134]].

## F154 - DeepSeek-V4.1-Flash cannot be served on sparkmax, and the blocker is not size alone

**Date:** 2026-09-11 | **Experiment:** E135 | **Status:** ESTABLISHED

**Kind: PLATFORM**

**Claim.** `deepseek-ai/DeepSeek-V4.1-Flash` cannot run on this box, for two
INDEPENDENT reasons. Either alone is sufficient.

**Reason 1 - it does not fit, and not narrowly.**

| fact | value | authority |
|---|---|---|
| parameters | 763,205,315,794 | HF API, 2026-09-11 |
| fp8 weights | 475.3 GiB, 48 shards | HF API sibling sizes |
| smallest quant existing ANYWHERE | 157.3 GiB (`apetersson/...MixedQ2-GGUF`) | HF API, 0 downloads |
| sparkmax RAM | 121 GiB | `free -g` |
| GTT ceiling | ~105 GiB | [[F109]] |

The floor is **36 GiB above total RAM before any KV cache**, and 52 GiB above
the GTT ceiling. Next sizes up are 198, 220, 366 and 475 GiB.

**Reason 2 - llama.cpp cannot execute it at all.** PR #28696
(`convert : add DeepSeek V4.1`) was opened 2026-09-10 and is a **DRAFT**. It
changes three files - `conversion/deepseek.py`, `conversion/__init__.py`,
`gguf-py/gguf/constants.py`. That is the HF-to-GGUF converter. **There is no
`src/models/` graph and no inference path.** The third-party GGUFs already on
HF were produced from that unmerged draft; nothing can run them.

**The port is not trivial, and one part of it fails SILENTLY.** The PR body
records that V4.1's FP8 scale block size is `[32, 32]` where V4 hardcodes
`[128, 128]`, and that reusing the V4 path **rescales every dequantised weight
without raising**. That is a silent-wrong-answer shape, so a hasty local
conversion would produce a model that loads and lies. It also adds an "engram"
conditional-memory mechanism with two `384,006,168 x 256` tables needing a
bespoke write path.

**Consequence.** V4.1-Flash is an API-routing question for this fleet, never a
serving one. Revisit only if BOTH a merged inference path and a sub-100 GiB
quant appear; track PR #28696.

Evidence: `results/e135-prereg.md` section A. See [[F109]], [[F58]].

## F155 - Qwen-Image-2.1 runs on sparkmax only with the gateway down and the VAE decode tiled

**Date:** 2026-09-21 | **Experiment:** E136 | **Status:** ESTABLISHED

**Kind: PLATFORM**

**Claim.** A 20B image DiT fits this box, but not beside the gateway's resident model, and not
with an untiled decode. With both fixes, 20/20 text-to-image renders completed across both
runtimes.

| run | config | outcome |
|---|---|---|
| attempt 1, diffusers W1 1376x768 | gateway UP, decode untiled | 40 steps fine, then the box died at the first second of decode; watchdog reset 24 min later |
| all re-runs | gateway DOWN, `--vae-tiling`, `mem_guard.sh` at 12 GiB | 20/20; guard never fired; min MemAvailable 75,793 MiB |

**The cause was system RAM exhaustion through GTT, not the F24 deadlock.** The previous boot's
kernel log shows a `kfd_ioctl_alloc_memory_of_gpu -> ttm_pool_alloc_page` allocation in
`__alloc_pages_slowpath` with swap at 20 kB free and 8.48 of 8.58 GB Normal-zone free being CMA.
That is a different stack from `docs/memory-edge-deadlock.md`, and it hit at decode, not load.

**The diffusers path has a second ceiling: attention memory.** On gfx1151, torch's flash and
mem-efficient SDPA are gated behind `TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1`, so it falls back
to MATH attention, which materialises the full matrix. A 1 MP edit (~8k image tokens) runs at
42.2 GiB peak. The 2528x1696 edit (~33.5k tokens) dropped MemAvailable 81,642 -> 12,050 MiB
inside one 11 s poll and the guard killed it at step 0.

**The escape hatch is broken.** With the AOTriton flag set, the full-size edit held memory
(43.28 GiB peak) and ran 40 steps in 8,919 s, then decoded to an all-black PNG with
`invalid value encountered in cast`. A one-variable test (the working 1 MP edit, flag ON, 4 steps)
was also blank. **The experimental attention produces NaN with this model here; size is not the
cause.** So diffusers on this box is capped by math-attention memory at roughly 1 MP for an edit.

**Stack.** sd.cpp `c678dfe` (Vulkan); diffusers `9f12469`, torch 2.9.1+rocm7.2.3. The kernel was
not recorded per run; it was 7.0.0-31 when this was registered. Re-test the AOTriton NaN after
any torch/ROCm move.

Evidence: `results/e136-prereg.md` amendments 1 and 4 and "NaN ATTRIBUTED";
`results/e136/d-1376/run.log`; `results/e136/nan-diag-aotriton-1mp/`. See [[F24]], [[F109]], [[F157]].

## F156 - an image DiT on gfx1151 is bound by weight traffic, and for BF16 diffusers beats sd.cpp

**Date:** 2026-09-21 | **Experiment:** E136 | **Status:** ESTABLISHED

**Kind: PLATFORM**

**Claim.** For Qwen-Image-2.1 at 1376x768, 40 steps, CFG 1.0, relay down (5 images per row):

| config | mean sampling s | vs sd.cpp BF16 |
|---|---|---|
| sd.cpp BF16 | 654.46 | 1.000 |
| sd.cpp BF16 + `--diffusion-fa` | 623.09 | 0.952 |
| **sd.cpp Q8_0 DiT** | **384.00** | **0.587** |
| diffusers BF16 (sampling + decode, W2-W5) | 467.53 | - |

End to end at steady state, **diffusers BF16 ~467.5 s vs sd.cpp BF16 ~665.4 s = 0.703.**

1. **Halving the weight bytes buys 41.3%; flash attention buys 4.8%.** The step is bound by weight
   traffic through the matmuls, not attention. The FLUX-derived prediction (100-400 s) missed
   because it assumed attention was a large share.
2. **At equal precision the ROCm GEMM path is ~30% faster than ggml-Vulkan's BF16 path.** The
   prediction said the opposite, on a premise carried over from the W3 TTS engines. It did not
   transfer to one large BF16 DiT. **ggml's advantage here is quantisation, not the runtime.**
3. **Q8_0 costs nothing visible.** W1 against BF16: mean abs pixel diff 1.2-1.6/255, PSNR 32.6 dB.
4. **Scaling is super-linear in pixels.** 2752x1536 (4.0x the pixels) sampled in 1912.26 s, 5.0x
   the Q8_0 time at 1376x768.

**The fastest config is sd.cpp + Q8_0 DiT.** Not tested: diffusers at Q8, and sd.cpp's edit path
(needs the Qwen3-VL mmproj, not fetched).

Evidence: `results/e136-results.md` timings and "What the misses say"; `results/e136/s-*`,
`results/e136/d-1376-tiled/`, `results/e136/final-W2-2752/`. See [[F155]].

## F157 - Qwen-Image-2.1 edit keeps text and layout but only makes LOCAL changes; it cannot regrade or upscale

**Date:** 2026-09-22 | **Experiment:** E136, E137 | **Status:** ESTABLISHED

**Kind: MODEL**

**Claim.** Three things about what the edit mode is and is not for.

1. **Text rendering is strong.** The `HumanSpark` wordmark was spelled correctly in every W1/W2
   render (8 images, both runtimes) and in all three E1 edits. In E137 every word on the cover
   survived character for character, including the small caps, byline, stamp and the
   handwritten tagline. W4's small dashboard labels did garble, in both runtimes.
2. **Edits change local things, never the global colour.** Asked to move the owner's wallpaper
   onto the brand palette, all three prompt variants kept every object in place, turned most
   orange to gold (orange px 691 -> 241-303), and left the overall colour alone: dark-pixel mean
   (1, 20, 30) -> (1, 19, 34) against brand navy (0, 8, 42). Wording barely mattered.
   **Recipe that works: edit, then a deterministic grade** (hue rotation plus a darkness-weighted
   blend toward #00082A), which gives (0.7, 10.4, 43.5) in under a second.
3. **It is not an upscaler.** Asked to "reproduce this image exactly at higher resolution", it
   moved the geometry a few px, retextured the paper, redrew the wax-seal bolt and left a faint
   ghost line under the stamp. PSNR of the output downscaled back to source: **17.95 dB, against
   36.22 for Real-ESRGAN x4plus and 46.25 for Lanczos**. It took 5,499.56 s (122.8 s/step) at
   1536 on math attention; Real-ESRGAN x4plus took 14.15 s.

**Consequence.** For fixed artwork, upscale with Real-ESRGAN x4plus, not a generative edit. Its
10 dB gap to Lanczos is mostly sharpening the source's JPEG-soft edges, which PSNR-back counts
as change, so the number understates its fidelity (E137 P3 falsified on this). The anime and
animevideov3 variants were all correct on text; x4plus-anime put a halo round every letter.
A 1 MP edit costs ~1.9x a text-to-image render at the same size (887.87-893.49 s steady).

Evidence: `results/e136-results.md` "E1"; `results/e137-results.md`; `results/e137/scores.json`,
crop sheets `results/e137/crops-*-3000.png`. See [[F155]], [[F158]].

## F158 - image tools here exit 0 on a blank output; check the pixels, not the status

**Date:** 2026-09-22 | **Experiment:** E136, E137 | **Status:** ESTABLISHED

**Kind: METHOD**

**Claim.** Two different tools produced all-black images and reported success. Both were caught
only because someone looked at the file.

| tool | what happened | reported |
|---|---|---|
| diffusers (AOTriton attention) | 2528x1696 edit, 8,919 s, NaN -> one unique colour (0,0,0), 16,725 B | saved as a normal output |
| realesrgan-ncnn-vulkan | two of five models, run beside the E136 edit, logged `vkQueueSubmit failed -4` and wrote black PNGs | exit 0 |

**The rule.** Every image runner must fail on a blank output: max 0, or standard deviation 0.
`qwen-image/run_diffusers.py` now raises on one, and `upscale/run_e137_esrgan.sh` checks each
output. Run Real-ESRGAN solo on an idle GPU; the contended pass is kept as void evidence in
`results/e137/raw/void-contended/`.

**Why it is worth a number.** A 16 KB file with a plausible name and a zero exit code looks like a
result, and the diffusers one cost 2h28m of GPU before anyone looked. This is [[F2]]'s "exit 0 is not completion"
in a new place: completion is a property of the artefact.

Evidence: commits `105f6c9`, `dedd625`; `results/e136-prereg.md` "AMENDMENT 4 RESULT";
`results/e137-results.md` "Tools that exit 0 on failure". See [[F2]], [[F155]].

## F159 - a public "73 tok/s on Strix Halo" does not reproduce: 34.16 is the ceiling here, and the claim's own memory figure names the slow file

**Date:** 2026-09-23 | **Experiment:** E138 | **Status:** ESTABLISHED

**Kind: MODEL**

**Claim.** Ternary Bonsai 2 27B (PrismML, ternary Qwen3.8-27B) on this box, nine arms, one clean
window, all full-offload Vulkan:

| config | CODE tok/s | peak GPU GiB |
|---|---|---|
| PQ2_0 + Bonsai-tuned DFlash2 drafter, n=4 | **34.16** | 11.94 |
| PQ2_0 alone | 22.22 | 8.07 |
| Qwen3.8-27B Q4_K_M + drafter (incumbent) | 25.67 | 20.66 |
| Qwen3.8-27B Q4_K_M alone (incumbent) | 12.33 | 16.78 |
| PTQ1_0 + drafter, `-c 4096` | 3.63 | **10.11** |

**The speed claim fails by 2.1x** (34.16 against ~73), and the best arm is a code-shaped prompt
with 79% draft acceptance - the most favourable case measured.

**The memory claim nearly matches exactly one configuration, and it is the slow one.** 10.11 GiB
(= 10.85 GB) for PTQ1_0 + Q8_0 drafter at `-c 4096`, against a claimed "10.1GB". Nothing else is
near 10 GB. That configuration decodes at 3.63 tok/s here. So the two halves of the claim are
consistent only under kernels that make PTQ1_0 ~20x faster on AMD than ours - which is what the
claim's "aggressive kernel optimization" would have to be delivering.

**What IS true.** Bonsai 2 beats our incumbent on both axes: 1.80x the plain decode on half the
memory, 1.33x best-to-best. Our best Vulkan arm also exceeds the best PUBLISHED Strix Halo Bonsai
figure (32.758 tok/s, Bonsai v1 on a ROCm fork). **Quality is not measured** - E138 block 2.

**Method note for reading claims like this one.** GiB and GB differ by 7% at this size, which is
larger than the gap between several arms, and the claim states neither that nor a context size -
and KV is what moves the memory figure. A claim without units, context and prompt shape cannot be
scored tighter than that.

Evidence: `results/e138-results.md`, `results/e138/speed-*.json` (3 reps each, server-side
timings), `results/e138/bench-*.stdout`. See [[F160]], [[F3]], [[F85]], [[F144]].

## F160 - the ternary PTQ1_0 file is a DECODE trap on AMD Vulkan, and speculation's gain is prompt-shaped

**Date:** 2026-09-23 | **Experiment:** E138 | **Status:** ESTABLISHED

**Kind: PLATFORM**

**Claim.** Two things a config must get right before any Bonsai figure means anything here.

**1. Use PQ2_0, never PTQ1_0, on RADV.** The smaller file is 6.6x SLOWER to decode: 3.34 vs
22.22 tok/s, from 5.53 vs 6.70 GiB. That is ~18 GB/s of effective bandwidth on a ~220 GB/s
machine. It is specific to decode - prefill is only 2.2x apart (91.9 vs 197.9 pp512) - and the
cause is visible in the fork: PTQ1_0's integer-dot mat-vec was enabled for Intel Xe2 (#238), so
AMD takes a dequantise path. **The vendor README recommends PQ2_0 for "Metal, CUDA, HIP and CPU"
and points Vulkan at PTQ1_0, which is exactly backwards for this GPU.**

**2. A DFlash2 drafter pays on code and not on prose, and more draft is worse.**

| arm | CODE | CHAT | acceptance CODE / CHAT |
|---|---|---|---|
| no drafter | 22.22 | 22.33 | - |
| n=4, Bonsai-tuned | 34.16 (1.54x) | 21.44 (0.96x) | 79% / 39% |
| n=4, generic Qwen3.8 | 31.44 | 20.71 | 70% / 37% |
| n=8, Bonsai-tuned | 25.64 | 13.92 | 58% / 24% |

Speculation is worth 54% on an edit-shaped prompt and NOTHING on prose, the same split [[F85]]
found for MTP (2.08x structured, 1.32x chat). **Raising `--spec-draft-n-max` from 4 to 8 costs
25% on code and 35% on chat**: longer drafts are rejected more often and every rejected token was
paid for. The model-matched drafter beats the generic one by 8.7%, worth having and not the
main effect.

**Toolchain note.** The PrismML fork at `bdc23b56b` cannot load ANY DFlash2 drafter (`wrong number
of tensors; expected 81, got 58`): its `draft-dflash` predates mainline's DFlash2 layout. Mainline
`daef7b6` loads the same files. Every arm above ran on a local port of mainline `b10f9ca58` onto
the fork - `results/e138/prism-e138-dflash2.patch`.

Evidence: `results/e138-results.md`; `results/e138/speed-*.json`; `results/e138/bench-*.stdout`.
See [[F159]], [[F3]], [[F85]].

## F161 - a reviewer that re-solves saves nothing: the workhorse -> 27B cascade is safe and 30% slower on short-answer work

**Date:** 2026-09-24 | **Experiment:** E140 | **Status:** ESTABLISHED (n=12, one run)

**Kind: MODEL**

**Claim.** On L3-hard through the live gateway, the 27B at `medium` reviewing a workhorse draft
reached the same 12/12 as the 27B alone and took **1.299x** as long (1,162.2 s against 894.6 s,
draft included). It beat the 27B alone on 1 of 12 items. Confirming a planted CORRECT draft cost
**1.093x** solving from scratch.

**The safety half held completely.** Twelve planted wrong drafts, each carrying the pack's own
trap value (stale, premature, precedence-missed, fabricated), in the workhorse's own two-line
format: **0 of 12 anchored**, and the review caught all 7 of the workhorse's real errors.
Twelve planted correct drafts: 0 broken. At n=12 that bounds anchoring below ~25%, not at zero.

**Why it is slower.** The registered premise was that the 27B's cost is generating, so a draft
lets it read and emit corrections. On a two-line answer there is nothing to skip: the cost is
reasoning, and the reviewer re-derives the answer and then reconciles it with the draft.
Median reasoning 1,995 chars reviewing against 1,484 solving (+34%); completion tokens 8,722
against 6,631.

**Operationally: do not build a draft-review cascade for short-answer questions.** The only
place it can pay is where the ANSWER is long relative to the reasoning (a letter, a report
section, a file), so accepting a draft skips real generation. That is untested here and needs a
long-output instrument. The same mechanism predicts the deferred gpt-oss-120b reviewer arm
would fail the same way on this bank.

Evidence: `results/e140-results.md`, `results/e140/calls.jsonl`, prereg `results/e140-prereg.md`
(+ amendment 1). See [[F86]], [[F91]], [[F69]].

## F162 - the workhorse is most confident where it is wrong, so it cannot gate the 27B; an effort router lost to fixed `low`

**Date:** 2026-09-24 | **Experiment:** E141 | **Status:** ESTABLISHED (n=12, one run)

**Kind: MODEL**

**Claim.** On L3-hard through the live gateway, no cheap decision in front of Qwen3.8-27B beat
the fixed setting `reasoning_effort: low` (12/12, 756.4 s):

| design | correct | time vs `low` | shipped wrong |
|---|---|---|---|
| workhorse self-check gate | 7 | 0.31 | **5** |
| workhorse logprob gate (>= 0.90) | 7 | 0.29 | **5** |
| workhorse effort router | 12 | **1.20** | - |
| perfect gate (bound) | 12 | 0.73 | 0 |

**Why the gates fail.** The workhorse's most confident answer on the bank (min token probability
0.999998) is wrong, and so is its second (0.999979). Its trap errors - stale, premature,
over-applied, precedence, fabricated - are made with near-certainty; only arithmetic failures
look uncertain. Asked to check its own answer, it called 5 of its 7 wrong answers CONFIDENT. No
threshold on either signal separates right from wrong on this bank.

**Why the router fails.** It never chose `off` (correct on 9 of 12) and chose `medium` 7 times;
`medium` is 12/12 like `low` and 18% slower. Its own call plus that upward bias cost 20%.

**Operationally:** do not put the workhorse in front of the 27B as a gate or an effort router.
**For document questions send `reasoning_effort: low`**: 12/12 like the production `medium`
default in 15.4% less time, reproducing [[F69]] live. `medium` stays the coding default ([[F71]]).
The external reasoning-gate project's -54% had no quality measure; with quality measured, this
design lost to a constant.

Evidence: `results/e141-results.md`, `results/e141/calls.jsonl`, prereg `results/e141-prereg.md`.
See [[F161]], [[F69]], [[F71]].

## F163 - the 27B can gate its own `off` answers safely, but the gate costs what it saves

**Date:** 2026-09-24 | **Experiment:** E142 | **Status:** ESTABLISHED (n=12, one run)

**Kind: MODEL**

**Claim.** On L3-hard through the live gateway, an escalate-or-ship gate with Qwen3.8-27B at `off`
as first stage (9/12, 246.7 s) ships **zero wrong answers** with either signal, reaches 12/12, and
is **no faster than fixed `low`** (12/12, 756.4 s):

| gate | correct | time vs `low` | shipped wrong | escalated |
|---|---|---|---|---|
| 27B self-check | 12 | **1.125** | 0 | 6 |
| 27B logprob (>= 0.90) | 12 | **1.004** | 0 | 9 |
| perfect gate (bound) | 12 | 0.665 | 0 | 3 |

**Contrast with [[F162]].** The workhorse shipped 5 wrong (its most confident answer wrong). The
27B's self-check escalated all three of its wrong items (P1, M1, M2); the logprob gate did too, at
the cost of escalating 9 of 12. The 27B knows more of what it does not know than the workhorse.

**Why it still loses.** The self-check re-reads the pack: 12 checks = 220 s, so O2 + checks
(466.7 s) is already 62% of `low` before any escalation, and an escalation costs ~59 s against a
~20 s draft. n=12 with three wrong items: 3 of 3 caught is not a measured catch rate.

**Operationally:** nothing to deploy. Fixed `low` for document questions stands ([[F162]]). A
first-stage gate would need a check that does not re-process the pack (a shared KV prefix) before
it could beat a constant.

Evidence: `results/e142-results.md`, `results/e142/calls.jsonl`, prereg `results/e142-prereg.md`.
See [[F162]], [[F161]].

## F164 - four models tie on Aider passes and split the tasks in opposite ways; the incumbent is 2x to 10x faster

**Date:** 2026-09-24 | **Experiment:** E143 | **Status:** ESTABLISHED for these tasks (3 tasks x 3 repeats)

**Kind: MODEL**

**Claim.** On the three real repo tasks through Aider, on one build (llama.cpp `daef7b6`, F117),
the models a Strix Halo chat recommended tie with our incumbent on pass count and are slower:

| model | passes /9 | T2 | T3 | time per repeat |
|---|---|---|---|---|
| Qwen3-Coder-30B-A3B (incumbent) | 5 | 0/3 | 2/3 | 166 s |
| Qwen3.6-35B-A3B | 6 | 3/3 | 0/3 | 321 s |
| Qwen3.8-Flash-Next | 6 | 3/3 | 0/3 | 707 s |
| Qwen3.8-27B | 5 | 2/3 | 0/3 | 1,719 s |

**No model is distinguished** (widest gap 1 of 9; the band was 4). **The totals hide opposite task
profiles:** the Coder fails T2 every time and passes T3 twice; the other three pass T2 8 of 9 and
never pass T3. That is a pointer for the next bank, not a rule: three tasks.

**Operationally:** nothing to change. `local_code` stays Qwen3-Coder; of the chat's picks only the
35B is within 2x of its speed. A bank that separates models needs tasks on which they disagree, and
T2 and T3 are the two that do. The chat's picks were confirmed as not worse, not shown better.

Evidence: `results/e143-results.md`, `results/raw/e143/`, prereg `results/e143-prereg.md`.
See [[F152]], [[F117]], [[F151]].

## F165 - Halogen prefills 32K at 1,152 tok/s here, 81% of its claim and 5.3x llama.cpp; the claim reproduces conditionally

**Date:** 2026-09-24 | **Experiment:** E139 | **Status:** ESTABLISHED (median of 3, one window per arm)

**Kind: PLATFORM**

**Claim.** The published "~1,424 tok/s prefill at 32K" for `halogen-flash-server` 0.13.8 measures
**1,152 tok/s** on this box (IOMMU translated, Chatterbox resident): REPRODUCED-CONDITIONALLY, above the
1,000 floor and below the 1,210 bar. Mainline llama.cpp on our unsloth GGUF measures **216.5 tok/s** at 32K,
so an end-to-end 32K request takes 33.4 s against 162.1 s (0.21x). MTP speculation is byte-identical to
serial decode on 4 of 4 prompts and on the image's own bench. Decode at 32K is 38.1 tok/s.

**The ratio is engine plus file.** H0 runs Halogen's own checkpoint; L0 runs a different quant in a
different format. The engine-only ratio needed G0 (F166) and could not be measured.

**Not reproduced:** the README's memory picture. Peak GPU memory was 43.3 GiB (35 GiB above baseline)
against a predicted 95-115; where the roughly 115 GiB of weights live is not established.

Evidence: `results/e139-results.md`, `results/e139/`, prereg `results/e139-prereg.md` (amendments 1-4).
See [[F116]], [[F164]].

## F166 - a maintenance window is not a clean box, and Halogen cannot serve our GGUF beside anything else

**Date:** 2026-09-24 | **Experiment:** E139 | **Status:** ESTABLISHED (two guard kills, one config error)

**Kind: PLATFORM**

**Claim.** (1) `relay_bench_window.sh down` stops only the gateway. The Chatterbox TTS container
(`spark-infer`, up for days) keeps **8.1 GiB of GTT** through every window, and `podman ps` as agent-spark
cannot see it. A "GPU free" gate at 4 GiB can never pass; E139 now gates at 10 GiB and records the baseline.
E138 and E143 ran under the same condition and E138's memory readings were not re-examined for it.

(2) Halogen repacks a GGUF into 70.55 GiB of host RAM, so on 121 GiB total with Chatterbox resident it
falls under the 12 GiB guard floor: MemAvailable **11,356 MiB** (G0) and **12,108 MiB** (with the
vendor's `HALOGEN_MAX_TOK=16384`). Its own checkpoint (H0) ran with MemAvailable never below 71.5 GiB.

**Operationally:** to run Halogen on a GGUF here, Chatterbox must be stopped (owner's call) and the
guard floor kept. `HALOGEN_KV_POOL_POSITIONS` cannot be set below the context (`--ctx`). Halogen's
health response, `/cache` and startup warnings are accurate and worth reading before a first run.

Evidence: `results/e139/speed-G0*.serverlog`, `results/e139/mem_guard.log`. See [[F165]].

## F167 - the widget's options tie with the 35B we already ran; its speed order holds, its speed size does not

**Date:** 2026-09-25 | **Experiment:** E145 | **Status:** ESTABLISHED for these tasks (3 tasks x 3 repeats)

**Kind: MODEL**

**Claim.** A third-party "approximate options for 128 GB" widget names three models with unexplained
"intelligence" and "tasks/hr" scores. Through Aider on the three E113 tasks, on the build and flags of
[[F164]], they measure:

| model | passes /9 | time per repeat |
|---|---|---|
| Qwen3.6-35B-A3B UD-Q4_K_M (widget "best fit") | 6 | 294 s |
| Ornith 1.0 35B Q4_K_M (widget "faster") | 6 | 179 s |
| Ornith 1.5 35B-A3B Q4_K_M (newer than the widget) | 6 | 267 s |
| Qwen3.6-27B Q4_K_M (stand-in for the MLX-only "OptiQ 4-bit") | 7 | 1,380 s |

**No model is distinguished** (widest gap 2 of 9 across all eight arms of E143 and E145; the band was 4).
The widget's speed ORDER holds: Ornith 1.0 takes 39% less time than the 35B best fit, which the widget put
at "~42% faster". The SIZE of the 27B penalty does not: the widget says 109% slower (2.09x), we measure
4.7x. Ornith 1.5 gives most of the speed back (49% slower than 1.0), so the widget's claim is about 1.0.

**What it cannot show.** The instrument has 5 to 7 of 9 across eight models, so the widget's intelligence
scores cannot be tested with it. Ornith's lineage is unverified (no declared base model). Time includes each
model's default thinking.

**Operationally:** nothing to change; `local_code` stays Qwen3-Coder ([[F164]]). If a fast 35B-class model is
wanted for small jobs, Ornith 1.0 is 39% faster than the Qwen3.6 35B at the same pass count on this bank,
with the provenance caveat.

Evidence: `results/e145-results.md`, `results/raw/e145/`, prereg `results/e145-prereg.md`.
See [[F164]], [[F151]], [[F126]].

## F168 - an Atlas benchmark measures its configuration: a checkpoint label and one missing flag each cost the whole run

**Date:** 2026-09-25 | **Experiment:** E146 | **Status:** ESTABLISHED (two independent failures, both reproduced from logs)

**Kind: PLATFORM**

**Claim.** Atlas-Inf HEAD (2d1aab8) built native-HIP on gfx1151 fails on the MLPerf entry's checkpoint, and the same engine is 6.5x slower on an
agentic workload unless prefix caching is switched on. (1) `nvidia/Qwen3.6-27B-NVFP4` labels its 193 MLP layers `W4A16_NVFP4`; the detector counts a layer as
NVFP4 only when `quant_algo == "NVFP4"`, so the model routes to the FP8 path and dies at `mlp.gate_proj` ("Expected FP8E4M3, got UInt8") after loading 20.4 GB.
One line fixes it. The MLPerf-era source snapshot predates that branch and loads the checkpoint unpatched. (2) `--enable-prefix-caching` is off by default, and for a
hybrid model a full prefix skip also needs `--ssm-cache-slots` above zero. Off: **61 s per turn**, re-prefilling 16K-token histories at about 195 tok/s. On: **9.4 s**.
The llama.cpp reference caches prefixes by default, so an Atlas run without the flags is not configured like the comparator.

**Operationally:** any Atlas number must state its flags. This is F39's rule again (a benchmark measures a configuration, not a box), and the second time here that a
missing serving flag, not the model, decided a result.

Evidence: `results/e146-results.md`, `results/raw/e146/M1/server.serverlog`, `results/raw/e146/M1p0/`, prereg amendments 2-3. See [[F39]], [[F108]], [[F128]].

## F169 - on the MLPerf edge-agentic metric Atlas takes about 27% less time per turn than the llama.cpp reference here, and the published latency is not reproduced

**Date:** 2026-09-25 | **Experiment:** E146 | **Status:** ESTABLISHED for this subset (206 turns, one run per arm)

**Kind: PLATFORM**

**Claim.** On MLCommons' own edge-agentic harness (Qwen3.6-27B, temperature 0, single stream, 4 of 20 trajectories), the llama.cpp reference averages **12,863 ms per turn**.
Atlas averages **9,307 ms** (patched HEAD, one-line fix) and **9,453 ms** (the entry's shipped source, native-HIP reconstruction): paired ratios 0.724 and 0.735 on the same
206 turns, consistent across thirds, inline accuracy within 0.015 and 0.032 of the reference. The entry's published Strix Halo figure is 7,059 ms: **1.32-1.34x higher here**,
outside the +/-25% band; ROCm 7.2.4 (theirs 7.13), a 4-trajectory subset and a resident TTS service are declared differences, not established causes.

On the README's own claim (Qwen3.8-27B, K=4) Atlas measures **27.2 tok/s on code** (claim 28.3-28.6, confirmed) and 15.3 on chat, against llama.cpp + drafter 23.6 and 11.0: chat
1.39x and clear; code 1.15x with overlapping repetitions, not established. Prefill is about 140 tok/s at 32K on all three engines. **Atlas is not byte-deterministic** (3
distinct outputs in 10 identical greedy requests). It reserves its GPU pool up front (66 GiB above baseline at `GPU_UTIL=0.60`).

**Limits:** the reference has no speculation and no llama.cpp arm with a drafter was run on Qwen3.6; the comparator is the MLPerf reference, not the best open configuration.

Evidence: `results/e146-results.md`, `results/raw/e146/`, prereg `results/e146-prereg.md`. See [[F168]], [[F84]], [[F85]], [[F165]].

## F170 - the vendor page's MLPerf figures do not match the MLCommons entry it cites

**Date:** 2026-09-25 | **Experiment:** E146 (gate G5) | **Status:** ESTABLISHED as a comparison of the page against the results repository

**Kind: METHOD**

**Claim.** `mlcommons/inference_results_v6.1`, `closed/Atlas_Inference`, reports Strix Halo as **Qwen3.6-27B NVFP4, MTP K=3, native HIP, Ubuntu, ROCm 7.13**, official metric mean
latency per turn: **7,058.99 ms** (DGX Spark **3,807.66 ms**), so Strix Halo is **1.85x slower** per turn. The vendor page states "19.63 tok/s ... cross-architecture parity" and
"under 64 minutes" for 1,007 turns. The entry's own `tps` for Strix Halo is 10.2 and its duration 118.5 minutes; "under 64 minutes" matches the DGX Spark (1,007 x 3.808 s = 63.9 min).
How 19.63 was derived is not in what was read; a decode-only rate is a plausible source, so this is a mismatch of stated numbers with the entry, not an accusation.
Two repositories present as Atlas (`Avarok-Cybersecurity/atlas`, 699 stars, created 2026-05-05; `Atlas-Inf/atlas`, 30 stars, created 2026-08-24, calling the older one a "disputed asset"); the
page's "675 stars" and "PR #187" match the older repo's numbers, not the one it links. Which is genuine was not settled and is out of scope.

**Operationally:** quote MLPerf results from the results repository, in the unit it defines. Read the descriptor before the marketing.

Evidence: `results/e146-gates.md`. See [[F159]], [[F165]].

## F171 - every T3 failure across eight models is an edit that never reached the file; the "opposite task profiles" of F164 and F167 are partly a harness artefact

**Date:** 2026-09-25 | **Experiment:** E143, E145 (diagnosis of banked results) | **Status:** ESTABLISHED from the recorded diffs

**Kind: METHOD**

**Claim.** Across E143 and E145, task T3 (make two test files skip cleanly when `fastapi` is absent) failed in 21 of 24
attempts. Every one of the 21 carries a recorded `git diff` of exactly **978 characters**, which is the task's seed restoring
the two pre-fix files and nothing else. The 3 passes carry 1,372 to 1,412 characters: the seed plus a fix. So in every failure the
model's edit never reached the working tree. The transcripts say otherwise: the Qwen3.8-27B run ends "The changes are complete",
names both files and the exact `importorskip` fix, and Aider exits 0. Every arm ran in Aider's `whole` edit format.

**What this changes.** F164 and F167 read T3 as the task the incumbent owns and the others cannot do. The measured fact is
narrower: the others' fixes were correct in prose and absent on disk. Whether each model emitted a whole file the format could not
apply, or a description with no file, is not established from the recorded tails; the kept worktrees under `results/raw/e143/*/worktrees/`
and `results/raw/e145/*/worktrees/` hold the Aider logs that would settle it. The incumbent also lost one T3 attempt the same way.

**Operationally:** an Aider pass count on this bank is a joint property of model and edit format ([[F114]]), and Aider's exit code is
not evidence ([[F113]], [[F152]]). Before the next coding bank, the harness records whether an edit was applied as its own field, and a
task whose failures all carry the seed diff is scored "not applied", never "wrong".

Evidence: `results/raw/e143/*/r?.json`, `results/raw/e145/*/r?.json` (fields `diff`, `aider_tail`, `verify_after_rc`). See [[F113]], [[F114]], [[F152]], [[F164]], [[F167]].

## F172 - with a drafter, llama.cpp beats Atlas on the MLPerf edge-agentic metric; F169's advantage was over a reference without speculation

**Date:** 2026-09-25 | **Experiment:** E147 | **Status:** ESTABLISHED for this subset (206 turns, one run)

**Kind: PLATFORM**

**Claim.** The MLPerf reference implementation (llama.cpp, Qwen3.6-27B Q4_K_M, no speculation) plus one change, a DFlash speculative
drafter at n=4, takes **7,775 ms per turn** on MLCommons' edge-agentic harness against 12,863 ms for the reference (paired 0.604) and
9,307 / 9,453 ms for the two Atlas builds of E146 (Atlas/M2 paired **1.197 and 1.216**, above the registered 1.15 line in the second and
third thirds of the run). Accuracy is identical to the reference to three decimals (0.637). The published Atlas Strix Halo latency of
7,059 ms sits inside the +/-25% band for this configuration (1.10x); it did not for either Atlas build.

**What it changes.** [[F169]] stands as stated: Atlas is about 27% faster than the reference. It is not faster than the open
engine configured with the speculation Atlas uses itself. Any "engine X is faster" claim needs the comparator's speculation stated;
the reference implementation is a floor, not the competition.

**Limits.** 4 of 20 trajectories; a community GGUF conversion of the z-lab drafter, untuned; Atlas's own DFlash mode not run; the
drafter's per-turn acceptance not recorded per turn (this build's server log carries no acceptance lines; the 20-token probe accepted 14 of 19 drafts, 0.737). *Addendum 2026-09-26:* Atlas's DFlash mode was run in E148 and is slower still, [[F175]].

Evidence: `results/e147-results.md`, `results/raw/e147/`, prereg `results/e147-prereg.md`. See [[F169]], [[F84]], [[F85]], [[F168]].

## F173 - the ternary Bonsai 2 keeps the incumbent's answers on documents and core coding and loses on expert coding; it also runs away twice in 47 items

**Date:** 2026-09-25 | **Experiment:** E138 blocks 2-4 | **Status:** ESTABLISHED (one run per bank)

**Kind: MODEL**

**Claim.** Ternary Bonsai 2 27B PQ2_0, the 8 GiB compression of the 27B that F159 found 1.8x faster than the incumbent, scores
**21 of 24** on the l5 document bank (incumbent 23; both misses calendar arithmetic, the incumbent's class too), **15 of 15** on
the core coding bank (incumbent 15) and **3 of 8** on the expert coding bank (incumbent 7). That is F144's shape a second time:
compression costs show on the hardest coding bank and nowhere else measured. Two items in 47 ran to their token cap and were never
answered: R10 at `low` effort (24,460 reasoning characters at an 8,192-token cap, twice) and `interval_map` at `medium` (24,576).
They are recorded as runaways, not misses. The 23 answered l5 items were identical across two runs (F59).

**Operationally:** Bonsai is a candidate for document work and routine coding at half the memory and nearly twice the speed, and
not for the hardest coding work. Its runaway rate (2 in 47) needs a token cap and a retry in any serving configuration, as F140
found for the incumbent at the wrong effort default. The routing guide is not changed by one run per bank.

Evidence: `results/e138-results.md` (blocks 2-4), `results/e138/quality-*.json`, prereg amendments 3-4. See [[F159]], [[F160]], [[F144]], [[F140]], [[F59]].

## F174 - on the same weights, pi passed the task Aider could not, because it applied the edit; the harness decided T3

**Date:** 2026-09-25 | **Experiment:** E138 block 4 | **Status:** ESTABLISHED (one run per harness)

**Kind: METHOD**

**Claim.** Bonsai 2 with its drafter, behind the same server, scored **2 of 3** through Aider and **3 of 3** through pi on the three
E113 tasks. The difference is T3: Aider's record carries a 978-character diff, the task's seed and nothing else, while pi's carries
1,389 characters including the `importorskip` fix, after 13 requests and 948 s. The same model proposed the same fix to both
harnesses; one wrote it to the file. This is [[F171]]'s mechanism observed from the other side: with F171 the failures shared a diff
size, here a second harness on identical weights turned the failure into a pass.

**Operationally:** a pass count on this bank is a property of the harness's edit path as much as of the model. Until the runner
records whether an edit applied as its own field, T3 results across models are not comparable, and the "Aider vs pi" question is
about edit application, not capability. P10 of E138 ("pi equals Aider") is falsified for that reason.

Evidence: `results/e138/agentic-aider.json`, `results/e138/agentic-pi.json` (field `diff`). See [[F171]], [[F113]], [[F114]], [[F152]].

*F171 and F174 addendum, 2026-09-26:* `tools/aider_task_runner.py` now records `seed_diff_chars` and `edit_applied` (the final diff differs from the seed's, same pathspec) on every record, and `classify()` returns `fail-not-applied` for a verify failure with no applied edit. Tests: `tests/test_aider_task_runner_classify.py`. Records from E113 to E145 predate the field; the 978-character heuristic in `tools/score_e138_blocks.py` covers them.

## F175 - Atlas's own DFlash mode is its slowest configuration on this box: the drafter accepts 0.064 tokens per 15-token step, and the MLPerf-era build cannot serve it on HIP at all

**Date:** 2026-09-26 | **Experiment:** E148 | **Status:** ESTABLISHED for this subset (206 turns, one run); cause OPEN

**Kind: PLATFORM**

**Claim.** Atlas HEAD (plus the one-line W4A16 patch of F168) serving the MLPerf model with `--dflash --draft-model` z-lab's
Qwen3.6-27B-DFlash, the checkpoint E147's GGUF drafter was converted from, takes **22,898 ms per turn** on MLCommons' edge-agentic
harness: paired **1.780x** the reference (12,863), **2.460x** Atlas's own MTP arm (9,307) and **2.945x** llama.cpp with the same
drafter lineage (7,775), in every third of the run. Accuracy held (0.631 against M1p's 0.622). The mechanism is in Atlas's own log:
4,006 of 4,160 verify steps accepted zero of 15 drafts (0.064 tokens per step; tokens per step 1.074 against MTP's 1.689), and
acceptance falls from 1.98 per step under 4K context to under 0.02 past 8K, where nearly every harness turn sits. The MLPerf
entry's shipped source accepts the flag and fails to build the model on HIP (`Module 'prefill_paged_indirect' not loaded`).

**What it changes.** [[F172]] is strengthened: with the same drafter on both engines the open configuration is 2.9x faster per
turn, and Atlas's best measured configuration remains MTP K=3, which F172 already placed behind llama.cpp with a drafter. The
vendor's "faster path" is a claim about its CUDA builds; on this hardware it is not faster and, in the recorded source, not runnable.

**Cause CLOSED-UNEXPLAINED 2026-09-26 (E149-E151, [[F176]] [[F177]] [[F178]]): attention pattern, context cap and prefix cache each tested in a single-variable arm and retired; the HIP kernel path remains and is not pursued.** Original text: **Cause open, three candidates, none tested:** HEAD and the MLPerf-era source disagree on the drafter's capture layers
(`[1, 16, 31, 46, 61] used directly` against `[0, 15, 30, 45, 60] offset=-1`), so an off-by-one feeding the drafter the wrong hidden
states is the first thing to try; `DFlash ctx_window = 4096` coincides with where acceptance collapses; and the HIP kernel path is
unexercised by the vendor. A prefix-caching WARN naming an SM12.x correctness regression did not show in the score.

Evidence: `results/e148-results.md`, `results/raw/e148/` (M3p per-turn record, both server logs), prereg `results/e148-prereg.md`,
`tools/e148_dflash_accept.py`. See [[F172]], [[F169]], [[F168]], [[F85]], [[F160]].

## F176 - F175's cause is Atlas's 4,096-token drafter context cap, stated in its own source; declaring the drafter's sliding-window layers is inert

**Date:** 2026-09-26 | **Experiment:** E149 | **Status:** the sliding-window result is ESTABLISHED (one capped run, 109 turns); **the cause claim in the title is RETRACTED by E150 ([[F177]]): lifting the cap nine-fold changed nothing**

**Kind: PLATFORM**

**Claim.** Supplying z-lab's drafter with the `causal`/`use_swa`/`swa_window_size` fields Atlas reads (the checkpoint declares them
at the top level, where Atlas does not look) changed nothing: **0.071** accepted tokens per step against M3p's 0.064, per-turn
server time **1.002x** M3p's on the same 109 turns, 107 of 109 turns with the identical output length. It could not have changed
anything: the engine's window argument overrode the config to 4,096, and the drafter's context is capped at 4,096
(`ATLAS_DFLASH_CTX_WINDOW`), so the sliding window covered everything the drafter could see. Atlas's source says what the cap
does: the drafter "was trained over the FULL captured prefix" and the cap "cripples it on prompts past a tiny window - Atlas's
6-10% acceptance vs the paper's 70% is dominated by this cap"; the default was raised from 512 to 4,096 for the vendor's own
workloads. The MLPerf agentic-coding turns run 2,000-28,000 tokens of context, and our acceptance curve (2.2 per step under 4K,
0.3 at 4-8K, under 0.02 beyond) is that cap measured.

**What it changes.** [[F175]]'s "cause open" narrows to one candidate with a vendor statement behind it, and a one-variable test:
E150, `ATLAS_DFLASH_CTX_WINDOW=36864`. The capture-layer off-by-one is retired as a candidate (HEAD's authors measured the
direct indexing better); the sliding-window declaration is retired by this run. Method: a harness killed at a cap writes no
events file, so capped arms are compared server-side on Atlas's per-turn lines.

Evidence: `results/e149-results.md`, `results/raw/e149/M4/`, prereg `results/e149-prereg.md` (amendment 1), `tools/score_e149.py`.
See [[F175]], [[F172]], [[F85]].

## F177 - Atlas's drafter context cap is not the cause of F175 either: lifted to 36,864, acceptance and output are identical to the shipped configuration; F176's cause claim is retracted

**Date:** 2026-09-26 | **Experiment:** E150 | **Status:** ESTABLISHED (one capped run, 128 turns); cause OPEN, prefix cache under test (E151)

**Kind: PLATFORM**

**Claim.** With `ATLAS_DFLASH_CTX_WINDOW=36864` (the serving context, against the default 4,096), Atlas's DFlash drafter accepted
**0.060** tokens per 15-draft step (M3p 0.064), 0.008 past 12K context (M3p 0.009), with tokens per step 1.071 against 1.071 and
the identical output length on 127 of 128 turns. Server-side time per turn 0.999x M3p. The vendor's source comment that its low
acceptance "is dominated by this cap" does not describe this workload: the cap was lifted nine-fold and nothing moved. Across
E149 and E150, three configurations produced one curve and the same output on 383 of 386 compared turns.

**What it changes.** [[F176]]'s cause claim is withdrawn; its measurement (the sliding-window declaration is inert) stands.
[[F175]] returns to "cause open" with two candidates retired (attention pattern, context cap) and one live: Atlas's own startup
WARN names a DFlash correctness regression on multi-turn prefix-cache hits, and M3p's log shows first turns of a conversation
accepting **1.125** per step at 4-8K context against **0.207** for later turns at the same context. E151 (pre-registered before
this result was read) tests the cache. If that fails too, the HIP kernel path is what remains, and this project stops there.

Evidence: `results/e150-results.md`, `results/raw/e150/M5/`, prereg `results/e150-prereg.md`, `tools/score_capped_atlas_arm.py`.
See [[F175]], [[F176]], [[F172]].

## F178 - Atlas's prefix cache is a 0.05-token contributor to its DFlash collapse, not the cause; three single-variable arms retire three explanations and the investigation stops

**Date:** 2026-09-26 | **Experiment:** E151 | **Status:** ESTABLISHED (one capped run, 31 turns); the Atlas DFlash cause is CLOSED-UNEXPLAINED by decision

**Kind: PLATFORM**

**Claim.** With `--enable-prefix-caching` removed, on the same first 31 turns as M3p, Atlas's DFlash drafter accepted **0.346** per
step at 4-8K context (M3p 0.338), **0.068** at 8-12K and **0.039** past 12K where M3p accepted exactly **0.000** over 491 steps.
The first-turn control held (2.238 against 2.429). Every turn re-prefilled its context, so time per turn was **3.436x** M3p's.
The startup WARN Atlas prints about DFlash and multi-turn cache hits describes a real but small effect here: about one accepted
token per 20 steps, against a first-turn level of 2.2 and llama.cpp's 0.74 acceptance rate on the same drafter lineage.

**What it changes.** [[F175]]'s cause is closed unexplained, by the rule fixed in E150's and E151's preregs: attention pattern
(E149, [[F176]]), context cap (E150, [[F177]]) and prefix cache (E151) are retired, the HIP kernel path is what remains, and this
project does not pursue engine internals. Operationally nothing changes from [[F172]]: on this box Atlas's usable speculative mode
is MTP, and it is behind llama.cpp with a drafter. Method, for the next engine claim: one variable per arm, the vendor's own
explanation tested first, a hard cap so a dead arm costs 40 minutes, and the per-turn server log as the ruler when the harness is
capped.

Evidence: `results/e151-results.md`, `results/raw/e151/M6/`, prereg `results/e151-prereg.md`, `tools/score_capped_atlas_arm.py`
(the M3p same-turns split). See [[F175]], [[F176]], [[F177]], [[F172]].

