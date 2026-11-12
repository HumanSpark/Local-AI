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
