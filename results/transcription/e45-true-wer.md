# E45: true WER says large-v3-turbo 2.40%, small 3.35% - and the BROKEN harness had said the opposite (2026-07-17)

# File: results/transcription/e45-true-wer.md
# Purpose: E42's model-size question, settled against real human ground truth.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E42 answered "are smaller whisper models better?" using an Otter.ai reference (~98%
# accurate, hand-copied), which gave disagreement rates with a ~2% floor rather than WER. This
# settles it on LibriSpeech test-clean - the standard benchmark, real human transcripts, and a
# PUBLISHED expected value that doubles as a harness check. It caught a bug in my own harness that
# had inverted the answer toward the hypothesis under test.

## Result

| model | **WER** | sub | del | ins |
|---|---|---|---|---|
| **large-v3-turbo** | **2.40%** | 88 | 10 | 11 |
| small | 3.35% | 130 | 14 | 8 |

200 utterances, 4542 reference words, LibriSpeech test-clean, human transcripts.

**2.40% matches the published figure for whisper large-v3 on test-clean (~2-3%)**, which validates
the harness as well as the measurement.

> **Alastair's hypothesis - "smaller models may actually be better quality than bigger models for
> transcription" - is REFUTED for a second time, now against real human ground truth.**
> large is ~28% better on meeting audio (E42) and ~28% better on read speech (here).

## The harness bug that confirmed the hypothesis

The first version of this benchmark batched 10 utterances into one wav separated by 1s gaps, to
amortise whisper's per-call startup. It produced:

| harness | large-v3-turbo | small | apparent verdict |
|---|---|---|---|
| **BROKEN** (batched) | 16.23% | **13.03%** | "small is better" - **confirms the hypothesis** |
| **FIXED** (per-utterance) | **2.40%** | 3.35% | "large is better" - **refutes it** |

The bug did not add noise. **It inverted the answer, toward the result we hoped to find.** Whisper
dropped audio from the concatenated files - visible in the error profile as 511 deletions vs 55
insertions, i.e. mass omission rather than mistranscription.

**What caught it: LibriSpeech has a published expected value.** 16.23% on test-clean is impossible
for large-v3-turbo, and being 6x off a well-known number is a loud, unambiguous signal. Had I run
this on our meeting corpus - where no expected value exists - the broken harness would have produced
a plausible number, confirming the hypothesis, and I would have shipped it.

This is the argument for public benchmarks with known values, stated as strongly as the evidence
allows: **they are not just data, they are an instrument check.**

## Error composition: the E42 asymmetry is real but small on clean speech

| | small | large |
|---|---|---|
| substitutions | 130 | 88 |
| deletions | 14 | 10 |
| **insertions** | **8** | **11** |

Large still inserts slightly more than small (11 vs 8) - the same over-generation tendency measured
on meeting audio (E42: large 95 insertions vs small 29) and on silence (F44: large fabricates
"Thank you.", small emits self-declaring `[BLANK_AUDIO]`). But on clean read speech the effect is
tiny and swamped by large's substitution advantage. **The failure-MODE asymmetry survives; the
quality claim built on it does not.**

## Scope

LibriSpeech is read audiobook speech: clean, single-speaker, no crosstalk, no meeting acoustics.
**It is the EASY case and 2.40% must never be quoted as our meeting transcription accuracy.** The
meeting figure is ~10.6% disagreement vs Otter (E42), whose true WER is unknown because that
reference carries a ~2% floor. What this establishes is the model COMPARISON, cleanly, and that
the transcription harness is sound.

Not tested: medium, large-v2, large-v3 (non-turbo); decoding parameters (whisper.cpp defaults, not
swept); other languages; VAD on/off for WER (VAD matters for silence, F44, not for continuous read
speech).

Evidence: this file; tools/librispeech_wer.py; e42-wer-model-size.md (the Otter-based version this
validates); F44 (the silence half); manifests/MANIFEST.md. Corpus: LibriSpeech (CC-BY-4.0) -
attribution required.
