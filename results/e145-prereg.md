# File: e145-prereg.md
# Purpose: Pre-registration for E145 - the models a third-party "approximate options for 128 GB" widget recommends, plus Ornith 1.5, through Aider on the three E113 tasks, against E143's arms.
# Project: sparkbench | Date: 2026-09-24
#
# Overview: The owner pasted a widget listing three options with "intelligence" and "tasks/hr" scores
# and no stated method. This tests the models it names on the instrument E143 used, on the same
# build and flags, so E143's four arms are the comparison and are not re-run. The widget's relative
# claims are turned into field-named predictions. Written before any run.

# E145 PRE-REGISTRATION - the widget's options through Aider (2026-09-24)

## The question

Do the widget's options behave on real repo tasks the way its numbers say relative to each other
(Ornith about 42% faster and about 98% as intelligent as the 35B best fit; the 27B about 5% more
intelligent and about 109% slower), and does either Ornith beat what E143 already measured?
The widget's own scores are not evidence: it states no method. Its claims are hypotheses here.

## Arms (llama.cpp `daef7b6`, served solo, E143's exact flags and conditions)

| arm | model | why it is here |
|---|---|---|
| **H** | Qwen3.6-35B-A3B UD-Q4_K_M | widget option 1 "best fit"; E143 arm C ran the UD-Q4_K_XL quant of the same model |
| **E** | Ornith 1.0 35B Q4_K_M | widget option 3 "faster" |
| **F** | Ornith 1.5 35B-A3B Q4_K_M | newer than the widget (created 2026-08-18); the widget lists 1.0 |
| **G** | Qwen3.6-27B Q4_K_M | GGUF stand-in for widget option 2. The widget's "Qwen3.6 27B OptiQ 4-bit" is an Apple MLX file this box cannot load; a different quant of the same dense model is the nearest thing that runs |

**Declared substitutions and unknowns:** G is a different quantisation from the widget's OptiQ, so
the widget's 27B claims are tested only approximately. Ornith's lineage is unverified: both repos
declare no base model (GGUF architecture `qwen35moe`, MIT). Thinking and sampling run at each model's
embedded defaults, as in E143; those defaults are unknown for Ornith.

## Comparison and conditions

Comparison arms are **E143's A, B, C, D, not re-run**: same build (F117), same harness, flags, tasks
and 3 repeats, so the two sets are comparable. Any change to the build or flags before the window
voids this and E143's arms are re-run. Arm order H, E, F, G (the dense 27B, slowest, last).
Everything else is E143's conditions: `-c 49152 --jinja`, full-offload gate, 12 GiB memory guard,
each arm banked before the next, relay restored on every exit path.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `H.passes` | 4-8 | E143 C (UD-Q4_K_XL) 6/9; a neighbouring quant |
| P2 | `H.time_per_repeat / C.time_per_repeat` | 0.85-1.15 | same model, near-identical quant size |
| P3 | `E.time_per_repeat / H.time_per_repeat` | 0.55-0.90 | widget: "~42% faster", i.e. 0.70 |
| P4 | `E.passes` | >= `H.passes` - 2 | widget: "retains ~98% intelligence" |
| P5 | `F.passes` | >= `E.passes` - 1 | a later release; no basis for a regression |
| P6 | `G.time_per_repeat / H.time_per_repeat` | 2.5-6 | widget says 2.09; E143's dense 27B ran 5.4x the 35B, with thinking on |
| P7 | `G.passes` | within 2 of `H.passes` | widget: "~5% more intelligent" |
| P8 | T3 passes, all four arms | <= 1 of 3 in at least 3 of 4 | E143: 3 of 4 arms at 0/3 |

## Decision bands (fixed now)

- A model is DISTINGUISHED from another only if its `passes` differ by **4 or more of 9**.
  Anything closer is "not separated on this instrument".
- **Widget speed claim (P3, P6) CONFIRMED** only if the measured ratio falls inside the registered
  range; **widget intelligence claim (P4, P7) CONFIRMED** only if the pass-count condition holds.
  These test the widget's direction and rough size, nothing more.
- No arm is recommended as a replacement for `local_code` from this run alone.

## Stop rules and out of scope

As E143. Server death or amdgpu fault voids the rest of that arm, recorded, not scored. Out of scope:
the OptiQ MLX file itself, Ornith 9B and 397B, thinking-effort sweeps, MTP or speculative arms,
Halogen and Orca engines.
