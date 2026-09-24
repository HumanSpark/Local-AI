# E99 PRE-REGISTRATION - does disabling thinking make these two models TERMINATE? (2026-08-31)

Written BEFORE any arm runs. Every prediction names the FIELD it is scored
against (the E64 rule).

**This is a DECLARED CONFIGURATION ARM, not a repair of a truncated run.** The
brief's own line: raising a token cap repairs, disabling reasoning is a
treatment. `--thinking off` changes what the model does, so it is a new arm
with its own registration and its numbers are never merged with the `default`
ones.

## Why now, and what decision it could change

Two models in this repo produce scores nobody may quote, for the same reason.

| arm | tier | reported | truncation gate | truncated |
|---|---|---|---|---|
| Kwaipilot KAT-Coder (E92) | l4 | 12/15 | **FAIL** | 1 |
| Kwaipilot KAT-Coder (E92) | expert coding | - | **FAIL** | 6 of 8 |
| Nemotron-3-Nano (E92) | l4 | 14/15 | **FAIL** | 1 |
| Nemotron-3-Nano (E98, tonight) | l4 | 14/15 | **FAIL** | 1 |

**E98 established that this is not a budget problem.** Nemotron's N2 consumed
**exactly 32,768 tokens** at a 32,768 cap, having consumed exactly 16,384 at a
16,384 cap. It does not run out of room; it does not stop. That is F119's
"specialist that does not terminate", now observed in a second model and a
second architecture.

**The decision:** neither model can be routed to for anything if it cannot be
relied on to finish. If `--thinking off` makes them terminate at an acceptable
score, both become usable and Kwaipilot's coding bank becomes measurable at
all. If it does not, the honest answer is that these two builds are not
deployable here regardless of how well they score on the items they do finish,
and the queue's coding-completion and quantisation follow-ups (A6, A11) are
dead behind them.

## Why `off` and not `low`

`--thinking low` is **inert** for both models and would have been a fake
treatment. Read from GGUF `tokenizer.chat_template` via `gguf_ctx_probe`, with
no model load:

| model | `reasoning_effort` | `enable_thinking` |
|---|---|---|
| Nemotron-3-Nano-30B-A3B | **absent** | present |
| Kwaipilot KAT-Coder-V2.5 | **absent** | present |

`run_ps_eval.py --thinking low` sends `reasoning_effort` in the payload; a
template that never references it ignores it, and the result file would record
`thinking: "low"` as applied. `--thinking off` sends
`chat_template_kwargs: {enable_thinking: false}`, which both templates DO
reference. So `off` is the only real effort treatment available for either
model, which is why it is the one registered.

## Arms

Build `daef7b687`, `-fa on -ctk q8_0 -ctv q8_0`, relay down, GPU uncontended,
`--thinking off` throughout.

| # | model | bank | ctx | max_tokens | control it is compared against |
|---|---|---|---|---|---|
| A | Kwaipilot KAT-Coder | l4 | 32768 | 16384 | E92 `default`, 12/15, gate FAIL |
| B | Kwaipilot KAT-Coder | expert coding | 32768 | 16384 | E92 `default`, 6 of 8 truncated |
| C | Nemotron-3-Nano | l4 | 32768 | 16384 | E92 + E98 `default`, both gate FAIL |

**Budgets are held at E92's `mt16384` values on purpose.** The question is
whether the model stops on its own, and raising the cap at the same time would
confound the treatment with a budget change - two variables, one arm. If a
model terminates here it did so inside a budget that was already proven
insufficient at `default`.

## Hypotheses. The FIELD is named in each.

1. **PRIMARY: `--thinking off` makes them terminate.** Field: `truncation_gate`
   on arms A, B and C. Registered direction: **`PASS` on all three**, with
   `truncated: 0`. This is the whole point of the arm - a reasoning loop that
   never converges cannot run if reasoning is switched off.
2. **Kwaipilot's coding bank becomes measurable for the first time.** Field:
   arm B `truncated`, which must fall from 6 to 0. F119 could not report a
   coding score at all; if this holds, the bank yields a number that is allowed
   to be quoted. **The score itself is secondary and is NOT predicted** - E92
   never got one, so there is nothing to predict against.
3. **The l4 scores FALL.** Field: `correct` on arms A and C. Registered
   direction: **both below their `default` figures**, because F77 already
   measured `enable_thinking: false` costing Qwen3-8B four points on the easy
   tier with every arithmetic item flipping to wrong, and l4 is arithmetic-heavy
   (five walked-period categories). Registered bands: Kwaipilot **8-12 of 15**
   (from 12), Nemotron **9-14 of 15** (from 14).
4. **Nemotron's N2 completes and is WRONG.** Field: the `outcome` of item N2 on
   arm C. Registered: any terminating outcome other than `truncated`, and
   `off_by_calendar` or `wrong` rather than `correct`. N2 is the hardest walked
   item, both Qwen3.8 builds fail it, and this arm removes the reasoning that
   might have saved it. **If N2 comes back `correct` with thinking OFF, the
   reasoning loop was actively harming it**, which would be the most
   interesting result on this page.
5. **Speed improves materially.** Field: `wall_s` per arm. Registered: each arm
   under half its `default` counterpart's wall. F77 measured 12.6x on Qwen3-8B;
   half is deliberately conservative.

## Falsifiers

- **If prediction 1 fails and they still truncate with thinking off**, then
  non-termination is not a reasoning-loop property and the cause is elsewhere -
  a template defect, a stop-token problem, or something in the serving path.
  That is a bigger finding than this experiment was designed for and the right
  response is to stop and diagnose one model properly rather than run arm C.
- **If prediction 3 fails and the scores hold or rise**, then the reasoning
  these models do is worthless on this bank - it costs the entire token budget
  and buys nothing - and `off` becomes the recommended configuration rather
  than a diagnostic.

## Scope

**Scope tag: CONFIGURATION**, per model. Two models, one treatment, three arms.
Nothing here licenses a claim about `enable_thinking` generally, about either
model family, or about any other bank. F118 is this repo's worked example of
moving outward a level without new evidence.

Not measured: throughput under load, long context, tool use, or whether either
model is a good choice at `default` on any bank where it does terminate.
