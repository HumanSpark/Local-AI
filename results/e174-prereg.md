<!--
# File: results/e174-prereg.md
# Purpose: Pre-registration for E174 - does a q8_0 KV cache help or hurt Flash-Next (a hybrid model with few attention layers) on llama.cpp?
# Project: sparkbench | Date: 2026-11-23
#
# Overview: Spike promoted from the scouting substream (scouting/inference-optimisation-skill/REPORT.md, "SPIKE one
# claim"); owner 2026-11-23: "The KV cache spike, run that please." One llama-bench grid on the newest llama.cpp build,
# three depths, f16 vs q8_0 K and V caches. Written before any GPU work.
-->

# E174 PRE-REGISTRATION - KV cache type on Flash-Next (llama.cpp)

## In plain English

The model's short-term memory of a conversation (the KV cache) can be stored at full precision or squeezed to half
the size. On the model we used to serve, squeezing it cost a little speed on short chats and gained speed on long
ones (F16). A community tuning guide claims the opposite on newer "hybrid" models, which keep that memory in only a
few layers: there, squeezing it made answers come out much slower. Flash-Next, the production model, is one of those.
We measure it ourselves.

## What is measured

- **Model:** Qwen3.8 Flash-Next, unsloth UD-Q4_K_XL, 4 shards, 111,334,654,784 B (103.7 GiB), restored 2026-11-23 from
  the lanhost archive and checked against the archive's sha256 list (`results/e174/restore.log`). MANIFEST entries
  from 2026-11-04 stay authoritative for provenance.
- **Engine:** llama.cpp `94f3af3d0` (the E172 build, newest here), `llama-bench`, `-ngl 999 -fa on`, via
  `tools/run_step8_leg.sh` (thermal capture).
- **Not production:** production serves Flash-Next on Halogen, not llama.cpp. This answers "which KV type for
  Flash-Next on llama.cpp" (the fallback engine and the community's default), not a Halogen setting.
- **Grid:** `-ctk f16,q8_0 -ctv f16,q8_0` (4 combinations; the matched pairs are scored, the mixed two are reported),
  tests pp512 and tg128, `-r 3`. **Depths 0, 8192 and 32768 run as three separate invocations** (CLAUDE.md: models
  over ~60 GiB split depth invocations).
- **Guards (F193, weights over 60 GiB):** relay window `idle-down`; GTT back to baseline before each invocation; no
  other disk I/O (restore and hashing finished first, E173 waits); owner present (2026-11-23 evening); stop at any
  DeviceLost or non-zero rc and reboot before any further GPU load. Kernel 7.0.0-43, no GPU fault in this boot's
  kernel log at 20:3xZ.

## Predictions (each names its field)

Fields are llama-bench `t/s` means, matched pairs only: `tg128@dN[f16]` = ctk=ctv=f16, `tg128@dN[q8_0]` = ctk=ctv=q8_0.

1. **P1 (the guide's claim, at short context):** `tg128@d0[q8_0]` is more than 5% below `tg128@d0[f16]`.
2. **P2 (F16's pattern, at long context):** `tg128@d32768[q8_0]` >= `tg128@d32768[f16]`.
3. **P3 (prefill):** `pp512@d0[q8_0]` is within 3% of `pp512@d0[f16]` (either direction).

Noise floor ±1.5% (F15); a difference inside it is reported as "no difference", not as a direction.

## What would change a decision

- P1 true and P2 false: q8_0 is a loss everywhere on this hybrid; any llama.cpp Flash-Next serving keeps f16.
- P2 true: q8_0 stays the long-context lever for hybrids too, and halves KV memory.

## Run log

- **Attempt 1, 2026-11-23 20:26:20-20:26:51Z: DeviceLost during the d0 model load** (6 s in), before any measurement:
  `radv/amdgpu: Not enough memory for command submission` -> `ggml_vulkan: device lost` -> `vk::Queue::submit:
  ErrorDeviceLost`. GTT baseline 17 MiB, GTT total 114,688 MiB, weights 103.7 GiB; `free -g` straight after: 68 GB
  buff/cache (the restore's sha256 pass read all 111 GB minutes earlier). Cause NOT established; page-cache pressure on
  GTT allocation is a hypothesis. No figures; no prediction scored. Runner stopped as designed; reboot required.
- **Attempt 2 (under A1), 2026-11-23 20:57:06-21:11:25Z: all three depths rc 0.** Eviction freed 77,034 MiB after
  idle-down (Cached 83,472 -> 6,438 MiB) and left 1-6 GB cached before each load. Scored in `results/e174-results.md`.

## Amendments

- **A1 (2026-11-23 ~20:55Z, before attempt 2, after a clean reboot at 20:32Z):** attempt 2 adds one step - after
  `idle-down` and before every depth invocation the runner evicts `/opt/models/staging` from the page cache
  (`tools/evict_page_cache.py`, `posix_fadvise DONTNEED`; bench has no root for `drop_caches`) and logs
  used/free/cache. Purpose: test the attempt-1 hypothesis. Reading: attempt 2 passes with cache low -> page cache
  is the likely trigger (not proven: one run); attempt 2 DeviceLosts with cache low -> the hypothesis is falsified
  and a 103.7 GiB load is past this box's edge on llama.cpp Vulkan, itself the finding. One retry only, owner at the
  power button. Grid, depths and predictions unchanged.
