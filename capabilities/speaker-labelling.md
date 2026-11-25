# Who said what (r6.2)

Tagging each line of a transcript with who said it.

**Against the frontier:** Not compared with a frontier service yet. ([how it compares](../FRONTIER.md))

## What works best now

- **In production: WeSpeaker + Silero, one enrolled speaker** on WeSpeaker + Silero (host-or-someone-else labelling), since 2026-07-18.
  Why: 97.2% of lines correctly tagged host or someone else on four real calls; sidesteps guessing how many speakers there are.

## Also tried

| Setup | Engine | Where it stands | Why |
|---|---|---|---|
| pyannote 3.1 full pipeline (default) | pyannote | tried | Better at general diarisation (6.5% against our 20.3% error on close-talk audio) but much slower; not needed for host-or-other. |

## The experiments behind this, best results first

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| Host or someone else: speaker labelling that a consultant needs (E50A) | 2026-07-17 | in production | 97.2% of lines correctly tagged as the host or someone else on four real calls. | [results/diarisation/e50-target-speaker.md](../results/diarisation/e50-target-speaker.md) |
| pyannote against our speaker pipeline (E46A) | 2026-07-17 | works, with caveats | pyannote is about three times better at general diarisation; ours is faster. | [results/diarisation/e46-pyannote-headtohead.md](../results/diarisation/e46-pyannote-headtohead.md) |

