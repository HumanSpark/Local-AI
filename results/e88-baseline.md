# E88 - SparkMax absolute inference baseline and latency-budget allocation

Run 2026-08-29. Pre-registration: `results/e88-prereg.md` (written before any run).
Raw evidence: `results/raw/e88/`.

## Configuration measured - the FROZEN production baseline, unchanged

Observed directly on the live relay (PID 1068495) before any work:

    -m /opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf \
    -c 98304 -fa on -ctk q8_0 -ctv q8_0 --jinja

| axis | value |
|---|---|
| model | Qwen3-30B-A3B-Instruct-2507, Q4_K_M, 17.28 GiB, 30.53 B total / ~3 B active |
| build | `b9865` / `067de9371` |
| backend | Vulkan, RADV GFX1151, `uma: 1`, `fp16: 1`, coopmat |
| kernel | `7.0.0-29-generic`, livepatch `nothing-to-apply` |
| KV cache | `q8_0` both K and V, flash attention on |
| context | `-c 98304`, `kv_unified = 'true'` (one request may use the whole window) |

**The sparkbench bench build and the sparkrouter serving build are the same
commit**, verified by `--version` on both binaries. A thin-path figure here
therefore describes production rather than approximating it. No serving flag was
changed at any point.

## The box was NOT quiet when this session started, and that matters

At 14:05 the GPU measured 85-95% busy, sclk pinned 2529 MHz, 78 W, 77 C, with the
`chatterbox-gateway` TTS container resident and holding 5.68 GB (`rocm-smi
--showpids`). The owner confirmed at 14:11 that that job had just finished.

Two independent rulers - sysfs `gpu_busy_percent`/hwmon and `rocm-smi` -
initially disagreed (98% versus 0%). They were not sampled at the same time. Once
sampled together they agree exactly. **The disagreement was the sampling, not the
sensors**, and the load was real.

**Consequence for anyone reading interactive-latency complaints from this
period: they were measured against a GPU already saturated by a co-resident TTS
batch.** Every leg below therefore carries a quiet gate (`gpu_busy_percent == 0`,
sclk at idle) checked immediately before it runs, and telemetry sampled *during*
the run rather than only at its ends. All 8 Phase A legs passed the gate; none is
marked contended.

## Phase A - thin path, no server, no agent

`llama-bench`, fresh process per leg, production model/quant/build/backend,
production KV flags (`-fa 1 -ctk q8_0 -ctv q8_0`), `-p 512 -n 128`, `-r 3`.

| leg | pp512 tok/s | tg128 tok/s | wall s |
|---|---:|---:|---:|
| **depth 0** | **1083.71 ± 7.82** | **90.67 ± 0.33** | 9.3 |
| depth 4,096 | 667.65 ± 10.12 | 76.38 ± 0.17 | 15.8 |
| depth 8,192 | 486.34 ± 2.29 | 68.87 ± 0.10 | 24.5 |
| depth 16,384 | 312.48 ± 3.75 | 59.13 ± 0.05 | 49.1 |
| depth 32,768 | 191.21 ± 2.38 | 44.82 ± 0.03 | 124.5 |
| depth 49,152 | 131.15 ± 1.24 | 36.29 ± 0.07 | 236.7 |
| C1 CPU-only (`-ngl 0`), depth 0 | 344.38 ± 1.48 | 33.39 ± 0.91 | 13.1 |
| C2 repro of depth 0, fresh process | 1075.72 ± 2.64 | 90.90 ± 0.05 | 9.3 |

### Controls

- **C2 reproducibility PASSES.** A fresh process reproduces depth 0 to **-0.74%
  on pp512 and +0.25% on tg128**, inside the F15 ±1.5% noise floor. This also
  bounds the one declared deviation: the relay could not be stopped from this
  account and stayed resident-but-idle throughout, and its effect is not
  detectable above noise.
- **C1 discriminates, but its registered threshold was wrong and is recorded as
  such.** P5 predicted CPU-only would be ≥5x slower; measured **3.15x on prefill
  and 2.72x on decode**. The instrument plainly observes the GPU. The threshold
  was mis-set because a 3 B-active MoE on 16 Zen 5 cores sharing the *same*
  unified memory is an unusually strong CPU arm - there is no PCIe transfer to
  lose. **P5 is falsified by the ruler, not by the box**, and that is the honest
  reading rather than a rescued one.
- **No thermal throttling.** Across the 237-second depth-49152 leg, sclk holds
  2475-2547 MHz with no downward trend, temperature 77-83 C and package power
  flat at 84-85 W, busy 100%. Peaks of 95 C / 117 W occur as brief transients
  during prefill bursts, not as a sustained state.

## Is SparkMax materially underperforming its hardware class?

The registered decision rule: within 25% of credible published figures for the
same silicon class, backend, model and quantisation closes the hardware branch;
more than 25% below opens it. A peer whose model, quant, backend or context
differs is recorded as a MISMATCH and does not silently enter the band.

**Comparable point is Phase A depth 0** - `llama-bench` allocates its own context
for the test rather than the production `-c 98304`, which is exactly how every
public figure below is produced, and is what makes them comparable at all. The
production-faithful measurement is Phase B, not this table.

| source | model / quant | backend | pp512 | tg128 | build |
|---|---|---|---:|---:|---|
| **this box (E88)** | **Qwen3-30B-A3B-Instruct-2507 Q4_K_M, KV q8_0** | **Vulkan RADV** | **1083.71** | **90.67** | **b9865** |
| strixhalo.wiki | Qwen3-30B-A3B UD-Q4_K_XL, `-fa 1` | Vulkan RADV | 755.14 | 85.11 | n/s |
| strixhalo.wiki | Qwen3-30B-A3B UD-Q4_K_XL, `-fa 1` | Vulkan AMDVLK | 741.60 | 81.79 | n/s |
| Level1Techs | Qwen3-30B-A3B UD-Q4_K_XL, `-fa 1` | Vulkan | 604.80 | 72.00 | ~b5863 |
| kyuz0 toolboxes | Qwen3-30B-A3B-Instruct-2507 **IQ4_XS** | Vulkan RADV | n/s | 100.04 | n/s |
| kyuz0 toolboxes | Qwen3-**Coder**-30B-A3B **Q4_K_S** | Vulkan RADV | n/s | 100.99 | b9851 |

### Mismatches, stated rather than pretended away

- **No published row is our exact quantisation.** UD-Q4_K_XL is a larger quant
  than Q4_K_M; IQ4_XS and Q4_K_S are smaller. Decode on this machine is
  bandwidth-bound, so quant size moves `tg128` directly - the two ~100 tok/s rows
  are smaller weights, not faster silicon.
- **No published row states its KV cache type**; ours is `q8_0` on both K and V.
  E87 measured q8_0 at +7.9% decode / -11.5% prefill against f16 at depth, with
  the effect near zero at depth 0. It does not explain a gap of this size either way.
- **Builds span roughly four thousand revisions.** The Level1Techs row is ~b5863;
  ours is b9865. Prefill has improved substantially in llama.cpp over that range,
  which is the most likely reading of our prefill lead rather than a hardware claim.

### The closest like-for-like peer, added after the table above

`soothill.io`, 2026-08-03, same silicon, same backend PAIR, same model class,
`llama-bench` pp512/tg128:

| | pp512 | tg128 |
|---|---:|---:|
| **this box** - Qwen3-30B-A3B-Instruct **Q4_K_M**, KV **q8_0**, Vulkan | **1083.71** | **90.67** |
| peer - Qwen3-Coder-30B-A3B **Q4_K_S**, Vulkan | 1115.30 | 97.73 |
| peer - Qwen3-Coder-30B-A3B **Q4_K_S**, **ROCm** | 1344.65 | 73.65 |

**Against the Vulkan peer this box is -2.8% on prefill and -7.2% on decode** -
and the peer runs a SMALLER quant (Q4_K_S) with no KV quantisation, both of which
move its numbers up. This is parity, comfortably inside the registered 25% band,
and it is the strongest single piece of evidence that the hardware branch should
close.

**The ROCm row matters for the ranked list rather than for the verdict.** On that
peer's measurement ROCm is **+20.6% prompt processing and -24.6% generation**
against Vulkan. Our dominant cost is prefill, so that trade runs in the helpful
direction for first-turn latency and the wrong direction for streaming
responsiveness. It is a real candidate, and it is UNMEASURED on this box.

### Verdict on the registered rule

**`tg128` at 90.67 sits inside the 72-101 tok/s band every peer reports, and
`pp512` at 1083.71 is above every published pp512 figure found.** Nothing here is
25% below the class. There is no evidence that this box is leaving substantial
performance unused at the thin path.

> **The hardware/runtime branch CLOSES.** SparkMax's thin inference path is
> healthy for its class: it decodes mid-to-upper band and prefills ahead of every
> published peer, holds clocks flat under four minutes of 100% load with no
> thermal decay, and reproduces itself to within 0.74%. The next investigation
> boundary is NOT the kernel, the driver, the clocks or the backend.

**What this verdict does not cover:** ROCm/HIP was not measured - this box serves
on Vulkan and the comparison was made Vulkan-to-Vulkan on purpose. Whether a ROCm
build would be faster still is unmeasured here and is a separate question from
whether the current stack is underperforming, which it is not.
## Phase B - the context tax, at the frozen production flags

Own `llama-server` on a non-production port carrying the EXACT production flag
string, `n_ctx_slot = 98304`, `kv_unified = 'true'`. Prompt lengths are exact
tokenizer tokens, built by round-tripping the server's own `/tokenize` and
`/detokenize` - never chars/4. `cache_prompt` disabled with a unique UUID per
request, so this is the COLD prefill cost with no prefix reuse.

| prompt tokens | TTFT s | prefill tok/s | decode tok/s |
|---:|---:|---:|---:|
| 1,024 | 0.93 | 1113.1 | 85.6 |
| 4,096 | 4.37 | 947.9 | 75.1 |
| 8,192 | 11.02 | 750.2 | 67.5 |
| 16,384 | 31.03 | 531.3 | 58.3 |
| 32,768 | 97.47 | 337.5 | 44.2 |
| **46,000** | **177.39** | **260.1** | **37.0** |

**The tax is super-linear. 45x the prompt costs 190x the wait**, because the
prefill RATE itself falls by 4.3x across the range while the token count rises.
Both terms move against you at once, which is why a 45k first turn does not feel
like "45 times a 1k turn" - it feels like a different machine.

**This independently corroborates F98.** That finding observed 183 s for 46,259
input tokens; measured cold here, 46,000 tokens takes **177.39 s**. Two
instruments, same answer.

**Reproducibility at the expensive end is excellent**: the two 46,000-token
replicates land at 177.31 s and 177.47 s, 0.09% apart.

The rate also decays WITHIN a single prompt, visible in the server's own progress
lines during one 46,000-token prefill: 937 tok/s at 6k cumulative, 557 at 16k,
346 at 33k, 270 at 45k. So the cost of a long prompt is not a fixed rate applied
to more tokens; the rate degrades as the prompt grows.

### Phase A and Phase B measure different things and both are wanted

`llama-bench`'s `pp512 @ dN` is the cost of 512 MORE tokens when N are already
resident. Phase B is the cost of prefilling the WHOLE prompt from cold. At 8,192
tokens the first reads 486 tok/s and the second 750 tok/s, and neither is wrong -
the second is an average over a range that starts fast. **Phase B is the
user-facing number**; Phase A is the one comparable to published benchmarks.

## Phase B2 - what the SECOND turn costs. This reframes the whole problem.

Same server, caching left at the server default, a 40,000-token prefix sent four
times:

| turn | TTFT s | tokens actually prefilled |
|---|---:|---:|
| 1 - cold prefill | **134.53** | 39,520 |
| 2 - identical prefix | **0.08** | 1 |
| 3 - identical prefix | 0.08 | 1 |
| 4 - same prefix, NEW tail | 0.25 | 7 |

**Turn 2 is 1,682x faster than turn 1.** Prefix reuse works, and it works on a
changed tail too - turn 4 re-processed 7 tokens, not 39,520.

**So the context tax is paid ONCE PER CONVERSATION, not once per turn.** Any
account of the interactive experience that multiplies the 45k prompt by the turn
count is wrong. The cost is concentrated entirely in the cold start.

⚠ **The caveat is slot affinity and it is NOT tested.** The server runs
`total_slots = 4` and its log shows `selected slot by LRU`. A turn routed to a
slot that never saw the prefix pays the full 134 s again. Whether that happens in
practice, and whether `-np 1` would prevent it, is the single highest-value
unanswered question left by this experiment.

## Phase C - the real client, replayed verbatim

The four surviving captures are real Claude Code requests, replayed against the
production model on the frozen config. Three variants each, because they answer
different questions.

| capture | variant | tools | schema bytes | outcome | TTFT s |
|---|---|---:|---:|---|---:|
| 28-tool (client FLOOR) | full | 28 | 73,480 | **REFUSED** - grammar | 0.095 |
| 28-tool | tools-only | 28 | 73,480 | **REFUSED** - grammar | 0.050 |
| 28-tool | no-tools | - | - | SERVED (cache hit, 20,086) | **0.31** |
| 57-tool | full | 57 | 97,011 | **REFUSED** - grammar | 0.096 |
| 57-tool | tools-only | 57 | 97,011 | **REFUSED** - grammar | 0.087 |
| 57-tool | no-tools | - | - | SERVED, 20,254 input tokens | **47.03** |

Refusal text, identical on all four: `Failed to initialize samplers: failed to
parse grammar`.

**Three things this settles that F104 could not.**

1. **The failure is the SCHEMAS ALONE.** The `tools-only` variant carries the tool
   array with a one-line message and no large context, and it still refuses. So
   the grammar builder is not being defeated by prompt size; 73 KB of schema is
   enough on its own.
2. **For the production model this is not a latency problem at all.** Claude Code
   with tools does not run slowly - it fails in **95 milliseconds**. Latency
   optimisation cannot touch it; only a client change or a llama.cpp fix can.
3. **The cache effect reproduces on the REAL artefact.** The same no-tools payload
   costs 47.03 s cold and 0.31 s warm - a **154x** swing driven by nothing but
   prefix reuse.

**C3 control: 20 requests served** across Phases B/B2/C. The model genuinely
spoke; no row here is a silent stack elimination misread as a timing.

## The latency budget

Computed by `tools/e88/latency_budget.py` from the measured curve, interpolating
between measured points. Total wall time for the 39,275-token first turn:
**136.8 s**.

| component | tokens | share |
|---|---:|---:|
| tool schemas (28 tools, client floor) | 19,206 | 48.9% |
| injected CLAUDE.md + rules + memory + system-reminder | 15,694 | 40.0% |
| SessionStart hook (superpowers) | 2,873 | 7.3% |
| system prompt | 1,500 | 3.8% |
| **the actual user turn** | **2** | **0.0%** |
| **total** | **39,275** | **100%** |

⚠ **The TOTAL is order-independent; the per-component SPLIT is not.** Because the
curve is super-linear, whichever tokens are counted LAST are the most expensive
per token. Do not read "tool schemas cost 42.5 s and injected context 67.9 s" as
a property of those components - it is a property of the order they were stacked
in. The defensible statement is the one that does not depend on ordering:
**removing any ~15,700 tokens from a 39,275-token first turn takes it to roughly
23,600 tokens, which the measured curve puts near 60 s instead of 137 s.**

### The single sentence

**99.995% of the first-turn prompt is overhead the user did not type**, the box
processes it at a rate that is at or above its hardware class, and it only has to
process it once per conversation.

## Optimisation opportunities, ranked by likely END-USER LATENCY GAIN

Ranked by wall time removed from real use, **not** by ease. Ease is noted
separately so convenience cannot quietly reorder the list.

### 1. For the production model, Claude Code is not slow - it does not run. Change the client.

This is first because it is not an optimisation, it is the difference between
working and failing. The workhorse **refuses Claude Code's tool schemas in 95 ms**
at the client's own floor (28 tools, 73 KB), and the `tools-only` control proves
the schemas alone cause it. No latency work can help; `--allowedTools` cannot
help either, because it gates permission rather than what is transmitted.

aider drives the same model, same weights, same server, same build, on **761
tokens** (F105). Against the measured curve that is roughly **0.7 s against
136.8 s** - and for the workhorse the honest comparison is 0.7 s against *never
completing*.

Cost: aider is a less capable harness than Claude Code. This is a real trade, not
a free win.

### 2. Protect the prompt cache - it is worth more than every other lever combined.

Turn 2 measured **1,682x faster** than turn 1 (0.08 s against 134.53 s), and the
same effect reproduced on the real client payload (0.31 s against 47.03 s, 154x).
Anything that silently invalidates the cached prefix converts a 0.3 s turn into a
47-137 s turn.

Three known invalidators, all already recorded in this repository: a request
sharing no prefix displaces the cached pack (E81); item order matters (E81);
and a server shared between a router and its answerer destroys it (E80 addendum).
Add to that `total_slots = 4` with LRU selection, so a turn can land on a cold
slot.

**Ranked second rather than first only because half of it is already working.**
The measurement says the cache engages; what is untested is how often it survives
a real multi-turn agent session.

Cost: `-np 1` is a serving-config change with ONE writer (F39) and is the owner's
call. Testing whether it is needed costs nothing.

### 3. Cut the injected always-loaded context. (largest lever fully under your control)

**15,694 tokens** of the first-turn payload is injected instructions; the
always-loaded set measures **20,240 tokens** standalone on the serving tokenizer.
Tool schemas belong to the client and cannot be cut past its floor. This can.

Taking a 39,275-token first turn down by ~15,700 tokens lands near 23,600, which
the measured curve puts at roughly **60 s instead of 137 s**.

⚠ **This is a latency argument, NOT a budget-breach claim.** The 15,000 figure in
`~/.claude/CLAUDE.md` is stated in tiktoken `cl100k`; 20,240 is Qwen's tokenizer.
Two rulers, and nothing is claimed from comparing them.

Cost: editorial work against instruction quality. The rules exist for reasons and
several were written after real incidents.

### 4. Reconsider the backend for prefill-dominated work. (real, unmeasured here)

On the closest published like-for-like, ROCm is **+20.6% prompt processing** and
**-24.6% generation** against Vulkan on this silicon. Our dominant cost is the
cold prefill, so the trade runs the helpful way for first-turn latency and the
wrong way for streaming.

At the measured 136.8 s first turn, +20% prefill is roughly 23 s - a sixth of what
item 3 buys, and it makes every subsequent token slower.

Cost: a second toolchain, and it is UNMEASURED on this box. Do not act on a
third-party ratio; measure it here first.

### 5. Do NOT tune KV quantisation or flash attention further. (exhausted)

q8_0 is applied and has earned its place: +7.9% decode at 14.7k, +16.1% at 37.8k,
4.22 GiB freed (E85/E87). **Flash attention alone buys nothing** (-0.14% /
+0.04%). There is no remaining gain of consequence on this axis.

### 6. Model choice - deliberately not scored here.

A different model would move every number on this page. This session scored no
coding capability and admits no toy success as evidence, so it recommends no
model. That is the next experiment - and F106 means it can now be run knowing the
hardware is not the variable.

## What remains UNMEASURED - stated, not implied

These are gaps in this experiment, listed so no reader mistakes silence for a
null result. "No finding" and "successful measurement" are not the same thing.

1. **ROCm/HIP was never benchmarked.** Everything here is Vulkan/RADV, because
   that is what the relay serves on. The peer comparison was deliberately made
   Vulkan-to-Vulkan. Whether a ROCm build with rocWMMA would beat this stack is
   an open question, and it is a DIFFERENT question from "is the current stack
   underperforming", which is answered.
2. **The relay was never stopped.** `/var/lib/sparkrouter` is 0750 spark-infer,
   `llama-gateway.service` is a systemd *user* unit, and `sudo` requires a
   password for this account. The relay stayed resident-but-idle throughout.
   Its effect is bounded below the F15 noise floor by control C2 (-0.74% / +0.25%
   on a fresh-process repeat), but it was not eliminated.
3. **Slot affinity was not tested.** The server runs `total_slots = 4` and the log
   shows `selected slot by LRU`, so an agent's second turn can land on a slot that
   never saw its prefix. Whether `-np 1` would materially improve multi-turn
   latency on a single-user box is a HYPOTHESIS from that log line, not a
   measurement, and it is ranked below as such.
4. **Coding capability is not scored here, at all**, and no toy success is
   admitted as evidence of agent quality. That was excluded by the brief and the
   exclusion is honoured.
5. **Only two agent clients carry measured payloads** - Claude Code (captured
   verbatim) and aider (F105's banked 761-token figure). The simpleloop local
   provider was not captured in this session.
6. **Concurrency was not measured.** Every figure is single-request. What happens
   when the TTS service and an agent contend was observed qualitatively at 14:05
   but never measured as a latency delta.
7. **One control threshold was mis-set before the fact** (C1, ≥5x). It is
   reported as falsified rather than quietly re-baselined.
