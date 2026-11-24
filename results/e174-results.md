<!--
# File: results/e174-results.md
# Purpose: Results of E174 - f16 vs q8_0 KV cache on Qwen3.8 Flash-Next (llama.cpp Vulkan), three depths.
# Project: sparkbench | Date: 2026-11-23
#
# Overview: Scores the predictions in results/e174-prereg.md against results/e174/bench-d{0,8192,32768}.md
# (attempt 2, under amendment A1). Attempt 1 DeviceLost at load; logs in results/e174/attempt1-*.
-->

# E174 RESULTS - KV cache type on Flash-Next (llama.cpp)

## In plain English

Squeezing the model's conversation memory (the KV cache) to half size never made Flash-Next faster on llama.cpp.
Short chats: answers come out at the same speed, but reading the prompt is about 8% slower. Long chats (32K
tokens): answers come out about 10% slower. The only thing q8_0 buys is half the cache memory, so f16 stays the
default for any llama.cpp serving of Flash-Next. All three predictions were wrong. Production (Halogen) is a
different engine and is not affected.

Separately: the first attempt crashed the GPU at model load with ~68 GB of page cache held from an earlier file
check; the second attempt, which evicted the model files from page cache before every load, ran three 103.7 GiB
loads cleanly. That supports page-cache pressure as the trigger. It is one run, not proof.

## Setup

llama.cpp `94f3af3d0`, `llama-bench -ngl 999 -fa on -ctk f16,q8_0 -ctv f16,q8_0 -p 512 -n 128 -r 3`, one
invocation per depth, kernel 7.0.0-43, Flash-Next UD-Q4_K_XL (103.68 GiB). Attempt 2 20:57:06-21:11:25Z.
Relay restored and probe-verified 21:12:31Z (decode 80.7 t/s; first POSITIVE case of the fixed probe).

## Matched pairs (t/s, mean ± sd of 3)

| Depth | Test | f16/f16 | q8_0/q8_0 | q8_0 vs f16 |
|---|---|---|---|---|
| 0 | pp512 | 516.68 ± 2.25 | 477.00 ± 4.19 | −7.7% |
| 0 | tg128 | 26.68 ± 0.03 | 26.57 ± 0.03 | −0.4% (noise) |
| 8192 | pp512 | 427.77 ± 7.69 | 419.38 ± 6.36 | −2.0% |
| 8192 | tg128 | 25.92 ± 0.26 | 25.89 ± 0.02 | −0.1% (noise) |
| 32768 | pp512 | 346.06 ± 2.44 | 341.17 ± 2.86 | −1.4% (noise) |
| 32768 | tg128 | 25.01 ± 0.02 | 22.45 ± 1.37 | −10.2% |

Mixed pairs (reported, not scored) are slower than either matched pair on pp512 at every depth: d0 492.13 / 489.18,
d8192 395.55 / 378.32, d32768 296.63 / 264.33 (f16-K/q8-V, q8-K/f16-V). Raw: `results/e174/bench-d*.md`.

## Predictions

- **P1 FALSIFIED.** `tg128@d0[q8_0]` 26.57 vs 26.68 = −0.4%, inside the ±1.5% floor, not >5% below.
- **P2 FALSIFIED.** `tg128@d32768[q8_0]` 22.45 < 25.01. Caveat: that cell's sd is 1.37 over 3 reps; even mean+sd
  (23.82) is below f16.
- **P3 FALSIFIED.** `pp512@d0[q8_0]` 477.00 vs 516.68 = −7.7%, outside ±3%.

## Deviations

- `failed to restore kv cache` x3 per depth>0: llama-bench reloads a saved depth state between instances; the state
  does not fit a different KV type, so it re-fills from scratch (`llama-bench.cpp` 2472-2474). Benign; every figure
  was measured at its full depth.
- Attempt 1 DeviceLost at load (prereg run log); A1 (page-cache eviction) declared before attempt 2. Kernel log
  (`results/e174/attempt1-kernel.txt`): eight `Couldn't update BO_VA (-12)` at 20:26:50 - the F198 -ENOMEM signature -
  with GTT at baseline; no reset, no oops. See F199 / F198 addendum.
