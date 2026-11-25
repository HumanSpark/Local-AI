# Engines (r5.19)

An engine is the software that runs a model, and the same model can run very differently on different engines. Comparing engines fairly needs the same model on each, so the comparisons at the end are same-model runs. Engine speed also depends on the work (code or prose, idle or live), and each row says which.

## What works best now

- **In production: Halogen**, running Qwen3.8-Flash-Next.
  Why: Fastest of five engines on production's model (86 tok/s on code, 18.7 s to first word at 32K, 4 Nov); closed source.
- **Fallback: HTR on vLLM**, the same model compressed by the community.
  Why: Community build with its own compression: same coding quality as production (6/10 vs 5/10), about 25% slower writing.

## Engines for language models

| Engine | Where it stands | Why |
|---|---|---|
| Halogen | production | Fastest of five engines on production's model (86 tok/s on code, 18.7 s to first word at 32K, 4 Nov); closed source. |
| HTR on vLLM | fallback | Community build with its own compression: same coding quality as production (6/10 vs 5/10), about 25% slower writing. |
| llama.cpp | baseline | The open-source standard; runs almost any model, so most model tests use it. About a third of Halogen's speed on production's model. |
| AMD Loom | tried | AMD's engine in development: 2.7 times llama.cpp on long prompts, but not faster than Halogen. |
| Talus | compared | Community engine for this chip: 2.5 times llama.cpp on code; runs the 27B runner-up. |
| gufo | compared | Community engine: second fastest on code in the 4 Nov comparison. |
| Strata | compared | Community engine (MIT): 2.2 times llama.cpp on code; ran Hy4-Flash. |
| Atlas | compared | Community engine: about 27% faster than llama.cpp here, slower than published; one mode unusable. |
| CIRU runtime | compared | Community vLLM packaging for this chip; ran Inkling-2-Mini. |

## Engines for other jobs

| Engine | Where it stands | Why |
|---|---|---|
| whisper.cpp | production | Runs production speech to text. |
| WeSpeaker + Silero | production | Runs production speaker labelling. |
| Chatterbox | production | Runs the production narration voice. |
| stable-diffusion.cpp | production | Runs production image generation. |
| Kokoro | fallback | Fixed voices; the opt-in narration fallback. |
| pyannote | tried | Better general diarisation, slower; not needed for host-or-other. |
| diffusers on ROCm PyTorch | tried | Runs Qwen-Image-2.1, only with the gateway down. |
| audio.cpp | tried | Runs the three song models tested. |
| cloud API | compared | Cloud models used as comparisons and judges only. |

## Same-model engine comparisons

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| One model, five engines (E153) | 2026-11-04 | adopted | Halogen fastest in every bucket (86 tok/s on code, 18.7 s to first word at 32K); it became the production engine. | [results/e153-results.md](../results/e153-results.md) |
| Atlas against llama.cpp (E146) | 2026-09-25 | informational | About 27% faster than llama.cpp here, and not as fast as published. | [results/e146-results.md](../results/e146-results.md) |
| Atlas against llama.cpp with a draft model (E147) | 2026-09-25 | informational | With a drafter, the open configuration beat Atlas on the MLPerf metric. | [results/e147-results.md](../results/e147-results.md) |
| Checking Halogen's published long-prompt speed (E139) | 2026-09-24 | informational | 1,152 tok/s at 32K, 5.3 times llama.cpp, short of the published 1,424. | [results/e139-results.md](../results/e139-results.md) |
| Production's model on the HTR engine (E177) | 2026-11-24 | not adopted | Same coding quality (6/10 against 5/10) but slower than Halogen; kept as a fallback. | [results/e177-results.md](../results/e177-results.md) |
| AMD's Loom against Halogen and llama.cpp (E163) | 2026-11-16 | not adopted | Loom reads long prompts 2.7 times faster than llama.cpp but is not faster than Halogen. | [results/e163-results.md](../results/e163-results.md) |

