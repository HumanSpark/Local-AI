# Music (r5.19)

Generating songs with sung lyrics.

## What works best now

- **In production:** nothing yet.
- **Best alternative: ACE-Step 1.5 Turbo** on audio.cpp (BF16), since 2026-11-24.
  Why: The only fast song model here and ties for clearest words; the owner liked none of the styles yet. No production pick.

## Also tried

| Setup | Engine | Where it stands | Why |
|---|---|---|---|
| YuE2-3B (BF16) | audio.cpp | tried | Clear words but slow, and its licence is non-commercial. |
| MiniMax Music 3 (BF16) | audio.cpp | tried | About 18 times slower than real time; one render failed to play. |

## The experiments behind this, best results first

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| Three local song models (E173) | 2026-11-24 | works, with caveats | ACE-Step is the only fast one and ties for clearest words; none matched the owner's taste in style. | [results/e173-results.md](../results/e173-results.md) |

