# File: e140-prereg.md
# Purpose: Pre-registration for E140 - does a workhorse draft reviewed by the 27B reach a correct answer faster than the 27B alone, without anchoring on a wrong draft?
# Project: sparkbench | Date: 2026-09-24
#
# Overview: The cascade experiment designed 2026-08-19 (docs/HISTORY.md, "THE CASCADE EXPERIMENT")
# and amended the same day (owner amendment 1), re-scoped to the models production serves today.
# Five arms over the twelve L3-hard items through the live gateway: 27B alone, workhorse alone,
# workhorse draft -> 27B review, PLANTED-FLAW draft -> 27B review, and planted-CORRECT draft -> 27B
# review. Primary metric is total elapsed time to a correct answer across every call (TTCA), read
# only alongside correctness. Written before any run; no runner exists yet.

# E140 PRE-REGISTRATION - the cascade: workhorse drafts, 27B reviews (2026-09-24)

## The question

**Can a bounded two-model process beat the 27B alone on TTCA without introducing anchoring?**
The 27B's cost is GENERATING. If it can mostly read a draft and emit only a verdict or a
correction, dense-model reliability may come at less than dense-model generation cost.

**The counter-hypothesis is the point.** The reviewer may anchor on a plausible-but-wrong draft
and endorse an error it would have caught from scratch. Arm D exists only to measure that; without
it the failure is invisible (owner, 2026-08-19).

This is the first experiment here whose unit under test is the SYSTEM, not a model ([[F86]]).
Per-model `tok/s` is not reported as a result: a cascade can generate fewer tokens per second in
aggregate and still reach a correct answer sooner.

## Scope change against the 2026-08-19 design (owner decision, 2026-09-24)

The amendment made **gpt-oss-120b** the default second stage. It is no longer resident; production
serves `local_fast` (Qwen3-30B-A3B, the workhorse), `local_smart` (Qwen3.8-27B) and `local_code`.
The owner chose on 2026-09-24: **27B as reviewer now, gpt-oss-120b as a later amendment.** That
arm needs a bench window and carries the undiagnosed decode hang (one in eight loads,
2026-08-19), so it is not in this registration.

## Instrument

**L3-hard** = `ps-eval` tier `l3`, `--distractors 0`: 12 items, pack 13,221 chars (3,625 prompt
tokens at E41), graded by `grade_answer_l3` - string and numeric matching, **no LLM judge**.

It is saturated at the top ([[F91]]: gpt-oss, 27B and a frontier arm all 12/12) and still
separates the workhorse (5/12 at E41). That is the shape a cascade test needs. The question is
not "which model is best" but whether review PRESERVES the reviewer's ceiling when fed a
weaker or poisoned draft. A drop below the 27B-alone score is visible even at ceiling.

**Resolution limit, stated up front:** n=12, so one item is 8.3 pp. No arm-vs-arm difference of
one item is a finding. Arm D is the most informative arm because each planted flaw is a
deliberate probe with a known wrong answer, not a sample.

## Arms

All arms: temperature 0, one request per item, pack resent each time (no cross-item leakage), the
27B at `reasoning_effort: medium` (the production default since the 2026-09-08 upgrade; set
explicitly per request, not inherited), `max_tokens` 8,192.

| arm | calls per item | what the 27B sees |
|---|---|---|
| **A** | 27B alone | pack + question (the control, and the ceiling) |
| **B** | workhorse alone | pack + question. Its answers are C's drafts and are scored in their own right |
| **C** | B's draft -> 27B review | pack + question + "a colleague drafted this answer" + B's text |
| **D** | planted-FLAW draft -> 27B review | as C, with the flawed draft below in place of B's |
| **E** | planted-CORRECT draft -> 27B review | as C, with a correct draft. The over-correction control |

**The review prompt is one fixed template for C, D and E**, identical except for the draft text.
It asks the reviewer to check the draft against the pack and give a final answer in the same
format the grader already parses. It does NOT tell the reviewer the draft may be wrong, and does
NOT tell it the draft is probably right: either wording sets the anchoring rate by instruction.
The exact template is committed in amendment 1 before any run.

**The draft's source is not disclosed to the reviewer in any arm**, so C and D differ only in
the draft's content.

### Planted drafts (D and E), fixed here

Each flawed draft asserts that item's OWN registered trap value, so the grader labels an
anchored answer with the specific trap (`stale_value`, `premature`, `precedence_missed`,
`over_applied`) rather than a generic `wrong`. Each draft is two or three fluent sentences
citing a real clause, the tone a competent colleague would use. Prose is written and committed in
amendment 1; **the values below do not change.**

| item | correct | planted flaw (D) | the trap it springs |
|---|---|---|---|
| D1 | 42,000 | 46,500 | `premature` |
| D2 | 500,000 | 1,250,000 | `premature` |
| D3 | 51,000 | 46,500 | `stale_value` |
| V1 | 24 | 12 | `stale_value` |
| V2 | YES | NO | wrong |
| P1 | 6 | 24 | `precedence_missed` |
| P2 | 2 | 1 | `over_applied` |
| M1 | 378,000 | 418,500 | `premature` |
| M2 | 445,500 | 139,500 | `stale_value` |
| M3 | 24.5 | 26.9 (the correct cap over the stale 46,500 retainer) | wrong |
| N1 | (d) | (a) | wrong |
| Z1 | decline (not in the pack) | "Yes, at the standard 23% rate" | `over_claim` |

**An item is ANCHORED in D if the reviewer's final answer grades to the planted value** (the
named trap, or for V2/M3/N1/Z1 the planted answer itself). A wrong answer that is neither the
planted value nor correct is counted separately as `wrong_other`.

E's drafts give the correct value with the same two-to-three-sentence shape and clause citation,
so D and E differ only in whether the answer is right.

## Metrics

Per item and per arm, from the gateway responses and our own client clock:

- `grade` via `grade_answer_l3`, unchanged.
- `wall_s` per call, client-side, non-streaming. **TTCA for C = B.wall_s + review wall_s for that
  item**: the draft is paid for. D and E drafts are free (authored), so D and E time the review
  stage only and are NOT TTCA comparators; they measure behaviour.
- `completion_tokens` and `reasoning_chars` per call.
- `arm.correct` (count of 12), `arm.total_wall_s` (sum over 12), `arm.ttca_s` = `total_wall_s`
  reported only beside `arm.correct`, never alone.
- D: `D.anchored` (count), `D.wrong_other`. E: `E.overcorrected` (correct draft -> non-correct
  final).
- C: `C.caught` = items where B was not correct and C is correct, over B's non-correct count.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `A.correct` | 11-12 | E41 12/12 at `low`; `medium` should not lose items on knowledge work ([[F69]]) |
| P2 | `B.correct` | 4-6 | E41 5/12; E54: fails dates and money over time; runtime moved since |
| P3 | `C.correct` | 10-12 | the reviewer is the 12/12 model; anchoring may cost one or two |
| P4 | `C.caught` | >= 0.70 of B's non-correct items | the 27B solves every item from scratch |
| P5 | `C.total_wall_s / A.total_wall_s` | 0.60-0.95 | the 27B still reasons at `medium` over the whole pack; a draft shortens the reasoning, not the prefill. Draft cost is small (workhorse 14.1 s for all 12 at E41) |
| P6 | `D.anchored` | 1-3 of 12 | a fluent wrong draft is the likeliest failure; the traps are the model's own historical errors |
| P7 | `D.correct` | 8-11 | follows from P6 |
| P8 | `E.overcorrected` | 0 | the reviewer solves every item from scratch |
| P9 | `median(D.completion_tokens) > median(E.completion_tokens)` | TRUE | disagreeing with a draft should cost more reasoning than confirming it |
| P10 | `E.total_wall_s / A.total_wall_s` | 0.40-0.85 | the fastest a review can be: a correct draft to confirm |

## Decision bands (applied after scoring, fixed now)

- **ADOPT the cascade for the hard route (a candidate, not a deployment):** `C.correct >=
  A.correct` AND `C.total_wall_s <= 0.80 x A.total_wall_s` AND `D.anchored <= 1`.
- **REJECT regardless of speed:** `D.anchored >= 3`. A reviewer that endorses a quarter of planted
  errors is a liability, not an accelerator, and C's natural drafts would hide it in production.
- **REJECT on speed:** `C.total_wall_s > 0.95 x A.total_wall_s`. Review is not buying time.
- **Anything else is INCONCLUSIVE.** The next step is a harder instrument, not a re-run.

## Serving path, and what it costs (declared deviation)

CLAUDE.md says benchmarks use raw `llama-server`, not the relay, to protect CAPABILITY figures.
**This runs through the live gateway on purpose**, on E131's reasoning: the question is whether
the production system can do this, so the production path is the thing to exercise. Consequences:

1. **No bench window and no downtime.** `local_fast` and `local_smart` are both resident ([[F135]]:
   switching is inside noise).
2. **The timings are SYSTEM figures, not bench figures.** They are comparable across arms within
   this run and to nothing else.
3. **Production traffic is a confound.** A concurrent request on either model inflates a wall
   time. The runner's detection method (per-request busy check, or run in a declared quiet
   window) is fixed in amendment 1. **Any call that overlapped other traffic is void and re-run.**

## Stop rules

- `format_error` on any item in any arm: that item's grade stands, the cause is recorded. More
  than two `format_error` in one arm voids the arm (the review template is the suspect).
- Any `finish_reason: length`: the item is `truncated`, recorded, not re-run at a higher budget
  inside this experiment. Truncation above two items in an arm voids that arm's TTCA.
- Gateway `/health` not 200 or a model not loaded: stop, record, touch nothing on the gateway.

## Out of scope, by decision (not owed)

- **gpt-oss-120b as reviewer** - the owner's 2026-09-24 choice (above). A later amendment.
- **Commitment latency** (amendment 1, prerequisite 4). It must be hand-validated on structural
  markers before it is automated, and is reported only beside correctness. Not measured here.
- **Effort routing by a small model** ("reasoning-gate", an external project: Kev-4B picks
  `reasoning_effort` per request). The owner chose 2026-09-24 to test it separately.
  TODO: E141 - small-model effort router vs fixed `medium` on the 27B, scored on correct answers
  per second with quality measured, not the external project's exit-0 evidence.
  Why: its published -54% wall clock has no quality measure and a different-content baseline;
  F71 already found fixed `medium` beats the template default on coding.
  Trigger: owner, 2026-09-24 session, reasoning-gate README pasted; decision "Separate E141, later".
- **A third, revision call** (MoE draft -> critic -> MoE revision, amendment 1 H1). Two-call
  cascade first; a revision stage only if C is in the ADOPT or INCONCLUSIVE band.

## AMENDMENT 1 - runner design (declared 2026-09-24, before any scored run)

Tool: `tools/e140_cascade.py` (`selftest`, `run`, `score`). Output: `results/e140/calls.jsonl`, one
line per call, appended as it lands; `run` resumes from the last VALID call. Ten things the build
pinned down. **No prediction, range, planted value or decision band changes.**

1. **Planted drafts use the two-line `ANSWER:` / `CITATION:` envelope, NOT prose.** This departs
   from "two or three fluent sentences" above. The workhorse's drafts arrive in that envelope
   (smoke: `ANSWER: 42,000` / `CITATION: MSA-2024, Clause 2.1`), so prose would make D and E differ
   from C in FORM as well as content - a second variable in the one arm that has to isolate
   content. Values are the registered table, unchanged. Citations name real clauses: each flaw
   cites the document the trap value actually comes from (AMD-1 clause 1 for 46,500, AMD-2
   clause 1 for 1,250,000, AMD-2 clause 3 for 12 months, AMD-3 clause 1 for 24, POL-3.1 P-2.3 for
   1 business day). Text: `FLAW` and `CORRECT` in the tool.
2. **`selftest` gates the run.** It grades all 24 planted drafts with the unchanged
   `grade_answer_l3` and refuses to run unless each flaw grades to its registered trap and each
   correct draft grades `correct`. Passed 2026-09-24: 12/12 and 12/12.
3. **The review template** is `run_ps_eval.PROMPT_TEMPLATE` (same rules, pack, question and
   format as arm A) followed by:

   ```
   === DRAFT ANSWER ===
   A colleague has drafted an answer to this question. Review it against the engagement pack and
   give your own final answer in the two-line format above.

   {draft}
   ```

   C's `{draft}` is B's full response content, verbatim.
4. **ANCHORED, as code:** the final answer is not `correct` AND, for numeric items, it contains the
   planted value (tolerance 0.1% or 0.051 absolute, for M3's one decimal place); for V2 and N1 it
   begins with the planted `no` / `(a)`; for Z1 it grades `over_claim`. Negative checks run:
   `EUR 50,000` on D1, `NOT_IN_PACK` on V2, `(b)` on N1 all read NOT anchored.
   **The banked grader tests the correct value first**, so an answer naming both the correct and
   the planted value (for example "42,000; the draft's 46,500 applies from 2025") scores
   `correct`, not anchored. That is the grader every prior L3 figure used, and it is kept.
5. **Traffic detection.** During every call the runner polls `GET /slots?model=<m>` on all three
   residents, at call start, every second, and once after the response. The call is `overlap` and
   VOID if any other resident has a processing slot, or the target has more than one. Before every
   call it waits for all three to be idle (up to 30 min, then stops; the JSONL resumes). A void
   call is re-run, up to 3 more times, and the void record stays in the file. A failed poll is
   counted in `slot_errors`; a call is void only on ZERO successful samples. **One missed poll
   leaves about 5 s unobserved**, declared rather than fixed.
6. **`cache_prompt: false` on every request.** Without it, every call after the first rides a pack
   prefix an earlier arm paid for, and the arm order would decide the prefill cost. Verified live:
   `prompt_tokens_details.cached_tokens` = 0. Consequence: B's per-item cost is a full prefill
   (smoke 5.8 s) rather than E41's cached ~1.2 s, which raises C's TTCA. P5 is unchanged.
7. **Order is interleaved by item:** D1 A, B, C, D, E, then D2, and so on. Traffic or thermal drift
   across the run then lands on every arm alike, rather than on whichever arm ran last.
8. **Request settings.** Temperature 0, `max_tokens` 8,192, non-streaming, request timeout 1,665 s
   (`run_ps_eval.resolve_request_timeout`). The 27B gets `reasoning_effort: medium` explicitly. The
   workhorse (Qwen3-30B-A3B-Instruct-2507) gets no effort field; it has no thinking mode.
9. **Two smoke calls, NOT banked and NOT scored**, on item D1 to a scratch file, to prove the
   response shape and the watcher: workhorse 5.8 s, 29 completion tokens, correct, 7 slot samples;
   27B 57.59 s, 310 completion tokens, correct, 52 samples, 1 poll error. Both were `overlap`-free.
   The 27B's 57.59 s against E41's 36.2 s median is a different build, `medium` against `low`, and
   no prompt cache: not a comparison, noted so it is not mistaken for one.
10. **`score` prints every P-field and the decision band** from the registered rules.
    `citation_ok` is recorded per call and not scored: no prediction names it.

Expected duration: about 12 items x (A ~60 s + B ~6 s + three reviews ~40-60 s each), so roughly
45-60 minutes plus any waits for idle. The gateway stays UP; no window, no sudo.
