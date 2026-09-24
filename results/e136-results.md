# File: e136-results.md
# Purpose: Results for E136 - Qwen-Image-2.1 on sparkmax, diffusers vs stable-diffusion.cpp, scored against the pre-registration.
# Project: sparkbench | Date: 2026-09-21
#
# Overview: Scores P1-P7 plus amendment 2's prediction from results/e136-prereg.md, using
# the per-image logs and metrics under results/e136/. Covers the attempt-1 wedge, the four
# scoreable runs inside the relay window (16:32:27 onward), and the full-size final.

# E136 - RESULTS: Qwen-Image-2.1 runs on sparkmax, and the runtime ranking is not the one predicted (2026-09-21)

## Headline

Qwen-Image-2.1 runs on sparkmax through BOTH runtimes, 20/20 images in the relay window, once
the gateway is down and the VAE decode is tiled. Attempt 1, with the gateway up and the decode
untiled, exhausted system RAM and the hardware watchdog reset the box (amendment 1).

The fastest configuration is **sd.cpp with the Q8_0 DiT: 384 s mean sampling per 1376x768
image**, visually indistinguishable from BF16 (W1: mean abs pixel diff 1.2-1.6/255, PSNR
32.6 dB). At equal BF16 precision, **diffusers is FASTER than sd.cpp**, the opposite of P4.

## Timings (relay DOWN, all runs 1376x768, 40 steps, CFG 1.0, seed 42)

| run | W1 | W2 | W3 | W4 | W5 | mean | vs S |
|---|---|---|---|---|---|---|---|
| **S** sd.cpp BF16, sampling s | 652.43 | 669.82 | 632.91 | 663.92 | 653.23 | **654.46** | 1.000 |
| S-fa, + `--diffusion-fa` | 626.97 | 611.75 | 631.74 | 613.54 | 631.45 | **623.09** | 0.952 |
| S-q8, Q8_0 DiT | 394.70 | 386.69 | 371.89 | 379.17 | 387.56 | **384.00** | 0.587 |
| **D** diffusers BF16, sampling + decode s | 660.19* | 463.61 | 463.04 | 480.06 | 463.39 | **467.53** (W2-W5) | - |

sd.cpp decode (tiled) is 10.6-11.5 s per image and is NOT in the S rows. D's `sec` includes
decode; W2-W5 sampling ran 11.2-12.5 s/step and decode ~14 s. *D W1 carries a one-off ~160 s
on its first decode (W2-W5 do not), so the D mean is taken over W2-W5 and W1 is shown, not
hidden. Like-for-like end to end, steady state: **D ~467.5 s vs S ~665.4 s** (654.46 + 10.91 mean decode).

## Predictions, scored

| # | field | predicted | observed | verdict |
|---|---|---|---|---|
| P1 | `D.completes` | 6/6 | 5/5 text-to-image in the window (attempt 1 wedged, see amendment 1); E1 not run - no reference file | **HELD for 5/5 T2I; E1 unscored** |
| P2 | `S.completes` | yes (~70%) | 5/5, and 5/5 for each variant | **HELD** |
| P3 | `S.sec_per_image` sampling | 100-400 s | 654.46 s mean | **FALSIFIED** - 1.6x over the top of the band |
| P4 | `D/S` sec per image | > 1.0 | 0.703 (467.5 / 665.4, end to end, steady state) | **FALSIFIED** - diffusers is the faster BF16 runtime |
| P5 | `D.peak_gpu_mem_gib` | < 40 | 35.52-35.59 GiB | **HELD** |
| P6 | `wordmark_correct` W1, W2, W4 | yes, all three | W1, W2 correct in all 8 images across S, S-q8, S-fa and D (each inspected); W4's header wordmark correct, its small dashboard labels garbled in both runtimes | **PARTIAL** |
| P7 | `owner_prefers_over_current` | at least one | owner, 2026-09-21, after W1-W5 and four W1 layout variations: *"the original is still the better composition of the lot"* - meaning his 18-month-old wallpaper. His earlier pick of W2 for a full-size render was a selection among the new set, not a preference over the old | **FALSIFIED** on composition |
| A2 | `S-fa / S` | < 0.8 | 0.952 | **FALSIFIED** |

## What the misses say

- **P3 and A2 miss for one reason.** The FLUX-derived estimate assumed step time scales with
  parameters and that attention is a big share. Flash attention buys 4.8%, while halving the
  DiT's weight bytes (Q8_0) buys 41.3%. On Vulkan/gfx1151 this DiT's step is bound by weight
  traffic through the matmuls, not by attention.
- **P4 misses because the premise was stale.** "PyTorch on ROCm is less tuned than ggml
  Vulkan here" came from the W3 TTS engines. For a single large BF16 DiT, the ROCm GEMM path
  beats ggml-Vulkan's BF16 path by ~30%. Quantisation is ggml's advantage, not the runtime.
- **Attempt 1 ran at 15.0 s/step; the window run at 11.2-12.5 s/step.** Two things changed
  at once - the gateway's resident model AND a concurrent 40 GB download with on-arrival
  hashing - so the ~20% cannot be pinned on the gateway alone. What is attributable is the
  RAM: the resident model took the headroom the untiled decode then exhausted.

## Memory

| run | min MemAvailable | guard fired |
|---|---|---|
| S | 84,241 MiB | no |
| D | 75,793 MiB | no |

## Not established

- **E1 (edit of the old wallpaper)** did not run: only a chat preview of the owner's image
  exists on the box. `qwen-image/e136_briefs.json` carries the TODO.
- **Seams in D's tiled decode**: faint vertical streaks were seen in D W1/W4. A column-gradient
  check found no periodic seam - the top columns sit on content edges in both runtimes. It is
  recorded as an unconfirmed visual note, not a finding.
- **What P7 leaves open:** the new renders win on palette and on the wordmark (correct in
  every W1/W2 image); the old image wins on composition. E1 - editing the OLD image onto the
  current palette - is the experiment that tests whether both can be had at once, and it is
  blocked only on the file.
- **D with Q8** and **D with experimental AOTriton attention** (`TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1`)
  were not run. Given A2, the attention flag is unlikely to matter much.

## Final for the owner (delivery, not part of the comparison)

W2 at the native **2752x1536**, sd.cpp `c678dfe`, Q8_0 DiT + `--diffusion-fa`, VAE tiled,
seed 42, CFG 1.0: sampling **1912.26 s** (47.8 s/step), decode 61.57 s, total 1977.89 s. Guard
never fired; MemAvailable stayed ~88 GiB. 4.0x the pixels of the comparison size cost 5.0x
the sampling time of S-q8 (384 s). Wordmark spelled correctly, filled gold bolt, left side
empty as briefed. File: `results/e136/final-W2-2752/W2-2752x1536.png` (4,460,615 B).

## E1 - editing the owner's original (amendment 3)

Arm D, relay down, 1248x832 (output_resolution 1024 at the original's 3:2), 40 steps, seed 42.
E1 1157.17 s (first edit, includes a one-off), E1b 893.49 s, E1c 887.87 s; peak 42.19-42.22 GiB;
guard never fired. The reference image roughly doubles the sequence, so an edit costs ~1.9x a
text-to-image render at the same size.

| # | field | observed | verdict |
|---|---|---|---|
| P8 | `layout_kept` | all three keep every object in place - laptop, chart panel, bar tower, both documents | **HELD for all three** (predicted drift in E1/E1c did not happen) |
| P9 | `orange_gone` | sampled orange px 691 -> 241 / 264 / 303, gold 41 -> 368 / 329 / 367 | **PARTIAL** - mostly moved to gold, not all |
| P10 | `wordmark_correct` laptop + notebook | correct and crisper on both, all three | **HELD** |

**The wording barely matters and the model will not move the global colour.** Mean dark-pixel
RGB: original (1, 20, 30); E1b "colours only" (1, 19, 34); brand navy is (0, 8, 42). The edit
path does LOCAL changes well and GLOBAL grading not at all.

**Recipe that works: edit, then grade.** A deterministic grade on E1 - remaining orange hues
rotated to brand gold's hue (0.130), dark pixels blended toward #00082A by a per-channel gain
weighted by darkness - gives dark-pixel mean (0.7, 10.4, 43.5) against (0, 8, 42), in under a
second. `results/e136/e1-1024/E1-graded.png`. This is the first output that keeps the owner's
composition AND sits on the current palette.
