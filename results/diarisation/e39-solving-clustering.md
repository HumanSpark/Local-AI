# E39: the diarisation failure was ONE WORD - and the sophisticated fix was the worst method (2026-07-17)

# File: results/diarisation/e39-solving-clustering.md
# Purpose: Autonomous attempt to solve E38b's failures. Result: clustering SOLVED, counting NOT.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E38b left three open items: a recording where the system beat no baseline, an unproven
# excuse blaming the reference, and unsolved speaker counting. Result: the failing recording is
# fixed (16.7% -> 3.2% DER) by changing average linkage to COMPLETE linkage - one word. The excuse
# was REFUTED acoustically: the failure was ours. Speaker counting remains UNSOLVED - three
# principled methods all failed, including the spectral eigengap work that consumed most of the
# session and scored WORST of everything tried.

## Corpus

Four real recordings, 147 min: one ~13.5 min internal planning discussion, two ~35 min client
calls, one ~63 min webinar. Reference: Otter.ai (a commercial system, NOT human truth - its errors
are inside every DER here). Recordings, references and transcripts are real personal data in
gitignored var/meetings/, never committed; described by SHAPE only.

## Headline: complete linkage reaches the supervised ceiling

All methods given the CORRECT speaker count, so the clustering ALGORITHM is the only variable:

| method | planning | **client-call-35** | client-call-36 | webinar | **mean** |
|---|---|---|---|---|---|
| AHC-**average** (what we shipped) | 14.0% | **16.7%** | 8.7% | 5.5% | **11.2%** |
| **AHC-complete** | **4.7%** | **3.2%** | 9.9% | 2.7% | **5.1%** |
| AHC-ward | 4.9% | 16.7% | 9.9% | 2.7% | 8.5% |
| KMeans | 4.2% | 16.4% | 9.5% | 2.6% | 8.2% |
| **Spectral** (the eigengap work) | 5.1% | 28.9% | 9.5% | **30.8%** | **18.6%** |
| *majority baseline* | *17.1%* | *15.3%* | *48.5%* | *45.1%* | *31.5%* |
| *supervised ceiling* | *4.1%* | *2.7%* | *8.8%* | *2.1%* | ***4.4%*** |

**Complete linkage: 5.1% mean DER against a supervised ceiling of 4.4%.** Unsupervised clustering
now extracts essentially everything the embeddings contain. The recording that failed outright goes
**16.7% -> 3.2%**, a 5x improvement, from changing `linkage="average"` to `linkage="complete"`.

### The mechanism

Average linkage merges on MEAN inter-cluster distance. On a recording where one speaker holds 84.7%
of the audio, it is cheaper to CLEAVE the big diffuse speaker in half than to isolate the small tight
one - both outcomes are "k=2", and the split scores better on mean distance. Complete linkage merges
on WORST-CASE distance, so it refuses to unite any pair of clusters containing a far-apart pair, and
the minority speaker survives as its own cluster.

The bug never appeared on the synthetic fixture because two Kokoro voices are balanced 50/50 and
maximally distinct. **The fixture could not contain the failure.** Third time that fixture's
optimism has cost something (tdrz probe -> E38 margin -> here).

### The uncomfortable part

**The spectral/eigengap work - the sophisticated thing this session was mostly spent on - is the
WORST method in the table** (18.6% mean, 30.8% on the webinar, worse than its own baseline). The fix
was a linkage parameter never questioned since it was chosen for the synthetic fixture. Recorded
because the effort/value ratio is the lesson: the cheap unexamined default was the bug, and the
expensive new machinery was noise.

## Speaker counting: UNSOLVED. Three methods, all failed.

Given the true k, complete linkage hits 5.1%. No automatic chooser finds the true k:

| chooser | mean DER (complete linkage) | k correct |
|---|---|---|
| **ORACLE** (true k - the ceiling) | **5.12%** | 4/4 |
| fixed k=3 (least-bad constant) | 9.51% | 1/4 |
| silhouette | 10.11% | 1/4 |
| all-clusters->=2% rule | 11.27% | 1/4 |

### The eigengap attempt, and why it is reported as a failure

Spectral eigengap (Wang et al. 2018 refinement chain) is the standard answer. It returned **k=3 for
every recording** - a constant, not an estimate. Sweeping its `p_percentile` knob:

| p_percentile | planning (3) | call-35 (2) | call-36 (2) | webinar (4) | correct |
|---|---|---|---|---|---|
| 0.70 | 1 | 1 | **2** | 3 | 1/4 |
| 0.90 | 2 | 3 | **2** | 3 | 1/4 |
| 0.95 | **3** | 3 | 3 | 3 | 1/4 |

**No setting exceeds 1/4.** The estimate swings 1->3 on the hyperparameter, so the output is
dominated by a knob I chose rather than by the audio. Any "success" would be picking p to match
answers already known - the exact sin refused elsewhere. Reported as a failure, not tuned green.

### A real bug found on the way (fixed; changed nothing)

The Laplacian had NEGATIVE eigenvalues - impossible, its spectrum is provably in [0,2]. Cause: the
refinement's row-max normalisation destroys the symmetry established one line earlier, and
`eigvalsh` then silently reads only the lower triangle - eigenvalues of a matrix never built. Fixed
by re-symmetrising; `spk_count.py` now RAISES on an asymmetric affinity or an out-of-range spectrum.

**Honest null: the fix changed no result.** eigvalsh's implicit mirror was similar enough to yield
identical k and DER. Kept anyway - the guard makes the next malformed affinity fail loudly instead
of returning a plausible number. The out-of-range eigenvalue was the ONLY visible symptom; the k
estimate looked entirely reasonable.

## The excuse from E38b: REFUTED. The failure was ours.

E38b floated a suspect for the failing call: that Otter merged Marina into an 8-minute Alastair
block, so our correct change-detection was scored as error. I said it needed a human to listen.
It did not - `tools/adjudicate_dispute.py` builds a VOICEPRINT for each speaker from their
UNDISPUTED turns (outside the disputed block, so the test cannot beg the question) and classifies
the block's interior against them.

- Voiceprints: 22 undisputed turns each; they score **0.196** against each other (distinct - the
  test discriminates).
- Inside the disputed block: **94 of 97 windows match Alastair** (0.69-0.87 vs Marina's 0.09-0.20).

> **VERDICT: the block really is one speaker. Otter was right. The failure was OURS.**

A plausible story, built from reading conversational back-channel in the transcript, that flattered
us. Flagged as "suspect, not finding" at the time - correct - but better not floated at all.
Its refutation is what forced the search that found the linkage bug.

## Shipped

`tools/diarise.py`: complete linkage; 3.0s/1.0s windows; energy floor 1e-3; `--speakers` supplied.
**Speaker count is now an INPUT, not a discovery** - in deployment the attendee count is known from
the meeting invite, which turns an unsolved research problem into a parameter. Default k=3 is the
least-bad measured constant and is documented in `--help` as a GUESS.

Verified end-to-end on the recording that previously failed: two speakers cleanly separated.

## Open

1. **Speaker counting.** The one real research gap. Worth trying: VAD-based re-segmentation into
   speaker-homogeneous turns before clustering (all four recordings cluster fixed 3s windows, which
   guarantees boundary mixtures); PLDA scoring instead of raw cosine.
2. **Whisper hallucinates on silence** - the 35-min call's dead air produced repeated "Thank you"
   segments. A transcription artifact, not diarisation, but it would reach a user. Needs `--vad`.
3. **n=4, one voice (Alastair) in all four.** No evidence about speakers this embedder has never
   heard, similar voices, or overlapping speech.

Evidence: this file; results/diarisation/real-audio-run1.md (E38/E38b); tools/{diarise,spk_count,
diarise_eval,diarise_sweep,adjudicate_dispute}.py; embedder-validation.md (the synthetic result whose
optimism this corrects for the third time).
