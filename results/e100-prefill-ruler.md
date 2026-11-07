# E100 RESULT - the client wall was right and my live sampling was wrong (2026-09-01)

Scored against `results/e100-prereg.md`, written before the deciding evidence
was read. Evidence: `prompt eval time` lines already present in
`results/raw/e94/e94-residency-ctx262144-{smart,all}.serverlog`. No GPU used.

**Decision state: HYPOTHESIS FALSIFIED.** The registered primary prediction was
wrong, the falsifier fired in terms, and **F136 stands exactly as published.**

## Result

`llama-server` reports its own prefill timing per request. Against the
client-derived figures in F136:

| arm | server `prompt eval` | client-derived | delta |
|---|---|---|---|
| `smart` alone, 262,144 | **73.94 tok/s** | 73.8 | -0.1% |
| `smart` with three resident, asymmetric | **73.98 tok/s** | 73.9 | -0.1% |
| `fast` with three resident, 32,768 | **347.49 tok/s** | 344.5 | -0.9% |
| `code` with three resident, 65,536 | **188.49 tok/s** | 187.8 | -0.4% |

**Agreement is within 0.9% on every arm.** For the 261,827-token request the
client measured 3,546.0 s wall and the server measured 3,541.27 s of prefill -
**a remainder of 4.7 seconds, 0.13% of the request.**

## Hypotheses, each on the field it named

1. **PRIMARY - the client wall is a composite and understates prefill.** Field:
   the server's `prompt eval` tok/s. Registered: materially above 73.8, within
   ~20% of the 105-116 live window. **FALSIFIED.** The server says 73.94.
2. **The gap is accounted for by tokenize round trips.** Field:
   `client wall - server prompt eval`, in seconds. Registered: a large
   remainder. **FALSIFIED** - the remainder is 4.7 s. This was the prediction
   written specifically to stop hypothesis 1 being confirmed on a plausible
   rate alone, and it did its job.
3. **Residency does not speed prefill up.** Field: server `prompt eval` tok/s,
   one model against three. **HOLDS** - 73.94 against 73.98, a 0.05%
   difference, far inside F15's +/-1.5% band. F135 is confirmed by a second
   instrument.
4. **Prefill rate is not constant across one prompt.** Registered: it varies.
   **SUPPORTED but not directly measured.** It is the only surviving
   explanation for the live windows, and the evidence is indirect: two windows
   at 27-36% progress read 104.7 and 116.4 tok/s while the whole-prompt average
   is 73.94, so the early-middle of a prefill runs roughly 1.5x the average.
   Recorded as the leading explanation, not as a measurement.

**The registered falsifier fired in terms:** *"if the server reports about
73.8 tok/s for that request, the client wall was right and the live windows
measure something else. The F136 column stands and the live-sampling method is
the thing to distrust."*

## What this changes

**Nothing in F136, and that is the outcome.** The chart, the rate column and
the superlinear finding are all confirmed by a second independent instrument -
the server's own accounting rather than the client's stopwatch. The OPEN flags
added to `docs/FINDINGS.md` and `results/e94-residency.md` are removed and
replaced with the confirmation.

**The method lesson is the finding, and it is F137.** A progress counter
sampled over two short windows gave 1.4-1.6x the true rate and looked
trustworthy, because the two windows agreed with each other.

## Why this experiment was worth running on a correct number

The discrepancy was noticed mid-run, and both explanations were defensible after
the fact. Registering the fields first is what made "the client wall is a
composite" a testable claim rather than a story. It happened to be wrong.

**Had the prediction not been registered, the likely outcome was a correction
to three documents that did not need correcting** - including the Alchemy
programme review - on the strength of a live reading that felt more direct
because it came from the server.
