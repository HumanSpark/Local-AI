# E100 PRE-REGISTRATION - is the F136 prefill curve measuring prefill? (2026-09-01)

Written BEFORE the answering evidence was read. Every prediction names the
FIELD it is scored against (the E64 rule).

**This registers a discrepancy noticed mid-run, so that it is resolved by
measurement rather than by whichever explanation reads best afterwards.**

## The discrepancy

F136 charts a prefill curve and its last point was computed from the client's
end-to-end wall clock:

| prompt | client wall | derived rate |
|---|---|---|
| 261,827 tokens, `smart` alone at `-c 262144` | 3,546 s | **73.8 tok/s** |

While the asymmetric arm was running, the SERVER's own prefill progress counter
was sampled twice on a 261,827-token prompt with three models resident:

| window | progress | rate | implied |
|---|---|---|---|
| 1 | 0.27 -> 0.31 over 90 s | 0.044%/s | **116.4 tok/s** |
| 2 | 0.32 -> 0.36 over 100 s | 0.040%/s | **104.7 tok/s** |

**The live figure is 1.4x to 1.6x the derived one, in the wrong direction.**
Three models resident should not be FASTER than one, and F135 measured
residency as free rather than beneficial.

So at least one of the two numbers is not measuring what its label says, and
**F136's rate column is currently in three documents** - `docs/FINDINGS.md`,
`results/e94-residency.md` and the Alchemy programme review.

## The instrument that settles it

`llama-server` prints its own `prompt eval time` per request, with a token
count and a tokens-per-second figure. **That is the server's accounting of
prefill alone**, and it is in the serverlogs already written. It has not been
read yet; this page was written first, deliberately.

Comparing it to the client wall for the SAME request separates prefill from
everything else in the round trip.

## Hypotheses. The FIELD is named in each.

1. **PRIMARY - the client wall is a composite and understates prefill.** Field:
   the `prompt eval time` tok/s reported by the server for the 261,827-token
   request in `results/raw/e94/e94-residency-ctx262144-smart.serverlog`.
   Registered direction: **materially above 73.8 tok/s**, and within about 20%
   of the 105-116 tok/s live window. If it holds, the 3,546 s wall contains
   prefill plus prompt-building round trips, decode and HTTP, and the F136 rate
   column is mislabelled.
2. **The gap is accounted for, not merely asserted.** Field:
   `client wall - server prompt eval time`, in seconds. Registered: the
   remainder is dominated by the `/tokenize` calls `build_prompt` makes while
   sizing the prompt, each of which posts roughly a megabyte of text. **If the
   remainder is small, hypothesis 1 is wrong even if its rate looks right.**
3. **Residency does not speed prefill up.** Field: server-reported
   `prompt eval` tok/s for a comparable prompt, one model resident against
   three. Registered: within F15's +/-1.5% noise band, in line with F135. The
   alternative - that three resident models genuinely prefill faster - would
   contradict a measured finding and needs its own explanation.
4. **Prefill rate is not constant across one prompt.** Field: successive
   `progress` deltas sampled across a single prefill, at roughly 10%, 50% and
   90%. Registered: **it varies**, so any two-window sample is a local rate and
   not the average. This is why two agreeing windows were not sufficient
   evidence to quote a whole-prompt rate.

## Falsifiers

- **If the server reports about 73.8 tok/s** for that request, the client wall
  was right and the live windows measure something else - a fast region, a
  different configuration, or a counter that does not mean what it appears to.
  The F136 column stands and the live-sampling method is the thing to distrust.
- **If hypothesis 3 fails** and three resident models really do prefill faster
  than one, then F135's "residency is free" is incomplete: residency would have
  a sign, and E94's H3 would need re-opening rather than merely annotating.

## What changes on each outcome

**If 1 and 2 hold:** F136's chart is still correct about the thing that matters,
because **time to first output token is what a user waits for and legitimately
includes overhead**. What is wrong is the column labelled as a prefill rate. The
fix is to relabel it - "end-to-end, client-observed" - and to add the server's
prefill figure beside it as a separate column, in all three documents.

**If 1 fails:** F136 stands as written and this page records why the live
sampling was not trusted.

Either way the correction is cheap. The reason to register it first is that both
outcomes are defensible after the fact, and a discrepancy noticed mid-run is
exactly where a preferred explanation gets adopted without a test.

## Scope

Measures **the instrument**, not the box and not a model. No GPU time is needed:
every figure comes from serverlogs already on disk plus the running arm's
counter. Scope tag: **general**, for the F136 curve and for any future use of
client wall clock as a prefill measure.
