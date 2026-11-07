# E37 RESULTS: MoE concurrency is stream-diversity-bound - F17's headline is a same-question artifact (2026-07-17)

# File: results/moe-diversity.md
# Purpose: The controls that settled F43's mechanism. Pre-registration: moe-diversity-prereg.md.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: CONFIRMED and MoE-specific. When 16 concurrent streams ask DIFFERENT questions, the
# workhorse's aggregate throughput falls 40% versus 16 streams asking the SAME question (181.28 ->
# 108.86 t/s), length and content class held constant. A DENSE model shows NO such penalty (-0.1%),
# which identifies expert routing as the mechanism. Consequence: F17's headline 193.5 t/s overstates
# real fleet throughput by 1.78x, because every stream in that benchmark asked the same question.
# F43's original framing ("output diversity") was itself confounded and is corrected here.

## Conditions

llama.cpp v200 (067de93), `-fa auto -ctk f16 -ctv f16`, 4096 ctx/slot, 128-token requests, one driver
for every arm. **All prompts padded to the same 144-word class** and `predicted_n` verified at exactly
128 (min = max = 128) in every arm - so neither prompt length nor early-EOS can explain any result
below. Gateway paused, attended, D-state 0 throughout, box restored exactly (GTT 20.21 GiB).

## The result

### Length-matched, MoE workhorse, 16 slots

| Prompt class | Streams | agg t/s | per-stream t/s |
|---|---|---|---|
| fox filler (repetitive) | identical | 191.70 | 14.54 |
| legal prose | identical | 181.28 | 13.64 |
| legal prose | **DISTINCT (16 topics)** | **108.86** | **7.79** |

- **Content costs ~5%** (191.70 -> 181.28): repetitive filler vs real prose, streams identical.
- **Stream diversity costs 40%** (181.28 -> 108.86): same content class, same length, same token
  budget - the only change is that the sixteen streams ask sixteen DIFFERENT questions.

### The honest user curve (same driver, same 45s window as the published fox curve)

| Concurrent users | SAME question (what F17 published) | **DIFFERENT questions (real load)** |
|---|---|---|
| 1 | 72.78 | 71.59 |
| 4 | 138.93 | **121.35** |
| 16 | 192.19 | **109.40** |
| scaling 1->16 | **2.66x** | **1.53x** |

**Sixteen real users is SLOWER than four.** The published curve rises to 16 slots ("no sharp knee,
still rising" - F17); the real-load curve **peaks at ~4 users and declines**. The 4-user figure
reproduced across two independent runs (121.35 and 121.09, 0.2% apart), so the knee is not noise.

This is the client-facing consequence: the box's best serving point is about FOUR concurrent users,
which is exactly the "small team of 3-5" the report claims - but that conclusion was previously
extrapolated from same-question data that happened to keep rising. It is now measured, and the number
attached to it (2.66x) was wrong for the scenario it described.

### The dense control - this is what identifies the mechanism

Same test, 4 slots, length matched:

| Model | identical streams | DISTINCT streams | diversity penalty |
|---|---|---|---|
| **MoE** Qwen3-30B-A3B | 43.91 t/s/stream | 38.77 t/s/stream | **-11.7%** |
| **DENSE** Mistral-24B | 10.04 t/s/stream | 10.03 t/s/stream | **-0.1%** |

A dense model reads ALL its weights for every token regardless of what else is in the batch, so batch
composition cannot change its memory traffic - and it doesn't, to within 0.1%. The MoE routes per
token, so a batch of divergent streams must fetch many experts per step. **The penalty exists only
where expert routing exists.** That is the mechanism, established by control rather than argument.

### The penalty scales with batch size

| Slots | MoE identical | MoE distinct | penalty |
|---|---|---|---|
| 4 | 43.91 | 38.77 | -11.7% |
| 16 | 13.64 | 7.79 | **-43%** |

More streams means more opportunity to diverge, so more experts per step - which is what
expert-sharing predicts and is further evidence for it. The effect is not a fixed tax; it grows with
exactly the concurrency that fleet serving implies.

## Prediction resolution

| ID | Prediction | Result | Verdict |
|---|---|---|---|
| A1 | Dense shows NO prompt/diversity effect (ratio 1.00 ±0.05) | 10.04 vs 10.03 = **1.001** | **HIT** |
| A2 | MoE shows the effect at the same slot count (ratio >= 1.15) | 1.133 at 4 slots | **MARGINAL MISS** |
| B1 | Identical streams reproduce E36 (~185-195 agg) | 191.70 | **HIT** |
| B2 | Diverse streams <= 170 agg (>=10% penalty) | **108.86** (-40%) | **HIT, and far beyond** |

**A2's marginal miss is informative, not cosmetic.** The prediction assumed a roughly fixed effect
size and named 4 slots; the measured 1.133 is just under the 1.15 line. But at 16 slots the same
comparison gives 1.75x. The prediction was wrong about the SHAPE - the penalty scales with batch size
rather than being a constant - and that scaling is itself the strongest support for the batch-sharing
mechanism. Recorded as a miss rather than quietly re-baselined to the slot count that would have hit.

## What this corrects

**F43 as originally written is wrong in its framing and is corrected here.** It said "MoE throughput
depends on OUTPUT DIVERSITY", inferred from a 26% gap between two prompts (192.19 vs 152.12). That
comparison was itself confounded: the two prompts differed in LENGTH (144 vs 45 words) as well as
content. With length controlled, prompt content is worth only ~5%; nearly all of the real effect is
STREAM diversity - whether the concurrent requests differ from each other, not whether any one of them
is interesting. The corrected claim is narrower, better evidenced, and more consequential.

**F17's headline is a same-question artifact.** F17 reports the workhorse at 193.5 t/s aggregate over
16 slots and frames it, in its own words, as "what the fleet gets at burst". Every stream in that
benchmark ran the same repetitive prompt. Sixteen real users asking sixteen different questions
measure **108.86 t/s** on the same box, same build, same slot count:

> **F17 headline: 193.5 t/s. Real fleet load: 108.86 t/s. Overstatement: 1.78x.**

F17's number is not fabricated - its conditions are stated, and it reproduces exactly (E36 measured
192.19 under those conditions). It is a best case that reads as a fleet number. The honest figure for
"sixteen colleagues hitting the box at once" is roughly half the published one.

Note this cuts the other way for the single user, who is unaffected: at 1 slot there is no penalty at
all (89.02 vs 89.94 t/s across prompts - E36). The finding is about fleets, not people.

## Why the same-question benchmark is the trap

Every concurrency benchmark that fires one prompt from N threads measures the best case for a MoE and
does not know it. The batch shares expert loads because the streams agree; real load does not agree.
This is not a llama.cpp quirk or a sparkbench harness bug - `serve_bench.py` does exactly what
standard practice does, and F17's method section is accurate about it. The lesson generalises:
**for MoE architectures, concurrency benchmarks must use DISTINCT prompts per stream or they measure
expert-cache locality rather than serving capacity.** Dense models are immune, which is why the
practice survived unexamined - it was correct for the architectures it was invented on.

## Operational miss, recorded

The final arm (the distinct-user curve) stopped `llama-gateway.service` and, unlike the earlier arms,
did not restart it - the script ended with `pkill -x llama-server` only. **Production was down for
about 7 minutes** (journal: stopped 06:24:03, started 06:31:07) before the closing health check caught
it. No harm done on a single-operator box at 06:24 local, but it was luck rather than design: any LAN
caller would have seen connection-refused, and nothing in the run would have told me.

The fix is the pattern the project already uses elsewhere and this script did not: `trap restore EXIT`
(as in tools/run_finetune_eval.sh), so the gateway is restored even if the run dies, errors, or is
interrupted. Recorded because "I remembered to restart it the other three times" is not a control.

## Limits

Two models (one MoE, one dense), one MoE family, 4 and 16 slots, one diversity condition (16 distinct
topics vs identical). Not tested: intermediate diversity (how many distinct streams before the penalty
saturates?); other MoE families (gpt-oss-20b, GLM-4.7-Flash - F17/F18 show their concurrency behaviour
already differs by architecture, so the diversity penalty may too); whether the penalty interacts with
F18's MLA anti-scaling; the effect above 16 slots.

Evidence: this file; pre-registration results/moe-diversity-prereg.md (committed a02f09b BEFORE any
run); E36 results/router-concurrency.md (where the signal appeared); F17 (the number corrected);
F41 (the bandwidth ceiling that makes expert traffic the binding constraint); F18 (architecture-
dependent concurrency, the reason to expect this to vary by MoE family).
