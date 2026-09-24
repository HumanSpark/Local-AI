# E35 PRE-REGISTRATION: router load/unload + concurrent inference (2026-07-17)

# File: results/router-loadtest-prereg.md
# Purpose: Predictions registered BEFORE the E35 runs - the three things F40 listed as untested.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: F40 established that two models sit resident at 41.04 GiB and switch in 0.04s, but
# explicitly did NOT test: eviction under --models-max pressure, explicit unload, concurrent
# inference against both models, or sustained residency. This registers falsifiable predictions for
# all four BEFORE any run (house rule: pre-register, deviations are findings). Results land in
# results/router-loadtest.md; this file is not edited after the first run except by declared amendment.

## What is being tested

The four items F40 listed as unknown. Each gets a prediction that can be wrong.

## Safety design (the constraint: do not wedge the box)

The ~60 GiB memory edge (F24) needs a physical power cycle to clear. Every arm is bounded below it:

- **Eviction arm** runs at `c = 16384` (not 49152) and uses **Qwen3-4B-Instruct-2507-Q4_K_M (2.50 GB)**
  as the third model. Worst case - if the router loads BEFORE evicting - the transient peak is
  workhorse + Mistral + 4B ≈ 33 GiB of weights plus small KV. Far under the edge even in the bad case.
  This is deliberate: the arm exists to discover whether load-then-evict happens, so it must be safe
  if it does.
- **Concurrency arm** reuses F40's exact resident pair at production `c = 49152` (41.04 GiB measured),
  adding no new weights - only concurrent requests.
- Gateway paused throughout (rule 3), KV always bounded (rule 4), disk quiet (rule 1), attended,
  D-state polled at every step. `--models-preset` only, never `--models-dir` (F40's safety property).

## Predictions

### A. Eviction under `--models-max 2`

With workhorse + Mistral resident (at cap), request a third model.

- **A1. The router evicts before loading** (evict-then-load), so GTT never holds three models at once.
  *Rationale:* `--models-max` exists to bound memory; loading first would defeat it. **This is the
  safety-relevant one** - if A1 is FALSE, then on a box like this `--models-max` does NOT bound peak
  memory, and a 3rd large model could transit the edge. That would be a finding worth publishing.
- **A2. Eviction is LRU** - the workhorse (least recently used at that point) is dropped, not Mistral.
  *Confidence: low.* Could equally be FIFO or first-loaded.
- **A3. Evicted memory is fully released** - GTT after settling ≈ (Mistral + 4B), not the 3-model sum.
- **A4. No deadlock, D-state stays 0.** Nothing here approaches the edge.

### B. Explicit unload (`POST /models/unload`)

- **B1. Unload returns GTT to the router-idle baseline (~0.02 GiB)** when all models are unloaded -
  i.e. memory is released to the system, not merely marked free inside the process.
- **B2. A subsequent request to the unloaded model reloads it on demand** (autoload), costing the
  same ~4s cold load F40 measured, not an error.

### C. Concurrent inference - the interesting one

Fire requests at BOTH resident models simultaneously and compare each to its solo throughput.

The physical claim: **both models are memory-BANDWIDTH bound, not compute bound.** Evidence it is
bandwidth: Qwen3-30B-A3B activates ~3B params/token (~1.7 GB read at Q4) and runs 92.28 t/s -> ~156
GB/s. Mistral-24B is dense, ~24B params/token (~13.4 GB at Q4) at 15.07 t/s -> ~201 GB/s. Two very
different models landing within ~30% of the same GB/s is the signature of a shared bus ceiling, and it
also explains the whole MoE speed advantage (F34's "5-8x slower" is a bandwidth ratio, not a mystery).

If that is right, two models sharing one bus must divide one budget:

- **C1. Normalised throughput sums to ~1.0:** `(w_concurrent / 92.28) + (m_concurrent / 15.07) ≈ 1.0`,
  tolerance ±0.3. This is the core prediction and the one most able to be wrong.
  - If the sum is **~1.0** -> confirmed bandwidth-bound; concurrency redistributes a fixed budget and
    buys nothing in aggregate.
  - If **> 1.3** -> there is real headroom (bandwidth not saturated solo, or useful interleaving while
    one model stalls). Concurrency would then be worth something, and the bandwidth story is wrong.
  - If **< 0.7** -> contention costs MORE than the bandwidth model predicts (context-switch or
    scheduler overhead between two GPU processes). Concurrency would be actively harmful.
- **C2. Neither model errors or times out** under concurrent load.
- **C3. D-state stays 0** - 41.04 GiB is not memory pressure, and F24's trigger is pressure, not load.
- **C4. Latency roughly doubles** for each model versus solo (the corollary of C1).

### D. Sustained residency

- **D1. GTT is flat** across repeated alternating requests over several minutes - no creep, no leak.
- **D2. Switching stays ~0.04s** and does not degrade with repetition (no silent reload).

## Decision rule (what the results would change)

- A1 FALSE -> `--models-max` does not bound peak memory on this box; router adoption would need a
  hard external cap, and this becomes a safety finding, not a footnote.
- C1 ~1.0 -> concurrency is a scheduling convenience, NOT a throughput gain; the routing guide should
  say so plainly (you do not get two models' work for one box's price).
- C1 > 1.3 -> concurrent serving is genuinely useful and the guide's advice changes materially.
- Any D-state > 0 -> stop, snapshot, report; do not retry (rule 6).

Evidence will be recorded in results/router-loadtest.md with the same GTT/D-state instrumentation
F40 used, and every prediction resolved explicitly as HIT / MISS / AMBIGUOUS.
