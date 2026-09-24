# Incident: gpt-oss-120b hangs in decode, and it is NOT the known deadlock

**Date:** 2026-08-19, 06:42-06:56 · **Host:** sparkmax · **Severity:** run lost,
box unharmed, no reboot needed
**Status:** unresolved. The arm must be re-run after a diagnosis; the failed run
must NOT be recorded as a capability result.


## What happened, in one paragraph

We loaded `gpt-oss-120b-mxfp4` (59.03 GiB, three shards) to run it against the
L3-hard document tier. The model loaded **completely and correctly**. The first
question was accepted, tokenized, and began decoding. Then the server stopped
responding and stopped logging, while holding 64 GiB of memory, and never
recovered. Twelve minutes later it was killed; all twelve questions are recorded
as `transport_failed`. **The box was never at risk and no power cycle was
required.**


## Why this matters more than one lost run

We ran this attended specifically because 59 GiB is near-edge for a documented
amdgpu suballocator deadlock that can only be cleared by physically power-cycling
the machine. **This was not that failure.** Establishing the difference quickly
is what turned a potential hard reset into a `pkill`.


## It is not the known deadlock, on every axis

`docs/memory-edge-deadlock.md` gives a six-signal fingerprint. This matched
**none** of them.

| signal | documented deadlock | observed here |
|---|---|---|
| process state | **`D`** (uninterruptible) | **`S`** - all 9 threads |
| killable | **no** - `SIGKILL` is inert in that path | **yes** - `pkill -x` cleared it in under 5s |
| VRAM | parks at exactly **2.00 GiB** (2,147,483,648 B) | 1.90 GiB, never parked |
| when it strikes | **during load**, never reaches inference | **after** a complete load, during decode |
| VmRSS | collapsed to ~30-57 MB | model fully resident |
| recovery | **hard power cycle** | killed normally; GTT reclaimed 64.07 -> 22.57 GiB |

**Caveat, stated rather than glossed:** a different fingerprint is not proof of a
different root cause. Both failures involve amdgpu at near-edge model sizes, and
this has been observed exactly once. What is established is that it is a
different *failure mode*, and specifically **not the one requiring a reboot**.


## What the evidence shows

Everything up to the point of decode succeeded:

- **Device:** `Vulkan0 (AMD Radeon Graphics (RADV GFX1151))`, 111,067 MiB free
- **Full-offload gate: PASSED** - 74 layer assignments, all `Vulkan0`, zero on CPU
- **Shards verified** against manifest byte counts before loading: 12,980,384 /
  31,738,487,200 / 31,635,878,880
- **Memory preflight: PASSED** - 111 GiB available against a 70 GiB floor
- **Context preflight: PASSED** - longest prompt 3,300 tokens, `max_tokens` 4,096,
  needed 7,396 of 32,768, headroom **25,372**
- **Model resident:** GTT reached **64.07 GiB**, `read_bytes` 57.65 GiB
- **`n_ctx_train` = 131,072**, `arch = gpt-oss` - both as expected
- **Request accepted and decoding:** the server logged
  `cached n_tokens = 61`, created a context checkpoint, and posted
  `decode: n_batch (effective) = 2048`

Then the serverlog **stopped growing at 06:43:24**, roughly 29 seconds after the
server came up, while the HTTP connection stayed open. The client sat on that
request for **754.95 seconds** before receiving
`Remote end closed connection without response` when the process was killed. The
remaining eleven questions failed as `Connection refused`.

**The 0/12 score is `transport_failed` twelve times over. It is an instrument
failure and is not a measurement of this model's capability.** Recording it as
0/12 would be the artefact-as-finding error this programme exists to catch.


## Hypotheses, and the one I already discarded

**DISCARDED - chat template.** My first suspicion was that gpt-oss needs OpenAI's
Harmony format and we served it without a template flag. **The log disproves
this:** llama.cpp loaded the correct template from the GGUF, logging
`chat template, example_format: '<|start|>system<|message|>You are ChatGPT, a
large language model trained by OpenAI.'` and `thinking = 1`. The template was
right.

**Live hypotheses, untested:**

1. **A compute hang in the Vulkan/RADV backend at this size or with MXFP4.**
   Logging stopping mid-decode while threads stay in interruptible sleep is
   consistent with waiting forever on a GPU fence. This is the leading candidate.
2. **Reasoning runaway with no output.** `thinking = 1`, and this family has an
   analogue we have already measured: F71, where Qwen3.8 at `xhigh` burned
   100,000 tokens over 2h 46m and returned nothing. Against this: a reasoning
   runaway still logs and still consumes CPU, and logging ceased entirely.
3. **Something specific to a 3-shard MXFP4 model on this build.** The only
   large-MoE arm we have run recently on build 770 / `9e40df63b`.


## The next diagnostic, and why it is cheap

**A smoke test, not another 12-question run.** One ten-token prompt, `max_tokens`
of 32, and a hard 120-second timeout. That distinguishes hypothesis 1 from 2
immediately:

- **No tokens at all, logging stops** -> a compute hang (hypothesis 1)
- **Tokens appear but never finish** -> reasoning runaway (hypothesis 2)

If it is a compute hang, worthwhile follow-ups in order of cost:
`-b 512 -ub 128` (the F72 flags that fixed large-pack loads for Qwen3.8),
then a smaller context, then checking whether the same model runs at all under
`llama-cli`-equivalent single-shot serving.

**Do not re-run the L3 tier until a smoke test produces a single token.** A
twelve-question run against a model that cannot emit one is 12 minutes of
`transport_failed` and no information.


## What this changes about the plan

**Nothing about the priority order.** GLM-4.7-Flash was already the highest-value
open question and it remains so - its confirmation arm started at 06:56:15, on
the same GPU, immediately after this was cleaned up.

gpt-oss-120b's role was always **conditional**: it tests whether much larger
total MoE capacity fixes the hard-tier weakness, and it matters less if GLM
confirms at 11-12/12. That conditionality is now doing useful work - the
diagnosis can wait behind a result that may make it unnecessary.


## Operational notes worth keeping

**The guard chain behaved correctly throughout.** Rule 9 refused to start GLM's
arm while the 120b server was up, preventing two GPU consumers and the memory
contention that is the documented deadlock trigger. Shard sizes and available
memory were both checked before the load. The watchdog correctly reported **no
deadlock** rather than crying wolf.

**One real defect was found and fixed in the monitoring itself.** The check
script initially reported `SUSPICIOUS` throughout normal loading, because `D`
state is the *normal* condition while reading 59 GiB from disk - the `wchan` was
`folio_wait_bit_common`, an ordinary page-cache wait. A check that alarms
constantly during normal operation trains its reader to ignore it, which is worse
than no check.

**A second defect was found in the logging.** Several scripts used
`echo "=== $(date -Is) rc=$? ==="`, but `$(...)` command substitution **resets
`$?`**, so those lines reported the exit status of `date` rather than of the
command being checked - a python process that exited 2 was logged as `rc=0`.
Corrected to capture into a variable first. No conclusion in the record rests on
one of those values: the two model downloads it affected were independently
verified by exact byte count and SHA256 against their pinned upstream oids.


## Evidence

- `results/raw/e61-20260819-gptoss120b-l3n0.json` - all 12 `transport_failed`
- `results/raw/e61-20260819-gptoss120b-l3n0.serverlog` - 227,460 bytes, last
  written 06:43:24
- `docs/memory-edge-deadlock.md` - the fingerprint this was checked against
- `tools/is_it_stuck.sh` - the check, with its reasoning in the header
