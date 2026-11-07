# E48: on REAL online calls, ours and hybrid tie on attribution (~95%) - the AMI hybrid win shrinks (2026-07-17)

# File: results/diarisation/e48-real-online-calls.md
# Purpose: ours vs hybrid on Alastair's actual 4 Otter-referenced online calls. The deployment check.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E47's hybrid (pyannote VAD + our embeddings) cut AMI IHM error 48%. This tests it on the
# REAL online calls E47 was a proxy for. The metric is forced by the reference: Otter gives speaker
# TURNS with no silence annotation, so standard DER would penalise a good VAD as "miss". Instead we
# report COVERAGE (% of call labelled speech) and ATTRIBUTION ACCURACY (of a system's own speech,
# duration-weighted % where its label maps to Otter's speaker). Result: on real online calls, ours
# and hybrid tie on attribution (~95%); the dramatic AMI hybrid advantage does NOT clearly replicate.

## Result (4 real online calls, supplied k = Otter effective speaker count)

| recording | k | ours coverage / attribution | hybrid coverage / attribution |
|---|---|---|---|
| planning (4spk, 13.5m) | 3 | 99% / 95.1% | 94% / 95.4% |
| client call (2spk, 34.6m) | 2 | 86% / 95.9% | 81% / **97.3%** |
| client call (2spk, 36.2m) | 2 | 91% / 95.6% | 77% / 96.1% |
| webinar (multi, 62.9m) | 4 | 99% / **97.0%** | 95% / 94.8% |

**Attribution is ~95-97% for BOTH systems** - they tie within noise. The hybrid wins the two 2-speaker
client calls (by 0.5-1.4 pts) and loses the webinar (94.8 vs 97.0); planning is a wash.

## Why the AMI hybrid win (48% error cut) did NOT replicate here

On AMI the hybrid halved confusion because a clean VAD stopped feeding non-speech (breath, keyboard,
room noise) into the clustering. On these online calls that effect is small, and the reason is the
audio: **online-call participants are each on their own mic, muted when not speaking, in different
quiet locations.** There is far less shared-room non-speech to pollute the clustering than in an AMI
meeting room. So our simple stack's clustering is already clean enough - ~95% attribution.

**But the coverage column shows the catch the attribution metric cannot:** ours labels 86-99% of each
call as speech; the hybrid labels 77-95%. A real call with pauses is not 99% speech. Ours is
OVER-COVERING - assigning a speaker during silence/pauses - which is exactly the false-alarm error
that DER would catch and this Otter metric cannot (no silence annotation). The hybrid's lower, more
realistic coverage is a quieter, real advantage this test under-rewards. So "they tie on attribution"
is true but does not mean "they are equal": ours is spending some of its output on non-speech that a
proper reference would penalise.

## The honest read for deployment

- **For attributing WHO SAID a transcribed line on a clean online call, our fast stack is already
  ~95%** - good enough for meeting notes, and it needs no torch. The hybrid does not clearly beat it
  on this audio, so the E47 recommendation to adopt the hybrid is WEAKER for online calls than the
  AMI proxy suggested.
- **The remaining question is false alarm**, which neither this metric nor the Otter reference can
  measure. AMI (real DER) said ours over-covers badly (FA was 69% of our error); the coverage numbers
  here are consistent with that. If false alarm matters for the deliverable (a speaker label stamped
  on a silent gap), the hybrid still helps; if only "right speaker when someone talks" matters, ours
  suffices.
- **Settling it needs a reference with silence** - AMI has it (E46/E47), these do not. AMI remains the
  quantitative authority; these real calls confirm the attribution half is production-usable.

## Limits

4 recordings, Otter reference (~98%, no silence annotation, so FA unmeasurable and attribution
carries Otter's own error), supplied k. Pyannote-full not yet run on these (slow, ~1x); it is the
next comparison when time allows. A larger real-call batch (14 more recordings) is being transcribed
+ diarised separately (batch fast-path); Otter references for those arrive later for scoring.

Evidence: this file; var/meetings/realaudio-ourshybrid.json (gitignored - real client audio);
tools/realaudio_bench.py; e47-hybrid-vad-swap.md (the AMI result this tests in the wild). Real client
recordings are personal data - gitignored, never committed, described by shape only.
