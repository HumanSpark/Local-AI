# File: cloud-published-benchmarks.md
# Purpose: Vendor-published knowledge-benchmark citations for cloud models used in the deeper-research campaign (context, not comparison).
# Project: sparkbench | Date: 2026-07-11
#
# Overview: Collates vendor-reported MMLU and related knowledge benchmarks
# for the three pinned cloud comparison tiers (GPT-5.6-sol frontier, GPT-5.4-mini
# cheap workhorse, mistral-large-2512 EU business tier) plus budget-permitting
# extras (mistral-medium-2508, mistral-small-2506, magistral-medium-2509).
# Each entry records exact benchmark variant, reported score, shot count and method
# where disclosed, source URL, and access date (2026-07-11). Primary sources
# (vendor model cards, official announcements, system cards) marked; secondary
# sources (leaderboards, press) noted as such. Where a pinned model has no findable
# published score, absence is recorded explicitly.

## Vendor-published knowledge benchmarks

| Model ID | Benchmark | Variant | Score | Shot count / Method | Source | Access date | Source type |
|---|---|---|---|---|---|---|---|
| openai/gpt-5.6-sol | MMLU | (classic) | None published | N/A | [OpenAI deployment safety hub](https://deploymentsafety.openai.com/gpt-5-6/gpt-5-6.pdf) | 2026-07-11 | Primary: official system card |
| openai/gpt-5.6-sol | Terminal-Bench 2.1 | agentic command-line coding | 88.8% (Sol base) | N/A | OpenAI official announcements | 2026-07-11 | Primary |
| openai/gpt-5.4-mini | MMLU | Pro (harder variant) | 55.29% | Not disclosed | [LayerLens benchmark review](https://layerlens.ai/blog/gpt-5-4-benchmark-review) | 2026-07-11 | Secondary: aggregator |
| openai/gpt-5.4-mini | MMLU | classic | None published | N/A | OpenAI official | 2026-07-11 | Primary |
| mistral-large-2512 | MMLU | Multilingual (8-language) | 85.5% | Not disclosed | [Medium review](https://medium.com/@leucopsis/mistral-large-3-2512-review-7788c779a5e4) + search results | 2026-07-11 | Secondary: blog analysis |
| mistral-large-2512 | MMLU | Pro (harder variant) | ~low 80s (range, not exact) | Not disclosed | [LLM analysis sources](https://medium.com/@leucopsis/mistral-large-3-2512-review-7788c779a5e4) | 2026-07-11 | Secondary |
| mistral-small-2506 | MMLU | classic | 81%+ (over 81%) | Not disclosed | [Mistral Small 3 official news](https://mistral.ai/news/mistral-small-3/) | 2026-07-11 | Primary: vendor news |
| mistral-medium-2508 | MMLU | Pro (harder variant) | 74.4% | Not disclosed | Benchmark aggregators | 2026-07-11 | Secondary |
| mistral-medium-2508 | MMMU | multimodal | ~63% (range) | Not disclosed | Benchmark aggregators | 2026-07-11 | Secondary |
| magistral-medium-2509 | MMLU | (classic or variant) | None published as of 2026-07-11 | N/A | [Mistral Magistral announcement](https://mistral.ai/news/magistral/) | 2026-07-11 | Primary: vendor news (reports AIME2024, not MMLU) |
| magistral-medium-2509 | AIME2024 | math competition | 73.6% (90% w/ majority voting @64) | Not disclosed | [Mistral official](https://mistral.ai/news/magistral/) | 2026-07-11 | Primary |

## Method caveat

These are vendor-reported numbers, produced with different harnesses, shot counts, and benchmark variants than our local measurements, on models whose training data may include the benchmark itself. They are context, not comparison. Our measured local-vs-cloud tables come only from the identical-suite runs (E27/E28), and our local MMLU numbers (0-shot logprob, 1,140-question balanced sample) must never be placed in the same table as these.

## Notes

- **GPT-5.6-sol**: OpenAI did not publish MMLU or other classic academic knowledge benchmarks at launch; the model's published evals focus on agentic and coding tasks (Terminal-Bench 2.1). No standard MMLU score available from OpenAI.
- **GPT-5.4-mini**: Only MMLU Pro variant found published (55.29%); standard MMLU not published by OpenAI. The Pro variant is harder than classic MMLU and introduces more subtle distractors.
- **mistral-large-2512**: Multilingual MMLU (8-language) score is firm (85.5%); the MMLU Pro range ("low eighties") is approximated from analysis rather than a discrete published figure.
- **mistral-small-2506**: "Over 81%" from Mistral's official announcement; exact figure not pinned in source.
- **mistral-medium-2508**: Conflicting secondary sources (74.4% on MMLU Pro vs. 49.1%); both attributed to aggregator benchmarks. No classic MMLU published; MMLU Pro and MMMU (multimodal) reported.
- **magistral-medium-2509**: This reasoning model (frontier-class, extended thinking) does not publish MMLU benchmarks; Mistral's official announcement focuses on AIME2024 math-competition performance. No MMLU score available.

## Sources consulted

Primary (vendor official):
- OpenAI Deployment Safety Hub: GPT-5.6 system card
- Mistral AI official news pages: mistral-small-3, magistral
- OpenAI official announcements (blog/press)

Secondary (aggregators, press, analysis):
- LayerLens benchmark review
- Medium blog analysis (Barnacle Goose)
- Various LLM benchmark tracking sites and leaderboards
