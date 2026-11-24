<!--
# File: results/e172-prereg.md
# Purpose: Pre-registration for E172 - Inkling-2-Mini on four engine/file setups plus production, the full test E170 did not give it.
# Project: sparkbench | Date: 2026-11-22
#
# Overview: E170 tested Inkling only on memory jobs, on our own Q8_0 conversion under plain llama.cpp with no drafter,
# beside live production, and five of its no-answers trace to a bank defect (14cb5f1). Two community reports put it
# near 46-100 tok/s on Strix Halo with speculative decoding (Loom 0.3; CIRU vLLM). Owner 2026-11-22: plan it for after
# the disk space is back and current testing is done; then "continue to progress elsewhere" while away from the
# terminal. STATUS: FROZEN 2026-11-23 ~00:05Z, before any E172 model call. Predictions may not change; any arm or
# procedure change from here is an amendment with its time, recorded before the affected step runs.
-->

# E172 PRE-REGISTRATION - Inkling-2-Mini, four setups, one ruler

## In plain English

Last week Inkling-2-Mini was the most accurate model at our memory-keeping jobs but six times slower than production,
and it sometimes gave no answer. We ran it on the slowest possible setup, beside production, on a test with a mistake
in it. Two other people report it running far faster on faster engines. This test runs it properly: three engines,
two files, an idle box, the test mistake fixed, our own stopwatch, and our hard coding tasks for whichever setup does
best. It also checks whether the community speed figures hold on our machine.

## Start conditions (all hold, 2026-11-23 00:00Z)

1. E171 finished and committed (a2f3571). 2. Offload finished, MANIFEST entry written (e955526), 787 GB free.
3. No other GPU experiment running or queued. Last boot 2026-11-18 11:27Z; no DeviceLost in any engine log since.
All arms are 17-23 GiB, well under F193's ~60 GiB edge, so the run proceeds with the owner away (reboot rule still
applies after any DeviceLost: stop, record, no further GPU loads).

## Arms

| Arm | File | Engine | Drafter |
|---|---|---|---|
| IQ | our `inkling-2-mini/Inkling-2-Mini-Q8_0.gguf` (E170) | llama.cpp `94f3af3d0` (2026-11-22), Vulkan, `-c 65536 -np 1` | none (as E170) |
| IM | unsloth `Mainline_Support/Inkling-2-Mini-UD-Q4_K_XL.gguf_file` (17,629,760,736 B, rev `45fd0876`) | same llama.cpp, same flags | none |
| IL | unsloth `Inkling-2-Mini-UD-Q4_K_XL.gguf` (17,629,759,456 B, sha256 `e62d463c...`) + `dspark-Inkling-2-Mini-Q8_0.gguf` (402,278,560 B, `2ec78510...`) | Loom 0.3.0 release wheel (ROCm/hrx-system, sha256 `6252bb0d...`), package `loom-fun/unsloth-Inkling-2-Mini-loom` @ `a8354e77` (its lock pins the same two GGUF sha256s) | DFlash depth 3 (package preset `chat`) |
| IC | `jcbtc/Inkling-2-Mini-CIRU-Halo-Agent-gfx1151` @ `1eb42fed` (CIRU v1.4.0; base + fitted weights ~22.7 GB) | CIRU vLLM fork `dfa00c92` + overlay/patch, vLLM 0.34.0+rocm100 wheel; both bundled binaries (`hip_moe_prefill_*.so`, patched `libhsa-runtime64.so.1`) built from the shipped source or replaced, never used prebuilt | DSpark K=7 (card default) |
| F | production Flash-Next on Halogen | as served (model-guard `local_smart`, live) | as served |

Draft amendments before freeze, against the draft's table: CIRU moved from `7c9c62b1`/v1.3.0 to `1eb42fed`/v1.4.0 (the
repo's current revision); arm IM added (same 4-bit file family on llama.cpp) so file and engine separate; llama.cpp
pinned at its latest build. **IC stop rule:** if IC is not serving within 4 hours of setup work, or needs any binary we
cannot build from source, IC is reported NOT RUN with the reason; the other arms are scored without it.

## Workloads

1. **Speed:** `tools/e163_speed.py` (E139 prompts, thinking off, temperature 0) on every Inkling arm, idle box
   (relay window `idle-down`). F's speed is not re-measured (E163/E171 figures stand; it is live production).
2. **Memory jobs:** `tools/run_e170.py --bank spikes/memory-tasks/bank_e170b.json` (E170b: E170's 50 tasks unchanged,
   every key's meaning now stated; sha256 `0ba83e4111fe6983a4d765fdb08668ceed3be41ef5d1b8cb774f651b9fce8a00`), every arm,
   temperature 0, `max_tokens` 16,384, each engine's default thinking, same grader. Output `results/e172/memory/`.
   Inkling arms on the idle box; F against live production as in E170.
3. **Coding:** the E167 visible-tests bank (sha256 prefix `925b63296a2fd720`, 3,600 s per task, E167 runner settings)
   for ONE Inkling arm, chosen by: most E170b updates exactly right, then extract F1, then lowest median s/task.

## Scored fields

- `<arm>.speed.<P8K|P32K|D1500>.<prefill_tps|decode_tps>`: `results/e172/raw/<arm>/speed.json` `summary`.
- `<arm>.e170b.extract_f1`, `.update_exact`, `.median_s_task`: `results/e172/memory/score.json` (`extract.f1`,
  `update.exact`, `wall_s_median`).
- `<arm>.e170b.update_no_answer`: count of U tasks whose `finish_reason` is `length` or whose output parses to no JSON.
- `best.e167.pass_count`: passes of the chosen arm on the E167 bank (`results/e172/raw/<arm>/<task>.json`).

## Predictions (each names its field)

1. **P1 Loom's prefill figure does not hold here.** `IL.speed.P8K.prefill_tps` < 1,580 (package card, 8K).
2. **P2 CIRU's prefill figure does not hold here.** `IC.speed.P8K.prefill_tps` < 2,141 (CIRU README, client, ~8K).
3. **P3 Loom's decode figure does not hold here.** `IL.speed.D1500.decode_tps` < 46.0 (package card, short prompt).
4. **P4 CIRU's decode figure does not hold here.** `IC.speed.D1500.decode_tps` < 93.1 (CIRU README, short, T=0).
5. **P5 the engine explains most of E170's slowdown.** min(`IL.e170b.median_s_task`, `IC.e170b.median_s_task`) <=
   `IQ.e170b.median_s_task` / 3.
6. **P6 fixing the bank cuts the no-answers.** `IQ.e170b.update_no_answer` < 5 (E170: 5).
7. **P7 accuracy holds on every setup.** `<arm>.e170b.extract_f1` >= 0.95 for every arm that runs.
8. **P8 production stays faster at memory jobs.** `F.e170b.median_s_task` < the lowest Inkling `median_s_task`.
9. **P9 Inkling does not beat production at hard coding.** `best.e167.pass_count` <= 5 (H, E167).

## Limits known now

- CIRU's runtime pins its own ROCm 10 Python SDK: a separate runtime identity on this box, set up and removed as
  `docs/TOOLCHAIN.md` requires. Its prebuilt binaries are excluded by rule, so a slower IC than CIRU measures may be
  partly that.
- The community figures are from other boxes and other clients; Loom's package was published for hrx-loom 0.2.0
  (0.3.0 states v0.2 packages run unchanged).
- F runs against live production with whatever traffic exists; its speed is not comparable to idle arms.
- One sample per memory task at temperature 0; ten coding tasks, one sample: a 1-2 task difference is not evidence.

## Amendments


- **A1 (2026-11-23 00:07Z, before any IL call):** Loom 0.3.0 rejects the package README's `--parameter_mode=preload`
  ("expected 'file' or 'direct'"); IL's first start failed to register, no request was served. The README states
  preload only changes host-side loading and that its performance rows were measured without it. IL is re-run with the
  flag omitted (engine default), all other README flags kept.
- **A2 (2026-11-23 05:40Z, before the IM re-run):** the first IM start (01:18:00Z, one second after IL's Loom engine
  exited) got -ENOMEM mapping GPU memory and its teardown panicked the kernel (F198); IM served no request and has no
  results. `tools/run_e154_arms.sh` now waits before each local engine start until GTT is within 2 GiB of the
  window-open baseline (+10 s), refusing the arm after 180 s. IM is re-run alone with the same build, file and flags.
  IL and IQ results stand (both banked before the crash; IL `c31fd6b`). No prediction changes.
- **A3 (2026-11-23 13:56Z, before any IC call):** how IC is set up and served.
  1. **Runtime source:** CIRU's INSTALL uses `pip install --extra-index-url https://wheels.vllm.ai/rocm/0.34.0/rocm100/`,
     which the standing settings deny rule blocks. Owner choice 2026-11-23: install from pinned files instead. 17 files
     (vLLM index + AMD `stable.repo.amd.com`), sha256 computed on arrival (`results/e172/ciru-wheels.SHA256SUMS`), installed
     `--no-deps`; every other dependency from PyPI alone, constrained to the local versions; `pip check` clean. Only gfx1151
     device packages (vLLM's metadata names nine GPU families). CIRU's own `install.sh` then passed its bundle, wheel-version
     and dependency checks and fetched its pinned vLLM fork and Transformers commits.
  2. **Bundled binaries (stop-rule clause):** the prebuilt `hip_moe_prefill_gfx1151_80df0ef12be2.so` is removed, so CIRU's
     loader JIT-builds it from the shipped `hip_moe_prefill.hip` with ROCm 10 `hipcc` (`rocm-sdk-devel` 10.0.0, pinned file).
     The prebuilt patched `libhsa-runtime64.so.1` is removed and replaced by the stock ROCm 10 SDK ROCr (the launcher's
     not-affected path); the patch throttles a CPU busy-poll in ROCr's interrupt-less fallback, so IC may use more host CPU
     than CIRU measured.
  3. **Serving config:** `serve.sh --mode single --context 65536 --seqs 1 --tools` (one stream, DSpark K=7 - the card's
     B=1 default), matching IQ/IM's `-c 65536 -np 1`. The card's default `vision` mode (8 sequences, 1M context, 52 GiB KV)
     would put the load past F193's ~60 GiB edge; single-stream is also what P2/P4's figures (client, T=0, B=1) describe.
  4. Speed and E170b exactly as the other arms (`E172_MEMORY=1`); thinking off via `chat_template_kwargs`. The 4-hour stop
     rule counts from 13:10Z today; not serving by 17:10Z = IC NOT RUN with the reason. No prediction changes.
- **A3 note (2026-11-23 13:58Z, IC has served no request):** the first IC start (13:57:37Z) died in 6 s at `import torch`:
  ROCm 10's `libamdhip64.so.7` bound the system ROCm 7.2.4 `libhsa-runtime64.so.1` (undefined symbol
  `hsa_amd_vmem_export_fabric_handle`). The original launcher always preloads a ROCr because the SDK's stock library is
  exactly the build its fix targets (sha256 `815364af...`); the replacement launcher now preloads the STOCK SDK ROCr the same
  way (`LD_PRELOAD` + `LD_LIBRARY_PATH`, mapping verified) instead of doing nothing. `import torch` verified before relaunch.
- **A3 note 2 (2026-11-23 14:02Z, before IC's speed re-run):** IC's first speed request (14:01Z) streamed no answer: CIRU's
  Inkling template has no `enable_thinking` switch (its thinking control is `reasoning_effort`, default 0.9), so
  `chat_template_kwargs.enable_thinking=false` was ignored and 254 of 256 tokens went to reasoning. `tools/e163_speed.py`
  gains `--thinking-off effort0` (`chat_template_kwargs.reasoning_effort=0`, the template's own "Thinking effort level: 0"),
  used for IC only. The memory bank is unaffected (each engine's default thinking, as declared). IC speed re-runs alone
  after its memory bank, same engine and flags.
- **A3 note 3 (2026-11-23 14:16Z, before IC's second speed re-run):** the 14:16Z re-run failed identically (254/256 reasoning
  tokens): vLLM merges the request's own `reasoning_effort` (None when unset) over `chat_template_kwargs`, so the kwargs value
  never reached the template. `--thinking-off effort0` now sends the top-level field `reasoning_effort: "none"`, which the
  template maps to 0.0. No other change.
- **A3 note 4 (2026-11-23 14:19Z, before IC's third speed re-run) - notes 2 and 3 misdiagnosed the failure; corrected here.**
  Thinking was never off on ANY Inkling arm: IQ, IM and IL's speed records show content empty, `reasoning_chars` ~1,060-1,120
  and all 256 completion tokens as reasoning (the Inkling templates ignore `enable_thinking`). Their speed figures are
  decode over reasoning tokens - consistent across arms, but "thinking off" as written in Workload 1 did not happen; this is
  reported as a deviation with the results. IC failed only because vLLM 0.34 streams reasoning as `delta.reasoning`, which
  `tools/e163_speed.py` did not read (it read `content` and `reasoning_content`). Fix: the tool also reads
  `delta.reasoning`; IC is sent exactly the same request as IQ/IM (`--thinking-off kwargs`), so all four arms are measured
  the same way. The `effort0` option stays in the tool, unused.
- **A4 (2026-11-23 15:22Z, before any redo call; owner-agreed):** Workload 1 is re-run with thinking VERIFIABLY off, on all four
  Inkling arms (IQ, IM, IL, IC), same prompts, same engines and flags, `E172_SPEEDREDO=1` -> `results/e172/raw/<arm>/speed-off.json`
  (the thinking-on `speed.json` files are kept and reported alongside). `tools/e163_speed.py --thinking-off auto-off` probes, in
  order: top-level `reasoning_effort: "none"`; `chat_template_kwargs.reasoning_effort: "none"`; `chat_template_kwargs.enable_thinking:
  false`; top-level `enable_thinking: false` - on one short request, and keeps the first that streams answer text with zero
  reasoning. If none does, that arm is reported "thinking cannot be disabled on this engine" and is not measured as
  thinking-off. Every request's `reasoning_chars` is recorded; any nonzero count is reported. **Scoring change:** P3
  (`IL.speed.D1500.decode_tps` < 46.0) and P4 (`IC.speed.D1500.decode_tps` < 93.1) are scored on `speed-off.json`; P1 and P2
  (prefill) are scored on both files and reported if they disagree. Memory (E170b) and coding are unaffected (default thinking
  by design).
- **A5 (2026-11-23 15:24Z, before any minimum-thinking call):** the A4 pass found that **no switch turns Inkling-2-Mini's thinking
  fully off** on llama.cpp (IQ: reasoning_chars 256 with `reasoning_effort: "none"` either way, 445 with `enable_thinking` in
  kwargs, 540 top-level; IM: same pattern, 528 at default) - the model still writes a short reasoning block (~60 tokens) at
  effort "none", then answers. That is reported as a finding: "thinking cannot be fully disabled on Inkling-2-Mini; minimum
  is ~60 tokens". Workload 1 is therefore re-run at **minimum thinking**: `--thinking-off min-thinking` probes the same four
  switches and uses the one that leaves the least reasoning before a real answer; every request's reasoning share is
  recorded. Output still `speed-off.json` (the A4 pass wrote none). P3 and P4 are scored on these minimum-thinking files,
  with the remaining reasoning share stated beside each figure; thinking-on figures reported alongside. Launched as a new
  runner invocation after the A4 pass exits (the runner script was edited while the A4 pass ran; bash had already parsed
  its arm loop, and relay restore is in the EXIT trap).
