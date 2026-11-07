# E94 PRE-REGISTRATION - three models resident at once, and whether Nemotron-3-Nano earns a routing cell (2026-08-31)

Written BEFORE any arm runs. Every hypothesis names the FIELD it is scored
against (the E64 rule).

## Why this is worth running now, and was not last month

F40 measured two models held resident under llama.cpp's router mode - 41.04 GiB,
switching in 0.04 s - and concluded **"2 models is the safe cap: 41.04 GiB
leaves ~19 GiB under the ~60 GiB deadlock edge (F24); a third at ~20 GiB lands
ON it."**

**That cap was arithmetic against an edge that no longer exists.** F109 retracted
the ~60 GiB boundary on kernel 7.0.0-29: a ladder to **105.15 GiB GTT** served
every rung with zero `drm_suballoc_new`, and a deliberate contention
reproduction at 0 GiB free with swap engaged loaded in 32.3 s and served 10/10.
So the reason a third model was refused is gone, and nobody has since asked the
question.

E92 also changed the *value* of asking it. Until today the two capable models
were near-substitutes on the axes we measure. They are not any more:

| model | walked periods | cross-document | tg128 | weights |
|---|---|---|---|---|
| workhorse Qwen3-30B-A3B | **0/8** | 4/12 | **92.28** | 17.28 GiB |
| Qwen3.8-27B `low` | 7/8 | **12/12** | **12.59** | 15.66 GiB |
| Nemotron-3-Nano | 7/8 | 8/12 | 64.52 | 22.96 GiB |

**Nemotron occupies a cell neither incumbent does: fast AND able to count a
period.** The workhorse is fast and cannot count at all; the 27B counts well and
decodes at an eighth of the speed. If a third resident model is affordable, the
routing question stops being "which one do we load today" and becomes "which one
answers this request".

## The memory projection this experiment tests

Weights total **55.90 GiB**. F40 measured the workhorse at 20.21 GiB loaded
against 17.28 GiB of weights - a 1.17 ratio at `-c 49152` with four slots.
Applying that ratio to all three projects **~65 GiB**, against 121 GiB of RAM
and F109's demonstrated 105.15 GiB GTT.

**The projection is the thing under test, not an assumption.** KV cache scales
with context, and three models sharing one box cannot each carry production's
`-c 98304`. The real question is therefore not "do the weights fit" - they
plainly do - but **what context budget each model can hold when three are
resident**, which is the number that decides whether this is usable.

## Arms

| # | configuration | purpose |
|---|---|---|
| A | router mode, workhorse alone, `-c 32768` | baseline, and an independent check that router allocation matches direct serving (F40 did this and it matched) |
| B | + Qwen3.8-27B, both resident | reproduces F40's two-model result on a new build and a new pair |
| C | **+ Nemotron-3-Nano, all three resident** | the experiment |
| D | arm C with each model's context raised until allocation fails | finds the actual context ceiling rather than assuming one |

Router mode per F40's safety findings: **`--models-preset`, never
`--models-dir`** (autoload plus `models-max 4` could pull a 100 GB artefact
straight off the disk), and `--models-max 3` explicit.

## Hypotheses. The FIELD is named in each.

1. **PRIMARY: all three models are resident simultaneously with GTT below
   75 GiB at `-c 32768` each.** Field: `mem_info_gtt_used` with all three
   loaded, minus the pre-load baseline. The 65 GiB projection plus headroom; if
   it lands above 75 the projection method is wrong and the ratio does not
   transfer across architectures.
2. **DISCRIMINATING: switching between any two of the three costs under
   0.5 s.** Field: wall time of a one-token request to model X immediately
   following a request to model Y, minus the same request's solo latency. F40
   measured 0.04 s for two models. If a third pushes this into seconds, the
   value proposition collapses - the point is per-request routing, not
   per-session swapping.
3. **Residency is free: an idle resident model costs the active model nothing
   measurable.** Field: `tg128` for the workhorse in arm C against its solo
   92.28, band +/- 3% (F15's single-run noise is +/-1.5%). This is the claim
   F40 asserted and did not test.
4. **The context ceiling is at least 32,768 per model with three resident.**
   Field: the largest `-c` at which arm D still loads all three and serves a
   request. Registered because 32K is the smallest context that covers the l3
   pack, so below it the third model cannot do document work at all.
5. **Nemotron reproduces 7 of 8 walked periods at effort matched to the
   incumbent's `low`.** Field: the walked-period sum on l4. E92 ran it at
   `default` and the comparison was therefore not effort-matched; this closes
   that gap.
6. **Nemotron's over-claim reproduces.** Field: `over_claims` on l4 plus
   `over_claim_rate` on the E76 abstention bank. E92 measured 1/1 on the single
   l4 item where both capable models declined. Registered as expected to HOLD,
   because it is the finding that decides whether it can be routed to at all.

## Falsifiers

**On hypothesis 1:** if three models will not co-reside below 75 GiB, the
three-model serve is dead for this trio and the follow-up is which PAIR to hold,
not which three.

**On hypothesis 3, and this is the one that would change the most:** if an idle
resident model measurably slows the active one, then residency is not free,
F40's headline is wrong on a point it asserted without testing, and even the
existing two-model plan needs revisiting.

**On hypothesis 6:** if Nemotron does NOT over-claim on the abstention bank, its
single l4 over-claim was noise on one item, and it becomes a serious candidate
for the fast-plus-arithmetic routing cell rather than a model with a known
liability.

## What this does NOT test

**Concurrent inference on two or three models at once. Deliberately.** F41
measured that as a fixed bandwidth budget split 4.6:1 against the MoE - the
workhorse kept 18.9% of its solo speed while a dense model kept 86.1%. The value
here is **residency and switching**, not parallelism, and an arm that ran three
models simultaneously would measure a thing already known to be a bad idea.

Also not tested: any capability axis for the workhorse or the 27B (E91 measured
both today), long context beyond arm D's ceiling, tool use, and whether router
mode is production-ready - llama.cpp still labels it experimental, so a positive
result here is a case for a proposal to sparkrouter, not a change to it.

## Cost and safety

One maintenance window, roughly 45-60 minutes. Loads are sequential and the
largest single load is 26.9 GiB projected, well inside F109's proven envelope.
No download. Rule 5 still applies: no heavy disk I/O concurrent with the loads,
which means no model fetch may run during this window.

**Serving stays untouched.** This is a bench-side experiment on a scratch port
using sparkbench's own build; `/var/lib/sparkrouter/serving.conf` has one writer
and this is not it (F39).


## AMENDMENT 1 - declared 2026-08-31 22:48, BEFORE any E94 arm runs

Three changes, each forced by evidence produced tonight and committed before
this amendment was written. **No hypothesis is reinterpreted after seeing E94
data, because no E94 arm has run.**

### 1. The third model is Qwen3-Coder, not Nemotron-3-Nano

**Reason: E99 rejected Nemotron, and it rejected exactly the property that
earned it a place here.** This page's case for a third resident model was that
"Nemotron occupies a cell neither incumbent does: fast AND able to count a
period". E99 (`results/e99-thinking-off.md`, F-register pending) measured both
of its available configurations:

| Nemotron-3-Nano, l4 | walked periods | terminates? | score quotable? |
|---|---|---|---|
| `default` | 7 of 7 **answered** | **no** - burns the entire budget on N2 | **no**, gate FAIL |
| `off` | **0 of 8** | yes, 30 s | yes |

The capability and the termination are the same setting. A model that cannot be
relied on to finish cannot hold a routing cell, so the trio becomes the one that
would actually be deployed:

| alias | model | weights |
|---|---|---|
| `fast` | Qwen3-30B-A3B-Instruct-2507 | 17.28 GiB |
| `smart` | Qwen3.8-27B-Q4_K_M | 15.66 GiB |
| `code` | Qwen3-Coder-30B-A3B-Instruct | 17.28 GiB |

**Weights total 50.22 GiB, DOWN from the registered 55.90.** Hypothesis 1's
75 GiB threshold is therefore *harder* to breach than when it was registered,
not easier - the amendment does not make the primary prediction easier to pass,
which is the property that matters when an arm changes after registration.
Hypotheses 1, 2, 3 and 4 are otherwise unchanged and are scored as written.

### 2. Hypothesis 5 is NOT RUNNABLE and is withdrawn

H5 reads: *"Nemotron reproduces 7 of 8 walked periods at effort matched to the
incumbent's `low`."* **That arm cannot exist.** Read from GGUF
`tokenizer.chat_template` with no model load, Nemotron's template contains **no
`reasoning_effort`** - `run_ps_eval.py --thinking low` sends it and the template
ignores it, so the arm would be byte-identical to `default` while the result
file recorded `thinking: "low"` as applied (F39's inert-flag class). The
incumbent has three effort levels; Nemotron has two states, on and off. **No
matched-effort comparison exists for this pair.**

Recorded as `NO DECISION - MEASUREMENT INVALID`, on metadata evidence, without
consuming a window. E98's prereg carries the same declaration for the same
reason.

### 3. Hypothesis 6 is HALF-BLOCKED and is withdrawn with it

H6 is scored on l4 `over_claims` **plus** `over_claim_rate` on the E76
abstention bank. The E76 bank cannot load - it fails its own gate on the U02
defect (`text asserted ABSENT is present in pack 's': '7.0.0'`, from F109's
kernel edit to `docs/memory-edge-deadlock.md`). With Nemotron out of the trio
the remaining l4 half has no arm to be measured on either, so H6 goes with H5.

**H5 and H6 were the only two capability hypotheses on this page.** What
survives is E94's infrastructure question - **can three models co-reside, how
fast is switching, is residency free, and what context does each get** - and
that is the half worth having, because it is the half that does not expire when
the models change. The owner's framing, 2026-08-31: *"this area is changing week
to week."*

### What the amendment costs

E94 is now a **capacity** experiment, not a capability one. It answers "two or
three, and what context each" and it does not answer "which three", because the
answer to that changes faster than the measurement does. That is the correct
division: the capacity result is durable, the model list is perishable, and the
alias layer is what keeps the perishable half cheap to change.
