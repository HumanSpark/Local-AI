# Coding agents (r5.19)

Fixing and changing real software on its own, checked by each project's tests.

## What works best now

- **In production: Qwen3.8-Flash-Next** on Halogen (Halogen's own checkpoint, community template, effort low), since 2026-11-04.
  Why: Best local result on all three coding banks (15/15, 9/10, 5/10), passed the everyday-work tests at effort low in a third of the time, and runs fastest on Halogen.
- **Best alternative: Qwen3.8-27B** on Talus (Q4), since 2026-11-06.
  Why: 8/10 on the bigger-fixes bank and stronger than the July model on hard knowledge work; slower than production.
- **Best alternative: Ornith 1.5 35B** on llama.cpp (Q8_0), since 2026-11-07.
  Why: Tied production at 9/10 on the bigger-fixes bank at 30.4 minutes a task; 3/10 on the hard bank.

## Also tried

| Setup | Engine | Where it stands | Why |
|---|---|---|---|
| Qwen3.8-Flash-Next (HTR Htr5Core v0.2.4) (MTP3, 131K context) | HTR on vLLM | tried | Same model, community compression: 6/10 on the hard coding bank against production's 5/10, but slower. The known-good fallback engine. |
| Qwen3.8-Flash-Next (UD-Q4_K_XL) (Vulkan) | llama.cpp | tried | About a third of Halogen's writing speed on the same model. |
| Ling-3.2-air (Q3_K_M) (Vulkan) | llama.cpp | rejected | Writes 37% faster than production's model on llama.cpp but solved 0 of 10 hard coding changes. |
| Hy4-Flash (220B) (SQ-96) | Strata | rejected | Stable but about 24 tok/s; 3/10 on the hard bank with every task at its hour limit. |
| Qwen3-Coder-30B (Q4) | llama.cpp | retired | The earlier coding pick; solved 2 of the bigger fixes. |

## The experiments behind this, best results first

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| A lighter reasoning setting for coding (E159) | 2026-11-13 | in production | Low effort kept 8/10 at about a third of the time; made the default. | [results/e159-results.md](../results/e159-results.md) |
| Ten bigger fixes (E156) | 2026-11-06 | in production | Production 9/10, the 27B 8/10, Sonnet and Opus 8/10 each. | [results/e156-results.md](../results/e156-results.md) |
| Fifteen real fixes from our own projects (E154) | 2026-11-05 | in production | Two local setups solved all 15, like Claude Sonnet, at about 15 times the time. | [results/e154-results.md](../results/e154-results.md) |
| Ten large changes, tests visible (E167) | 2026-11-18 | works, with caveats | GPT-6.1 Sol 10/10, production 5/10. | [results/e167-results.md](../results/e167-results.md) |
| Newer local coding models on the bigger fixes (E158) | 2026-11-07 | works, with caveats | Ornith 1.5 35B tied production at 9/10; nothing beat it. | [results/e158-results.md](../results/e158-results.md) |
| Coding models a comparison widget recommended (E145) | 2026-09-25 | inconclusive | They tied with what we had already run. | [results/e145-results.md](../results/e145-results.md) |
| Four coding models on the same tasks (E143) | 2026-09-24 | inconclusive | They tied on passes and split the tasks in opposite ways. | [results/e143-results.md](../results/e143-results.md) |
| Ling-3.2-air on the box (E176) | 2026-11-24 | did not work | Writes 37% faster than production's model on llama.cpp; 0/10 on the hard coding bank. | [results/e176-results.md](../results/e176-results.md) |
| Production's model on the HTR engine (E177) | 2026-11-24 | not adopted | Same coding quality (6/10 against 5/10) but slower than Halogen; kept as a fallback. | [results/e177-results.md](../results/e177-results.md) |
| Hy4-Flash on the Strata engine (E171) | 2026-11-22 | did not work | Stable but slow; 3/10 with every task at its hour limit. | [results/e171-results.md](../results/e171-results.md) |
| The same ten changes, tests hidden (E168) | 2026-11-19 | did not work | Both local setups solved 1 of 10. | [results/e168-results.md](../results/e168-results.md) |

