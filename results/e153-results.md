<!--
# File: e153-results.md
# Purpose: E153 results - five Strix Halo engines serving Qwen3.8-Flash-Next on one box, timed by one client.
# Project: sparkbench | Date: 2026-11-04
#
# Overview: Scores results/e153-prereg.md (11 predictions, 4 gates, amendments 1-3) from the banked per-arm JSON in
# results/e153/speed-<arm>.json. Three relay windows on 2026-11-04 (17:10-17:52, 17:59-18:30, 18:32-18:53), TTS gateway
# resident throughout (5.5 GiB GTT baseline), kernel 7.0.0-38, Livepatch nothing-to-apply, IOMMU DMA-FQ.
-->

# E153 RESULTS - Halogen leads every bucket; four specialised engines are 2.2-3.2x llama.cpp on code (2026-11-04)

## The table (bucket medians, client clock, greedy, thinking off, single stream)

Decode, tok/s:

| arm | engine (version) | weights | CODE | PROSE | JSON | AGENT | P8K | P32K |
|---|---|---|---|---|---|---|---|---|
| L0 | llama.cpp `5851a8e` Vulkan, no drafter | UD-IQ4_XS | 27.1 | 26.2 | 26.2 | 26.0 | 25.2 | 24.6 |
| S | Strata 0.2.10 / engine 0.1.56, DFlash2 | UD-IQ4_XS | 60.7 | 41.2 | 62.7 | 65.0 | 37.7 | 38.6 |
| T | Talus v0.1.3 on ROCm 7.14.1 (fallback) | UD-IQ4_XS | 67.9 | 46.7 | 69.0 | 69.9 | 50.1 | 45.9 |
| G | gufo 0.29.0, MTP | UD-Q4_K_XL | 69.1 | 38.6 | 73.0 | 72.2 | 43.1 | 41.0 |
| H | Halogen 0.18.23, defaults | own v2 checkpoint | **86.0** | **58.3** | **88.9** | **85.5** | **59.5** | **57.1** |

Prefill (prompt tokens / time to first token), tok/s, and time to first token at 32K:

| arm | AGENT (1.0-1.8K ctx) | P8K | P32K | TTFT P32K |
|---|---|---|---|---|
| L0 | 301 | 353 | 315 | 104.1 s |
| S | 481 | 709 | 691 | 47.4 s |
| T | 914 | 1,119 | 1,258 | 26.1 s |
| G | 1,341 | 1,451 | 1,497 | 21.9 s |
| H | 1,399 | 1,674 | **1,755** | **18.7 s** |

Short-prompt buckets (CODE/PROSE/JSON, ~60-90 tokens) are omitted from the prefill table: their TTFT is fixed overhead,
not prompt reading. Package power was 81-87 W on every arm (CODE median: L0 81.2, S 84.5, T 84.7, G 85.4, H 87.0).

**Not served:** L1 (llama.cpp + MTP) crashed at load twice - the shared head has no `token_embd`, the standalone head aborts
in `process_ubatch` with `GGML_ASSERT(buffer)` at 114 GiB free (amendments 2-3). H-gguf (Halogen on UD-IQ4_XS) was killed by
the memory guard 30 s into its repack: MemAvailable fell from 114 GiB to 12.2 GiB with the TTS gateway resident.

## Predictions

| # | field | registered | measured | verdict |
|---|---|---|---|---|
| P1 | H.CODE decode | >= 58.4 | 86.0 | HELD (118% of the README's 73) |
| P2 | H.PROSE decode | >= 43.2 | 58.3 | HELD (108% of 54) |
| P3 | H.P32K prefill | >= 1,250 | 1,755 | HELD (101% of the synthetic 1,740) |
| P4 | H.CODE / G.CODE | >= 1.15 | 1.245 | HELD |
| P5 | T.CODE decode; T.P32K prefill | >= 59.1; >= 1,187 | 67.9 (66.7 without its 3 tool-call records); 1,258 | HELD, both |
| P6 | S.P8K prefill; S.P8K decode | >= 927; >= 42.5 | 709; 37.7 | FAILED, both |
| P7 | G.P32K prefill | >= 1,368 | 1,497 | HELD |
| P8 | L0.P32K prefill; L0.CODE decode | 150-350; 12-25 | 315; 27.1 | prefill HELD; decode FAILED (above the range) |
| P9 | L1 byte-identical to L0 | all equal | L1 never served | UNSCORABLE |
| P10 | every G/H/S/T CODE >= 1.5 x L1 | | L1 never served | UNSCORABLE. Against L0 instead: S 2.24x, T 2.51x, G 2.55x, H 3.17x |
| P11 | CODE > PROSE for every speculative arm | | S, T, G, H all | HELD |

Gates: G1 ready - L1 failed (load crash), H-gguf failed (killed); G2 thinking leaks 0 on every served arm; G3 ruler - five
records flagged, resolved below; G4 fit - H-gguf failed; every served arm stayed above the 12 GiB floor (minimum
MemAvailable: L0 13.9, G 17.5, S 35.8, T 39.6, H 79.3 GiB).

## Ruler notes (G3), resolved before comparison

- **T emitted three responses as `tool_calls`** (CODE-2, AGENT-4, AGENT-5) with no tool schema in the request. The client times
  only content deltas, so those records divide the full token count by a shorter span and run high (CODE-2 81.0). T's CODE
  median without them is 66.7 (vs 67.9), AGENT 72.5 (vs 69.9); no verdict changes.
- **AGENT-2 (and H's AGENT-5)** differ by one token between the engine's count and the local re-tokenisation (47 vs 46):
  re-tokenisation noise just over the 2% line, immaterial.
- **AGENT answers are short** (46-96 tokens on every arm: the model stops to call a tool), so the AGENT decode column carries
  more noise than CODE/PROSE/JSON (512 tokens). Treat it as indicative.

## What it changes

1. **The community claim reproduces, and is larger here.** Halogen over gufo on code is 1.245x (86.0 vs 69.1); dsp457 reported
   60-65 vs 45-55 (about 1.2-1.3x). Halogen also leads prose, JSON, agent turns, 32K decode and prefill at every depth.
   The comparison is engine plus file: Halogen's own checkpoint (4.16 bpw by its README) against gufo's UD-Q4_K_XL (~5.0 bpw).
   No quality was measured, so "faster" is not "better".
2. **Talus's README holds at 85 W on a non-shipped runtime.** 67.9 code (92% of 73.9 at 120 W) and 1,258 at 32K (85%).
3. **Strata's maintainer figures do not hold with today's default drafter.** 709 / 37.7 at 8K against the MTP-era 1,159 / 53.1;
   the plan picked DFlash2. An MTP arm was not run, so the drafter is a suspect, not a cause.
4. **llama.cpp mainline has moved:** 27.1 tok/s decode against E139's 16.6 on build `daef7b6` (the production build), same
   file and KV config. But its Flash-Next MTP path does not run on Vulkan from unsloth's files, so the fair "llama.cpp with a
   drafter" arm is still missing.
5. **Memory decides what runs beside the TTS gateway.** gufo's UD-Q4_K_XL left 17.5 GiB; Halogen's GGUF path could not start.

## Not measured / open

- Quality of any arm (KL or task scores) - required before any recommendation stronger than "fastest".
- Strata with `--drafting mtp`; Talus on its pinned ROCm nightly; llama.cpp + MTP (needs a llama.cpp fix or a GGUF with an
  embedded head); unsloth's new "UD 3.1" quants (uploaded 2026-11-04 15:56-16:15); an idle box without the TTS gateway.
- One run per arm (F15: single-run noise about 1.5% on llama-bench; served-path noise here not measured).

Evidence: `results/e153/speed-{L0,S,T,G,H}.json` (+ `.stdout`, `.serverlog`), `speed-L1.*` and `speed-H-gguf.*` (failed
starts), `window.log`, `mem_guard.log`, `prompts.json`; prereg `results/e153-prereg.md` (amendments 1-3).
