<!--
# File: results/e179-results.md
# Purpose: Results of E179 - HTR v0.2.5 against v0.2.4 and Halogen, same model; speed leg (bank leg partial, appended when done).
# Project: sparkbench | Date: 2026-11-25
#
# Overview: Prereg results/e179-prereg.md. Speed: tools/run_e179_htr025.sh (identical to E177's speed leg except the
# image), client-timed with tools/e163_speed.py on the E139 prompts, thinking off; Halogen timed live the same night.
# Raw: results/e179/raw/{HS,HT}/speed.json, results/e179/run.log.
-->

# E179 RESULTS - HTR v0.2.5 (2026-11-25)

## In plain English

On our test, one user at a time, the new HTR release runs at the same speed as the old one. Averaged over three repeats
of each prompt, writing was 44.3 against 44.8 tokens a second at 8K and 44.1 against 44.6 at 32K; reading a long
document was about 3% slower, within the spread between repeats. Production's Halogen engine, timed the same night,
wrote at 63.0 and read at 1,662. The maker's gains were with several users at once and in a long-conversation mode we
don't use. HTR stays the backup engine.

**Correction (2026-11-25, same morning):** the first version of this file said v0.2.5 was 7.6% slower at writing. That
compared one request on each release. Repeats of the same prompt on the same release ranged from 36 to 53 tokens a second
(a spread of 38% of the mean at 8K, 11% at 32K; draft acceptance changes per request), so a single request cannot
show a 7.6% change.

## Speed (one request at a time, thinking off, client-timed; tokens a second, seconds to first token)

| Engine | Short prompt: writing | 8K prompt: writing / reading / first token | 32K prompt: writing / reading / first token |
|---|---|---|---|
| HTR v0.2.5 (tonight) | **44.15** | 43.46 / 939.0 / 8.74s | 42.72 / 895.3 / 36.61s |
| HTR v0.2.4 (E177, 24 Nov) | 47.76 | 44.93 / 968.5 / 8.47s | 44.05 / 923.6 / 35.49s |
| Halogen 0.18.23 (tonight, live) | 62.95 | 56.36 / 1,543.4 / 5.32s | 51.21 / 1,661.7 / 19.73s |

The table shows each prompt's median. Per request, decode on the same 8K prompt was 53.13, 43.46 and 36.21 on v0.2.5
and 46.12, 43.49 and 44.93 on v0.2.4; at 32K, 47.13, 42.72, 42.47 against 49.93, 44.05, 39.71. Means: 8K 44.3 vs 44.8,
32K 44.1 vs 44.6. The short prompt ran once per release (44.15 vs 47.76), inside that spread. Reading at 8K and 32K was
about 3% lower on v0.2.5, also within the spread. The ±1.5% noise figure (F15) is for llama-bench without speculative
decoding and does not apply here. Mean draft acceptance on our prompts was about 2.3 tokens per step, against the
maker's 3.21 on theirs. The new native kernels did load (the server log shows the native routes active). Load took
420s with 72.5 GB of GPU memory. Conditions matched E177 (kernel 7.0.0-43, page cache evicted, GTT baseline 17 MiB)
except that tonight Halogen had just been timed, leaving 16.8 GB of page cache against 4.9 GB and 22 GB free against
37 GB; no thermal or power capture on either night.

## Large changes (partial by design: new tasks only until 08:00)

HTR v0.2.5 solved **3 of the 3** large changes it started (clearmail-3d41463d0, clearmail-7fe0a79c1,
clearmail-01d445d75), in 822s, 1,266s and 1,428s. v0.2.4 passed the same three (1,079s, 1,083s, 1,476s). The other
seven were not started; they run in a later window. Three tasks cannot show a quality change; they show the new release
still solves what the old one solved.

## Predictions

| # | Prediction (field) | Result |
|---|---|---|
| P1 | `summary.D1500.decode_tps` >= 49.0 | **FALSIFIED** (44.15; one request, so it also cannot show a regression) |
| P2 | `summary.D1500.decode_tps` below Halogen's same night | **HELD** (44.15 vs 62.95) |
| P3 | `summary.P32K.prefill_tps` within 5% of 923.6 | **HELD** (895.3, -3.1%) |
| P4 | bank leg: `passed` matches E177 on at least 80% of completed tasks | **HELD** (3 of 3 match; partial leg) |

## Limits

One run per engine. Our prompts are prose and code at one user; the maker's gains were at four users and in an 8-bit
long-context mode. Three repeats per prompt cannot resolve a change under about 10%; the maker's own benchmark script on this box,
or ten repeats per prompt, would.
