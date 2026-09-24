# File: e139-prereg.md
# Purpose: Pre-registration for E139 - testing halogen-flash-server's published prefill and decode claims for Qwen3.8-Flash-Next on this box.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: The claim (the engine README's Measured table), what the public record and our own
# E91 logs already say, the arms (halogen 0.13.8 on its own checkpoint, halogen on our unsloth
# GGUF, mainline llama.cpp on the same GGUF), one speed+memory block and one identity check,
# predictions that each name the field they are scored against, and the stop rules. Written
# before any run; the weights were still downloading when this was committed.

# E139 PRE-REGISTRATION - does halogen-flash prefill 32K at ~1,424 tok/s on this box? (2026-09-24)

## The claim (owner-supplied workplan 2026-09-24, checked against the engine README)

The owner pasted a Gemini-generated deployment plan. Every flag, port and bench command it names
exists in the real README (`peonist-ai/halogen-flash-server`, fetched 2026-09-24). The figures
below are the README's own, not the plan's.

| # | part | README figure (0.5.3 unless noted) | testable here? |
|---|---|---|---|
| C1 | prefill @ 32,768 | **~1,424 tok/s** (TTFT 23.0 s) | yes - the headline, and "the column carrying the claim" per the README |
| C2 | prefill @ 8,192 | ~1,246 tok/s | yes |
| C3 | decode, serial greedy @ ctx 1,500 | 37.6 tok/s | yes |
| C4 | decode, MTP, served, @ ctx 32,768 | 41.7 tok/s (mean of ten prompts) | yes |
| C5 | ~4x faster end to end than other runtimes | 29.1 s vs 118 s (competitors' own figures, their machines) | yes, against OUR llama.cpp arm on the same box |
| C6 | temp 0 output byte-identical to serial greedy | stated, "verified on every release" | yes |
| C7 | 1M-context rows, agent-turn rows, prompt cache ~2 s follow-ups | 0.6.0 / 0.12.0 rows | not in this experiment |

## Public record at registration

- Engine: closed source, repo created 2026-08-26, 667 stars, 10 open issues at 2026-09-24.
  Image `ghcr.io/peonist-ai/halogen-flash-server:0.13.8` =
  **`sha256:6e626c979d536ab1edb07898e278be6686afd353758ea268817457f801d687dd`** (`:latest` pointed at
  the same digest on 2026-09-24). **Every arm runs by digest, never by tag.**
- Weights: `peonist-ai/halogen-qwen3.8-flash-next` @ `e053f488b120b99ed2525e6ac99f68c51b3b6179`,
  Apache-2.0 derivative of Qwen3.8-Flash-Next. Checkpoint 115.55 GiB (5.53 bpw across 179.55B
  params), needs ~68 GiB resident plus a 47.7 GiB FP8 n-gram table that is paged, not resident.
- Reference conditions (README "Measured"): ROCm 7.14.0, **~85 W sustained package power**,
  **IOMMU OFF**. The README measures IOMMU passthrough as costing 13-16% of prefill, and says it
  has NOT measured translated mode.
- Our box at registration: kernel 7.0.0-31, MemTotal 121.2 GiB, `ttm.pages_limit=29360128`,
  **IOMMU ON in translated mode** (`iommu_groups/0/type = DMA-FQ`), memlock hard limit ~15 GiB.
  The weight lock is opt-in and the engine "runs unlocked either way", so memlock does not block
  the default config. `amdgpu power1_average` is readable for the power record.
- **Our own prior figure:** E91 (build `daef7b687`, Vulkan, UD-IQ4_XS, relay down) prefilled a
  21,217-token prompt at **217.90 tok/s** (`results/raw/e91/e91-C-flashnext-low-l3.serverlog`).
  No `llama-bench` or decode leg has ever run on Flash-Next here (E91 results, line 108).

## Arms

| arm | engine | weights | config |
|---|---|---|---|
| **H0** | halogen @ digest above | shipped `w4b` + `overlay` sidecar | image defaults: KV pool 524,288, `MAX_TOK` 32,768, prompt cache on, MTP on. No `WEIGHTS_LOCK`. `HALOGEN_DOWNLOAD` unset (no outbound connections), models volume `:ro` |
| H0s | same | H0 + `overlay-speed` | labelled extra, the README's "speed arm" |
| **G0** | halogen @ digest | our `unsloth/Qwen3.8-Flash-Next-GGUF` UD-IQ4_XS (manifest line 1458) + `mtp.hgn` | the README's bring-your-own-GGUF path. Isolates ENGINE from QUANT against L0 |
| **L0** | mainline llama.cpp `daef7b687` (E91's build), Vulkan RADV | same UD-IQ4_XS | `-c 40960 -np 1 -fa on`, E91's KV types, offload gate per Rule 3 |

Declared: G0 and L0 share the file, so G0/L0 is the engine comparison; H0/G0 is the quant
comparison. The kernel and IOMMU are held fixed across all arms and recorded, not varied.

## Block 1 - speed + memory (the only scored speed block)

Measured through OUR client over HTTP, not the engine's own bench. Per arm, cold server, one
request per prompt, temperature 0, thinking off:

- **P32K**: one real-text prompt, 32,768 tokens by the model's own tokenizer (not chars/4),
  256 generated. Three reps, fresh prompt-cache state each (restart or distinct prompt prefix).
- **P8K**: same shape at 8,192.
- **D1500**: ~1,500-token prompt, 512 generated, once serial (drafting off) and once with the
  arm's default drafting.

Recorded per request: the response's `timings` (prefill and decode rates), client-side TTFT and
total wall time, peak `mem_info_gtt_used + mem_info_vram_used`, MemAvailable minimum, and
`amdgpu power1_average` sampled at 1 Hz. The engine's own `flash_serve bench` / `sweep` are
run once for H0 and recorded, **not scored** - the verdict comes from our client.

## Block 2 - identity (C6)

H0, the D1500 prompt plus the three P8K prompts, temperature 0, serial vs drafting on:
compare generated text byte for byte.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `H0.loads` | YES, serves `/health` 200 within 15 min of start, no memlock failure | lock is opt-in; 68 GiB + 35 GiB pool + working set fits 121 GiB with the gateway down |
| P2 | `H0.P32K.prefill_tps` (median of 3) | **1,000-1,300** | 1,424 less 13-16% for IOMMU, less more again for translated mode; power envelope unknown |
| P3 | `H0.P8K.prefill_tps` | 900-1,200 | same discount on 1,246 |
| P4 | `H0.D1500.decode_tps_serial` | 32-38 | decode is bandwidth-bound; the README says IOMMU does not move it |
| P5 | `H0.P32K.decode_tps` (drafting on) | 34-42 | 41.7 claimed; our prompts are not theirs |
| P6 | `L0.P32K.prefill_tps` | 150-230 | E91's 217.90 at 21K; mainline MoE prefill falls with depth |
| P7 | `G0.P32K.prefill_tps / L0.P32K.prefill_tps` | >= 3.0 | if the kernels carry the claim, it survives a shared file |
| P8 | `H0.P32K.total_s / L0.P32K.total_s` | <= 0.30 | the README's ~4x end to end |
| P9 | `H0.peak_gpu_mem_gib` (GTT+VRAM) | 95-115 | 68 resident + 35 pool + ~9 prefill arena |
| P10 | `H0.identity.byte_equal` | 4 of 4 prompts equal | stated guarantee; greedy verification cannot change a token |

**C1 is scored REPRODUCED if `H0.P32K.prefill_tps` >= 1,210** (1,424 less the README's own
upper IOMMU cost, 15%). Between 1,000 and 1,210 is scored REPRODUCED-CONDITIONALLY, attributed
to the IOMMU only if a later IOMMU-off arm closes the gap. Below 1,000 is NOT REPRODUCED.
L0's decode rate has no prior here: it is recorded, not predicted.

## Stop rules

- Container fails to start or never reaches `/health` 200 in 15 min: record the log, P1
  falsified, G0 still runs if the failure is checkpoint-specific.
- Memory guard: stop the arm if MemAvailable < 12 GiB (as E136, E138).
- L0 offload gate finds any layer on CPU: L0's speed is void, not slow.
- Any run concurrent with the gateway or another GPU job is void (Rule 9). The gateway is down
  for the whole window via `relay_bench_window.sh down`.

## Out of scope, by decision (not owed)

- **Kernel command line changes** (`amd_iommu=off`, `ttm.pages_limit=32505856`): sudo, a
  reboot, a security trade-off, and a new bench variable. They are the owner's call, and only
  worth asking for if P2 lands in the conditional band.
- **BIOS UMA carve-out:** already minimal here (121.2 GiB visible).
- **Routing agents at it** (workplan Phase 5): the routing guide changes only after quality
  is measured. F116 already found Flash-Next matches the incumbent on quality for 5.6x the
  memory; a speed win does not change that on its own.
- **Quality banks:** no quality block is registered. If H0 reproduces C1, quality on the F116
  banks is the next amendment, declared before it runs.

## AMENDMENT 1 - runner design (declared 2026-09-24, before any run; weights still fetching)

Tools: `tools/e139_prompts.py` (prompt set), `tools/e139_speed.py` (one arm),
`tools/run_e139_window.sh` (the window). Five things the build pinned down that the registration
left open. **No prediction, range or scoring bar changes.**

1. **Prompts are fixed and committed.** `results/e139/prompts.json`: this repo's own long-form
   docs, encoded once with the checkpoint's `tokenizer.json`, cut into NON-OVERLAPPING windows so
   no request hits another's prefix cache. Content lengths 32,768 / 32,767 / 32,768 (P32K),
   8,192 x3 (P8K), 1,500 (D1500), closing question included; chat-template overhead is whatever
   `timings.prompt_n` reports. Thinking off on every request (`chat_template_kwargs`).
2. **TTFT is the server's `prompt_ms`, not a client-side stream timestamp.** Requests are
   non-streaming so both engines return the same `timings` object. Client wall time per request
   is recorded and is the `total_s` P8 is scored on.
3. **Block 2 runs on its own server, arm H0-id, with `HALOGEN_PROMPT_CACHE=0`.** The README
   documents the default cache mode as NOT giving byte-identical repeat answers, and the serial
   and MTP requests necessarily repeat a prompt. Under mode 2 a mismatch could not be told
   from a cache effect. Drafting is switched per request (`"drafter": "serial" | "mtp"`).
4. **The KV pool is sized by the image at startup** (`HALOGEN_HOST_RESERVE_GIB` default 20),
   not fixed at 524,288 positions. H0 keeps image defaults; `/health` is recorded per arm. P9
   is unchanged.
5. **P32K rep 0 is the first long prompt after a start**, so it pays cold reads of the 47.7 GiB
   lookup table (README: ~1.3 s on NVMe). It is recorded as-is; the median of three is what is
   scored.

Order: H0, H0-id, H0s, G0, L0, then the image's own `bench` and `sweep` (recorded, not
scored). Power is `amdgpu power1_average` at 1 Hz, averaged per request.

## AMENDMENT 2 - the box is never GPU-empty: Chatterbox TTS stays resident (declared 2026-09-24 21:05, before any E139 run)

**Trigger:** the first E139 window attempt (20:58-21:00) refused to start. `relay_bench_window.sh down` stops
only the gateway unit; `chatterbox-gateway` (a `spark-infer` podman container, up 3 days, on `/dev/kfd`)
keeps running and held **8 GiB of amdgpu GTT** for the full 150 s wait, with no `llama-server` and no
visible container (`podman ps` as agent-spark cannot see another user's containers). The "GTT under 4
GiB" gate could therefore never pass. No model ran; the gateway was restored and verified 21:01:03.

**Decision:** Chatterbox is NOT stopped. The window grant covers the gateway unit only, and stopping a
TTS service is the owner's call. Changes, all before any run:

1. The refusal gate becomes **GTT < 10 GiB** (the 8 GiB baseline plus 2 GiB of slack), still refusing on any
   `llama-server` or visible container.
2. The window-open baseline (GTT and VRAM) is recorded in `results/e139/window.log` and in every arm.
3. **P9 is scored net of that baseline**, not as an absolute reading.
4. **Declared confound:** every arm has about 8 GiB less GTT available than the README's clean measurement,
   and the earlier E138 and E143 windows ran with the same resident Chatterbox. If H0 fails to load or shows
   a memory-shaped anomaly, this is the first suspect; the fallback is a re-run with Chatterbox stopped by
   the owner, recorded as a separate arm rather than a substitution.

## AMENDMENT 3 - G0 was killed by the memory guard; one retry with a smaller KV pool (declared 2026-09-24 21:20, before the retry)

**Trigger:** arm G0 (Halogen on our unsloth GGUF) died at 21:11:27 with container rc=137. The cause is
the memory guard, not the engine: `mem_guard.sh` (floor 12 GiB, 1 s poll) fired at **MemAvailable 11,356
MiB**, having fallen 112 GiB -> 80 -> 58 -> 41 -> 11 GiB over the load. Halogen had repacked all 70.55
GiB of the GGUF and registered it, and was reserving the KV pool (262,144 positions) when the guard
fired. The 70.55 GiB repack, the KV pool and the resident Chatterbox TTS (amendment 2) share 121 GiB.

**Status of G0 (attempt 1):** VOID by memory guard. It is not a failure of the engine and not a result.
The guard floor is the protection against the RAM exhaustion that reset this box in E136 and is NOT
lowered.

**Retry (arm G0k), one attempt, declared now:** the same command as G0 plus
`HALOGEN_KV_POOL_POSITIONS=65536` (Halogen's own log names this setting, and says a smaller pool leaves
each request's speed unchanged). 65,536 positions still covers the 32,780-token P32K prompt with room
for its output. Expected saving about 5 GiB of the 12 GiB floor's margin. Run in a second, short window
after this one closes.

- **Scored for P7 only**, and only if it completes. If the guard fires again, G0 is recorded
  VOID-by-memory, **P7 is unscorable on this box**, and there is no third attempt.
- The KV pool size is a labelled difference from H0/H0s/L0 (262,144 / n/a) and is reported beside the
  P7 ratio. It is not expected to move prefill speed; that expectation is itself unverified.

## AMENDMENT 4 - G0k was a config error, not a memory result; retry G0m with the vendor's own lever (declared 2026-09-24 21:40, before the retry)

**Trigger:** arm G0k (amendment 3) exited rc=1 after **6 seconds**, before loading anything. The engine
rejected the flag: `--kv-pool 65536: at least --ctx 262144`. The KV pool cannot be smaller than the
context window, so amendment 3's lever was invalid. **The memory guard did not fire and no memory
outcome was measured.** G0k is void as a config error; it does not use up amendment 3's "one attempt",
which was defined as an attempt that reaches the memory question.

**Retry (arm G0m), one attempt:** G0 with `HALOGEN_MAX_TOK=16384` and the default pool. The engine's own
startup log names this as the fix for a host short of RAM: "halves the prefill arena", about 9 GiB back,
"for about 9% of prefill speed". About 9 GiB is more than the 5 GiB the pool change would have given
against a 12 GiB guard floor that G0 missed by 0.9 GiB. The guard floor stays at 12 GiB.

- **Declared bias:** the vendor's 9% prefill cost applies to G0m only, and pushes its 32K prefill DOWN,
  so P7 (`G0.P32K.prefill_tps / L0.P32K.prefill_tps` >= 3.0) is scored on G0m with the 9% stated beside it.
  L0 measured 216.5 tok/s, so G0m needs about 650 tok/s to pass; H0 (a different file) measured 1,152.
- The engine also refuses the last pin under 16 GiB MemAvailable. A clean refusal at that point is a
  valid outcome: G0 is then recorded infeasible on this box at this memory state, P7 is unscorable, and
  there is no further attempt. A second guard kill is the same outcome.
