# E159 prereg - Flash-Next reasoning effort and the froggeric template

**Date:** 2026-11-12 · **Window:** owner granted the server for 12 h from ~00:38Z (ends ~12:38Z) ·
**Written before any E159 run.**

## In plain English

Production runs Qwen3.8 Flash-Next. Its official chat template tells it to think at the
highest setting ("xhigh") unless the caller asks for less. Our coding result for it (9 of 10
real fixes, E156) was measured at that default. It cost a median of about 59,000 tokens and 21
minutes per task. Community testers report that a fixed template from froggeric, which defaults
to "medium", cuts thinking by roughly 15x. One tester claims quality ranks xhigh > low > medium.
This run asks two things on the same ten tasks. Does a lower setting make it faster? Does it cost
correctness?

## Why (trigger)

Owner, 2026-11-12, relaying a community thread: "froggeric template now, and if that isn't
sufficient I guess I'll test Swift"; "I have seen benchmarks where Qwen Flash Next quality goes
as xhigh > low > medium"; "the first 12 tests completed using a median of only 1.6K tokens vs the
non-froggeric using 24K". Then: "set up a benchmark test to see if any of this improves speed or
quality". Inspection on 2026-11-12 (`3487e49`): Halogen serves the stock template,
`reasoning_effort|default('xhigh')`, and the E156 H body sent no effort.

## Measured before the run (not scored)

Production (guard 127.0.0.1:8402, `local_fast`) honours a top-level per-request `reasoning_effort`.
For one fixed prompt, prompt_tokens were 93 with no effort (xhigh system line), 81 at `low` (low line)
and 51 at `medium` (no line). This matches the stock template. So the arms below set the effort per
request, which any client can do. No production change is needed to adopt a winner.

## Arms

All arms use the same engine, weights and sampling as E156 H. Engine: Halogen image
`ghcr.io/peonist-ai/halogen-flash-server@sha256:b53c96ed...` (= production's
`sparkrouter-halogen.service`). Weights: `/opt/models/staging/halogen-qwen3.8-flash-next-v2`.
Sampling: 1.0 / 0.95 / top_k 20 / min_p 0.

| arm | template | effort sent | what it isolates |
|---|---|---|---|
| HF | froggeric v22.5 | none (template default = medium) | "the froggeric template", as the thread ran it |
| HFL | froggeric v22.5 | `low` | the thread's suggested follow-up |
| HM | stock (sha256 c3cf9e34abf4f9e3) | `medium` | effort alone, without changing the template |
| HL | stock | `low` | effort alone |
| HX | stock | `xhigh` (explicit = the default) | control: E156 H re-run on today's kernel |

froggeric template: `froggeric/Qwen-Fixed-Chat-Templates` commit `855bffc49448e299789730ff92c9b8d834d6cc14`,
`chat_template.jinja` 28,234 bytes, sha256 `e57684bae4156211a55473c5a63be976a405a37ab5be5ae0e5abf1df5349c4b2`,
size checked against the HF tree API. Copy: `var/e159/froggeric/chat_template.jinja`, mounted read-only over the
stock file. HF vs HM separates template wording from effort.

**Run order:** HF HFL HM HL HX. The cheap arms go first, so results exist even if the window runs
short. HX goes last because E156 H (9/10, kernel 7.0.0-38) is the fallback comparator if HX is cut off.
This run is on kernel 7.0.0-42.

**Common (as E156):** frozen bank `results/e156/bank.jsonl` (10 tasks), `--isolate podman`, the same four tools,
60-minute wall budget per task, 200 model calls, 6 recoverable tool errors. One run per task.
`E154_DEADLINE` = 11:25Z: no task starts after it, so a final 60+10-min task still ends inside the window.
Unstarted tasks are reported as NOT RUN, not as failures.

**Declared deviations.** (1) The standing latest-software rule is NOT applied to the engine. The
question is what production should send, so the production image is the one under test. (2) Swift 1.5
(tomngdev GGUF fine-tune) is not an arm. It ships only as GGUF and Halogen loads `.hgn`, so testing it
would change the engine as well as the weights. It is a candidate for a later run, conditional on this
result (see below).

## Scored fields (results/e159/raw/<arm>/<task>.json)

- `pass_count` = tasks with `status == "pass"`.
- `tokens_median` = median `usage.completion_tokens` over the tasks run, failures included.
- `wall_median_s` = median `wall_time` over the tasks run, failures included.

**Noise rule, declared now:** one run per task at temperature 1.0. A pass_count difference of 1 is
noise. A quality claim (better or worse) needs a difference of **2 or more**. A speed claim needs
`tokens_median` and `wall_median_s` to move in the same direction.

## Predictions (each names its field)

- **P1:** HM `tokens_median` <= 0.5 x HX `tokens_median`.
- **P2:** HM `pass_count` >= HX `pass_count` - 1 (medium costs no real quality on this bank).
- **P3:** HL `pass_count` <= HM `pass_count` (F71's middle optimum carries to Flash-Next; the
  thread's "low > medium" does not reproduce).
- **P4:** HF `pass_count` within +/-1 of HM, and HF `tokens_median` within +/-25% of HM (at the same
  effort, the template's wording does not matter).
- **P5:** HX `pass_count` >= 8 (E156 H's 9/10 reproduces within noise on kernel -42).
- **P6:** HX `wall_median_s` >= 3 x HM `wall_median_s`.

## Decision this feeds

If an arm meets the noise rule's speed bar and is within 1 of HX on pass_count, recommend that clients
(the coding route first) send that effort, and amend the routing guide. If the medium and low arms
lose 2+ passes, Swift 1.5 becomes the next run, as the thread suggested: it claims xhigh quality at
fewer tokens. Adopting any of this is the owner's call. This run changes no production config.

## Amendment 1 (2026-11-12 18:30Z, before any task was scored)

The first attempt started at 00:36Z and was stopped at 00:47Z so another GPU job could use the GPU. No task finished and
nothing was scored; `results/e159/raw/HF/harness.log` from that attempt is kept. The 12 h window and the 11:25Z
deadline above are void.

**New window:** the owner approved (2026-11-12) running E159 to completion as soon as another GPU job released benchhost,
which happened at ~18:25Z. **New `E154_DEADLINE` = 2026-11-13 07:00Z (epoch 1794553200).** No task starts after it.
Arms, run order, bank, budgets, scored fields, predictions and the noise rule are unchanged. Kernel is still
7.0.0-42.

## Amendment 2 (2026-11-12 19:28Z, before the affected task is re-run)

At 19:22Z E159 was stopped to give another GPU job a ~45 min window for Chatterbox and one render. Tasks HF 1-3 had
finished and are kept. My pause attempt (SIGSTOP on the runner) orphaned it from its parent shell, so the kernel's
SIGHUP killed it. Its EXIT trap then stopped the bench engine while HF 4/10 (sparkforge-baab4031f) was still working,
at turn 69, 573 s in. The harness verified the working tree it had at that moment and recorded a pass.

That record is not a clean run: the model was cut off by our action, not by its own stop or a budget. **It is set
aside, not scored:** `results/e159/raw/HF/superseded/sparkforge-baab4031f.interrupted-20261112T1923Z.json`. HF 4/10
is re-run from scratch when E159 resumes. Nothing else changes. Future pauses wait for a task boundary and never
signal the runner.

## Amendment 3 (2026-11-12 22:15Z, before any task the 07:00Z deadline would affect)

At ~15 min per task, the 43 tasks left at 22:08Z will not fit before 07:00Z. The owner extended the window
(2026-11-12): **new deadline 2026-11-13 11:00Z (epoch 1794567600).** The running runner cannot take a new deadline while it
runs. So any task it reports as NOT RUN after 07:00Z is not a result. That task writes no record, and it is run when the
runner is relaunched with the new deadline (done tasks are skipped). Nothing else changes. HF 1-7 scores (6 pass, 1 fail) were
seen, but the extension was decided on pace alone and applies to every arm equally.

## Amendment 4 (2026-11-12 22:25Z)

The owner removed the deadline: "I want it completed. Deadline is arbitrary." When the runner relaunches after 07:00Z it
runs with `E154_DEADLINE=0` (none), so every arm runs to completion. The NOT RUN handling in amendment 3 is unchanged.

## Amendment 5 (2026-11-13 00:55Z, before any affected task runs)

The owner changed the order (2026-11-13): "do low before medium (let current test finish)". HM 7/10 (in flight) finishes
as normal. The runner then stops at that task boundary and relaunches as **HL, then HM 8-10, then HX**, with no
deadline. Finished tasks are skipped. Arms, settings, bank and scoring are unchanged. The pause holds the runner
(SIGSTOP) in its own session (setsid), so it cannot be orphan-killed as in amendment 2. The runner exits only once the
in-flight task has written its record.

## Amendment 6 (2026-11-13 04:50Z)

At the owner's request (2026-11-13: "Pause the max testing. Let's do some knowledge work and writing tests"), HX pauses
at a task boundary for E160 (`results/e160-prereg.md`). HX 1-6 are done, and HX 7 finishes normally before the pause.
HX 8-10 resume after E160 by relaunching `tools/run_e154_arms.sh HX`, which skips finished tasks. Nothing else changes.
Amendment 5's time (00:55Z) is corrected to 00:52Z, when the swap actually happened.
