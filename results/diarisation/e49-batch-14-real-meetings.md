# E49: 14 real meetings (11 hours) through the fast path - transcription solid, auto-k is the deployment gap (2026-07-17)

# File: results/diarisation/e49-batch-14-real-meetings.md
# Purpose: Batch fast-path run over Alastair's real meeting archive. Robustness + the k-in-production gap.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: 14 real Zoom/Teams recordings (668 min / 11.1 h), run through the pure fast stack
# (whisper large-v3-turbo + VAD; Silero VAD + WeSpeaker + complete-linkage AHC with AUTO-estimated k).
# 14/14 succeeded at ~28x real time. Transcription is production-ready. The finding is that AUTOMATIC
# SPEAKER COUNT is the real deployment gap: it mostly defaults to 2 and occasionally explodes (one
# webinar -> 8), exactly as E39/E40 predicted. The majority-vote attribution layer partially
# self-corrects (a solo narration estimated k=2 collapsed to 1 speaker in the output).
#
# Content is real client data (names, businesses): transcripts are gitignored. Only de-identified
# stats (duration, estimated k, speaker-share SHAPE, speech %, speed) appear here.

## Run: 14/14 succeeded, ~28x real time

| duration (min) | est k | speaker-share shape | speech % | speed |
|---|---|---|---|---|
| 109.8 | 2 | 90/10 | 98% | 28x |
| 92.7 | 2 | 80/20 | 95% | 28x |
| 68.2 | 2 | 54/46 | 96% | 29x |
| 65.6 | 3 | 63/19/18 | 99% | 27x |
| 63.3 | **8** | 75/6/5/4/4/3/1/1 | 96% | 27x |
| 62.2 | 2 | 82/18 | 91% | 33x |
| 61.1 | 2 | 75/25 | 96% | 30x |
| 29.2 | 2 | 68/32 | 99% | 24x |
| 28.7 | 2 | 68/32 | 68% | 36x |
| 26.9 | 2 | 61/39 | 80% | 36x |
| 20.8 | 2 | 72/28 | 97% | 28x |
| 18.8 | 2 | 62/38 | 88% | 30x |
| 16.4 | 2 | 52/48 | 98% | 22x |
| 4.1 | 2 | **100** (solo) | 99% | 27x |

## What works

- **Transcription: 14/14, ~28x real time, no failures** across 11 hours of varied audio (2-person
  calls, webinars, monologue dictation, a product-intro narration). This is the production-ready half.
  Spot-checked output is clean and coherent (a 2-person client call read as a correct back-and-forth).
- **Robustness:** each file wrapped independently; a single bad file could not abort the batch. None did.
- **Attribution is good where there are ~2 balanced speakers** (share shapes near 50/50-65/35): these
  are the real 2-person calls, and the transcripts are usable now.

## The gap: automatic speaker count

- **est_k mostly defaults to 2** (11 of 14), regardless of true content - silhouette's known small-k
  bias (E39/E40). One webinar exploded to **8** (one presenter at 75% shattered into 7 fragments).
- **Monologues are mis-counted:** the solo product-intro was estimated k=2. It survived only because
  the majority-vote attribution assigned 100% of segments to one cluster - the spurious second
  cluster got no text. The attribution layer is more robust than the raw count, but that is luck, not
  design.
- **Skewed share shapes are the tell:** 90/10, 100/0, 75/6/5/4... flag monologues/presentations where
  the extra "speakers" are over-splits; balanced shapes flag genuine multi-party calls.

**This is the E39/E40 unsolved problem biting in production.** The fast path transcribes anything, but
it cannot reliably decide HOW MANY speakers. In real deployment k comes from the meeting invite; for
this archive it comes from the Otter transcripts (arriving later), which set the true count per file
and enable both (a) attribution scoring and (b) a re-run with correct k.

## Speed at scale

668 min processed in ~24 min of wall clock (~28x aggregate). A day of meetings diarises in the time it
takes to make coffee. Per-file speed 22-36x (auto-k silhouette adds overhead on top of the ~60x raw
diarisation; it is the k-search, not the pipeline, that costs the difference).

## Next (when Otter transcripts arrive)

1. Score attribution accuracy per file against Otter (the metric Otter supports; see E48).
2. Re-run with TRUE k per file - the fast path's real accuracy, unconfounded by auto-k.
3. The 14 + the original 4 = 18 real online calls with references: a proper real-world evaluation set,
   the strongest test yet of the production config on the actual deployment audio.

## Limits

Auto-k (silhouette, subsampled) is a stopgap, not a solution. No accuracy numbers here - no ground
truth yet. Transcription WER not measured on these (no reference); LibriSpeech (E45) is the WER
authority. Real client audio - gitignored, described by shape only.

Evidence: this file; var/meetings/batch2/out/ (gitignored - transcripts + batch-stats.json);
tools/batch_fastpath.py; e48-real-online-calls.md; e39/e40 (the auto-k problem this surfaces at scale).
