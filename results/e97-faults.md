# E97 RESULT - the harness banks a plausible score for a run that never happened (2026-08-31)

Scored against `results/e97-prereg.md`, written before any fault was injected.
Raw evidence: `results/raw/e97/e97-faults.json` plus one result file per fault.

**Decision state: FOLLOW-UP EARNED.** One defect class confirmed, with a
concrete correction owed to one published report.

## What was run

`tools/run_ps_eval.py`, unmodified, driven end to end seven times against
`tools/e97/fake_llama_server.py` - a stand-in that speaks `/health`,
`/tokenize` and `/v1/chat/completions` and emits the `assigned to device`
lines the Rule 3 offload gate greps for. Nothing inside the runner was
patched. Tier `l1` (20 items); the bank's content is irrelevant because the
model is a fake.

**Every timing here is void by declaration** - `--allow-busy-gpu`, no GPU, a
fake server. E97 measures gate behaviour.

## Result

| # | fault | exit | score written to disk | outcome counts | required | verdict |
|---|---|---|---|---|---|---|
| - | none (control) | 0 | 1/20 | correct 1, over_claim 4, wrong 15 | no red | **MET** |
| 1 | truncation | **3** | 0/20, `truncation_gate: FAIL` | truncated 20 | no score | see below |
| 2 | malformed response | **0** | **0/20**, `truncation_gate: PASS` | transport_failed 20 | no score | **BREACHED** |
| 3 | empty response | 0 | 0/20 | format_error 20 | not `wrong` | **MET** |
| 4 | missing output file | 1 | none | - | no score | **MET** |
| 5 | server interruption | **0** | **1/20**, `truncation_gate: PASS` | correct 1, transport_failed 17, wrong 2 | no score | **BREACHED** |
| 6 | scorer exception | 1 | none | - | no score | **MET** |

Five of the six registered predictions held exactly, including both registered
gaps. The control behaved as a control must: it produced an ordinary score and
went nowhere near a gate.

## The one defect class, stated once

**Faults 2 and 5 are the same failure: `transport_failed` is counted in `total`
but nothing gates on it.** An item the model never answered is scored as though
it were answered and wrong.

Fault 5 is the sharp form. The server died after answering 3 of 20 items and
the run exited **0** with `correct: 1, total: 20` and a **PASSING** truncation
gate. That file is indistinguishable, to any later reader or script, from a
model that sat the whole bank and got 19 questions wrong.

This is exactly the shape Rule 13 was written for, one layer out. Rule 13
caught `truncated` - an item cut off at the token cap. It never covered
`transport_failed` - an item whose request never completed. **Both mean the
same thing: the model was never asked, or its answer never arrived.** The
evidence doctrine's own line applies unchanged - *empty != unavailable*.

### Fault 1 scores two ways, and that is my error, not the harness's

Prediction 1 named two fields: **exit code** and **`truncation_gate`**. Both
held - exit 3, gate `FAIL`. On the fields it named, **prediction 1 HOLDS.**

But the prereg's requirements table demanded something stricter for the same
fault: *"no result file a reader could quote a `correct` count from"*. The
runner writes the summary before returning 3, so `"correct": 0` does sit on
disk - beside `"truncation_gate": "FAIL"` and `"truncated": 20`, which a reader
would have to ignore to be misled.

**So the same fault reads as HOLDS on one clause and BREACHED on another, and
that is the E64 failure repeating inside the pre-registration written to
prevent it.** E64's "cold load over 100s" matched two fields at once and scored
as neither. This one is milder - the fields agree, the table is stricter than
the prediction - but the lesson is identical: a requirement stated in prose and
a prediction stated in fields must be the same sentence. Recorded rather than
resolved in my favour.

## The historical check, and what it does and does not touch

19 committed result files carry `transport_failed` items. Two are E97's own.
Of the remaining 17:

- **E61's twelve** are documented in terms - `docs/2026-08-19-gptoss120b-decode-hang.md`
  names the twelve `transport_failed` from a decode hang, and the retry is the
  real result. Caught by a person.
- **E33's four** are documented in terms, in `resolve_request_timeout`'s own
  docstring: the re-run was destroyed by a timeout and "produced no data at
  all". Caught by a person.

**The defence has been human attention, not machinery.** That is precisely what
Rule 13 replaced for truncation, and it is why this gap is worth closing rather
than noting.

### One published number is confounded, and it is narrow

`reports/2026-08-16-technical-complete-summary.md:245` reads:

> **The cloud arm of the same model is not the same instrument.** Four runs of
> Qwen3.8 through a cloud API at temperature 0 returned **6/20, 19/20, 11/20 and
> 12/20**. Local runs are byte-deterministic. This is F66, and it means a single
> cloud number is a sample, not a measurement.

Those four arms dropped **13, 1, 9 and 8** of 20 requests. Among the items that
actually completed they scored:

| arm | reported | never answered | correct / completed |
|---|---|---|---|
| `qwen38-cloud` | 6/20 | 13 | 6/7 |
| `qwen38-cloud-complete` | 19/20 | 1 | 19/19 |
| `qwen38-cloud-rep2` | 11/20 | 9 | 11/11 |
| `qwen38-cloud-rep3` | 12/20 | 8 | 12/12 |

48 of 80 requests never returned. **The 6-to-19 spread is transport, not model
non-determinism**, and the four figures should not be quoted as scores.

**Two limits on that correction, both load-bearing:**

1. **F66 ITSELF IS UNAFFECTED AND STANDS.** Its evidence table is
   `gemini-3.7-flash` (20/20, 20/20, 20/20) and `upstage/solar-pro4` (15/20,
   16/20, 15/20). **Every one of those six arms has zero `transport_failed`**,
   and F66's sharpest case - `solar-pro4` returning 19.1%, 19.4%, 19.3%, 19.4%
   for one arithmetic item - is untouched. The confounded numbers are a
   restatement in one report, not the finding's basis.
2. **The completed-only figures are NOT a corrected score for the model.**
   Transport failures need not be random: E33's lesson is that the longest
   generations time out first, so the surviving items may be the easier ones.
   The right conclusion is that the four reported figures are invalid as
   scores, not that the model was really 48/49.

The report line is client-facing prose and its amendment is the owner's call,
so it is recorded here and in `HANDOFF.md` rather than edited.

## Three defects this experiment paid for in its own instruments

All three are the same shape as the thing being tested, which is worth stating
plainly rather than tidying away.

1. **The fault injector targeted item `Q3`, which does not exist in the l1
   bank.** Fault 6 silently ran as a healthy arm and produced outcome counts
   **byte-identical to the control**. A fault injection that cannot fail is not
   a fault injection. `sitecustomize.py` now refuses an unknown item id.
2. **The runner read a STALE result file** left by an earlier pass and reported
   it as the current run's output, so a crashed run showed `score_emitted:
   true`. The target is now deleted before each run. Same trap as the doctrine's
   *empty != unavailable*.
3. **The pre-registration stated one fault's requirement two ways** - see fault
   1 above.

## What this changes

The harness must refuse to report a score when any item was never answered,
the same way Rule 13 refuses when any item was truncated. That is **Rule 14**
and **F121**.


## ADDENDUM - the fix, and E97 re-run against it (2026-08-31)

Added after the result above was committed as measured (`d3c3287`), so the
evidence for the unfixed harness stands on its own.

**Rule 14 implemented**: `transport_failed` counted, a `transport_gate` field
recorded, **exit 4** rather than a score, `--allow-transport-failures` as the
declared override. Exit 4 and not 3 because Rule 13 owns 3 and the two need
different repairs.

E97 re-run unchanged against the repaired harness
(`results/raw/e97/e97-faults-after-rule14.json`):

| fault | before | after |
|---|---|---|
| none (control) | exit 0, 1/20 | **exit 0, 1/20** - still passes |
| truncation | exit 3, gate FAIL | exit 3, gate FAIL - unchanged |
| malformed | **exit 0**, 0/20, gate PASS | **exit 4**, `transport_gate: FAIL` |
| empty | exit 0, 20 format_error | unchanged |
| missing output | exit 1, no file | unchanged |
| interrupt | **exit 0**, 1/20, gate PASS | **exit 4**, `transport_gate: FAIL` |
| scorer exception | exit 1, no file | unchanged |

The control still passes, which is the half that matters: a gate that fires on
a healthy run trains its reader to pass the override every time.

Held by `tests/test_transport_gate.py` - five tests driving the real runner end
to end against the fake server, including the clean-run control and an assertion
that the two gates carry different exit codes.

**The prereg clause that is still NOT met.** E97 required "no result file a
reader could quote a `correct` count from". The summary is still written before
either gate returns, so `"correct": 0` sits on disk beside
`"transport_gate": "FAIL"`. Rule 13 has always had this shape. Withholding the
headline number would touch 12 tools that read `correct`, so it is a separate
decision and is recorded here as unmet rather than quietly reinterpreted as met.
