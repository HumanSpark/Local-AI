<!--
# File: e161-results.md
# Purpose: Results of E161 - do MoE expert "helpers" (CPU cores, tandem.cpp's hot-expert cache) speed up Flash-Next on
# one unified-memory box, and how concentrated is expert routing on our real work?
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Scored against results/e161-prereg.md (P0-P8, amendments 1-2). Speed records results/e161/speed-<arm>.json
# (tools/e153_speed.py); skew fields results/e161/skew.json (tools/e161_skew.py over llama-imatrix GGUFs, which are
# 1.1 GB each and kept on disk, gitignored). Window log results/e161/window.log. Finding F188.
-->

# E161 RESULTS - expert helpers do not pay on unified memory; routing is concentrated but workload-specific (2026-11-15)

## In plain English

Tandem speeds up big "mixture of experts" models on PCs with graphics cards. It caches the busiest experts in the
card's fast memory and has a helper compute the rest. We tried every version of that idea we could run on this
machine.

None was faster than leaving the whole model on the graphics side. Moving experts to the CPU cost 10% to 32% of
generation speed, depending on how many moved. tandem.cpp's own cache, sized by hand, came out 16% slower than the
same engine without it. Its automatic setting never switched the cache on: it looked for dedicated graphics memory,
which this machine does not have.

The second half asked whether a few experts do most of the work. They do: the busiest fifth handle about 70% of
routing, far more than the 20% an even split would give. But the busy set changes with the job. Code uses a different
set from documents and prose; documents and prose share theirs. A model that keeps only its busy experts at high
precision would therefore have to be tuned to a kind of work. That is a narrower idea than the one we planned to test
next, so we did not start it.

## Speed (Qwen3.8-Flash-Next UD-IQ4_XS, E153 prompts, greedy, thinking off, one stream)

| arm | engine | routed experts | CODE decode tok/s | vs own baseline | P8K prefill tok/s |
|---|---|---|---|---|---|
| M0 | llama.cpp e574a17 Vulkan | all on GPU | 27.74 | 1.00 | 373.9 |
| M4 | same | first 4 of 48 layers on CPU | 24.82 | 0.89 | 360.7 |
| M12 | same | 12 layers on CPU | 21.65 | 0.78 | 342.1 |
| M24 | same | 24 layers on CPU | 18.93 | 0.68 | 323.5 |
| T0 | tandem.cpp 8fba592 HIP | all on GPU | 25.16 | 1.00 | 494.3 |
| T1 | same | `-cmoe`, cache `auto` (disabled itself) | 12.10 | 0.48 | 328.0 |
| T2 | same | `-cmoe`, 24 GiB hot-expert cache (amendment 2) | 21.09 | 0.84 | 111.6 |

PROSE and JSON decode match CODE to within 0.1 tok/s on every arm except T2 (PROSE 22.84, JSON 22.65). Zero thinking
leaks on every arm, and every arm answered all 14 requests. During M24 decode the server ran at 878% CPU, so the CPU
arms really did compute experts on the CPU.

T1 and T2 are compared with T0 only: HIP against Vulkan is its own variable. Unattributed side observation: the T build
reads prompts about 1.3x faster than mainline Vulkan (494 against 374 tok/s at 8K). That could be the HIP backend or
the tandem patch; nothing here separates the two.

**T2 nearly exhausted memory.** Its minimum MemAvailable was 0.66 GiB, against 23.9-27.3 GiB on the other arms. With
`-cmoe` the experts stay in host memory and the cache copies them a second time into the same physical pool. On this
box that duplication is the memory edge (docs/memory-edge-deadlock.md), and a larger cache could take the machine down.

## Skew (llama-imatrix routing counts, 48 layers x 512 experts, medians over layers)

| corpus | tokens | top 20% of experts take | top 10% take | experts never routed |
|---|---|---|---|---|
| code (E159 agent transcripts) | 61,440 | 0.704 (0.48-0.86) | 0.510 | 5 |
| docs (kw-eval lab documents) | 61,440 | 0.675 (0.43-0.86) | 0.444 | 10 |
| prose (E160 answers, amendment 1) | 17,920 | 0.682 (0.46-0.84) | 0.459 | 32 |

Overlap of the top-20% sets (Jaccard; two random sets would give about 0.11):

| pair | median (min-max) |
|---|---|
| code - docs | 0.193 (0.10-0.38) |
| code - prose | 0.176 (0.06-0.29) |
| docs - prose | 0.700 (0.59-0.84) |

Limitation (declared in the prereg): imatrix routes the corpus as prompt tokens; decode routing over generated tokens
is not measured. Prose's higher dead count is partly its smaller sample.

## Predictions

| | prediction | verdict |
|---|---|---|
| P0 | M0 CODE decode within ±15% of E153 L0's 27.06 | HELD (27.74, +2.5%) |
| P1 | every CPU arm slower than M0 on CODE | HELD |
| P2 | M0 > M4 > M12 > M24 | HELD |
| P3 | M24 <= 0.6 x M0 | **FAILED** (0.68x: the CPU cost was milder than predicted) |
| P4 | M24 P8K prefill <= 0.5 x M0 | **FAILED** (0.87x) |
| P5 | T1 <= 1.05 x T0 | HELD, but the cache never engaged (amendment 2) |
| P5b | T2 <= 1.05 x T0 | HELD (21.09 v 25.16 = 0.84x) |
| P5c | T2 > T1 | HELD (21.09 v 12.10) |
| P6 | tandem.cpp builds and serves on gfx1151 | HELD (T0 14/14) |
| P7 | median cov20 (code) in [0.30, 0.55] | **FAILED** (0.704: routing is more concentrated than predicted) |
| P8 | median jaccard_top20(code, docs) < 0.5 | HELD (0.193) |

P4 likely failed because llama.cpp moves CPU-resident expert weights to the GPU for large prompt batches, and on
unified memory that move is cheap. That is a hypothesis; it was not measured.

## Decision (the prereg's rule)

- **CPU and tandem-style expert helpers do not pay on this box.** Every helper arm was slower than its own all-on-GPU
  baseline. The CPU-helper question is closed for Flash-Next on this machine.
- **E162 (mixed precision by hotness) is not proposed as written.** Concentration clears the bar (cov20 >= 0.60 on
  every corpus), but the hot sets do not carry across workloads (code pairs 0.18-0.19, under the 0.5 bar).
- **New hypothesis, not tested:** docs and prose share hot sets (0.70), so a precision-by-hotness build tuned for text
  work might hold. Any test would need the decode-routing measurement this experiment lacked, and it would need to be
  run on DeepSeek-V4.1-Flash, where memory capacity actually binds.

## Evidence files

Speed: `results/e161/speed-M0.json`, `results/e161/speed-M4.json`, `results/e161/speed-M12.json`, `results/e161/speed-M24.json`, `results/e161/speed-T0.json`, `results/e161/speed-T1.json`, `results/e161/speed-T2.json`. Skew: `results/e161/skew.json`. Window: `results/e161/window.log`, `results/e161/run.out`,
`results/e161/run-T2.out`. Builds: `results/e161/build-mainline.log`, `results/e161/build-tandem.log`.

## Run notes

- Window 1 03:19-04:18Z (skew, M0-M24, T0, T1). Window 2 04:18-04:29Z (T2). Production was verified restored after each
  by `halogen_effort_check.py` (LOW DEFAULT LIVE), about 70 minutes down in total.
- Kernel `7.0.0-42-generic`. The Livepatch field came back empty (the status call printed no "patch state" line), so
  Livepatch state is unrecorded for this run.
- Amendment 1 (before any run): prose adds E160 KX's answers and runs at its own 35 chunks.
- Amendment 2 (after T1, before T2): T1's cache had disabled itself, so the exploratory T2 arm was added.
