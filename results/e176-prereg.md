<!--
# File: results/e176-prereg.md
# Purpose: Pre-registration for E176 - is Ling-3.2-air (124B total / 5.5B active) faster and as capable as Flash-Next here?
# Project: sparkbench | Date: 2026-11-24
#
# Overview: Written before any Ling-3.2-air load. Speed leg (tools/run_e176_speed.sh) then the E167 hard coding bank
# (tools/run_e154_arms.sh arm LG). Predictions name their field. Deviations are findings; amendments are declared
# before the runs they affect.
-->

# E176 PRE-REGISTRATION - Ling-3.2-air on benchhost (2026-11-24)

## In plain English

The owner sent inclusionAI's new Ling-3.2-air and asked for a benchmark straight away. It is a large model (124B
parameters) that only uses 5.5B per word, so it should be fast here. Its maker says it got much better at workflow
automation and professional documents. We measure two things: how fast it runs on this box, and how many of our ten
hard real coding fixes (the E167 bank) it solves, against Flash-Next, our production model.

## Setup

- Model: bartowski/Ling-3.2-air-GGUF @ `2073edb5`, Q3_K_M (57.3 GiB, 2 shards; manifest entry "Scouting (2026-11-24)").
  Q3_K_M is the largest quant under the ~60 GiB memory-edge line (F193), so no owner-at-the-power-button run is needed.
  **Confound, declared:** Flash-Next runs at UD-Q4_K_XL (104 GiB); Ling runs at roughly 3.9 bits. A Ling loss could be
  the quant, not the model.
- Engines: upstream llama.cpp `94f3af3d0` (2026-11-22, the E174 build) and `ae6a7ad2c` (2026-11-24, newest), Vulkan.
- Speed: llama-bench `-p 512 -n 128 -r 3 -fa on -ngl 999`, f16 KV, one invocation per depth 0 / 8192 / 32768, both
  builds. Flash-Next comparison = E174's f16 rows on `94f3af3d0` (not re-run: a 104 GiB load is over the F193 line):
  d0 pp512 516.68 / tg128 26.68; d8192 427.77 / 25.92; d32768 346.06 / 25.01 (t/s).
- Bank: `results/e167/bank.jsonl` (sha256 prefix `925b63296a2fd720`), same settings as E167: 3,600 s per task, 200
  model calls, podman isolation, one attempt. Arm LG = llama-server `ae6a7ad2c`, `-c 131072 -fa on -ngl 999 --jinja`,
  card sampling (temperature 1.0, top_p 0.95, top_k 20), thinking = template default (on). Comparison = E167 arm H
  (Flash-Next on Halogen, 2026-11-18): pass_count 5/10, wall_median_s 685. **Different engine and date for H**: the
  comparison is setup against setup, not model against model.

## Predictions (field named for each)

- **P1** (`tg128` at d0, build 94f3af3d0): Ling > 26.68 t/s (faster decode than Flash-Next, 5.5B active).
- **P2** (`tg128` d32768 / d0, build 94f3af3d0): Ling keeps >= 90% of its d0 decode at 32K (hybrid linear attention).
- **P3** (`pp512` at d0, build 94f3af3d0): Ling >= 300 t/s.
- **P4** (`tg128` at d0, ae6a7ad2c vs 94f3af3d0): within +-5% (two days of upstream change).
- **P5** (`pass_count`, E167 bank): Ling >= 3/10.
- **P6** (`pass_count`, E167 bank): Ling < 5/10 (does not beat Flash-Next).
- **P7** (`wall_median_s`, E167 bank): Ling < 685 s.

## Gates

- G1 load: llama-server reaches ready with every layer offloaded (log grep, zero evidence = fail). A DeviceLost stops
  E176 and the box is rebooted before any further GPU load (F193).
- G2 tool calls: the bank's first task produces at least one parsed tool call; if none parse (template/parser gap),
  the bank leg stops and is reported as not run, not as 0/10.

## Run log

- 2026-11-24 11:43Z speed leg (both builds, all depths rc=0), relay restored and verified 11:54Z.
- 11:55Z bank leg started (Ling server ready in 26 s, 57 GiB in GPU memory; the load gate held). The tool-call gate held:
  task 1 made 46 tool calls, 0 malformed.
- Tasks 1-4 scored: all fail (task 1 context overflow at 135,730 tokens after editing only test files; task 2 3,488 s;
  task 3 2,501 s; task 4 hit the 3,600 s limit).
- **~15:40Z PAUSED on the owner's instruction** to run the Flash-Next HTR test (E177) first. Task 5
  (`sparkforge-66de8e1d0`) was interrupted mid-run; its file is the harness's `status: started` placeholder, which the
  runner's resume check (`-s file`) would wrongly treat as done. **To resume: delete
  `results/e176/raw/LG/sparkforge-66de8e1d0.json`, then re-run `tools/run_e176.sh` with the speed leg skipped** (tasks
  1-4 are kept and skipped). Not a deviation of method: the same task is re-run from scratch.

## Amendment A1 (2026-11-25, declared before these runs) - the easier banks

Owner, 2026-11-25: "there's no point in just having it fail 0 of 10 on the hard coding bank with no idea of how it does
on the easier ones." Ling is run up the ladder from the easiest bank, same server and settings as the bank leg:
1. **E154 bank** (15 real fixes, `results/e154/bank.jsonl`), 1,200 s per task (E154's budget), podman. Production
   (Flash-Next on Halogen) solved 15/15 there.
2. **E156 bank** (10 bigger fixes, `results/e156/bank.jsonl`), 3,600 s per task (the capability index's budget),
   podman. Production solved 9/10.
- **P8** (`pass_count`, E154 bank): Ling >= 5/15.
- **P9** (`pass_count`, E156 bank): Ling >= 2/10.
- **P10** (`pass_count`): Ling's E154 share > its E156 share > its hard-bank share (0/10), i.e. the ladder orders it.
Raw records: `results/e176/raw-e154/LG/`, `results/e176/raw-e156/LG/`.
- 2026-11-25 ~01:17Z: A1's E154 leg was stopped during task 4 (clearmail-12bddf4d0) to start a settings sweep; the
  owner then asked to finish the easy bank as configured and report it. The interrupted task's record (status
  "killed") is removed and the leg resumes with that task re-run from scratch; tasks 1-3 are kept. The E156 leg is
  held until the easy bank is reported (owner decides it alongside the settings sweep).

## Amendment A2 (2026-11-25 ~01:45Z, before any A2 run): thinking off

Owner 2026-11-25: "make changes to the Ling setup to get it to run properly". On the easy bank Ling spent 52-100 s per
turn and changed no file in 20 minutes (tasks 1-3, A1). A2 changes ONE thing: arm LGN = LG with
`chat_template_kwargs: {"enable_thinking": false}` sent per request (inclusionAI's card documents this switch; the
template then says "detailed thinking off"). Same server, build, quant, context, sampling and harness. Bank: the first
5 tasks of results/e154/bank.jsonl (results/e176/bank-e154-first5.jsonl), 1,200 s per task, podman isolation.
Runs after A1's E154 leg finishes (owner: finish the easy bank as configured).

- P11: median `wall_time / turns` across the 5 records is under 30 s (A1 tasks 1-3: 52, 71, 100 s).
- P12: `passed` is true on at least 1 of 5 (A1 so far: 0 of 3 on the same tasks).
- P13: `diff` is non-empty on at least 3 of 5 (A1: empty on all 3).
- Check, not a prediction: the server log shows no reasoning content on LGN requests; if it does, the switch did not
  take and A2 is void.
