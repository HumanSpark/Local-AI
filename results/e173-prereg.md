<!--
# File: results/e173-prereg.md
# Purpose: Pre-registration for E173 - three open-weights song generators (YuE2, MiniMax Music 3, ACE-Step 1.5) on benchhost, one engine, one ruler.
# Project: sparkbench | Date: 2026-11-23
#
# Overview: Owner 2026-11-23 asked to benchmark the models in songcreator.pro's "YuE2 vs MiniMax Music 3" article
# (vendor piece: the publisher sells a YuE2 app; its only numbers are YuE2's own model card). Owner choices the same
# day: three arms (adding ACE-Step 1.5 as the reference the article's table also scores); ruler = runs on gfx1151 +
# speed + memory + lyric WER + the owner's blind listening; client-facing from the start. STATUS: FROZEN 2026-11-23 (A1). A throwaway
# spike (below) decides go/no-go per arm; predictions freeze after the spike and before any scored render.
# Box work is HELD while the owner's security audit runs on benchhost (2026-11-23) and behind the E172 IM re-run.
-->

# E173 PRE-REGISTRATION (DRAFT) - can this box write a song?

## In plain English

Three free music models now write whole songs, with vocals, from lyrics and a style description. The one we were
pointed at says it beats the others, but its maker wrote the test. We run all three on our own machine, on the
same software, with the same five songs to write. We time them, check whether a speech recogniser can make out the
words, and Alastair listens to every result without knowing which model made it.

## Axis and arms

The axis is the MODEL. Engine, backend, precision class, prompts and seeds are held fixed, so three arms differ only
along it. Quantised variants, if run, are variants of an arm and never count toward N.

| Arm | Model | Weights (audio.cpp GGUF) | Licence |
|---|---|---|---|
| YU | YuE2-3B (m-a-p, 2026-09) | `audio-cpp/Yue2-3B-GGUF` `yue2-3b-bf16.gguf` (7,261,484,576 B) + `yue2-vae-f32.gguf` (530,537,760 B) | CC BY-NC 4.0 + individual-creator permission |
| MM | MiniMax Music 3 (2026-08) | `audio-cpp/MiniMax-Music3-GGUF` BF16 mix: `language_model_bf16`, `rvq_depth_decoder_bf16`, `transformer_bf16`, `condition_encoder` | MiniMax-Music3 Community License (UI attribution; >US$20M revenue needs written approval) |
| AS | ACE-Step 1.5 Turbo (2026-01) | `audio-cpp/audio.cpp-gguf` (rev `8aa1ea47`) `ACE-Step1.5-GGUF/turbo/ace-step-1.5-turbo-bf16.gguf` (10,090,406,336 B, lfs sha256 `7aa8cc911bb7e476...`); a Q8_0 exists and is not used | MIT |

- **Engine:** audio.cpp (`0xShug0/audio.cpp`, ggml), newest release at spike time, built from source here; exact
  commit recorded. Its README lists Ubuntu backends CPU, Vulkan and HIP/ROCm ("test"). The official PyTorch paths
  are CUDA-only by their cards; they are not arms.
- **Backend:** whichever of HIP or Vulkan passes the spike for ALL three; if they split, the arm's backend is named
  beside every figure and that is a limit, not a hidden variable.
- **Precision:** BF16 for every arm. Memory is not the constraint on a 128 GB box,
  so quantisation is removed as a quality confound. Revision pins (HF API `sha` + per-file sha256) go into
  manifests/MANIFEST.md before first use.
- **Not arms:** Suno v6 and MiniMax Music 2.6 (closed); MiniMax's hosted API (closed to new users 2026-08-20);
  YuE2 best-of-8 (picks 1 of 8). Note even the card's "standard" YuE2 row (PER 8.44%) keeps the lower-PER of two
  candidates (card line 353); every arm here gets ONE render per prompt and seed, so YU is not compared on that row's terms.

## Spike (throwaway, go/no-go only)

Scratch directory, no commit. Per arm, in order of what disqualifies fastest:
1. audio.cpp builds with HIP (gfx1151), and separately Vulkan.
2. One 30 s lyric song renders to completion without DeviceLost, oops or `-ENOMEM` (F198: `gpu_settle` before every
   start; kernel log unreadable as bench, so watch engine stderr and `/var/crash`).
3. The file is music with a voice: LISTEN to it, and measure its level directly (RMS / LUFS), never by duration or an
   exit code (F44/F50: a well-formed WAV was a -48 dB noise floor).
An arm that fails 1-3 on both backends is reported as eliminated, with the reason; that elimination is a finding.

## Spike results (2026-11-23 13:08-13:52Z, throwaway; audio.cpp v0.9.6 `04a37f2`, relay window, F198 settle each start)

Same test verse, seed 7, ~30 s request. wall = render incl. model load; level by ffmpeg ebur128; words by whisper
large-v3-turbo (CPU). No new `/var/crash` entry; relay restored 13:52Z, production probe (code) passed on retry.

| Arm | Backend | rc | Audio s | Wall s | Peak GTT over base MiB | Integrated LUFS | Lyrics heard |
|---|---|---|---|---|---|---|---|
| YU | Vulkan | 0 | 39.9 | 82.2 | 6,268 | -15.1 | all lines ("ooh" intro) |
| MM | Vulkan | 0 | 30.0 | 540.6 | 16,308 | -14.8 | verse + first chorus line; cut by the 30 s frame budget |
| AS | Vulkan | 0 | 30.0 | 47.6 | 10,955 | -11.1 | all lines, two words misheard |
| YU | HIP | 0 | 39.8 | 44.0 | 7,455 | -13.9 | all lines |
| MM | HIP | **124 (30 min timeout)** | none | 1,800 | 16,831 | - | GTT flat at 9,867 MiB for 28 min after "CUDA graph warmup"; no output |
| AS | HIP | 0 | 30.0 | 18.6 | 12,593 | -12.6 | all lines but the last word |

**Spike decisions (before the freeze):**
1. **Backend = Vulkan** for all three (the only backend all three pass). HIP is faster for YU (1.9x) and AS (2.6x), but MM
   does not finish on HIP; that failure is a finding, reported with the results, not a hidden variable.
2. **MM's `duration_sec` must exceed the target length** (it is a frame budget, not a duration): scored renders request
   `duration_sec` = the lyric's target + 30 s and record the delivered length.
3. **MM at BF16 on Vulkan runs ~18x real time** (RADV reports `bf16: 0`). A ~90 s song is ~27 min; five songs ~2.3 h. Kept
   at BF16 (precision rule); a Q8 variant could be a labelled variant later, never an arm.
4. **P1 is settled by the spike** (YES on Vulkan) and **P3's MM half is no longer a forecast** (the spike measured it): both
   are reported as spike observations, not scored predictions. P3's YU half and P2, P4-P6 remain forecasts.

## Workloads (scored)

- **Five prompts** (amended 2026-11-23, owner: use HumanSpark frameworks, humanspark.ai/frameworks, as the song
  content; prompt injection and "human review" excluded by the owner). Owner picked FIVE frameworks 2026-11-23:
  **Butler vs Advisor**, **The Verification Dial**, **The Pipeline Problem**, **The Boring AI Manifesto**, **The
  Amplification Problem**. One song each, one style each, genres all different, vocals three female and two male;
  English, verse/chorus, target ~90 s, keeping each framework's exact names and step labels. Lyrics drafted by
  sparkbench, APPROVED OR REWRITTEN BY THE OWNER before any render (his IP, client-facing). Prompt file and its
  sha256 frozen with the predictions. 3 arms x 5 = 15 renders.
- **YuE2 licence decision:** **Owner decision 2026-11-23: YuE2 stays as an INTERNAL-ONLY test arm.** It is run and scored, its audio is never published or played outside the owner's own review, and reports mention it only as speed and intelligibility figures. This reads the licence's "commercial use of the model weights by companies" narrowly; that judgement is the owner's.
- **Publication limit:** the winning renders feed a separate SparkForge video demo (not part of this experiment).
  YuE2 output is CC BY-NC and HumanSpark is a company, so YU renders are scored here but never published.
- Each arm renders each prompt once, seed 7, engine defaults otherwise (each model's documented recommended
  sampling), idle box (relay window `idle-down`), one engine at a time.
- **Lyric WER:** `ggml-large-v3-turbo` (`/opt/models/staging/whisper/`, already pinned) transcribes each render;
  word error rate against the requested lyrics with `tts-bench/check_intelligibility.py`'s normalisation. Sung
  vocals over a mix are far harder for ASR than speech, so WER is RELATIVE between arms on the same prompts, and a
  reject signal, never proof a song is good.
- **Owner listening:** the 15 renders, loudness-normalised to -16 LUFS, labelled A/B/C per prompt with the mapping
  shuffled per prompt (`tts-bench/build_listening_set.py`), about 23 minutes. Per prompt: rank 1-3, plus "would you
  use this" yes/no. Mapping sealed in the repo before he listens.

- **Key teaching phrases (owner review 2026-11-23, added before freeze):** whole-song WER can hide a reversed lesson (the
  Verification Dial hook without "not" barely moves WER). Each song gets a short list of key phrases frozen with the
  prompt file (e.g. "It ran is not it worked"). Field `<arm>.key_phrases_heard`: phrases the recogniser transcribes
  exactly, per song. Any key phrase not heard exactly triggers a mandatory human listen of that line, recorded as
  heard / misheard / reversed; a reversed key phrase marks that render unusable regardless of WER.
- **Listening sheet asks two separate questions** per song: blind rank, and "would you actually play this to a room?"
  (a blind favourite can still be unusable).
- **Workshop pilot (outside the scored fields):** The Verification Dial is the first workshop pilot. After the blind
  ranking, its winning track is played to someone who has not seen the framework card, then asked: "The system says an
  invoice was paid. What would you check?" Their answer decides whether the next four videos get made.

## Scored fields

- `<arm>.spike.renders`: yes/no per backend (spike notes, transcribed into the results file).
- `<arm>.rtf_median`: median of wall seconds / audio seconds over the five renders, model load excluded, warm.
- `<arm>.load_s`: cold model load to first-request-ready.
- `<arm>.peak_gtt_mib`: max `mem_info_gtt_used` sampled every 1 s during renders, minus the window-open baseline.
- `<arm>.wer_median`: median lyric WER over the five renders.
- `<arm>.owner_rank1`: count of prompts where the owner ranked the arm first; `<arm>.owner_use_yes`: count of yes.
- `<arm>.key_phrases_heard`: key phrases transcribed exactly, out of the frozen list; human-listen verdicts beside it.

## Predictions (FROZEN 2026-11-23 by A1, each names its field)

1. **P1 all three run here on one ggml backend.** `YU/MM/AS.spike.renders` = yes on a shared backend.
2. **P2 ACE-Step is fastest.** `AS.rtf_median` < both `YU.rtf_median` and `MM.rtf_median` (its card: a full song in
   under 10 s on an RTX 3090).
3. **P3 the 5090 figures do not hold here.** `MM.rtf_median` > 1.389 (audio.cpp card, BF16, 5090) and
   `YU.rtf_median` > 0.2688 (audio.cpp card, BF16 + F32 VAE, 5090).
4. **P4 MiniMax sings the words most clearly.** `MM.wer_median` is the lowest of the three (YuE2's own table:
   MiniMax Music 3 phoneme error 6.27% vs YuE2 8.44% standard; the only cross-model intelligibility figure published).
5. **P5 the vendor's quality ranking does not survive a blind single-render test.** `YU.owner_rank1` is NOT strictly
   the highest of the three (YuE2's card puts it first on SongBench, but with best-of-8 and its own benchmark).
6. **P6 memory is not a constraint.** every `<arm>.peak_gtt_mib` < 32,768 at BF16.

## Limits known now

- The only published cross-model numbers come from YuE2's team (WildSongBench); MiniMax published none for Music 3.
- audio.cpp is a community port. A slow or poor arm may be the port, not the model; where a model's own runtime
  could run here, that is a follow-up arm, not a silent substitution.
- Five prompts, one render each, one listener: a one-prompt difference is not evidence. The listener is the owner,
  who knows the models exist but not the mapping.
- WER on sung lyrics is noisy (above). Musicality has no automatic ruler here; the owner's ranking is the only one.
- Licences differ (table). Any published sample carries its model's licence terms; YuE2 outputs are fine for an
  individual creator, not for a company without a licence.

## Procedure guards

- Relay window via `relay_bench_window.sh idle-down`/`up`, production probe after `up` (HARNESS-RULES).
- F198: GTT back to the window baseline before each engine start.
- Bank both sides: commit + push before the first render and after each arm.
- Downloads via the pinned fetch path, sha256 on arrival, MANIFEST row before first use.

## Amendments

**A1 (2026-11-23, before any scored render) - freeze on the DRAFT lyrics.** Owner 2026-11-23: "run 173 from your draft
lyrics please. Don't worry about my versions, just run it." So:
1. **Prompt file:** `results/e173/prompts.json`, sha256 `cc582713dc24edb2ba2e2118fce5d9d2d02162a21297ecf0d3a3dcc2fdcf0420`,
   extracted unchanged from `results/e173/lyrics-draft.md` (styles and lyrics). The owner's rewritten sheets are NOT
   used; if they arrive later they are a second round, not a replacement of this one.
2. **Key phrases (frozen in the prompt file):** S1 "Butler or Advisor", "pick by task, not by flair", "Sycophancy Trap";
   S2 "Turn the dial", "It ran is not it worked", "Errors reset it"; S3 "Junior work is how people become senior",
   "Cut the drudgery, keep the core"; S4 "The most valuable AI work is boring", "Dependable first", "Clever later";
   S5 "Garbage in, garbage out", "Output's capped by what you put in". "Is the money in the bank?" is in the owner's
   version, not the draft, so it is not checked.
3. **Length target 90 s -> 120 s.** Each draft is two verses, two choruses and a bridge (147-195 words), which does not
   sing in 90 s. AS `--duration-seconds 120`; MM `duration_sec=150` (frame budget = target + 30 s, spike decision 2);
   YU has no length option and runs as long as its lyric. Delivered length is recorded per render.
4. **Prompt mapping per arm:** YU `style="English, <style>"`; MM `--text "A song with <style>."`; AS `--text "<style>"`.
5. **`load_s`:** the CLI loads and renders in one call; `load_s` is taken from audio.cpp's own `--log-file` timing if it
   reports a load phase, otherwise reported as not separable and `rtf_median` is computed on wall time INCLUDING load
   (stated beside the figure).
6. **Runner:** `tools/run_e173_renders.sh` (Vulkan, seed 7, one window, F198 settle, 90 min timeout per render).
7. **Ordering:** runs after E174 (no disk I/O beside E174's 104 GiB loads).

**A2 (2026-11-24 ~01:15Z, BEFORE the key was opened) - no owner ranks; rank fields void.** The owner returned the
listening page with "would play to a room" ticks and no ranks (`results/e173/owner-answers-1.txt`, e48cfe97), and when
asked chose "score room ticks only" over adding ranks. So: `<arm>.owner_rank1` is VOID and **P5 is UNSCORED** (not
held, not falsified). `<arm>.owner_use_yes` is scored from the room ticks. Blinding limit recorded with the gate:
ACE-Step renders are always 120 s and the player shows length, so the room ticks are not fully blind for that arm.
Everything else (P1-P4, P6, WER, key phrases) unchanged.
*Note added AFTER unsealing (2026-11-24 ~01:25Z), not an amendment:* the owner then said the rank dropdown did not
work for him, so no ranks was a page defect, not a choice; and S4 take C (MiniMax) failed to play in the viewer (file
verified intact). See `results/e173/owner-notes-1.md`.
