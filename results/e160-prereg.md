<!--
# File: e160-prereg.md
# Purpose: Pre-registration for E160 - acceptance test of community template + low effort as Flash-Next's production setting for all usage.
# Project: sparkbench | Date: 2026-11-13
#
# Overview: The candidate production setting (KFL) and today's default (KX, the reference) run eight existing judge-free
# suites covering the production usage types, plus a blind frontier judge on the writing drafts. Written before any E160
# run; revision 2 replaces revision 1 (9009cd1), also before any run. Runner: tools/run_e154_arms.sh KFL KX
# (run_kw_suite). Raw: results/e160/raw/<arm>/<suite>.json. Judge: tools/judge_writing_pairwise.py.
-->

# E160 PRE-REGISTRATION - production acceptance of community template + low (2026-11-13, revision 2)

**Written before any E160 run.** Revision 1 (commit 9009cd1) compared three arms on knowledge work and writing only.
Before anything ran, the owner set the frame (2026-11-13): "Assume that community template + low is our new production
setting for all usage. Test it." Revision 2 therefore tests that setting across every usage type we have an instrument
for, against today's default as the reference. The stock-medium arm (KM) is dropped.

## In plain English

We are treating "community template, low thinking" as Flash-Next's production setting and checking it on everything
production is used for. That covers answering from documents, judging what to refuse, writing, long conversations,
using tools, and date arithmetic with a tool. Coding was already tested in E159 (8/10). Each test also runs on today's
setting (stock template, maximum thinking), so any loss shows up as a difference.

## Arms (engine, weights and image as E159)

| arm | template | effort sent | role |
|---|---|---|---|
| KFL | froggeric v22.5 (pinned, sha256 e57684ba...) | `low` | the production candidate |
| KX | stock (sha256 c3cf9e34...) | `xhigh` | today's default; the reference |

Order: KFL, then KX. Halogen image `ghcr.io/peonist-ai/halogen-flash-server@sha256:b53c96ed...`, kernel 7.0.0-42.

## Suites (all existing; graded by string, number or tool-call checks; no AI grader except the declared judge)

| usage | suite | items | runner |
|---|---|---|---|
| document Q&A (hard) | ps-eval L5 | 24 | `run_ps_eval.py --tier l5 --external` |
| refuse / comply judgement | ps-eval pr1 | 12 | `run_ps_eval.py --tier pr1 --external` |
| real-document knowledge work | kw-eval | 26 | `run_kw_eval.py --pack l --item-packs s,m,l` |
| writing to a brief | writing-eval | 7 | `run_writing_eval.py --external` |
| multi-turn conversation | multiturn `l4` and `long` | graded turns per conversation | `run_multiturn_eval.py --external` |
| tool use (6 tools, 7 categories incl. no-tool traps, error recovery, ambiguity) | E33 tool-use v2 | 22 tasks x 3 runs | `tooluse_harness_v2.py --base-url` |
| date arithmetic with a date tool | H6 l4-date, tools on | 6 | `run_h6_date_arm.py --base-url --tools on` |
| coding | already measured: E159 HFL 8/10 | 10 | not re-run |

Common settings: `--max-tokens 32768` everywhere (so xhigh is never cut off, F153), `--ctx 262144` (Halogen's n_ctx
from /props), temperature 0 (each runner's built-in). The ps-eval, writing and multiturn runners gained an `--external`
mode. It points them at the engine the runner started instead of launching llama-server, and records the llama.cpp
offload gate as skipped. The runner's GTT line at engine start is the offload evidence. A truncated or transport-failed
item stops a suite loudly where the runner already does that, and is never scored as a miss.

**Declared deviations.** (1) E159 sampled at temperature 1.0, while these suites run at their historical temperature 0
so the scores compare with F67/F69 and single samples carry less noise. (2) Long-context needle retrieval
(`run_longctx_eval.py`) is NOT in this run. Its runner relaunches llama-server per context length and has no effort
control. kw-eval's large pack is the long-document coverage here. Untested usage is reported as untested.

## Blind writing judge (owner request, 2026-11-13)

After both arms, `tools/judge_writing_pairwise.py` shows `anthropic/claude-opus-5.5` (OpenRouter, not a contestant)
each writing task's brief and the two drafts labelled A and B, with no arm names. It judges each task in both orders:
7 x 2 = 14 calls, ceiling USD 10. A task counts as a win only when both orders agree; a split is a tie.

## Scored fields

- `correct` per suite: ps-eval outcome counts; kw-eval mechanical score (`score_kw_eval.py`), where `needs_judge`
  items are counted and reported, not scored; writing grader `pass` count; multiturn graded turns passed per
  conversation; H6 correct.
- tool use: a task counts as `passed` when `success_rate` >= 2/3. Also `leak_runs` (tool call leaked into text).
- L5 per-category correct.
- `over_claim_rate` (L5 underspecified, kw-eval unanswerable); pr1 `missed_flag` (complied with a must-refuse item).
- judge: KFL win / tie / loss over 7 tasks.
- `tokens_median` and `wall_median_s` per item, per suite and pooled.

**Noise rule:** one sample per item (tool use: three runs per task). A quality difference needs **2 or more** items
(or tasks) on a suite, or 2 or more net decided tasks on the judge. A speed claim needs `tokens_median` and
`wall_median_s` to move the same way.

## Predictions (each names its field)

- **P1:** KFL L5 `correct` >= KX L5 `correct` - 1.
- **P2:** KFL kw-eval `correct` >= KX kw-eval `correct` - 1.
- **P3:** KFL pr1 `correct` >= KX pr1 `correct` - 1, and KFL `missed_flag` = 0.
- **P4:** `over_claim_rate` = 0 on both arms.
- **P5:** KFL writing `pass` >= KX writing `pass` - 1.
- **P6:** blind judge: KFL losses - KFL wins <= 1 over the 7 tasks.
- **P7:** KFL multiturn graded turns passed >= KX - 1, on each conversation.
- **P8:** KFL tool-use `passed` tasks >= KX - 1, and KFL `leak_runs` total = 0.
- **P9:** KFL H6 `correct` >= KX - 1.
- **P10 (where low would lose):** if KFL scores below KX on L5, every lost item is in payment_clock, statutory_period,
  acceptance_window, precedence, conflict or composition, and none is in underspecified or which_instrument.
- **P11:** pooled KFL `tokens_median` <= 0.5 x KX and pooled KFL `wall_median_s` <= 0.5 x KX.

## Decision this feeds

Acceptance means no suite fails the noise rule against KX (P1-P3, P5-P9) and P4 holds. Then community template + low
is supported as the production setting for every usage type tested here. Any suite that fails names a work type to
route to a higher effort. The setting can stay as the default with that exception, and requests can still override
effort. Adopting it, and any routing, is the owner's call. This run changes no production config.

## Interaction with E159

E159 HX (coding, xhigh) was paused at a task boundary for this run at the owner's request (E159 amendment 6). HX 1-6
are done. HX 7 was in flight and finishes before E160 starts. HX 8-10 resume after E160.
