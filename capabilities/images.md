# Images (r6.2)

Generating and editing pictures from a description.

**Against the frontier:** Not compared with a frontier service yet. ([how it compares](../FRONTIER.md))

## What works best now

- **In production: FLUX.1-schnell (Q4_0)** on stable-diffusion.cpp (served on request by the gateway's image service), since 2026-08-10.
  Why: Passed the image probe and a 50-image style gallery the owner assessed; runs beside the language model.
- **Best alternative: Qwen-Image-2.1** on diffusers on ROCm PyTorch (BF16, tiled VAE decode), since 2026-09-21.
  Why: Runs and edits text well, but only with the gateway down; edits are local changes only.

## The experiments behind this, best results first

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| Image generation probe and 50-image style gallery (P3.2) | 2026-07-04 | in production | FLUX.1-schnell runs on the box; the owner assessed a 50-image gallery. | [capability-probes.md](../capability-probes.md) |
| Qwen-Image-2.1 on the box (E136) | 2026-09-21 | works, with caveats | Runs, but only with the gateway down and the image decode tiled. | [results/e136-results.md](../results/e136-results.md) |
| Upscaling a cover image (E137) | 2026-09-22 | inconclusive | A one-off upscaling job for a cover image. | [results/e137-results.md](../results/e137-results.md) |

