<!--
# File: results/e164-prereg.md
# Purpose: Pre-registration for E164 - Qwen4 Max (OpenRouter) on the E160 suites and the E162 client-drafting bank.
# Project: sparkbench | Date: 2026-11-17
#
# Overview: Written and committed BEFORE any scored call. Runner tools/run_e164.sh. Suites reach OpenRouter through
# tools/cloud_proxy.py (ledger results/e164/raw/ledger.jsonl); drafting and judging through tools/run_e162.py
# --out-dir results/e164/drafting. Owner budget $10 (2026-11-17), enforced as three hard ceilings summing to $9.50.
-->

# E164 PRE-REGISTRATION - Qwen4 Max against production and the cloud references (2026-11-17)

## In plain English

Alibaba released Qwen4 Max on OpenRouter on 2026-11-16. It is the first Qwen4 model and is available only through the
API: there are no Qwen4 weights on Hugging Face today, so it cannot run on this box. We test it anyway, for two reasons.
It tells us where the next generation of the model family we run in production lands against production and against
the cloud models we already measured. And when open Qwen4 models ship, it gives us a ceiling to compare them with.

We run it on the same tests production passed in E160, and on the ten client-drafting jobs from E162, judged blind
against production, Claude Sonnet 5.5 and GPT-6.1 Sol. Budget: up to $10, owner-approved.

## Arms

| arm | model | how called | source |
|---|---|---|---|
| Q | `qwen/qwen4-max` | OpenRouter, provider default reasoning, $1.425/$4.275 per M tokens (listing 2026-11-17) | NEW, this run |
| KFL | production Flash-Next, community template + low | Halogen | E160, banked (c6c7878) |
| KX | production Flash-Next, stock + xhigh | Halogen | E160, banked (6560d5b) |
| L | production at its live default (low) | model-guard | E162, banked |
| C | `anthropic/claude-sonnet-5.5` | OpenRouter | E162, banked |
| G | `openai/gpt-6.1-sol` | OpenRouter | E162, banked |

The axis is the model. Q is the only new arm; every comparison arm is a banked result, not re-run.

## Method

**Suites (E160's, unchanged):** ps-eval L5 (24), ps-eval pr1 (12), writing-eval (7), multiturn l4 and long, E33 tool
use v2 (36 tasks x 3 runs), H6 l4-date with the date tool (6). Same runners, same flags as `run_kw_suite` in
`tools/run_e154_arms.sh` except: `--thinking default` (the runners then send no reasoning setting, so Qwen4 Max uses its
provider default, as E162's cloud arms did), `--allow-busy-gpu` on ps-eval and H6 (their guard protects local
timings; this arm's timings are cloud timings and are not compared), and the endpoint is the proxy on 127.0.0.1:8164.

**Not run: kw-eval.** Its runner measures context through the server's `/tokenize`, which OpenRouter does not have,
and it sent 4.1M prompt tokens in E160 (about $5.90 at Q's price). Both reasons exclude it.

**The proxy (`tools/cloud_proxy.py`)** pins the model, adds the vaulted key, answers `/health` itself, and copies
OpenRouter's `reasoning` text into `reasoning_content` so the runners record it. Prompts, items, sampling and grading
are unchanged. Every call, with OpenRouter's billed cost, is in the ledger. Smoke 2026-11-17: one call, $0.00012,
provider Alibaba, correct answer, response shape accepted.

**Drafting (E162's bank, unchanged):** `run_e162.py --out-dir results/e164/drafting draft --arm Q` (cloud max_tokens
16000, temperature 0, as C and G), then `grade`, then `judge --judge x-ai/grok-4.7 --arms Q,L,C,G`. E162's drafts-L,
drafts-C, drafts-G and judge-grok-4.7.json are copied into that folder first, so the judge skips the pairs it already
decided and asks only Q-L, Q-C and Q-G (3 pairs x 10 tasks x 2 orders = 60 calls). One judge, not two: Kimi cost $12.92
in E162 and agreed less with hand adjudication; Grok agreed with Kimi on 67 of 100 pair-tasks.

**Ceilings (hard, each enforced by its own process):** suites $5.50 (proxy ledger), drafting $1.00, judge $3.00.
Sum $9.50, under the owner's $10.

**Scoring:** suites by `score_e160.arm_fields`, unchanged (field names below are its keys; kw fields absent). Drafting: net per pair = tasks decided for the first arm
minus for the second, of 10, decided = both orders agree (E162's rule); mechanical checks by `grade`.

**Noise rule (E160's):** one sample per item; a difference of 2 or more items is needed to call one arm better.

## Predictions (each names its field)

- **P1:** Q `l5` >= 23 (KFL 23/24).
- **P2:** Q `pr1` = 12 and `missed_flag` = 0.
- **P3:** Q `writing` >= 6 (KFL 6/7).
- **P4:** Q `mt-l4` >= 9 and `mt-long` >= 18 (KFL 9/11, 18/20).
- **P5:** Q `tooluse` >= 33 and `leaks` = 0 (KFL 33/36, 0).
- **P6:** Q `h6` = 6.
- **P7:** grok net, Q over L >= +3 (Sonnet over L was +3 in E162).
- **P8:** grok net, G over Q >= +1 (GPT-6.1 Sol stays ahead).
- **P9:** grok net, Q over C >= 0.
- **P10:** total provider-reported spend (proxy ledger + drafting + judge records) <= $8.00.

## Decision rule

No production decision follows: Q cannot run locally. The result is recorded as a finding and a routing-guide note
(where Qwen4 Max sits for cloud fallback), and as the reference arm for any open Qwen4 model that ships.

## Known limits, declared now

- **Every Q wall time is VOID as a speed measure (Rule 9):** it is network plus a cloud provider's queue, and
  `--allow-busy-gpu` is passed because production keeps the GPU. Correctness is unaffected.
- Q runs at its provider default effort; KFL ran at low. Q's per-item tokens and wall time are reported, never
  compared as speed.
- The suites are near ceiling for production (23/24, 12/12, 6/6, 33/36), so they can show Q losing items, not much
  winning. The drafting bank is the discriminating test.
- E162 task C02 has a wrong weekday in the prompt (E162 known defect). It is left as is so Q sees what the others saw.
- A transport failure or a 402 from the ceiling stops a suite loudly; it is never scored as a miss.

## Amendment 1 (2026-11-17 05:20Z, before any affected suite produced a result)

The first launch (05:10Z) stopped l5, pr1, writing, mt-l4 and mt-long within a second each with HTTP 404: their
context preflight (`bench_context`) asks the server's `/tokenize`, and H6 attached by URL asks `/props`. OpenRouter
has neither, and the proxy served only `/health`. No item was sent and nothing was scored. Tool use is unaffected
(it was already running) and continues.

Fix, transport only: `cloud_proxy.py` now answers `/tokenize` with the text's UTF-8 byte count, a strict upper bound
on tokens for a byte-level tokenizer, and `/props` with n_ctx 262,144 (below Q's real 1M). The preflight can therefore
only be stricter than reality. Consequence: any token count a runner records from `/tokenize` for Q (multiturn's
history size, the preflight's `longest_prompt_tokens`) is a byte count, not tokens, and is not compared. Each call's
provider-reported `usage.prompt_tokens` in the ledger is the authoritative size and the truncation check. Prompts,
items, settings and grading are unchanged. The five suites and H6 run after the first launch finishes, through the
same ledger and $5.50 ceiling.
