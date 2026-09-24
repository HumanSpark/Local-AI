# File: e139-results.md
# Purpose: Results for E139 - does halogen-flash prefill 32K at ~1,424 tok/s on this box?
# Project: sparkbench | Date: 2026-09-24
#
# Overview: Scored against results/e139-prereg.md and amendments 1-4. Three gateway windows
# (21:02-21:32 main, 21:32 G0k, 21:33 G0m), Chatterbox TTS resident throughout (amendment 2).
# C1 is REPRODUCED-CONDITIONALLY at 1,152 tok/s; 8 predictions held, P9 falsified, P7 unscorable
# because G0 was killed twice by the 12 GiB memory guard. Raw: results/e139/. Registered as F165, F166.

# E139 RESULTS - Halogen reaches 1,152 tok/s at 32K, 5.3x llama.cpp, but cannot serve our GGUF here (2026-09-24)

## The headline (C1)

`H0.P32K.prefill_tps` (median of 3) = **1,152.01 tok/s**. The claim is 1,424; the bar was 1,210.
**C1 = REPRODUCED-CONDITIONALLY** (band 1,000-1,210). Attribution to the IOMMU (translated mode here,
passthrough in the README) would need an IOMMU-off arm, and none exists, so it stays conditional.
Runs were 942 / 1,152 / 1,170 tok/s: the first of three is the slow one.

## Per arm (medians of 3; Chatterbox TTS resident, baseline 8,484 MiB GTT+VRAM)

| arm | what | P8K prefill | P32K prefill | P32K decode | P32K wall s | peak GPU GiB |
|---|---|---|---|---|---|---|
| H0 | Halogen 0.13.8, its own checkpoint | 1,005.9 | **1,152.0** | 38.1 | 33.4 | 43.3 |
| H0-id | same, prompt cache off, serial vs MTP | 1,044-1,084 | - | 33.4-33.7 serial, 37-43 MTP | - | 43.3 |
| H0s | same, "speed" overlay (extra, not scored) | 1,010.2 | 1,210.0 | 33.5 | 31.6 | 43.3 |
| L0 | mainline llama.cpp daef7b6, our UD-IQ4_XS GGUF | 235.5 | **216.5** | 16.6 | 162.1 | 70.2 |
| G0 | Halogen on our GGUF | - | - | - | - | VOID, guard kill |
| G0k | G0 + KV pool 65,536 | - | - | - | - | VOID, config error |
| G0m | G0 + `HALOGEN_MAX_TOK=16384` | - | - | - | - | VOID, guard kill |

Identity: **4 of 4** prompts byte-equal serial vs MTP (H0-id), and the image's own `bench` reports
"PASS, every drafter byte-identical on every case" (mean MTP 44.9 tok/s over its cases, recorded not scored).

## Scored predictions

| # | field | predicted | measured | verdict |
|---|---|---|---|---|
| P1 | `H0.loads` | YES within 15 min, no memlock failure | YES, 77.3 s, no memlock failure | HELD |
| P2 | `H0.P32K.prefill_tps` | 1,000-1,300 | 1,152.0 | HELD |
| P3 | `H0.P8K.prefill_tps` | 900-1,200 | 1,005.9 | HELD |
| P4 | `H0.D1500.decode_tps_serial` | 32-38 | 33.6 | HELD |
| P5 | `H0.P32K.decode_tps` | 34-42 | 38.1 | HELD |
| P6 | `L0.P32K.prefill_tps` | 150-230 | 216.5 | HELD |
| P7 | `G0/L0 P32K prefill` | >= 3.0 | **not measured** | **UNSCORABLE** |
| P8 | `H0/L0 P32K total_s` | <= 0.30 | 33.38 / 162.06 = 0.206 | HELD |
| P9 | `H0.peak_gpu_mem_gib` | 95-115 | 43.3 (35.05 above baseline) | **FALSIFIED** |
| P10 | `H0.identity.byte_equal` | 4 of 4 | 4 of 4 | HELD |

## Why P7 is unscorable

The memory guard (floor 12 GiB, 1 s poll) killed G0 at MemAvailable **11,356 MiB** and G0m at
**12,108 MiB**. The engine had repacked all 70.55 GiB of our GGUF into host RAM both times. G0k was
rejected by the engine in 6 s (`--kv-pool` cannot be below `--ctx`), a config error with no memory
result. Per amendment 4 a second guard kill ends the arm: no further attempt. The vendor's "about 9 GiB
back" from `HALOGEN_MAX_TOK=16384` did not show: 0.75 GiB better at the kill point, which may be a
different phase of the load and is not established either way.

## Limits

- H0 (Halogen's own checkpoint) vs L0 (unsloth UD-IQ4_XS) differ in the FILE as well as the engine.
  The 5.3x ratio (1,152 / 216.5) is engine plus quant plus format, not the engine alone; P7 was to
  separate them and could not.
- Chatterbox held 8.1 GiB throughout, so every arm had that much less GTT than the README's clean box.
- The built-in `sweep` table reads 363,514 tok/s at pp8192 and is not interpretable as a rate
  (impossible against H0's 1,006); it is recorded and unused.
- One window per arm, medians of 3, IOMMU translated. No IOMMU-off arm.
