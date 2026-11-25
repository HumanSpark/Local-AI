# Office tools (r6.3)

Calling office tools: create a document, send an email, look up a client.

**Against the frontier:** Not compared with a frontier model yet. ([how it compares](../FRONTIER.md))

## What works best now

- **In production: Qwen3.8-Flash-Next** on Halogen (Halogen's own checkpoint, community template, effort low), since 2026-11-04.
  Why: Best local result on all three coding banks (15/15, 9/10, 5/10), passed the everyday-work tests at effort low in a third of the time, and runs fastest on Halogen.

## Also tried

| Setup | Engine | Where it stands | Why |
|---|---|---|---|
| Qwen3-30B-A3B (Q4_K_M, Vulkan) | llama.cpp | retired | The July everyday model; replaced by Flash-Next. |

## The experiments behind this, best results first

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| The lighter setting across eight kinds of everyday work (E160) | 2026-11-13 | in production | Matched maximum thinking on seven of eight at 0.41 times the time. | [results/e160-results.md](../results/e160-results.md) |
| Qwen4 Max on client drafting (E164) | 2026-11-17 | works, with caveats | Beat production on drafting but trailed both frontier references. | [results/e164-results.md](../results/e164-results.md) |
| Office tool use (create a document, send an email, look up a client) (E33A) | 2026-07-14 | works, with caveats | The July model called the right tool 91% of the time; judgement inside a call needed a human check. | [results/tool-use/E33-results.md](../results/tool-use/E33-results.md) |
| A paired question that catches a broken chat template (E175) | 2026-11-24 | informational | The pair caught a silently broken template and raised no false alarm. | [results/e175-results.md](../results/e175-results.md) |
| Auditing our own tests (E165) | 2026-11-17 | a correction to our own test | Five tests marked models down for following their own instructions; corrected, every setup passed 36/36 tool tasks. | [results/e165-results.md](../results/e165-results.md) |
| AMD's Loom against Halogen and llama.cpp (E163) | 2026-11-16 | not adopted | Loom reads long prompts 2.7 times faster than llama.cpp but is not faster than Halogen. | [results/e163-results.md](../results/e163-results.md) |

