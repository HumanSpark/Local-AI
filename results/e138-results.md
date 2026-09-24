# File: e138-results.md
# Purpose: Results for E138 block 1 - the "~73 tok/s, 10.1 GB, Bonsai 2 on Strix Halo" claim, scored against the pre-registration.
# Project: sparkbench | Date: 2026-09-23
#
# Overview: Nine arms measured in one clean window (gateway down, 01:48-02:57 + two extra memory
# arms), scored against results/e138-prereg.md and its two amendments. Speed is llama-server's own
# timings.predicted_per_second, median of three reps; memory is peak amdgpu GTT+VRAM against the
# idle baseline. Covers C1 (73 tok/s) and C2 (10.1 GB); C3-C6 wait for the second window.

# E138 RESULTS - the speed claim does not reproduce, and the MEMORY figure identifies the config (2026-09-23)

## Headline

**~73 tok/s does not reproduce on this box: the best of nine arms is 34.16 tok/s.** That is
Bonsai 2 PQ2_0 with the Bonsai-tuned DFlash2 drafter on a code prompt, and it is 2.8x the
incumbent's plain 12.33 - a real gain, less than half the claim.

**The 10.1 GB figure points at one configuration, and nearly matches it.** PTQ1_0 + the Q8_0
drafter at `-c 4096` peaks at **10.11 GiB = 10.85 GB**, against a claimed 10.1 GB: 7% high in GB,
and an exact match on the NUMBER if the claim was quoted in GiB. No other arm is near 10 GB. That
is the ternary file, and on our Vulkan stack it decodes at **3.63 tok/s**. So the claimed memory and the claimed speed belong to the same configuration
only if their kernels make PTQ1_0 roughly 20x faster than ours do - which is what "aggressive
kernel optimization" would have to mean.

## Every arm (clean window, gateway down, Rule 9 satisfied; all arms full-offload Vulkan0)

| arm | model + drafter | CODE tok/s | CHAT tok/s | draft acceptance CODE / CHAT | peak GPU GiB |
|---|---|---|---|---|---|
| **B1p** | PQ2_0 + ProCreations Q8_0, n=4 | **34.16** | 21.44 | 79% / 39% | 11.94 |
| B2p | PQ2_0 + z-lab Q8_0, n=4 | 31.44 | 20.71 | 70% / 37% | 11.94 |
| B1p-c4096 | as B1p, `-c 4096` | 31.09 | 21.06 | 38% (combined) | 11.29 |
| Q1 | Q4_K_M + z-lab Q8_0, n=4 | 25.67 | 16.70 | 82% / 44% | 20.66 |
| B1p-n8 | PQ2_0 + ProCreations, n=8 | 25.64 | 13.92 | 58% / 24% | 12.53 |
| B0p | PQ2_0, no drafter | 22.22 | 22.33 | - | 8.07 |
| **Q0** | Q4_K_M, no drafter (incumbent) | 12.33 | 12.37 | - | 16.78 |
| B1-c4096-ptq1 | PTQ1_0 + ProCreations, `-c 4096` | 3.63 | 2.80 | - | **10.11** |
| B0 | PTQ1_0, no drafter | 3.34 | 3.35 | - | 6.90 |

Reps are tight: B1p CODE 34.08 / 34.31 / 34.16, Q0 12.33 / 12.34 / 12.33. Load is 3.0 s for
every Bonsai arm.

`llama-bench` (tg128, d0 / d4096 / d8192): PQ2_0 **17.77 ± 2.97** / 17.21 / 17.81; PTQ1_0 2.95 /
3.17 / 3.27; Q4_K_M 12.58 / 12.31 / 12.12. Prefill pp512: 197.9 / 91.9 / 279.3.

⚠️ **Ruler note, unresolved.** `llama-bench` gives PQ2_0 17.77 tok/s where the server gives 22.22
on the same build and file, a 25% gap, and its error bar is ±2.97 against the server's ±0.16.
Q4_K_M shows no such gap (12.58 vs 12.33). Not traced; the PQ2_0 kernel may be warm-up sensitive.
**Scoring uses llama-bench where the prediction named it and the server elsewhere, as registered.**

## Predictions, scored

| # | field | predicted | observed | verdict |
|---|---|---|---|---|
| P1 | `B0.loads_vulkan` | yes, full offload (~60%) | loads, 130/130 Vulkan0, correct output | **HELD** (scored in amendment 1) |
| P2 | `B0p.llama_bench_tg128_d0` | 22-36 | **17.77 ± 2.97** | **FALSIFIED** - below the band. The server figure (22.22) lands inside it, which is why the ruler note matters |
| P3 | `B1p.server_tps_CODE` | 35-60, NOT >= 70 | **34.16** | **FALSIFIED** by 0.84 tok/s on the low edge. The directional half (not >= 70) held |
| P4 | `B1p.server_tps_CHAT` | >= 20% below CODE | 21.44 vs 34.16 = **37% below** | **HELD** |
| P5 | `B1p / B2p` CODE | > 1.0 | 34.16 / 31.44 = **1.087** | **HELD** - the Bonsai-tuned drafter accepts 79% against the generic one's 70% |
| P6 | `B1p.peak_mem_gib` at `-c 16384` | 8.0-11.0 | **11.94** | **FALSIFIED** - above the band |
| P7-P10 | quality, agentic, pi | - | not run (amendment 2) | **UNSCORED** |

**C1 (>= 65 tok/s on `server_tps_CODE`): NOT REPRODUCED.** Best arm 34.16.
**C2 (10.1 GB): NEAREST MATCH 10.11 GiB = 10.85 GB**, at PTQ1_0 + drafter, `-c 4096` - 7% above
the claim as stated in GB, exact if the claim meant GiB. The claim names no context size, and KV
is what moves this figure: the same config at `-c 16384` would sit higher.

## What the numbers say

1. **Speculation pays on code and costs nothing on chat.** B1p is 1.54x B0p on CODE (34.16 vs
   22.22) and 0.96x on CHAT (21.44 vs 22.33) - acceptance falls from 79% to 39%. This is F85's
   structured-vs-chat split again, on a different mechanism.
2. **More draft is worse.** n=8 drops CODE to 25.64 (acceptance 79% -> 58%), a 25% loss against
   n=4, and CHAT to 13.92, a 35% loss. Whatever "aggressive" means in the claim, raising the draft length is
   not it.
3. **Bonsai 2 genuinely beats the incumbent on speed and memory.** Plain: 22.22 vs 12.33 tok/s
   (1.80x) on 8.07 vs 16.78 GiB. Best-to-best: 34.16 vs 25.67 (1.33x) on 11.94 vs 20.66 GiB.
   **Whether it keeps the incumbent's ANSWERS is unmeasured** until block 2 - F144 found a 3-bit
   quant of this same model losing 3 of 8 on the expert bank while three other banks called it
   identical.
4. **The PTQ1_0 path is broken for decode on RADV, not merely slower.** 3.34 tok/s from a 5.53 GiB
   file is ~18 GB/s of effective bandwidth against a ~220 GB/s machine. It is a DECODE defect:
   prefill is only 2.2x slower than PQ2_0 (91.9 vs 197.9 pp512) where decode is 6.6x slower
   (3.34 vs 22.22). The fork enabled PTQ1_0's integer-dot
   mat-vec for Intel Xe2 only (#238); AMD RADV takes a dequantise path.
5. **73 tok/s would need a further 2.1x over our best arm.** Two candidates, neither testable
   here: kernels that make PTQ1_0 fast on AMD (the config the 10.11 GiB match points at), or a
   HIP build (the only public Strix Halo Bonsai figures, 32.758 tok/s on Bonsai v1, are ROCm).
   Our best Vulkan arm already exceeds that published ROCm figure.

## Honest caveats

- **The claim's own build is not ours.** All Bonsai arms ran on a LOCAL port: mainline's DFlash2
  commit cherry-picked onto the PrismML fork (amendment 1). The fork alone cannot load either
  DFlash2 drafter. If the poster ran a different tree, their kernels are not the ones measured here.
- **"98% FP16 precision" is not addressed by this block.** It is PrismML's own 20-benchmark
  aggregate on an H100. Block 2 tests retention against our Q4_K_M incumbent, not against FP16.
- **No HIP arm was run.** The pre-registered fallback was for a Vulkan failure, and Vulkan did not
  fail. HIP remains the leading untested explanation for the gap.
- `-c 16384` for the main arms, `-c 4096` for the two extras; the claim names no context size.
- **GiB vs GB is not cosmetic here.** Every figure in this file is GiB unless it says GB; the
  claim's "10.1GB" is ambiguous and the two readings differ by 7%, which is larger than the gap
  between two of the arms.
