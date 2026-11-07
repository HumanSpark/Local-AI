# File: e151-results.md
# Purpose: Results for E151 - with Atlas's prefix cache off, the DFlash drafter accepts a little past 8K context instead of nothing; the cache is a minor contributor, not the cause. The Atlas DFlash investigation stops here.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: Scored against results/e151-prereg.md. One window 13:29-14:09, one arm, capped at 2,400 s as declared: 31 of
# 206 turns (each turn re-prefilled its whole context, 3.4x M3p's time per turn). On the same 31 turns, later turns at
# 4-8K accepted 0.346 per step against M3p's 0.338; past 8K they accepted 0.04-0.07 where M3p accepted exactly 0. The
# first-turn control held (2.238 against 2.429). P1 and P2 falsified, P3, P4, P5 held. By E150's and E151's decision
# rules, the remaining candidate is the HIP kernel path and this project does not pursue it. Scorer
# tools/score_capped_atlas_arm.py, output results/raw/e151/score.txt. Registered as F178.

# E151 RESULTS - the prefix cache is not the cause; Atlas DFlash on this box is left unexplained and unusable (2026-09-26)

## What ran

M6 = E148's M3p with one change: `--enable-prefix-caching` removed. G1 held (pinned drafter bytes). G2 held: `Prefix caching:
disabled`; the drafter-loaded line as M3p's. G3: kernel 7.0.0-31, Livepatch nothing-to-apply, GTT 66 GiB before the window,
5 spark-infer processes resident; memory guard did not fire; 0 amdgpu fault lines. Harness killed at 2,400 s as declared after 31
turns (TTFT averaged 57.6 s: every turn re-prefilled up to 28K tokens); window closed 14:09:47.

## Result: a nudge past 8K, nothing else

Acceptance per 15-draft step, split by turn position, **both arms on the same first 31 turns**:

| | first turns, 0-4K | later turns, 4-8K | later turns, 8-12K | later turns, 12K+ |
|---|---|---|---|---|
| M3p (cache on) | 2.429 (21 steps) | 0.338 (80) | **0.000** (142) | **0.000** (349) |
| **M6 (cache off)** | 2.238 (21) | 0.346 (81) | **0.068** (133) | **0.039** (337) |

Overall 0.179 per step over 574 steps (M3p on its whole run 0.064). Server-side, same 31 turns: tokens per step 1.267 against
1.177, first-draft acceptance 0.132 against 0.074, decode 4.90 against 4.62 tok/s, time per turn **74,544 ms against 21,696**
(ratio 3.436, the re-prefill), output token counts identical on 31 of 31 turns.

So the cache does take something from the drafter past 8K: with it, exactly zero of 491 steps accepted a token; without it, 1 in
20 steps accepted one. That is a contributor of the order of 0.05 tokens per step, against a first-turn level of 2.2 and
llama.cpp's 0.74 of 4 drafts on the same lineage. It is not the cause.

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | later turns, 4,096-8,191 | >= 0.8 | 0.346 (M3p same turns 0.338) | FALSIFIED |
| P2 | later turns, 8,192+ | >= 0.5 | 0.068 / 0.039 (M3p 0.000 / 0.000) | FALSIFIED |
| P3 | first turns, 0-4K (control) | 2.0-2.6 | 2.238 | HELD |
| P4 | cap fires | yes | fired at 2,400 s, 31 turns | HELD |
| P5 | server-side time vs M3p, same turns | 1.5-4.0x | 3.436x | HELD |

Decision, per the prereg: **P1 and P2 falsified with P3 held: the cache is not the cause; the remaining candidate is the HIP
kernel path, which this project does not pursue.**

## Where this leaves Atlas DFlash on this box

Four arms, four single changes, one curve. The drafter accepts about 2.2 of 15 drafts per step while the context is under 4K and
collapses as context grows, and neither its attention pattern (E149), nor how much prefix it may see (E150), nor the prefix cache
(E151, a 0.05 effect) moves that. Atlas's MTP mode (9,307 ms per turn) remains its only usable speculative mode here, and it is
behind llama.cpp with a drafter of the same lineage (7,775 ms, F172). The vendor's own explanation of its low DFlash acceptance
(the context cap, from_weights.rs) was tested and does not hold on this hardware; whether the HIP port of the DFlash kernels is
where the acceptance goes is a question for the vendor, with these four logs as the report.

## Limits

31 of 206 turns, server-side timing, one run; the M3p comparison is restricted to the same 31 turns, so its 8K+ zeros are over
491 steps, not the whole run's 3,261.
