# Release Notes - sparkbench-data-r5.14

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.14)

- **Findings:** 195 in FINDINGS.md, newest F195.
- **Claims:** 60 active in claims.yml.
- **README: what production runs now covers speech too.** The section gains a table of all three production jobs:
  the language model (unchanged), speech to text (Whisper large-v3-turbo with voice-activity detection and
  host-versus-other tagging, since 18 July 2026, F44-F46) and text to speech (Chatterbox cloning VCTK speaker p239,
  since 1 August 2026, F56; Kokoro bf_emma as the opt-in fallback).
- **New page VOICES.md with eleven audio samples** in `voices/`: the two VCTK reference recordings, the production voice
  (a short take and the 68-second sample that closed the narrator search), the runner-up voice, VoxCPM2's clones of
  both voices, Kokoro bf_emma, and one garbled CosyVoice3 render (F55). Most read the same line. F5-TTS and Fish
  s2-pro samples are not published (licence). The VCTK CC BY 4.0 attribution is on the page.
- **VOICES.md documents how numbers, dates and symbols are written out before speaking**, with a before/after pair
  in the production voice (samples 10 and 11): Chatterbox does no number handling, and the Whisper intelligibility
  check cannot see a misread number. Ships the rewriter `tts-bench/speakable.py` and its 183 tests,
  `tests/test_speakable.py`.
- No finding, claim or evidence file changes.

## Changed claims (old -> new)

- (none.)

## Retracted claims

- (none.)

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
