# File: e137-results.md
# Purpose: Results for E137 - upscaling the Dispatches cover to 1500 and 3000 px, scored against the pre-registration.
# Project: sparkbench | Date: 2026-09-22
#
# Overview: Three arms (L Lanczos, R Real-ESRGAN x5 variants, Q Qwen-Image-2.1 edit), each run
# solo on an idle GPU with the relay down. Faithfulness is PSNR of the output downscaled back to
# 1254 against the source; text is judged on crop sheets. Figures from results/e137/scores.json.

# E137 - RESULTS: upscaling the Dispatches cover (2026-09-22)

Pre-registration: `results/e137-prereg.md` (plus amendment 1). Source: `results/e137/source-dispatches-1254.png`.

## Table

| output | raw px | solo time | PSNR back (dB) | text |
|---|---|---|---|---|
| L-lanczos | 1254 | - | 46.25 | all correct, soft |
| R-realesrgan-x4plus | 5016 | 14.15 s | 36.22 | all correct, sharpest, cleanest edges |
| R-realesrgan-x4plus-anime | 5016 | 5.26 s | 34.78 | all correct, halo round every letter - rejected |
| R-realesr-animevideov3-x2 | 2508 | 1.16 s | 34.76 | all correct |
| R-realesr-animevideov3-x3 | 3762 | 2.17 s | 34.88 | all correct |
| R-realesr-animevideov3-x4 | 5016 | 3.36 s | 35.02 | all correct |
| Q-qwen-edit | 1536 | 5,499.56 s (40 steps, 122.8 s/step) | 17.95 | all correct - see below |

Q: diffusers, math attention, `output_resolution=1536`, seed 42, CFG 1.0, VAE tiled, peak GPU
82.5 GiB, MemAvailable floor 16,206 MiB against a 12 GiB guard (never fired). Run 00:44-02:05.

Ruler note: re-measuring x4plus from its raw 5016 PNG in the Q scoring pass gave 36.25 dB against
the stored 36.22. The 0.03 dB is not traced. It does not affect any verdict (the nearest
decision gap is 18 dB).

## What Q did

Every word survived, character for character: small caps line, byline, stamp `HUMANSPARK.AI`,
the handwritten tagline. It still redrew the picture:

1. **Geometry moved.** Card, stamp and seal sit a few px off their source positions (visible on
   every crop sheet as an offset). That drives most of the 17.95 dB.
2. **Paper retextured.** Coarse, crinkled grain where the source is smooth card.
3. **Wax seal redrawn.** A new bolt shape, stubbier than the source's, and a rougher wax texture.
4. **A faint ghost** of the stamp text line sits just under `HUMANSPARK.AI`.

Crops: `results/e137/crops-Q-{byline,handwriting,stamp,smallcaps,seal}-3000.png` (source,
L, x4plus, Q). R-only sheets: `crops-{...}-3000.png`.

## Predictions

| # | field | result | verdict |
|---|---|---|---|
| P1 | `L.text_legible_3000` | legible, soft, no new detail | **held** |
| P2 | `R.best_variant` | x4plus best; x4plus-anime plasticky/haloed; animevideov3 fine but softer | **held** |
| P3 | `R.psnr_back` vs `L.psnr_back` | 36.22 vs 46.25 = 10.03 dB below | **falsified** (predicted within 2 dB). Much of R's gap is sharpening the source's own JPEG-soft edges, which PSNR-back counts as change |
| P4 | `Q.psnr_back` | 17.95, 28.30 dB below L | **held** |
| P5 | `Q.text_correct` | wordmark and "Dispatches" survive; NO small text line altered | **half held** - the "at least one small line altered" half is falsified; the changes landed on texture and the seal instead |
| P6 | `owner_pick` | owner asked for the largest x4plus render and took 3000 + 1500 JPGs from it before Q finished | **held** (by delivery, before Q was shown) |

## Findings

- **For a cover, use Real-ESRGAN x4plus.** 14 s, faithful, cleanest type. Delivered:
  `results/e137/Dispatches-cover-3000.jpg` (q92) and `Dispatches-cover-1500.jpg` (q85).
- **Qwen-Image-2.1 edit is not an upscaler.** It kept every word, which is a real advance in
  text rendering, but it moved, retextured and redrew the brand mark in a 92-minute run. It
  redraws rather than enlarges, so it is not safe for anything where the artwork is fixed.
- **Tools that exit 0 on failure.** First R pass beside the E136 edit: two models wrote all-black
  PNGs on `vkQueueSubmit failed -4`. Void, re-run solo (`results/e137/raw/void-contended/`).
