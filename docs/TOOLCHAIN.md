<!--
# File: TOOLCHAIN.md
# Purpose: Record of user-level toolchain installs on benchhost - what, where, why, how to remove or make permanent.
# Project: sparkbench | Date: 2026-07-04
#
# Overview: Alastair authorised user-level installs 2026-07-04 (remote, no
# sudo available) with the instruction to document everything for a later
# tidy-up-or-make-permanent decision. Each entry records the exact
# footprint, the provenance chain, removal commands, and the permanent
# alternative. Nothing here touches shell init files or anything under
# ~/workstation-dotfiles - that tree is deploy-managed and edits would
# create drift.
-->

## Node.js v24.18.0 LTS "Krypton" (user-level tarball)

- **Why:** promptfoo spike (Step 9 roadmap) requires Node; host has none.
- **Why a tarball and not nvm:** nvm patches shell init files, which on
  this machine belong to the deploy-managed workstation-dotfiles repo -
  drift there gets hard-reset on the next `dotpush`. The tarball is one
  self-contained directory, needs no shell-config changes, and is used
  via explicit PATH per invocation.
- **Where:** `~/.local/opt/node-v24.18.0-linux-x64/`
  (**2.1 GB** - includes promptfoo's node_modules, see below)
- **Provenance:** https://nodejs.org/dist/v24.18.0/node-v24.18.0-linux-x64.tar.xz,
  31,511,588 bytes, sha256
  `55aa7153f9d88f28d765fcdad5ae6945b5c0f98a36881703817e4c450fa76742`
  verified against the release SHASUMS256.txt before extraction
  (download-integrity rule; tarball deleted after extraction).
- **How to use:** prefix commands with
  `PATH=$HOME/.local/opt/node-v24.18.0-linux-x64/bin:$PATH`
  (nothing auto-loads it).

## promptfoo 0.121.17 (global install inside the Node prefix)

- **Why:** eval-harness candidate; spike PASSED 2026-07-04 3/3 against
  llama-server's /v1 endpoint (PHASE-A-LOG entry + spikes/promptfoo-spike/).
- **Where:** inside the Node prefix above
  (`lib/node_modules/promptfoo`, `bin/promptfoo` symlink) - removing
  the Node directory removes promptfoo with it.
- **Side-effect dirs created by npm/promptfoo:**
  - `~/.npm` - npm download cache, **993 MB**. Safe to delete anytime.
  - `~/.promptfoo` - promptfoo eval history/state. Small; delete if
    promptfoo is abandoned, keep if adopted (it is the local eval DB).
- **Telemetry:** disabled at run time via env
  (`PROMPTFOO_DISABLE_TELEMETRY=1 PROMPTFOO_DISABLE_UPDATE=1`) - these
  are NOT persisted anywhere; set them in the harness wrapper when
  Phase B adopts promptfoo.

## Piper TTS 2023.11.14-2 (pre-built binary, user-level)

- **Why:** briefing v2 Part 3.3 TTS probe; pip absent on host
  (python3-pip in DEFERRED-ROOT.md) so the pre-built release binary
  was used per the briefing's fallback.
- **Where:** `~/sparkbench/piper/` (gitignored; ~90MB incl.
  onnxruntime + espeak-ng data) and `~/sparkbench/piper/voices/`
  (en_GB-alba-medium, 63MB).
- **Provenance (origin publishes no checksums - local sha256 at
  verified-fetch time IS the record, per download-integrity):**
  - piper_linux_x86_64.tar.gz: 26,460,462 B, sha256
    a50cb45f355b7af1f6d758c1b360717877ba0a398cc8cbe6d2a7a3a26e225992
  - en_GB-alba-medium.onnx: 63,201,294 B, sha256
    401369c4a81d09fdd86c32c5c864440811dbdcc66466cde2d64f7133a66ad03b
  - en_GB-alba-medium.onnx.json: 4,888 B, sha256
    aa965a2f02ecced632c2694e1fc72bbff6d65f265fab567ca945918c73dd89f4
- **Removal:** `rm -rf ~/sparkbench/piper` (self-contained).
- **Permanent option:** `pip install piper-tts` once python3-pip
  exists, if TTS becomes a service rather than a probe.

## whisper.cpp + stable-diffusion.cpp (source checkouts)

- **Where:** `~/sparkbench/whisper.cpp/`, `~/sparkbench/stable-
  diffusion.cpp/` (both gitignored; own upstream git histories).
  Vulkan builds, same stack as llama.cpp. Removal: delete the dirs.
- Whisper models (~2GB) live inside whisper.cpp/models/.

## Real-ESRGAN ncnn-vulkan v0.2.5.0 (pre-built binary, user-level)

- **Why:** E3 upscaler probe - completes the 1080p/4K image pipeline
  (FLUX native ceiling is 1536x864; upscaling covers the rest in
  seconds).
- **Where:** `~/sparkbench/realesrgan/` (gitignored, ~140MB with
  models). Removal: delete the dir.
- **Provenance:** release zip 46,931,474 B, local sha256
  e5aa6eb131234b87c0c51f82b89390f5e3e642b7b70f2b9bbe95b6a285a40c96
  (GitHub publishes no checksum - local hash at verified-fetch time
  is the record).

## Total current footprint

~3.1 GB, all under $HOME, zero system changes, zero shell-config changes.

## Removal (complete, verified paths)

```bash
rm -rf ~/.local/opt/node-v24.18.0-linux-x64   # node + promptfoo (2.1G)
rm -rf ~/.npm                                  # npm cache (993M)
rm -rf ~/.promptfoo                            # promptfoo state (only if abandoning)
```

## Make-permanent options (needs Alastair + sudo)

1. **apt:** `sudo apt install nodejs npm` - but Ubuntu 24.04 ships Node
   18/20-era packages; promptfoo wants >=18 so it works, yet the
   user-level v24 LTS is newer than apt's. Check versions before
   switching.
2. **NodeSource repo:** current LTS via apt with proper updates -
   the usual choice if Node becomes production infrastructure on this
   box (i.e. promptfoo is adopted for Phase B).
3. **Keep user-level (recommended until Phase B decides):** the
   tarball is pinned, hash-verified, and touches nothing - re-point
   PATH in the harness wrapper only. Tidy-up cost stays three rm -rf
   commands. TODO: revisit at Phase B harness decision.
   Why: promptfoo adoption is not yet decided; installing system-wide
   before that decision spends sudo on a maybe.
   Trigger: PHASE-A-LOG 2026-07-04 promptfoo spike entry + Alastair's
   user-level authorisation (this file's Overview).

## 2026-07-06 user-level pip installs (site + charts)
- markdown, matplotlib (superseded), plotly==5.24.1, kaleido==0.2.1 via `pip install --user --break-system-packages`
- Removal: `pip uninstall --break-system-packages plotly kaleido markdown matplotlib`; regenerate charts with tools/build_charts.py
- playwright (chromium, ~/.cache/ms-playwright) via pip --user, for static-site visual verification. Remove: `pip uninstall --break-system-packages playwright` + `rm -rf ~/.cache/ms-playwright`

## 2026-07-06 Kokoro TTS (podcast/narration audio engine)
- **Isolated venv** at `kokoro-tts/venv` (gitignored), NOT a user-level install - keeps the ~220MB engine off the system site-packages. Packages: kokoro-onnx, onnxruntime (CPU), phonemizer-fork + espeakng-loader (bundled espeak-ng, no sudo), soundfile, numpy.
- **Model** (gitignored `kokoro-tts/models/`, provenance in manifests/MANIFEST.md): kokoro-v1.0.onnx + voices-v1.0.bin, fetched + byte/sha-verified by `kokoro-tts/fetch_kokoro.py`.
- **Trap avoided:** `misaki[en]` (the alternative G2P) drags in torch + NVIDIA CUDA (~4GB, useless on this AMD box); kokoro-onnx phonemises via espeak, so the slim install omits misaki. Rebuild slim: `python3 -m venv --clear kokoro-tts/venv && kokoro-tts/venv/bin/pip install kokoro-onnx soundfile`.
- **Use:** `kokoro-tts/venv/bin/python tools/kokoro_tts.py podcast <script> <out.mp3> --host bf_emma --guest bm_george`.
- **Removal (needs no sudo):** `rm -rf kokoro-tts/` (venv + model together). Replaces the Piper podcast; Piper install (piper/, gitignored) still used for the "listen to this page" narrations.

## ROCm llama-server (added 2026-07-12)

`llama.cpp/build-rocm/bin/llama-server` now exists (built from the
F22/F23-provenanced ROCm tree; the web-UI assets required node/npm on PATH
- `~/.local/opt/node-v24.18.0-linux-x64/bin` - because the CDN fetch
fails; the npm fallback builds them). Serving-validated at 64K context
(F31): ~2x Vulkan prefill at depth, the long-document serving option.
Removal path: delete build-rocm/bin/llama-server + tools/ui artefacts;
the tree itself predates this (E18/F22).
