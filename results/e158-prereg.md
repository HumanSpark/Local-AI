# E158 pre-registration - newer local coding candidates on the frozen E156 bank

Written 2026-11-06 before any E158 arm runs. Amendments are appended below with a timestamp before the runs they affect.

## In plain English

Yesterday's harder test (E156, 10 real coding fixes from our own repos) put two local models level with or ahead of
Claude. Flash-Next solved 9 of 10, Qwen3.8-27B solved 8, and Sonnet 5.5 and Opus 5.5 solved 8 each. People in the
local-AI community suggested newer models built for coding: Ornith 1.5, Tess 4 and 4.5, and KRAFTON's Raon-1. This test
gives each of them the same 10 fixes under the same rules, to see whether any of them beats Flash-Next. The score is
tasks solved. Time is reported, but a slow model is not marked down.

## Design

- **Bank:** `results/e156/bank.jsonl`, frozen at amendment 4 (sha256 prefix `4ea581da822d8edb`), the final prompts of
  every E156 arm.
- **Harness and isolation:** same harness and runner as E156: `tools/run_e154_arms.sh` (frozen copy per run),
  `--isolate podman`, verify in a fresh container, 3,600 s per task, one relay idle window.
- **Comparators:** the E156 arms as scored (H 9/10, T27 8/10, S 8/10, O 8/10, Q 2/10). They are not re-run.
- **Engine:** newest upstream llama.cpp at the time of the run, `e14a77971` (2026-11-06), Vulkan build, as required by
  the owner's latest-software rule. Raon-1 uses KRAFTON's fork `fb895662d` because upstream has no `raon1`
  architecture. Every arm uses `-c 131072 -fa on -ngl 999 --jinja` on a single slot pool (no explicit `-np`).
- **Sampling:** each model card's own sampling settings, as in E154/E156.

| Arm | Model (file, `/opt/models/staging`) | Sampling | Notes |
|---|---|---|---|
| OR35 | Ornith-1.5-35B-A3B Q8_0 | T 0.6, top_p 0.95, top_k 20 | card: precise coding |
| OR122 | Ornith-1.5-122B Q5_K_M | T 0.6, top_p 0.95, top_k 20 | card: precise coding |
| TS45 | Tess-4.5-27B Q8_0 + MTP draft head Q8_0 | T 1.0, top_p 0.95, top_k 20 | card: `--spec-type draft-mtp` |
| TS4 | Tess-4-35B-A3B Q8_0-MTP-Q4D-Q4H-PV64K | T 1.0, top_p 0.95, top_k 20 | no speculation (see below) |
| RA | Raon-1-mini-preview Q8_0 | T 1.0, top_p 0.95, top_k 20, min_p 0, presence 0 | KRAFTON fork |

- **Tess-4 settings:** the Tess-4 card's draft-mtp runtime is a fork (`opt-minimax`), and the card says to serve
  without speculation for evals. Its card gives no sampling, so it borrows the Tess-4.5 card's.
- **Speculation:** speculative decoding changes speed only. The trunk model verifies every drafted token.
- **Run order:** OR35, OR122, TS45, TS4, RA. Order by expected value. Raon is a preview and has the highest load risk.
- **GPU offload evidence:** after each engine reports ready, the runner logs VRAM and GTT in use from amdgpu sysfs. An
  arm whose GTT use is far below its weight size is treated as not offloaded and its speed is not reported. This
  replaces the startup-log grep, because this llama.cpp's default verbosity prints no per-layer offload line (seen on
  the Raon load test, 2026-11-05).

## Scoring

The score is pass or fail per task, from the `status` field of `results/e158/raw/<arm>/<task>.json`. That status
comes from the hidden fail-to-pass tests plus a pass-to-pass guard, run in a fresh container. The headline is tasks
solved out of 10. A difference of one task is "about the same".

## Predictions

Each prediction names the field it is scored on: tasks solved = count of `status == "pass"`.

- **P1:** the best E158 arm solves at least 8/10 (tasks solved, max over the E158 arms).
- **P2:** no E158 arm solves more than H's 9/10 (tasks solved, each arm).
- **P3:** OR122 solves at least as many as OR35 (tasks solved).
- **P4:** TS45 solves at least as many as T27's 8/10. Tess-4.5 is a fine-tune of Qwen3.8-27B, the T27 model
  (tasks solved).
- **P5:** RA solves at most 6/10. It is a small preview model (tasks solved).
- **P6, reported only, not a prediction:** median wall minutes per task for each arm.

## Limits stated up front

- The bank is 10 tasks from three of the owner's Tier B repos. A one-task gap is noise.
- Four arms share this llama.cpp build and the Halogen/Talus comparators use their own engines. A model result here is
  a model-plus-engine result, as in E154.
- The E156 prompts were corrected four times (amendments 1-4) during E156. E158 sees only the final prompts.
