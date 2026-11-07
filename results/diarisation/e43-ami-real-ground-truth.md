# E43: against REAL ground truth our DER is 29.2%, not 3.51% - and 69% of the error is a VAD we never built (2026-07-17)

# File: results/diarisation/e43-ami-real-ground-truth.md
# Purpose: The primary config vs AMI, human annotation, standard DER. Pre-reg: e43-ami-prereg.md.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: First evaluation not resting on a reference I typed by hand. Result: DER 29.2% (IHM) /
# 33.1% (SDM) by the standard metric - versus the 3.51% we have been quoting, which was never DER.
# The dominant error is FALSE ALARM (20.2% of 29.2%), i.e. our speech detector; CONFUSION is only
# 8.7% on speakers this embedder has never heard, including far-field. The speaker model is good;
# the speech detector is a component we never built. 2 of 6 predictions hit.

## Corpus and method

- **AMI test split**, 16 meetings, 8.9 h per condition, 3-4 speakers, 13.4-48.2 min each,
  **17.0% overlapped speech**. CC-BY-4.0 (**attribution required**), ungated, size+sha256 verified,
  manifested before use. Human annotation - not Otter, not hand-typed by me.
- **Conditions:** IHM (close-talk headset) and SDM (single distant mic - the realistic meeting case).
- **Primary config:** WeSpeaker ResNet34-LM ONNX, 3.0s/1.0s windows, energy gate 1e-3,
  complete-linkage AHC, speaker count SUPPLIED from the reference.
- **Metric:** `pyannote.metrics` DiarizationErrorRate - the standard implementation, not mine.

## Result

| condition | policy | **DER** | miss | **FA** | conf |
|---|---|---|---|---|---|
| **IHM** | collar 0.25, overlap-skipped | **29.2%** | 0.3% | **20.2%** | 8.7% |
| IHM | collar 0.25, overlap-SCORED | 35.3% | 11.9% | 15.8% | 7.6% |
| IHM | collar 0.0, overlap-skipped | 32.3% | 0.4% | 21.9% | 10.1% |
| **SDM** | collar 0.25, overlap-skipped | **33.1%** | 0.1% | **25.1%** | 7.9% |
| SDM | collar 0.25, overlap-SCORED | 38.8% | 11.8% | 19.6% | 7.4% |

## THE CORRECTION: our 3.51% was never DER

**My Otter-based scoring SKIPPED every region where the reference had no speaker**
(`t_spk = at(midpoint); if not t_spk: continue`). False alarm was therefore **structurally
invisible** in E38, E38b, E39 and E40. That metric measured CONFUSION ONLY, on speech regions.

- Our confusion on AMI: **7.6-8.7%** - the honest analogue of the 3.51%, on much harder data.
- Our DER on AMI: **29.2%**.
- pyannote v3.1, published: **~9-11%** on meeting data (unverified by us).

> **We are roughly 3x WORSE than the open-source reference, not 3x better.** Every document
> quoting 3.51% as a diarisation error rate must be corrected: it is a confusion rate on
> pre-selected speech regions, against a commercial reference, on four clean recordings that all
> contain one voice.

This is the F17 error in its purest form: a true, reproducible number that measured an easier task
than the one it appeared to describe.

## Prediction resolution: 2 hits, 4 misses

| ID | Prediction | Actual | Verdict |
|---|---|---|---|
| A1 | 3.51% will not transfer; IHM DER >= 18% | **29.2%** | **HIT** |
| A2 | Overlap worth >= 10 points | 6.1 points | **MISS** |
| A3 | SDM >= 8 points worse than IHM | **3.9 points** | **MISS** |
| A4 | IHM DER excl. overlap 12-25% | 29.2% | **MISS** |
| A5 | No-collar >= 5 points worse | 3.1 points | **MISS** |
| A6 | Beat the majority baseline (~75% for 4 speakers) | 29.2% | **HIT** |

Badly calibrated, and the misses are informative:

- **A3's miss is the good news.** SDM (one distant mic in a room) costs only 3.9 points. The
  WeSpeaker embeddings are far more robust to far-field than I predicted - this is the condition I
  expected to break them.
- **A2's miss** means overlap is NOT our biggest problem (6.1 points), despite being 17% of speech
  and structurally unrepresentable by a single-label system. I had it ranked first; it is third.

## The diagnosis: we never built a VAD

**False alarm is 20.2% of a 29.2% DER - 69% of all error.** Our speech detector is `RMS > 1e-3`.
That is a volume threshold, not a voice detector: on real meeting audio, breathing, paper,
keyboards and room tone clear it and get assigned a speaker. Measured coverage: the energy gate
keeps 92.9% / 75.3% / 96.3% of three recordings whose reference speech is 82.7% / 65.0% / 86.2%.

**Confusion at 7.6-8.7% on unseen speakers, including far-field, says the speaker model is sound.**
The gap to pyannote is not embeddings or clustering - it is the component we skipped.

### Two VAD attempts, both rejected - recorded so they are not retried

1. **Whisper's segments as a speech mask.** They cover **97-98.5%** of a recording (vs 65-83%
   actual reference speech) because segments span the pauses BETWEEN words by design, and
   `--max-len 60` lengthens them. Using them made FA **worse: 40.7% -> 59.5%**. Whisper segments
   are transcription units, not speech regions - the same error class as v1 embedding whisper
   segments for diarisation.
2. **Silero VAD (ONNX, onnx-community/silero-vad, verified + manifested).** **NOT ADOPTED.** The
   positive control refuses it: on `jfk.wav` - 11s of continuous speech - it reports **60.9%**
   coverage. Adding the 64-sample context window Silero v5 expects moves it to 62.4%. A VAD that
   finds 60% speech in continuous speech is not usable, and the fault is on our side (invocation or
   this export). On AMI it gives 26-50% vs a 65-86% reference, i.e. it would trade false alarm for
   large MISS. **Had I skipped the control, FA would have dropped and I would have declared
   victory while making the system worse** - the reference cannot shout about miss the way it does
   about false alarm.

## Two instrument bugs found BEFORE any number was reported

Both would have made the system look far worse than it is:

1. **Hypothesis span bug - worth ~20 DER points.** I emitted each window as its full 3s span and
   merged overlapping ones. A 3s window is a decision about its CENTRE, not a claim that all 3
   seconds are that speaker - so every speech region got a ~3s tail, manufacturing false alarm the
   system never committed. The tell was arithmetic that did not reconcile: an energy gate keeping
   92.9% of windows on a recording that is 82.7% speech cannot produce 40.7% FA. Fixed: each window
   contributes only its hop-width slice. **DER 44.9% -> 25.1%, FA 40.7% -> 16.7%.**
2. **Multi-dot path bug.** `Path.with_suffix` on `EN2002b.Mix-Headset.wav` treats `.Mix-Headset` as
   the extension.

## Next (in order of measured value)

1. **A working VAD.** 20.2 of 29.2 points. Nothing else comes close. Options: fix the Silero ONNX
   invocation (validate on jfk.wav FIRST - the control is the gate); or pyannote's segmentation
   model (gated, needs Alastair's HF token); or NeMo MarbleNet.
2. **Overlap handling** (6.1 points) - needs a multi-label architecture, a real change.
3. Speaker counting remains unsolved (E39/E40) but is NOT on this critical path: k was supplied here
   and the system still lost 29 points elsewhere.

## Limits

AMI only; one language; k supplied from the reference. **No WER here** - this AMI distribution has
no transcripts, so E42's 10.7% disagreement figure remains unvalidated against real ground truth
(needs LibriSpeech). pyannote/NeMo were NOT run on this harness, so the ~9-11% comparison is
indicative only: different papers use different collars, overlap policies and subsets, and those
choices move DER by more than the differences being compared.

Evidence: this file; pre-registration e43-ami-prereg.md (committed db0d95a BEFORE any run);
tools/ami_bench.py, tools/vad.py; results/raw/ami-{ihm,sdm}-2026-07-17.txt; manifests/MANIFEST.md.
Corpus: AMI Meeting Corpus (CC-BY-4.0) - attribution required in any published use.
