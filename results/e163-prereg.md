<!--
# File: e163-prereg.md
# Purpose: Pre-registration for E163 - is AMD's agent-ported HRX Loom engine faster than our production Halogen on
# Flash-Next, faster than llama.cpp as AMD claims, and does it give the same answers?
# Project: sparkbench | Date: 2026-11-16
#
# Overview: Three arms in one idle window via tools/run_e154_arms.sh (E154_RAW=results/e163/raw): LM Loom, LC llama.cpp,
# HS Halogen. Speed by tools/e163_speed.py (one client-side ruler for all three); quality by the E160 suites at
# reasoning effort low on LM and HS. Written before any prompt was sent to Loom; the only engine traffic before it was
# none (install, hash verification and builds only).
-->

# E163 PRE-REGISTRATION - AMD HRX Loom vs production Halogen vs llama.cpp on Flash-Next (2026-11-16)

## In plain English

AMD published an experiment on 2026-11-13: coding agents ported 51 popular models to a new AMD engine called HRX
Loom in four days, and the result runs long prompts about 1.5 times faster than llama.cpp. One of the 51 is the model
we run in production, Qwen3.8 Flash-Next.

We do not use llama.cpp in production; we use Halogen, which is already several times faster than llama.cpp on long
prompts (F165). So the useful questions are: is Loom faster than what we actually run, and do kernels written by
agents in a few days give the same answers? We run all three engines on this box, timed by the same client, and put
Loom through the same quality tests our production setting passed on 2026-11-13.

## Why (owner 2026-11-16)

The owner sent the AMD announcement and asked whether anything was worth testing; I proposed this run and the owner
said "Do it. Start".

## Arms

| arm | engine | weights | how served |
|---|---|---|---|
| LM | `loom-serve`, hrx-loom 0.2.0.dev0 (ROCm/hrx-system `314238a8`, CI artifact 13628412621, wheel sha256 `9dc1e352...`) | loom-fun/unsloth-Qwen3.8-Flash-Next-loom programs (sha `baf07498...`, as AMD measured) over unsloth `UD-Q4_K_XL` + `mtp-Qwen3.8-Flash-Next-Q8_0` (rev `766911a6`, sha256 verified against the package lock) | package README flags: active wait, `--pool_backing=fixed`, preset vision-mtp (MTP depth 3) |
| LC | upstream llama.cpp `9fba51d` (2026-11-16) | the same GGUF and MTP file | AMD's 1-stream baseline flags: `-md <mtp> --spec-type draft-mtp -cram 0 -c 65536 -np 1`, plus `-fa on -ngl 999` |
| HS | production's Halogen image (by digest, as E159/E160) | Halogen's own checkpoint | STOCK template, `reasoning_effort: low` per request |

**Why HS uses the stock template.** Production runs the community template at low (F186/F187). Loom's chat program
(`program/shared/program/text/qwen3_8/chat.loom`) renders the stock Qwen3.8 framing with effort levels none / low /
medium / xhigh. To compare engines rather than templates, HS is Halogen with the stock template at low, the same
framing Loom gets. Production's own E160 arm KFL (community + low, 2026-11-13, same image) is quoted as a reference, not
re-run and not scored against.

**Declared confound.** LM and HS do not run the same weights: Halogen serves its own checkpoint, Loom serves unsloth's
UD-Q4_K_XL GGUF. LM vs HS is therefore "Loom as published vs our production engine as deployed", not engine-only.
The engine-only comparison is LM vs LC on one file, which is speed only.

## Smoke (unscored, before the scored runs)

`E163_SMOKE=1` runs `tools/e163_smoke.py` against LM: "Reply with OK", "What is 2+2?" and a one-tool weather call, in
the request shapes the E160 suites use (no `model` field, model "x", Halogen's id, `/tokenize` with `content` only,
effort levels, both thinking-off spellings, streamed usage). If Loom rejects a shape a suite sends, the fix is declared
as an amendment here BEFORE any scored request, and it may only change transport (model name, field spelling), never
prompts, items, settings or grading.

## Speed block (LM, LC, HS)

`tools/e163_speed.py`: E139's fixed prompts (`results/e139/prompts.json`): P8K x3 and P32K x3 at 256 generated tokens,
D1500 at 512, non-overlapping, thinking off, temperature 0, streamed. Client-side timing for every arm, because Loom
reports no server `timings` and comparing engines on their own timings would compare rulers:

- `prefill_tps` = usage `prompt_tokens` / time to first streamed token (includes one decode step and HTTP).
- `decode_tps` = (`completion_tokens` - 1) / (last token time - first token time). With MTP on (LM, LC) and Halogen's
  default drafting (HS) this is the effective rate including speculation.

Fields: `summary.P32K.prefill_tps`, `summary.P8K.prefill_tps`, `summary.D1500.decode_tps`, `summary.P32K.decode_tps`
(decode after a 32K prompt), each the median of its requests. Server timings are recorded beside them where present.

## Quality block (LM, HS)

The E160 suites exactly as `run_kw_suite` runs them (results/e160-prereg.md "Suites" and "Scored fields"): ps-eval L5
and pr1, kw-eval large pack, writing-eval (grader only; no judge call this time), multiturn l4 and long, E33 tool use
v2 (3 runs per task), H6 l4-date with tools. `--max-tokens 32768`, `--ctx 262144` (Loom's package declares
`context_capacity` 262144), effort low, temperature 0. Scored with E160's field definitions and its noise rule: a
difference needs 2 or more items (or tasks) on a suite.

## Predictions (each names its field)

AMD's own card for this package (measured on DevLab Strix Halo runners, 2026-11-13) gives Loom 1,196 tok/s prefill at
32K and 41.9 tok/s short-prompt decode, against llama.cpp ROCm b1371 at 378.7 and 34.4.

- **P1 (AMD's headline, engine only):** LM `summary.P32K.prefill_tps` >= 1.5 x LC `summary.P32K.prefill_tps`.
- **P2 (AMD's number reproduces):** LM `summary.P32K.prefill_tps` within 15% of 1,196 (1,017 to 1,375).
- **P3 (decode, engine only):** LM `summary.D1500.decode_tps` >= 1.1 x LC `summary.D1500.decode_tps`.
- **P4 (not faster than production on prefill):** LM `summary.P32K.prefill_tps` <= 1.0 x HS `summary.P32K.prefill_tps`.
- **P5 (slower than production on decode):** LM `summary.D1500.decode_tps` <= 0.7 x HS `summary.D1500.decode_tps`.
- **P6 (no correctness regression, per suite):** on every suite, LM `correct` >= HS `correct` - 1 (L5, pr1, kw-eval,
  writing `pass`, each multiturn conversation, H6).
- **P7 (tool calling works):** LM tool-use `passed` >= HS `passed` - 1, and LM `leak_runs` = 0.
- **P8 (clean transport):** no LM suite stops on a transport or engine error after the smoke's amendments, if any.

## Decision this feeds

- If LM is at least HS's speed on both P32K prefill and D1500 decode AND P6-P8 hold: Loom becomes a production
  candidate, and the next step is a soak and template test (community template support) before any switch.
- If LM is slower than HS on either field: production stays on Halogen. The routing guide gains one line: AMD's 1.5x
  is against llama.cpp, and on this box Halogen is already past it (or not, as measured).
- If P6 or P7 fails: the failure is recorded per item as a correctness defect in the agent-written port. Anything sent
  to AMD (an issue on loom-fun/loom-skills) is outward-facing and needs the owner's approval first.

## Run notes

- One idle window (`relay_bench_window.sh idle-down`): Halogen production, Chatterbox and Flux stop for its length,
  estimated 2.5 to 3 hours. Order: LM, LC, HS. The runner's EXIT trap restores the relay and verifies it.
- `E154_NOBANK=1`: raw files are committed by hand after the window (the secret gate blocks raw transcripts).
- Kernel and Livepatch state are recorded in the results. The Loom dev build's CI artifact expires 2026-11-22; the
  install record is `/home/bench/loom-e163/sdk/loom-install.json` (copied to `results/e163/loom-install.json`).
- No cloud spend: the writing judge is not run.

## Amendment 1 (2026-11-16, 05:50Z, after the unscored smoke, before any scored request)

The smoke (`results/e163/raw/LM-smoke.jsonl`, window 05:37-05:39Z) showed loom-serve answers "Reply with OK" and 2+2
correctly, honours `reasoning_effort` low/medium/xhigh (advertised levels none/low/medium/xhigh, default none),
returns `reasoning_content` separately, returns structured `tool_calls`, and sends a usage block on a stream. It
REJECTS: a chat request with no `model` (400 `loom_route_error`), model `"x"` or Halogen's id (404 "model is not
registered"), and `/tokenize` without `model` (400). The E160 suites send exactly those shapes (kw-eval: no model and a
model-less tokenize; tool use and H6: "x"; ps-eval, writing, multiturn: Halogen's id).

Fix, transport only: for arm LM the suites connect to `tools/e163_model_proxy.py` on 127.0.0.1:8163, which sets
`model` to Loom's served id (`unsloth-Qwen3.8-Flash-Next-loom`) on every POST and forwards to loom-serve, streaming the
response back unchanged (tested against a fake SSE upstream: chunks arrive incrementally, only `model` changes). It
logs each rewrite to `results/e163/raw/LM/proxy.log`. Prompts, items, settings and grading are unchanged. The speed
block talks to loom-serve directly (it sends the served id itself). Wall times in LM's suites include one extra
loopback hop; per-item wall is not a scored field here.

Also noted: the runner's "relay NOT serving after 'up'" line is the known Halogen-solo false alarm (same in E160's
window log); production was verified separately with `halogen_effort_check.py` (LOW DEFAULT LIVE, 05:41Z, after
Halogen's ~75 s warm-up).

### Amendment 1b (2026-11-16, 05:52Z, during LM; transport only)

Correction to amendment 1's time: it was committed (`c9d03b8`) at about 05:41Z, just before the scored window opened at
05:41:24Z, not 05:50Z. Production's LOW DEFAULT LIVE check passed shortly before that.

ps-eval, writing and multiturn wait for llama-server's `GET /health` before their first item; loom-serve serves
`/healthz`, so LM l5 spent its 300 s wait on 404s and stopped with rc 1 having sent NO item (05:44-05:49Z). The proxy now
renames `GET /health` to `/healthz` (path only) and was restarted at 05:51Z; pr1 then passed its wait and began. LM l5
is re-run after HS by a second `run_e154_arms.sh LM` pass, which skips every suite that already has its file. The LM
speed block (05:41-05:44Z) did not use the proxy and is unaffected.
