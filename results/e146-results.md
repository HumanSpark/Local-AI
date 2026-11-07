# File: e146-results.md
# Purpose: Results for E146 - does the Atlas inference engine deliver its published Strix Halo speed, and does it beat llama.cpp on the MLPerf edge-agentic metric?
# Project: sparkbench | Date: 2026-09-25
#
# Overview: Scored against results/e146-prereg.md and Amendments 1-3, gates in results/e146-gates.md. Three gateway
# windows (01:21-03:09, 04:14-04:45 stopped, 04:46-05:53). On a 4-trajectory (206-turn) subset of MLCommons' own harness,
# Atlas (patched HEAD, and the MLPerf entry's shipped source) takes about 27% less time per turn than the llama.cpp reference
# and stays within 0.03 of its inline accuracy; the published 7,059 ms is NOT reproduced (9.3-9.5 s here). The registered arm M1
# could not load the checkpoint. Scorer: tools/score_e146.py; output results/raw/e146/score-final.txt. Registered as F168-F170.

# E146 RESULTS - Atlas is about 27% faster than the llama.cpp reference here, and not as fast as published (2026-09-25)

## Block M - MLCommons edge-agentic harness, Qwen3.6-27B, 4 of 20 trajectories (206 turns)

| arm | what it is | turns ok | mean latency | median | p95 | TTFT median | tps | accuracy | paired vs M0 |
|---|---|---|---|---|---|---|---|---|---|
| **M0** | llama.cpp `daef7b6`, the MLPerf reference (Q4_K_M, no speculation) | 206/206 | **12,863 ms** | 8,704 | 33,553 | 4,479 | 6.36 | 0.637 | 1.000 |
| M1 | Atlas-Inf HEAD 2d1aab8, as registered | **VOID** | - | - | - | - | - | - | - |
| M1p0 | M1p with prefix caching OFF (aborted at 29 of 206 turns) | stopped | 61 s per turn | - | - | - | - | - | not scored |
| **M1p** | Atlas-Inf HEAD **plus a one-line patch** (not the vendor's code), prefix caching on | 206/206 | **9,307 ms** | 6,358 | 25,133 | 3,432 | 8.56 | 0.622 | **0.724** |
| **M1s** | the MLPerf entry's shipped source, native-HIP reconstruction, prefix caching on | 206/206 | **9,453 ms** | 6,673 | 23,917 | 3,656 | 6.75 | 0.606 | **0.735** |

- **Paired comparison** (the same 206 turns, joined on conversation and turn): M1p/M0 = 0.724 and M1s/M0 = 0.735. In issue order, thirds
  are 0.748 / 0.717 / 0.711 for M1p and 0.794 / 0.687 / 0.738 for M1s: the advantage is consistent, not driven by a few turns.
  Band: "Atlas-code faster than the reference" for both. Inline accuracy is within 0.015 (M1p) and 0.032 (M1s) of M0.
- **Published latency NOT reproduced.** The entry reports 7,058.99 ms on its Strix Halo. M1p is 1.32x and M1s 1.34x that figure,
  outside the registered +/-25% band. This holds for THIS code and THIS box only. Declared differences: ROCm 7.2.4 (theirs 7.13), about
  105 GiB GTT (theirs about 62.5 GB), Chatterbox TTS resident, a 4-trajectory subset whose turn mix differs from the full 1,007 turns.
- **The comparator is the reference, not the best llama.cpp.** M0 has no speculation; Atlas runs MTP K=3. A llama.cpp arm with a drafter on
  Qwen3.6-27B was not run. Block 1 (below) shows the size of that gap on Qwen3.8.

## Block 1 - speed client, Qwen3.8-27B (one ruler for every engine)

| arm | CODE tok/s | CHAT tok/s | D1500 | P8K prefill | P32K prefill (TTFT) | decode at 32K | determinism (10 identical greedy) |
|---|---|---|---|---|---|---|---|
| Q0 llama.cpp, no drafter | 10.35 | 11.89 | 10.96 | 151 | 141.8 (231 s) | 8.75 | 1 distinct |
| Q1 llama.cpp + DFlash2 drafter, n=4 | 23.56 | 10.96 | 14.14 | 191 | 139.0 (236 s) | 11.66 | 1 distinct |
| **X1 Atlas HEAD, MTP K=4** | **27.18** | **15.27** | 15.97 | 175 | 139.6 (235 s) | 13.26 | **3 distinct** |

- **README claim "28.3 to 28.6 tok/s"** (Qwen3.8 K=4): X1 CODE 27.18, **CONFIRMED** (band >= 26.0). Its 32K decode of 13.26 matches the
  README's "13.3 to 13.6".
- **X1 vs Q1 (Atlas vs llama.cpp with a drafter):** CHAT 1.394x, clear (X1 14.9-15.6 against Q1 10.93-11.00, no overlap). CODE 1.154x, at the
  1.15 threshold, and **not established**: Q1's repetitions were 30.85 / 23.56 / 23.45 and X1's 25.00 / 27.19 / 27.18, so the ranges overlap. By the
  registered rule ("faster on both if >= 1.15 on both") it is "Atlas faster", by 0.4% on CODE.
- **Prefill is the same on all three engines at 32K**, about 140 tok/s.
- **Atlas is not byte-deterministic** here: 3 distinct outputs in 10 identical greedy requests.
- **Ruler check:** Q0 CODE 10.35 here against E138's 12.33 (server-reported) for the same model and engine; Q1 23.56 against 25.67. The client-side
  ruler reads 4-16% lower (CHAT 4%, Q1 CODE 8%, Q0 CODE 16%), which is why the baselines were re-run in the same window and E138's figures are never mixed with Atlas's.

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| PM1 | an Atlas arm serves the MLPerf checkpoint | YES | M1 **no**; M1p and M1s yes | **M1 FALSIFIED**; M1p, M1s HELD |
| PM2 | mean turn latency, Atlas | 5,500-9,500 ms | M1p 9,307; M1s 9,453 | HELD (both near the upper edge) |
| PM3 | mean turn latency, M0 | 8,000-16,000 ms | 12,863 | HELD |
| PM4 | paired ratio Atlas/M0 | 0.45-0.90 | 0.724; 0.735 | HELD |
| PM5 | accuracy within 0.05 of M0 | yes | 0.015; 0.032 | HELD |
| PM6 | tps | 7-14 | M1p 8.56; M1s 6.75 | M1p HELD, **M1s FALSIFIED** |
| P1 | X1 serves | YES | yes | HELD |
| P2 | X1 CODE decode | 22-32 | 27.18 | HELD |
| P3 | X1 CHAT decode | 13-20 | 15.27 | HELD |
| P4 | X1/Q1 CODE | 0.85-1.25 | 1.154 | HELD |
| P5 | X1/Q1 CHAT | 0.75-1.25 | 1.394 | **FALSIFIED** (Atlas faster than predicted) |
| P6 | X1/Q1 P32K prefill | 0.5-2.0 | 1.004 | HELD |
| P7 | X1 decode at ~32K | 9-16 | 13.26 | HELD |
| P8 | X1 determinism | 10 of 10 equal | 3 distinct | **FALSIFIED** (the fresh-process half was not run) |
| P9 | SCALE lineage arm | - | withdrawn | Amendment 1 |
| P10 | X1 GPU memory above the window-open baseline | 20-32 GiB | 66.1 (peak 74.4) | **FALSIFIED**: Atlas reserves its pool up front at `GPU_UTIL=0.60`, so peak reflects the setting |
| P11 | block 2 (Aider) | 3-7 of 9 | not run | not scored |

## What went wrong, and how it was handled

1. **M1 could not load the checkpoint (Amendment 2).** HEAD's `mixed_precision_variant` counts a layer as NVFP4 only when `quant_algo == "NVFP4"`;
   this checkpoint labels its 193 MLP layers `W4A16_NVFP4`, so the whole model went down the FP8 path and failed at `mlp.gate_proj`. Found by reading the
   code. M1 stays VOID; M1p (one-line patch) and M1s (the shipped source) were declared and run instead.
2. **M1p0: prefix caching was off (Amendment 3).** 61 s per turn against 12.9 s for M0, from re-prefilling 16K-token histories every turn. My omission:
   `--enable-prefix-caching` and `--ssm-cache-slots` were not passed. Stopped after 29 turns (gateway down 31 min), corrected, re-run. With it on, 9.4 s per turn.
3. **The bank step failed for the first arms:** the commit hook's secret pattern matched "token" inside the 12.7 MB harness conversation log. Nothing was lost;
   the log stays local, a compact `per-turn.json` is banked, and the script now reports a refusal. The scorer's first memory baseline was also wrong (taken after
   the server loaded) and was fixed before the figure was reported.
4. **Two amendment headers carried times written from memory** and were corrected to their commit times.

## Limits

4 of 20 trajectories; ROCm 7.2.4, not 7.13; M1p is patched HEAD, not vendor code; M1s is a best-effort reconstruction because the shipped scripts are SCALE-era
and the entry's descriptor says native HIP; the Strix build needs `--dangerously-allow-unresolved-kernel-lookups` (92 kernel sites fall back), and its own script says
to read the kernel audit before quoting a Strix number as final. M0 is the reference (no speculation); llama.cpp build `daef7b6`, not the validated `cfff1fc`. One run per
arm. The MLPerf 1,007-turn workload was not run in full, so the published entry is neither confirmed nor refuted, only not reproduced on this subset and stack.
