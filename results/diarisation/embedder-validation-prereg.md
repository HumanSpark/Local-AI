# PRE-REGISTRATION: does the WeSpeaker embedding extractor actually discriminate speakers? (2026-07-17)

# File: results/diarisation/embedder-validation-prereg.md
# Purpose: Predictions registered BEFORE running the speaker-embedder positive control.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Before any diarisation result is believed, the instrument must be validated. The
# tinydiarize probe (tdrz-probe.md) produced 0/7 with a negative control that returned the SAME
# answer for both hypotheses - i.e. it discriminated nothing, so the probe could not distinguish
# "model failed" from "fixture is wrong". This control is designed to discriminate: it must
# separate same-speaker pairs from different-speaker pairs, on REAL audio as well as synthetic.

## Why this control exists

The risk surface is the FEATURE PIPELINE, not the model. WeSpeaker's ONNX takes 80-bin Kaldi
fbank (25ms/10ms, CMN applied). If our fbank differs from the training config in scaling,
normalisation, or windowing, the embeddings are **silently wrong** rather than obviously broken -
they still come out 256-dim, still L2-normalise, still cluster into *something*. A diarisation
run against a broken extractor would produce plausible-looking speaker labels that are noise.
Nothing downstream can detect this. So it is checked here, first, explicitly.

## Method

`tools/spk_embed_validate.py`, using:
- **REAL audio:** `whisper.cpp/samples/jfk.wav` (11s, one real human speaker), split in half.
- **Synthetic audio:** `results/diarisation/twospeaker.wav` segments, cut on the exact ground-truth
  boundaries in `twospeaker-truth.json` (bf_emma = British female, bm_george = British male).

Cosine similarity of L2-normalised 256-dim embeddings. Higher = more likely the same speaker.

## Predictions (registered BEFORE the run)

| ID | Pair | Speakers | Prediction | Rationale |
|---|---|---|---|---|
| **P1** | jfk 1st half vs jfk 2nd half | SAME, real | cosine **> 0.5** | The load-bearing one: same real human, real audio. If this fails the extractor is broken. |
| **P2** | bf_emma vs bm_george | DIFFERENT | cosine **< 0.3** | Female vs male voice - the easiest possible discrimination. |
| **P3** | bf_emma turn A vs bf_emma turn B | SAME, synthetic | cosine **> 0.5** | Same TTS voice across different utterances. |
| **P4** | bm_george turn A vs bm_george turn B | SAME, synthetic | cosine **> 0.5** | As P3, other voice. |
| **P5** | jfk vs bm_george | DIFFERENT (real vs synth) | cosine **< 0.3** | Both male - harder than P2, and cross-domain. |
| **P6** | **Separation margin** | - | min(same-pairs) − max(diff-pairs) **> 0.2** | The decisive test. Clustering only works if the two populations separate. A large margin means a threshold exists; a margin near zero means the extractor cannot support identity at all, regardless of individual scores. |

## Disposition rule (registered in advance so it cannot be rationalised after the fact)

- **P1 and P6 both hold** -> extractor VALIDATED. Proceed to build the clustering pipeline.
- **P1 fails** -> the feature pipeline is wrong. Do NOT proceed, do NOT tune thresholds. Fix the
  extractor (suspect fbank scaling / CMN / dither first) and re-run this control unchanged.
- **P1 holds but P6 fails** -> embeddings carry some signal but not separable signal. Investigate
  before building anything on top.

## What this control CANNOT establish

Recorded now, so it is not overclaimed later. Passing this proves the extractor produces
speaker-discriminative embeddings on clean, single-speaker, well-separated audio. It does NOT
prove the full stack works on real meetings, where the hard parts are: overlapping speech,
short turns, similar voices (two men of the same age and accent - P2 is the EASY case), channel
and room variation, and choosing the number of speakers without being told. Those need real
multi-speaker audio and remain open regardless of this result.

## Note on the synthetic-fixture lesson

Synthetic TTS was the prime suspect for tdrz's 0/7, because turn DETECTION keys on conversational
prosody that concatenated isolated utterances do not have. Speaker EMBEDDING is a weaker demand on
the fixture: it keys on vocal timbre, which TTS voices genuinely differ in. That is a reason to
expect the synthetic pairs to be *informative here* where they were *uninformative there* - but it
is an argument, not evidence, which is exactly why P1 (real audio) is the load-bearing prediction
and the synthetic pairs are supporting.
