# E42: large beats small on real speech (10.7% vs 13.7%) - but small OMITS and large FABRICATES (2026-07-17)

# File: results/transcription/e42-wer-model-size.md
# Purpose: The missing half of E41 - does model size change quality on actual SPEECH?
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E41 measured silence only and found the failure MODE inverts with model size. Alastair
# proposed the stronger claim that "smaller models may actually be better quality than bigger models
# for transcription". REFUTED: large-v3-turbo disagrees with the reference 10.7% vs small's 13.7%,
# i.e. small is ~28% worse. But the error COMPOSITION confirms and strengthens the E41 asymmetry:
# small's errors are DELETIONS (267 vs 29 insertions) and large's are INSERTIONS (95 vs small's 29).
# Small under-generates; large over-generates. Config answer: large-v3-turbo + VAD wins on BOTH axes.

## What this measures - and what it CANNOT

The reference is an Otter.ai transcript. **Alastair estimates Otter at ~98% accurate (2026-07-17) -
so ~2% is our measurement FLOOR.** A PERFECT transcript would still score ~2% here by correctly
differing from Otter's own errors. Therefore:

- These are **DISAGREEMENT RATES, not word error rates.** The absolute number is an UPPER BOUND on
  true WER, not an estimate of it.
- Config-vs-config comparison is valid (same reference, same floor) but the gap is **compressed**,
  and biased toward whichever model resembles Otter more.
- A config scoring below ~2% would be suspicious, not excellent.

One recording (13.5 min planning meeting), 2570-word reference, standard ASR normalisation
(lowercase, punctuation stripped, contractions expanded) so typography is not scored as word errors.

## Result

| config | words | **disagreement** | sub | **del** | **ins** |
|---|---|---|---|---|---|
| **large-v3-turbo** | 2550 | **10.7%** | 65 | **115** | **95** |
| **large-v3-turbo + VAD** | 2585 | **10.6%** | 72 | 93 | 108 |
| small | 2332 | 13.7% | 57 | **267** | 29 |
| small + VAD | 2405 | 14.7% | 82 | 230 | 65 |

### Alastair's hypothesis is REFUTED

> "smaller models may actually be better quality than bigger models for transcription"

**No.** large-v3-turbo is ~28% better on real speech (10.7% vs 13.7%). Recorded as refuted rather
than reworded: it was a checkable claim, and the check answered it.

E41 could never have supported it - **every E41 fixture contained NO SPEECH.** E41 measured what
whisper does with silence and was literally silent on transcription quality. Extending a
silence-only result into a quality claim would have been the same error class as F17's headline: a
true measurement extended to a scenario it never covered.

### What DOES survive - and it is the interesting part

The error COMPOSITION inverts with model size, and it matches E41 exactly:

| | small | large |
|---|---|---|
| **deletions** (drops real words) | **267** | 115 |
| **insertions** (adds unspoken words) | 29 | **95** |
| on SILENCE (E41) | `[BLANK_AUDIO]` - self-declared omission | `Thank you.` - plausible fabrication |

> **Small under-generates; large over-generates. The failure MODE inverts with model size, even
> though large is more accurate overall.**

That is coherent across two independent experiments (silence and speech) and it is the defensible
version of Alastair's intuition. It has a real consequence: **large's errors are the dangerous kind**
(words nobody said, invisible to a reader), while small's are the visible kind (missing words, which
a reader notices as a gap). Accuracy and safety are not the same axis.

## Config answer: large-v3-turbo + VAD

Best on BOTH axes, so there is no trade-off to manage:

- **Quality:** 10.6%, marginally better than large without VAD (10.7%) and far better than small.
- **Safety:** 0 fabrications across E41's 72 silence conditions.
- VAD **hurts** small (13.7% -> 14.7%) but not large.

## Usability verdict (Alastair's actual goal)

10.6% disagreement with a ~2% floor implies true WER somewhere near **~8-9%**. Honest read:
**usable for meeting notes, summaries and search; marginal for verbatim quotation.** Combined with
diarisation at 3.51% duration-weighted segment error, the stack produces attributed notes that are
good enough to work from and NOT good enough to quote from without checking.

## Limits

**One recording, one reference, one language.** The 2570-word reference was hand-copied from Otter's
display, so its own fidelity is a second uncontrolled variable on top of Otter's ~2%. Not tested:
medium/large-v2/large-v3 (non-turbo), decoding parameters (left at whisper.cpp defaults, not swept),
or the other three recordings. `--max-len 60` throughout.

Before any of this is published, the honest fix is a public dataset with real ground truth (AMI or
LibriSpeech) - that removes BOTH the Otter floor and the hand-copy variable, and it is the same fix
the diarisation side needs (see docs/plans/2026-07-17-diarisation-landscape-research.md).

Evidence: this file; tools/wer_bench.py; var/meetings/truth/survey-text.txt (gitignored - real
meeting content); e41-silence-hallucination.md (the silence half); docs/FINDINGS.md F44.
