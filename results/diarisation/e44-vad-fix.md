# E44: a real VAD halves the error - DER 29.2% -> 20.2% held out, and far-field costs 0.9 points (2026-07-17)

# File: results/diarisation/e44-vad-fix.md
# Purpose: Fixing E43's diagnosis - false alarm was 69% of all DER because we never built a VAD.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E43 measured our stack against AMI (real human ground truth) at 29.2% DER and found the
# error was dominated by FALSE ALARM from an energy gate (RMS > 1e-3) - a volume threshold, not a
# voice detector. Replacing it with Silero (via whisper.cpp's own VAD tool) gives 20.2% DER on 13
# HELD-OUT meetings, and confusion falls as a side effect. The far-field result is the surprise:
# SDM costs 0.9 points over close-talk headsets.

## Result: held out, not tuned

The VAD threshold was chosen on 3 AMI meetings. **The other 13 were never touched** and are the
report set - because choosing a threshold on the meetings you report is tuning on test data, the
same sin refused in E39 (where a cluster-size guard was left unfixed rather than fitted to a known
fixture).

| condition | DER (energy gate, E43) | **DER (real VAD, HELD OUT)** | change |
|---|---|---|---|
| **IHM** (close-talk headset) | 29.2% | **20.2%** | **-9.0** |
| **SDM** (single distant mic) | 33.1% | **21.1%** | **-12.0** |

Held-out breakdown (collar 0.25, overlap-skipped):

| condition | DER | miss | FA | conf |
|---|---|---|---|---|
| IHM | 20.2% | 2.4% | 10.2% | 7.6% |
| SDM | 21.1% | 4.4% | 8.6% | 8.1% |

**The tuning set said 14.4%; held out it is 20.2%.** That 5.8-point spread IS the tuning-on-test
effect, measured rather than assumed. **20.2% is the number.** 14.4% was optimism, and would have
been the figure had the corpus not been split.

## The surprise: far-field is nearly free

**SDM 21.1% vs IHM 20.2% - one distant microphone in a room costs 0.9 points.** E43's prediction A3
said >= 8 points and missed; with a working VAD the gap closes almost entirely. This is the single
most useful practical finding here: **an on-prem meeting box does not need headsets.** One mic on
the table is within a point of a headset per person.

Not over-claimed: AMI's SDM is a good array mic in a purpose-built meeting room, not a laptop in a
noisy office. It is far-field, not worst-case.

## The threshold sweep (AMI IHM, 3 tuning meetings)

| threshold | DER | miss | FA | conf |
|---|---|---|---|---|
| energy gate (shipped) | 29.2% | 0.3% | **20.2%** | 8.7% |
| 0.50 (Silero default) | 24.8% | 18.0% | 1.9% | 4.9% |
| 0.35 | 24.2% | 16.0% | 2.4% | 5.7% |
| 0.20 | 21.2% | 11.3% | 3.8% | 6.1% |
| **0.10** | **14.4%** | 3.1% | 8.3% | 3.0% |
| 0.05 | 14.9% | 2.9% | 8.7% | 3.3% |

The threshold is the miss/false-alarm dial. There is a **sharp knee between 0.15 and 0.20**, and
0.05-0.15 is a **flat plateau** (all within 0.5 points) - so 0.10 is a plateau midpoint, not a
fitted magic number. **Silero's own default (0.50) is badly wrong for this task**: it is tuned for
"is this speech?" on clean audio, and on meeting audio it discards 18% of real speech.

**Unpredicted bonus: confusion falls 8.7% -> 3.0%.** Cleaner windows make better clusters - the
energy gate was feeding non-speech embeddings into the clustering and polluting it.

## What was rejected, and why - recorded so it is not retried

1. **Whisper's SEGMENTS as a speech mask.** They cover 97-98.5% of a recording vs 65-83% real
   reference speech, because segments span the pauses BETWEEN words by design and `--max-len 60`
   lengthens them. Made FA **worse: 40.7% -> 59.5%.** Whisper segments are transcription units, not
   speech regions - the same error class as v1 embedding whisper segments for diarisation.
2. **Our own Silero ONNX port** (fetched, verified, manifested, unused). It under-detects relative
   to whisper.cpp's C++ implementation of the same weights. Not debugged: whisper.cpp already ships
   `whisper-vad-speech-segments`, a purpose-built tool using the ggml Silero model we already had.
   Built against the existing Vulkan config, no flag changes. **The capability was already on the
   box** - I wrote an ONNX port before checking.

### A correction to my own reasoning

I first rejected the ONNX port because it scored **60.9% coverage on jfk.wav** where I "expected
~90%+". **My expectation was the faulty instrument.** jfk.wav genuinely contains ~28% pause, and
whisper.cpp's VAD scores 71.4% on the same file, emitting **4 segments that match its 4 phrases
exactly**. I judged a measurement against a number I had assumed rather than established - the same
error as blaming the model for a turn I dropped by hand (E40/F45). The right control was never "does
it hit a number I imagined", it was "does its coverage track the reference on the actual benchmark".

## Where we stand vs the field

| system | DER on meeting data |
|---|---|
| ours, energy gate (E43) | 29.2% |
| **ours, real VAD (E44, held out)** | **20.2%** |
| pyannote v3.1, published | ~9-11% |

**Still ~2x behind the open-source reference, down from ~3x.** Not comparable rigorously: their
figure comes from different papers using different collars, overlap policies and subsets, and those
choices move DER by more than the gap being discussed. The only honest comparison runs pyannote on
THIS harness - which needs Alastair's HF token, and is now worth doing.

## Remaining error budget (held out, IHM)

| source | points | tractable? |
|---|---|---|
| false alarm | 10.2 | partly - the VAD still over-covers; a better VAD (pyannote segmentation) is the lever |
| **confusion** | **7.6** | the embedding/clustering limit on unseen speakers |
| miss | 2.4 | mostly the plateau's cost |
| (overlap, when scored) | +8.4 | structural - needs a multi-label architecture |

## Limits

AMI only; one language; k supplied from the reference (automatic counting remains unsolved, E39/E40,
but is NOT on the critical path - k was given here and we still lost 20 points elsewhere). The
threshold plateau was established on 3 meetings of one condition; it may not transfer to phone audio
or noisy rooms. No WER here - AMI in this distribution has no transcripts.

Evidence: this file; e43-ami-real-ground-truth.md (the diagnosis); e43-ami-prereg.md (predictions,
committed db0d95a BEFORE any run); tools/ami_bench.py, tools/diarise.py, tools/vad.py;
results/raw/ami-{ihm,sdm}-vad-heldout-2026-07-17.txt, results/raw/vad-threshold-sweep-2026-07-17.txt.
Corpus: AMI Meeting Corpus (CC-BY-4.0) - attribution required in any published use.
