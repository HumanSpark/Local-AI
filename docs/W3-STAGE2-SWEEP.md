# W3 Stage-2 quality-first sweep - engine spike records

**Project:** sparkbench | **Date:** 2026-07-26 | **Plan:** quality-first sweep (supersedes the
WORKPLAN's T11-before-T13 order; see HANDOFF.md)

Per-engine viability spikes on sparkmax (gfx1151 / Radeon 8060S, ROCm 7.2.4). Each engine is stood
up from the cached `rocm/pytorch:rocm7.2.3` base, rendered on one shared 26-word line, and judged by
ear before any corpus work. Throughput is recorded because it falls out for free - **it is not the
selection criterion** (owner, 2026-07-26: *"quality of the speech has always been number one for me
... generation speed is secondary"*).

**The shared line** (`tts-bench/corpus/11-british-female-test.txt`, 26 words):
> The businesses that win with AI won't be the ones with the biggest budgets. They'll be the ones who
> understood the problem before buying the tool.

## Status

| Engine | Stood up | Renders | RTF | Quality verdict |
|---|---|---|---|---|
| Kokoro-82M (incumbent, CPU) | ✅ | ✅ | ~8-9x | **FAILED** (owner, by ear - all voices) |
| F5-TTS | ✅ | ✅ | 0.60x | not yet judged; **cc-by-nc, cannot ship** |
| Chatterbox (std, exagg 0.7) | ✅ | ✅ | 0.185x | not yet judged |
| VoxCPM2 | ✅ | ✅ | **0.140x** | not yet judged |
| Qwen3-TTS-1.7B-CustomVoice | ✅ | ✅ | 0.102x | not yet judged |
| Fish s2-pro | ✅ | ⚠️ | 0.044x | **BROKEN on this line** (F50) |
| CosyVoice3 | ✅ | ⚠️ | ~~0.242x~~ | **GARBLED - 'WORKING' RETRACTED** (F54 amendment) - all 5 renders unintelligible |
| MegaTTS3 | ❌ | ❌ | - | **DISQUALIFIED (F52)** - WavVAE encoder withheld; cannot clone our own audio |
| Zonos | ✅ | ❌ | - | **NOT VIABLE (F53)** - torch.compile fallback + `.to(cuda,bf16)` never completes |

**Correction, 2026-07-26 (F51): the PyPI routes recorded above for CosyVoice3 and Zonos were wrong
and neither was installed.** `cosyvoice` 0.0.8 is a third-party repackage (`lucasjinreal`) uploaded
2024-11-17, which predates CosyVoice 3 and therefore cannot be it; `zonos` 0.1.0.dev0 carries
unedited cookiecutter placeholders (author *"Your Name"*, home `github.com/yourusername/zonos`) and
declares `torch>=2.5.1`, the documented route to a CUDA torch evicting the ROCm build. **All three
remaining engines install from a git clone.** Licence was checked first because it is free and
instant, and F5 had already died on exactly that gate - all three clear, code and weights both
Apache-2.0:

| Engine | Code | Weights (HF) |
|---|---|---|
| CosyVoice3 | `FunAudioLLM/CosyVoice` | `FunAudioLLM/Fun-CosyVoice3-0.5B-2512` - note the `Fun-` prefix and `-2512` suffix; the guessed `CosyVoice3-0.5B` 401s |
| Zonos | `Zyphra/Zonos` (last push 2025-03-05, ~17mo stale) | `Zyphra/Zonos-v0.1-transformer`, `-hybrid` |
| MegaTTS3 | `bytedance/MegaTTS3` | `ByteDance/MegaTTS3` |

**Kokoro is fully rejected.** `bf_emma` and `bm_george` were rejected in July
(`results/audio-quality-verdict.md`); `af_heart` - documented in
`docs/kokoro-tts-tuning.md` as *"the most naturally emotive voice in the lineup"* and never
previously auditioned - was rejected by the owner on 2026-07-26. Its ~1 GPU-hour backfill cost is
therefore irrelevant: it is not a quality option at any voice.

## Per-engine records

### VoxCPM2 - `openbmb/VoxCPM2`, Apache-2.0

Stood up cleanly. **RTF 0.140x** (6.88s audio in 49.1s), model load 203.8s, peak 0.83 (healthy
signal). `pip install --no-deps voxcpm` + explicit deps; `pydantic` was the only missing transitive
dep, resolved in-container rather than by rebuilding.

**MEASUREMENT TRAP, caught before it was reported as a result:** VoxCPM's output sample rate is
**48000** (`voxcpm/modules/audiovae/audio_vae_v2.py:367 out_sample_rate: int = 48000`), not the 16000
first assumed from the encoder-side default on line 366. The first render was written at 16 kHz,
which made it play 3x too slow and produced a headline **RTF of 0.421x - 3x too fast**, plus a
nonsensical 1.26 words/sec. Corrected to 0.140x and 3.78 words/sec (normal speech) by reinterpreting
the same samples at 48 kHz. **Never infer an engine's sample rate; read it from the code.**

### Chatterbox - `ResembleAI/chatterbox`, MIT

**Use the STANDARD `ChatterboxTTS`, not `ChatterboxTurboTTS`.** Turbo explicitly ignores
`exaggeration` and `cfg_weight` (`chatterbox/tts_turbo.py`: *"CFG, min_p and exaggeration are not
supported by Turbo version and will be ignored"*), and our own July code
(`tools/chatterbox_tts.py:25`) imports the standard class at `exaggeration=0.7`, annotated in-source
as *"the approved 'expressive' setting"*. `results/audio-quality-verdict.md` credits exactly that
control for the delivery that beat Piper and Kokoro. **Turbo was fetched first by mistake (3.8 GB)
before the July code was checked** - a five-minute listen would have caught it sooner than a fetch
script did.

Blob reuse: `s3gen.safetensors` and `ve.safetensors` are byte-identical across the two repos (same
published LFS oids), so the standard fetch copies them from the Turbo download and re-verifies rather
than re-downloading (~1.06 GB saved).

Runtime trap: `resemble-perth`'s `PerthImplicitWatermarker` resolves to `None` in this environment;
the model cannot construct without it. Stubbed with a no-op - it is an optional perceptual watermark,
irrelevant to internal benchmarking. Load time **4.7s**, by far the fastest of any engine here
(Fish: 11-25 minutes).

### Fish s2-pro - BROKEN on this line (see F50)

Reproducible 47.5s / -48 dB non-speech, 3 renders of 3, returning HTTP 200 and a valid WAV.
Separately, **Fish's reference-cloning path is blocked on ROCm entirely**:
`Error in TTS generation: TorchCodec is required for load_with_torchcodec`. Fish's default-voice path
works (all nine Stage-1 excerpts rendered), but any reference/clone request needs torchcodec, which is
CUDA-linked and cannot load here. Fixable with the same soundfile monkeypatch used in the other
runners; not attempted.

### Qwen3-TTS - `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`, Apache-2.0

Full record in `tts-bench/results/qwen3-tts/RESULTS.md`. **No British female voice exists in this
checkpoint** - the two English-native timbres (Ryan, Aiden) are both male; the female timbres are
Chinese/Japanese/Korean natives. Unresolved bimodal RTF anomaly (14/18 at 0.1019, 4/18 at 0.2469) -
see that file's TODO; the fast arm resembles a batched path, which ties directly into the batching
lever below.

### CosyVoice3 - `FunAudioLLM/Fun-CosyVoice3-0.5B-2512`, Apache-2.0 - **NOT WORKING (retracted)**

> **RETRACTION (same day).** This section originally read "WORKING" with RTF 0.242x. An
> intelligibility gate then showed **every CosyVoice3 render was garbled** - WER 0.96 to 8.54,
> Whisper hearing "yes yes yes yes" and "it's it's it's". The RTF figure is real but measures
> the production of gibberish. Likely cause: casting the bf16 checkpoint's LLM to float32 to
> silence a dtype error, which suppressed the error and broke the numerics. See the F54
> amendment in docs/FINDINGS.md. The traps below are still accurate and still worth keeping.

Stood up 2026-07-26. **RTF 0.242x** (9.56s audio in 39.5s), model load 5.3s, 2.72 words/sec. Clones
transcript-free via `inference_cross_lingual(text, prompt_wav)`. Real output confirmed by direct
level measurement (mean -22.3 dB, peak -0.1 dB), not by exit code.

Five traps, and the ORDER they were hit matters because each one cost a run behind a 9.75 GB download:

1. **Its `requirements.txt` is unusable on this box and must not be used.** It carries an
   `--extra-index-url .../whl/cu121`, `torch==2.3.1` (would evict the ROCm build - trap #3),
   `onnxruntime-gpu`, and `tensorrt-cu12*`. Install the inference packages individually instead and
   keep the build-time torch gate as the backstop.
2. **`openai-whisper` is a HARD import** in `cosyvoice/cli/frontend.py`, and its sdist build needs
   `pkg_resources`, which setuptools 81 removed - so `pip install setuptools<81` must come first.
   Leave the whisper version unpinned; the pinned 20231117 is the release that needs the dead API.
3. **The dependency chain leaves CosyVoice entirely.** The flow decoder is
   `matcha.models.components.flow_matching.BASECFM`, i.e. the Matcha-TTS submodule, which brings its
   own deps (gdown, unidecode, phonemizer...). Because modules are instantiated BY NAME from yaml via
   hyperpyyaml + `pydoc.locate`, each missing one surfaces as a separate late
   `pydoc.ErrorDuringImport` from inside yaml parsing - not as an ImportError at the top.
4. **`prompt_wav` is a PATH, not a tensor.** The newer API renamed `prompt_speech_16k` -> `prompt_wav`
   and moved the load inside; passing a tensor yields
   `LibsndfileError: Error opening 'tensor([[...]])'`.
5. **CosyVoice3 REQUIRES a system-prompt prefix ending in `<|endofprompt|>`** (asserted at
   `cosyvoice/llm/llm.py:479`). The `<|en|>` language tag shown in the repo's own older example is
   **CosyVoice 1's** convention and does NOT satisfy it. Correct form:
   `inference_cross_lingual("You are a helpful assistant.<|endofprompt|>" + text, prompt_wav)`.
6. **The checkpoint is BFloat16 but the frontend emits float32 embeddings**, so the first matmul dies
   with `mat1 and mat2 must have the same dtype, but got Float and BFloat16`. `fp16=False` does NOT
   cover this - it selects the flow's precision, not the LLM checkpoint's dtype. Cast the LLM:
   `m.model.llm = m.model.llm.to(torch.float32)`.

**THE DIAGNOSTIC TRAP, and the transferable part.** CosyVoice runs its LLM in a worker thread
(`cosyvoice/cli/model.py` `llm_job`). Traps 5 and 6 BOTH raised inside that thread, and the exception
was **logged rather than propagated** - so the main thread carried on and built audio from ZERO
speech tokens, dying three modules later in HiFiGAN's `f0_predictor` as
`RuntimeError: Calculated padded input size per channel: (3). Kernel size: (4)`.

A precise, actionable assertion was converted into a bogus conv1d shape error far from the cause, and
two full runs were spent debugging a "shape bug" that never existed. **When a pipeline crashes on an
implausibly small tensor, grep the log for a WORKER THREAD traceback before believing the main one.**
This is `error-suppression.md` in the wild: a swallowed exception in a thread should fail the request,
not leak an empty result downstream.

### Zonos v0.1 transformer - `Zyphra/Zonos-v0.1-transformer`, Apache-2.0 - stood up, PERFORMANCE PROBLEM

Container builds clean and imports fine. Clones transcript-free via `make_speaker_embedding(wav, sr)`.
Use the **transformer** checkpoint, not the hybrid: the `compile` extra needs FlashAttention 2 (no
gfx1151 build, trap #2) and `mamba-ssm`, which only the hybrid requires.

**Unresolved: it runs on CPU, not the GPU.** Observed at 90-110% CPU with **0% GPU utilisation** for
15+ minutes on a single 26-word line. Decomposing `from_pretrained` proved model init is NOT the
problem - config resolve, construct (incl. DACAutoencoder), state-dict load and `.to(cuda)` total
**7.8s**. The time is downstream, in `make_speaker_embedding` / `generate`. Note the speaker model
(`Zyphra/Zonos-v0.1-speaker-embedding`) downloads separately and IS cached, so it is not a fetch stall.
Moving the model manually with `.to("cuda", bfloat16)` instead of letting `from_pretrained` do it
produced `Expected all tensors to be on the same device` inside `torchaudio`'s melscale filterbank
during speaker embedding - so the speaker-cloning path has its own device handling that must not be
second-guessed. **Measurement note:** on this APU the GPU shares system RAM, so `rocm-smi`'s VRAM
figure under-reports GPU residency - utilisation %, not VRAM, is the trustworthy signal.

## Three traps every remaining engine must handle by construction

All three have been seen for real on this box:

1. **torchcodec** links CUDA's libnvrtc and dies at import on ROCm (F5-TTS hit it on output; Fish hits
   it on reference input). Uninstall it and route `torchaudio.load/save` through `soundfile`.
2. **FlashAttention 2 has no gfx1151 build**, and several model cards recommend it. Pass `sdpa`.
3. **pip can silently resolve a CUDA/CPU torch over the base image's ROCm build** (chatterbox-tts
   hard-pins `torch==2.6.0`). Install with `--no-deps` + explicit deps, and keep the **build-time
   torch gate** that fails the build rather than invalidating a measurement.

Plus, from this sweep: **read the output sample rate from the code, never assume it.**

## 2026-07-26: the shared-line reel shipped, and the batching lever was DEFERRED behind it

**What changed.** The section below queued the batching lever as the next action. It was deferred,
deliberately, and the reasoning is recorded here because it contradicts a bolded instruction:

1. **Batching is a throughput test, and throughput is criterion #2.** The owner's recorded position
   is *"quality of the speech has always been number one for me ... generation speed is secondary"*,
   and that judging quality with most of the field untested is *"a damning indictment of the
   process"*. The quality-first plan change that same day set the order as
   *stand up -> render the shared line -> whole field audible in ONE batch -> owner scores -> full
   corpus and throughput ONLY for survivors*. Batching-first contradicts that amendment.
2. **Judged first, the batching work gets SCOPED.** Batch-testing three engines before knowing which
   survive an ear test risks measuring two engines that get rejected anyway.
3. **It cost minutes, not an hour.** Every arm was already on disk from the viability spikes, so the
   reel needed no GPU and no engine re-stand-up.

**Shipped:** `tts-bench/listening/w3-shared-line-reel.mp3` (2:04), built by
`build_ab_reel.py --takes tts-bench/arms-shared-line.json`. Five takes, honestly counted as **three
shippable candidates** - Chatterbox (MIT), VoxCPM2 (Apache-2.0, never previously auditioned),
Qwen3-TTS (Apache-2.0) - plus rejected Kokoro as a reference floor and cc-by-nc F5 as the quality
yardstick, both labelled as such *in the audio*. Fish excluded (F50).

**The arm manifest is tracked** so what was compared and what was omitted survive the session, and
`build_ab_reel.py` now **level-gates every arm before building** - anything under -40 dB mean aborts
the run. Verified against the real failure: the F50 Fish render (-48.5 dB) is refused and no file is
written. That makes `comparison-integrity` rule 6 structural rather than remembered.

**Incidental, and it resolves a duration outlier:** F5's 1.87 words/sec is **three long internal
pauses** (1.51 + 1.38 + 0.97s), not slow speech - net of them it reads ~2.6 w/s, normal. Chatterbox
has *zero* internal pauses and reads the 26-word line in 5.4s continuous (4.81 w/s, ~1.5x normal
pace), which is audible and may itself be a quality judgement. Per-arm measurements:

| Arm | Mean level | Duration | Words/sec |
|---|---|---|---|
| Kokoro af_heart (rejected anchor) | -22.7 dB | 8.0s | 3.23 |
| Chatterbox | -17.6 dB | 5.4s | **4.81** |
| VoxCPM2 | -22.3 dB | 6.9s | 3.78 |
| Qwen3-TTS Ryan | -21.6 dB | 9.7s | 2.69 |
| F5-TTS (yardstick) | -16.9 dB | 13.9s | 1.87 (2.6 net of pauses) |
| ~~Fish s2-pro~~ | **-48.5 dB** | 47.5s | - (gate-refused) |

The 5.4 dB raw level spread across arms is why loudness normalisation is load-bearing rather than
tidy: unnormalised, the reel would measure output gain.

## 2026-07-26 (later): the field is THREE CLONING ENGINES, so the voice is an INPUT

**The reframe that changes the benchmark.** With Kokoro rejected, Fish broken (F50) and Qwen3-TTS
eliminated by the female-only rule (its only two English-native timbres, Ryan and Aiden, are both
male), every remaining candidate - Chatterbox, VoxCPM2, F5-TTS - is a voice-CLONING design. Their
voice is not a property of the engine; it is a reference clip we supply. Three consequences:

1. **The earlier verdicts were partly verdicts on the wrong thing.** "VoxCPM2 too bland, need a
   different voice" judged the default/zero-shot voice, not the engine. Each arm in that reel had a
   DIFFERENT voice, so engine quality and voice choice were confounded.
2. **The correct design holds voice constant and varies the engine.** Every render from here uses
   one shared reference clip.
3. **The reference clip became the blocking decision** and was asked (`AskUserQuestion`). Owner
   chose "I source a licensed clip" over supplying one or cloning a synthetic voice - the latter
   mattering because `chatterbox-tts/refs/emma-ref.wav`, used for the July podcast, has **no
   provenance record anywhere in the repo** and its name suggests it is a Kokoro `bf_emma` render,
   i.e. a synthetic reference from an engine since rejected.

**Two voice tracks now run in parallel** (owner: *"I am superseding the female only rule for ME and
ME only"*):

| Track | Reference | Status |
|---|---|---|
| British female narrator | VCTK, CC BY 4.0, 8 English-accented female speakers - the whole set | auditioned; **no winner yet**. If none lands, the answer is a different corpus, not another speaker. |
| Owner's own voice | his podcast, "Go-To Expert" episode | clips ranked by him: 975.9s > 553.2s > 859.9s > 144.7s, *"all pretty decent"* |

### The accent/pace coupling - the session's live hypothesis

Cloning the owner's voice with Chatterbox: at `cfg_weight=0.5` the pace was too fast; at
`cfg_weight=0.3` the pace improved and **the accent went American** (owner: *"suddenly my voice has
an American accent, not my neutral accent"*).

**`cfg_weight` is classifier-free-guidance strength, so it is simultaneously the pace control AND
the accent-fidelity control, and they pull in opposite directions.** Lowering it slows delivery by
loosening adherence to the reference - which is exactly what lets Chatterbox's overwhelmingly
American training prior reassert itself. Slowing via `cfg_weight` therefore CANNOT preserve accent.

**The decoupling:** hold `cfg_weight` high (accent-faithful), then slow the render afterwards with a
pitch-preserving time stretch (`atempo`). Measured: cfg 0.5 -> 3.99 w/s, +atempo 0.85 -> 3.12 w/s;
cfg 0.7 -> 4.04 w/s, +atempo 0.82 -> 3.10 w/s. **Awaiting the owner's ear** - the hypothesis is
unconfirmed until he says the accent survived, and is NOT recorded as a finding until then.

Cross-engine control, voice held constant on the same reference: Chatterbox 3.99 w/s vs VoxCPM2
3.69 w/s (RTF 0.095x). If one holds the accent and the other does not, that is an engine property.

### Reference-clip tooling, and four bugs it surfaced

`stage2-sweep/fetch_refvoice.py` (VCTK, licensed) and `stage2-sweep/extract_ref_clips.py` (clean
clips from long recordings). Both committed; provenance in `manifests/MANIFEST.md`. The bugs are
the transferable part, and three of the four were SILENT:

- **Off-by-one speaker metadata** - read from `rows[0]` of a window spanning two speakers. Caught
  only because the female-only rule made a male result impossible to miss. The audio was fine
  (byte-identical sha256 across the re-fetch), but the code could have mixed two speakers into one
  reference clip.
- **Clipping tested by peak level** - a mastered podcast is limited to ~0 dBFS deliberately; the
  episode measures peak +0.71 dB with astats **flat factor 0.000000**, i.e. zero distortion. The
  peak screen would have rejected the entire episode. Flat factor is the real test. (Needs `-vn`:
  podcast MP3s carry an mjpeg cover-art stream that astats analyses instead.)
- **Index-based clip filenames are not identities** - changing the screen re-ordered the picks, so
  `uk-audio2_clip1.wav` silently became a DIFFERENT segment *after the owner had approved clip 1 by
  ear*. Clips are now named by source offsets.
- **The sidecar was overwritten** per run, discarding the previous recording's offsets and hashes.

**Two things no automated screen caught, both found by ear:** audience clapping in one recording
(broadband and sustained, so it reads as speech), and a female voiceover intro on the podcast
(clean, well-levelled speech in the wrong voice - the one thing a reference must never contain,
now excluded with `--skip-start`).

## 2026-07-26: own-voice track PARKED, narrator track reframed

**Own voice: closed as not achievable zero-shot (F54).** Four architecturally-distinct engines,
one shared reference clip the owner picked himself, all rejected on accent - *"None of the cloned
versions of my voice work. All too American"*. Settings were not the cause and that was tested, not
assumed (cfg sweeps, pace/guidance decoupling, F5's native speed, zero-shot-with-transcript, and an
explicit "speak with an Irish accent" instruct). Owner's call: park it, finish the narrator.

**THE REFRAME that should have come earlier.** The narrator candidates were being auditioned as RAW
CORPUS RECORDINGS, but a corpus clip is only the *reference* - what ships is the reference cloned
through an engine. So "find the perfect British female recording" was the wrong question; the right
one is "does this reference, cloned, sound good?". Both are now delivered as PAIRS (human reference,
then the clone) in `tts-bench/listening/narrator-cloned.mp3`.

The accent risk does **not** transfer from F54: English accents are abundant in TTS training data
where Irish is not, so the drift that killed the own-voice track is not predicted for the narrator.

CosyVoice3 zero-shot, using the VCTK **real transcripts** carried in the reference sidecars (not an
ASR guess):

| Reference | Owner's raw-audio rank | Clone duration | Words/sec | RTF |
|---|---|---|---|---|
| p233 Staffordshire (SNR 27.7 dB) | 2nd | 9.80s | 2.65 | 0.221x |
| p239 SW England (SNR 20.9 dB) | **1st** | 9.60s | 2.71 | 0.248x |
| p239 **denoised** (afftdn) | - | **5.28s** | **4.92** | 0.195x |

**An internal control caught a real defect, and it vindicates a warning made before the fact.** Two
clones of identical text from two different references agree within 2% (9.80s vs 9.60s). The clone
from the DENOISED reference is **45% shorter**. Denoising had improved the measured SNR from 20.9 to
49.4 dB while gating the quiet passages to a **-inf noise floor** - flagged at the time as an
artefact rather than a win, because no real recording is digitally silent between words. It did not
merely fail to help: **it produced a materially degraded clone.** The metric said "cleaner", the
control says "worse".

**Transferable:** when judging a processing step by a quality metric, add a downstream control that
uses the output for its actual purpose. Here, "same text, same engine, different reference" turned an
inaudible regression into a 45% duration gap that needed no listening to detect.

## The batching lever (still open, now scoped to survivors)

**Rationale (F49).** Throughput is set by autoregression (~150 sequential passes) x model size,
costing ~3000x, against a ~35x GPU advantage. At **batch=1 an autoregressive model wastes essentially
all the GPU's width** - thousands of tiny sequential dependent ops. Batching posts or sentences should
scale near-linearly on the SAME hardware.

**Why it was argued to come first** (superseded above, kept because the argument is still half-right -
it applies once there ARE survivors): if batching delivers 5-8x, it changes
the viability verdict for **every AR engine already tested** - Qwen goes 0.102x -> ~0.5-0.8x, Chatterbox
0.185x -> ~1x+. That would move the whole field from "not viable for the backfill" to "viable", and it
would do so without a single new engine. Standing up three more engines at batch=1 measures the wrong
thing three more times.

**Test plan (cheap, ~1 hour):**
1. Qwen3-TTS first - it exposes batch inference natively (`generate_custom_voice` accepts a LIST of
   texts, with per-item `language`/`speaker`). Render the 9-excerpt corpus as ONE batched call and
   compare total wall time against the recorded per-excerpt sum (metrics.json).
2. If it scales, repeat for Chatterbox and F5 (drive them with batched inputs).
3. Resolve Qwen's bimodal RTF at the same time - log generated token/chunk counts (its runner logs
   neither, which is why it could not be settled in-run).

**Then** resume the engine sweep (CosyVoice3, MegaTTS3, Zonos) with batching applied from the start,
and deliver ONE batched listening reel - N arms, N engines, stated honestly (see the fleet rule
`comparison-integrity.md`).

## 2026-07-27: every spike/audition file in this sweep, audited and renamed

All 226 test/benchmark audio files this document describes - every engine spike, VCTK speaker
audition, own-voice clone, denoise experiment, and comparison reel across `stage2-sweep/out/` and
`tts-bench/listening/` - were audited and renamed to carry their verdict in the filename
(`<original>__<VERDICT-TAG>__<reason>.<ext>`). Nothing was deleted. Narrative with real examples per
engine: `docs/w3-audio-audit-report.md`. Full old-name/new-name mapping: `docs/w3-audio-rename-log.csv`. This document itself names no bare
filenames, so nothing here needed updating - but `docs/FINDINGS.md` and
`tts-bench/results/narrator-batch-report.md` both quote captured log output using pre-rename names
(`cb_tra_a`, `ctl_docs_zh`, etc.); those are annotated in place rather than rewritten, since the
quoted text is the original evidence.
