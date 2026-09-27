# File: e146-prereg.md
# Purpose: Pre-registration for E146 - does the Atlas inference engine deliver its published Strix Halo decode speed on Qwen3.8-27B, and does it beat llama.cpp with a drafter?
# Project: sparkbench | Date: 2026-09-25
#
# Overview: The owner pasted the marketing page of atlasinference.dev. Its Strix Halo claims are 19.63 tok/s
# in an MLPerf edge-agentic run and, in the engine README, "28.3 to 28.6 tok/s" at K=4 on Qwen3.8-27B-NVFP4.
# Two GitHub repositories both present themselves as Atlas and are in a declared dispute, so this
# registration pins exact commits and takes no side. The fair comparator is llama.cpp WITH a drafter,
# already measured in E138 (25.67 tok/s on code prompts). Written before any build or run.

# E146 PRE-REGISTRATION - Atlas on Strix Halo vs llama.cpp with a drafter (2026-09-25)

## The question

On this box (Ryzen AI Max+ 395, gfx1151, Linux), does Atlas serve `nvidia/Qwen3.8-27B-NVFP4` at its
published decode speed, and does it beat llama.cpp serving the same model with speculative decoding?
The interesting margin is small: the README's 28.3 to 28.6 tok/s is about 10% above E138's llama.cpp +
DFlash2 code-prompt figure of 25.67. A result "Atlas works" is not the test; "Atlas is faster than the
open alternative, on which workload" is.

## What this can and cannot test (declared now)

- **NOT tested: the MLPerf number.** 19.63 tok/s across 1,007 agentic turns is defined by MLPerf's own
  harness and workload, which this run does not reproduce. Gate G5 only reads the primary MLCommons entry.
- **Different weights.** Atlas runs NVFP4 (20.44 GiB, FP8 attention plus NVFP4 MLP); llama.cpp runs
  Q4_K_M (15.66 GiB). Speed is compared, quality is not, except by the conditional block 2.
- **Provenance is disputed and this run does not settle it.** `Atlas-Inf/atlas` (created 2026-08-24, 30
  stars) presents itself as the replacement official channel and calls the older repo a disputed asset.
  `Avarok-Cybersecurity/atlas` (created 2026-05-05, 699 stars) holds the `mlperf-edge-strix-*` tags and a
  `toolchain-scale-1.7.1` tag. The vendor page shows "675 stars" and a "PR #187" link that match the older
  repo's numbering, not the one it links; recorded as a fact, not as a verdict. We test code at pinned
  commits, never installers.

## Gates before any GPU window (CPU only, all recorded in `results/e146-results.md`)

| # | gate | pass condition |
|---|---|---|
| G1 | provenance record | both repos, commit SHAs, licences (both AGPL-3.0), CLA files read; nothing fetched by `curl | sh`, `sparkrun` or `uvx` |
| G2 | source review of the build | the build scripts named in the README are read; every network fetch and binary download in them is listed |
| G3 | sandboxed build of Atlas-Inf @ 2d1aab8 | built under `/home/agent-spark/atlas-e146/` as agent-spark, no sudo, no apt, system ROCm 7.2.4 unchanged (F58); if the Rust toolchain is missing it is installed user-local, version pinned and recorded |
| G4 | weights | `nvidia/Qwen3.8-27B-NVFP4` fetched, every file size and sha256 equal to the manifest pin |
| G5 | primary MLPerf entry | the MLCommons result for the Atlas submission is read: submitter, hardware, OS, model, division, verified or not. Recorded whichever way it falls |
| G6 | runner | tools/e138_speed.py gains an `--engine atlas` mode; its design is declared in Amendment 1 before any run |

A gate that fails stops the affected arm; it is recorded as VOID, never scored as slow.

## Arms (one server at a time, solo, gateway down)

| arm | engine and commit | model | why |
|---|---|---|---|
| **Q0** | llama.cpp `daef7b6` | Qwen3.8-27B Q4_K_M, no drafter | E138 incumbent, 12.33 tok/s; re-run because the window differs (F117) |
| **Q1** | llama.cpp `daef7b6` | Qwen3.8-27B Q4_K_M + Qwen3.8-27B-DFlash2-Q8_0 drafter, n=4 | E138 best open configuration, 25.67 CODE / 16.70 CHAT; re-run |
| **X1** | Atlas-Inf/atlas @ `2d1aab8bf4f813059d5614776117b27d17931c05` | Qwen3.8-27B-NVFP4, K=4 | the README's Strix Halo claim, on the repo the vendor page links |
| **X2** | Avarok-Cybersecurity/atlas at tag `mlperf-edge-strix-k3-m64-20260724` | as X1 if it accepts it | the lineage that carries the MLPerf tags; needs the SCALE toolchain, so it may be VOID |

## Block 1 - decode and prefill (the scored block)

- **Decode:** E138's CODE and CHAT prompts, unchanged, 3 repeats each at temperature 0. Speed is the
  server's own decode rate where the engine reports one; otherwise client-side tokens over generation
  time, declared per engine in Amendment 1 and reported beside the other.
- **Context:** one ~30K-token prompt and its decode rate (the README quotes 13.3 to 13.6 tok/s "at 30k").
- **Prefill:** E139's exact-token 8K and 32K prompts, median of 3.
- **Determinism:** 10 identical greedy requests in one process, byte-compared, then 2 in a fresh process.
- **Memory and network:** peak GPU memory against the window-open baseline (Chatterbox resident, amendment
  2 of E139 applies); the set of established network connections is recorded during every serving arm.
- Same conditions as E139: 12 GiB memory guard, relay restored on every exit path, each arm banked.

## Block 2 - quality parity (conditional)

Runs only if X1 completes block 1. E143's harness (Aider, three tasks, three repeats) against X1's
OpenAI-compatible endpoint, compared with E143 arm A (Qwen3.8-27B Q4_K_M: 5/9). Not an engine test; it
asks whether the NVFP4 build behaves like the model we already know.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `X1.serves` | YES: builds and serves the model within the window | README claims Linux support merged; active commits |
| P2 | `X1.CODE.decode_tps` (median of 3) | 22-32 | README 28.3-28.6 at K=4; E138 Q1 25.67 |
| P3 | `X1.CHAT.decode_tps` | 13-20 | F85: acceptance is workload-shaped; E138 Q1 CHAT 16.70 |
| P4 | `X1.CODE / Q1.CODE` | 0.85-1.25 | both are bandwidth-bound and speculative; the README implies about 1.10 |
| P5 | `X1.CHAT / Q1.CHAT` | 0.75-1.25 | as P4 |
| P6 | `X1.P32K.prefill_tps / Q1.P32K.prefill_tps` | 0.5-2.0 | no prior for either engine at this depth; deliberately wide |
| P7 | `X1.decode_tps` at ~30K context | 9-16 | README 13.3-13.6 |
| P8 | `X1.determinism` | 10 of 10 byte-equal, and 2 of 2 across a fresh process | the vendor states deterministic greedy output; F96 warns about repeats within one process |
| P9 | `X2.builds` | NO (VOID within the window) | SCALE toolchain access and licence unknown |
| P10 | `X1.peak_gpu_mem_gib`, net of baseline | 20-32 | 20.44 GiB weights plus KV |
| P11 | `X1.aider_passes` (block 2) | 3-7 of 9 | E143 A scored 5/9 on the same model family; quantisation differs |

## Decision bands (fixed now)

- **Atlas speed claim (28.3-28.6 tok/s):** CONFIRMED if `X1.CODE.decode_tps` >= 26.0 (the low end less
  about 8%); REPRODUCED-CONDITIONALLY at 20-26; NOT REPRODUCED below 20 or if X1 does not serve.
- **Atlas versus llama.cpp with a drafter:** "Atlas faster" only if `X1/Q1` >= 1.15 on BOTH CODE and CHAT;
  "not separated" between 0.87 and 1.15; "llama.cpp faster" at <= 0.87 on both. A split is reported as
  workload-dependent, never averaged into a winner.
- **MLPerf claim:** NOT TESTED. Whatever G5 finds is reported as what the primary source says.
- Nothing here recommends adopting or avoiding either repository; provenance is out of scope.

## Stop rules

Memory guard fires, GPU fault in `dmesg`, or a serving arm holding an established connection to any
non-local address the build scripts did not declare (G2): stop the arm, record it, restore the relay. An
arm still running at 2 h stops at its next request boundary. Second guard kill on an arm ends it.

## Out of scope

The MLPerf agentic workload, the Windows path, other models (Qwen3.8-Flash-Next is listed by the vendor as
not yet run on Strix Halo Linux), the sparkrun recipe system, and any judgement on which repository is
the genuine Atlas.

## AMENDMENT 1 - G5 changes the design: test MLPerf's own metric against MLPerf's own reference (declared 2026-09-25, before any GPU run)

**Trigger.** Gate G5 (results/e146-gates.md) read the primary MLCommons entry. Four findings change the plan:

1. The published Strix Halo configuration is **Qwen3.6-27B** (`nvidia/Qwen3.6-27B-NVFP4` @ 0893e160), **MTP K=3**,
   native HIP on Linux with ROCm 7.13. This registration assumed Qwen3.8-27B at K=4 (the README's claim). Both
   claims stay in scope; they are different configurations.
2. The official MLPerf metric is **mean latency per turn**, not tok/s: Strix Halo 7,058.99 ms, DGX Spark 3,807.66 ms.
   The vendor page's tok/s figures and "under 64 minutes" do not match it (gates file).
3. The harness, dataset and configuration are public (`mlcommons/endpoints` @ 4235a9c8), and its README names the
   reference: **Qwen3.6-27B Q4_K_M under llama.cpp**. That file is already on this box (E145 arm G).
4. The entry's descriptor says native HIP, not SCALE. **Arm X2 (the SCALE lineage) is withdrawn** and P9 with it.

**Blocks (replaces the arm table's role; Q0, Q1, X1 move to block 1 unchanged).**

| block | arm | engine | model | purpose |
|---|---|---|---|---|
| **M (scored, primary)** | M0 | llama.cpp `daef7b6`, reference flags | Qwen3.6-27B Q4_K_M (unsloth, 16,817,244,384 B) | MLPerf reference implementation, on this box |
| | M1 | Atlas-Inf @ 2d1aab8, all-targets build, `NUM_DRAFTS=2` (K=3) | nvidia/Qwen3.6-27B-NVFP4 @ 0893e160 | the published entry's configuration |
| **1 (secondary)** | Q0, Q1, X1 | as registered above | Qwen3.8-27B | the README's "28.3 to 28.6 tok/s" claim |

**Block M conditions.**

- Harness `inference-endpoint benchmark from-config --mode perf`, config `online_edge_full_run.yaml` edited ONLY
  for `model_params.name`, `model_params.tokenizer_name` (a local snapshot path), the endpoint, `report_dir`, and
  `num_trajectories_to_issue`. No other field changes; the edited configs are committed beside the results.
- **Declared deviation:** `num_trajectories_to_issue` = **4 of 20** (about 200 of 1,007 turns), the same
  trajectories for both arms (checked by comparing the per-turn ids in the two result files). The full run is
  about 2 h on Atlas and longer on llama.cpp; it is a follow-up, not this window. A 4-trajectory mean latency
  is an estimate of the 20-trajectory figure and is reported with the paired per-turn comparison, which cancels
  turn mix.
- M0 launch: `llama-server --model <gguf> --host 127.0.0.1 --port 8080 --ctx-size 32768 -np 1 --reasoning off
  --flash-attn on --n-gpu-layers 99 --seed 42`, alias `Qwen3.6-27B-Q4_K_M` (the harness README's command, host
  changed to loopback). **Declared difference:** build `daef7b6`, not the validated `cfff1fc`.
- M1 launch: `serve-amd.sh` with a LOCAL model path, `HOST=127.0.0.1`, `NUM_DRAFTS=2`, `GPU_UTIL` set so weights and
  cache stay under the 12 GiB memory guard (value recorded per run), max-batch 1. No repo id, so nothing is
  downloaded at serve time.
- **Declared differences from the published run:** ROCm 7.2.4 (theirs 7.13), about 105 GiB GTT (theirs about
  62.5 GB), Chatterbox TTS resident, a 4-trajectory subset. A latency within the band below is consistent with the
  published entry; it does not prove the hardware is identical.

**Block 1 ruler (like for like).** Both engines are timed by ONE new client, `tools/e146_speed.py`, over the
OpenAI-compatible streaming API: decode rate = (completion tokens - 1) / (last token time - first token time),
prefill rate = prompt tokens / time to first token (this includes one decode step, declared, and identical for
every engine). It reuses E138's CODE/CHAT prompts and E139's exact-token 8K/32K prompts. Server-reported timings,
where an engine has them, are recorded beside the client figure, never instead of it.

**Predictions, block M (field named).**

| # | field | prediction | basis |
|---|---|---|---|
| PM1 | `M1.serves` | YES on ROCm 7.2.4 | it built cleanly; the entry ran ROCm 7.13, so this is a real risk. A failure is recorded VOID and a private ROCm 7.13 SDK is a labelled follow-up |
| PM2 | `M1.mean_turn_latency_ms` | 5,500-9,500 | published 7,059 ms; subset and stack differ |
| PM3 | `M0.mean_turn_latency_ms` | 8,000-16,000 | 72 output tokens per turn at our measured 12.3 tok/s is 5.9 s, plus prefill of a growing context |
| PM4 | `M1 / M0` paired per-turn latency ratio | 0.45-0.90 | Atlas speculates (K=3) and the reference does not |
| PM5 | `M1.accuracy_inline` within `M0.accuracy_inline` | within 0.05 | different quantisation; published entry scored 0.862 on BFCL, a different accuracy set |
| PM6 | `M1.tps` (harness field) | 7-14 | published 10.216 |

**Bands (block M, fixed now).**

- **Published Strix Halo latency REPRODUCED** if `M1.mean_turn_latency_ms` is within +/-25% of 7,059 (5,294-8,824).
- **Atlas faster than the reference:** `M1/M0` <= 0.85, and consistent in at least 2 of 3 trajectory-quartile
  splits. **Not separated:** 0.85-1.15. **Reference faster:** > 1.15.
- The vendor page's tok/s figures are not run outcomes and are not scored; the gates file records how they compare
  with the source.

**Order in the window:** M0, M1, then Q0, Q1, X1. Stop rules and the 12 GiB guard are unchanged. An arm that
cannot start (guard, config, build) is VOID and recorded, never scored slow.

## AMENDMENT 2 - arm M1 could not load the checkpoint; two labelled follow-up arms (declared 2026-09-25 02:09, commit 8606fbf, before either ran)

**What happened.** Arm M1 (Atlas-Inf @ 2d1aab8 serving `nvidia/Qwen3.6-27B-NVFP4` @ 0893e160) loaded all 20.4 GB
of weights in 14 s and then failed at model build: `Expected FP8E4M3 for model.language_model.layers.0.mlp.gate_proj.weight,
got UInt8`. The log had already printed `Weight format: Fp8BlockScaled, NVFP4 variant: Fp8Dequanted`. Arm M1 is
**VOID as registered** and stays so: this engine version does not load the MLPerf entry's checkpoint here.

**Cause, found by reading the code (not by trial).** For `MIXED_PRECISION` checkpoints `nvfp4_detect.rs`
(`mixed_precision_variant`) sets `saw_nvfp4` only when a compute layer's `quant_algo` is exactly `"NVFP4"`. This
checkpoint labels its 193 MLP layers `W4A16_NVFP4` and its 208 attention layers `FP8`, so only `saw_fp8` is set and
the whole model is routed to the FP8 path. The MLPerf-era source snapshot in the results repository lacks the
`MIXED_PRECISION` branch entirely, so this is a statement about HEAD, not about what MLCommons recorded. Whether
the entry ran a different code version is not known: the snapshot's `serve-amd.sh` is a 21-line SCALE-era stub whose
default model is `Qwen/Qwen3.6-27B-FP8`, while the entry's `measurements.json` names the NVFP4 checkpoint.

**Follow-up arms (second window, after this one).** Neither replaces M1; each is scored on its own and labelled.

| arm | what | why |
|---|---|---|
| **M1p** | Atlas-Inf @ 2d1aab8 plus ONE change: `mixed_precision_variant` also counts a layer whose `quant_algo` ends in `NVFP4` (patch committed as `results/e146/w4a16-nvfp4.patch`) | what HEAD does with the smallest fix; **patched HEAD is not the vendor's code** |
| **M1s** | the MLPerf entry's shipped source, `mlcommons/inference_results_v6.1` @ 10ecdffd, `closed/Atlas_Inference/src/Halo/atlas`, built native HIP (`ATLAS_TARGET_HW=strix-hip`) | the code MLCommons recorded, reconstructed: the shipped scripts are SCALE-era, the entry's descriptor says native HIP |

- **M1s is a best-effort reconstruction and is declared so.** SCALE (Spectral Compute) is not fetched in this
  experiment because its terms are unread. If the snapshot has no native-HIP path, M1s is VOID and recorded.
  Serve flags for both: `--speculative --num-drafts 2` (K=3), `--max-seq-len 36864`, `--gpu-memory-utilization 0.60`,
  `--kv-cache-dtype bf16`, `--max-batch-size 1`, `ATLAS_W4A16_VARIANT=v1`, `ATLAS_FORCE_GLOBAL_GDN=1`, weights by local path.
- **Scoring.** PM2, PM4, PM5 and PM6 apply to each follow-up arm that serves, against the same bands, labelled M1p or
  M1s. The "published latency REPRODUCED" band is reported for the code actually run, never for "Atlas" in general.
  The paired ratio is computed against M0, which stays the reference.
- Arm X1 (Qwen3.8-27B NVFP4) is a different checkpoint and runs in this window as registered; if it fails the same
  way it is VOID and the amended `W4A16_NVFP4` finding applies to it as well.

**Bookkeeping fixes declared with this amendment.**
1. The per-arm bank step failed for every arm that produces a harness report: the commit hook's secret pattern matched
   the word "token" inside `events.jsonl` (12.7 MB of benchmark conversation text), and the script only logged the
   refusal. Nothing was lost; files are on disk and staged. The banked artefact per harness arm is the summary, the
   scores, the configs, the stdout and a compact `per-turn.json` (conversation, turn, latency, accuracy) that the
   scorer derives from `events.jsonl`, which stays local because it is large, public benchmark text and not a claim.
2. The failure mode was silent. Later window scripts print the hook's refusal to the terminal and record `BANK FAILED`.

## AMENDMENT 3 - the follow-up arms ran with prefix caching off; corrected configuration for both (declared 2026-09-25 04:46, commit e81c102, before the re-run)

**What happened.** Follow-up window 2 started arm M1p at 04:14:48. After 29.5 minutes it had completed 29 of 206 turns, **61 s per
turn**, against 12.9 s per turn for the llama.cpp reference (M0). At that pace the harness's 5,400 s cap would have ended the arm at about
90 turns. The server log shows why: startup printed `Prefix caching: disabled`, and each turn re-prefilled its whole conversation
(16,656 tokens in the last turn logged) in 2,048-token chunks of about 10.5 s each. I stopped the run at 04:45, so the gateway was down for
31 minutes, and the gateway was restored and verified at 04:45:47.

**Cause: my configuration, not the engine.** `--enable-prefix-caching` defaults to false, and for a hybrid model (48 linear-attention and 16
softmax layers) a full prefix skip also needs `--ssm-cache-slots` above zero; HEAD's `serve-amd.sh` defaults `SSM_SLOTS` to 0. The llama.cpp
reference caches prompt prefixes by default. The arms were therefore not configured symmetrically for a multi-turn agentic workload. That is
Rule 8 (F39) again: a benchmark measures a configuration, not a box.

**The aborted run is recorded, not scored.** Label `M1p0` ("patched HEAD, prefix caching off"): 29 of 206 turns, 61.0 s per turn from the
progress bar, no report written (killed). It is evidence for what the missing flag costs, and for nothing else.

**Corrected arms (re-run in a new window).**

| arm | change from Amendment 2 |
|---|---|
| **M1p** | add `--enable-prefix-caching` and `SSM_SLOTS=32` (with the existing `SSM_CKPT_INTERVAL=128`) |
| **M1s** | add `--enable-prefix-caching --ssm-cache-slots 32` (with the existing `--ssm-checkpoint-interval 128`) |

- 32 slots at 128 (2,048 tokens per snapshot) is about 4.8 GB and covers a 36,864-token sequence with room. The engine's own help recommends 16
  slots for multi-turn workloads; the higher value is a margin, not a tuned setting, and is recorded per run.
- Everything else, the bands and the predictions are unchanged. PM4 (0.45-0.90) was a prediction made assuming a working cache.
- A **harness time cap** stays 5,400 s. If an arm still cannot finish 206 turns in that time it is reported with the turns it completed and the
  paired comparison restricted to those turns; it is not extrapolated.
- **Scope of the correction.** Block 1 (X1) is unaffected: its prompts are distinct and decode-timed, so prefix caching could not have changed
  its CODE/CHAT figures. Its 8K/32K prefill rates were measured cold on purpose.

*Correction, 2026-09-25 04:48: the headers of Amendments 2 and 3 first carried times written from memory (02:20 and 04:55). Both are replaced by the commit times above; the declared content is unchanged and each was committed before the runs it governs.*
