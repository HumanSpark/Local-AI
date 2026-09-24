# File: e136-prereg.md
# Purpose: Pre-registration for E136 - can sparkmax run Qwen-Image-2.1, through which runtime, how fast, and does it fix FLUX's text failure.
# Project: sparkbench | Date: 2026-09-21
#
# Overview: Registers the question, the two runtime arms (one variant inside
# the sd.cpp arm), the wallpaper briefs, and seven predictions each naming the FIELD
# they are scored against - all BEFORE any generation runs.

# E136 - PRE-REGISTRATION: Qwen-Image-2.1 on sparkmax (2026-09-21)

## The question

The owner asked whether `Qwen/Qwen-Image-2.1` (released 2026-09-20) can run here.
Licence was cleared by the owner the same day: Qwen state that generated outputs
are not part of the licensed Materials and users keep the rights to them.

Mode: **spike**. Go/no-go and a first look. Numbers are reported, so downloads are
pinned and manifested, but nothing here graduates to serving.

## The arms - TWO, along the RUNTIME axis

| arm | runtime | weights | precision |
|---|---|---|---|
| **D** | diffusers `QwenImage21Pipeline` @ `9f12469`, torch 2.9.1+rocm7.2.3, container `localhost/qwen-image21:rocm` | `Qwen/Qwen-Image-2.1` @ `790c926` (official, sharded) | BF16 throughout |
| **S** | stable-diffusion.cpp @ `c678dfe70` (Vulkan, HEAD 2026-09-20; Qwen-Image-2.1 landed in #1994) | `Comfy-Org/Qwen-Image-2.1` @ `ace0ede`: bf16 DiT + bf16 VAE + qwen3vl_8b bf16 TE | BF16 throughout |
| S-q8 | variant of S, NOT a third arm | `leejet/Qwen-Image-2.1-GGUF` Q8_0 DiT, rest as S | Q8_0 DiT |

D and S hold precision constant so the runtime is the only difference. S-q8 asks
the deployment question (what does quantising the DiT cost) and is labelled a variant.

## Settings, identical across arms

**Test project (owner, 2026-09-21, before any run): replace his desktop wallpaper.** The
reference is his current wallpaper, made ~18 months ago: 1536x1024, dark teal/navy, a
laptop showing a "HumanSpark" wordmark with a bolt, 3D bar charts, orange accents. It
predates the current palette (humanspark.ai/design-language, fetched 2026-09-21): navy
`#00082A`, navy-light `#103A65`, brand gold `#EEBA00`, teal `#008A8B`; the spark is a
FILLED bolt; type is Inter. Orange is not canon.

**Comparison: 1376x768** - exactly half of the model's native 16:9 bucket (2752x1536, from
the model card's aspect table), ~1.06 MP so it sits beside E3's 1024x1024 figures. 40 steps,
seed 42, one image per brief, gateway left UP (workhorse resident; not a llama-server run).

**CFG = 1.0 (no guidance) on BOTH arms.** Declared before any run: the pipeline docstring says
Qwen-Image 2.1 "is meant to be sampled without guidance, hence the default of 1.0", while
sd.cpp's docs example passes `--cfg-scale 6.0`, which doubles the DiT passes per step. The
comparison uses the model author's value; sd.cpp at 6.0 may be run once, labelled, as a note.

Timing excludes model load, taken per image. **Finals** for the owner are re-rendered at the
native 2752x1536 on the winning runtime; that is delivery, not part of the comparison.

Briefs (5 text-to-image + 1 edit), full text in `qwen-image/e136_briefs.json`:

| id | brief | tests |
|---|---|---|
| W1 | the same concept, redone: laptop with the HumanSpark wordmark and a filled gold bolt, rising charts, current palette | direct like-for-like with the old image |
| W2 | minimal: navy ground, one gold filled bolt and the wordmark, faint teal circuit lines, left two-thirds empty for desktop icons | typography, restraint |
| W3 | abstract: light trails and particles converging on a gold spark, no text | pure image quality |
| W4 | cinematic photo: dark walnut desk, laptop showing a HumanSpark dashboard | photorealism + small text |
| W5 | isometric illustration of an on-prem AI workshop: server, laptop, charts, in the palette | illustration, detail |
| E1 | EDIT of the old wallpaper: move it to the navy/gold palette, keep the composition, crisp wordmark | image editing (D only if S lacks a vision projector) |

## Predictions (field named)

| # | field | prediction | why |
|---|---|---|---|
| P1 | `D.completes` | YES - D produces 6/6 images on gfx1151 | diffusers + ROCm torch runs the W3 engines here |
| P2 | `S.completes` | YES, weaker confidence (~70%) | support is one day old; open issue #2012 is a ROCm abort on Windows gfx1201 - we use Vulkan on Linux, so it should not apply |
| P3 | `S.sec_per_image` (sampling only, 1376x768, CFG 1) | 100-400 s | E3: FLUX-schnell 12B Q4_0 took ~36 s for 4 steps at 1024 (~9 s/step); scaling to 7B gives ~5 s/step, x40 steps, one pass per step at ~1 MP |
| P4 | `D.sec_per_image / S.sec_per_image` | > 1.0 (D slower) | PyTorch-on-ROCm for gfx1151 is less tuned than ggml Vulkan on this box |
| P5 | `D.peak_gpu_mem_gib` | < 40 GiB | 30.9 GiB of weights plus 1376x768 activations |
| P6 | `wordmark_correct` on W1, W2, W4, both arms | YES - "HumanSpark" spelled correctly in all three | Qwen-Image's headline strength; FLUX-schnell failed text outright |
| P7 | `owner_prefers_over_current` | at least one of W1-W5/E1 beats his current wallpaper | the old image predates two model generations |

P6 and P7 are visual judgements; the images go to the owner.

## AMENDMENT 1 - after attempt 1 wedged the box (declared 2026-09-21 16:30, before any re-run)

**Attempt 1, arm D, W1, 1376x768:** 40 steps completed at a steady 15.0 s/step
(10:18:55-10:28:41). The journal stops at 10:28:41, the first second of the VAE decode. No
image was written. The hardware watchdog reset sparkmax at 10:52:51. Nothing from attempt 1
is scoreable.

**Cause, from the previous boot's kernel log** (run by the owner with sudo): at 10:41:00 a
GPU allocation (`kfd_ioctl_alloc_memory_of_gpu -> amdgpu_bo_create -> ttm_pool_alloc_page`)
was in `__alloc_pages_slowpath` with **swap at 20 kB free**, `all_unreclaimable? yes`, and
Normal-zone free 8.58 GB of which 8.48 GB was CMA (unusable for this allocation). **System
RAM exhaustion through GTT**, with the gateway's model co-resident. NOT the
`drm_suballoc_new` deadlock of `docs/memory-edge-deadlock.md` - a different stack, and at
decode, not load. The log's header line (OOM-killer vs allocation stall) was not captured.

**Rule 9 was breached by this registration and is corrected here.** "Gateway left UP" voids
every timing under `docs/HARNESS-RULES.md` Rule 9; it also removed the memory headroom that
attempt 1 ran out of. Changes for all re-runs:

1. **The relay comes down** via `tools/relay_bench_window.sh down` (owner, sudo) for the
   whole E136 window. If it cannot, timings are recorded but VOID and P3/P4 are not scored.
2. **VAE tiling ON for both arms** (`--vae-tiling` in each runner). S already had it. D gains
   it so the arms decode the same way. This changes D from the first registration, and is
   declared here before it runs.
3. **`qwen-image/mem_guard.sh` runs beside every arm** and kills the job if MemAvailable
   falls below 12 GiB. A fired guard is a result (`completes = NO, memory`), not a crash.
4. **Order: S first, then D.** S has the tiled decode that was already proven on FLUX, and a
   second failure on D would say nothing new about the upgrade.

## AMENDMENT 2 - flash-attention variant (declared 2026-09-21 17:30, before it runs)

Arm S ran with `diffusion_flash_attn: false` (its log's own config line): `--diffusion-fa` was
not passed. **S-fa** is a labelled variant of S, not an arm: same BF16 files, same settings,
plus `--diffusion-fa`, all five briefs, in the same relay window after D. Prediction, field
`S-fa.sec_per_image / S.sec_per_image`: **< 0.8**, because attention over ~4k image tokens
plus the text prefix is a large share of each DiT step, and the non-FA path materialises it.

## AMENDMENT 3 - E1, editing the owner's original (declared 2026-09-21 21:15, before it runs)

Trigger: P7 falsified - the owner prefers his original's composition over all nine new
renders. E1 tests whether the edit path keeps that composition while moving it onto the
current palette. Reference: `qwen-image/original-HumanSpark-DesktopBG-v2.png`, 1536x1024,
1,913,138 B, fetched from Mailbox Drive `Pictures/` (size matches the remote listing).

Arm D only (sd.cpp's edit path needs the Qwen3-VL mmproj, not fetched). Relay down, VAE tiled,
mem_guard, seed 42, 40 steps, CFG 1.0, `output_resolution=1024` (~1 MP at the reference's
3:2). Three wordings in `e136_briefs.json` `edits`: E1 (as registered), E1b (colours only),
E1c (same layout, re-rendered sharper). Predictions, fields named:

| # | field | prediction |
|---|---|---|
| P8 | `E1*.layout_kept` - laptop, left chart panel, right bar tower and both documents in the same positions | YES for E1b; E1 and E1c drift more |
| P9 | `E1*.orange_gone` - no orange accent left | YES for all three |
| P10 | `E1*.wordmark_correct` on laptop AND notebook | YES on the laptop; the notebook's smaller text is the risk |

## AMENDMENT 4 - the full-size edit, after the guard fired (declared 2026-09-21 22:02, before the retry)

The E1 edit at `output_resolution=2071` (2528x1696) was killed by `mem_guard.sh` at 21:58:31, at
step 0: MemAvailable fell from 81,642 MiB to 12,050 MiB within one 11 s poll gap, swap starting
to fill. Diffusers' SDPA fell back to the MATH path (its own log: flash and mem-efficient attention
are "still experimental" on this GPU, gated on `TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1`), which
materialises the full attention matrix. Output + reference at this size are ~33.5k image tokens:
~2.2 GB per head at BF16 - tens of GB per layer call. At 1248x832 the same is ~8k tokens (~3 GB
total), which is why the 1 MP edits ran. The guard converted a wedge into a clean kill: first
real firing.

Retry: same run, plus `TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1`. Prediction, field
`e1final.completes`: YES, with peak GPU memory < 60 GiB. If the experimental kernel errors or the
guard fires again, fall back to `output_resolution=1536` (~2.4 MP) with the flag off.

## AMENDMENT 4 RESULT (recorded 2026-09-22 00:35)

`e1final.completes`: **FALSIFIED.** The AOTriton retry held memory (peak 43.28 GiB, MemAvailable
never under ~64 GiB, guard silent) and ran 40 steps in 8,919 s (210-215 s/step), but the output is
an all-black 2528x1696 PNG: one unique colour (0,0,0), 16,725 B, and diffusers logged
`invalid value encountered in cast` - NaN. Two variables changed against the working 1 MP edit
(AOTriton attention, and ~4x pixels), so the cause is not attributed. `run_diffusers.py` now raises
on a blank output instead of saving it as a success.

## NaN ATTRIBUTED (2026-09-22 00:40)

Diagnostic `results/e136/nan-diag-aotriton-1mp/`: the SAME 1 MP edit that succeeded as E1 (1248x832),
changing ONE variable - `TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL=1` - with 4 steps. Output blank
(max 0, std 0.00), `invalid value encountered in cast`; the new blank check raised. **The experimental
AOTriton attention produces NaN on gfx1151 with this model; size is not the cause.** Without it, math
SDPA materialises attention and the full-size edit exhausts RAM (amendment 4). So on this box the
diffusers path is capped by math-attention memory, not by time.
