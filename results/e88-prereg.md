# E88 - SparkMax absolute inference baseline and latency-budget allocation

Pre-registered 2026-08-29, BEFORE any run. Amendments are declared inline and
dated. Each prediction names the FIELD it is scored against, so it reads one way.

## Question

Is SparkMax's thin-path inference materially below its hardware class, or is the
poor interactive experience dominated by a higher layer (context size, client
payload, model behaviour, agent harness)?

## Frozen baseline - NOT tuned in this experiment

The deployed relay config, observed directly on PID 1068495 at 14:0x:

    -m /opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf \
    -c 98304 -fa on -ctk q8_0 -ctv q8_0 --jinja

Build: `b9865` / `067de9371`, Vulkan (RADV GFX1151). **The sparkbench bench build
and the sparkrouter serving build are the same commit** - verified by
`--version` on both binaries - so a thin-path figure here describes production.

Kernel `7.0.0-29-generic`, livepatch `nothing-to-apply`. Mesa/RADV per F57.

## Box-state gate (new instrument, and the reason it exists)

At 14:05 the GPU was measured at 85-95% busy, sclk pinned 2529 MHz, 78 W, 77 C,
with the `chatterbox-gateway` TTS container resident (5.68 GB VRAM via
`rocm-smi --showpids`). The owner confirmed at 14:11 that that job "just
finished". It was real work, not a sensor artefact - two independent rulers
(sysfs `gpu_busy_percent`/hwmon, and `rocm-smi`) agree once sampled at the same
time.

**Consequence: every leg records GPU busy/sclk/power/temp DURING the run, and a
leg whose pre-gate is not quiet is marked contended rather than averaged in.**
An uncontended baseline that silently includes a TTS batch is the failure this
gate prevents.

**Known, stated deviation:** the relay cannot be stopped from this account
(`/var/lib/sparkrouter` is 0750 spark-infer, the unit is a systemd *user* unit,
and `sudo` requires a password here). It therefore stays RESIDENT but IDLE
during the legs, holding ~25.9 GiB GTT and doing no compute. This is a Rule 9
deviation and is declared, not hidden. Its size is bounded empirically by the
reproducibility control below.

## Arms

**Phase A - thin path, no server, no agent.** `llama-bench`, fresh process per
leg, production model/quant/build/backend, production KV flags
(`-fa 1 -ctk q8_0 -ctv q8_0`), `-r 3`, depths 0 / 4096 / 8192 / 16384 / 32768 /
49152, `-p 512 -n 128`.

**Phase B - context tax through llama-server at the frozen flags.** Own server,
non-production port, exactly the production flag string. Prompt lengths ~1k, 4k,
8k, 16k, 32k, 46k measured in TOKENIZER tokens (never chars/4). `cache_prompt`
disabled and a unique prefix per request, because the prompt cache is part of the
config (F96) and would otherwise manufacture a flat curve. Scored fields come
from llama.cpp's own `timings` object: `prompt_n`, `prompt_ms`, `predicted_n`,
`predicted_ms`, plus wall-clock TTFT from a streaming request.

**Phase C - client workload characterisation.** The four surviving VERBATIM
Claude Code captures (`req-00{1..4}`, 183 KB and 159 KB) replayed against the
same server, plus aider and the simpleloop local provider. Fields: input tokens,
serialised tool-schema bytes, tool count, requests actually served, TTFT, total.
Synthetic probes are excluded - F104 records that every synthetic probe built
gave the opposite answer to the real artefact.

## Controls - these decide whether the instrument is observing real work

| control | purpose | pass condition |
|---|---|---|
| **C1 positive - CPU-only** | prove the instrument sees the GPU at all | `-ngl 0` at depth 0 is >=5x slower on `tg128` than the GPU leg |
| **C2 reproducibility** | bound run-to-run noise AND the idle-relay deviation | depth-0 leg repeated in a FRESH process lands within +/-1.5% on `tg128` (F15 noise floor) |
| **C3 requests-served** | prove the model actually spoke | `grep -c 'slot launch'` > 0 on every Phase B/C server log; zero means the row is a stack elimination, not a latency figure (F103) |
| **C4 quiet gate** | prove no co-resident job is contending | `gpu_busy_percent` == 0 and sclk == 600 MHz immediately before each leg |

## Predictions, each naming its scored field

- **P1** - Phase A `tg128` at depth 0 lands in 45-75 tok/s. *Field: llama-bench
  `t/s` on the `tg128` row, depth 0.*
- **P2** - Phase A `pp512` at depth 0 lands in 450-750 tok/s. *Field: llama-bench
  `t/s` on the `pp512` row, depth 0.*
- **P3** - decode degrades with depth by less than 2x from depth 0 to depth
  49152. *Field: ratio of `tg128` t/s at depth 0 to `tg128` t/s at depth 49152.*
- **P4** - prefill degrades with depth by MORE than 2x over the same span,
  reproducing the 605 -> 252 tok/s already observed. *Field: ratio of `pp512` t/s
  at depth 0 to `pp512` t/s at depth 49152.*
- **P5** - C1 fires: CPU-only is >=5x slower. *Field: `tg128` t/s ratio.*
- **P6** - the Claude Code capture's input tokens exceed the aider figure by more
  than 20x. *Field: `prompt_n` from the server `timings` object on each replay.*
- **P7** - first-turn wall time for the real Claude Code capture exceeds 100 s.
  *Field: measured TTFT seconds on the streaming replay.*

## Decision rule, registered before the data

- If Phase A depth-0 `pp512` and `tg128` land within **25%** of credible
  published figures for the same silicon class / backend / model / quant, the
  hardware-runtime branch **CLOSES** and the report allocates the remaining
  latency to the higher layers.
- If either lands **more than 25% below** that band, the hardware-runtime branch
  **OPENS** and the report names the next investigation boundary (backend choice,
  driver, clocks, memory bandwidth) rather than proceeding upward.
- A peer figure whose model, quantisation, backend or context differs is recorded
  as a MISMATCH and does not enter the band. If no credible like-for-like peer
  exists, that is reported as unresolved - not filled in with an unlike one.

## Out of scope, deliberately

Coding capability is NOT scored. No toy coding success is admitted as evidence of
agent quality. No serving flag is changed.
