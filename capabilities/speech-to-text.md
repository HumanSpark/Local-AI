# Speech to text (r6.4)

Turning recordings into text.

**Against the frontier:** Not compared yet. ([how it compares](../FRONTIER.md))

## What works best now

- **In production: Whisper large-v3-turbo** on whisper.cpp (Silero voice detection), since 2026-07-18.
  Why: 2.40% word error rate on LibriSpeech, about 28 times real time on a clean clip; voice detection stops invented words over silence.

## Also tried

| Setup | Engine | Where it stands | Why |
|---|---|---|---|
| Whisper small (Silero voice detection) | whisper.cpp | tried | Faster but less accurate on real speech (3.35% against 2.40% word error rate). |

## The experiments behind this, best results first

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| Transcription accuracy against human transcripts (E45A) | 2026-07-17 | in production | Whisper large-v3-turbo 2.40% word error rate; the small model 3.35%. | [results/transcription/e45-true-wer.md](../results/transcription/e45-true-wer.md) |
| Whisper inventing words over silence (E41A) | 2026-07-17 | works, with caveats | Without voice detection Whisper invents about two utterances a minute of silence. | [results/transcription/e41-silence-hallucination.md](../results/transcription/e41-silence-hallucination.md) |

