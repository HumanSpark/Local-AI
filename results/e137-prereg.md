# File: e137-prereg.md
# Purpose: Pre-registration for E137 - can the models on sparkmax upscale a text-heavy brand image to 1500 and 3000 px square.
# Project: sparkbench | Date: 2026-09-22
#
# Overview: Three arms along the METHOD axis (classical resample, a GAN super-resolution
# network, a diffusion re-render), variants labelled inside their arm, predictions with fields,
# written before any run.

# E137 - PRE-REGISTRATION: upscaling the Dispatches cover (2026-09-22)

Owner's ask: upscale the HumanSpark Dispatches cover (1254x1254) to 1500x1500, ideally 3000x3000,
testing "all the models we have available". Source: `results/e137/source-dispatches-1254.png`.

## Arms - THREE, along the method axis

| arm | method | variants (NOT arms) |
|---|---|---|
| **L** | Lanczos resample (Pillow) - the control; invents nothing | - |
| **R** | Real-ESRGAN ncnn-vulkan v0.2.5.0 (installed, E3) | `x4plus` (general), `x4plus-anime`, `animevideov3` x2 / x3 / x4 |
| **Q** | Qwen-Image-2.1 edit mode, asked to reproduce the image at higher resolution (diffusers, AOTriton attention, relay down) | native 1:1 bucket 2048x2048 |

Every output is brought to exactly 1500 and 3000 by a final Lanczos resample, so sizes match.
Not included, and why: sd.cpp's `--upscale-model` runs the same ESRGAN family as R; FLUX and
the Qwen text-to-image path are generators, not upscalers.

## Measures

- **Faithfulness** (objective): downscale each output back to 1254 and compute PSNR against the
  source. A faithful upscale lands near L's value; a re-render that changed content lands far below.
- **Text** (visual, owner is the judge): zoomed crops of the small caps line, "Written by / Narrated
  by", the stamp's "HUMANSPARK.AI", and the handwritten tagline.

## Predictions (field named)

| # | field | prediction |
|---|---|---|
| P1 | `L.text_legible_3000` | legible but soft - no new detail |
| P2 | `R.best_variant` | `x4plus` for the photo-like paper and wax texture; an anime variant sharper on type but plasticky on texture |
| P3 | `R.psnr_back` vs `L.psnr_back` | within 2 dB - R sharpens, does not rewrite |
| P4 | `Q.psnr_back` | at least 5 dB below L - the diffusion path redraws |
| P5 | `Q.text_correct` | the large wordmark and "Dispatches" survive; at least one small text line (handwriting or stamp) is altered |
| P6 | `owner_pick` | an R variant, not Q - faithfulness matters more than invention for a cover |

## AMENDMENT 1 - arm Q's size and attention path (declared 2026-09-22 00:42, before Q runs)

E136's diagnostic (same day) shows AOTriton attention returns NaN on this box, and math attention at
2048x2048 + a 2048 reference needs ~70 GB (the E136 guard firing). Q therefore runs with math
attention at `output_resolution=1536` (1536x1536 output, reference resized to match): ~18.4k image
tokens, estimated ~21 GB of attention. 1536 is above the 1500 target; Q's output is resampled to 1500
and 3000 like every other arm. Prompt: "Reproduce this image exactly at higher resolution: identical
composition, layout, colours and all text, character for character. Sharpen detail and textures.
Change nothing else." Seed 42, 40 steps, CFG 1.0, VAE tiled, relay down, mem_guard. P4-P5 stand.
