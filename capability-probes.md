# File: capability-probes.md
# Purpose: Results log for non-LLM capability probes (briefing v2 Part 3: STT, image generation, TTS).
# Project: sparkbench | Date: 2026-07-04
#
# Overview: Exploratory probes - "does it work, roughly how fast" - not
# comprehensive benchmarks. One section per probe with the briefing's
# capture fields, build provenance, and the consulting question answered.
# Stack: Vulkan RADV / Mesa 25.2.8 / kernel 6.17.0-35 unless noted.

## 3.1 Speech-to-text: whisper.cpp - PASS, 28x real-time

- Build: whisper.cpp master @ clone 2026-07-04, `-DGGML_VULKAN=ON`,
  checkout at ~/sparkbench/whisper.cpp (gitignored). Built clean,
  first try.
- Vulkan acceleration CONFIRMED: model loaded to Vulkan0 (Radeon
  8060S RADV GFX1151), 1.62GB on-device for large-v3-turbo.
- Test audio: samples/jfk.wav (11s) + a 330s file made by
  concatenating it 30x (stdlib wave; no ffmpeg on host - see
  DEFERRED-ROOT note below).

| Model | Audio | Total time | RTF | Transcript |
|---|---|---|---|---|
| large-v3-turbo (1.6GB) | 11s | 1.27s (incl. 0.31s load) | ~11x | correct |
| large-v3-turbo | 330s | 11.69s | **~28x real-time** | correct |
| small (466MB) | 330s | 11.87s | ~28x | correct |

- **Finding: quality is free.** small and large-v3-turbo run at the
  SAME speed on this stack (both ~28x; the bottleneck is not the
  encoder GPU work at these sizes). Always use large-v3-turbo.
- **Consulting question ("real-time meeting transcription?"): YES,
  emphatically.** A 1-hour meeting transcribes in ~2 minutes with
  the best turbo model; live streaming use leaves >25x headroom.
- Caveats: single-speaker clean audio sample; repeated content may
  flatter the decoder slightly. Real meeting audio (crosstalk,
  accents) is a quality question for a later eval, not a throughput
  one. ffmpeg absent (apt) - listed in DEFERRED-ROOT.md alongside
  ROCm; stdlib wave sufficed here.

## 3.2 Image generation: stable-diffusion.cpp - PASS (with one required flag)

- Build: stable-diffusion.cpp master @ clone 2026-07-04, `-DSD_VULKAN=ON`,
  at ~/sparkbench/stable-diffusion.cpp (gitignored). Built clean.
  NOTE: the CLI binary is now `sd-cli`, not `sd` (briefing's command
  is stale); FLUX split files load via `--diffusion-model`, not `-m`.
- Model set (tool-local models/, provenance = size+sha256 verified at
  fetch): flux1-schnell-Q4_0.gguf (6.77GB, city96, oid-matched);
  ae.safetensors (335MB - SUBSTITUTION: black-forest-labs repo is
  GATED (401), ungated second-state mirror used, byte-size identical,
  oid-matched); clip_l (246MB) + t5xxl_fp16 (9.79GB) from
  comfyanonymous, oid-matched.
- VRAM: 15.94GB total (t5xxl 9.3GB dominates - fp8 variant would
  halve this if VRAM ever matters).

| Resolution | Sampling (4 steps) | VAE decode | Total gen | Verdict |
|---|---|---|---|---|
| 512x512 | 8.52s | 0.94s | **~9.5s** | clean image |
| 1024x1024 (no flag) | 40.25s | FAILS | - | OOM at decode |
| 1024x1024 --vae-tiling | 40.25s | 7.23s | **~48s** | clean image |

- **FINDING - deployment gotcha:** at 1024x1024 the FLUX VAE requests
  an 8.5GB contiguous compute buffer; RADV's single-allocation limit
  (~4.3GB) rejects it AFTER 40s of successful sampling. `--vae-tiling`
  is mandatory at 1024 on this stack (7.2s tiled decode, no quality
  complaint visible). Failure mode is late and expensive - bake the
  flag into any wrapper.
- Quality: both images coherent, well-lit, artefact-free to my eye;
  sent to Alastair 2026-07-04 for the subjective call.
- **Consulting question ("local images instead of Midjourney/
  DALL-E?"): qualified YES** - 9.5s at 512, 48s at 1024, on-prem,
  no per-image billing; the qualification is FLUX-schnell's style
  range vs commercial tools, a quality question not a speed one.

### 3.2 addendum: 50-image style gallery + resolution ceiling (2026-07-04)

- **Gallery batch (Alastair request):** 50 business-blog prompts
  across 10 style families (photography, flat/isometric illustration,
  watercolor, oil, cartoon/comic, 3D render, sketch/line art, pixel
  art, business-concept), 1024x1024, seeds 1001-1050, prompts tracked
  in results/flux-gallery-prompts.txt. **50/50 succeeded**, ~36s
  sampling each, ~55 min wall total, images in results/flux-gallery/
  (gitignored, 67MB) + zip delivered to Alastair. Sampling time was
  style-invariant (35.9-36.1s across all families) - cost depends on
  pixels, never on content or style.
- **Resolution ceiling (Alastair request - 1080p/4K):**

| Resolution | MP | Result |
|---|---|---|
| 1024x1024 | 1.05 | OK, ~40s sampling |
| 1344x768 (16:9) | 1.03 | OK, 35s |
| 1536x864 (16:9) | 1.33 | **OK, 49s - largest verified 16:9** |
| 1792x1008 (16:9) | 1.81 | FAILS - flux compute buffer over allocation cap |
| 1920x1080 (native 1080p) | 2.07 | FAILS - same cap |
| 3840x2160 (native 4K) | 8.29 | FAILS - requests a 208GB buffer (impossible: exceeds total RAM) |

- **FINDING:** the binding constraint is the RADV single-allocation
  cap (~4.3GB) on the transformer's attention buffer, which grows
  ~quadratically with pixel count - NOT total VRAM (only 16GB of
  110GB was in use). Practical ceiling ~1.3-1.5MP. Production recipe
  for 1080p/4K deliverables: generate at 1536x864 and upscale (1.25x
  to 1080p; a dedicated upscaler for 4K - candidate future probe,
  e.g. realesrgan-ncnn-vulkan). Failure mode caveat from the first
  attempt: errors can arrive AFTER a full sampling phase, and a
  filtered log can hide them - always check the output file exists.

## 3.3 Text-to-speech: Piper - PASS, 26.6x real-time on CPU

- Install: pre-built binary release 2023.11.14-2 (pip unavailable on
  host - python3-pip in DEFERRED-ROOT.md; the briefing's binary
  fallback used instead). Location: ~/sparkbench/piper/ (gitignored);
  tarball sha256 recorded in docs/TOOLCHAIN.md.
- Voice: en_GB-alba-medium (63MB onnx, sha256 in TOOLCHAIN.md) -
  British English per the briefing's Irish-market note.
- Test: 497-character paragraph -> **30.1s of audio in 1.13s = 26.6x
  real-time, CPU-only** (no GPU involvement at all - this leaves the
  GPU free for concurrent LLM work).
- Quality: **APPROVED for utilitarian narration - Alastair auditioned the
  sample 2026-07-04: "sounded great", and he specifically likes the alba
  voice.** en_GB-alba-medium remains the default voice for the "listen to this
  page" read-aloud narrations. A subsequent by-ear comparison of three engines
  (Piper / Kokoro / Chatterbox) for the expressive two-voice podcast judged
  Piper too flat and monotone there and adopted Chatterbox instead
  (results/audio-quality-verdict.md). The two verdicts are consistent, not
  contradictory: Piper is good enough for a flat, functional read-aloud but not
  for expressive delivery.
- **Consulting question ("local speech generation for
  accessibility/training?"): YES, unqualified** - a 10-minute
  narration renders in ~23 seconds on CPU while the GPU serves LLM
  load, and the quality passed the founder's ear test.
