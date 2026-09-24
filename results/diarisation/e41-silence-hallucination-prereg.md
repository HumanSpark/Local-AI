# PRE-REGISTRATION: when does Whisper invent speech out of silence? (2026-07-17)

# File: results/diarisation/e41-silence-hallucination-prereg.md
# Purpose: Predictions registered BEFORE the silence-hallucination benchmark runs.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E40 found whisper large-v3-turbo fabricates speech over silence on a real client call
# (120s of dead air -> four "Thank you" segments; a 180s clip -> six fabrications including "I'm
# going to go to the next meeting with Marina and Claire"). That was an incidental discovery on one
# recording. This benchmark asks the questions that make it a FINDING rather than an anecdote: is it
# reliable or sporadic? What triggers it? Does it depend on model size, silence type, duration, or
# position? Does VAD actually eliminate it, or just reduce it?

Why: transcription is a production capability of this box (published at 28x real time since Phase A)
and it is the input to the diarisation stack. A system that INVENTS SPEECH is a correctness failure,
not an accuracy one - a wrong speaker label is visible to a reader, fabricated speech is not.
Trigger: E40's incidental discovery + Alastair (2026-07-17): "I have noticed it with some frontier
labs where their transcriptions hallucinate 'thank you' occasionally" - i.e. the suspicion that this
is a WHISPER-FAMILY property, not a sparkmax artifact.

## Background: why "Thank you" specifically

Whisper was trained on ~680k hours of weakly-supervised web audio, much of it YouTube with
uploader-supplied captions. "Thank you", "Thanks for watching", and "Subscribe" are the most
over-represented phrases in that corpus's tail, and they systematically co-occur with LOW-INFORMATION
audio (outros, music beds, silence). The decoder is autoregressive with no acoustic "emit nothing"
token - given a segment it MUST emit something. **Prediction of the mechanism: on silence, the
decoder falls back to its unconditional prior, and that prior is YouTube outro boilerplate.**

This is a mechanism hypothesis, to be TESTED below, not asserted. If it is right, the fabricated
text should be drawn from a small, recurring, YouTube-flavoured set rather than being random.

## Method

Synthetic fixtures built with numpy/soundfile at 16 kHz mono. Every condition is generated, so
ground truth is EXACT: we know precisely which regions contain no speech, because we made them.
Real speech (`whisper.cpp/samples/jfk.wav`, 11s) is used as the speech anchor where a condition
needs one. Scored by counting segments whose time range lies entirely inside a known-silent region.

Conditions:
- **Duration**: 5, 10, 30, 60, 120, 300 s of silence.
- **Silence type**: digital zero; low-level white noise (-60 dBFS); "room tone" (-45 dBFS pink-ish).
- **Position**: silence-only (no speech at all); leading (silence -> speech); trailing (speech ->
  silence); sandwiched (speech -> silence -> speech).
- **Model**: large-v3-turbo (production) vs small (is this size-dependent?).
- **VAD**: off vs on (does it eliminate or merely reduce?).

## Predictions (registered BEFORE any run)

| ID | Prediction | Rationale |
|---|---|---|
| **S1** | **Pure digital-zero silence with NO speech anywhere produces ZERO or near-zero hallucination** | With no context at all, whisper's no-speech probability should fire. The E40 case had real speech BEFORE the silence - I suspect the fabrication is CONDITIONED on prior context, not on silence alone. This is the prediction I am least sure of and the most interesting either way. |
| **S2** | **Silence AFTER speech (trailing/sandwiched) hallucinates MORE than leading silence** | E40's case was silence after an opening line. Whisper carries a text prompt from the previous window; with speech in context the decoder has something to continue. |
| **S3** | **Hallucination rate scales with silence DURATION** | More 30s decode windows = more chances. Roughly linear in the number of windows. |
| **S4** | **Low-level NOISE hallucinates MORE than digital zero** | Digital zero is trivially detectable as non-speech; faint noise is ambiguous and may be decoded as very quiet speech. |
| **S5** | **The fabricated text is drawn from a SMALL RECURRING SET dominated by "Thank you" / "Thanks for watching" / similar** | The YouTube-prior mechanism above. If instead the text is varied and content-like, the mechanism hypothesis is WRONG. |
| **S6** | **`--vad` reduces hallucinated segments to ZERO in every condition** | VAD removes non-speech before the decoder ever sees it. If any survive, VAD is a mitigation rather than a fix - a materially weaker claim than E40 made. |
| **S7** | **small hallucinates MORE than large-v3-turbo** | Weaker models lean harder on their prior. If large-v3-turbo is WORSE, "just use the big model" is not a defence and the finding is more serious. |

## Disposition

- **S1 true** -> the trigger is CONTEXT, not silence, which sharpens the guidance: the risk is
  silence *inside* a recording (exactly the meeting case), not silence in an empty file.
- **S6 false** -> E40's "VAD eliminates it" is an OVERCLAIM and must be corrected in place.
- **S5 false** -> the YouTube-prior mechanism is wrong and must be retracted, not reworded.

## What this CANNOT establish

Whisper.cpp is one implementation. Findings here are about whisper.cpp + these GGML weights on this
box; they do not automatically transfer to OpenAI's hosted API or to other Whisper implementations,
whose decoding parameters (temperature fallback, no-speech threshold, condition_on_previous_text)
differ and are not all visible to us. Alastair's report of frontier-lab "thank you" hallucinations is
consistent with a shared family trait, but testing that requires running those APIs - not done here.
Claims will be scoped to what was measured.
