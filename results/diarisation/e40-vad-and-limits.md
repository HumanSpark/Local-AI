# E40: whisper INVENTS SPEECH over silence - and the diarisation residual is physics, not model (2026-07-17)

# File: results/diarisation/e40-vad-and-limits.md
# Purpose: Continued autonomous work on E39's open items. One correctness bug found, one limit proven.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: The most important finding is NOT about diarisation. Without VAD, whisper large-v3-turbo
# FABRICATES SPEECH over silence - 120s of dead air on a real client call became four "Thank you"
# segments, and a clip of the same audio invented "I'm going to go to the next meeting with Marina
# and Claire", words nobody said. `--vad` eliminates it; VAD is now mandatory in the pipeline.
# Separately: clustering is DONE (unsupervised now equals the supervised ceiling) and the residual
# error is proven to be the boundary-mixture problem - physics, not a model weakness. Speaker
# counting remains UNSOLVED.

## THE HEADLINE IS A CORRECTNESS BUG, NOT AN ACCURACY ONE

Whisper large-v3-turbo, no VAD, on 120s of opening silence in a real 35-min client call:

```
[  0.00-  5.00] Okay, so this is my meeting with Marina and Claire.
[ 30.00- 59.98] Thank you.          <- silence
[ 60.00- 89.98] Thank you.          <- silence
[ 90.00-119.98] Thank you.          <- silence
[120.00-149.98] Thank you.          <- silence
```

A 180s clip of the SAME audio hallucinated worse - six fabricated segments including
`"I'm going to go to the next meeting with Marina and Claire"` and `"I'm going to go to the next
meeting with Marina."` **Nobody said any of it.**

With `--vad -vm ggml-silero-v6.2.0.bin` the transcript jumps cleanly 4.11s -> 149.92s, where speech
actually resumes. Zero fabrications.

**Why this outranks every DER number in this file:** a wrong speaker LABEL is visible to a reader -
they see a turn attributed to the wrong person and can question it. Invented SPEECH is invisible. It
reads as a real utterance, in a real meeting, attributed to a real named person, in a document that
may go to a client. We have been publishing "28x real time transcription" as a capability since
Phase A **without ever checking what it does with silence**.

VAD is therefore MANDATORY in tools/diarise.py - it raises if the model is absent, rather than
degrading quietly. Model fetched from the canonical upstream (ggml-org/whisper-vad, MIT, ungated),
size + sha256 verified, manifested before use. whisper.cpp ships a working
`models/for-tests-silero-v6.2.0-ggml.bin`, but depending on a TEST FIXTURE for a correctness
guarantee is not a plan.

## Final shipping numbers (147 min real audio, Otter.ai reference)

| recording | k | segments | majority baseline | **SEGMENT err (by duration)** | frame-DER |
|---|---|---|---|---|---|
| planning-13min | 3 | 330 | 17.1% | **2.4%** | 4.7% |
| client-call-35min | 2 | 691 | 15.3% | **2.3%** | 3.2% |
| client-call-36min | 2 | 592 | 48.5% | **10.0%** | 9.9% |
| webinar-63min | 4 | 1552 | 45.1% | **2.5%** | 2.7% |
| **MEAN** | | | **31.5%** | **4.31%** | 5.12% |

**The SEGMENT column is the deliverable metric** - "is this paragraph attributed to the right
person?" - and it is what a reader experiences. Frame-DER (5.12%) is a COMPONENT metric that
overstates user-visible error, because the product assigns each transcript segment by
majority-overlap vote, which outvotes contaminated boundary windows. I had been optimising the
component metric for two sessions without measuring the deliverable.

**client-call-36min is the outlier at 10.0%** and it is NOT a clustering failure: its supervised
ceiling is 8.8%, so the EMBEDDINGS themselves struggle on that recording. Different failure mode
from everything else here; unexplained. Not averaged away.

## Clustering is DONE - unsupervised now equals supervised

Speech-pure windows (whisper's own segment timings used as a free VAD mask - the transcription is
required anyway, so cost is zero), used to LEARN speakers, then propagated to every frame:

| recording | cluster-all (E39) | **pure-learn + propagate** | supervised ceiling |
|---|---|---|---|
| planning | 4.7% | **4.0%** | 4.1% |
| call-35 | 3.2% | **2.6%** | 2.7% |
| call-36 | 9.9% | **8.8%** | 8.8% |
| webinar | 2.7% | 3.0% | 2.1% |
| **MEAN** | **5.12%** | **4.58%** | **4.45%** |

4.58% vs a 4.45% ceiling: **unsupervised clustering now extracts essentially everything the
embeddings contain**, matching or beating supervised on 3 of 4. Further DER gains require better
embeddings or better frames - not better grouping. Modest (0.54 points) and it made the webinar
slightly worse; reported as measured.

### A measurement bug I nearly published

The first version of this comparison scored speech-pure windows at **3.0% mean DER vs 5.1%** - a
huge win. It was fake. Filtering dropped 810 windows to 89 (planning), and the DER was computed only
over the SURVIVING windows - the clean, mid-utterance, boundary-free ones. I discarded 89% of the
audio and then scored better on what was left. **That is not an improvement, it is an easier exam.**
The valid comparison propagates labels to the IDENTICAL full frame set, and the real gain is 0.54
points, not 2.1. Same like-for-like violation as F17's same-question benchmark.

## The residual is PHYSICS, not a model weakness

Where the supervised error lives, using a 3.0s window (so a window within 1.5s of a true turn
boundary physically contains two voices):

| recording | frames near a boundary | **errors near a boundary** |
|---|---|---|
| planning | 8.5% | **75.8%** |
| call-35 | 5.6% | **57.9%** |
| call-36 | 10.6% | **39.8%** |
| webinar | 5.0% | **56.8%** |

Boundary frames are 5-10.6% of the audio but carry 40-76% of the errors - a **6-9x
over-representation**. A window spanning a turn change contains two voices; no embedding of it can
be correct, because the truth says one speaker and the signal holds two. This is the same mixture
problem that made v1 report 1 speaker on a 2-speaker fixture, now down to its irreducible core.
Shrinking the window would reduce mixtures but costs embedding quality (E38: 1.5s -> same-speaker
sim 0.78 vs 0.85 at 3.0s). That trade is the remaining engineering lever.

## Speaker counting: STILL UNSOLVED (fourth method failed)

E39 tried silhouette, a >=2% rule, and spectral eigengap - all failed. E40 tried the **dendrogram
merge-gap** on complete linkage (newly viable, since a clusterer that splits the dominant speaker
has a meaningless dendrogram):

| recording | true k | gap_k |
|---|---|---|
| planning | 3 | 2 |
| call-35 | 2 | **2 OK** |
| call-36 | 2 | **2 OK** |
| webinar | 4 | 3 |

**2/4** - the best of any method tried, and still not usable. The merge-distance ratios are flat
(1.01-1.17): no decisive signal. Those merge distances also reach ~1.0, i.e. NEAR-ORTHOGONAL pairs
inside one speaker's own cluster - which is the boundary-mixture contamination above, visible from
another angle.

k remains an INPUT (`--speakers`), taken from the meeting invite in deployment.

## Open

1. **Speaker counting.** Four methods, none usable. The one real research gap.
2. **call-36's 10.0%** - an embedding-level failure (ceiling 8.8%), mechanism unknown.
3. **n=4, one voice (Alastair) in all four recordings.** Nothing here says how this behaves on
   speakers the embedder has never heard, on similar voices, or on overlapping speech.
4. **Whisper's hallucination is now fixed for silence** - but no test covers music, hold tone, or
   crosstalk, which are the same class of out-of-distribution input.

Evidence: this file; e39-solving-clustering.md; real-audio-run1.md; tools/{diarise,spk_segments,
spk_embed,diarise_eval}.py; manifests/MANIFEST.md. Recordings are real personal data - gitignored
var/meetings/, never committed; described by SHAPE only.
