# E41: Whisper invents "Thank you." out of pure digital silence - ~2/min, and the BIGGER model is the DANGEROUS one (2026-07-17)

# File: results/transcription/e41-silence-hallucination.md
# Purpose: Systematic silence-hallucination benchmark. Pre-reg: ../diarisation/e41-silence-hallucination-prereg.md.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: whisper.cpp large-v3-turbo fabricates speech over silence at a near-constant ~2 segments
# per minute, and 97% of it is the single phrase "Thank you." It does this on PURE DIGITAL ZERO -
# a file containing literally nothing but zeros, with no speech anywhere and no acoustic signal to
# misinterpret. VAD eliminates it completely (0/72 conditions). The most consequential result is a
# reversal: `small` emits MORE fabricated segments (298 vs 208) but 85% are self-declaring
# annotations like [BLANK_AUDIO]; large-v3-turbo emits plausible speech. Counted by HARM rather than
# volume, **large-v3-turbo is 4.9x worse than small** - "use the better model" makes it worse.

## Why this matters more than any DER number in this register

Transcription has been a published capability of this box since Phase A (28x real time,
C-CAPABILITY-TRANSCRIPTION-001) and it is the INPUT to the diarisation stack. We never checked what
it does with silence.

**A wrong speaker label is visible. Invented speech is not.** A reader can question a turn attributed
to the wrong person. Nobody can detect "Thank you." inserted into a client meeting transcript - it is
grammatical, plausible, and will be attributed to a named person at a real timestamp.

## Method

Synthetic fixtures (numpy + soundfile, 16 kHz mono) so ground truth is EXACT - we generate the
silence, so we know precisely which regions contain no speech. Real speech anchor where a condition
needs one: whisper.cpp's `jfk.wav`. Scoring: any transcript segment lying wholly inside a
known-silent region is a fabrication. 72 conditions = 4 positions x 3 silence types x 6 durations,
run three times (large no-VAD, large+VAD, small no-VAD). No personal data - publishable as-is.

## Prediction resolution (registered in e41-...-prereg.md, committed 5c7a64d BEFORE any run)

| ID | Prediction | Result | Verdict |
|---|---|---|---|
| **S1** | Pure silence with NO speech anywhere -> ~zero hallucination; the trigger is CONTEXT | **55 fabrications** from silence-only; digital zero alone hallucinates | **REFUTED** |
| **S2** | Silence AFTER speech hallucinates more than leading | 55 / 54 / 51 / 48 across positions - flat | **REFUTED** |
| **S3** | Rate scales with duration | **~2.0/min, near constant** (1.0-2.2/min across 5-300s) | **HIT** |
| **S4** | Low-level noise > digital zero | 72 / 69 / 67 - digital zero slightly WORST | **REFUTED** |
| **S5** | Text is a small recurring YouTube-ish set | **202/208 = "Thank you."  THREE distinct strings total** | **HIT** |
| **S6** | VAD reduces to zero everywhere | **0 fabrications across all 72 conditions** | **HIT** |
| **S7** | `small` hallucinates more than large | 298 vs 208 by count - but see the reversal below | **HIT by count, INVERTED by harm** |

**4 hits, 3 refutations.** The refutations are the valuable part - S1 in particular.

## S1's refutation is the headline: it is NOT context-bleed

I predicted the fabrication was conditioned on prior speech - that whisper needed something to
continue from. **Wrong.** Feed it a file containing nothing but digital zeros - mathematically
perfect silence, no dither, no signal whatsoever - and it emits "Thank you." at ~2/min:

| silence-only, digital zero | 5s | 10s | 30s | 60s | 120s | 300s |
|---|---|---|---|---|---|---|
| fabrications | 0 | 0 | **1** | **2** | **4** | **10** |

There is no acoustic signal to misinterpret. **The model is transcribing its own prior.**

Position barely matters (silence-only 55, sandwiched 54, leading 51, trailing 48) and silence TYPE
barely matters (digital-zero 72, noise 69, roomtone 67). The effect is essentially a **constant
background rate of ~2 fabrications per minute of silence, independent of everything except duration.**

## S5: three distinct strings across 208 fabrications

| count | share | text |
|---|---|---|
| **202** | **97.1%** | `Thank you.` |
| 4 | 1.9% | `.` |
| 2 | 1.0% | `And so, my fellow Americans, ask not what your country can` |

The mechanism hypothesis registered in advance - an autoregressive decoder with no "emit nothing"
option falling back to the most over-represented phrase in a YouTube-heavy training tail - **survives
this test.** A model straying randomly would not produce three strings in 208 tries.

The two stray JFK strings are the tell that CONTEXT-BLEED also exists, as a separate and much rarer
mode: real prior speech leaking into the silence that follows it. So there are TWO failure modes -
an unconditional prior (dominant) and context-bleed (rare). S1 refutes context-bleed as the *primary*
mechanism, not as a mechanism.

## THE REVERSAL: the better model is the dangerous one

S7 is where counting segments hides the truth. My own metric was wrong - it counted volume, not harm.

| model | total | **annotations** (self-declared non-speech) | **DANGEROUS** (plausible speech) | top dangerous |
|---|---|---|---|---|
| **large-v3-turbo** | 208 | 4 | **204** | 202x `Thank you.` |
| **small** | 298 | **256** | **42** | 15x `you` |
| **large + VAD** | **0** | 0 | **0** | - |

`small` emits MORE segments, but 85% are `[ Silence ]`, `[no audio]`, `[BLANK_AUDIO]` - the model
TELLING YOU there is no speech. Those are self-labelling, trivially filtered, and harmless to a human
reader. large-v3-turbo emits grammatical English.

> **large-v3-turbo produces 4.9x MORE DANGEROUS fabrications than small (204 vs 42).**
> "Use the better model" makes the SAFETY problem WORSE.

This is worth stating plainly because it is counterintuitive and it inverts the obvious mitigation.
The larger model is better at transcription AND better at producing convincing fiction, because
convincing fiction is what a stronger language prior buys you.

## S6: VAD is a fix, not a mitigation

**0 fabrications across all 72 conditions.** Not reduced - eliminated. E40's claim that "VAD
eliminates it" stands, now on 72 conditions rather than one anecdote. `tools/diarise.py` raises if
the VAD model is absent rather than degrading quietly.

## Client-facing consequence

Any Whisper transcription pipeline WITHOUT VAD silently inserts ~2 fabricated utterances per minute
of silence. A one-hour recording with 10 minutes of dead air (joining early, a break, someone muted)
gets **~20 invented "Thank you" lines**, attributed to whoever the diariser thinks was speaking.
Nothing in the output marks them as fabricated.

This is not a sparkmax defect, a llama.cpp quirk, or a quantisation artifact - it is a property of
the Whisper decoder, and Alastair independently reports the same "thank you" hallucination from
hosted frontier-lab transcription services (2026-07-17). **Scope discipline: we measured whisper.cpp
+ these GGML weights on this box. The hosted-API case is consistent with a shared family trait but
was NOT tested here** - their decoding parameters (temperature fallback, no_speech_threshold,
condition_on_previous_text) differ and are not visible to us. Testing that needs those APIs run
directly; registered as open.

## Limits

- One implementation (whisper.cpp), two model sizes, one language, synthetic silence.
- Not tested: music, hold tone, crosstalk, or background speech - the same class of
  out-of-distribution input, and the meeting-realistic ones.
- Not tested: hosted APIs (OpenAI, Deepgram, AssemblyAI), which is what would turn Alastair's
  observation into a measured cross-vendor claim.
- `--max-len 60` is in the command line; not varied. Decoding parameters were left at whisper.cpp
  defaults throughout and were not swept.

Evidence: this file; pre-registration ../diarisation/e41-silence-hallucination-prereg.md (committed
5c7a64d BEFORE any run); tools/silence_bench.py; results/transcription/silence-{large-novad,
large-vad,small-novad}.json; ../diarisation/e40-vad-and-limits.md (the incidental discovery this
systematises); manifests/MANIFEST.md (the VAD model's provenance).
