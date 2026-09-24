# PRE-REGISTRATION: the primary config against REAL ground truth (AMI) (2026-07-17)

# File: results/diarisation/e43-ami-prereg.md
# Purpose: Predictions registered BEFORE the first run against human-annotated ground truth.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Every diarisation number so far (E38-E40, 3.51% duration-weighted segment error) was
# measured against an Otter.ai reference that is ~98% accurate, that I hand-typed (dropping a turn
# I then blamed on the model for two write-ups), on four recordings that ALL contain Alastair's
# voice. AMI removes every one of those crutches at once: human annotation, public corpus, unseen
# speakers, far-field condition, and 17% overlapped speech.

Why: our headline diarisation number is measured against a ruler we estimated and I typed by hand.
Trigger: Alastair, 2026-07-17 - "go get us that Data and do a proper benchmark now with the primary
configuration".

## Setup

- **Corpus:** AMI test split, 16 meetings, 8.9 h per condition, 3-4 speakers, 13.4-48.2 min each.
  CC-BY-4.0, ungated, verified size+sha256, manifested before use. **17.0% of speech time is
  OVERLAPPED.**
- **Conditions:** IHM (close-talk headset) and SDM (single distant mic - the realistic meeting case).
- **Primary config under test:** WeSpeaker ResNet34-LM ONNX embeddings, 3.0s window / 1.0s hop,
  energy floor 1e-3, complete-linkage AHC, speaker count SUPPLIED from the ground truth (k is an
  input in deployment - taken from the meeting invite).
- **Metric:** `pyannote.metrics` DiarizationErrorRate - the STANDARD implementation, not mine. This
  matters: my own DER code is a variable I can now remove. Reported both with the standard 0.25s
  collar and without, and both scoring and skipping overlap.

## Predictions (registered BEFORE any run)

| ID | Prediction | Rationale |
|---|---|---|
| **A1** | **Our 3.51% will NOT transfer. AMI IHM DER (overlap scored, 0.25s collar) will be >= 5x worse, i.e. >= 18%** | Every crutch removed at once. If it lands near 3.51% I should suspect the harness, not celebrate. |
| **A2** | **Overlap is the single biggest error source: skipping overlap improves DER by >= 10 points** | We emit ONE label per window. On 17% of speech time we are wrong by construction. This is structural, not tunable. |
| **A3** | **SDM is >= 8 points worse than IHM** | Far-field: reverberation and lower SNR degrade speaker embeddings. Every prior recording was close-talk or VC-quality. |
| **A4** | **DER excluding overlap, IHM, will be 12-25%** | Our supervised ceiling on clean 2-4 speaker audio was ~3.6%, but on UNSEEN speakers with real annotation I expect materially worse. |
| **A5** | **The collar matters a lot: no-collar DER is >= 5 points worse than 0.25s-collar DER** | Our 3.0s windows cannot resolve turn boundaries finely; E40 showed boundary frames carry 40-76% of errors. The collar forgives exactly those. |
| **A6** | **We will still beat the majority baseline comfortably on both conditions** | 3-4 balanced speakers means the baseline is weak (~65-75% DER). If we do NOT beat it, the stack does not work on real meetings at all. |

## Disposition

- **A1 false (we score near 3.51%)** -> suspect the harness before believing it. A result that good
  on AMI would contradict the entire published literature (pyannote v3.1 is reported ~9-11% on
  meeting data, and it is a far more sophisticated system than ours).
- **A2 true** -> overlap handling is the single highest-value next engineering step, and our
  single-label architecture is the thing to change.
- **A6 false** -> the stack does not generalise beyond clean audio and Alastair's voice, and the
  3.51% must be re-scoped in every document that cites it.

## What this CANNOT establish

AMI has no transcripts in this distribution, so this scores **DER only - no WER.** The E42 WER
number (10.7% disagreement vs Otter) remains unvalidated against real ground truth; that needs
LibriSpeech or AMI's separate transcript annotations, not fetched.

We are testing OUR stack, not pyannote/NeMo. Any comparison to their published ~9-11% is
indicative only until they are run on this same harness - different papers use different collars,
overlap policies and subsets, and those choices move DER by more than the differences being
compared.
