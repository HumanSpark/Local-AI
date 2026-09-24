# E35 RESULTS: router load/unload + concurrent inference (2026-07-17)

# File: results/router-loadtest.md
# Purpose: Results for the four items F40 left untested. Pre-registration: router-loadtest-prereg.md.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: All predictions resolved. Headline: eviction is safe (--models-max DOES bound peak memory),
# unload is clean, residency is leak-free - but CONCURRENT inference is bandwidth-bound and brutally
# UNFAIR: running dense Mistral alongside the MoE workhorse costs the workhorse 81% of its speed while
# Mistral loses 14%. The router is a fast SWITCH, not a way to get two models' work from one box.
# Methodology note: the first concurrency measurement said 1.37 (prediction MISS) and was a
# partial-overlap artifact; measuring per-token timestamps inside the provable overlap window gave
# 1.05 (HIT). The artifact, not the number, is the transferable lesson.

## Conditions

llama.cpp v200 (067de93), router mode, `--models-preset` only, `--models-max 2`, gateway paused,
attended, disk quiet. Arm A at `c = 16384` with a 2.50 GB third model (deliberately safe if the
risky prediction failed); arms C/D at production `c = 49152`, 4 slots. D-state polled at every step:
**0 throughout**. Box restored to its exact pre-test state (GTT 20.21 GiB, D-state 0).

## Prediction resolution

| ID | Prediction | Result | Verdict |
|---|---|---|---|
| A1 | Router evicts BEFORE loading (models-max bounds peak memory) | Peak GTT 32.71 GiB = the existing 2-model level; never held 3 | **HIT** |
| A2 | Eviction is LRU (drops the workhorse) | workhorse evicted; Mistral + 4B retained | **HIT** |
| A3 | Evicted memory fully released | 32.71 -> 18.66 GiB (Mistral + 4B) | **HIT** |
| A4 | No deadlock, D-state 0 | D-state 0 | **HIT** |
| B1 | Unload returns GTT to idle | 18.66 -> **0.02 GiB** after unloading both | **HIT** |
| B2 | Unloaded model reloads on demand | workhorse answered 3.3s after being unloaded | **HIT** |
| C1 | `(w_con/w_solo) + (m_con/m_solo) ≈ 1.0 ±0.3` | **1.05** (in-overlap) | **HIT** |
| C2 | No errors/timeouts under concurrent load | none | **HIT** |
| C3 | D-state 0 under concurrent load | 0 | **HIT** |
| C4 | Latency roughly doubles for each model | **MISS - wildly asymmetric**, see below | **MISS** |
| D1 | GTT flat, no leak | 41.05 GiB across 20 switches, drift **0.000 GiB** | **HIT** |
| D2 | Switching stays ~fast, no silent reload | workhorse median 42ms, Mistral median 535ms, stable | **HIT** |

## A/B: loading, eviction, unloading

```
idle                        0.02 GiB   all unloaded
workhorse loaded           17.18 GiB
+ mistral (AT CAP)         32.71 GiB
+ qwen3-4b (3rd, over cap) 18.66 GiB   <- workhorse EVICTED; peak never exceeded 32.71
unload mistral + 4b         0.02 GiB   <- fully released to the system
```

**A1 is the safety-relevant result and it passed:** `--models-max 2` evicts before loading, so peak
memory is bounded by the cap, not by the cap plus the incoming model. Sampled GTT every 50ms across
the third load and the maximum equalled the pre-existing 2-model level - there is no transient
three-model window. This is what makes `--models-max 2` a real guard against the ~60 GiB edge (F24)
rather than a soft hint. Eviction is LRU, and `POST /models/unload` returns memory to the system
(0.02 GiB), not merely to a free-list inside the process.

## C: concurrent inference - the finding

Solo baselines and concurrent rates, streamed identically (same harness, same prompt, per-token
timestamps - the only honest way to compare):

| | Solo | Concurrent (in-overlap) | Retained |
|---|---|---|---|
| Qwen3-30B-A3B (MoE, ~3B active/token) | 91.37 t/s | **17.28 t/s** | **18.9%** |
| Mistral-24B-Q4 (dense, ~24B/token) | 15.24 t/s | **13.13 t/s** | **86.1%** |
| | | **normalised sum** | **1.05** |

**C1 HIT: the box is memory-bandwidth bound, and concurrency redistributes a fixed budget.** The
normalised fractions sum to ~1.0, which is what a single shared bus predicts. You do not get two
models' work for one box's price; you get approximately one box's work, split.

**C4 MISS, and this is the decision-grade part: the split is not fair - it is 4.6:1 against the fast
model.** The prediction assumed both would degrade about equally (~2x latency each). Instead the MoE
workhorse lost **81%** of its throughput while dense Mistral lost **14%**. The mechanism follows from
the bandwidth model: Mistral reads ~13.4 GB per token and the workhorse ~1.7 GB, so Mistral's demand
dominates the bus. The workhorse's entire advantage IS bandwidth efficiency, so competition destroys
precisely the thing that makes it fast, while barely inconveniencing the model that is already
bandwidth-hungry. **Running a dense model concurrently guts the MoE.**

Corollary worth keeping: this is more evidence that F34's "Mistral is 5-8x slower" is a bandwidth
ratio, not a mystery - the same arithmetic predicts both the solo speeds and the contended split.

## D: sustained residency

20 alternating switches at production context: GTT **41.05 GiB, drift 0.000 GiB**. Workhorse median
latency 42ms, Mistral 535ms, both flat from first cycle to last - no creep, no silent reload, no leak.
(Mistral's 535ms vs the workhorse's 42ms for an 8-token reply is the dense/MoE prefill+generation gap,
not a switching cost.)

## Methodology: the artifact that nearly produced a false MISS

The first concurrency run measured each request's own wall-clock average and reported a normalised sum
of **1.37** - outside the ±0.3 band, i.e. "prediction MISS, real headroom exists, the bandwidth story
is wrong". It was an artifact. The two jobs were sized 600 and 100 tokens, so Mistral finished at 7.7s
while the workhorse ran to 13.0s: **the workhorse spent its last 5.3s running ALONE at full speed**,
and that solo tail was averaged into its "concurrent" rate. Overlap was only 59%.

The fix was to record a timestamp per streamed token and compute each model's rate strictly inside the
mutual overlap window (both provably generating). That gives 17.28 t/s and a sum of **1.05** - a HIT,
and a different conclusion. Note the arithmetic check done before re-running: if the tail ran at solo
speed, the contended rate had to be ~15.3 t/s and the sum ~1.04 - which predicted the measured 17.28 /
1.05 closely, so the artifact was diagnosed before the second run rather than discovered by it.

The transferable rule: **a throughput number measured over a window that includes non-contended time
is not a contention measurement.** Same family as F34's judge-truncation and letterhead-leakage
artifacts, and as this week's `--jinja` retraction - the ruler, not the data, was wrong. Reported here
because "we predicted 1.0, measured 1.37, so we were wrong" would have been the easy write-up, and the
false MISS would have argued for adopting concurrency on the strength of headroom that does not exist.

## What this means operationally

- **The router is a fast SWITCH, not a concurrency engine.** Its value is 0.04s model changes, on-demand
  loading, and per-model config - not parallel serving. For a single-operator box that is the right
  shape anyway: you are one person, you use one model at a time.
- **Never serve the MoE and a dense model concurrently on purpose.** The workhorse drops to 17 t/s -
  slower than Mistral running alone. If concurrent load is expected (two LAN callers, an agent plus a
  human), the sane configurations are one model, or two models of similar bandwidth appetite.
- **`--models-max 2` is a real cap** (A1), which makes preset-only + models-max 2 a defensible
  production configuration from the memory-safety side.
- Residency is free: 41.05 GiB held flat indefinitely with zero drift, and unload reclaims fully, so
  there is no cost to keeping both resident for switching.

## Still not tested

Multi-slot concurrency WITHIN one model under the router (F17's knee measured a single llama-server;
whether the router changes it is unknown); `--sleep-idle-seconds` behaviour; >2 models with small
models only; router stability over days rather than minutes; whether tool use survives multi-round
chains on Mistral (E33's chain confound, still unresolved).

Evidence: this file; pre-registration results/router-loadtest-prereg.md (committed deef627 BEFORE any
run); F40 / results/router-multimodel.md (the residency baseline these arms extend); F24 /
docs/memory-edge-deadlock.md (the edge that sets models-max 2); F34 (the 5-8x dense/MoE ratio this
explains); F17 (the single-model concurrency knee, untouched here).
