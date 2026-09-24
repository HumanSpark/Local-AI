# E97 PRE-REGISTRATION - does the harness go RED, or does it bank a plausible number? (2026-08-31)

Written BEFORE any fault is injected. Every prediction names the FIELD it is
scored against (the E64 rule).

Design source: `docs/2026-08-31-rd-programme-merge.md` section 2, item **E97**
(the programme's **B2**). That page carries the design; this page makes it
scoreable by naming the fields and registering the directions.

## The question

Rule 13 exists because of ONE real case: E92 scored a coding model 0/8 when 7 of
its 8 outputs had been cut off at the token cap and returned nothing. A model
that was never asked and a model that answered wrong are different observations,
and folding one into the other produced a number that read like a capability
result.

**Rule 13 fixed that one case. It did not prove the class.** The question here
is whether the OTHER ways a run can be invalid also go red, or whether they
quietly land in the numerator and denominator of a score that a routing decision
then rests on.

This is not hypothetical and it is not old. **Four hours ago tonight, both `pr1`
arms of E93 died four seconds in on a `KeyError` inside an open maintenance
window** - the tier was registered in `TIERS` but no prompt had ever been built
for it. The runner logged `WARNING: ... exited 1; continuing` and carried on. The
crash was loud, which is the only reason it was caught; nothing in the harness
distinguishes "this arm produced no data" from "this arm has not run yet".

## What decision this could change

Every routing, purchasing and client-use recommendation this repo has made rests
on a score emitted by this harness. If an invalid run can emit a plausible score,
then the question is not "is this model good enough" but "is any of it
measurement". A confirmed gap changes what may be reported from every future arm,
and it is the cheapest experiment on the queue.

## Method

A **fake llama-server** (`tools/e97/fake_llama_server.py`) that speaks the three
endpoints the runner uses - `/health`, `/tokenize`, `/v1/chat/completions` - and
writes the `assigned to device ROCm0` lines the Rule 3 offload gate greps for.
`tools/run_ps_eval.py` is then driven END TO END against it, unmodified, once per
fault. Nothing is stubbed inside the runner: the seam under test is the real one.

**No GPU is used and every timing in this experiment is VOID by declaration.**
The runs pass `--allow-busy-gpu` because the production relay holds the GPU and
E97 measures gate behaviour, not throughput. This is the documented use of that
flag, and the breach is recorded in each result file by the runner itself.

**Scored on the l1 tier**, which is the cheapest bank, because the bank's content
is irrelevant here - the model is a fake and the subject is the harness.

## The six faults, and the FIELD each is scored against

| # | fault | injected as | REQUIRED behaviour | FIELD |
|---|---|---|---|---|
| 1 | truncation | `finish_reason: "length"`, empty content | refuse to report a score | process exit code, `truncation_gate` |
| 2 | malformed response | HTTP 200 whose body has no `choices` | refuse to report a score | process exit code |
| 3 | empty response | HTTP 200, `content: ""`, `finish_reason: "stop"` | must not be scored as a WRONG answer | `outcome_counts` |
| 4 | missing output file | `--out` under a directory that cannot be created | raise; write nothing | process exit code |
| 5 | server interruption | fake exits after item 3 of the bank | refuse to report a score | process exit code |
| 6 | scorer exception | grader raises on one item | propagate; do not become an outcome | process exit code |

**"Refuse to report a score" is the testable property**, and it means a non-zero
exit AND no result file a reader could quote a `correct` count from. A run that
exits 0 with `correct: 3, total: 15` after the server died at item 4 has failed
this experiment even though every line of it ran.

## Predictions. Registered before any fault runs.

1. **Fault 1 exits 3 and records `truncation_gate: "FAIL"`.** Field: exit code
   and `truncation_gate`. Registered direction: HOLDS. This is Rule 13 doing
   exactly what it was written for and is the positive control - a fault-injection
   suite where nothing goes red cannot distinguish a working harness from a
   harness that never fired.
2. **Fault 2 exits 0 and emits a score.** Field: exit code. Registered
   direction: **FAILS the required behaviour.** `ask()` raises, the per-item
   `except Exception` records `transport_failed`, and nothing downstream gates on
   it - `transport_failed` items sit in `total` and not in `correct`, so a
   malformed-server arm reports a low score that reads as a capability result.
3. **Fault 3 is recorded as `format_error`, not as `wrong` or `correct`.**
   Field: `outcome_counts`. Registered direction: HOLDS. `parse_response`
   returns `None` on empty text and `grade_answer` maps `None` to
   `format_error`, which is a distinct and honest outcome.
4. **Fault 4 raises and exits non-zero.** Field: exit code. Registered
   direction: HOLDS.
5. **Fault 5 exits 0 and emits a score.** Field: exit code. Registered
   direction: **FAILS the required behaviour**, and this is the one with the
   sharpest consequence: a server that dies at item 4 of 15 produces
   `correct: 3, total: 15`, which is indistinguishable from a model that got 12
   questions wrong.
6. **Fault 6 propagates and exits non-zero.** Field: exit code. Registered
   direction: HOLDS. There is no `try/except` around `grade()`.

**So the registered expectation is 4 holds and 2 gaps.** If all six hold, the
harness is sounder than this pre-registration believes and the honest report is
that Rule 13's class was already covered - a publishable negative, and it must be
reported as readily as a positive. If faults 2 and 5 fail as predicted, they earn
one rule, not two: `transport_failed` and `truncated` are the same failure at
different layers - **an item that was never answered must never be scored.**

## Falsifiers

- **If fault 1 does not go red**, Rule 13 is not actually wired into the path
  this experiment drives, and every result since it was written is unprotected.
  That finding outranks all five others and stops the experiment.
- **If faults 2 and 5 both hold** (non-zero exit, no score emitted), the gap this
  experiment was designed around does not exist and prediction 2 and 5 are
  falsified. Report it as a negative and do not write a rule.

## Scope

This measures **the harness**, not a model, and its findings are scope-tagged
`general` only for `tools/run_ps_eval.py`. `tools/run_coding_eval.py` carries its
own copy of the Rule 13 gate and is NOT tested here; whether it shares these gaps
is a separate question this experiment does not answer.

Not measured: throughput, correctness of any bank, any model. The fake returns
fixed strings and its answers are meaningless by construction.
