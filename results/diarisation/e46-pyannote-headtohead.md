# E46: pyannote 3.1 vs our stack, like-for-like - 6.5% vs 20.3% on close-talk, and WHERE the gap lives (2026-07-17)

# File: results/diarisation/e46-pyannote-headtohead.md
# Purpose: The honest head-to-head. Same AMI meetings, same metric, same collar/overlap, same k.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Every prior "us vs pyannote" was a cross-paper hand-wave (our number vs their published
# ~9-11%, different collars/subsets/references). This runs BOTH systems on the identical 6 held-out
# AMI meetings, identical pyannote.metrics DER, identical scoring policies, identical supplied k.
# Result: pyannote wins clearly (IHM 6.5% vs 20.3%, SDM 13.8% vs 21.7%), and the component breakdown
# shows the gap is TWO things - a cleaner VAD (false alarm) and much better close-talk clustering
# (confusion) - the second of which was a genuine surprise.

## Setup (identical for both systems)

- **Corpus:** AMI test, meetings 4-9 (offset 3, limit 6) - the held-out set our 20.2% was reported
  on. IHM (close-talk headset) and SDM (single distant mic). 3-4 speakers each. CC-BY-4.0.
- **Metric:** pyannote.metrics DiarizationErrorRate, four policies. Headline = collar 0.25,
  overlap-skipped (the common reporting convention).
- **Speaker count:** supplied to BOTH from the reference (num_speakers for pyannote; --speakers for
  ours). k is known from the meeting invite in deployment (E39/E40).
- **Ours:** WeSpeaker ONNX + Silero VAD (thr 0.10) + 3s/1s windows + complete-linkage AHC.
- **pyannote:** speaker-diarization-3.1, CPU, in-memory audio, var/pyannote-venv (isolated - ft-venv
  never touched). Scored on `.speaker_diarization` (its full overlap-capable output).

## Headline (collar 0.25, overlap-skipped)

| condition | **ours** | **pyannote 3.1** | ratio |
|---|---|---|---|
| **IHM** (close-talk) | 20.3% | **6.5%** | **3.1x** |
| **SDM** (far-field) | 21.7% | **13.8%** | **1.6x** |

**pyannote wins decisively on close-talk and clearly on far-field.** Our own 6-meeting numbers
reproduce the 13-meeting held-out figures (IHM 20.3% vs 20.2%, SDM 21.7% vs 21.1%), so the subset is
representative and the comparison is fair. pyannote's IHM 6.5% also sits right at its published
~9-11% band (better here, on this subset), which independently validates our harness.

## WHERE the gap lives - the component breakdown is the finding

collar 0.25, overlap-skipped, component split:

| | ours IHM | pyan IHM | ours SDM | pyan SDM |
|---|---|---|---|---|
| **false alarm** | 10.6% | **3.2%** | 9.4% | **3.5%** |
| **confusion** | 8.6% | **1.1%** | 10.0% | **7.7%** |
| miss | 1.1% | 2.3% | 2.3% | 2.6% |

Two distinct gaps, and they behave differently:

1. **False alarm: pyannote is ~3x cleaner on BOTH conditions** (3.2/3.5% vs our 10.6/9.4%). This is
   their segmentation model vs our Silero-VAD-plus-threshold. It is the gap E44 already identified as
   our largest remaining item, and it is real: pyannote's VAD is simply better at "is this speech?"
   Their segmentation model IS available (pyannote/segmentation-3.0, now ungated to us) - so this
   part of the gap is CLOSEABLE by adopting their VAD, which is the highest-value next step.

2. **Confusion: pyannote is ~8x better on close-talk (1.1% vs 8.6%) but only ~1.3x on far-field
   (7.7% vs 10.0%).** This was NOT expected - I believed our WeSpeaker embeddings were near-parity
   on the "who is this?" question. They are not, on clean audio: pyannote's clustering finesse
   (its own embeddings + a tuned clustering it controls end-to-end) extracts far more from
   close-talk. Crucially, that advantage COLLAPSES at distance - both systems land near 8-10%
   confusion on SDM. So pyannote's headline win is disproportionately clean-audio clustering skill
   that degrades when the mic is far, not a uniform embedding superiority.

## What this corrects and confirms

- **Confirms** E43/E44's diagnosis that our false alarm is a top problem, and quantifies exactly how
  much better a good VAD can be (~3x).
- **Corrects** my standing belief (from the WeSpeaker validation, E38) that our embeddings were
  near-parity on identity. On close-talk they are well behind pyannote's clustering. The synthetic
  and Otter-referenced work never exposed this because it measured confusion on easy, pre-segmented,
  one-recurring-voice audio. Real ground truth on unseen speakers shows the true gap.
- **The far-field convergence is the practically useful nuance:** for an on-prem meeting box using a
  table mic (the realistic deployment, SDM), the gap is 1.6x (13.8 vs 21.7), not 3x. pyannote is
  still better, but the distance between the systems is much smaller in the condition that matters.

## Four-policy detail (for reproducibility)

| policy | ours IHM | pyan IHM | ours SDM | pyan SDM |
|---|---|---|---|---|
| collar 0.25, overlap-skipped | 20.3% | 6.5% | 21.7% | 13.8% |
| collar 0.25, overlap-SCORED | 28.6% | 11.8% | 29.4% | 18.3% |
| collar 0.0, overlap-skipped | 23.7% | 9.6% | 25.1% | 16.8% |
| collar 0.0, overlap-SCORED | 33.4% | 15.9% | 34.1% | 22.2% |

pyannote's advantage holds across all four policies. Note pyannote's overlap-scored penalty is
smaller than ours (IHM +5.3 vs our +8.3 at collar 0.25) because it CAN assign overlapping speakers
and we cannot - part of its win is a capability our single-label architecture lacks by design.

## Honest limits

- **6 meetings, one corpus (AMI), English, k supplied.** A real evaluation is the full test set on
  both, but 6 held-out meetings on the identical harness is already a far stronger claim than the
  cross-paper comparison it replaces.
- **pyannote ran on CPU** (torchcodec can't use this AMD GPU); its ~real-time speed here is not its
  best. Our stack runs ~60x real time with the GPU free - a speed advantage not captured in DER and
  worth measuring separately if speed matters for the use case.
- Not run: pyannote's segmentation model AS our VAD (the closeable-gap experiment), or
  speaker-diarization-community-1. Both are now unblocked and are the obvious next steps.

## Next (by measured value)

1. **Adopt pyannote/segmentation-3.0 as our VAD, keep the rest of our stack.** Isolates how much of
   the false-alarm gap (7 points) we can close while keeping our ONNX/no-torch serving path. If it
   closes most of it, our stack lands near pyannote on SDM without the torch dependency.
2. Decide whether the confusion gap is worth chasing (our clustering) or whether "adopt pyannote
   wholesale for close-talk, keep ours for its speed/simplicity on far-field" is the right call.

Evidence: this file; results/raw/{ours,pyannote}-{ihm,sdm}-6mtg-2026-07-17.txt; tools/pyannote_bench.py,
tools/ami_bench.py; e44-vad-fix.md (our 20.2%/21.1%), e43-ami-prereg.md. Corpus: AMI (CC-BY-4.0) -
attribution required. pyannote-audio 4.0.7, pyannote/speaker-diarization-3.1.
