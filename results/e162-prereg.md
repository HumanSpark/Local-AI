<!--
# File: e162-prereg.md
# Purpose: Pre-registration for E162 - on real client-shaped work, how close is production Flash-Next (low, medium,
# xhigh) to frontier models, judged blind and checked mechanically?
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Ten tasks in spikes/client-tasks/tasks.py, drafted by five arms, run by tools/run_e162.py (draft, grade,
# judge). Two blind judges from neither contestant's family compare every pair of arms in both orders. Mechanical
# checks count dropped unfavourable facts, planted over-claims and figures not in the source. Written before any task
# was drafted (the harness smoke sent only "Reply with OK" and a 2+2 verdict probe).
-->

# E162 PRE-REGISTRATION - client-shaped tasks, local vs frontier (2026-11-15)

## In plain English

Our earlier tests asked whether the local model gets facts right. This one asks the question a business owner
actually has: if I give it the kind of job I would give an assistant, is the result as good as ChatGPT or Claude
would give me?

We wrote ten realistic jobs for invented businesses: a proposal section from call notes, actions from a meeting, a
reply to an angry customer, a staff policy summary, a board summary from a sales table, an outage notice, a job ad,
a contract explained in plain English, a decision memo and a LinkedIn post. Each hides a trap: an awkward fact that
must stay in, and a gap a fluent writer is tempted to fill with something invented.

The local model writes each one at three effort levels. Claude Sonnet 5.5 and OpenAI's GPT-6.1 Sol write them too.
Two judges from other AI companies compare the drafts in pairs without knowing who wrote which.

## Why (owner 2026-11-15)

The owner asked for more knowledge-work testing and chose "real client-shaped tasks, judged blind against a frontier
model" over a harder document bank, medium on existing suites, or long-context retrieval.

## Tasks

`spikes/client-tasks/tasks.py`, ten tasks C01-C10. Every business, person and figure is invented. Each task names a
word limit and the house style: plain English, use only the facts given, say "to be confirmed" rather than invent.
Per task, the file fixes `negatives` (unfavourable facts a send-ready draft keeps; 20 in all), `traps` (things the
source withholds; a match is an over-claim) and `derived` (figures legitimately worked out from the source).

## Arms

| arm | model | how called | effort |
|---|---|---|---|
| L | production Flash-Next on Halogen (community template) | model-guard 127.0.0.1:8402, `local_smart` | none sent = the live default, low |
| M | same | same | `reasoning_effort: medium` |
| X | same | same | `reasoning_effort: xhigh` |
| C | `anthropic/claude-sonnet-5.5` | OpenRouter, `tools/cloud_client.chat` | provider default |
| G | `openai/gpt-6.1-sol` | OpenRouter | provider default |

All arms: the task prompt as the only user message, temperature 0, one draft per task. Local max_tokens 32,768, cloud
16,000. Local arms run one request at a time against production, L then M then X; cloud arms may run alongside.
`ops/halogen_effort_check.py` must print `LOW DEFAULT LIVE` before L and after X, or L is not the production setting.
Production stays up; other callers may share Halogen, so wall times are indicative, not a speed benchmark.

## Judges

`x-ai/grok-4.7` and `moonshotai/kimi-k3.1-pro` (OpenRouter), neither from a contestant's family (Anthropic, OpenAI,
Qwen). Rubric, prompt and verdict parser are `tools/judge_writing_pairwise.py`'s (accuracy first, then fitness for the
reader, clarity, house style; length is not quality). Every pair of the five arms, every task, both orders: 10 pairs x
10 tasks x 2 orders = 200 calls per judge. A pair-task is DECIDED only when both orders agree; otherwise a tie.
Unparsed verdicts are kept raw and counted, never coerced.

## Fields

- `grade.json`: `<arm>.totals.dropped_negatives | trap_hits | fabrication_candidates | over_length | incomplete |
  think_leaks | wall_s_total`.
- `judge-<slug>.json` records: for a pair (P, Q), `net(P over Q)` = tasks decided for P minus tasks decided for Q, over
  the 10 tasks, per judge.
- Judge agreement: the share of the 100 pair-tasks where the two judges' combined outcomes are identical.

Fabrication candidates and trap hits are scored RAW for the predictions. After the run I adjudicate each one (real
over-claim or checker false positive) and report both, as E160 did for kw-eval.

## Predictions

| | prediction | field |
|---|---|---|
| P1 | Claude beats production on client work | `net(C over L) >= 2` on BOTH judges |
| P2 | GPT beats production on client work | `net(G over L) >= 2` on BOTH judges |
| P3 | medium does not improve on low | `abs(net(M over L)) <= 1` on both judges |
| P4 | xhigh does not improve much on low | `abs(net(X over L)) <= 2` on both judges |
| P5 | low keeps the awkward facts | `L.dropped_negatives <= 3` (of 20) and `<= C.dropped_negatives + 2` |
| P6 | over-claims are rare everywhere | `trap_hits <= 2` for L and for C |
| P7 | invented figures are rare everywhere | `fabrication_candidates <= 3` for every arm (raw) |
| P8 | the judges mostly agree | agreement >= 0.60 |
| P9 | low is fast | `L.wall_s_total <= 0.5 x X.wall_s_total` |
| P10 | every draft completes cleanly | `incomplete == 0` and `think_leaks == 0` for every arm |

## Decision rule (stated now)

- If `net(C over L)` and `net(G over L)` are both <= 1 on both judges, production at low is recorded as at parity with
  frontier models on client-shaped drafting, and the routing guide says so.
- If a frontier arm leads low by >= 2 on both judges but M or X is within 1 of it on both, client-facing drafting is
  routed to that effort.
- If every local effort trails a frontier arm by >= 2 on both judges, client-facing drafting is recorded as a frontier
  (or human-edited) job, and the routing guide says so plainly.
- Judges that disagree (one says >= 2, the other <= 1) give "not shown"; that is reported as such, not averaged.

## Run notes

- Spend ceilings: each cloud draft arm $10, each judge $30. Estimated total under $20.
- Order: `draft --arm L`, `M`, `X` (sequential, production); `C`, `G` alongside; `grade`; both judges.
- Kernel and the Halogen image digest are recorded in the results; Halogen's image is pinned by digest in
  `/opt/sparkrouter/systemd/sparkrouter-halogen.service`.

## Amendment 1 (2026-11-15, 13:30Z, after kimi finished, before any analysis; tightened 13:50Z)

kimi-k3.1-pro returned an empty reply on 51 of its 200 calls (39 of 100 pair-tasks unparsed). The first pass did not
record finish_reason or token usage per call, so the cause is a HYPOTHESIS (reasoning using the whole 6,000-token cap),
confirmed or not only by the retries' metadata.

The tallies had already printed, so this is a declared deviation. The rule is mechanical and does not depend on
outcomes:

1. Only sides whose reply was empty are re-asked. Every non-empty verdict stays as it was.
2. Each is re-asked once, with the same prompt, draft order, temperature 0, timeout and client retries. Only
   `max_tokens` changes (6,000 to 16,000). Command: `run_e162.py judge --redo-empty`.
3. Stopping rule: a side still empty after its one retry, or not reached when the $15 retry ceiling is hit, stays
   unparsed and is reported as unresolved. No further retries of any kind.
4. Each record keeps its first pass in `first_pass`. The first-pass cost stays in `spend` and the retry cost goes in
   `spend_redo`. Results report first-pass completion and completion after retries separately, and give the total
   judging cost of both.
5. Each retry records finish_reason, completion tokens, reasoning and content length, and wall time. The first two
   retries (C01 C v G yx, C01 C v M xy) ran before those fields were added and record only finish_reason. Both
   finished with `stop`.

grok-4.7 gets the same treatment if it has empty replies when it finishes.
