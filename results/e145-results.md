# File: e145-results.md
# Purpose: Results for E145 - the models from a third-party "approximate options for 128 GB" widget, plus Ornith 1.5, through Aider on the three E113 tasks, against E143's arms.
# Project: sparkbench | Date: 2026-09-25
#
# Overview: Scored against results/e145-prereg.md (4de0526), window script tools/run_e145_window.sh.
# One window 22:33-00:20, 6,429 s, four arms, 36 attempts, 0 void, 0 amdgpu fault lines. E143's four arms
# are the comparison, not re-run (same build daef7b6, harness, flags). No arm is distinguished from another
# on pass count; the widget's speed ORDER holds and its speed SIZE does not. Scoring output
# results/raw/e145/score.txt, per-attempt evidence results/raw/e145/<arm>/. Registered as F167.

# E145 RESULTS - the widget's options tie with what we already ran (2026-09-25)

## Per arm (3 tasks x 3 repeats, llama.cpp daef7b6, served solo)

| arm | model | passes | T1 | T2 | T3 | mean repeat s | vs H |
|---|---|---|---|---|---|---|---|
| H | Qwen3.6-35B-A3B UD-Q4_K_M (widget 1) | 6/9 | 3/3 | 3/3 | 0/3 | 294 | 1.00 |
| E | Ornith 1.0 35B Q4_K_M (widget 3) | 6/9 | 3/3 | 3/3 | 0/3 | 179 | **0.61** |
| F | Ornith 1.5 35B-A3B Q4_K_M (newer than widget) | 6/9 | 3/3 | 3/3 | 0/3 | 267 | 0.91 |
| G | Qwen3.6-27B Q4_K_M (stand-in for widget 2) | **7/9** | 3/3 | 3/3 | 1/3 | 1,380 | **4.69** |
| C | (E143) Qwen3.6-35B UD-Q4_K_XL | 6/9 | 3/3 | 3/3 | 0/3 | 321 | 1.09 |
| A | (E143) Qwen3.8-27B | 5/9 | 3/3 | 2/3 | 0/3 | 1,719 | 5.85 |
| B | (E143) Flash-Next | 6/9 | 3/3 | 3/3 | 0/3 | 707 | 2.40 |
| D | (E143) Qwen3-Coder | 5/9 | 3/3 | 0/3 | 2/3 | 166 | 0.56 |

Widest pass-count gap between any two of the eight arms: 2 of 9. **No arm is distinguished** (band: 4).

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `H.passes` | 4-8 | 6 | HELD |
| P2 | `H/C repeat time` | 0.85-1.15 | 0.913 | HELD |
| P3 | `E/H repeat time` | 0.55-0.90 | 0.61 | HELD |
| P4 | `E.passes` >= `H.passes` - 2 | >= 4 | 6 | HELD |
| P5 | `F.passes` >= `E.passes` - 1 | >= 5 | 6 | HELD |
| P6 | `G/H repeat time` | 2.5-6 | 4.69 | HELD |
| P7 | `G.passes` within 2 of `H.passes` | within 2 | 7 vs 6 | HELD |
| P8 | T3 passes <= 1 of 3 in >= 3 of 4 arms | yes | 0, 0, 0, 1 | HELD |

## Against the widget's claims (bands fixed in the prereg)

| widget claim | measured | verdict |
|---|---|---|
| Ornith 1.0 "~42% faster", "retains ~98% intelligence" | 39% less time (1.64x the speed); 6/9 = 6/9 | **speed order CONFIRMED, size larger; intelligence not separable** |
| Qwen3.6 27B "~5% more intelligent" | 7/9 vs 6/9 (G is a Q4_K_M stand-in for OptiQ 4-bit) | direction consistent; a 1-in-9 gap is not a result |
| Qwen3.6 27B "~109% slower" (2.09x) | **4.69x** the 35B's time | **the widget understates it by more than 2x** |
| "best fit" 35B | ties every 35B-class arm on passes | not distinguished |

Caveats that bind the speed rows: the 27B thinks by default and the 35Bs run at their embedded
defaults, so time includes thinking; the widget's "tasks/hr" has no stated method; G is a different
quantisation from the widget's OptiQ MLX file, which this box cannot load.

## What the totals show

1. **Eight models, one band.** Passes run 5 to 7 of 9 across two experiments and eight arms. The
   instrument cannot rank them, so the widget's intelligence scores (68.9, 72.0, 67.2) cannot be tested
   with it. F151 and F126 said this about saturated banks; here it is resolution, not saturation.
2. **Ornith 1.5 gave the speed back.** F is 49% slower than E (267 s vs 179 s) at the same pass count, and
   about level with the Qwen3.6 35B. The widget lists 1.0; its speed claim does not carry to 1.5.
3. **The dense Qwen3.6-27B did the most, slowly.** 7/9 and the only non-Coder T3 pass (1 of 3), at 4.7x the
   35B's time. Qwen3.8-27B (E143 A) scored 5/9 on the same bank: a 2-of-9 gap, inside the band, so not a
   generation ranking.
4. **T3 across all eight arms: 3 passes in 24 attempts** (Coder 2, Qwen3.6-27B 1). T1 passes 24 of 24.
   Whether T3's failures are Aider application faults (F152) is still undiagnosed.

## Limits

3 tasks, so three independent draws per model; the repeats measure sampling noise, not task variety.
Ornith's lineage is unverified (no base model declared). Comparison arms are E143's, run on the same
build and flags but in a different window. Server-default sampling and thinking per model.
