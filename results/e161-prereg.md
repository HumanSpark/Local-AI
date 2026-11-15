<!--
# File: e161-prereg.md
# Purpose: Pre-registration for E161 - does a "helper" for MoE experts (CPU cores, or tandem.cpp's hot-expert scheme) speed
# up Flash-Next on one unified-memory box, and how concentrated is expert routing on our real work?
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Two parts. SPEED: seven arms of llama.cpp-family engines on Qwen3.8-Flash-Next UD-IQ4_XS, timed by
# tools/e153_speed.py on E153's fixed prompts, varying only where the routed experts run. SKEW: llama-imatrix routing
# counts per expert on three corpora of our own work, read by tools/e161_skew.py. Runner tools/run_e161_window.sh,
# builds tools/e161_build.sh. Written before any arm ran.
-->

# E161 PRE-REGISTRATION - expert helpers on unified memory, and routing skew (2026-11-15)

## In plain English

Tandem (github.com/ewhacc/tandem) speeds up big "mixture of experts" models on PCs with a graphics card. It keeps the
most-used experts in the card's fast memory and lets a second card or the CPU compute the rest. Our machine has a
single shared memory pool, so we expect the trick to give nothing here. This experiment checks that cheaply, including
with tandem.cpp itself.

The second half measures something the trick depends on: whether a few experts do most of the work on our real tasks.
If they do, a model could keep its busy experts at high precision and squeeze the rest. That could fit a better large
model into this box's memory. If they don't, that idea is dead for this model and we say so.

## Why (owner 2026-11-15)

The owner asked whether Tandem suggests an experiment here. My analysis, given before any run: on unified memory there
is no slow tier to cache experts out of, and CPU and GPU share one memory bus (F41: concurrent work splits it), so a
helper should not pay. The owner chose this test (CPU-helper sweep + skew) and asked for a tandem.cpp arm.

## Engines and model

- **Model (all speed arms):** unsloth Qwen3.8-Flash-Next UD-IQ4_XS, three shards, `/opt/models/staging/qwen3.8-flash-next-udiq4xs/`
  (MANIFEST E153 entry). 48 layers, 512 routed experts per layer, 10 used per token, plus a shared expert.
- **M arms:** llama.cpp mainline `e574a17b0` (2026-11-15, newest at prereg), Vulkan, built by `tools/e161_build.sh mainline`.
- **T arms:** tandem.cpp (MIT, ewhacc/tandem.cpp, commit recorded in `results/e161/build-tandem.log`), a patch on llama.cpp
  `f5222f25c` (its BASE_COMMIT), built with HIP for gfx1151. Upstream documents gfx1100 only; gfx1151 is untested there.

## Arms (speed)

Common: `-m <shard 1> -c 65536 -np 1 -fa on -ctk q8_0 -ctv q8_0 --jinja -ngl 99 --host 127.0.0.1 --port 8161`, one arm
at a time, nothing else on the GPU (relay idle window). `-t 16` on every arm (16 physical cores).

| arm | engine | where routed experts run |
|---|---|---|
| M0 | mainline Vulkan | all on GPU (E153 L0's config on a newer build) |
| M4 | mainline Vulkan | `--n-cpu-moe 4`: experts of the first 4 layers on CPU |
| M12 | mainline Vulkan | `--n-cpu-moe 12` |
| M24 | mainline Vulkan | `--n-cpu-moe 24` (half the layers) |
| T0 | tandem.cpp HIP | all on GPU (no `-cmoe`): the T build's own baseline |
| T1 | tandem.cpp HIP | `-cmoe --moe-cache-mib auto -lm none` (its README recipe): experts in host RAM, GPU cache of hot experts, CPU computes misses |

T1 is compared with T0 (same binary), never with M0: HIP versus Vulkan is a separate variable.

## Workload (speed)

`tools/e153_speed.py` with `results/e153/prompts.json`, buckets **CODE, PROSE, JSON, P8K** (14 requests; AGENT and P32K
are dropped to bound CPU-arm time). Greedy, thinking off, one stream, client clock. Order M0 M4 M12 M24 T0 T1.

## Skew

`llama-imatrix` (mainline M build, all on GPU) with `-c 512 --chunks 120` (61,440 tokens per corpus, exact), writing the
GGUF imatrix, whose per-expert `counts` give routed tokens per expert per layer. Three corpora, built by
`tools/e161_corpus.py` into `results/e161/corpus/` (gitignored: the code corpus quotes private repositories):

- **code:** the model's own E159 HFL agent transcripts (its reads, edits and reasoning on ten real fixes).
- **docs:** the real lab documents behind kw-eval (findings register, routing guide, harness rules).
- **prose:** Flash-Next's own E160 KFL answers (writing, conversations, document answers).

Fields, per corpus, per layer, over the 512 routed experts (`tools/e161_skew.py`):
- `cov20` = share of routed tokens that went to the top 20% (102) experts. Uniform routing gives 0.20.
- `cov10` likewise for the top 10%.
- `jaccard_top20(a,b)` = overlap of the top-20% expert sets of corpora a and b.
- `dead` = experts with zero routed tokens.
Reported as the median over the 48 layers, plus the minimum and maximum.

Limitation, declared: imatrix routes the corpus as PROMPT tokens. Decode routes generated tokens. Two corpora are text
the model itself generated, which is the closest proxy without patching the engine.

## Predictions

Speed fields are `buckets.<B>.decode_tps_median` and `buckets.P8K.prefill_tps_median` in `results/e161/speed-<arm>.json`.

| | prediction | field |
|---|---|---|
| P0 | ruler: M0 CODE decode within ±15% of E153 L0's 27.06 | `M0.CODE.decode_tps_median` |
| P1 | every CPU arm decodes slower than M0 on CODE | `M4/M12/M24.CODE.decode_tps_median < M0` |
| P2 | decode falls monotonically with CPU layers | CODE: `M0 > M4 > M12 > M24` |
| P3 | half the layers on CPU costs at least 40% | `M24.CODE.decode_tps_median <= 0.6 x M0` |
| P4 | P8K prefill at least halves with half the layers on CPU | `M24.P8K.prefill_tps_median <= 0.5 x M0` |
| P5 | tandem's helper mode gives no decode gain on unified memory | `T1.CODE.decode_tps_median <= 1.05 x T0` |
| P6 | tandem.cpp builds and serves on gfx1151 (exploratory) | T0 answers all 14 requests |
| P7 | routing is moderately concentrated on code | median `cov20` (code) in [0.30, 0.55] |
| P8 | hot sets are workload-specific | median `jaccard_top20(code, docs)` < 0.5 |

A failed build or load in a T arm is the result for that arm (P5 and P6 then read UNSCORABLE / FAILED). It is not a
reason to change flags. One retry is allowed only for a documented typo in our own command line.

## Decision rule (stated now)

- If P1 holds for every CPU arm and P5 holds, the conclusion is that CPU or tandem-style expert helpers do not pay on
  this box. This is recorded as a finding and closes the CPU-helper question.
- **Mixed precision by hotness (a possible E162)** is proposed only if median `cov20 >= 0.60` on every corpus AND median
  `jaccard_top20 >= 0.5` for every pair. Below that, a fixed hot set would cover too little of real routing to justify
  a converter and an engine patch (mainline llama.cpp stores a layer's experts in one tensor, so per-expert precision
  needs both). The result would be recorded as "not worth it on Flash-Next". Flash-Next is a proxy here: the model
  where capacity binds is DeepSeek-V4.1-Flash, and a positive result would need re-measuring on it.

## Run notes

- Window: `sudo -n /usr/local/sbin/relay_bench_window.sh idle-down`, restored by `up` on any exit (the E154 runner's
  pattern). Production is down for the window, an estimated 1.5-2 h.
- Kernel and Livepatch are recorded at window open.

## Amendment 1 (2026-11-15, before any run)

The prose corpus from E160 KFL alone is 33,827 characters, about 8,500 tokens, far short of 120 chunks of 512. Change:
the prose corpus adds E160 KX's answers (the same model at maximum effort), and prose runs at as many 512-token chunks
as it holds, recorded in `results/e161/skew.json`. code and docs keep `--chunks 120`. At 10 routes per token, even 30
chunks give about 150,000 routes per layer over 512 experts, enough for share-of-routes fields. P7 is scored on code and
is unaffected; the E162 decision rule's every-corpus condition reads prose at its smaller sample.

## Amendment 2 (2026-11-15 04:20Z, after T1, before T2)

T1 did not test tandem's cache. Its server log reads "MoE cache auto size: less than 256 MiB free, the cache is
disabled". HIP on this unified-memory APU reports device memory as the small BIOS VRAM carve-out, not the shared pool,
so `--moe-cache-mib auto` sized the cache at zero and T1 ran every routed expert on the CPU. T1 stands as run and P5 is
scored on it as written, with that cause stated.

Added, exploratory and declared now: **arm T2** = T1's command with `--moe-cache-mib 24576` in place of `auto`
(about a quarter of the expert bytes, the top ~20-25% of experts, which took 67-70% of routes in the skew part).
Same build, prompts, buckets and client. The server log must show the cache enabled, or T2 is reported as not
engaged. Predictions:
- **P5b:** `T2.CODE.decode_tps_median <= 1.05 x T0` (a hot-expert cache cannot beat all-on-GPU when both read one pool).
- **P5c:** `T2.CODE.decode_tps_median > T1` (the cache should recover some of what CPU-only experts lose).
One short window, production restored and verified as before.
