# Text and reasoning (r6.4)

Answering questions, summarising and pulling facts from documents, everyday writing.

**Against the frontier:** Level on routine document work; clearly behind on client drafting. ([how it compares](../FRONTIER.md))

## What works best now

- **In production: Qwen3.8-Flash-Next** on Halogen (Halogen's own checkpoint, community template, effort low), since 2026-11-04.
  Why: Best local result on all three coding banks (15/15, 9/10, 5/10), passed the everyday-work tests at effort low in a third of the time, and runs fastest on Halogen.
- **Best alternative: Qwen3.8-27B** on Talus (Q4), since 2026-11-06.
  Why: 8/10 on the bigger-fixes bank and stronger than the July model on hard knowledge work; slower than production.

## Also tried

| Setup | Engine | Where it stands | Why |
|---|---|---|---|
| Qwen3.8-Flash-Next (HTR Htr5Core v0.2.4) (MTP3, 131K context) | HTR backup engine | tried | The fallback engine for production's model: same model, community compression; 6/10 against production's 5/10 on the hard coding bank; slower. |
| Qwen3.8-Flash-Next (loom-serve 0.2) | AMD Loom | tried | 2.7 times llama.cpp on long prompts, but not faster than Halogen overall. |
| Qwen3.8-Flash-Next (UD-Q4_K_XL) (Vulkan) | llama.cpp | tried | About a third of Halogen's writing speed on the same model. |
| Ling-3.2-air (Q3_K_M) (Vulkan) | llama.cpp | rejected | Writes 37% faster than production's model on llama.cpp but solved 0 of 10 hard coding changes. |
| Hy4-Flash (220B) (SQ-96) | Strata | rejected | Stable but about 24 tok/s; 3/10 on the hard bank with every task at its hour limit. |
| Qwen3-30B-A3B (Q4_K_M, Vulkan) | llama.cpp | retired | The July everyday model; replaced by Flash-Next. |

## The experiments behind this, best results first

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| The lighter setting across eight kinds of everyday work (E160) | 2026-11-13 | in production | Matched maximum thinking on seven of eight at 0.41 times the time. | [results/e160-results.md](../results/e160-results.md) |
| One model, five engines (E153) | 2026-11-04 | adopted | Halogen fastest in every bucket (86 tok/s on code, 18.7 s to first word at 32K); it became the production engine. | [results/e153-results.md](../results/e153-results.md) |
| Qwen4 Max on client drafting (E164) | 2026-11-17 | works, with caveats | Beat production on drafting but trailed both frontier references. | [results/e164-results.md](../results/e164-results.md) |
| Client drafting against cloud models, judged blind (E162) | 2026-11-15 | works, with caveats | GPT-6.1 Sol won clearly; local losses were unsupported promises and omissions. | [results/e162-results.md](../results/e162-results.md) |
| Document summarising and instruction following, local against cloud (E31) | 2026-07-11 | works, with caveats | The July local model (since retired) matched cloud models on fact-checkable document tasks; these suites no longer separate strong models. | [experiments/E31.md](../experiments/E31.md) |
| The newer HTR release, same model (E179) | 2026-11-25 | informational | No measurable speed change at one user (about 44 tokens a second both releases); 3 of 3 large changes still solved. | [results/e179-results.md](../results/e179-results.md) |
| A paired question that catches a broken chat template (E175) | 2026-11-24 | informational | The pair caught a silently broken template and raised no false alarm. | [results/e175-results.md](../results/e175-results.md) |
| Auditing our own tests (E165) | 2026-11-17 | a correction to our own test | Five tests marked models down for following their own instructions; corrected, every setup passed 36/36 tool tasks. | [results/e165-results.md](../results/e165-results.md) |
| Halogen under load from other work (E152) | 2026-09-27 | informational | Coding turns at 44 tok/s and 4 s follow-ups under contention. | [results/e152-results.md](../results/e152-results.md) |
| Why Atlas DFlash was slow: the sliding window (E149) | 2026-09-26 | informational | The sliding-window setting was inert. | [results/e149-results.md](../results/e149-results.md) |
| Why Atlas DFlash was slow: the context cap (E150) | 2026-09-26 | informational | The context cap was not the cause. | [results/e150-results.md](../results/e150-results.md) |
| Atlas against llama.cpp (E146) | 2026-09-25 | informational | About 27% faster than llama.cpp here, and not as fast as published. | [results/e146-results.md](../results/e146-results.md) |
| Atlas against llama.cpp with a draft model (E147) | 2026-09-25 | informational | With a drafter, the open configuration beat Atlas on the MLPerf metric. | [results/e147-results.md](../results/e147-results.md) |
| Checking Halogen's published long-prompt speed (E139) | 2026-09-24 | informational | 1,152 tok/s at 32K, 5.3 times llama.cpp, short of the published 1,424. | [results/e139-results.md](../results/e139-results.md) |
| Checking a public speed claim for Ternary Bonsai (E138) | 2026-09-23 | informational | The claimed ~73 tok/s did not reproduce; 34.16 was the best of nine configurations. | [results/e138-results.md](../results/e138-results.md) |
| Can the knowledge-work tests still separate strong models? (E135) | 2026-09-11 | informational | No: three models across a 40x price range scored within one item. | [results/e135-results.md](../results/e135-results.md) |
| How long a document the box can handle interactively (E30) | 2026-07-11 | informational | Accuracy held past 80K tokens; first-answer time was the limit on the July engine. | [experiments/E30.md](../experiments/E30.md) |
| Energy cost per million tokens (E12) | 2026-07-04 | informational | About EUR 0.09 per million tokens generated, single user, at the July tariff. | [experiments/E12.md](../experiments/E12.md) |
| Inkling's DSpark helper on plain llama.cpp (E183) | 2026-11-26 | not adopted | About 16% faster short answers with 3 draft words, no gain in long conversations, slower with 7; Loom and CIRU gave 2-2.5x. | [results/e183-results.md](../results/e183-results.md) |
| Ling-3.2-air on the box (E176) | 2026-11-24 | did not work | Writes 37% faster than production's model on llama.cpp, but solved 1 of 15 everyday fixes and 0 of 10 large changes; thinking off made it loop. | [results/e176-results.md](../results/e176-results.md) |
| Production's model on the HTR engine (E177) | 2026-11-24 | not adopted | 6/10 against Halogen's 5/10 on large changes, but slower; kept as a fallback. | [results/e177-results.md](../results/e177-results.md) |
| An 8-bit conversation memory on llama.cpp (E174) | 2026-11-23 | not adopted | Never helped production's model: up to 10% slower. | [results/e174-results.md](../results/e174-results.md) |
| Hy4-Flash on the Strata engine (E171) | 2026-11-22 | did not work | Stable but slow; 3/10 with every task at its hour limit. | [results/e171-results.md](../results/e171-results.md) |
| AMD's Loom against Halogen and llama.cpp (E163) | 2026-11-16 | not adopted | Loom reads long prompts 2.7 times faster than llama.cpp but is not faster than Halogen. | [results/e163-results.md](../results/e163-results.md) |
| Expert helpers on unified memory (E161) | 2026-11-15 | not adopted | They do not pay on this kind of memory. | [results/e161-results.md](../results/e161-results.md) |
| Atlas's DFlash mode (E148) | 2026-09-26 | not adopted | Slower than its other mode and than the reference here. | [results/e148-results.md](../results/e148-results.md) |
| Why Atlas DFlash was slow: the prefix cache (E151) | 2026-09-26 | not adopted | Not the cause either; left unexplained and unusable here. | [results/e151-results.md](../results/e151-results.md) |
| A cheap-then-expensive model cascade (E140) | 2026-09-24 | did not work | Safe, but slower than a fixed setting. | [results/e140-results.md](../results/e140-results.md) |
| Choosing the reasoning effort per question (E141) | 2026-09-24 | did not work | No cheap decision beat a fixed low effort. | [results/e141-results.md](../results/e141-results.md) |
| Letting the 27B model decide when to think harder (E142) | 2026-09-24 | did not work | It can, but the check costs what it saves. | [results/e142-results.md](../results/e142-results.md) |

