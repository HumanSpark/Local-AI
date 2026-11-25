<!--
# File: docs/GLOSSARY.md
# Purpose: Plain-English meanings for the names, codes and terms used across sparkbench, so a reader without the prereg open can follow.
# Project: sparkbench | Date: 2026-11-24
#
# Overview: Owner, 2026-11-24: "a glossary of terms that were previously being used so we can see them and understand
# them." One line per entry. Sources: tools/run_e154_arms.sh header (arm codes), the prereg files named per entry,
# docs/FINDINGS.md. Add a row whenever a new code or name appears in a prereg; the chat naming check
# (.claude/hooks/shorthand_check.py) points here.
-->

# Glossary

## How to read a number

| Looks like | Means |
|---|---|
| E171 | An **experiment**, numbered in order. Its plan and predictions are in `results/e171-prereg.md`, its outcome in `results/e171-results.md`. |
| F193 | A **finding**: a conclusion we would stand behind, in the findings register (`FINDINGS.md`). One experiment can produce several. |
| P3 | **Prediction** 3 in an experiment's prereg, written before the run. It either held or was falsified. |
| G2 | **Gate** 2: a check that must pass before results count (for example "tool calls parse"). |
| A1 | **Amendment** 1: a change to an experiment's plan, declared before the runs it affects. |
| r5.16 | A **release** of the Local-AI data package published on GitHub. |
| T1, T3 | A **track** in HANDOFF.md (a workstream), not an experiment. |

## Arm codes (one setup inside an experiment)

An "arm" is one setup being compared: a model, on an engine, with given settings. The code is only an identifier.

| Code | What it was | Experiment |
|---|---|---|
| H | Production: Qwen3.8 Flash-Next on the Halogen engine | many (E154 onward) |
| HX, HM, HL | Production at reasoning effort extra-high / medium / low | E159 |
| HF, HFL | Production with a community-fixed chat template, at default / low effort | E159 |
| HS | Production (Halogen) at low effort, as the comparison for Loom | E163 |
| S | Claude Sonnet 5.5 in the cloud (reference) | E154, E156 |
| O | Claude Opus 5.5 in the cloud (reference) | E156 |
| GS | GPT-6.1 Sol in the cloud (reference) | E167 |
| Q | Qwen3-Coder-30B on llama.cpp (the old local coding pick) | E154, E156 |
| QN | Qwen3-Coder-Next on llama.cpp | E154 |
| T27 | Qwen3.8-27B on the Talus engine | E154, E156 |
| TL | Laguna-S-2.1 on the Talus engine | E154 |
| OR35, OR122 | Ornith 1.5, 35B and 122B, on llama.cpp | E158, E167 |
| TS45, TS4 | Tess-4.5-27B and Tess-4-35B on llama.cpp | E158 |
| RA | Raon-1-mini on KRAFTON's llama.cpp fork | E158 |
| GL | GLM-5.3-Flash, heavily compressed, on llama.cpp | E155 |
| DC | DeepSeek-V4.1-Flash coder variant on llama.cpp | E155 |
| NM | Nemotron-3.5-Super on llama.cpp | E166, E167 |
| HY | Hy4-Flash on the Strata engine | E171 |
| LM | Flash-Next on AMD's Loom engine | E163 |
| LC | Flash-Next on llama.cpp, speed only | E163 |
| IQ, IM, IL, IC | Inkling-2-Mini on llama.cpp Q8 / llama.cpp Q4 / Loom / CIRU runtime | E170, E172 |
| YU, MM, AS | Song models YuE2, MiniMax Music 3, ACE-Step 1.5 | E173 |
| LG | Ling-3.2-air (inclusionAI) on llama.cpp | E176 |
| T1-T10, X1-X10, E1-E10 | Music tasting clips: owner's picks / neighbouring styles / teaching-song styles (not experiments) | style tasting, 2026-11-24 |

## Engines and runtimes (software that runs a model)

| Name | Meaning |
|---|---|
| llama.cpp | The open-source engine we benchmark most; runs GGUF model files on our AMD GPU via Vulkan. |
| Halogen | Closed-source engine that serves production (Flash-Next). |
| Talus | Community engine tuned for this chip; ran Qwen3.8-27B and Laguna. |
| Strata | Community engine (MIT licence) that ran Hy4-Flash. |
| Loom | AMD's HRX Loom, an inference engine still in development. |
| CIRU runtime | A community packaging of vLLM tuned for our AMD chip. |
| audio.cpp | Engine for audio models (the song generators in E173 and the tasting). |
| Engram | Part of some models (not an engine): a large lookup table read from disk during generation. |

## Recurring terms

| Term | Meaning |
|---|---|
| Production / Flash-Next | Qwen3.8 Flash-Next on Halogen: the model the office actually uses. |
| Relay / sparkrouter | The gateway that serves production to the network. Benchmarks take it down ("idle window") and restore and check it after. |
| Prereg | Pre-registration: the plan and predictions written and committed before an experiment runs. |
| Hard coding bank | Ten real fixes from our own projects, each graded by the project's tests (E167's bank). Production solved 5, the best cloud model 10. |
| Capability index | The monthly re-run of a fixed bank to see whether this box gets more capable over time. |
| Memory-edge crash / DeviceLost | The GPU driver failure on very large loads (over about 60 GiB). After one, the box is rebooted before any further GPU work (F193). |
| GTT | The share of system memory the GPU is using; we wait for it to return to its resting level before each run. |
| Page cache | Files Linux keeps in memory after reading them; we clear it before big loads because it can push the GPU into the memory-edge crash. |
| Quant (Q4_K_M, Q3_K_M, ...) | How compressed a model file is. Lower numbers are smaller and faster but can lose quality. |
| tok/s, pp512, tg128 | Speed: tokens per second reading a 512-token prompt (pp) and writing 128 tokens (tg). |
| Context (8K, 32K, 131K) | How much text the model holds at once, in tokens. |
| Active parameters | The part of a mixture-of-experts model used per word; it sets the speed more than total size does. |
| Scouting | Read-only review of an outside tool or model, ending in reject / watch / spike / adopt (`scouting/REGISTER.md`). |
| Spike | A quick throwaway test to see whether something deserves a full experiment. |
| Local-AI | The public GitHub data package of our results (HumanSpark/Local-AI). |

## Claim status

Every claim in `claims.yml` and `claims.json` carries these fields (added 2026-11-24).

| Field | Meaning |
|---|---|
| status `current` | Still supports today's advice. |
| status `qualified` | Holds, with the caveat in `note` (often: measured on an older setup, or narrowed by later work in `qualified_by`). |
| status `historical` | An accurate record of a setup, model or price that is no longer the advice. |
| status `superseded` | A newer result replaces it; `superseded_by` names it. |
| `tested` | Date the measurement was made. |
| `reviewed` | Date of the last status review. |
| `record` | The exact evidence: a file in this package, plus an anchor where there is one. |
| `source_url` | That record, pinned to the release tag. |
| access `inspect` | The outputs and scores are published; read them. |
| access `recalculate` | A published script rebuilds the number from published inputs. |
| access `rerun` | Published inputs and harness; re-running needs the model. |
| access `private` | Inputs are withheld (client documents, private repositories, real calls); the scores and method are published. |
| track | `documents`, `drafting`, `meetings`, `unattended` (multi-step work, tested through coding and tool use) or `running` (speed, capacity, cost, power, stability). |
| `setup_role` / `setup_technical` | The plain-English and the technical name of the setup measured. |

## Experiment numbers used twice

E32, E33 and E35 to E50 each name two experiments, one from July and one from August. The July ones are written with an
A: E32A, E33A, E35A to E37A (router and multi-user tests) and E38A to E50A (meetings and transcription).
`experiments/E32.md` and the rest are the August ones.
