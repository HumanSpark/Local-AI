<!--
# File: results/e183-results.md
# Purpose: Results of E183 - Inkling-2-Mini with the DSpark draft on stock llama.cpp, against no draft.
# Project: sparkbench | Date: 2026-11-26
#
# Overview: Scores results/e183-prereg.md (amendments A1-A3) against results/e183/raw/{N0,D3,D7}/speed-r{1,2}.json.
# Runs 2026-11-26 14:15-14:50Z, llama.cpp b671865c7 (Vulkan), kernel 7.0.0-44 (livepatch checkState: checked),
# relay restored and probe-verified 14:50:52Z. GPU shared with sparkscene by message protocol; nothing else ran.
-->

# E183 RESULTS - DSpark on stock llama.cpp

## In plain English

The small DSpark helper model does speed Inkling up on stock llama.cpp, but only a little: about 16% faster on short
answers when it guesses 3 words ahead, and no gain once the conversation is long. Letting it guess 7 words ahead makes
things slower, because most of its guesses get thrown away. That is far short of the 2-2.5x the same helper gave
through AMD Loom and the CIRU runtime (E172). So the big DSpark speed-up on this box still needs one of those
engines; plain llama.cpp is not there yet.

Two practical lessons came out on the way: unsloth's Inkling files come in two layouts, and the helper must match the
main model's layout. The helper we downloaded for E172 only works with the Loom layout. unsloth published a
llama.cpp-compatible helper three days later.

## Results (decode tok/s, client-timed; r1 / r2)

| Setup | Short answer (D1500) | After 8K (P8K) | After 32K (P32K) | Draft tokens accepted |
|---|---|---|---|---|
| N0 no draft | 28.86 / 28.85 | 27.85 / 27.86 | 24.23 / 24.21 | - |
| D3 DSpark, 3 ahead | **33.51 / 33.11** (1.16x) | 28.02 / 28.43 (1.01x) | 23.70 / 25.27 (1.01x mean) | 49% (mean run 2.47) |
| D7 DSpark, 7 ahead | 24.35 / 24.13 (0.84x) | 19.13 / 20.79 (0.72x) | 20.09 / 17.31 (0.77x) | 28% (mean run 2.97) |

Prefill tok/s (r1 only, A2): N0 344.2 / 260.6 / 355.3 (P8K / P32K / D1500); D3 343.3 / 252.2 / 338.7;
D7 337.7 / 251.5 / 334.2. Acceptance from llama-server's `draft acceptance` lines, 14 requests per arm.

Spread: N0 decode r1-r2 within 0.02; D3 D1500 within 0.40, so its +4.5 tok/s gain is real; D3 P32K spread is 1.57
(23.70 vs 25.27), wider than its gap to N0, so "no gain at 32K" is the honest reading, not "slower". D7's losses at
D1500 and P8K exceed their spreads.

## Predictions

- **P1 FALSIFIED.** Better draft arm's D1500 decode is 1.16x N0 (D3, 33.51 vs 28.86), not >= 1.5x.
- **P2 HELD.** The gain shrinks with context: 1.16x at D1500, about 1.0x at P32K.
- **P3 HELD.** N0 D1500 28.86 vs E172 IM 26.59 (+8.5%, within 10%). Same file and flags; build b671865c7 vs
  94f3af3d0. All three N0 decode fields are 7-9% faster than E172 IM: the newer build is faster.
- **P4 HELD.** Draft arms' prefill within 10% of N0 on every field (worst: D7 D1500 -5.9%).
- Declared risk (llama.cpp #23126, Vulkan draft slowdown): not the main story. D3 does gain, but acceptance (49%) is
  well below what Loom/CIRU's 2-2.5x implies. Why llama.cpp's DSpark accepts less than those engines' was not tested.

## Attempts (all in the prereg amendments)

1. Attempt 1: Loom-layout target refused by mainline (`blk.24.attn_q.weight not found`). A1: Mainline_Support target.
2. Attempt 2: N0 measured; draft refused (`markov_w1.weight` 256 x 201,024 vs expected 200,058). A3: unsloth's
   mainline draft (fetched 2026-11-26, MANIFEST E183).
3. Attempt 3: D3 and D7 measured with the mainline draft.
A2: r2 prompts were served from llama-server's prompt cache, so prefill comes from r1 only; decode is unaffected.

## Limits

One prompt set (E139 prompts, thinking off), two draft lengths (3, 7), one target quant (UD-Q4_K_XL), one build.
Lengths 4-5 and other quants were not tried. Speed only; output quality was not compared (speculative decoding is
designed to leave outputs unchanged).

## Decision

Stock llama.cpp + DSpark is not a reason to move Inkling off Loom/CIRU for speed. If Inkling is ever served on
llama.cpp, use 3 draft tokens (never 7). Recheck on a later llama.cpp build (WATCHLIST row: llama.cpp DSpark
acceptance on Inkling).
