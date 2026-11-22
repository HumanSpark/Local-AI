<!--
# File: results/e171-prereg.md
# Purpose: Pre-registration for E171 - Tencent Hy4-Flash (220B, 12B active) on Strata, against production on the E167 coding bank.
# Project: sparkbench | Date: 2026-11-22
#
# Overview: Hy4-Flash is the first model larger than Flash-Next that is packed for a 128 GB box. Owner 2026-11-22: "Go
# ahead. Test it." One arm (HY) runs the E167 visible-tests bank unchanged, plus the E163 speed block, in one relay idle
# window with the owner in the building. Written before the model has been loaded or called.
-->

# E171 PRE-REGISTRATION - Hy4-Flash on Strata (2026-11-22)

## In plain English

Tencent released a model about three times the size of the one we run in production. A community engine, Strata, has
squeezed it into packs sized for machines like ours. We test whether the bigger model fixes more of our ten hard coding
tasks than production does (5 of 10) and how fast it really runs here. The model keeps a 63 GiB lookup table on disk and
reads it during every answer, which is new for us and touches the box's one known crash, so the run has extra guards.

## Question

On the E167 bank (ten large real changes, tests visible), does Hy4-Flash solve more tasks than production Flash-Next on
Halogen (H, 5/10, median 685 s)? Secondary: does the maintainer's Strix Halo speed (51-60 tok/s decode, 728 tok/s
prefill, measured on SQ-64) hold for SQ-96 here?

## Arm

| Arm | Model / file | Engine | Sampling |
|---|---|---|---|
| HY | Hy4-Flash `Hy4-Flash-SQ-96.strata` + `Hy4-Flash-Engram-Q8.strata` (repo rev `995bac2`) | Strata 0.2.18: control 0.1.64 `serve/server.py` + `strata-hy4` 0.1.64 hip-halo (build `6e38f588a646`) | 0.9 / top_p 1.0 / top_k off (model card) |

- **Pack choice: SQ-96**, not SQ-128. SQ-128 (107.5 GiB in use, 181 GB on disk) leaves 28 GB of disk and no memory
  headroom; SQ-96 (85.1 GiB) is the card's 128 GiB alternative and drifts less than SQ-64 on tool prompts (KL 0.237 vs 0.518).
- **Context `--max-context 131072`**, as OR35/NM on E167. Declared fallback: 65536 if the load or smoke leaves
  MemAvailable under 12 GiB; that fallback is recorded as an amendment before the bank starts.
- **Thinking:** the server default (`high`, the card's default). DFly2 speculative decoding: engine default (`--draft auto`).
- **One deviation from shipped, for safety:** `HY4_ENGRAM_ODIRECT=1`. Strata reads ~50 random 4 KiB Engram pages per
  decode step with `pread`; by default those go through the page cache, and page-cache pressure on top of a large
  resident model is the F193 deadlock trigger (docs/memory-edge-deadlock.md). O_DIRECT keeps them out of the cache; the
  engine's own host-RAM row cache still applies. It may cost speed; that is a property of this config, not of Strata.
- Vision shard not fetched or loaded (text only).

## Procedure

1. Fetch both packs with `tools/fetch_hf_model.sh` (REVISION pinned), sha256 against the repo's `SHA256SUMS.txt` before
   any load; MANIFEST entry before first use. Hashing finishes before the window opens (no I/O beside the load).
2. Tokenizer: `strata-hy4 --export-tokenizer` from the SQ-96 pack, converted by `tools/hy4_tokenizer.py`.
3. `tools/run_e154_arms.sh HY` with the E167 settings: `E154_BANK=results/e167/bank.jsonl` (sha256 prefix
   `925b63296a2fd720`), `E154_RAW=results/e171/raw`, 3,600 s per task, 200 model calls, `--isolate podman`, one attempt.
   Speed block (`tools/e163_speed.py`, E139 prompts, thinking off, temperature 0) runs first, then the bank.
4. `qwen-image/mem_guard.sh proc:strata-hy4 12` beside the arm. Engine `/proc/<pid>/io` read_bytes logged before and
   after the speed block.
5. Deadline `E154_DEADLINE` = 2026-11-22T19:00Z (owner in the building); unrun tasks are reported as not run, never failed.

## Scored fields

- `HY.pass_count`, `HY.run_count`, `HY.wall_median_s` as E167 (results/e171/raw/HY/<task>.json).
- `HY.speed.P8K.decode_tps`, `HY.speed.P8K.prefill_tps` (results/e171/raw/HY/speed.json `summary`).
- `HY.engram_read_gib` = engine read_bytes delta over the speed block, GiB.
- `HY.load_ok` = ready within 900 s on the first start, with no guard fire in `mem_guard.log`.

## Predictions (each names its field)

1. **P1 loads.** `HY.load_ok` is true.
2. **P2 bigger is smarter.** `HY.pass_count` >= 5 (H on E167).
3. **P3 slower than production.** `HY.wall_median_s` > 685.
4. **P4 maintainer decode does not hold.** `HY.speed.P8K.decode_tps` < 51 (their Strix low end, on the smaller SQ-64).
5. **P5 maintainer prefill does not hold.** `HY.speed.P8K.prefill_tps` < 728.
6. **P6 the disk is in the loop.** `HY.engram_read_gib` > 1.

## Limits, stated before the data

- One sample per task at temperature 0.9; with ten tasks a 1-2 task difference from H is not evidence.
- Engine plus file: no same-model llama-server arm exists (Tencent's GGUFs are 126-157 GiB and need unmerged llama.cpp
  PR #32517), so any result is "Hy4-Flash as Strata packs it", not "Hy4-Flash".
- H's 5/10 is from 2026-11-18 on the same bank and runner settings, not re-run today.
- HY sees the whole E167 bank; GS solved 10/10, so the bank cannot rank HY above frontier.
- Strata uploaded the packs 2026-11-21 (one day old); quantization quality beyond the card's 8-prompt KL is unverified.

## Amendments

(Any change after the arm starts is recorded here with its time before the affected step runs.)
