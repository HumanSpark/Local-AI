# Speaker IDENTITY works on this box, ungated - extractor validated, pipeline attributes 15/15 (2026-07-17)

# File: results/diarisation/embedder-validation.md
# Purpose: The result that unblocked diarisation. Pre-registration: embedder-validation-prereg.md.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Speaker IDENTITY (not just turns) runs on this box today with NO HuggingFace token and
# NO loss of transcription quality. The WeSpeaker embedder passed all 6 pre-registered predictions
# with a separation margin of +0.5884 (same-speaker and different-speaker pairs do not overlap at
# all across 45 pairs). The full pipeline attributed 15/15 text segments correctly on the
# two-speaker fixture. Two honest caveats: the speaker COUNT was wrong (3 vs 2), and the fixture is
# synthetic. Both are stated below rather than smoothed over.

## The headline: the gate was never the blocker

pyannote/speaker-diarization-3.1 is `gated: auto` and we hold no HF token. That was recorded as the
blocker for speaker identity. **It was not.**

pyannote 3.1's pipeline is two models: a segmentation model and an EMBEDDING model. The embedding
model is `wespeaker-voxceleb-resnet34-LM` - which pyannote **mirrors from WeSpeaker**. The upstream
`Wespeaker/wespeaker-voxceleb-resnet34-LM` is **ungated** (CC-BY-4.0) and additionally ships a
ready-made **ONNX** export. The identity-bearing half of pyannote - the part that answers "is this
the same person?" - was public all along. Only the pipeline wrapper is gated.

**No gate was bypassed and none needed to be.** This is the authors' own public distribution, fetched
normally, size+sha256 verified against the HF API authority, manifested before first use.

## The architecture (and why it answers the transcription-quality concern)

    audio ─┬─► whisper.cpp large-v3-turbo ──► text + timestamps      [QUALITY UNTOUCHED]
           └─► sliding window ─► WeSpeaker ONNX ─► cluster ──► speaker timeline
                                                          └─► align on overlap ─► attributed transcript

Two INDEPENDENT passes. The speaker model never sees a word; the transcription model never sees a
speaker. **Adding identity therefore costs nothing in transcription accuracy** - large-v3-turbo is
unchanged. This is the concrete reason tinydiarize is rejected: tdrz IS the transcription model
(`small.en`), so it would trade transcript quality for speaker marks, AND it only marks turns.
Both of Alastair's requirements (identity; keep large-v3-turbo) rule it out independently.

Runs CPU-only via onnxruntime: **no torch, no torchaudio, no ROCm**. Deliberate - torchaudio has no
wheel matching torch 2.10.0+rocm7.13, so pip would have "resolved" it by upgrading torch inside
var/ft-venv, silently replacing F37's proven fine-tune stack to run an experiment. Isolated
var/diar-venv instead (343 MB). The GPU stays free for llama-server.

## Control 1: is the extractor real? (all 6 predictions HIT)

The risk was never the model - it was the FEATURE pipeline. A fbank mismatch against the training
config yields embeddings that are **silently wrong** rather than broken: still 256-dim, still
normalised, still clusterable into noise. Nothing downstream can detect that. So it was tested first.

| ID | Pair | Truth | Predicted | Measured | Verdict |
|---|---|---|---|---|---|
| **P1** | jfk 1st half vs 2nd half | SAME, **real human** | > 0.5 | **0.7141** | **HIT** |
| P2 | bf_emma vs bm_george | DIFFERENT | < 0.3 | 0.0510 | HIT |
| P3 | bf_emma turn0 vs turn1 | SAME (synth) | > 0.5 | 0.8416 | HIT |
| P4 | bm_george turn0 vs turn1 | SAME (synth) | > 0.5 | 0.9223 | HIT |
| P5 | jfk vs bm_george | DIFFERENT (x-domain) | < 0.3 | 0.0771 | HIT |
| **P6** | **separation margin** | - | **> 0.20** | **+0.5884** | **HIT** |

Across all 45 pairs (13 same-speaker, 32 different):

| population | min | mean | max |
|---|---|---|---|
| same-speaker | **0.7141** | 0.8367 | 0.9223 |
| different-speaker | -0.0164 | 0.0449 | **0.1258** |

**The populations do not overlap at all.** min(same) = 0.7141 exceeds max(diff) = 0.1258 by 0.5884.
Any threshold in that gap separates them perfectly, so the pipeline does not depend on a tuned magic
number - which is exactly why the threshold was set to the gap's midpoint rather than fitted.

Contrast with the tdrz probe, whose negative control returned the SAME answer for both hypotheses and
so discriminated nothing. This control separates, on real audio (P1 was made load-bearing precisely
so the verdict would not rest on my own TTS).

## Control 2: the full pipeline - 15/15 attributed, but the COUNT is wrong

On `twospeaker.wav` (36s, 8 alternating turns, exact ground truth):

**Attribution: 15 of 15 text segments correct.** Every bf_emma turn -> SPEAKER_1, every bm_george
turn -> SPEAKER_0, with no crossovers.

**Speaker count: 3 discovered, truth is 2. This is an error, and it is fully traced.**

The third cluster is **exactly one window of 70**, at 18.50-20.00s. Ground truth confirms that window
straddles a turn boundary: it contains the tail of bm_george, the inter-turn gap, and the start of
bf_emma. Its embedding is a MIXTURE of two voices, so it resembles neither and forms its own
singleton cluster. Resolved to the unit: 1 window, known location, known cause.

Attribution survived only because the majority-overlap vote ignored a singleton. **The count error and
the attribution success are separate claims; the good one does not excuse the bad one.**

### The mixture problem is the whole story of this pipeline

v1 of this tool embedded each WHISPER segment. Whisper returned two 30s segments on this 36s fixture -
each spanning BOTH speakers - so each embedding averaged two voices, the two mixtures resembled each
other, and the pipeline reported **1 speaker**. The extractor was already validated, which is what made
the diagnosis instant: the fault had to be the segmentation unit.

**Whisper segments are sized for transcription convenience and are not speaker-homogeneous. They must
never be the diarisation unit.** The speaker pass owns its own windowing. Shrinking the window from
30s to 1.5s did not remove the mixture problem - it shrank it from catastrophic (total collapse) to one
stray window, because only windows sitting ON a boundary can be mixtures, and boundaries are rare.

### Why the count is NOT fixed here

The obvious fix is "drop clusters below N windows". N would be chosen against a fixture whose answer I
already know - tuning until the number reads 2. That manufactures a result rather than measuring one,
and it would trade away genuine short interjections (a real "mm-hm" is also a small cluster). The
guard needs REAL audio to set honestly. Left unfixed and stated, rather than tuned and quiet.

## Limits - what this does NOT establish

Passing proves the extractor produces speaker-discriminative embeddings, and that the pipeline
attributes correctly on **clean, synthetic, non-overlapping, two-speaker audio with maximally distinct
voices (one female, one male)**. That is the EASY case. It does not establish:

- **Overlapping speech** - people talking over each other. The mixture problem above is a hint of how
  this degrades, and real meetings are full of it.
- **Similar voices** - two men of the same age and accent. P2 was the easiest possible discrimination.
- **Short turns** - a 1.5s window cannot sit inside a 0.5s "yes".
- **Real acoustics** - room tone, mic differences, phone/VC codecs.
- **Speaker count on real audio** - see above; unsolved.
- **Any comparison against pyannote**, which remains the reference. If the token arrives, benchmark
  this stack against it rather than assuming parity.

The fixture is synthetic, which mattered less here than for tdrz (speaker embedding keys on vocal
timbre, which TTS voices genuinely differ in; turn detection keys on conversational prosody, which
concatenated isolated utterances lack) - but "mattered less" is not "did not matter". **Real
multi-speaker audio is still the blocking input for any recommendation.**

## Consequence for tinydiarize

The tdrz question is now **moot, not merely inconclusive**. It fails both of Alastair's stated
requirements independently (turns not identity; small.en not large-v3-turbo). Chasing real audio to
settle its 0/7 would settle a question that no longer decides anything. Dropped.

Evidence: this file; pre-registration results/diarisation/embedder-validation-prereg.md (committed
c6e489d BEFORE any run); tools/spk_embed.py, tools/spk_embed_validate.py, tools/diarise.py;
results/diarisation/diarise-out.json; manifests/MANIFEST.md (provenance);
docs/plans/2026-07-17-diarisation-investigation.md (landscape); results/diarisation/tdrz-probe.md.
