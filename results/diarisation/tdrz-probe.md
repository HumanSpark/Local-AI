# Diarisation probe 1: tinydiarize on synthetic 2-speaker audio - INCONCLUSIVE (2026-07-17)

# File: results/diarisation/tdrz-probe.md
# Purpose: First diarisation test. Result: 0/7 turns detected - but the fixture is the prime suspect.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: tinydiarize (small.en-tdrz) detected ZERO of 7 speaker changes on a clean synthetic
# two-speaker conversation. This is NOT reported as "tinydiarize does not work": the fixture is
# TTS-generated and almost certainly out-of-distribution for a model fine-tuned on real speech.
# The probe is recorded as inconclusive pending REAL multi-speaker audio. Investigation + the
# verified landscape: docs/plans/2026-07-17-diarisation-investigation.md.

## What ran

- Model: `ggml-small.en-tdrz.bin`, 487,614,184 B, upstream SHA256 verified on arrival, manifested
  before first use (MANIFEST.md). Ungated, MIT, rev d44ba793.
- Harness: the existing whisper.cpp Vulkan build, `whisper-cli -tdrz`. No rebuild, no new deps.
- Fixture: `twospeaker.wav` - 36.0s, 16 kHz mono, 8 turns strictly alternating between bf_emma
  (British female) and bm_george (British male), 0.35s gaps, built with Kokoro TTS. Ground truth is
  EXACT because we generated it: `twospeaker-truth.json` records every turn boundary to the
  millisecond. 7 true speaker changes.

## Result

**Transcription: excellent.** All eight turns transcribed essentially verbatim (small.en on clean
synthetic speech - unsurprising).

**Diarisation: 0 of 7 turns detected.** Read from the raw `speaker_turn_next` flag via
`--output-json`, not from console rendering:

| segment end | speaker_turn_next | true change here? |
|---|---|---|
| 4.38s | False | YES |
| 9.92s | False | YES |
| 14.24s | False | YES |
| 19.14s | False | YES |
| 23.02s | False | YES |
| 27.88s | False | YES |
| 32.30s | False | YES |
| 35.66s | False | (end) |

`main:` confirms `tdrz = 1` was active, so the feature was enabled. The mechanism is wired: whisper.cpp
suppresses the speaker-turn token (`token_solm = 50359`) only when tdrz is DISABLED, and it was not.
The model simply never emitted it.

**Negative control:** real single-speaker audio (`jfk.wav`) also returns `speaker_turn_next=False` -
correct behaviour, but it does NOT discriminate, since it is the same answer the fixture gave. A
control that returns the expected answer for both hypotheses tests nothing.

## Why this is INCONCLUSIVE, not a verdict on tinydiarize

The fixture is the prime suspect, and it is my fixture:

- **The audio is synthetic.** tinydiarize is a fine-tune of Whisper on REAL conversational speech.
  Kokoro TTS output is clean, studio-dry, and has no room tone, no breaths, no mic characteristics.
- **Each turn was synthesised in ISOLATION and concatenated.** There is no conversational prosody -
  no interruption, no anticipation, no cadence carrying across a turn boundary. The acoustic cues a
  turn-detector would key on may simply not exist in the signal.
- **The joins are digital silence**, not the acoustic texture of a real pause.

In short: I built an audio file that sounds like two people to a human, and may look like one
continuous clean speaker to a model trained on real meetings. **0/7 is at least as likely to be a
statement about the fixture as about the model**, and reporting it as "tinydiarize fails" would be the
same error class as this week's `--jinja` retraction - asserting a property of the system under test
from an instrument that was never validated.

**What the probe DOES establish**, independent of the fixture question:
1. The whole path works end-to-end with zero friction: ungated model, existing build, existing flag,
   provenance verified, ~40s to first result. The plumbing is not a barrier.
2. `--output-txt` silently DROPS the marker - it is console/JSON only (cli.cpp:441). Anyone scoring
   tdrz from the txt writer would measure zero turns forever and conclude the model is broken.
3. Transcription quality on small.en is fine for clean audio, which is not the interesting question.

## Next (in order)

1. **Get REAL multi-speaker audio.** Until then nothing here is decidable. Options: a public sample
   with a clear licence, or a genuine recording. This is the blocking step for the tdrz question.
2. **Ask Alastair for the HF token + pyannote terms acceptance** (QUESTIONS-FOR-ALASTAIR). pyannote is
   MIT but `gated: auto`, and it is the option that does speaker IDENTITY rather than turns - which is
   what meeting attribution actually needs. Our ROCm torch stack (torch 2.10+rocm7.13, Radeon 8060S)
   is already proven, so the path is short once ungated.
3. Re-run this probe against real audio before drawing ANY conclusion about tinydiarize.

Evidence: this file; results/diarisation/{twospeaker.wav,twospeaker-truth.json,tdrz-out.json};
manifests/MANIFEST.md (provenance); docs/plans/2026-07-17-diarisation-investigation.md (the verified
landscape, including pyannote's gating and the turns-vs-identity distinction).
