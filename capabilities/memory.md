# Memory (r6.0)

Keeping an assistant's notes about a person up to date without inventing or keeping rejected facts.

**Against the frontier:** Not compared with a frontier model yet. ([how it compares](../FRONTIER.md))

## What works best now

- **In production: Qwen3.8-Flash-Next** on Halogen (Halogen's own checkpoint, community template, effort low), since 2026-11-04.
  Why: Best local result on all three coding banks (15/15, 9/10, 5/10), passed the everyday-work tests at effort low in a third of the time, and runs fastest on Halogen.
- **Best alternative: Inkling-2-Mini** on llama.cpp (Q8_0, our conversion), since 2026-11-21.
  Why: No mistakes on fifty memory jobs, but 6.5 times slower than production and no answer on 5 of 20 updates.

## The experiments behind this, best results first

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| Keeping an assistant's memory up to date (E170) | 2026-11-21 | in production | Production made one mistake in fifty and kept the nightly job. | [results/e170-results.md](../results/e170-results.md) |

