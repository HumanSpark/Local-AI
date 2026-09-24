# E38: real audio breaks the synthetic verdict - the margin was measured in the wrong universe (2026-07-17)

# File: results/diarisation/real-audio-run1.md
# Purpose: First diarisation run on REAL meeting audio. Predictions + findings. R&D record.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: The synthetic fixture's separation margin (+0.5884) did not survive real audio. The
# collapse is NOT where I predicted: real same-speaker similarity is fine (0.85, vs TTS 0.84); it is
# DIFFERENT-speaker similarity that rises from 0.045 (TTS) to 0.337 (real), because real speakers
# share a room, mic, codec and accent while two TTS voices share nothing. Usable margin falls from
# +0.588 to ~+0.075. First run reported 94 speakers on a ~4-speaker meeting. Diagnosis: not a
# threshold error - a long tail of fragment clusters. Speaker COUNT remains unresolved: three
# principled methods give two different answers and nothing on hand can adjudicate.

## Corpus (privacy-bounded)

Four real recordings, 147 minutes total, supplied by Alastair from his own meeting archive:
one ~13.5 min internal planning discussion, two ~35 min client calls, one ~63 min webinar.
**Recordings and transcripts are real personal data: they live in gitignored var/meetings/ and are
NEVER committed.** Only aggregate findings enter the repo. For publication, recordings are
describable by SHAPE only ("a one-hour webinar", "client calls") - never by organisation, client,
or participant. Confirmed by Alastair 2026-07-17.

## Predictions (stated in-session BEFORE the run)

| ID | Prediction | Result | Verdict |
|---|---|---|---|
| R1 | Speaker count comes out too HIGH (boundary-window mixtures, worse than synthetic) | 94 on a ~4-speaker meeting | **HIT** (direction), but the MECHANISM was wrong - see below |
| R2 | Transcription will be fine - large-v3-turbo on real speech is its home turf | Clean, coherent, correct | **HIT** |
| R3 | The 63-min webinar may be near-single-speaker (different shape from a meeting) | genuine 4-way panel: 54.9/23.5/18.6/2.8% | **MISS - refuted** |

## The finding: the fixture flattered the TASK, not the extractor

After seeing 94 clusters I hypothesised that REAL same-speaker similarity would be much lower than
TTS (one person varies across a meeting: volume, pitch, mic distance, laughter). **That hypothesis
is WRONG, and the measurement refuted it.** Recorded because the wrong hypothesis was plausible and
I nearly acted on it by retuning the threshold.

Free ground truth trick: overlapping ADJACENT windows are almost certainly the same speaker, so they
sample the real same-speaker population with no labels required.

| population | TTS fixture | REAL meeting (3s windows) |
|---|---|---|
| **same**-speaker mean sim | 0.84 | **0.85** - essentially IDENTICAL |
| **different**-speaker mean sim | **0.045** | **0.337** |
| different-speaker p90 | - | 0.552 |
| different-speaker max | **0.126** | **0.714** |
| **usable margin** (same p10 - diff p90) | **+0.588** | **~+0.075** |

**The same-speaker side was never the problem.** Two Kokoro voices from different TTS models, one
female and one male, are about as acoustically unrelated as two signals can be - hence 0.045. Real
people in one room share microphone, codec, room acoustics and accent, so two DIFFERENT speakers
still score 0.337 and sometimes 0.714. On min/max the populations **overlap outright**.

> The synthetic margin of +0.5884 was real, reproducible, and measured the wrong universe. It proved
> the extractor CAN separate voices; it said nothing about the difficulty of the actual task,
> because TTS has neither within-speaker variation nor shared-channel between-speaker similarity.

This is the tdrz lesson recurring one level up. There, the fixture was wrong about the model. Here,
the fixture was wrong about the DIFFICULTY - which is subtler, because the extractor genuinely works.

Window length matters: 1.5s gives same-speaker 0.777, 3.0s gives 0.847. Longer windows nearly double
the usable margin. Adopted 3.0s/1.0s hop (a real cost: a window cannot sit inside a shorter turn).

## The "94 speakers" was not a threshold error

Sweeping AHC average-linkage on the 13.5-min meeting (810 windows @ 3s):

| threshold | total clusters | clusters holding >=2% of windows |
|---|---|---|
| 0.30 | 194 | **4** |
| 0.35 | 130 | **4** |
| 0.40 | 85 | **4** |
| Ward @ 4.0 | 4 | **4** |

The gross structure is ~4 speakers across a wide threshold range; the rest is a long tail of tiny
fragment clusters (boundary mixtures, noise, breaths). Raising the energy floor 1e-4 -> 1e-3 removed
half the windows as near-silence. So R1 hit on direction but my stated mechanism ("boundary-window
mixtures dominate the count") was only part of it: the count is dominated by fragments AND by
average-linkage stalling early on a broad, overlapping similarity distribution.

## RESOLVED SAME SESSION: Otter.ai ground truth arrived - DER 5.2%

Alastair supplied Otter.ai diarised transcripts for the recordings (the audio came from there).
That converts cluster-count eyeballing into a measured benchmark: **our ungated on-prem stack vs a
commercial cloud service, on identical audio.**

**Otter's answer for the 13.5-min meeting: 4 speakers.** Scoring the three methods that disagreed:

| method | answer | vs Otter |
|---|---|---|
| clusters holding >=2% of windows | **4** | **CORRECT** |
| Ward linkage @ 4.0 | **4** | **CORRECT** |
| silhouette over k=2..8 | 2 | **WRONG** |

My suspicion of silhouette was right, and now it is measured rather than suspected.

### DER against Otter (frame-level, 3s windows @ 1s hop, optimal cluster->speaker assignment)

| k | frame accuracy | **DER** |
|---|---|---|
| 2 (silhouette's pick) | 86.5% | 13.5% |
| 3 | 86.0% | 14.0% |
| **4 (the >=2% / Ward pick)** | **94.8%** | **5.2%** |
| 5 | 94.8% | 5.2% |

**5.2% DER at the right speaker count.** Confusion matrix is a clean one-to-one mapping - the stack
tracks people, not artifacts:

| Otter speaker | C0 | C1 | **C2** | **C3** |
|---|---|---|---|---|
| Alastair | 7 | 1 | **657** | 6 |
| Speaker 1 | 3 | 2 | 9 | **80** |
| Speaker 2 | 5 | **30** | 6 | 1 |
| Speaker 3 | 0 | 0 | 2 | 0 |

**Choosing k is the single biggest lever in the system: k=2 costs 13.5% DER, k=4 costs 5.2% - a 2.6x
error reduction.** Silhouette would have quietly forfeited most of the accuracy while looking
principled. The >=2%-of-windows rule and Ward both got it right, independently.

**Caveat on the reference:** Otter's "Speaker 3" holds **2 windows** total (a ~2s "Yeah. Okay.
Okay."). Our stack folded it into Alastair. That is plausibly Otter OVER-segmenting rather than us
failing - Otter is a reference, not ground truth from God. DER against it is therefore a
system-vs-system agreement measure, and the residual 5.2% includes Otter's own errors. Not
separable without human labelling; stated rather than ignored.

## SUPERSEDED: the speaker-count question as it stood before ground truth arrived

| method | 13.5-min meeting | 35-min client call |
|---|---|---|
| clusters >=2% of windows | **4** | 3 |
| Ward linkage @ 4.0 | **4** | - |
| **silhouette over k=2..8** | **2** | 3 |

**Three principled methods, two different answers, and nothing on hand can adjudicate.** Silhouette
is known to bias toward small k, so I suspect it - but "I suspect" is not a measurement. This is
NOT reported as solved, and no threshold has been tuned to make the numbers agree: tuning against
a recording whose answer I do not know is guessing, and tuning against one whose answer I do know
is manufacturing.

**Resolution path (Alastair, 2026-07-17): he holds Otter.ai diarised transcripts for all four
recordings** - the audio came from there. That is real ground truth from a commercial system, and it
converts this from cluster-count eyeballing into a measurable **DER (diarisation error rate)**
benchmark: our ungated on-prem stack vs a commercial cloud service, on identical audio. Requested.

## What holds so far

- **Transcription (large-v3-turbo): unaffected and good.** The two-pass architecture delivers what it
  promised - identity is bolted alongside, not traded against.
- **The extractor tracks voices.** A 90-second monologue held one label throughout; adjacent-window
  similarity of 0.85 on real audio confirms embeddings are stable within a speaker.
- **Speed:** 13.5 min of audio -> 40s wall clock (transcription + 810 embeddings + clustering),
  CPU-only for the speaker pass, GPU free. ~20x real time end-to-end.
- **Speaker attribution and count: NOT established on real audio.** Open.

Evidence: this file; tools/diarise.py, tools/spk_embed.py; results/diarisation/embedder-validation.md
(the synthetic result this corrects); results/diarisation/tdrz-probe.md (the same fixture lesson, one
level down). Recordings deliberately absent - gitignored var/meetings/.

## Publication policy for this corpus (Alastair, 2026-07-17)

Recordings are describable by SHAPE, never by identity. Permitted: "a one-hour webinar", "client
calls", "an internal planning discussion", durations, speaker counts, DER. **Never**: organisation,
client, participant names, or subject matter. The recordings, the Otter transcripts and our own
transcripts are real personal data and commercially sensitive: gitignored var/meetings/, never
committed, and no verbatim content enters the repo, the data package, or any published report.

## Next

1. Run the remaining recordings (35-min client call, 63-min webinar) and get DER for each. The
   webinar tests R3 (near-single-speaker shape) and the long-recording case.
2. **Make the k-chooser principled.** The >=2% rule beat silhouette on n=1. That is not a method,
   it is one data point; validate it across all four recordings before it is a rule.
3. Compare against a second reference if one is cheap - Otter's own errors are inside our 5.2%.


## E38b: all three recordings scored - and DER without a baseline is nearly meaningless

**The methodological finding: never report DER without the MAJORITY BASELINE beside it** - what a
system that always emits the dominant speaker, and does nothing else, would score. On a
one-presenter recording a BROKEN single-label system posts a spectacular DER. tools/diarise_eval.py
now refuses to print DER without it.

| recording | real speakers | **majority baseline** | **our DER** | vs baseline |
|---|---|---|---|---|
| 13.5-min internal planning | 4 | 17.1% | **5.2%** (k=4) | **+11.9** |
| 34.6-min client call | 2 (+1 singleton) | 15.3% | **16.7%** (k=2) | **-1.4 FAIL** |
| **62.9-min webinar** | 4 (+3 singletons) | **45.1%** | **2.9%** (k=5) | **+42.2** |

This INVERTS the naive reading. Without the baseline, the survey (5.2%) looks better than the
webinar (2.9% - near-identical). With it, the webinar is a massive win and the survey a modest one:
the survey is 83% one voice, the webinar is a real conversation. **The recording that looks hardest
is where the system proves most valuable; the one that looks easy is where it barely earns its keep.**

Same class of error as F17's same-question concurrency headline: a number that is true, reproducible,
and quietly flattering because the baseline was never stated.

### R3 REFUTED

I predicted the webinar would be near-single-speaker. It is a genuine four-way panel
(54.9 / 23.5 / 18.6 / 2.8%) - and the BEST result of the three. Prediction recorded as a miss rather
than reworded after the fact.

### The client call FAILS - stated, not explained away

On the 34.6-min call the system adds **nothing** over always guessing the dominant speaker
(16.7% vs 15.3% baseline). It is the only recording where one speaker holds 84.7% AND the reference
gives very long monologue blocks.

**Suspect, NOT a finding:** the Otter reference has a visible mis-attribution there - Alastair's
7:08->15:15 block is an eight-minute monologue, inside which Marina audibly speaks ("Yeah, it's
true, and yeah, you're right. And for me, it's also what I have reflected on..."). If Otter merged
her into his block, our system detecting that change is scored AS AN ERROR while being correct.
That would make the reference wrong rather than us. **Unproven without listening to the audio -
flagged as unresolved, not claimed as vindication.** The failure stands until disproved.

### Speed

62.9 min of audio scored in 62s wall clock (~60x real time): transcription on GPU, 3773 embeddings +
clustering on CPU. The GPU stays free for llama-server throughout.

### The >=2% speaker-count rule: not a rule

| recording | >=2% clusters at best k | reference k | best-DER k |
|---|---|---|---|
| survey | 3 | 4 | 4 |
| leadership | 2 | 3 | 2 |
| webinar | 4 | 7 | 5 |

It tracks the right ORDER of magnitude but is not exact, and reference k is inflated by singleton
labels Otter emits for ~2s interjections. It won on n=1 against silhouette; across three recordings
neither is reliable. **Speaker-count selection remains the open problem and the biggest lever.**
