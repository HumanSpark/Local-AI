# E37 PRE-REGISTRATION: is F43 batched expert-sharing? (2026-07-17)

# File: results/moe-diversity-prereg.md
# Purpose: Predictions registered BEFORE the E37 runs - the two controls that settle F43's mechanism.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: F43 (open) recorded that changing only the prompt moved the workhorse's aggregate
# concurrent throughput 26% (192.19 -> 152.12 t/s @16 slots). E36's own data already narrows the
# mechanism, and this registers the two controls that would confirm or kill it.

## What E36's data already tells us - and why it changes the hypothesis

F43 was written as "MoE throughput depends on output diversity". The 1-slot data says that is too
loose:

| Prompt | 1 slot per-stream | 16 slot per-stream |
|---|---|---|
| fox filler ("The quick brown fox..." x16) | 89.02 t/s | **14.57 t/s** |
| real legal prose | 89.94 t/s | **10.21 t/s** |
| difference | **~1% (none)** | **43%** |

**At 1 slot there is NO prompt effect. It appears only under concurrency.** So this is not "diverse
tokens are slower to generate" - a single stream generating diverse prose runs at full speed. The
effect is BATCH-level.

**Refined hypothesis: batched expert-sharing.** Qwen3-30B-A3B activates ~3B of 30B params per token
and routes per token. In E36 all 16 concurrent streams ran the SAME prompt (differing only by a
`[req tid-n]` prefix), so they generate near-identical text and route to near-identical experts. The
batch then loads one expert set to serve all 16 streams - maximal weight reuse on a bandwidth-bound
box (F41). With 16 streams generating DIFFERENT content, the batch must load many experts per step,
and bandwidth - the binding constraint - multiplies.

If true, the implication is sharper and worse than F43 as written: **F17's 193.5 t/s is a best case
not merely because the text is repetitive, but because all 16 streams are running the SAME text.**
Real fleet load is 16 different people asking 16 different things - the worst case for expert reuse.

## The two controls

### Control A - dense model (does the effect vanish without expert routing?)

Same driver, same settings, both prompts, run on DENSE Mistral-Small-24B (no experts to route) and on
the MoE workhorse, at the same slot count. Compare the WITHIN-MODEL ratio (fox / legal), not absolute
speed - the models are 6x apart and that is not the question.

- **A1. Dense Mistral shows NO prompt effect: ratio 1.00 +/- 0.05.** A dense model reads all weights
  every token regardless of content, so batch composition cannot change its memory traffic.
- **A2. The MoE workhorse DOES show the effect at the same slot count: ratio >= 1.15.**
- If A1 and A2 both hit -> the mechanism is expert routing, and F43 is confirmed as MoE-specific.
- **If A1 MISSES (dense shows it too) -> the mechanism is NOT expert routing** and F43's hypothesis is
  dead; something else (scheduler, sampling, KV layout) is responsible and would need its own hunt.

Settings: 4 slots (not 16 - Mistral at 16 slots would run ~1 t/s per stream, so 128 tokens would
exceed the request timeout), 128 gen tokens, 60s window, `-fa auto -ctk f16 -ctv f16`, 4096 ctx/slot.

### Control B - stream diversity (the one that matters for the real-world claim)

Workhorse, 16 slots, fox prompt, one difference: **all 16 streams identical vs all 16 streams
DIFFERENT** (16 distinct prompts on distinct topics). This isolates batch-level expert divergence from
prompt content entirely - same model, same slot count, same token budget.

- **B1. Identical streams reproduce E36: ~185-195 t/s aggregate.**
- **B2. Diverse streams are SLOWER: <= 170 t/s aggregate**, i.e. at least a 10% penalty purely from
  the streams not sharing experts.
- If B2 hits -> batched expert-sharing confirmed, and **the honest fleet number for this box is the
  diverse figure, not F17's 193.5**. That would make F17's headline an artifact of every stream in the
  benchmark asking the same question.
- If B2 MISSES (diverse ~= identical) -> the batch-sharing story is wrong even though the 1-slot data
  ruled out per-token cost; the effect would then live in prompt content itself and need a third
  explanation.

## Decision rule

- A1+A2+B2 all hit -> promote F43 from open to confirmed, MoE-specific, with the fleet-number
  correction stated plainly. F17 gets a caveat naming its identical-stream condition.
- A1 misses -> F43's mechanism is retracted; record the effect as real but unexplained, and do not
  attribute it to MoE routing anywhere.
- B2 misses -> keep F43 open; the mechanism is not batch sharing.

## Safety

Gateway paused (rule 3), KV bounded 4096/slot (rule 4), preset-only where the router is used, disk
quiet (rule 1), attended, D-state polled each arm. Peak is one model at a time, ~21 GiB max - far
under the ~60 GiB edge (F24). Mistral at 4 slots x 4096 = 16K context, trivial.
