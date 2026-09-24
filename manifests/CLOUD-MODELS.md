# File: CLOUD-MODELS.md
# Purpose: Pinned cloud comparator models for the deeper-research campaign (E28) - IDs, versions, prices, access dates, selection rationale.
# Project: sparkbench | Date: 2026-07-11
#
# Overview: The cloud side of the report's data-residency spectrum (plan Task 3;
# brief Section 5's three comparison points). Every E28 run must use exactly
# these IDs. Convention: cloud models changing under us between runs is a
# FINDING about cloud (recorded, dated), not a flaw in the method. Prices are
# vendor list prices via the OpenRouter catalogue / Mistral docs on the access
# date, USD per million tokens.

## The three comparison points (brief Section 5)

| Tier | Model ID | API | Ctx | $ in/M | $ out/M | Pinned |
|---|---|---|---|---|---|---|
| US frontier (the honest ceiling) | `openai/gpt-5.6-sol` | OpenRouter | 1,050,000 | 5.00 | 30.00 | 2026-07-11 |
| Cheap cloud workhorse | `openai/gpt-5.4-mini` | OpenRouter | 400,000 | 0.75 | 4.50 | 2026-07-11 |
| EU business tier (GDPR/data-residency) | `mistral-large-2512` | Mistral (api.mistral.ai) | 262,144* | 2.00* | 6.00* | 2026-07-11 |

*Mistral ctx/prices to be confirmed from Mistral's own docs at first E28 run
and updated here; the ID itself was pinned from Mistral's live `/v1/models`
on 2026-07-11 (dated snapshot deliberately preferred over `-latest`).

**Budget-permitting extras (drop order when the budget gate bites:
magistral, medium, small - never the EU tier itself):**

| Extra | Model ID | API | Role |
|---|---|---|---|
| EU reasoning mirror | `magistral-medium-2509` | Mistral | mirrors how local reasoning models are tested |
| EU price/perf point | `mistral-medium-2508` | Mistral | the advisor-review plan's workhorse pick |
| EU cheap tier | `mistral-small-2506` | Mistral | cheap-EU cross-check (used in the Task 2 smoke) |

## Selection rationale (access 2026-07-11, OpenRouter catalogue, 345 models)

- **Frontier:** `openai/gpt-5.6-sol` is the newest flagship tier of the
  ChatGPT family (5.6 line, created 2026-07; sol > terra > luna by price
  tier at $5/$30 vs $2.5/$15 vs $1/$6). The report's organising reader
  question is literally "is it as good as ChatGPT?", so the ceiling should
  BE the current ChatGPT flagship. Alternatives considered:
  `anthropic/claude-fable-5` ($10/$50 - strongest candidate on capability,
  2x the price, and not the model the reader means by "ChatGPT");
  `anthropic/claude-opus-4.8` ($5/$25); `openai/gpt-5.5` ($5/$30, superseded
  by 5.6). One frontier only, per the brief ("drop a second frontier model
  before you drop the EU tier").
- **Cheap workhorse:** `openai/gpt-5.4-mini` ($0.75/$4.50) is the mainstream
  budget tier an IT provider would actually propose to a small firm.
  `deepseek/deepseek-v4-flash` is ~10x cheaper ($0.077/$0.154) but a
  confidentiality-led firm would not accept the hosting jurisdiction - it
  appears in the report's cost analysis as the absolute price floor, NOT as
  a benchmarked comparator. `google/gemini-3.1-flash-lite` ($0.25/$1.50)
  considered; the mini tier keeps the frontier and budget points in one
  vendor family, which makes the capability gap cleanly attributable to
  tier, not vendor.
- **EU tier:** unchanged from the 2026-07-11 Mistral pin (see HANDOFF /
  advisor plan Section 4). Chat/instruct only; embedding/OCR/FIM/audio out
  of scope.

## Spend projection (Task 3 gate: < 50% of remaining OpenRouter cap)

Computed 2026-07-11 from the authored suites' actual prelude sizes (word x 1.4
heuristic), not from the smoke's 300-token profile. Per cloud model:
summarisation ~135K in (30 tests, doc preludes 1.8-9.5K tokens), IF ~7K in
(24 short tests), long-context ~564K in (6 tests x each of ~16K/~24K/~54K
corpora), output ~29K (72 tests x ~400). Total ~0.71M in / ~0.03M out.

| Model | $ estimate |
|---|---|
| gpt-5.6-sol (frontier) | ~$4.45 |
| gpt-5.4-mini (cheap) | ~$0.67 |
| OpenRouter total | **~$5.10 = 3.4% of the $150 cap - GO** |
| mistral-large-2512 | ~$1.60 (separate Mistral key) |
| Mistral extras (small+medium+magistral) | ~$2-4 if run |

Gate PASSED with ~15x margin; even a full re-run of everything stays under
10% of the cap. Smoke baseline (per-provider wiring + token accounting):
results/deep-eval/smoke-usage-notes.md.

## Aliases deliberately avoided

`~openai/gpt-latest`, `~anthropic/claude-sonnet-latest`, `-latest` Mistral
aliases: all rejected - they re-point silently, which breaks reproducibility.
Dated/pinned IDs only.
