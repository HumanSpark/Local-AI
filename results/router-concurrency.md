# E36 RESULTS: single-model concurrency under the router (2026-07-17)

# File: results/router-concurrency.md
# Purpose: Does the router's proxy hop change F17's concurrency scaling? Pre-reg: router-concurrency-prereg.md.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: The router is FREE for throughput - within 0.7% of direct at every slot count, F17's 2.66x
# scaling preserved - with one exception: TTFT p95 at 16 slots is +46%. The proxy costs tail latency,
# not throughput. Bigger incidental finding: aggregate throughput moved 26% purely by changing the
# PROMPT (152 -> 192 t/s), which means F17's headline 193.5 is measured on degenerate repetitive text.
# Two ruler errors were caught and corrected before any of these numbers were trusted; both are recorded.

## Conditions

llama.cpp v200 (067de93), Qwen3-30B-A3B-Q4_K_M, 4096 ctx/slot, 128-token requests, 45s window,
`-fa auto -ctk f16 -ctv f16 -v`. Both arms measured in THIS session on THIS build with ONE driver -
F17's banked numbers were deliberately NOT used as the baseline (they predate this build; comparing
across builds would confound router effect with build change). Gateway paused, attended, preset-only.
**D-state 0 throughout. Box restored exactly (GTT 20.21 GiB).**

## Headline: the router is free for throughput

| Slots | DIRECT agg t/s | ROUTER agg t/s | router/direct |
|---|---|---|---|
| 1 | 72.78 | 72.81 | **1.000** |
| 4 | 138.93 | 139.27 | **1.002** |
| 16 | 192.19 | 193.54 | **1.007** |
| scaling 1->16 | 2.64x | 2.66x | - |

The proxy hop is not a bottleneck at any concurrency tested, and F17's 2.66x MoE scaling is preserved.

## Prediction resolution

| ID | Prediction | Result | Verdict |
|---|---|---|---|
| P1 | DIRECT reproduces F17 (~70-75 -> ~180-200, 2.4-2.9x) | 72.78 -> 192.19, **2.64x** (F17: 72.9 -> 193.5, 2.66x) | **HIT** |
| P2 | Router >= 0.95 x direct at 1 slot | 1.000 | **HIT** |
| P3 | Router >= 0.90 x direct at every N; scaling within 0.2x | 1.000 / 1.002 / 1.007; 2.66x vs 2.64x | **HIT** |
| P4 | Router TTFT p50 +<50ms at 1 slot; ~6x growth preserved | +1.0ms; router 6.0x vs direct 5.6x growth | **HIT** |
| P4b | (implied: tails behave) | **p95 at 16 slots +46%** - see below | **MISS** |
| P5 | No deadlock, D-state 0 | 0 | **HIT** |

## Where the router is NOT free: the TTFT tail

| | direct | router | delta |
|---|---|---|---|
| 1 slot p50 | 305.4 ms | 306.4 ms | +1.0 ms |
| 16 slot p50 | 1721.8 ms | 1825.4 ms | +6% |
| **16 slot p95** | **1754.7 ms** | **2554.8 ms** | **+46%** |

Median latency is essentially unaffected even at 16 slots, but the 95th percentile inflates sharply.
Direct serving has a remarkably tight distribution at 16 slots (p50 1721.8 -> p95 1754.7, a 2% spread);
the router's spread is 40%. The proxy adds jitter under concurrent load rather than a constant cost.
For a single operator this is invisible. For a latency-sensitive multi-client service it is the thing
to know: **the router costs tail latency, not throughput.**

## The incidental finding that matters more: prompt content moved throughput 26%

While validating the driver (below), the ONLY change was the prompt text, everything else identical:

| Prompt | agg t/s @16 slots | per-stream t/s | TTFT p50 |
|---|---|---|---|
| `"The quick brown fox..."` x16 (serve_bench's, ~144 tok) | **192.19** | 14.57 | 1721.8 ms |
| Real legal prose, ~45 tok ("summarise a boundary survey...") | **152.12** | 10.21 | 762.3 ms |

**26% aggregate difference, 43% per-stream difference, from the prompt alone.** This is not an
early-EOS artifact: `predicted_per_second` is a server-side RATE (predicted_n / predicted_ms),
independent of how many tokens were produced. The shorter prompt was the SLOWER one, so it is not
prefill cost either - which rules out the obvious explanations and leaves the interesting one.

**Hypothesis (untested): MoE expert routing.** Qwen3-30B-A3B activates ~3B of 30B params per token,
and WHICH experts activate depends on the tokens. Degenerate repetitive text ("the quick brown fox"
sixteen times, continued) should keep hitting the same small set of experts - good weight-reuse, less
memory traffic. Diverse real prose should touch more experts per unit output - more weight movement,
and this box is memory-bandwidth bound (F41). If that is the mechanism, the effect is a property of
MoE architectures specifically and would not appear on a dense model.

**Why it matters: F17's headline 193.5 t/s aggregate is measured on repetitive filler.** Real work
measured here runs ~152 t/s at the same slot count - about 21% lower. F17's number is not wrong (its
own conditions are stated), but it is a best case, and "what the fleet gets at burst" - F17's own
client-facing framing - is closer to the lower figure for real prompts. This needs its own experiment
before anything is re-published: n=2 prompts is a signal, not a result, and the mechanism is a
hypothesis. Registered as the next open question rather than asserted here.

## Two ruler errors caught before trusting any number

Recorded because both would have produced confident, wrong findings.

**1. The flags.** The first DIRECT arm used bare `-m -np -c`, but serve_bench launches with
`-fa auto -ctk f16 -ctv f16 -v`. Re-ran with the exact flags: 76.52 / 145.44 / 152.12 vs bare
76.82 / 146.10 / 150.39 - **not the explanation**, but it had to be excluded before blaming anything else.

**2. The prompt - this one nearly produced a false BUILD REGRESSION.** With my own prompt, DIRECT
measured 152.12 t/s at 16 slots against F17's 193.5 and a 1.99x scaling ratio against F17's 2.66x.
Per the pre-registered decision rule that is "P1 MISS -> F17's numbers are stale for this build", a
significant and publishable claim. The control that stopped it: running **F17's own harness**
(serve_bench.py) on the same box, same build - it returned **191.76 t/s**, reproducing F17. So the
build was fine and MY DRIVER was the outlier. Swapping in serve_bench's exact BASE_PROMPT made my
driver return **192.19** - matching serve_bench within 0.2% and validating the driver. Only then were
the router numbers measured.

The rule: **when a new harness disagrees with a banked number, run the OLD harness before concluding
anything about the world.** A 21% gap that looks like a regression in the system under test is, more
often, a difference in the instrument. Same family as F41's overlap artifact and this week's `--jinja`
retraction - three ruler errors in one week, each caught by measuring the thing rather than reasoning
about it. The prompt sensitivity that caused this error is itself the session's most interesting result.

## Operational read

- **The router is viable for concurrent serving**, not just switching: identical throughput, F17's
  scaling preserved, no errors at 16 concurrent streams. The remaining objections are llama.cpp's
  own "experimental" label and the p95 tail.
- **Native `/completion` requires a `"model"` field under the router** and returns 400 Bad Request
  without one; a direct llama-server needs no such field. Any existing client using the native
  endpoint breaks on migration. `/v1/chat/completions` callers already send `model` and are unaffected.
- The router's cost is tail latency at high concurrency (p95 +46% at 16 slots), not throughput.

## Still open

The prompt-sensitivity experiment (is it MoE expert routing? does it vanish on a dense model like
Mistral-24B? what does the curve look like across prompt diversity?); `--sleep-idle-seconds`; router
stability over days; concurrency beyond 16 slots.

Evidence: this file; pre-registration results/router-concurrency-prereg.md (committed a8d2df8 BEFORE
any run); control run via tools/serve_bench.py (F17's own harness) = 191.76 t/s @16 slots; F17 (the
scaling this reproduces); F41 (the bandwidth ceiling that explains why the MoE routing hypothesis is
plausible); F40 (the router baseline).
