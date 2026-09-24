# File: e143-prereg.md
# Purpose: Pre-registration for E143 - the coding models a Strix Halo chat recommended (Qwen3.8 Flash, the 27B, a 35B-A3B) run through Aider on our three real repo tasks, against our incumbent coding model.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: The owner asked a Strix Halo chat for preferred coding models and got "Qwen 3.8 flash",
# "27b, with the 35b variants for little stuff". This tests those picks on the one coding
# instrument that is not saturated (F151) and not rotted (F152): tools/aider-tasks.json, three real
# tasks, independent verify. Four arms, ONE build, solo serving, relay down. Written before any run.

# E143 PRE-REGISTRATION - chat-recommended coding models through Aider (2026-09-24)

## The question

Do the models a Strix Halo chat recommends for coding do real repo work through Aider on this box
at least as well as our incumbent, and at what time cost? This measures the RECOMMENDATION on OUR
tasks. It does not measure what the chat's users tested or how.

## What this instrument can and cannot do (declared now)

- Three tasks x three repeats = **9 attempts per arm**. It can show a large gap. It cannot rank
  models a few points apart, and a 9-attempt pass count is not a rate.
- **T3 is known to fail through an APPLICATION fault, not a capability one** (F152: the model
  proposed the right change and Aider mis-applied it). Expect it to fail everywhere; it is kept
  because dropping it after seeing the result would be choosing the bank.
- The independent `verify` is the only signal. Aider's exit status is not evidence (F113, F152).

## Arms (all on llama.cpp `daef7b6`, served solo, relay down)

F117: a new model forced a build change, so EVERY arm runs on `daef7b6`, including the incumbent.
E113's 2/3 was measured on `b10435` and is not reused as a baseline.

| arm | model | why it is here |
|---|---|---|
| **A** | Qwen3.8-27B Q4_K_M | chat pick #2; our `local_smart`; E113 baseline (2/3 on b10435) |
| **B** | Qwen3.8-Flash-Next UD-IQ4_XS (3 shards, 87.25 GiB) | chat pick #1 ("Qwen 3.8 flash") |
| **C** | Qwen3.6-35B-A3B UD-Q4_K_XL (20.8 GiB) | chat pick #3 ("35b variants for little stuff") |
| **D** | Qwen3-Coder-30B-A3B Q4_K_M | our incumbent coding default (control) |

**Assumption on C, stated so it is cheap to correct:** "35b variants" is taken to mean Qwen's
official 35B-A3B, which is the 3.6 generation (`Qwen/Qwen3.6-35B-A3B`); under the 3.8 name only
community "Distill" variants exist. The file is the one already pinned and verified in
`manifests/MANIFEST.md` on 2026-07-03 (unsloth, revision a483e9e6, sha256 707a55a8...), re-fetched
after deletion. If the chat meant a 3.8 distill, that is a later arm, not a substitution.

## Conditions (identical for every arm)

- `llama-server -c 49152 --jinja --host 127.0.0.1 --port 8400 --no-webui -v`, exactly E113's flags.
  No KV quantisation, no `-np`, no speculative decoding, sampler and thinking at each model's
  embedded defaults. **Declared confound:** Flash-Next and the 27B think by default and the coder
  does not; that is how each is used, and the time cost is part of the finding.
- Full-offload gate per arm (E113): zero `assigned to device` lines, or any on CPU, voids the arm.
- `aider_task_runner.py` with the probe proxy, `--timeout 1800`, preconditions checked first
  (all three valid on 2026-09-24). Three repeats per arm on one server instance.
- Arm order **D, A, C, B**: the 87 GiB model last, so a wedge costs the least. Results are
  committed and pushed after each arm (bank both sides).

## Metrics

Per arm: `passes` of 9 (independent verify), passes per task, median wall seconds per attempt,
requests per attempt (probe log), timeouts. A wedge or server death VOIDS the arm's remaining
attempts; it is recorded, never scored as a fail.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `A.passes` | 4-7 | E113: 2 of 3 on b10435 |
| P2 | `D.passes` | 4-7 | current coding default; no instrument has separated it from A |
| P3 | `B.passes` | 3-7 | F116: parity with A on documents; not measured on code |
| P4 | `C.passes` | 1-4 | workhorse-class 3B-active MoE scored 0/8 walked on F116 |
| P5 | `B.median_wall_s / A.median_wall_s` | 0.6-1.0 | F116: 413-682 s vs 598-804 s per query |
| P6 | `T3.passes` in each arm | <= 1 of 3 in at least 3 of 4 arms | F152 application failure |
| P7 | `max - min` of `A.passes, B.passes, D.passes` | <= 3 | instrument is coarse; saturation is not the risk here, resolution is |

## Decision bands (fixed now)

- **A model is DISTINGUISHED from A** only if its `passes` differ from A's by **4 or more of 9**.
  Anything closer is reported as "not separated on this instrument", not as a ranking.
- **Chat pick CONFIRMED on code** only if it is not distinguished BELOW A and its
  `median_wall_s` <= A's. **Contradicted** if distinguished below A.
- No arm is recommended as a replacement for `local_code` from this run alone. It could only
  motivate a larger bank.

## Stop rules

Server dies or `dmesg` shows an amdgpu fault: stop, restore the relay, record the arm as VOID and
do not retry in the same window. Relay is restored on every exit path (E91's trap). Any arm still
running past 2 h wall stops at its next attempt boundary.

## Out of scope

`pi` as the agent, thinking-effort sweeps, MTP/speculative arms, Halogen and Orca engines (E139,
a separate arm), and the 3.8 35B distills. Sampler is not tuned per model.
