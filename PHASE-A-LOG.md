# Phase A execution log

<!--
File: PHASE-A-LOG.md
Purpose: Dated evidence record for every Phase A gate and benchmark run on sparkmax.
Project: sparkbench | Date: 2026-07-03
#
# Overview: Append-only run log. Each entry records the step, command,
# environment (build hash, backend, kernel), raw numbers, and verdict.
# Referenced by WORKPLAN.md Section 5; promotion evidence lives in runtime
# specs, this file is the bring-up trail.
-->

## 2026-07-03 - Step 1 verification (partial FAIL, awaiting re-run)

- Packages installed: mesa-vulkan-drivers 25.2.8, vulkan-tools 1.3.275,
  libvulkan-dev 1.3.275, glslc 2023.8, cmake 3.28.3, git 2.43.
- MISSING at first verification: build-essential (g++ absent),
  /opt/models/{staging,production}, models group membership (group exists,
  no members), render group membership for agent-spark.
- Kernel cmdline verified: `ttm.pages_limit=27648000 ttm.page_pool_size=27648000`
  (in-tree names, correct). Disk: 1.8TB free.

## 2026-07-03 - Step 2 driver gate (BLOCKED, diagnosed)

- `vulkaninfo --summary` shows only llvmpipe (CPU rasterizer), not Radeon
  8060S/RADV. Root cause: /dev/dri/renderD128 is root:render 660 and
  agent-spark is not in `render` group. amdgpu module loaded; radeon_icd.json
  (RADV) present. Fix: `usermod -aG render agent-spark` + fresh login.
- NOT a driver fault - do not reinstall Mesa over this.
- RESOLVED same day: `usermod -aG models,render agent-spark spark-infer` run by
  Alastair. Via `sg render`: **GPU0 = Radeon 8060S Graphics (RADV GFX1151)**,
  driverName radv, Mesa 25.2.8. Memory heaps 35.82 + 71.65 = 107.5 GiB =
  105.5 GiB TTM GTT + 2 GiB BIOS UMA (Mesa 1/3 host-visible / 2/3
  device-local split). Budget confirmed - at the 62GB TTM default the heaps
  would total ~61 GiB. **Step 2 verdict: PASS.**
- Session note: current shell predates the usermod, so all GPU work runs via
  `sg render -c ...` and staging writes via `sg models -c ...` until a fresh
  login makes the groups ambient.

## 2026-07-03 - Step 2b CPU memory bandwidth (PASS)

- Tool: `tools/membw.c` (STREAM-style, OpenMP, 3x1.6GB arrays, best of 10),
  compiled `gcc -O3 -march=native -fopenmp`, 32 threads. mbw equivalent per
  WORKPLAN step 2b.
- **read 118.7 GB/s, copy 110.4 GB/s, triad 107.4 GB/s.**
- Verdict: PASS. Within the documented healthy band (~110-120 GB/s CPU-side;
  Infinity Fabric-limited). Confirms dual-channel LPDDR5x negotiated full
  speed. GPU-side ~220 GB/s to be validated by step 5 reference benchmark.

## 2026-07-03 - Step 3 llama.cpp source pinned (build pending g++)

- Clone: https://github.com/ggml-org/llama.cpp.git (depth 200)
- **Pinned commit: 067de937183141f54c681ed684f540706d2c420a** (2026-07-03,
  "ui: align persisted config with strict server schema...").
- Build blocked on build-essential; Vulkan build flags per plan:
  `-DGGML_VULKAN=ON`.

## 2026-07-03 - Step 3 build complete (PASS)

- build-essential installed by Alastair; also spirv-headers, spirv-tools,
  glslang-tools, glslang-dev (ggml-vulkan requires SPIRV-Headers cmake
  package at this commit). A briefly-vendored project-local SPIRV-Headers
  copy (`deps/`) was superseded by the system package and is dead - remove.
- Configure: `cmake --fresh -B build -DGGML_VULKAN=ON -DLLAMA_CURL=OFF
  -DCMAKE_BUILD_TYPE=Release`, system spirv-headers 1.6.1+1.4.309.0.
- **DECLARED DEVIATION - LLAMA_CURL=OFF:** (a) libcurl4-openssl-dev absent
  on this host at build time (verified via dpkg; only runtime libcurl4t64 +
  curl binary present), so ON could not configure; (b) kept OFF by choice:
  the `-hf` fetch path caches outside /opt/models/staging and records no
  URL/revision/SHA256, structurally bypassing Section 4.6 manifest
  discipline. All model downloads use explicit curl + HF API revision query
  + sha256sum on arrival. Flag is part of the recorded build flags; revisit
  consciously if a runtime spec ever needs it ON.
- Build: `cmake --build build -j 30 --target llama-cli llama-server
  llama-bench` - all three linked.
- Acceptance: `llama-cli --list-devices` (via sg render) shows
  **Vulkan0: Radeon 8060S Graphics (RADV GFX1151), 110048 MiB** (matches
  heap total). **Step 3 verdict: PASS.**

## 2026-07-03 - Step 4a model staged

- Qwen3-0.6B-Q8_0.gguf (639,446,688 bytes) downloaded to
  /opt/models/staging via explicit curl; manifest entry in
  `manifests/MANIFEST.md`. Smoke run result to follow.

## 2026-07-03 - Step 4a tiny smoke test (PASS)

- Run: `llama-cli -m Qwen3-0.6B-Q8_0.gguf -ngl 99 -n 48 -st -p ...` via
  sg render, timeout-guarded. Generated coherent text (Qwen3 thinking mode
  visible through embedded chat template).
- Throughput: prompt 1173.4 t/s, generation 253.5 t/s - GPU-class for
  0.64GB Q8 (bandwidth arithmetic ceiling ~344 t/s; CPU would be ~5x slower).
- Offload evidence (verbose log): `using device Vulkan0 (Radeon 8060S
  Graphics (RADV GFX1151)) - 109882 MiB free`; **58/58 layer assignments to
  Vulkan0, 0 to CPU**; Vulkan0 model buffer 604.15 MiB. The 157.65 MiB
  CPU_Mapped buffer is the host-mapped token-embedding table - expected,
  not fallback. **Step 4a verdict: PASS.**
- FINDING (Phase B relevant): at commit 067de937 llama-cli is a chat-first
  TUI - `--no-conversation` prints "not supported... use llama-completion
  instead" and an EOF'd stdin loops forever on the chat prompt (first run
  hung exactly this way; killed). Scripted/harness runs must use
  llama-server (or llama-completion) + HTTP, never llama-cli. Single-turn
  `-st -p` works for manual smoke checks; always wrap in `timeout`.
- Chat-UI stdout suppresses classic load logs and stderr is empty by
  default; offload evidence requires `-v`. sparkbench harness should
  capture verbose logs for its "no CPU fallback" gate.
- Findings promoted to hard rules in docs/HARNESS-RULES.md (Rules 1-3).

## 2026-07-03 - Step 4b mid-size smoke test (PASS)

- Model: Qwen3-14B-Q4_K_M.gguf (9,001,752,960 bytes, revision 530227a7,
  manifest entry recorded). Download took ~4 min (~35MB/s on Wi-Fi -
  faster than assumed).
- Server: `llama-server -m ... -ngl 99 --host 127.0.0.1 --port 8100
  --jinja -v`, ephemeral high port per two-plane architecture (4.5).
- /v1/models healthy on first poll (~2s after model load completed).
- Chat completion via tools/chat_smoke.py (urllib probe, temperature 0):
  correct answer ("Paris"), Qwen3 thinking mode active through --jinja
  template (reasoning_content populated), 136 completion tokens in 5.70s
  wall (~24 t/s incl. prompt phase - matches 220/9GB bandwidth ceiling).
- Offload evidence: `using device Vulkan0 ... 109882 MiB free`; **82/82
  layer assignments to Vulkan0, 0 to CPU**; CPU_Mapped 417.30 MiB =
  host-mapped embeddings (expected). **Step 4b verdict: PASS.**
- Server stopped cleanly after test (exit 0).

## 2026-07-03 - Step 4c reference-model download started

- ggml-org/gpt-oss-120b-GGUF, revision d932fcea62f83e088d8f076a2cd2d7eb02dfa682,
  3 shards (gpt-oss-120b-mxfp4-0000{1,2,3}-of-00003.gguf), explicit curl
  with resume (-C -) into staging; SHA256 on completion.
- **Divergence note (Section 3 like-for-like discipline):** community
  reference table says "Q8"; the artefact everyone actually benches is
  this ggml-org GGUF whose MoE weights are native MXFP4 (ftype reports
  MXFP4 MoE; non-expert tensors Q8_0). Same artefact family as the
  reference numbers; label recorded here so the comparison is fair.
- Sequencing amendment approved by Alastair: overlap big download with 4b
  (in the event, 4b passed before the download began, so plan order was
  preserved anyway).

## 2026-07-03 - Step 4c reference model staged (COMPLETE)

- Download history: first attempt (plain curl loop) died on a Wi-Fi drop
  mid-shard-2; second attempt failed instantly (bashism under sg's
  /bin/sh=dash - exit-in-seconds is the "never ran" tell). Final:
  tools/fetch_gpt_oss_120b.sh - resumable, size-verified against HF API
  byte counts, bounded retries. Shard 1 (12.4MB) is metadata-only and was
  complete all along; ~60MB/s sustained on resume.
- All 3 shards COMPLETE, sizes exact, SHA256s recorded in
  manifests/MANIFEST.md. Total 63.4GB staged.
- Lesson recorded in HARNESS-RULES.md spirit: completion = byte-count
  match against authority, never "curl exited 0".

## 2026-07-03 - Step 5 reference benchmark (gate run - AWAITING HUMAN VERDICT)

- Exact spec (Section 3 reference-run discipline):
  - Model: gpt-oss-120b-mxfp4 shards, revision d932fcea (manifest entry;
    ftype reported "MXFP4 MoE", 59.02 GiB, 116.83B params)
  - Build: llama.cpp 067de937 (b200), `-DGGML_VULKAN=ON -DLLAMA_CURL=OFF
    -DCMAKE_BUILD_TYPE=Release`, gcc 13.3.0
  - Backend: Vulkan RADV, Mesa 25.2.8, kernel 6.17.0-35-generic HWE,
    TTM 105GB (dmesg-verified)
  - Command: `llama-bench -m <shard1> -o md` (all defaults: pp512, tg128,
    5 reps, ngl -1 = full offload)
  - Divergence from community config: newer llama.cpp build than the
    reference run (theirs unrecorded/older); same hardware, same backend
    class, same artefact family.
- Results vs Section 3 reference (GMKtec EVO-X2):
  - pp512: **545.65 ± 10.01** vs 517.61 ± 8.01 -> **+5.4%**
  - tg128: **53.44 ± 0.38** vs 45.54 ± 0.02 -> **+17.3%**
- Sanity arithmetic: ~2.6GB effective active bytes/token -> ceiling
  ~84 t/s; 53.4 observed is 64% of ceiling - plausible, not
  broken-measurement territory. Excess over reference consistent with
  months of Vulkan MoE improvements since the community run.
- Long-context probe (`llama-bench -d 8192`, same spec otherwise):
  - pp512 @ d8192: **423.71 ± 5.93** (-22.3% vs d0)
  - tg128 @ d8192: **48.35 ± 0.45** (-9.5% vs d0)
  - Smooth degradation, no cliff; tg at 8K depth still exceeds the
    community d0 reference (45.54). ROCm's claimed ~3x prefill advantage
    at 130K+ (WORKPLAN 4.2) remains untested - only relevant if a
    long-context workload materialises.
- Raw outputs: llama.cpp/bench-step5-gate.md, bench-step5-longctx.md.
- **Verdict: PENDING (human gate - Alastair).** Resolved same day - see the
  step 5 verdict entry below.

## 2026-07-03 - Step 5 reference gate verdict (PASS - Alastair)

- **Verdict: PASS.** Rationale recorded with the tick: the gate's purpose
  was never "match the reference exactly" - it exists to detect a broken
  stack (CPU fallback, partial offload, misconfigured memory) before the
  matrix runs. The evidence rules all of those out: 58/58 and 82/82 layer
  assignments to Vulkan0 in the smoke tests, Vulkan heap totals matching
  the TTM budget to the gigabyte, bandwidth sanity arithmetic passing
  (53.4 t/s observed = 64% of the ~84 t/s ceiling implied by ~2.6GB
  effective active bytes), and both directions of the reference comparison
  explained (same ggml-org artefact family; newer llama.cpp build carrying
  months of Vulkan MoE kernel improvements). The surplus is attributed,
  not mysterious.
- Wrinkle noted in the verdict: +17.3% tg128 is technically
  outside the "~10%" band, which was written imagining only
  underperformance. WORKPLAN step 5 amended same day to asymmetric
  tolerance (below band = stack problem, stop; above band = attribute the
  surplus before proceeding) - codifying the behaviour this gate run
  already exhibited.
- **House reference baseline established:** pp512 545.65 ± 10.01 / tg128
  53.44 ± 0.38 (d0) and 423.71 ± 5.93 / 48.35 ± 0.45 (d8192), at llama.cpp
  067de937, Vulkan RADV, Mesa 25.2.8, kernel 6.17.0-35-generic, TTM 105GB.
  This is now the regression baseline for every future kernel, Mesa, or
  llama.cpp bump on this machine. The community table did its one job
  (validating the stack) and retires to a footnote in WORKPLAN Section 3.
- **LLAMA_CURL=OFF endorsed as a standing decision, not a workaround:**
  the manifest-discipline rationale (the `-hf` fetch path caches outside
  staging with no URL/revision/SHA256) stands on its own, so the flag
  stays OFF even now that installing libcurl4-openssl-dev would be
  trivial. Binding rule: HARNESS-RULES.md Rule 4. Revisit only via a
  conscious runtime-spec decision.
- **Step 4c download lesson promoted fleet-wide:** "completion = byte-count
  match against the source-of-truth API, never 'curl exited 0'" now lives
  in ~/workstation-dotfiles/.claude/rules/download-integrity.md (tidybot
  and ragbuilder fetch things too); HARNESS-RULES.md remains the
  sparkbench-local binding.

## 2026-07-03 - Housekeeping: dead vendored deps/ removed

- The briefly-vendored SPIRV-Headers copy (`deps/`, flagged dead in the
  step 3 build entry) is removed - closes step 3's pending item.
- Pre-deletion check: system spirv-headers package confirmed installed
  (dpkg status "install ok installed", /usr/include/spirv present). The
  recorded `--fresh` configure resolved against the system package, and
  SPIRV-Headers is build-time only - neither the shipped binaries nor a
  future rebuild reference the vendored copy.

## 2026-07-03 - Step 6 matrix opened: Qwen mid-MoE workhorse (download + pin)

- Matrix order (Alastair, 2026-07-03): Qwen mid-MoE workhorse FIRST
  (production-relevant instant-tier candidate - ~70 t/s clears the
  business case), GLM-4.5-Air second (thinking and non-thinking modes as
  separate entries), 235B stress probe + pressure test parked for an
  attended, physically-present session per 4.3.
- Candidate pinned at execution per 4.4:
  unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF, Q4_K_M, revision eea7b2be,
  18,556,686,752 bytes. Selection rationale in manifests/MANIFEST.md (no
  official Qwen GGUF of the 2507 refresh exists; unsloth is the
  high-trust community-standard artefact, 511k downloads). This repo
  publishes upstream LFS SHA256 - arrival hash will be compared to it.
- Fetch: tools/fetch_hf_model.sh (generalised from fetch_gpt_oss_120b.sh;
  third scripted fetch earned the abstraction), size-verified per the
  download-integrity rule.
- Artefact verified on arrival: size exact match against HF API
  (18,556,686,752 bytes) AND local sha256sum byte-identical to the
  upstream LFS oid - first artefact in the store with a full
  origin-to-disk checksum chain (gpt-oss's xet-backed repo published
  none).
- **DECLARED DEVIATION - sg wrapping retained for this one leg:**
  Alastair's sequencing put a fresh agent-spark login before step 6
  (retiring `sg render -c`). This session's process predates the fresh
  login and cannot re-PAM itself: `id` shows no ambient render/models
  membership while `getent group` confirms both memberships exist. Rather
  than park the afternoon, this first matrix leg runs via sg render
  exactly as steps 2-5 did (same session-note pattern as the step 2
  entry). The sg wrapper is a session artefact, NOT part of the recorded
  spec - canonical commands are logged unwrapped. The next session must
  start from a fresh login so the wrapper retires before further matrix
  legs and all Phase B work.

## 2026-07-03 - Step 6 matrix: Qwen mid-MoE workhorse (PASS - business case cleared)

- Exact spec (Section 3 discipline): Qwen3-30B-A3B-Instruct-2507-Q4_K_M
  (unsloth, revision eea7b2be, manifest entry, SHA256 verified against
  upstream oid), llama.cpp 067de937 Vulkan build, Mesa 25.2.8, kernel
  6.17.0-35, TTM 105GB. Canonical commands: `llama-bench -m <gguf> -o md`
  and `llama-bench -m <gguf> -d 8192 -o md` (all other defaults; executed
  via sg render per the declared session deviation above).
- Results (llama-bench reports 17.28 GiB file, 30.53B params):
  - pp512: **1137.67 ± 11.04** | tg128: **92.83 ± 0.46**
  - pp512 @ d8192: **561.10 ± 6.78** | tg128 @ d8192: **66.97 ± 0.53**
- **Business case: 92.8 t/s clears the ~70 t/s instant-tier line by +33%,
  and still holds ~67 t/s at 8K depth.**
- Surplus attribution (asymmetric-tolerance discipline, first
  application): naive ceiling = ~2.0GB active bytes (A3B at ~0.61
  bytes/param) -> ~110 t/s; observed 92.8 = 84% of ceiling - high but
  below ceiling, so not broken-measurement. The 2x over Section 3's ~45
  t/s field figure is a CROSS-BACKEND comparison (that figure was ROCm;
  Vulkan is field-verified faster on this silicon per 4.2) plus the same
  kernel-vintage delta the step 5 verdict accepted. Like-for-like anchor
  is the ceiling arithmetic, not the ROCm number.
- tg degradation at depth (-28%) is steeper than gpt-oss-120b's (-9.5%):
  expected physics - the smaller the active set, the larger the KV-read
  fraction per token at depth. Smooth, no cliff.
- Raw outputs: llama.cpp/bench-step6-qwen3-30b-a3b-2507.md,
  bench-step6-qwen3-30b-a3b-2507-longctx.md.

## 2026-07-03 - Step 6 matrix: small fast baseline Qwen3-14B (recorded)

- Same build/backend spec; model from step 4b (manifest entry, Qwen3-14B
  Q4_K_M dense, 8.38 GiB). Canonical command:
  `llama-bench -m <gguf> -d 0,8192 -o md`.
- Results:
  - pp512: **633.72 ± 1.39** | tg128: **24.39 ± 0.04**
  - pp512 @ d8192: **282.30 ± 7.35** | tg128 @ d8192: **21.23 ± 0.01**
- Sanity: 24.39 t/s is the 220/9.0GB naive ceiling almost exactly, and
  matches step 4b's ~24 t/s server-side observation - two measurement
  paths agreeing.
- **Matrix insight, MoE-first thesis now empirical on this silicon:** the
  30B-A3B MoE generates 3.8x faster than the dense 14B while being the
  stronger model. Dense-at-interactive-speed remains physics-limited,
  exactly as 4.4 predicted. Whether 24 t/s still clears any instant-tier
  workload is a Phase B question (the "operational minimum" row exists
  for retry/fallback behaviour, not speed records).
- Raw output: llama.cpp/bench-step6-qwen3-14b.md.

## 2026-07-03 - Step 6 matrix: GLM-4.5-Air pinned, download running

- Pinned per 4.4 execution-time versioning: unsloth/GLM-4.5-Air-GGUF
  Q4_K_M, revision 506d64aa, 2 shards, 73.0GB total, upstream LFS SHA256s
  recorded (manifest entry with selection rationale and quant-choice
  note). Download via tools/fetch_hf_model.sh (now handles repo
  subfolder paths, flattening to staging root); resumable if interrupted
  by session restart.
- Execution-time landscape check: no Air-class successor exists
  (GLM-4.6/4.7 are 355B-class). **Observation for Alastair:**
  GLM-4.7-Flash (2026-01, MIT, 31B-class MoE, ggml-org GGUF available -
  it is llama-bench's own help-text example at our pinned commit) is a
  direct rival for the QWEN WORKHORSE row, not for Air. Decision whether
  it earns a matrix row is his; not staged.
- Bench deferred to the next (fresh-login) session so the sg wrapper
  retires first. Thinking/non-thinking modes are an eval-time split;
  llama-bench produces one throughput row per artefact.

## 2026-07-03 - Step 6 matrix: GLM-4.5-Air quality-leaning middle (recorded - not instant-tier on this silicon)

- Exact spec (Section 3 discipline): GLM-4.5-Air Q4_K_M (unsloth,
  revision 506d64aa, 2 shards staged flat; resumed download arrived
  byte-exact vs HF API pins, local SHA256s match upstream LFS oids,
  manifest flipped PENDING -> VERIFIED), llama.cpp 067de937 Vulkan
  build, Mesa 25.2.8, kernel 6.17.0-35, TTM 105GB. First bench of the
  fresh-login era: `id -nG` shows ambient render/models, sg wrapper
  retired per the 2026-07-03 decision - commands below ran unwrapped.
- Canonical commands: `llama-bench -m <shard1> -o md` and
  `llama-bench -m <shard1> -d 8192 -o md` (all other defaults).
  **Declared deviation from the handoff's single combined command:**
  the combined `-d 0,8192` invocation ABORTS on this artefact
  (radv/amdgpu "Not enough memory for command submission" ->
  vk::DeviceLostError, SIGABRT during decode; no rows emitted). Split
  invocations - the same form the gpt-oss and Qwen legs already used -
  pass. See memory-edge finding below.
- Results (llama-bench reports 67.96 GiB file, 110.47B params, glm4moe
  106B.A12B, full offload):
  - pp512: **232.38 ± 8.14** | tg128: **23.90 ± 0.09**
  - pp512 @ d8192: **55.24 ± 11.68** | tg128 @ d8192: **20.74 ± 0.13**
- Ceiling arithmetic (asymmetric-tolerance): active bytes ~7.9GB (A12B
  at the artefact's ~0.66 bytes/param) -> naive ceiling ~28 t/s;
  observed 23.9 = 86% of ceiling. Below ceiling - no surplus to
  attribute.
- **Business case: FAILS the ~70 t/s instant-tier line (23.9 t/s) -
  ties the dense 14B baseline (24.39) despite 110B params.** The
  quality-leaning-middle row is quality-tier only on this box; whether
  its output quality earns that slot is a Phase B eval question, not a
  throughput one.
- tg degradation at depth (-13.2%) sits between gpt-oss-120b (-9.5%)
  and Qwen A3B (-28%), consistent with the active-set/KV-fraction
  physics. Smooth, no cliff.
- **FINDING - memory-edge behaviour at ~68GiB weights:** the 71.65 GiB
  device-local heap (Mesa 2/3 split of 105.5 GiB GTT, step 2 entry)
  leaves ~3.7 GiB headroom over the weights. Two symptoms: (1) the
  combined-invocation DeviceLost abort above; (2) pp512 @ d8192
  variance ±11.68 = 21% CV vs the matrix-typical ~1-2% - treat 55.24
  as memory-pressured, not a clean measurement. Operational rule for
  this box: models >~60GiB bench via separate d0 / d8192 invocations.
  Kernel-side mechanism unconfirmed (dmesg needs sudo; noted, not
  pursued).
- Raw outputs: llama.cpp/bench-step6-glm45air.md,
  bench-step6-glm45air-longctx.md.
- Matrix status: unattended portion COMPLETE (reference + workhorse +
  small baseline + GLM). 235B stress probe and pressure test stay
  parked until Alastair is physically present, per 4.3.

## 2026-07-08 - F6 follow-up: baseline re-run does NOT reproduce (unplanned finding)

- Context: docs/plans/2026-07-08-vulkan-memory-ceiling-investigation.md Task
  2 Step 1 - re-running F6's exact combined invocation
  (`llama-bench -m <GLM-4.5-Air shard1> -d 0,8192 -o md`) as a baseline
  before testing `-ub 128`. Artefact SHA256-reverified against manifest
  first (match: 3e7e5d25a6...). Same build (067de937, confirmed via
  `git log -1`), same kernel/session (uptime 5d4h - this is the SAME boot
  as the original step 6 run, not a fresh one).
- **Result: PASS, all four rows, no DeviceLost.** pp512 @ d8192: 67.91 ±
  0.89 (1.3% CV) - nothing like the original 55.24 ± 11.68 (21% CV).
  tg128 @ d8192: 20.63 ± 0.02. Full: llama.cpp/bench-t2-glm45air-ub512-baseline.md.
- System was near-idle at run time (2.4GiB used / 121GiB free). The
  original F6 run's own log entry (step 6, "GLM-4.5-Air pinned, download
  running") shows the benchmark ran in the session immediately following
  a 73GB download + SHA256 verification of the same artefact - heavy
  sustained disk I/O right before the bench. Per the project's own
  canonical-bench caveat (CLAUDE.md: "heavy disk hashing may not [overlap
  benches safely]"), this is the leading candidate explanation for F6's
  DeviceLost + 21% CV, NOT a true ~68GiB memory-ceiling effect.
- **Status: OPEN - not resolved to the unit.** A plausible mechanism is
  named but not proven; the direct reproduction (bench during simulated
  disk-hashing load) has not been run. F6 should not be treated as
  confirmed disk-I/O confound until that direct test is done. Flagging
  per the "no hand-waved discrepancies" discipline - this is a discrepancy
  between two runs of the identical command, not yet fully explained.
- **Consequence for the memory-ceiling investigation:** if this baseline
  doesn't reproduce the crash, the planned `-ub 128` step (Task 2 Step 2)
  has nothing to isolate right now - paused pending Alastair's input.

## 2026-07-08 - F6 follow-up: disk-I/O control test produces a WORSE failure mode (unkillable hang, not a crash)

- Test: re-ran the same combined invocation
  (`llama-bench -m <GLM-4.5-Air shard1> -d 0,8192 -o md`) with a background
  `timeout 600 sha256sum` of two cold Llama-4-Scout shards (62GB, not
  touched this session - chosen to avoid page-cache overlap with the GLM
  shard) running concurrently, simulating the disk/CPU load from the
  original run's just-finished download-verify.
- **Result: the llama-bench process (PID 444301) hung in uninterruptible
  D-state** rather than reproducing F6's clean DeviceLost/SIGABRT. `timeout
  600` on the outer shell elapsed (exit 143) without the child terminating -
  D-state processes do not respond to SIGTERM/SIGKILL until whatever
  kernel-level wait they're blocked on resolves. Re-checked at +10min and
  +44min: identical PID, identical accumulated CPU time (0:19), memory/swap
  essentially unchanged (66-67GiB used, ~2GiB swap, both flat) - `vmstat`
  shows near-zero `si/so`/`bi/bo` throughout, meaning this is NOT active
  thrashing, it is a genuine stall with no forward progress.
- Cannot read `dmesg` without sudo to confirm the mechanism (almost
  certainly a GPU driver-level fence/reclaim wait, not visible at the
  process level). Alastair informed; awaiting his decision (dmesg check /
  continue waiting / plan a recovery reboot).
- **Operational finding (independent of F6's ultimate cause):** a `timeout`
  wrapper is necessary but NOT sufficient for this hardware/driver stack -
  it bounds how long a caller waits, but cannot force-terminate a
  process wedged in an uninterruptible kernel-level wait. HARNESS-RULES
  Rule 2 should be read as "converts hangs into a loud TIMEOUT signal to
  the caller," not "guarantees the underlying process dies" - worth a
  Rule 2 addendum once this incident resolves and the mechanism is known.
- **llama-gateway.service remains stopped** (paused for this test per
  operator confirmation) - not restarted while the GPU/driver state is
  unconfirmed, to avoid a second process contending with a possibly-wedged
  Vulkan context.
- **RESOLVED (mechanism confirmed) - Alastair ran `sudo dmesg` at +44min.**
  Kernel hung-task trace (full trace in session transcript, 2026-07-08)
  confirms PID 444301 blocked inside `amdgpu_cs_ioctl ->
  amdgpu_vm_bo_update -> amdgpu_vm_sdma_prepare ->
  amdgpu_job_alloc_with_ib -> amdgpu_sa_bo_new -> drm_suballoc_new ->
  schedule` since before the first hung-task warning at +1228s ("blocked
  for more than 1228 seconds"), still blocked at +44min with zero
  progress. This is the amdgpu driver's own VM-update SDMA job
  suballocator, starved - not the Vulkan heap split, not a Vulkan-level
  timeout. Promoted to docs/FINDINGS.md F24. The process cannot be
  killed (D-state); the box needs Alastair's decision on reboot timing -
  see conversation for options (plain recovery reboot vs. combining with
  the already-planned Task 4 ttm.pages_limit change, since he is now
  physically present regardless).
- Recovery: box was rebooted (reboot alone, Task 4's GRUB change deferred).
  Both gateway units came back on their own via systemd's user-service
  auto-start; confirmed post-boot at `active` with a `200 {"status":"ok"}`
  health response before any further work.

## 2026-07-08 - Task 3: ROCm single-shot load of the F6 combined invocation - PASSES, decisive

- Context: docs/plans/2026-07-08-vulkan-memory-ceiling-investigation.md
  Task 3 - does the ROCm backend see the same edge as Vulkan on the exact
  invocation that produced F6's original DeviceLost? Binary provenance
  confirmed against F22/F23 before running (llama.cpp/build-rocm/bin/
  llama-bench, ROCm 7.2.4, gfx1151 native, built 2026-07-05 - not
  rebuilt). Gateway paused (operator-confirmed window) for the run only;
  no concurrent disk I/O (F24 rule).
- Command: `llama-bench -m <GLM-4.5-Air shard1> -d 0,8192 -o md`, same
  artefact/shard/depths as the Task 2 Step 1 baseline and the original F6
  run.
- **Result: exit 0, all four rows complete, no HIP OOM/abort in stderr.**
  ROCm reports the full 114688 MiB (112GB) GTT pool as VRAM (device 0,
  gfx1151) and loads the ~68GiB artefact without incident.
  - pp512 (d0): 295.30 ± 6.26 | tg128 (d0): 21.89 ± 0.16
  - pp512 @ d8192: 182.62 ± 1.98 | tg128 @ d8192: 15.87 ± 0.51
  - Raw: llama.cpp/bench-t3-glm45air-rocm.md, copied to
    results/raw/bench-t3-glm45air-rocm.md.
- **Decisive: this is the "ROCm succeeds where Vulkan aborts" outcome.**
  Confirms the Mesa/RADV Vulkan heap split - not the underlying kernel
  GTT pool - is the actual constraint behind the original combined
  invocation's instability; ROCm addresses the same physical memory
  without hitting it. Promoted to docs/FINDINGS.md as F25.
- Gateway restarted and health-verified (`active`, `200 {"status":"ok"}`)
  immediately after the run per plan Step 3.
- **CORRECTED below (same day) - this entry's "ROCm succeeds where Vulkan
  aborts" framing was not a like-for-like comparison.** Alastair had
  raised `ttm.pages_limit` from 27648000 to 29360128 (~105.47GiB ->
  112GiB) immediately before the reboot that preceded this run (Task 4
  Steps 1-2, done during the F24 recovery reboot) - this run therefore
  used a larger pool than the original F6 crash and the same-day Task 2
  Step 1 baseline. See the "Task 4" entry immediately below for the
  full reconciliation; docs/FINDINGS.md F25 is corrected by F26.

## 2026-07-08 - Task 4: Vulkan re-run at the new 112GiB ceiling PASSES too - F25's comparison was confounded, F6 remains unreproduced

- Context: while closing out Task 3, Alastair flagged that the GRUB
  edit for Task 4 (`ttm.pages_limit` 27648000 -> 29360128) had in fact
  already been done - combined with the F24 recovery reboot, since he
  was physically present regardless (exactly the option floated in the
  F24 entry above). Confirmed from disk evidence, not assumption:
  `/etc/default/grub.bak-2026-07-08` (17:21) captures the old value,
  the live file (modified 17:22) shows the new value active, and the
  system booted at 17:40 - after the edit. `/proc/cmdline` and the live
  `/sys/module/ttm/parameters/pages_limit` both confirm 29360128 is the
  value this session has been running under, including the Task 3 ROCm
  run above. Task 4 Steps 1-2 are therefore DONE (not "blocked" as this
  session's earlier HANDOFF.md refresh incorrectly stated - corrected).
- **Step 3 (heap-split verification):** `dmesg` is sudo-restricted for
  agent-spark (`kernel.dmesg_restrict`, matches the earlier F24
  investigation), so the GTT-ready dmesg line couldn't be re-checked.
  `vulkaninfo` (no sudo needed) shows GPU0's device-local heap is now
  **76.00 GiB** (heap[1] of 2, `MEMORY_HEAP_DEVICE_LOCAL_BIT`; heap[0]
  non-device-local = 38.00 GiB; total 114.00 GiB reported vs 112GiB from
  `ttm.pages_limit` - a small, unexplained ~2GiB gap, noted not chased
  further as it doesn't bear on the decisive question). 76.00 GiB is
  close to the plan's "~74-75GiB" prediction for a heap that scales
  proportionally (~2/3) with the GTT pool, not the "~71.65GiB flat
  regardless" alternative - **confirms the device-local Vulkan heap
  does scale with `ttm.pages_limit`**, the plan's own decisive test for
  this specific sub-question.
- **Step 4 (re-run Task 2's exact baseline at the new ceiling):**
  `tools/run_step8_leg.sh t4-ttm112-glm45air llama.cpp/bench-t4-glm45air-ttm112.md
  -m <GLM-4.5-Air shard1> -d 0,8192 -o md`. Gateway paused
  (operator-confirmed), no concurrent disk I/O. **Result: exit 0, all
  four rows, no DeviceLost/abort.** Raw:
  results/raw/bench-t4-glm45air-ttm112.md.
  - pp512 (d0): 230.59 ± 8.41 | tg128 (d0): 24.24 ± 0.12
  - pp512 @ d8192: 41.28 ± 1.60 | tg128 @ d8192: 21.06 ± 0.09
  - vs. the OLD-ceiling baseline (Task 2 Step 1, same command, same
    idle-no-I/O conditions): pp512 (d0) 221.91 ± 6.53, tg128 (d0)
    23.96 ± 0.12, pp512 @ d8192 **67.91 ± 0.89**, tg128 @ d8192
    20.63 ± 0.02.
  - d0 rows and tg128 @ d8192 are consistent between the two ceilings
    (within/near error bars). **pp512 @ d8192 dropped 39% (67.91 ->
    41.28) at the LARGER pool size** - counter-intuitive (more headroom,
    worse prefill-at-depth throughput) and **UNRESOLVED**: no system-load
    snapshot was captured at the time of the original (OLD-ceiling) run
    to rule out a load-state difference, and no other cause has been
    confirmed. Flagged per the project's discrepancy discipline rather
    than attributed to a guess - candidate mechanisms (page-table/TLB
    overhead from a larger GTT pool, allocator layout change) are
    plausible but NOT verified.
  - Gateway restarted post-run; briefly `503` (model still loading, ~10s
    - consistent with the previously-documented ~18s total recovery
    timing for this model size), then `200 {"status":"ok"}`.
- **The decisive reconciliation: Vulkan did NOT crash at either ceiling
  today.** Task 2 Step 1 (old ceiling, idle) passed clean; this Task 4
  Step 4 run (new ceiling, idle) also passed clean. Neither reproduced
  F6's original DeviceLost/21%-CV failure. Combined with the disk-I/O
  control test producing a categorically different failure (F24's
  kernel deadlock, not a DeviceLost) rather than F6's crash: **F6's
  original failure mode has not been reproduced under any controlled
  condition tested in this investigation**, at either pool size, idle or
  disk-I/O-loaded. F25's claim that "ROCm succeeds where Vulkan aborts"
  is therefore not supported as a live comparison - Vulkan has not been
  observed to abort on this workload at all this session, only in the
  historical F6 report. F6's true trigger remains OPEN; the leading
  unproven candidate is still something specific to the *original* run's
  circumstances (finishing a 73GB download+verify immediately
  beforehand), not general disk I/O (which produces F24's different
  failure) and not pool size (both ceilings pass when idle). Correction
  recorded as F26; F25's status line updated to point to it.
- Commit: f448678.

## 2026-07-08 - Task 4 Step 5: decision - KEEP ttm.pages_limit at 112GiB

- Alastair's call (plan Step 5): keep the new GRUB config. No revert.
- Rationale: the plan's own revert criterion is instability under
  combined load - none was observed. Both ROCm (Task 3) and Vulkan
  (Task 4 Step 4) loaded the ~68GiB artefact cleanly at the new
  ceiling; llama-gateway restarted and health-checked fine after both
  runs. The one open item (pp512 @d8192's unresolved 39% drop, see
  Task 4 entry above) is a throughput question on a single metric, not
  a stability failure, and doesn't meet the revert bar.
- Forward-looking reason to keep: more `ttm.pages_limit` headroom
  directly enables testing larger/near-edge models - including the
  235B stress probe parked pending Alastair's physical presence (step
  6, 4.3) - which is the whole reason Task 4 existed. Reverting would
  remove exactly the capacity this investigation was raising.
- Backup remains on disk at `/etc/default/grub.bak-2026-07-08`
  (untouched) as a rollback path if instability ever surfaces later.
  No further action taken; GRUB is already live at 112GiB since the
  2026-07-08 17:40 reboot.
- **F6 follow-up investigation (docs/plans/2026-07-08-vulkan-memory-
  ceiling-investigation.md) is now closed**: Tasks 1, 3, 4 complete;
  Task 2 Steps 2-5 remain open but superseded (pool size is not the
  operative variable per F26) - worth a formal close-as-superseded
  note rather than running, next time this thread is picked up. F6's
  original trigger remains genuinely unexplained.

## 2026-07-09 - Upper-limits campaign Task 6 (Devstral 2 123B): a likely F24 recurrence halts benchmarking, session ends for a reboot

- Context: docs/plans/2026-07-09-upper-limits-reporting-plan.md Task 6
  (E23, Devstral 2 123B). Full campaign background: HANDOFF.md
  "Benchmarking + reporting phase" and docs/plans/2026-07-09-upper-
  limits-reporting-design.md.
- First-pass anomalies (via superpowers:subagent-driven-development, one
  implementer + reviewer cycle): tg128 missing at d=4096/d=8192 (present
  at d=0, and present for every other model in the batch at every
  depth), and eval-pilot judged "timed out" at ~10 minutes despite the
  script's real 1800s budget. Alastair: "properly benchmark and rework...
  redo anything where we had an issue... I would rather have everything
  double checked rather than make false claims in our reporting" -
  chose full re-verification of the whole batch, including Tasks 2/3
  which had already passed clean review.
- Re-investigation (with live process monitoring, full-timeout patience)
  found a REAL, benign root cause for the original tg128 symptom:
  `run_step8_leg.sh` redirects only stdout, and llama-bench writes
  tg128/build-metadata to stderr - `2>&1` fixed it, d=4096 now shows
  both rows cleanly (2.45 t/s tg128, consistent with the dense corridor
  prediction). This part is resolved and is a genuine harness-bug
  finding, not a model or hardware issue.
- But the SAME re-investigation then hit something much more serious:
  d=8192's re-run and a fresh eval-pilot attempt both hung. Direct
  process inspection (`/proc/<pid>/wchan`, `/proc/<pid>/status`,
  `/proc/<pid>/io` - agent-spark has no sudo on sparkmax, `dmesg` is
  restricted, but these /proc files are readable for one's own process)
  found the stuck `llama-server` (PID 361827) blocked in
  `drm_suballoc_new` - the same terminal kernel frame as F24's confirmed
  amdgpu SDMA suballocator deadlock trace. Unchanged across repeated
  checks spanning 24-27+ minutes; `read_bytes` of 121.8GB against an
  ~88.2GB total model size (more data read than exists - a thrash
  pattern, not a slow normal load). New finding logged: **F27**
  (docs/FINDINGS.md) - notably, WITHOUT F24's own confirmed trigger
  (concurrent heavy disk I/O); this model has the MOST headroom of any
  in the 8-model batch. Two candidate explanations registered, neither
  confirmed: cumulative driver/GPU state after ~13 large-model
  load/unload cycles today with no reboot, or a lighter-weight trigger
  than F24's original 62GB-hash-scale concurrent I/O.
- **Action taken: benchmarking halted immediately on discovery.** Per
  F24's own established rule, SIGKILL cannot act on a D-state task
  blocked in this kernel path - recovery requires a system reboot, not
  a kill or a retry. No attempt was made to force the process or work
  around it. E23 (Devstral 2 123B) was corrected in results/experiments.md
  to attribute the d=8192 and eval-pilot failures to F27, replacing an
  earlier mischaracterization ("eval-pilot server configuration is
  incompatible with this model") that undersold the severity - this
  correction was made directly (not via the usual subagent+reviewer
  cycle) given the time-criticality of an imminent reboot.
- **Session ends here for the reboot.** Full resume instructions:
  HANDOFF.md "Open / next". Outstanding for Devstral: d=8192 tg128 leg,
  full quality eval, both need a clean re-attempt post-reboot (not a
  resume of the stuck process, which the reboot clears). Outstanding
  for the campaign: Tasks 7-9 (3 remaining models), the full
  re-verification of Tasks 2/3, and Tasks 10-13 (report writing +
  publish) - none of this can safely proceed until GPU/system health is
  reconfirmed post-reboot.

## 2026-07-09 (later) - Post-reboot recovery: F27 cleared, GPU/system health signed off as usable

- The reboot the F27 entry above ended for did NOT come back cleanly on
  its own - it needed a hard power cycle. `last -x` confirms the
  mechanism: an attempted shutdown/reboot at 08:06 hung (down 08:06,
  boot recorded 08:13 that did not come up), then a manual hard power
  cycle brought the current boot up at 08:16. **This is the expected
  consequence of F27, not a second fault:** a D-state task blocked in
  `drm_suballoc_new` is uninterruptible AND stalls a clean shutdown
  (systemd waits on a process that never unblocks), so the graceful
  reboot could not complete. The hard power cycle was the only exit.
  The stuck `llama-server` (PID 361827) is confirmed gone
  (`/proc/361827` no longer exists).
- **Health verified across every axis an unclean hard power-cycle could
  damage, each measured rather than assumed:**
  - Stuck / D-state tasks: NONE (`ps -eo stat` shows no `D`; the F27 PID
    is gone).
  - GPU (amdgpu): functional - driver bound (PCI 1002:1586, RADV
    GFX1151), Vulkan device enumerates, `uma:1`.
  - Kernel this boot: 1 warning total, ZERO amdgpu/DRM
    reset/hang/fault/suballoc lines.
  - Root filesystem: `rw` with a clean ext4 journal replay - no
    read-only emergency remount (the tell-tale of on-disk corruption).
    439G free (76% used).
  - Git repo: intact - `git fsck` shows only benign dangling objects
    (amended/reset history), zero corruption/missing/broken-link errors;
    tree clean, in sync with origin/main.
- **Known-good GPU load test (the decisive sign-off).** Paused
  `llama-gateway.service` to free the GPU (it had auto-started on boot
  and re-loaded Qwen3-30B - see gotcha below), then ran the canonical
  `llama-bench` on Qwen3-4B-Instruct-2507 Q4_K_M (a single-file model
  already in the survey cohort) at d=0. Result: **pp512 2049.84 ± 15.81
  t/s, tg128 78.64 ± 0.49 t/s**, exit 0, no DeviceLost/abort in stderr,
  sub-1% CV on both. This is a like-for-like MATCH to the historical
  baseline (results/model-survey.md: pp512 2051.57, tg128 78.38 - deltas
  -0.08% and +0.33%, both far inside the ±1.5% F15 noise band). The test
  is meaningful precisely because it exercises the exact subsystem F27
  deadlocked: model load into the unified/GTT pool, then GPU inference
  through the Vulkan/RADV path. **Verdict: machine state signed off as
  fully usable.**
- **Gotcha recorded for the campaign (and any future reboot mid-run):**
  a reboot silently UNDOES the campaign's gateway-paused state.
  `llama-gateway.service` auto-starts and re-loads its model onto the
  GPU, violating the F24/F27 one-model-at-a-time rule. It MUST be paused
  (`systemctl --user stop llama-gateway.service`) before any bench/eval
  run resumes, exactly as Task 1 of the plan did originally. Confirmed
  paused as of this sign-off; GPU is free for the Devstral Task 6
  re-attempt.
- **Resume point unchanged from the F27 entry's "Outstanding" list:**
  Devstral (E23) d=8192 tg128 leg + full quality eval need a clean
  re-attempt (not a resume), then Tasks 2/3 re-verification, Tasks 7-9,
  then report writing. Proceeding now with Task 6.

## 2026-07-03 - Step 7 pre-registration: three new rows queued (decisions locked by Alastair)

- Bench queue brief received (decisions locked 2026-07-03, Alastair with
  Claude web). Green-lit, queue order: gpt-oss-20b MXFP4 (efficiency
  control), Qwen3.6-35B-A3B UD-Q4_K_XL (workhorse challenger),
  GLM-4.7-Flash Q4_K (workhorse hedge). GLM-4.5-Air weights HELD for the
  Phase B quality audition - no further throughput work. Qwen3-Next-80B-
  A3B demoted to watchlist (superseded generation; documented Vulkan pp
  weakness on this hardware). Do-not-test by corridor pricing:
  Qwen3.6-27B dense (~18GB/token -> ~11-12 t/s here), Llama-4 Scout
  class (17B active, ~16 t/s), all 235B+ (does not fit; stress probe
  stays parked per 4.3).
- **Pre-registered predictions (recorded BEFORE any Step 7 run;
  deviations are findings):**
  - Row A gpt-oss-20b (~12GiB MXFP4, ~3.6B active): naive ceiling
    ~220/1.94GB = ~113 t/s. Fork: tg128 near 90 (~80% of naive) ->
    the 120b's 67%-of-ceiling is model-specific overhead; near 75
    (~67%) -> MXFP4 carries a quant tax on this box and the pre-screen
    constant gains a quant term.
  - Row B Qwen3.6-35B-A3B (35B/3B-active hybrid MoE, DeltaNet + Gated
    Attention; text bench only): tg128 d0 ~80-90 t/s (~2.0-2.2GB/token
    at this quant, 0.8 x 220). pp512 deliberately NOT predicted - it
    measures Vulkan kernel maturity for the DeltaNet path; weak pp
    beside healthy tg = software finding, not model failure. Bench at
    DEFAULT ubatch 512 (sibling Qwen3-Next has a documented Strix
    Halo/RADV pp regression above ubatch 512 - do not tune around it;
    the default-config number is the finding). At 8K: shallow tg slope
    expected if kernels behave.
  - Row C GLM-4.7-Flash (31.2B/~3-3.6B active pure-transformer MoE):
    tg128 d0 ~75-90 t/s; pp512 expected in pure-MoE class (Qwen3-30B
    territory) - weak pp here IS a genuine anomaly, unlike Row B.
- Row C artefact gate: GGUF upload must post-date 2026-01-21
  (llama.cpp scoring_func softmax->sigmoid fix; earlier GGUFs loop and
  score badly). House build gate PASSED: pinned commit 067de937 is
  dated 2026-07-03 (verified via git show) - post-dates the fix, no
  rebuild needed.
- Invocation: combined `-d 0,8192` permitted for all three rows (all
  well under the ~60GiB split-invocation rule from the GLM-4.5-Air
  memory-edge finding).
- **OPEN CONVENTION FLAG for Alastair - not resolved unilaterally:**
  does the ~70 t/s instant-tier line apply at d0 only, or must it also
  hold at 8K? The current workhorse sits at 66.97 @ d8192, so the
  choice changes its badge and how the new rows get judged.

## 2026-07-03 - Step 7 Row A: gpt-oss-20b efficiency control (recorded - fork lands on MXFP4 quant tax)

- Exact spec: gpt-oss-20b-mxfp4.gguf (ggml-org, revision e1dc459f,
  manifest VERIFIED on arrival - size byte-exact, sha256 identical to
  upstream oid), llama.cpp 067de937 Vulkan, Mesa 25.2.8, kernel
  6.17.0-35, TTM 105GB. Canonical command:
  `llama-bench -m <gguf> -d 0,8192 -o md` (combined permitted per
  brief - 11.27 GiB, well under the ~60GiB split-invocation rule).
- Declared condition: Row B download ran concurrently (~16MB/s network
  -to-disk over eno1; <0.1% of the ~220GB/s memory bandwidth - declared
  rather than silently absorbed).
- Results (llama-bench: 11.27 GiB file, 20.91B params):
  - pp512: **1366.71 ± 12.31** | tg128: **77.76 ± 0.81**
  - pp512 @ d8192: **1005.33 ± 41.22** | tg128 @ d8192: **70.65 ± 0.58**
- **Pre-registered fork resolution: 77.76 = 68.8% of the ~113 t/s
  naive ceiling - decisively the "near 75 / ~67%" arm (11 points from
  the 80% arm, under 2 from the 67% arm). MXFP4 carries a quant tax on
  this box; the pre-screen constant gains a quant term.**
  Effective-bandwidth clusters across the matrix: Q4_K family lands
  84-100% of naive (14B ~100%, GLM-Air 86%, Qwen A3B 84%); MXFP4 lands
  ~64-69% (120b per step 5 entry, 20b here). Residual confound:
  both MXFP4 points are also both gpt-oss architecture, so family
  overhead is not fully separable from quant with this pair alone. The
  clean discriminator exists: GLM-4.7-Flash ships a same-model
  Q4_K_M / MXFP4_MOE pair (both pinned in the manifest) - Alastair's
  call whether that second data point earns a run.
- Depth behaviour: tg -9.1% at d8192 (70.65) - same shallow slope as
  the 120b (-9.5%); the family's alternating/SWA attention pattern.
- Convention-flag side effect: gpt-oss-20b clears the ~70 t/s line at
  BOTH d0 and 8K - instant-tier under either reading of the open
  convention. An unplanned candidate out of the control row; Phase B
  use would need harmony-format handling.
- Raw output: llama.cpp/bench-step7-gptoss20b.md.

## 2026-07-03 - Step 7 Row B: Qwen3.6-35B-A3B workhorse challenger (recorded - tg MISSES pre-registered band; pp healthy)

- Exact spec: Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf (unsloth, revision
  a483e9e6, manifest VERIFIED on arrival - size byte-exact, sha256
  identical to upstream oid), llama.cpp 067de937 Vulkan, Mesa 25.2.8,
  kernel 6.17.0-35, TTM 105GB. Canonical command:
  `llama-bench -m <gguf> -d 0,8192 -o md` at DEFAULT ubatch 512 per
  pre-registration - no tuning around the sibling (Qwen3-Next) pp
  regression.
- Declared condition: Row C download ran concurrently (~16-19MB/s to
  disk; <0.1% of memory bandwidth).
- Results (llama-bench: 20.81 GiB file, 34.66B params, qwen35moe
  35B.A3B):
  - pp512: **996.40 ± 5.90** | tg128: **59.30 ± 0.36**
  - pp512 @ d8192: **803.78 ± 12.62** | tg128 @ d8192: **55.29 ± 0.42**
- **Pre-registered prediction vs outcome (deviations are findings):**
  - tg128 d0 predicted ~80-90: observed **59.30 - MISS, 26% below the
    band floor.** Effective bandwidth ~119-125GB/s = ~54-57% of naive -
    below even the MXFP4 cluster, on a Q4_K artefact. The weight-bytes
    model does not capture this hybrid's per-token cost: DeltaNet
    recurrent-state read/write traffic and/or immature Vulkan kernels
    on the recurrent path are the candidate drags (not separable from
    llama-bench alone).
  - pp512 (unpredicted by design): 996 d0 / 804 @8K - HEALTHY, second
    only to Qwen3-30B's 1138. The anticipated Qwen3-Next-style Vulkan
    pp collapse did NOT materialise at default ubatch.
  - Depth slope: tg -6.8% at 8K - shallowest in the matrix (-9.1/-9.5%
    gpt-oss, -13.2% GLM-Air, -28% Qwen30B). The linear-attention
    shallow-slope prediction CONFIRMED.
- Business case: 59.3 d0 / 55.3 @8K fails the ~70 t/s line at both
  depths - the challenger misses the workhorse audition on throughput
  under either reading of the open convention. Its distinguishing
  asset is the flattest depth curve; any crossover vs Qwen3-30B sits
  beyond 8K (unmeasured - noted, not extrapolated).
- Finding shape for the pre-screen rule: healthy pp + depressed tg is
  the INVERSE of the failure mode the brief hedged against. Hybrid
  architectures need a per-token-cost term in the corridor rule, not
  just active weight bytes.
- Raw output: llama.cpp/bench-step7-qwen36-35b.md.

## 2026-07-03 - Step 7 addendum pre-registration: quant-isolation pair (GLM-4.7-Flash MXFP4_MOE)

- Green-lit by Alastair 2026-07-03 under the dual-purpose research
  reframe (lab findings are client-facing on-prem AI research;
  resolving the Row A confound is the point, not a nice-to-have).
- Design: same model (GLM-4.7-Flash), same build/backend, quant varied:
  Q4_K_M (Row C, the matrix row, 18,312,339,808 bytes) vs MXFP4_MOE
  (16,968,499,296 bytes, upstream oid ecf4f3fd..., same 2026-02-12
  upload date - passes the scoring_func date gate). This isolates the
  quant variable that Row A's gpt-oss pair could not separate from
  architecture family.
- **Pre-registered fork (efficiency fractions, fixed before either
  GLM-4.7-Flash artefact is benched):** if MXFP4_MOE lands in the
  ~64-69%-of-naive-ceiling cluster while Q4_K_M lands in the 84-100%
  cluster, the MXFP4 tax is quant-intrinsic on this stack and the
  pre-screen quant term stands. If both land in the same cluster, Row
  A's depressed fraction was gpt-oss-family overhead and the quant
  term is withdrawn. Naive ceilings computed per row from llama-bench's
  reported params x artefact bytes/param x active fraction, per the
  house convention.
- Caveat pre-declared: gpt-oss MXFP4 is quantization-aware/native;
  GLM-4.7-Flash MXFP4_MOE is a post-hoc community requant. A
  same-cluster result withdraws the quant term; a split result
  confirms the tax for POST-HOC MXFP4 on this stack, with native
  MXFP4 evidence still resting on the gpt-oss pair alone.
- Sequencing: bench AFTER Row C's Q4_K_M matrix row completes
  (sequential GPU use, sequential downloads on the ~16-19MB/s
  upstream-limited line).

## 2026-07-03 - Step 7 Row C: GLM-4.7-Flash workhorse hedge (recorded - tg near-miss; pp healthy at d0; MLA arch tax surfaced)

- Exact spec: GLM-4.7-Flash-Q4_K_M.gguf (unsloth, revision 0d32489e,
  date gate PASSED, manifest VERIFIED on arrival - size byte-exact,
  sha256 identical to upstream oid), llama.cpp 067de937 Vulkan, Mesa
  25.2.8, kernel 6.17.0-35, TTM 105GB. Canonical command:
  `llama-bench -m <gguf> -d 0,8192 -o md`.
- Declared condition: MXFP4_MOE download ran concurrently (~16-19MB/s).
- Arch note: llama-bench identifies the artefact as **deepseek2
  30B.A3B** (29.94B params reported vs the brief's 31.2B) -
  GLM-4.7-Flash runs on llama.cpp's DeepSeek-V2-style graph (MLA
  attention + shared-expert MoE). Load-bearing for the arithmetic
  below.
- Results (17.05 GiB file):
  - pp512: **943.49 ± 1.24** | tg128: **71.93 ± 0.69**
  - pp512 @ d8192: **340.01 ± 16.91** | tg128 @ d8192: **50.74 ± 0.29**
- Pre-registered prediction vs outcome:
  - tg128 d0 predicted ~75-90: observed **71.93 - NEAR-MISS, 4.1%
    below the band floor.**
  - pp512 (expected pure-MoE class): 943 at d0 - healthy, no anomaly.
    BUT pp @8192 = 340 (-64%) is the steepest non-memory-edge prefill
    slope in the matrix (Qwen30B -51%, 14B -55%); candidate cause is
    MLA latent-projection compute at depth on Vulkan. Recorded as
    observation, not attributed.
  - tg depth slope -29.5% - matches Qwen30B's -28% (small-active-set
    physics, as expected).
- Ceiling arithmetic: 0.612 bytes/param; active 3.0-3.6B ->
  1.83-2.20GB/token -> naive ceiling ~100-120 t/s; observed 71.93 =
  **60-72% of naive (central ~66% at 3.3B active) - on a Q4_K
  artefact. The 84-100% Q4_K premise does NOT hold for this model.**
- **Matrix insight - the A3B label is not a price:** three A3B-class
  MoEs, same quant family, same hardware: Qwen3-30B (pure MoE) 92.8 =
  84% of naive; GLM-4.7-Flash (MLA MoE) 71.9 = ~66%; Qwen3.6-35B
  (DeltaNet hybrid) 59.3 = ~55%. A 1.57x tg spread by architecture
  alone. Extends the Row B finding: the corridor rule needs an
  ARCHITECTURE term, not just active weight bytes - MLA and hybrid
  recurrence both underprice per-token cost.
- **AMENDMENT to the quant-isolation pre-registration (declared BEFORE
  the MXFP4_MOE leg runs):** the fork assumed the Q4_K_M leg would
  land in the 84-100% cluster; it landed at ~66%. The fork therefore
  resolves on the SAME-MODEL DELTA: MXFP4_MOE fraction within a few
  points of Q4_K_M's ~66% -> no quant tax beyond the arch effect
  (quant term weakened; architecture is the operative lever).
  MXFP4_MOE fraction clearly below -> quant tax stacks on the arch tax
  (quant term confirmed for post-hoc MXFP4). The same-model design is
  unaffected by the premise miss - resolving exactly this ambiguity is
  why the pair exists.
- Business case: 71.93 clears the ~70 line at d0 by 2.8% but sits at
  50.74 @8K - the OPEN CONVENTION FLAG now decides this row's badge
  too (d0-only: instant tier, barely; also-8K: fails). On throughput
  Qwen3-30B keeps the workhorse seat (92.8/67.0 vs 71.9/50.7);
  GLM-4.7-Flash's Phase B audition case is quality + MIT licence, not
  speed.
- Raw output: llama.cpp/bench-step7-glm47flash.md.

## 2026-07-03 - Step 7 addendum resolved: MXFP4 tg tax CONFIRMED, stacks on arch tax

- Exact spec: GLM-4.7-Flash-MXFP4_MOE.gguf (unsloth, revision
  0d32489e, date gate passed, manifest VERIFIED on arrival - size
  byte-exact, sha256 identical to upstream oid), same build/backend as
  Row C. Canonical command: `llama-bench -m <gguf> -d 0,8192 -o md`.
  No concurrent downloads - first clean-condition run of step 7.
- Results (15.79 GiB file, 29.94B params, deepseek2 30B.A3B MXFP4 MoE):
  - pp512: **985.57 ± 2.46** | tg128: **62.94 ± 0.16**
  - pp512 @ d8192: **327.42 ± 2.89** | tg128 @ d8192: **46.22 ± 0.28**
- **Amended-fork resolution: QUANT TAX CONFIRMED, tg-specific.**
  Same-model delta: Q4_K_M 71.93 tg = ~66% of naive; MXFP4_MOE 62.94 =
  ~53.5% (0.567 bytes/param -> 1.87GB/token central -> ceiling ~118) -
  a 12.5-point fraction drop. The decisive framing: the MXFP4 artefact
  is 7.3% SMALLER (fewer bytes to read per token) yet generates 12.5%
  SLOWER. Effective bandwidth 117.7 vs 145.2 GB/s = MXFP4 achieves 81%
  of Q4_K's per-byte efficiency on the identical model, build, and
  hardware. Bandwidth arithmetic cannot produce that sign; the MXFP4
  dequant path on this Vulkan stack costs it.
- Refinement: **the tax is TG-ONLY.** pp512 985.57 is +4.5% ABOVE the
  Q4_K_M leg - compute-bound prefill pays no MXFP4 penalty here; the
  cost lands exactly where production latency lives, token generation.
- Cross-check vs Row A: gpt-oss MXFP4 fractions (64-69%) sit ABOVE
  GLM's MXFP4 (53.5%) - architecture still dominates absolute levels
  (gpt-oss SWA > GLM MLA). Clean isolated claims: (1) post-hoc MXFP4
  requant costs ~19% effective tg bandwidth vs Q4_K, same-model, this
  stack; (2) native-MXFP4 (gpt-oss) evidence is consistent with a tax
  but family-confounded, per the pre-declared caveat.
- Pair design bonus: depth slopes are quant-invariant (tg -26.6% vs
  -29.5%; pp -66.8% vs -64.0%) - the MLA-at-depth behaviour is an ARCH
  property, cleanly separated from quant by the same-model design.
- **Pre-screen corridor rule as Phase A closes:** t/s ~= (220 GB/s /
  active bytes per token) x arch factor (dense ~1.0, pure MoE ~0.84,
  MLA-MoE ~0.66, DeltaNet hybrid ~0.55) x quant factor (Q4_K baseline
  1.0, post-hoc MXFP4 ~0.81 on tg). Phase B may refine the factors;
  the FORM is now evidence-based, all terms from pre-registered runs.
- **Step 7 COMPLETE:** 3 matrix rows + 1 research pair; every artefact
  manifest-VERIFIED against upstream oids; every run pre-registered;
  every deviation logged as a finding.
- Raw output: llama.cpp/bench-step7-glm47flash-mxfp4.md.

## 2026-07-03 - Step 8 pre-registration: unattended window (depth curves, dense/MLA constants, contamination + KV-quant characterisation)

- Provenance: brief authored outside the session (author lacked full
  project context), sanity-checked against log/manifest/staging this
  session, APPROVED by Alastair 2026-07-03 with amendments (recorded
  below). Everything here is logged BEFORE any Step 8 run.
- **Sanity-check corrections (declared before runs):**
  1. The brief's findings register (F3/F11/F12 references) did not
     exist. Created docs/FINDINGS.md: F1-F11 numbered chronologically
     from this log; content-mapping lands the "single-cluster" quant
     reading at F3, so the brief's supersession reference holds as
     written. F11 (already resolved by the step 7 pair) entered now;
     F12 reserved for the 2d fork.
  2. Stop-on-anomaly CV gate scoped: >5% halts tg legs; pp-at-depth
     legs halt at >10%. Healthy artefacts already show 4-5% pp@8192 CV
     (gpt-oss-20b 4.1%, Flash Q4 5.0%) - a flat 5% gate would
     false-halt known-good measurement classes.
  3. Block 3a premise corrected: Row B measured HEALTHY pp at default
     ub 512 (996 t/s); the documented regression is on sibling
     Qwen3-Next, ABOVE ub 512. Registered expectation unchanged - pp
     degrades above 512; a flat sweep is a kernel-maturity finding.
  4. End-state badge table will carry BOTH convention columns (d0-only
     AND both-depths). The brief's "under the both-depths convention"
     would unilaterally resolve the step 7 OPEN CONVENTION FLAG; two
     columns satisfy the brief without closing Alastair's flag.
  5. Block 2d fork registered verbatim (below) plus a pin-time
     derivation check: naive ceiling recomputed from the pinned
     artefact's actual bytes; if the implied factor boundaries move
     materially (>~5 t/s), a declared amendment lands BEFORE the run.
  6. Block 2c: meta-llama HF repos are gated; planned substitution is
     an ungated community GGUF (bartowski or lmstudio-community),
     logged per the brief's substitution rule.
  7. Network note: approval message says "still on Wi-Fi" - eno1
     ethernet is in fact active and default-routed (ip route verified
     this session). The power-blip caveat stands regardless: unattended
     window, unconfirmed AC-restore behaviour - a mysteriously short
     log has a known suspect.
- **Alastair's amendments (approved 2026-07-03, overriding the brief
  where they conflict):**
  1. Blanket "downloads may overlap benches" REPLACED by Block 3c
     contamination experiment. Until 3c reports, Block 2 downloads
     wait for Block 1 benches to finish. 3c design: canonical
     Qwen3-30B leg quiet vs with a download + SHA256 verification
     deliberately active (the first Block 2 fetch is the contamination
     source - on UMA, disk I/O, page cache, and hashing share the
     LPDDR5x bus the GPU reads weights from). PREDICTION: tg delta
     <2%, within triplet CV. Holds -> overlap rule becomes
     evidence-based; breaks -> Block 1 numbers were protected.
  2. DeviceLost canary gate: after ANY DeviceLost, run the Qwen3-0.6B
     canary (~30s) before touching the queue. Canary passes ->
     continue; fails or degrades -> HALT the entire window and flag
     (a wedged Vulkan driver produces plausible-looking garbage - the
     worst unattended outcome, because it looks like data).
  3. Block 3d added - KV-cache-quant depth leg on Qwen3-30B
     (-ctk q8_0 -ctv q8_0). Design note declared now: quantised
     V-cache requires flash attention, so the lever config is
     -fa 1 + q8 KV = TWO variables vs baseline; an intermediate
     -fa 1 (f16 KV) leg is added so FA and KV-quant effects separate
     (quant-isolation discipline, applied again). Registered
     expectations: d0 tg within ~5% of baseline for both legs; at max
     shared depth, q8-KV tg >= f16 baseline (the lever "works").
     Fork: -fa 1 alone regressing tg >5% = the lever is FA-blocked on
     this Vulkan stack (a finding, not a failure).
  4. Thermal capture: amdgpu hwmon edge temp logged before/after every
     leg (tools/run_step8_leg.sh wrapper, hwmon node resolved by name)
     -> llama.cpp/bench-step8-thermal.log. Gives the repeatability
     triplet its explanation if CV drifts; sustained-load thermal
     behaviour is itself client-facing material.
  5. End-state gains item 6 - re-run trigger: the canonical set
     re-executes on any llama.cpp/Mesa/kernel bump, diffed against the
     house baseline (binding text lands in WORKPLAN Section 3 at
     end-state). Constants are maintained measurements, not decaying
     folklore.
  6. Concurrency scaling explicitly PARKED for Step 9: needs
     llama-server + a load generator - real machinery with judgment
     calls, disqualified from an unattended window; that machinery is
     the Phase B harness's server-lifecycle core, so Step 9 builds it.
  7. Reframe on the record: the METHOD is the product, not the
     constants (see FINDINGS.md F10 status note).
- **Block 1 registered questions** (depth curves
  `-d 0,2048,4096,8192,16384`, +32768 only where n_ctx_train >= 32896
  - read from the loader's metadata at launch, not asserted from
  memory - and KV arithmetic clears 5GiB heap headroom, trivially true
  at these sizes; six residents: Qwen3-30B-A3B, Qwen3.6-35B, Flash
  Q4_K_M, Flash MXFP4_MOE, gpt-oss-20b, Qwen3-14B; Qwen3-0.6B excluded
  as smoke/canary; Air + 120b excluded per brief):
  - Q1: at what depth does Qwen3-30B tg cross below 70? PREDICTION:
    between 4096 and 8192 (interpolating 92.83 -> 66.97; linear and
    reciprocal-linear models both put the crossing ~6.9-7.2K).
  - Q2: at what depth does gpt-oss-20b tg cross below 70? PREDICTION:
    between 8192 and 16384 (held 70.65 +/- 0.58 at 8K - by 1.1 sigma).
  - Q3: does the hybrid hold a flatter tg slope than pure-MoE rows?
    PREDICTION priced from its own step 7 points: yes - Qwen3.6-35B
    repeats ~-7% at 8K vs Qwen3-30B's -28%; expect the flattest curve
    in the matrix at every depth.
  - Q4: do the Flash Q4/MXFP4 curves stay parallel at all depths?
    PREDICTION: yes - extends quant-invariant slopes from 2 points
    to 5.
- **Block 2 registered bands (verbatim from the brief):**
  - 2a Qwen3-4B, newest instruct variant, Q4_K family (~2.5GB):
    tg128 d0 in 75-85. The 8K badge is a registered QUESTION, not a
    number.
  - 2b Qwen3-8B, Q4_K family (~5GB): tg128 d0 in 37-43.
  - 2c Llama-3.1-8B dense family control, Q4_K family (~5GB, ungated
    community GGUF per correction 6): tg128 d0 in 38-44. Landing well
    off the Qwen 8B number = dense constant is family-contaminated,
    and the register must say so.
  - 2d DeepSeek-V2-Lite (16B total / 2.4B active, MLA, Q4 family,
    ~10GB): FORK - tg128 <=105 confirms MLA as a general constant
    class; >=112 says the 0.66 was Flash-specific; 105-112 recorded
    as inconclusive. Older model: support problems -> log and skip,
    no unattended debugging.
- **Block 3:** 3a ubatch sweep, Qwen3.6-35B pp512 at
  -ub 128,256,512,1024,2048, d0 (registered expectation: pp degrades
  above ub 512, per corrected premise in correction 3). 3b
  repeatability triplet: canonical Qwen3-30B leg (`llama-bench -m
  <gguf> -o md`) at window start/middle/end; PREDICTION: tg CV <2%
  across the three. 3c and 3d as amended above.
- **Standing rules otherwise as the brief wrote them:** retention rule
  (nothing deleted); pause downloads below 10% free disk (1.6T free
  at window open - not in play); stop-on-anomaly halts the leg, not
  the queue (except the canary gate); Rule 4.3 untouched - no stress
  probes, nothing over 25GiB.
- **Execution order:** 3b leg 1 -> Block 1 curves (six models) ->
  3b leg 2 -> 3c at the Block 1/Block 2 boundary -> Block 2
  (fetch+verify+bench per artefact) -> 3a -> 3d -> 3b leg 3 ->
  end-state (combined table; constants ladder with n per constant;
  F12 + Block 1 badge-death findings into FINDINGS.md; DUAL-convention
  badge table; WORKPLAN Section 3 re-run trigger; HANDOFF refresh;
  plain-language note for Alastair on what changed and which
  predictions broke).

## 2026-07-04 - Step 8 Block 2 pins, declared 2d amendment, 3c design note

- All four Block 2 artefacts pinned per 4.4 execution-time versioning
  (revisions, byte sizes, upstream LFS oids in manifests/MANIFEST.md,
  entries PENDING until arrival verification):
  - 2a unsloth/Qwen3-4B-Instruct-2507-GGUF Q4_K_M, rev a06e946b,
    2,497,281,120 B.
  - 2b unsloth/Qwen3-8B-GGUF Q4_K_M, rev a6adef13, 5,027,784,512 B.
  - 2c bartowski/Meta-Llama-3.1-8B-Instruct-GGUF Q4_K_M, rev bf5b95e9,
    4,920,739,232 B (ungated community GGUF per correction 6).
  - 2d mradermacher/DeepSeek-V2-Lite-Chat-GGUF Q4_K_M, rev 9ee9f1f8,
    10,364,416,768 B. SUBSTITUTION declared: the bartowski repo for
    this model does not exist (HF API 401); mradermacher mirror used.
- **DECLARED AMENDMENT - 2d fork thresholds (before the 2d run; the
  pre-registered materiality trigger fired):** the brief's 105/112
  values imply a ~157 t/s naive ceiling (0.585 B/param pure-quant
  assumption). The pinned artefact is 0.660 B/param (house convention:
  file bytes / params) -> 2.4B active -> ~1.58 GB/token -> naive
  ~139 t/s. Applying the brief's own factor semantics to the real
  ceiling: **tg128 <=92 confirms MLA as a constant class; >=99 says
  the 0.66 was Flash-specific; 92-99 inconclusive.** Same fork shape,
  same inconclusive-zone width (5% of ceiling), recalibrated to the
  actual artefact 13 t/s below the brief's assumed one.
- **3c design refinement (declared before the run):** quiet-CONTAM-
  quiet sandwich instead of a single quiet reference. Triplet leg 2
  (93.41, seconds before) is the leading quiet bracket; a trailing
  quiet leg runs immediately after the contaminated one. Delta is
  measured against the bracket mean - run-level drift (observed
  +/-1.5-3% across the window) would otherwise be indistinguishable
  from contamination. Contamination source: the real 2a fetch
  (~17MB/s network-to-disk write) plus a deliberate sha256sum of the
  47GB Air shard 1 (sustained ~GB/s read+hash on the shared LPDDR5x
  bus). Prediction unchanged: tg delta <2%.
- Triplet leg 2 recorded: pp512 1117.68 +/- 9.14, tg128 93.41 +/- 0.53
  (llama.cpp/bench-step8-triplet-2.md). Leg 1/leg 2 spread 90.63 ->
  93.41 (CV 2.1%, straddling the registered 2% line; leg 3 decides).
  Leg 2 is FASTER after ~4h of sustained benching, and every leg
  starts from the same 46-47degC idle - thermal-accumulation
  explanation dead; drift is non-monotonic state noise.

## 2026-07-04 - Step 8 Block 3c RESOLVED: contamination null on mean; variance signature found

- Declared deviation: the composite's first invocation carried a shell
  precedence bug (`&` bound the var-assignment + fetch chain, so the
  parent shell's hash load died instantly on an empty-variable
  redirect). Consequence: the two contamination sources ran as
  SEPARATE arms - download-only, then hash-only - which gives
  per-source attribution the registered lumped design could not.
  Overlap evidenced in both arms (fetch reaped only after the bench
  returned; explicit `kill -0` probe printed OVERLAP-CONFIRMED).
- Arm 1 - download (~17MB/s network-to-disk write; the real 2a
  fetch): tg 92.37 +/- 0.44 vs quiet bracket (93.41 lead / 92.42
  trail, mean 92.92) -> **delta -0.6%. NULL.**
- Arm 2 - sha256 of the 47GB Air shard (sustained ~GB/s read+hash on
  the shared LPDDR5x bus): tg 93.05 +/- 2.01 vs bracket (92.42 lead /
  91.05 trail, mean 91.74) -> **delta +1.4%. NULL on mean - but
  within-run sigma inflated ~4x** (2.01 vs 0.16-0.80 on every quiet
  leg this window). Bus contention on UMA arrives as JITTER, not
  throughput loss.
- **PREDICTION HOLDS (<2% both arms). Overlap rule now
  evidence-based:** downloads may overlap benches freely; heavy
  sequential disk-read/hash work leaves means intact but inflates
  variance - keep it away from legs whose CV matters, or expect the
  variance flag. Client-facing form: "ingest during inference on
  unified memory: throughput holds, latency jitter rises."
- 2a arrived during arm 1 and VERIFIED (byte-exact 2,497,281,120 B,
  local sha256 identical to upstream oid) - manifest flipped.
- Quiet-leg tg catalogue this window: 90.63 / 93.41 / 92.42 / 91.05
  (plus 92.28 curve d0) - run-level spread ~+/-1.5% around ~92 is the
  measured error bar for single-run numbers on this stack (bears on the
  Q2 bracket miss).
- Raw: llama.cpp/bench-step8-3c-contam.md, -contam-hash.md,
  -quiet-after.md, -quiet-after2.md.
- 2b/2c/2d downloads start now, overlapped with Block 2 benches per
  the resolved rule (declared condition on affected legs).

## 2026-07-04 - Step 8 Block 2a: Qwen3-4B dense boundary case (recorded - band HIT; 8K question answered)

- Exact spec: Qwen3-4B-Instruct-2507-Q4_K_M.gguf (unsloth, rev
  a06e946b, manifest VERIFIED on arrival), llama.cpp 067de937 Vulkan,
  Mesa 25.2.8, kernel 6.17.0-35, TTM 105GB. Canonical
  `llama-bench -m <gguf> -d 0,8192 -o md`. Declared condition: 2b
  download ran concurrently (evidence-based overlap rule, 3c entry).
- Results (2.32 GiB file, 4.02B params):
  - pp512: **2051.57 ± 8.40** | tg128: **78.38 ± 0.64**
  - pp512 @ d8192: **665.94 ± 12.71** | tg128 @ d8192: **54.12 ± 0.22**
- **Registered band 75-85: HIT (78.38).** The dense boundary case
  clears the ~70 instant line at d0. Registered 8K QUESTION answered:
  54.12 - no badge under a both-depths reading; the 4B loses 31% of
  tg by 8K, the STEEPEST tg slope in the matrix (steeper than the
  30B MoE's -28%). Small weight set -> KV-read fraction dominates
  early; F5 physics at its sharpest.
- Ceiling arithmetic (house convention): 0.620 B/param x 4.02B dense
  -> 2.49 GB/token -> naive ~88 t/s; observed 78.38 = **88.7% of
  naive** - inside the Q4_K 84-100% cluster, with first signs of
  small-model overhead at the cluster's low edge.
- pp512 2051 at d0 is the highest prefill in the matrix - the
  instant-feel asset of tiny dense models is prompt latency, not
  generation.
- Raw: llama.cpp/bench-step8-block2a-qwen3-4b.md.

## 2026-07-04 - Step 8 declared deviation: 3a pulled into the download window

- Registered order was Block 2 complete -> 3a -> 3d. The 2b/2c/2d
  fetches (~20GB at upstream-limited ~17MB/s) leave the GPU idle for
  ~20 min; 3a (ubatch sweep, resident Qwen3.6-35B) runs now instead,
  with Block 2 benches interleaving as artefacts verify. Downloads
  overlapping benches is the 3c-resolved rule; sweep legs carry the
  declared condition.

## 2026-07-04 - Step 8 Block 3a first pass: brief's design cannot test its own question; AMENDED before the extension runs

- Results (pp512 only, -n 0, ub sweep; declared condition: downloads
  active): ub128 **555.86 ± 11.41**, ub256 **700.39 ± 9.18**, ub512
  **899.00 ± 11.39**, ub1024 **896.11 ± 8.25**, ub2048 **893.21 ± 6.30**.
- **Design flaw exposed by the data:** with a 512-token prompt, ubatch
  above 512 never fills - the prompt caps the physical batch, so the
  ub 1024/2048 legs are computationally identical to ub 512. The
  three statistically indistinguishable results (899/896/893) confirm
  it empirically. The registered expectation ("pp degrades above
  ub 512") is UNTESTABLE at pp512; the only real information below
  512 is a normal saturation curve (556 -> 700 -> 899, no anomaly).
- **DECLARED AMENDMENT (before the extension runs):** re-run at
  pp2048 with ub 512/1024/2048 so ubatch actually exceeds 512 in
  flight. Expectation carried over unchanged: if the sibling
  (Qwen3-Next) regression manifests in this architecture, per-token
  prefill rate degrades at ub 1024/2048 vs 512. Flat = kernel
  maturity finding.
- Raw: llama.cpp/bench-step8-block3a-ubatch.md.
- Note for the brief's post-mortem: pp512 @ ub2048 was a
  never-fires configuration in the original design - the sweep needed
  prompt >= max ubatch from the start.

## 2026-07-04 - Step 8 Block 3a RESOLVED: no ubatch regression; mild ub1024 optimum

- Amended sweep (pp2048, -n 0; declared condition: 2c download active):
  ub512 **929.40 ± 35.99**, ub1024 **1014.55 ± 2.50**, ub2048
  **929.54 ± 10.23**.
- **Registered expectation ("pp degrades above ub 512") MISSES - in
  the good direction.** No Qwen3-Next-style collapse manifests in
  qwen35moe on this stack: ub1024 IMPROVES on ub512 by +9.2%, and
  ub2048 returns to ub512 level (flat, not degraded). Kernel-maturity
  finding: the hybrid's prefill path is healthy across ubatch; the
  default leaves ~9% on the table at ub1024 for long prompts.
  Deployment note only - the canonical bench spec stays at default
  512 per Section 3 discipline.
- ub512's elevated variance (3.9% CV) is consistent with the 3c
  variance signature: the fetch chain sha256-hashes each completed
  file, and 2b's end-of-file hash plausibly overlapped this first
  sweep leg (jitter, no mean shift). Under the 10% pp gate; recorded,
  not halted.
- Raw: llama.cpp/bench-step8-block3a-ubatch-pp2048.md.

## 2026-07-04 - Step 8 Block 2b: Qwen3-8B second dense point (recorded - band overshot by a hair; dense-at-ceiling confirmed)

- Exact spec: Qwen3-8B-Q4_K_M.gguf (unsloth, rev a6adef13, manifest
  VERIFIED on arrival), house build/backend. Canonical
  `llama-bench -m <gguf> -d 0,8192 -o md`. Declared condition: 2c/2d
  downloads active (evidence-based overlap rule).
- Results (4.68 GiB file, 8.19B params):
  - pp512: **1078.08 ± 1.70** | tg128: **43.56 ± 0.24**
  - pp512 @ d8192: **499.97 ± 10.38** | tg128 @ d8192: **35.23 ± 0.15**
- **Registered band 37-43: overshot by 1.3% (43.56)** - a marginal
  high-side miss that the ceiling arithmetic explains: 0.614 B/param
  x 8.19B dense -> 5.03 GB/token -> naive 43.7 t/s; observed = **99.7%
  of naive**. Dense Q4_K runs AT the bandwidth ceiling on this stack
  (14B: ~100%, now 8B: ~100%; the 4B's 88.7% marks where small-model
  overhead starts). The band was drawn conservative, the physics is
  F4 exactly.
- Raw: llama.cpp/bench-step8-block2b-qwen3-8b.md.

## 2026-07-04 - Step 8 Block 2c: Llama-3.1-8B family control (recorded - dense constant is FAMILY-CLEAN)

- Exact spec: Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf (bartowski, rev
  bf5b95e9, manifest VERIFIED on arrival; ungated community GGUF per
  correction 6), house build/backend. Canonical
  `llama-bench -m <gguf> -d 0,8192 -o md`. Declared condition: 2d
  download active (evidence-based overlap rule).
- Results (4.58 GiB file, 8.03B params):
  - pp512: **1089.93 ± 2.11** | tg128: **44.21 ± 0.21**
  - pp512 @ d8192: **538.54 ± 10.40** | tg128 @ d8192: **35.96 ± 0.29**
- **Registered band 38-44: at the ceiling edge (44.21, 0.5% over).**
  Ceiling arithmetic: 0.613 B/param x 8.03B dense -> 4.92 GB/token ->
  naive 44.7; observed = **98.9% of naive**.
- **Family-contamination check RESOLVES CLEAN:** Qwen3-8B 43.56 =
  99.7% of naive; Llama-3.1-8B 44.21 = 98.9% - the two most
  architecturally distinct mainstream dense families land within 1%
  of each other in ceiling fraction. Dense Q4_K ~= 1.0 x naive is a
  STACK property, not a Qwen property. Dense constant now n=4 (14B
  ~100%, 8B x2 ~99%, 4B 88.7% marking small-model overhead onset).
- Raw: llama.cpp/bench-step8-block2c-llama31-8b.md.

## 2026-07-04 - Step 8 Block 2d: DeepSeek-V2-Lite MLA fork (recorded - F12 RESOLVED: 0.66 was Flash-specific)

- Exact spec: DeepSeek-V2-Lite-Chat.Q4_K_M.gguf (mradermacher, rev
  9ee9f1f8, manifest VERIFIED on arrival; substitution declared in the
  pins entry), house build/backend. Canonical
  `llama-bench -m <gguf> -d 0,8192 -o md`. No downloads active - 2d
  was the last fetch. The "older model support problems" caveat never
  fired: the deepseek2 graph is this model's home graph.
- Results (9.65 GiB file, 15.71B params, deepseek2 16B):
  - pp512: **1640.63 ± 13.15** | tg128: **110.80 ± 0.55**
  - pp512 @ d8192: **1181.76 ± 29.65** | tg128 @ d8192: **44.52 ± 0.21**
- **Amended fork resolution: 110.80 >= 99 -> the ~0.66 MLA-MoE factor
  was FLASH-SPECIFIC.** 110.80 / ~139 naive = **~80% of ceiling** -
  pure-MoE territory (0.84), nowhere near 0.66, on the archetype of
  the same llama.cpp graph GLM-4.7-Flash runs. MLA alone does not
  price a model; the corridor rule's MLA-MoE row becomes a per-model
  range (0.66-0.80, n=2) pending a mechanism split.
- **The amendment converted an inconclusive into a decisive result:**
  under the brief's original thresholds (105/112, derived from an
  assumed ~157 ceiling) this exact measurement would have landed in
  the inconclusive zone. Pin-time re-derivation is now a proven step,
  not a formality.
- Depth wrinkle: tg -59.8% at 8K - the steepest 8K drop in the
  matrix, per-token depth cost (+13.4ms at 8K) 2-3x Flash's or
  Qwen3-30B's. Candidate cause: deepseek2/MLA per-token compute at
  depth on Vulkan (consistent with Flash's pp-at-depth collapse,
  amplified by the tiny 2.4B active set). Recorded, not attributed.
- Business aside: 110.80 d0 is the fastest tg in the matrix, but the
  8K number (44.52) fails the line - a pure d0-demo model on this
  stack unless short-context workloads dominate.
- Raw: llama.cpp/bench-step8-block2d-dsv2lite.md.

## 2026-07-04 - Step 8 Block 3d RESOLVED: q8 KV is a working depth lever; FA is free

- Signature check before the runs: at 067de937 `-fa` is tri-state
  (on|off|auto, default auto) - the brief's implied 0/1 form would
  have errored, and the Block 1 baseline ran under auto. Design
  unaffected: leg 1 vs baseline reads what auto chose; leg 2 vs leg 1
  isolates the KV quant.
- Leg 1 (-fa on, f16 KV, six depths): tg 92.12 / 81.60 / 75.78 /
  66.66 / 53.09 / 38.15 - identical to the auto-baseline within noise
  at every depth (-0.2 to -0.9%). **Registered FA-blocked fork does
  NOT fire; FA costs nothing here** (auto almost certainly resolves
  to on for this model). Raw: bench-step8-block3d-fa-on-f16.md.
- Leg 2 (-fa on, q8_0 K+V, six depths): tg 88.66 / 79.64 / 75.34 /
  67.98 / 57.61 / 43.75. Deltas vs leg 1: **-3.8% / -2.4% / -0.6% /
  +2.0% / +8.5% / +14.7%** - a clean crossover at ~4-6K depth.
  **Both registered expectations HOLD:** d0 cost inside the ~5%
  budget; q8 >= f16 at max shared depth, decisively. Raw:
  bench-step8-block3d-fa-on-q8kv.md.
- Nuance for the badge-death map: the 70-line crossing moves only
  ~6.9K -> ~7.1K (the crossing sits near the q8 break-even), so KV
  quant does NOT rescue instant badges - what it buys is deep-context
  throughput (+15% at 32K) and half the KV footprint (unmeasured
  capacity headroom noted, not claimed).
- pp under q8 KV: mostly slightly slower (-3 to -9% through 16K),
  +5.8% at 32K - mixed, secondary, recorded in the raw table.

## 2026-07-04 - Step 8 END-STATE: window complete (5 mandated deliverables + item 6)

### 1. Combined depth matrix (canonical spec: llama.cpp 067de937 Vulkan, Mesa 25.2.8, kernel 6.17.0-35, TTM 105GB; all VERIFIED artefacts)

tg128 (t/s) by depth:

| Model | d0 | 2048 | 4096 | 8192 | 16384 | 32768 |
|---|---|---|---|---|---|---|
| Qwen3-30B-A3B Q4_K_M | 92.28 | 82.35 | 76.30 | 67.06 | 53.21 | 38.32 |
| ^ +q8 KV (fa on) | 88.66 | 79.64 | 75.34 | 67.98 | 57.61 | 43.75 |
| Qwen3.6-35B UD-Q4_K_XL | 58.71 | 57.08 | 56.53 | 55.14 | 52.47 | 47.87 |
| GLM-4.7-Flash Q4_K_M | 70.93 | 62.75 | 57.12 | 50.50 | 39.21 | 27.91 |
| GLM-4.7-Flash MXFP4 | 63.44 | 56.44 | 52.72 | 45.43 | 36.47 | 26.29 |
| gpt-oss-20b MXFP4 | 75.22 | 71.97 | 71.24 | 67.51 | 63.57 | 56.08 |
| Qwen3-14B Q4_K_M | 24.34 | 23.39 | 22.65 | 21.19 | 18.85 | 15.47 |

pp512 (t/s) by depth:

| Model | d0 | 2048 | 4096 | 8192 | 16384 | 32768 |
|---|---|---|---|---|---|---|
| Qwen3-30B-A3B Q4_K_M | 1140.72 | 912.75 | 744.61 | 561.16 | 346.59 | 182.10 |
| Qwen3.6-35B UD-Q4_K_XL | 982.86 | 870.38 | 844.46 | 799.36 | 702.46 | 587.42 |
| GLM-4.7-Flash Q4_K_M | 922.24 | 613.14 | 484.49 | 315.59 | 197.01 | 113.85 |
| GLM-4.7-Flash MXFP4 | 968.27 | 628.99 | 479.14 | 321.82 | 199.57 | 113.48 |
| gpt-oss-20b MXFP4 | 1321.83 | 1141.74 | 1084.99 | 964.48 | 727.08 | 457.86 |
| Qwen3-14B Q4_K_M | 621.66 | 453.03 | 386.27 | 271.79 | 156.47 | 39.54* |

*flagged: 10.7% CV, marginally over the pp gate - low confidence; the
dense 16K->32K prefill cliff (4x drop) is real in direction, magnitude
low-confidence.

Block 2 rows (canonical d0/8192):

| Model | tg d0 | tg 8K | pp d0 | pp 8K | % of naive (d0) |
|---|---|---|---|---|---|
| DeepSeek-V2-Lite Q4_K_M | 110.80 | 44.52 | 1640.63 | 1181.76 | ~80% |
| Qwen3-4B-2507 Q4_K_M | 78.38 | 54.12 | 2051.57 | 665.94 | 88.7% |
| Llama-3.1-8B Q4_K_M | 44.21 | 35.96 | 1089.93 | 538.54 | 98.9% |
| Qwen3-8B Q4_K_M | 43.56 | 35.23 | 1078.08 | 499.97 | 99.7% |

### 2. Constants ladder (n per constant; single machine, single stack)

- Naive ceiling: 220 GB/s / active bytes per token (house convention:
  file bytes/param x active params).
- Dense Q4_K arch factor: **~1.00** (n=3: 14B 1.00, Qwen-8B 0.997,
  Llama-8B 0.989 - FAMILY-CLEAN per 2c). Small-dense overhead onset:
  0.89 at 4B/2.3GiB (n=1).
- Pure-MoE Q4_K: **~0.84-0.86** (n=2: Qwen3-30B 0.84, GLM-Air glm4moe
  0.86).
- MLA-MoE Q4_K: **per-model 0.66-0.80, NOT a single class** (n=2:
  Flash 0.66, DeepSeek-V2-Lite 0.80; F12 resolved Flash-specific).
- DeltaNet-hybrid Q4_K: **~0.55** (n=1: Qwen3.6-35B).
- MXFP4 quant multiplier: **~0.81, tg-only** (n=1 same-model isolated;
  gpt-oss native-MXFP4 consistent but family-confounded).
- q8_0 KV lever: -3.8% at d0, break-even ~4-6K, +8.5% @16K, +14.7%
  @32K; FA itself free (n=1: Qwen3-30B).
- Depth slopes: architecture-determined, quant-invariant (Flash pair,
  5 depths); hybrid flattest (-18.5% by 32K), MLA/pure-MoE steepest
  (-59 to -61%), dense pays the full quadratic pp price at 32K.
- Single-run noise: **±1.5% CV** (triplet n=3); one cross-evening pair
  (gpt-oss-20b, -3.3%/-4.4%) exceeds it - unexplained, watch.

### 3. Findings register updated

F11/F12 resolved earlier this window; F13 (badge-death map), F14
(depth-dependent workhorse crossover), F15 (run-noise + UMA jitter
signature), F16 (q8-KV lever) appended to docs/FINDINGS.md; F10 ladder
re-priced per above.

### 4. Badge table - BOTH conventions (the flag stays Alastair's)

Badge-death = interpolated depth where tg crosses below 70.

| Model | d0-only | both-depths (d0+8K) | badge-death |
|---|---|---|---|
| Qwen3-30B-A3B | INSTANT (92.3) | NO (67.1 @8K) | ~6.9K (q8 KV: ~7.1K) |
| gpt-oss-20b | INSTANT (75.2-77.8) | BORDERLINE - 8K value straddles the line across runs (70.65 step 7 / 67.51 step 8) | ~5.5-9K, measurement-sensitive (flat curve at the line) |
| GLM-4.7-Flash Q4 | INSTANT, hairline (70.93) | NO (50.5) | **~230 tokens** - most fragile badge in the matrix |
| DeepSeek-V2-Lite | INSTANT (110.8, fastest d0 in matrix) | NO (44.5) | ~3.2K (2-pt estimate) |
| Qwen3-4B-2507 | INSTANT (78.4) | NO (54.1) | ~2.2K (2-pt estimate) |
| Qwen3.6-35B | NO (58.7) | NO | never held it (but holds 47.9 at 32K - best deep-context tg) |
| all dense 8-14B, Air, 120b, Flash MXFP4 | NO | NO | - |

Convention-flag consequence, stated plainly: d0-only awards FIVE
badges (three of them dying under 3.5K of context); both-depths awards
ZERO unambiguously (gpt-oss-20b is borderline). The 8K convention is
effectively a one-model club on this hardware - and that model's
membership flips with ±2% run noise.

### 5. Prediction scoreboard (11 registered, pre-run)

- Q1 crossing 4096-8192: **HIT** (~6.9K). Q2 crossing 8192-16384:
  **MISS** - landed 4096-8192 via cross-run drift; finding, not
  failure. Q3 flattest hybrid slope: **HIT** (+crossover found). Q4
  parallel quant curves: **HIT** with mechanism refinement
  (convergence at depth). 2a 75-85: **HIT** (78.38). 2b 37-43:
  overshot 1.3% (at-ceiling). 2c 38-44: edge (44.21, at-ceiling,
  family-clean). 2d fork: **decisive via declared amendment**
  (Flash-specific). 3a "degrades above ub512": **MISS good-direction**
  (+ original design was untestable - flaw found and amended). 3b
  triplet CV<2%: **HOLDS** (1.52%). 3c contamination <2%: **HOLDS**
  both arms (+jitter signature). 3d d0<5% and q8>=f16 at depth: both
  **HOLD**.

### 6. Re-run trigger

Banked in WORKPLAN Section 3 (two-tier: quick on any bump, full
depth-curve set on tolerance breach or kernel-relevant changes; ±1.5%
noise floor written into the tolerance).

### Plain-language note (Alastair)

What changed in the constants: dense ~1.0 is now family-clean (n=3);
"MLA-MoE 0.66" died as a class - it is Flash-specific (DeepSeek-V2-Lite
runs 0.80); pure-MoE 0.84-0.86 gained a second point; the quant-tax and
hybrid numbers stand unchanged. What broke: only Q2 (gpt-oss crossing
bracket, run-drift artefact) and 3a's expectation (no ubatch regression
exists - and the brief's original sweep couldn't have detected one; the
amended sweep settles it). New levers you can quote to clients: q8 KV
costs ~4% fresh and buys ~15% at 32K with half the KV memory; ingest
during inference holds throughput and costs only jitter; every "instant"
badge on this box dies with context depth, and the depth where it dies
is now a measured number per model.

## 2026-07-04 - Phase B roadmap sequenced (Alastair)

- Order: Step 9 concurrency characterisation FIRST (Phase B on-ramp -
  server-lifecycle core + throughput-vs-slots chart, one session, two
  deliverables) -> promptfoo spike (rides the same server machinery;
  eval suites get short- and long-context variants per task type, per
  the step 8 badge-death data) -> 235B probe + pressure test (parked
  for physical presence per 4.3; KV-quant lever and contamination
  variables now pre-designed rather than discovered under pressure).
  Qwen3-Coder bench and whisper.cpp STT spike slot into gaps
  (half-day, non-blocking).
- Assistant design notes recorded at sequencing time:
  (a) Step 9's comparison anchor is our own single-slot Vulkan
  numbers - the ROCm ~168 t/s @16-slot field figure is cross-backend,
  same trap the step 6 surplus attribution avoided; aggregate-speedup
  curve is the correct chart. A q8-KV arm belongs in the design (F16:
  halved KV = more slots per context budget).
  (b) 235B arithmetic: Q4_K_M ~133GB exceeds the 105.5GiB GTT
  outright; Q2/Q3 quants graze the 71.65GiB device-local heap - the
  probe is an F6 memory-edge/heap-spill experiment by construction,
  and quant selection is part of the design, not an afterthought.
  (c) The thermal-envelope urgency on the Coder bench is retired by
  step 8 evidence: 6h of sustained benching, every leg starting
  46-47degC, no drift (triplet CV 1.52%) - the box re-enters its
  envelope in seconds, so the Coder bench is a gap-filler without a
  clock. Pre-registration gift: same arch/quant/size as the workhorse
  -> predict ~92 t/s tg d0; any deviation is a finding about coder
  fine-tunes, not physics.
  (d) Long-context eval variants are diagnostic only BEYOND a model's
  F13 badge-death depth, and the harness should measure TTFT
  separately from generation - pp collapse (Flash -88% by 32K, dense
  4x cliff at 16K->32K) is the failure users actually feel.

## 2026-07-04 - Step 9 pre-registration: concurrency characterisation (spec: docs/plans/2026-07-04-step9-concurrency.md)

- Green-lit by Alastair 2026-07-04 ("plan and execute"). Spec written
  first per specs.md; deviation noted there (SPEC-TEMPLATE.md does not
  exist in this repo; equivalent sections carried explicitly).
  docs/plans/ created this session.
- Deliverables: (A) tools/serve_bench.py - the Phase B server-lifecycle
  core (HARNESS-RULES 1-4 binding); (B) throughput-vs-slots dataset,
  Qwen3-30B workhorse, slots {1,2,4,8,16} x KV {f16,q8_0}; secondary
  gpt-oss-20b {1,4,16} f16 if the window allows.
- **Pre-registered predictions (before any run):**
  - P1: single-slot per-stream gen rate 85-93 t/s.
  - P2: aggregate monotonic in slots; 16-slot/1-slot aggregate RATIO
    2.5-4.5x (ROCm field ratio ~3.7x is the anchor for the ratio only;
    cross-backend caveat declared).
  - P3: per-stream monotonically declining; instant-tier frontier
    (max slots with per-stream >= 70) at 1-2 slots.
  - P4: q8-KV aggregate within -6%..+2% of f16 at equal slots.
  - P5: registered QUESTION - the scaling knee (slot count where the
    marginal aggregate gain per doubling drops below 20%).
- Pulled-forward smoke per integration-smoke rule: Qwen3-0.6B, -np 2,
  before any workhorse config.
- Gap-filler pre-registration (Coder): Qwen3-Coder-30B-A3B-Instruct
  Q4_K_M pinned (rev b17cb02d, 18,556,689,568 B - within 3KB of the
  workhorse artefact, same arch/quant). **Registered band: tg128 d0
  90.5-94** (workhorse triplet band); deviation = coder-finetune
  finding, not physics. Bench runs only in a GPU gap; download
  overlaps per the 3c rule.
- promptfoo spike BLOCKED on Node (absent on host) - toolchain
  decision flagged to Alastair (apt nodejs vs user-level nvm). Step 9
  proceeds; the spike inherits serve_bench's machinery when unblocked.

## 2026-07-04 - Step 9 RESULTS: concurrency characterisation (deliverables A+B complete)

- Deliverable A shipped: tools/serve_bench.py (HARNESS-RULES 1-4
  enforced in code: HTTP-only /completion, timeouts on every wait,
  Rule 3 offload gate parses -v logs and treats zero evidence as
  failure, finally-guaranteed kill). Pulled-forward smoke PASSED
  first-run (Qwen3-0.6B, -np 2, 20 requests, gate green). Post-run
  process check: CLEAN (pgrep -x, no llama-server left; note: pgrep
  -af self-matches through the session shell wrapper - use -x).
- Method note: aggregate = generated tokens / wall (includes each
  request's prompt phase - serving throughput); per-stream = mean of
  server-side gen-phase rates (tg128 analog). Unique prompt prefix
  per request, cache_prompt=false, so every request pays realistic
  prefill. Declared condition: Coder download active throughout
  (3c rule).
- **Primary matrix, Qwen3-30B-A3B Q4_K_M (aggregate / per-stream /
  TTFT p50 ms):**

| slots | f16 KV | q8_0 KV |
|---|---|---|
| 1 | 72.85 / 87.81 / 287 | 67.97 / 85.00 / 285 |
| 2 | 104.53 / 63.37 / 390 | 103.54 / 62.69 / 405 |
| 4 | 137.08 / 42.97 / 695 | 133.92 / 41.84 / 718 |
| 8 | 159.79 / 24.86 / 1154 | 157.87 / 24.53 / 1186 |
| 16 | 193.49 / 14.68 / 1677 | 192.39 / 14.79 / 1720 |

- **Secondary, gpt-oss-20b MXFP4 f16 (slots 1/4/16):** 59.86 / 101.32
  / 108.99 aggregate; per-stream 71.57 / 31.86 / 8.23; TTFT p50 273 /
  750 / 2540 ms.
- **Prediction resolutions:**
  - P1 HIT: single-slot per-stream 87.81 (band 85-93); server+HTTP
    costs ~4.8% vs bare llama-bench tg128.
  - P2 HIT: 16-slot/1-slot aggregate ratio **2.66x** (band 2.5-4.5).
    Absolute 193.5 t/s is +15% over the ROCm ~168 field figure -
    the recurring Vulkan>ROCm pattern, cross-backend caveat stands.
  - P3 HIT: per-stream monotone declining; **instant-tier frontier =
    1 slot** (63.4 at 2 slots already fails the ~70 line).
  - P4: 4/5 configs in the -6..+2% band; ws1 lands -6.7%, 0.7 points
    past the floor - within the +/-1.5% run-noise of the boundary.
    Verdict: q8 KV is effectively FREE under concurrency at 4K
    contexts, while halving the KV budget that caps slot count.
  - P5 answered: NO sharp knee on the workhorse - gains per doubling
    +43/+31/+17/+21%, still rising at 16 slots. The knee exists on
    gpt-oss-20b instead: scaling collapses past ~4 slots (+7.6% from
    4->16).
- **FINDING (new, -> F17): concurrency scaling is architecture-
  dependent.** Workhorse 2.66x at 16 slots vs gpt-oss 1.82x; the
  models' single-user gap (92 vs 78, 1.2x) WIDENS to 1.8x aggregate
  under fleet load. Candidate causes for the gpt-oss plateau: MXFP4
  dequant cost compounding in batched matmuls (F11 mechanism), or
  the SWA/alternating-attention batch path; not separable with this
  tool - a Coder-vs-workhorse pair can't test it, but a Q4_K vs
  MXFP4_MOE concurrency pair on GLM-4.7-Flash could (same-model
  isolation again; noted as a candidate follow-up, not scheduled).
- TTFT is the user-visible cost of fleet load: p50 grows ~6x from 1
  to 16 slots (287 -> 1677 ms) on the workhorse, 2.5s on gpt-oss@16.
  Phase B evals that care about perceived latency must budget TTFT
  per slot count, not just throughput.
- Raw: llama.cpp/bench-step9-ws*-{f16,q8}.json,
  bench-step9-oss20b-ws*.json (+ .serverlog per config); smoke JSON
  in session scratchpad (throwaway per no-home-clutter).

## 2026-07-04 - Gap-filler: Qwen3-Coder-30B bench (recorded - band HIT dead-centre)

- Exact spec: Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf (unsloth, rev
  b17cb02d, manifest VERIFIED on arrival - byte-exact, sha256 = oid),
  house build/backend. Canonical `llama-bench -m <gguf> -d 0,8192 -o
  md`. GPU-gap sequencing honoured (ran after the Step 9 matrix).
- Results (17.28 GiB, 30.53B params, qwen3moe - same graph as the
  workhorse):
  - pp512: **1108.96 ± 8.96** | tg128: **93.05 ± 0.65**
  - pp512 @ d8192: **558.57 ± 7.43** | tg128 @ d8192: **67.09 ± 0.84**
- **Registered band 90.5-94: HIT, dead-centre.** The coder finetune is
  throughput-identical to the workhorse (d0 within the triplet band;
  @8K 67.09 vs 67.06 - to three significant figures). Fine-tuning
  changes weight VALUES, not weight BYTES; the corridor rule prices
  both identically and the measurement agrees. Phase B can choose
  between them on quality alone; throughput is a wash.
- Raw: llama.cpp/bench-step9-coder30b.md.

## 2026-07-04 - promptfoo spike PASSED (3/3); user-level toolchain installed and documented

- Authorisation: Alastair 2026-07-04, remote - "user level for
  anything you need, document it" -> docs/TOOLCHAIN.md carries the
  full what/where/why/removal/permanent-options record.
- Toolchain: Node v24.18.0 LTS tarball (hash-verified against
  SHASUMS256.txt per download-integrity) at ~/.local/opt/, chosen
  over nvm because nvm patches shell init files that belong to the
  deploy-managed dotfiles repo. promptfoo 0.121.17 installed inside
  the prefix. Measured footprint: ~3.1GB (2.1G prefix incl. promptfoo
  node_modules + 993M npm cache) - larger than the ~40MB quoted when
  flagging the option; the delta is promptfoo's dependency tree, not
  Node.
- Spike (spikes/promptfoo-spike/): llama-server on Qwen3-4B (-np 4,
  -c 16384 explicit, --jinja), promptfoo openai provider at
  127.0.0.1:8100/v1, three wire-up tests (factual / is-json /
  arithmetic). **Result: 3/3 PASS, 90 tokens, concurrency 4; server
  killed cleanly (pgrep -x verified).** Raw: spikes/promptfoo-spike/
  results.json; server log in session scratchpad (throwaway).
- **Verdict vs HARNESS-RULES:** Rule 1 native fit (promptfoo speaks
  OpenAI HTTP); Rule 2 satisfiable (outer timeout wrapped the eval;
  per-request timeouts configurable) with the key division of labour
  CONFIRMED: promptfoo does NOT manage servers - our serve_bench-class
  wrapper keeps lifecycle, offload gate (Rule 3), and outer timeouts.
  Rule 4 untouched (spike used a manifest-VERIFIED artefact).
  promptfoo is VIABLE for Phase B as the eval orchestrator inside our
  lifecycle wrapper; adoption decision remains a Phase B design call
  (with Step 8's short+long context variants as a design input).
- Telemetry/update pings disabled via env at run time (not persisted;
  the Phase B wrapper must set them - noted in TOOLCHAIN.md).

## 2026-07-10 (later) - Post-reboot recovery (F28)

Recovery from the F28 amdgpu SDMA deadlock (docs/FINDINGS.md F28).
Like F27, the graceful `sudo reboot` did NOT come back on its own -
remote access hit "No route to host" and Alastair performed a **hard
power cycle** (second consecutive occurrence of this class to need
one). Machine back: booted 2026-07-10 18:28:14 (confirmed from inside;
this session runs on sparkmax).

Health sign-off before any GPU work:
- No stray `llama-bench`/`llama-server`; no D-state tasks.
- `llama-gateway.service` had auto-restarted on boot (holding the 30B) -
  stopped it (`systemctl --user stop`), confirmed inactive, GPU VRAM
  back to 148 MB idle baseline.
- Known-good `llama-bench` (Qwen3-4B-Instruct-2507-Q4_K_M, `-ngl 99`,
  Vulkan): **pp512 2033.45 ± 20.39, tg128 78.85 ± 0.21** vs survey
  baseline 2051.57 / 78.38 - both within F15's ±1.5% single-run noise
  (pp512 -0.88%, tg128 +0.60%). No CPU compute-buffer lines. GPU
  healthy, deadlock cleared. Stderr captured to session scratchpad.

Durable outcome of this incident: added HARNESS-RULES.md **Rule 5**
(never re-create the deadlock's known triggers during routine benching)
at Alastair's explicit request. Resume point unchanged: repeatability
campaign Phase 2, Task 26 (Devstral d0/d4096) - NOT Command A+ d8192,
which is folded into F28's open trigger question.
