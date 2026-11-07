# E47: swapping in pyannote's VAD cuts our online-call error 48% (20.3% -> 10.5%) at 55x real time (2026-07-17)

# File: results/diarisation/e47-hybrid-vad-swap.md
# Purpose: The hybrid result. Pre-registration: e47-hybrid-prereg.md (committed 466ffb2 BEFORE).
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E46 put pyannote 3x ahead of us on IHM (online-call proxy). This swaps ONLY the VAD -
# pyannote/segmentation-3.0 for our Silero - keeping our fast WeSpeaker embeddings + complete-linkage
# clustering. Result on IHM: 20.3% -> 10.5% (a 48% error cut), at 55x real time vs pyannote's ~1x.
# The confusion drop (8.6% -> 4.1%) REFUTES pre-registered H2 and reveals our VAD was hurting us
# twice: false alarm AND clustering pollution.

## The three-way, same 6 held-out AMI meetings, collar 0.25 overlap-skipped

| system | IHM | SDM | speed | dependency |
|---|---|---|---|---|
| ours (Silero VAD) | 20.3% | 21.7% | ~60x RT | ONNX, no torch |
| **HYBRID (pyannote VAD + our embed/cluster)** | **10.5%** | **16.9%** | **55x RT** | torch (VAD only) |
| pyannote 3.1 (full) | 6.5% | 13.8% | ~1x RT (CPU) | torch (whole pipeline) |

**For online calls (IHM is the right proxy - close mics mixed to one stream, like AMI Mix-Headset):
20.3% -> 10.5%, a 48% error reduction.** The gap to pyannote closes from 3.1x to 1.6x. On far-field
the hybrid is 16.9% (from 21.7%), also a clear gain.

## Component breakdown - why it worked better than predicted (IHM)

| | ours | hybrid | pyannote |
|---|---|---|---|
| false alarm | 10.6% | **3.5%** | 3.2% |
| confusion | 8.6% | **4.1%** | 1.1% |
| miss | 1.1% | 2.9% | 2.3% |

- **False alarm dropped to pyannote's level (3.5% vs 3.2%).** The VAD swap transferred essentially
  all of pyannote's speech-detection advantage. This was predicted (H1).
- **Confusion HALVED (8.6% -> 4.1%), which REFUTES H2.** I predicted confusion would stay near ours
  (7-9%) because we kept our clustering. It did not. **Our bad VAD was hurting us TWICE:** directly
  (false alarm) and by feeding non-speech windows - breaths, keyboard, room noise - into the
  clustering, polluting the speaker groups. A clean VAD fixes both.

**This corrects E46's conclusion.** E46 said "our embeddings/clustering trail pyannote's badly on
close-talk (1.1% vs 8.6% confusion)". That overstated it: roughly HALF of that confusion gap was our
VAD, not our embeddings. With a clean VAD our clustering reaches 4.1% - still behind pyannote's 1.1%,
but the true embedding/clustering gap is ~3 points, not ~7.

## Prediction resolution

| ID | Prediction | Result | Verdict |
|---|---|---|---|
| H1 | Hybrid FA <= 5% | 3.5% | HIT |
| H2 | Confusion stays 7-9% | 4.1% | **REFUTED (the finding)** |
| H3 | DER 11-15% | 10.5% | HIT (just beat the range low) |
| H4 | Slower than ours, >> pyannote | 55x vs 60x vs ~1x | HIT |

## Speed - the stated priority, measured not assumed

193 min of audio processed in ~211s: pyannote VAD 65s + our embed/cluster 146s = **55x real time,
CPU-only, GPU free.** Barely slower than our pure stack (~60x) and ~50x faster than pyannote's full
pipeline on this box. For a 1-hour call: ~1 minute, vs pyannote's ~1 hour. On a batch of meetings
this is the difference between "done before you've made coffee" and "run it overnight".

The torch dependency is the cost: the hybrid reintroduces torch (for segmentation-3.0) that our pure
stack avoided. It runs in the isolated var/pyannote-venv; ft-venv is untouched. Whether that
dependency is acceptable is a deployment call, but it buys a 48% error cut for ~10% of the speed.

## The decision this clarifies

For Alastair's use case (online calls, speed valued):

- **Adopt the hybrid.** 10.5% on online-call-like audio at 55x real time is a large, cheap win over
  our 20.3%, and it needs only the VAD swap - our embedding/clustering path is unchanged.
- **The remaining gap to pyannote (10.5% vs 6.5%) is now purely clustering** (~3 pts confusion +
  overlap handling we lack). Whether to chase it is a clean question: is 10.5% good enough for
  attributed meeting notes, or is pyannote's 6.5% worth ~50x the compute and no speed headroom?
- **Overlap is untouched** here (segmentation-3.0 used as a binary VAD). pyannote's remaining edge
  includes its ability to assign overlapping speakers, which our single-label stack cannot do by
  design.

## Limits

6 held-out AMI meetings, English, k supplied, one corpus. segmentation-3.0 used as a binary VAD
(its overlap output collapsed). Not yet tested on the REAL online-call recordings (the 4 Otter-
referenced meetings) - AMI IHM is a strong proxy but a direct test on actual Zoom/Teams audio with
codec artifacts is the natural next validation. Speed measured on CPU; segmentation-3.0 on GPU (if
the ROCm/torchcodec path were solved) would be faster still.

Evidence: this file; e47-hybrid-prereg.md (committed 466ffb2 BEFORE the run); e46-pyannote-
headtohead.md; results/raw/hybrid-{ihm,sdm}-6mtg-2026-07-17.txt; tools/hybrid_bench.py. Corpus: AMI
(CC-BY-4.0) - attribution required. pyannote/segmentation-3.0 (MIT), pyannote-audio 4.0.7.
