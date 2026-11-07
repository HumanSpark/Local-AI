# File: e147-results.md
# Purpose: Results for E147 - llama.cpp with a speculative drafter on the MLPerf edge-agentic metric, the like-for-like arm E146 lacked.
# Project: sparkbench | Date: 2026-09-25
#
# Overview: Scored against results/e147-prereg.md. One window 09:35-10:02 (1,632 s), one arm, 206 turns, 0 failures,
# 0 amdgpu fault lines, all three gates passed. With a drafter, llama.cpp takes about 40% less time per turn than the
# MLPerf reference and about 17-18% less than either Atlas build, at accuracy identical to the reference. Scorer
# tools/score_e146.py (E147 section), output results/raw/e147/score.txt. Registered as F172.

# E147 RESULTS - with a drafter, the open configuration beats Atlas on the MLPerf metric (2026-09-25)

## The arm and its comparators (same 206 turns, paired by conversation and turn)

| arm | what | mean latency per turn | median | p95 | TTFT median | accuracy | vs M0 |
|---|---|---|---|---|---|---|---|
| M0 (E146) | llama.cpp reference, no speculation | 12,863 ms | 8,704 | 33,553 | 4,479 | 0.637 | 1.000 |
| M1p (E146) | Atlas HEAD plus a one-line patch, MTP K=3 | 9,307 ms | 6,358 | 25,133 | 3,432 | 0.622 | 0.724 |
| M1s (E146) | the MLPerf entry's shipped source, MTP K=3 | 9,453 ms | 6,673 | 23,917 | 3,656 | 0.606 | 0.735 |
| **M2** | llama.cpp reference flags + Qwen3.6-27B DFlash drafter, n=4 | **7,775 ms** | 5,790 | 15,720 | 3,070 | **0.637** | **0.604** |

- **M2 against the reference:** paired ratio 0.604, thirds 0.741 / 0.548 / 0.554. Accuracy 0.637 against 0.637: identical to
  three decimals, as F84 says greedy speculation should leave it.
- **Atlas against M2:** M1p/M2 = **1.197** (thirds 1.01 / 1.31 / 1.28), M1s/M2 = **1.216** (1.07 / 1.25 / 1.33). Both above the
  registered 1.15 line in every third but the first. Band: **open configuration faster**.
- **The published Strix Halo latency (7,059 ms) is inside the +/-25% band for M2** (7,775 ms, 1.10x). Neither Atlas build reached
  that band on this box; the open configuration with a drafter did.
- Gates: G1 drafter size and sha256 matched the pin; G2 probe 14 of 19 drafts accepted at 14.6 tok/s; G3 kernel 7.0.0-31,
  Chatterbox resident, GTT 67 GiB before the window. Full offload: 142 layers including the drafter, 0 on CPU.

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `M2.turns_ok` | 206 | 206 | HELD |
| P2 | `M2.mean_turn_latency_ms` | 7,500-10,500 | 7,775 | HELD |
| P3 | `M2/M0` paired ratio | 0.55-0.85 | 0.604 | HELD |
| P4 | `M2.accuracy` within 0.03 of M0 | yes | 0.000 difference | HELD |
| P5 | `M1p/M2` paired ratio | 0.85-1.20 | 1.197 | HELD (at the top of the range) |
| P6 | `M2.draft_acceptance` | 0.55-0.85 | not recorded per turn (this build's server log carries no acceptance lines; the 20-token probe accepted 14 of 19 drafts, 0.737) | UNSCORED (no per-turn record) |

## What this settles and what it does not

F169's claim stands: Atlas is about 27% faster than MLPerf's reference implementation. What E147 adds is that the reference is
not the best open configuration. Give llama.cpp a drafter, with no other change to the reference flags, and it takes about 40%
less time per turn than the reference and about 17% less than Atlas, at the reference's own accuracy. Atlas's advantage in
E146 was an advantage over an engine running without the speculation Atlas itself uses.

Limits: 4 of 20 trajectories, one run per arm; the drafter is a community GGUF conversion of z-lab's DFlash head, chosen because
it exists, not tuned; Atlas's own DFlash mode (its serve script supports one) was not run, and would be the next like-for-like
step on the Atlas side. ROCm 7.2.4 throughout. M0 was not re-run in this window (same build, host and kernel; declared in the prereg).
