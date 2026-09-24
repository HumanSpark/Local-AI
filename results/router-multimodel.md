# E34: llama.cpp router mode - multiple models on call (2026-07-17)

# File: results/router-multimodel.md
# Purpose: Does llama.cpp's router mode give us multiple models loaded on call, safely, on this box?
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Alastair asked what a Mistral swap costs and whether models could be loaded "on call".
# This llama.cpp build (v200, 067de93) has a built-in ROUTER MODE, so the answer needed measuring
# rather than designing. Result: it works, both models sit resident at 41.04 GiB at production
# context, switching is 0.04s, and per-model presets solve the tool-template gap that a single
# global flags line could not. Constraint: 2 models is the safe cap - 3 lands on the memory edge.
# Box constraint honoured throughout: nothing approached the ~60 GiB deadlock edge; D-state 0 all run.

## Question

The gateway serves ONE model (`serving.conf` -> one `LLAMA_MODEL`, one `LLAMA_SERVING_FLAGS`), so
routing today means a blue/green swap. Can the box instead hold several models and route per request?

## Method

`llama-server` launched with NO model = router mode. Model sources are the HF cache, `--models-dir`,
or `--models-preset`. **Preset-only was chosen as a safety property, not a convenience:**
`--models-dir /opt/models/staging` would expose all ~70 GGUFs there - including Qwen3.5-397B and
other 100 GB+ artefacts - to `--models-autoload` (default enabled, `--models-max` default 4). That
combination could load straight through the ~60 GiB memory edge and wedge the box. A preset names
exactly the models allowed, so the router cannot discover anything else.

Preset (`version = 1`, `[*]` globals + one section per model, keys = long flag names without dashes;
`load-on-startup = false` so nothing loads until called):

```ini
version = 1
[*]
c = 49152
no-webui = true
[workhorse]
model = /opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf
load-on-startup = false
[mistral-24b]
model = /opt/models/staging/Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf
chat-template-file = /home/agent-spark/sparkbench/results/tool-use/mistral-v7-tool.jinja
load-on-startup = false
```

Run attended, gateway paused (HARNESS-RULES rule 3), `--models-max 2`, KV bounded explicitly
(rule 4), disk quiet (rule 1). Routing is by the `"model"` field in the request body.

## Results

### Memory and switching (production context, c = 49152, 4 slots)

| State | GTT | D-state | Latency |
|---|---|---|---|
| Router idle (nothing loaded) | 0.02 GiB | 0 | - |
| workhorse loaded on demand | 20.21 GiB | 0 | 4s cold |
| **+ mistral-24b, BOTH resident** | **41.04 GiB** | 0 | 4s cold |
| switch back to workhorse | 41.04 GiB | 0 | **0.04s** |
| after teardown | 0.02 GiB | 0 | - |

The workhorse's 20.21 GiB matches the production gateway's footprint exactly - an independent
consistency check that the router is not doing anything unusual to allocation. Mistral adds
20.83 GiB. Loading is on demand: nothing is resident until a request names it.

### Routing works

`/v1/models` advertises `workhorse`, `mistral-24b`, `default`. Requests routed by name reached the
right model (workhorse: "I am Qwen."; mistral-24b: "I am Mistral."). Once resident, a model answers
in **0.04s** with no reload - that is the "on call" property.

### Per-model presets solve the tool-template gap

| Mistral config | Plain chat | Tool call |
|---|---|---|
| GGUF's own template (no override) | works ("I am Mistral.") | **REFUSES** - "I'm unable to directly create or manipulate files" |
| `chat-template = mistral-v7-tekken` (BUILT-IN) | **BROKEN - pretraining garbage** | not reached |
| `chat-template-file = mistral-v7-tool.jinja` (E33's hand-written) | works | **WORKS** -> `create_document` |

Three things follow:

1. **E33/F38 is independently reproduced.** Mistral-Small-3.1 refuses tool calls on its own template,
   with the same refusal string E33 recorded, reached by a completely different serving path.
2. **The built-in `mistral-v7-tekken` template is a TRAP for this model.** Setting it produced forum-post
   continuation garbage - the exact fingerprint of F37's chat-template packaging bug, from a different
   cause: F37 had a MISSING template, this is a WRONG one overriding a working one. The built-in list
   containing a plausible name does not mean it fits your GGUF. Use E33's file.
3. **The per-model flags gap is closed.** `serving.conf` has one global flags line, so a Mistral swap
   would silently lose tool use (the flags Mistral needs are not the flags the workhorse needs). A
   preset carries `chat-template-file` per model, and Mistral then does tool calls AND still chats.

## Constraints and caveats

- **2 models is the safe cap on this box.** 41.04 GiB for two leaves ~19 GiB of headroom under the
  ~60 GiB memory edge (F24). A third at ~20 GiB lands ON the edge - the regime that needs a physical
  power cycle to clear. `--models-max` defaults to 4; that default is unsafe here and must be set to 2.
- **`--models-dir` is unsafe on this box** while /opt/models/staging holds 100 GB+ artefacts and
  autoload is on by default. Preset-only, or a curated directory.
- **llama.cpp calls router mode EXPERIMENTAL** and warns "not recommended to use this mode in
  untrusted environments". The gateway is LAN-facing (behind Caddy + forward_auth), which is not
  untrusted, but this is a real caveat for a production swap-in and is the reason this is a measured
  option, not yet a recommendation.
- Not tested: concurrent inference against BOTH models at once (GPU contention, and the F17
  concurrency knee); sustained multi-hour residency; the router's unload/TTL behaviour under
  `--models-max` pressure; whether tool use survives multi-round chains on Mistral (E33 flagged its
  chain score as template-confounded, and that confound is not resolved here).

## What this changes

The routing guide's "the swap costs more than the quality difference on any single short job" is a
statement about `model_swap.sh`, and the router removes the premise: with both models resident,
picking a model per request costs 0.04s and one JSON field. That makes task-shaped routing viable
where today only session-shaped routing is. It is not adopted yet - the experimental warning and the
untested items above are the gap between "measured working" and "serving production".

Evidence: this file; preset + logs in the session scratchpad (transient); reproduced against
llama.cpp v200 (067de93). Related: F38/E33 (tool use, reproduced here), F37 (the template-garbage
fingerprint), F24/memory-edge-deadlock.md (the ~60 GiB cap that sets `--models-max 2`), F39 (the
single-source-of-truth serving config this would extend).
