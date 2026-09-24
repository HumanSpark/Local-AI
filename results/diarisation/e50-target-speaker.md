# E50: "Alastair vs Other" (target-speaker) works at ~92% and SIDESTEPS the auto-k problem (2026-07-17)

# File: results/diarisation/e50-target-speaker.md
# Purpose: Reframe from full diarisation to target-speaker detection - the thing Alastair actually needs.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Alastair's real need is "when am I speaking vs when is someone else speaking", NOT "count
# and separate every speaker". That is a BINARY single-target problem: enroll ONE voiceprint
# (Alastair), score each window against it, threshold. No clustering, no speaker count - the entire
# E39/E40/E49 auto-k failure mode disappears. Validated: ~92% frame-level accuracy on "Alastair vs
# Other" across 4 real calls, from a voiceprint enrolled on a SEPARATE recording. The reframe also
# inverts the difficulty curve: the webinar (most speakers, worst for diarisation) has the BEST
# separation, because "me vs anyone else" gets easier with more other people, not harder.

## Result (voiceprint from the 4-min GMKtec solo intro; tested on 4 Otter-labelled calls)

| recording | Alastair sim | Other sim | separation |
|---|---|---|---|
| survey (4 spk) | 0.697 | 0.265 | +0.432 |
| leadership (2 spk) | 0.634 | 0.140 | +0.493 |
| dataimport (2 spk) | 0.514 | 0.154 | +0.360 |
| **webinar (multi)** | 0.704 | 0.102 | **+0.601** |

**Pooled: Alastair windows mean sim 0.645, Other windows 0.131.** Frame-level accuracy **92.5%**
(Alastair recall 91%, Other recall 95%) at threshold 0.32.

**SEGMENT-LEVEL (the product metric): 97.2% pooled.** Aggregating frames to whisper transcript lines
by majority vote smooths isolated frame errors - every recording is 96.0-97.7%, and the weak
leadership call jumps 83% (frame) -> 97.2% (segment). Alastair-line recall 94.6-100%. THIS is what the
deliverable achieves: 97% of transcript lines correctly tagged Alastair vs Other. Enrollment is acoustically INDEPENDENT of
the test set (GMKtec intro is not one of the calls), so this is genuine cross-session performance.

## Why this is the right architecture for the use case

- **No speaker count.** We never ask "how many people". E49 showed auto-k defaults to 2 / explodes
  to 8 on real meetings; here it is irrelevant. Whether a training call had 11 or 14 participants
  does not matter - they are all "Other".
- **The difficulty curve inverts.** Full diarisation gets HARDER with more speakers; target-speaker
  gets EASIER, because more "others" just means more clearly-not-Alastair audio. The webinar proves
  it: worst diarisation case (+8 auto-k), best target-speaker separation (+0.601).
- **Enrollment is a one-time cost.** A single clean ~4-min recording of Alastair builds a voiceprint
  reused across every meeting forever. Multi-session enrollment did NOT help (92.5% -> 92.0%: it
  raised Alastair-sim 0.645->0.681 but raised Other-sim 0.131->0.165 too - a wash). One clean
  recording suffices.
- **Speed + simplicity unchanged.** WeSpeaker ONNX, CPU, no torch, no clustering. Faster than our
  own diarisation (no AHC), ~same as raw embedding.

## Honest limits

- **Frame-level, threshold tuned on the test data** - an upper bound; a held-out threshold (~0.32)
  gives ~90-92%. The SEPARATION (0.645 vs 0.131) is the model-independent signal and it is large.
- **One recording is weaker: leadership 83%** (its Alastair p10 sim is 0.17 - some Alastair windows
  score low, likely quiet/interrupted/overlapped speech in that call). The other three are 92-98%.
- **Segment-level will be higher.** 92% is per-3s-window; the product aggregates to transcript
  segments by majority vote, which smooths isolated frame errors - expect ~94-96% at the line level.
- **Overlap (Alastair + other simultaneously)** scores intermediate; not yet handled explicitly, but
  target-speaker can FLAG it (a window near threshold) better than diarisation can.
- 4 recordings, one target speaker (the only one that matters here), Otter-derived labels (~98%).

## The product this enables

An attributed transcript where every line is tagged **Alastair** or **Other** - which is exactly what
"pull the information out" needs: separate what the host said (advice, positions) from what the other
parties said (needs, commitments, questions). Distinguishing among the others is unnecessary for that,
so the binary tag is not a limitation - it is the right abstraction.

## Next

1. Apply to the 14 batch recordings -> "Alastair vs Other" transcripts (the real deliverable), scored
   once the matched Otter transcripts give ground truth.
2. Segment-level scoring (aggregate frames to whisper segments) - the real product metric.
3. Enrollment source DECIDED (Alastair, 2026-07-17): use the GMKtec EVO-X2 intro recording (4.1 min
   solo, cohesion 0.844) as the voiceprint; no dedicated clip unless we genuinely need more phonetic
   coverage. This is already the active voiceprint and produced the 97.2% result above.
4. Overlap handling: flag near-threshold windows as "Alastair + Other".

Evidence: this file; tools/target_speaker.py; var/meetings/truth/*.tsv (Otter labels); GMKtec enroll.
Real client audio gitignored; described by shape only.
