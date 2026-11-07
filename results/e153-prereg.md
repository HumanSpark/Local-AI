# File: e153-prereg.md
# Purpose: Pre-registration for E153 - gufo, Halogen, Strata and Talus against llama.cpp on Qwen3.8-Flash-Next, one client, one box.
# Project: sparkbench | Date: 2026-11-04
#
# Overview: Four Strix Halo engines publish Flash-Next figures on this exact box model (GMKtec EVO-X2) that disagree with each
# other and with community reports (owner-pasted Reddit thread 2026-11-04: "Halogen 60-65 vs gufo 45-55 tok/s", "75-100").
# E153 serves each engine at its LATEST release (owner rule 2026-11-04) in its shipped configuration, and times every engine
# with one streaming HTTP client (tools/e153_speed.py) on one fixed prompt set (tools/e153_prompts.py), so the comparison
# is the engines, not their harnesses. Written before any arm runs.

# E153 PRE-REGISTRATION - five Flash-Next engines, one client (2026-11-04)

## Question

Which engine serves Qwen3.8-Flash-Next fastest on this box, on which kind of work, and do the published figures hold here?

## Arms (latest release of each, recorded by commit/digest)

| arm | engine | version | weights | drafter | context |
|---|---|---|---|---|---|
| L0 | llama.cpp mainline, Vulkan | build 2451 `5851a8e50` (2026-11-04) | unsloth UD-IQ4_XS | none | `-c 65536 -np 1 -fa on -ctk q8_0 -ctv q8_0 --jinja` (E139's config) |
| L1 | same | same | same | `--spec-type draft-mtp -md mtp-...-shared-Q8_0.gguf` (default draft length) | same |
| G | gufo | 0.29.0, image `sha256:9d77753a...`, engine `883f67b6` | unsloth UD-Q4_K_XL (rev `38bb39ee`, gufo's pin) | MTP, shared-Q8_0 sidecar | `--sessions 1 --context 65536` |
| H | Halogen | 0.18.23, image `sha256:b53c96ed...` | its own v2 checkpoint + n-gram table (repo rev `53113ce2`) | image defaults (draft head + prompt lookup) | image default |
| S | Strata | 0.2.10 / engine 0.1.56 `linux-x86_64-hip-halo` | unsloth UD-IQ4_XS, pack built by `strata launch` | MTP (setup default) | 65536 |
| T | Talus | v0.1.3 release tarball | unsloth UD-IQ4_XS, pack per its MODELS.md | MTP `--spec 5` + suffix drafter (shipped args) | shipped 262144 |
| H-gguf (optional) | Halogen 0.18.23 | as H | unsloth UD-IQ4_XS via `HALOGEN_CHECKPOINT` | draft head file + prompt lookup | image default |

Why the files differ: gufo loads only UD-Q4_K_XL for Flash-Next; Halogen ships its own checkpoint; Strata, Talus and llama.cpp
run UD-IQ4_XS. **A speed gap between G or H and the IQ4_XS arms is engine plus file, not engine alone.** H-gguf is the one arm
that isolates an engine on a shared file (against L0/L1/S/T). No quality is measured in E153 (speed only); a lighter file
winning on speed is stated as such, not as a better engine.

**Declared deviations from "as shipped":** context 65536 where the engine takes a flag and ships larger (gufo native 262144,
Strata), because TTS stays resident (below); Talus keeps its shipped 262144 and falls back to `--max-context 65536` only if
the memory guard fires (that fallback is declared now, not after). Talus's ROCm SDK: the pinned nightly 10.2.0a20261014 if
the owner's install has landed in `var/engines/talus-v0.1.3/rocm-venv` when the window opens; otherwise Strata's bundled ROCm
7.14.1 libraries (hipBLASLt 100401, a table Talus ships) and the arm is labelled **T-rocm714, not Talus as measured upstream**.

## Box state (Rule 8: the config a figure needs)

Kernel `uname -r` and Livepatch recorded at window open. Package power is whatever this box sustains (E152 read 84-85 W);
Talus's figures are from the same box model at **~120 W**, Halogen's at **~85 W**: power is recorded per request and a decode
gap to Talus's README is not attributed to the engine until power is named. sparkrouter's relay is stopped for the window
(`relay_bench_window.sh down`); the TTS services (Chatterbox, Kokoro) stay resident because this account cannot stop them.
The GTT+VRAM they hold is recorded as each arm's baseline. Memory guard: 12 GiB MemAvailable floor, kills the arm.

## Workload (tools/e153_prompts.py -> results/e153/prompts.json, 23 requests)

Greedy, thinking off (`chat_template_kwargs.enable_thinking=false`), single stream, one request at a time, fixed order, one
excluded warm-up. Buckets: CODE x4 and PROSE x4 and JSON x3 (short prompts, 512 generated), AGENT x6 (E152's SWE-agent turns,
1,000-1,800 tokens of context, 400 generated), P8K x3 and P32K x3 (E152's exact-token windows, 256 generated).

**Scored fields (client clock, tools/e153_speed.py):** `decode_tps` = (completion_tokens - 1) / (last text chunk - first
text chunk), completion_tokens from the engine's usage (local tokenizer count recorded beside it; >2% gap = ruler problem,
resolved before any comparison); `prefill_tps` = prompt_tokens / ttft. Bucket figure = median over the bucket.

## Predictions (each names the field it is scored against)

1. **P1 Halogen code.** `H.buckets.CODE.decode_tps_median` >= 58.4 (80% of the README's 73 "writing code"; 0.18.0, 85 W).
2. **P2 Halogen prose.** `H.buckets.PROSE.decode_tps_median` >= 43.2 (80% of 54).
3. **P3 Halogen prefill.** `H.buckets.P32K.prefill_tps_median` >= 1,250 (README 1,740 on a synthetic prompt; it states real
   text through the template runs 8-12% slower; 80% of 1,740 x 0.9).
4. **P4 the Reddit gap.** `H.CODE.decode_tps_median / G.CODE.decode_tps_median` >= 1.15 (dsp457: 60-65 vs 45-55 on an EVO-X2).
5. **P5 Talus.** `T.CODE.decode_tps_median` >= 59.1 (80% of 73.9) and `T.P32K.prefill_tps_median` >= 1,187 (80% of 1,484).
   Registered expecting the power gap (85 vs 120 W) to cost Talus decode; if P5 fails at ~85 W, power is the first suspect.
6. **P6 Strata.** `S.P8K.prefill_tps_median` >= 927 and `S.P8K.decode_tps_median` >= 42.5 (80% of the maintainers' Linux
   UD-IQ4_XS 8K row, 1,159 / 53.1, merged-code defaults).
7. **P7 gufo prefill.** `G.P32K.prefill_tps_median` >= 1,368 (80% of Talus's 1,710 measurement of gufo at 32K).
8. **P8 llama.cpp baseline.** `L0.P32K.prefill_tps_median` in 150-350 (E139 L0, build daef7b6: 216.5) and
   `L0.CODE.decode_tps_median` in 12-25 (E139 serial decode 16.6).
9. **P9 llama.cpp MTP exactness.** Every L1 `content` is byte-identical to its L0 counterpart on CODE, PROSE and JSON
   (greedy speculation must be exact). Falsifier: any difference (cf. E59, upstream #25618). Divergence is reported, not the speed.
10. **P10 the specialised engines earn their keep.** Every one of G, H, S, T has `CODE.decode_tps_median` >= 1.5 x L1's.
11. **P11 workload shape.** For every speculative arm, `CODE.decode_tps_median` > `PROSE.decode_tps_median` (drafts accept
    better on code), so a single "tok/s" figure without the workload is not a property of the engine.

## Gates (an arm that fails a gate is reported as such, not scored)

- G1 ready: `/v1/models` answers within 1,200 s.
- G2 thinking off: `thinking_leaks` == 0 (else the arm measured a different workload).
- G3 ruler: `count_mismatches` == 0, or resolved before comparison.
- G4 fit: the memory guard did not fire.

## Order and banking

L0, L1, G, H, S, T, then H-gguf if time allows. Each arm's JSON, stdout and server log are committed and pushed as it finishes
(bank both sides of a risky run). Results: `results/e153-results.md`, finding(s) from F180.

## Amendment 1 (2026-11-04 ~17:20, declared BEFORE any arm ran)

1. **Weights revision.** unsloth replaced `UD-IQ4_XS` and `UD-Q4_K_XL` on `main` with "Better UD 3.1 quants" between 15:56 and
   16:15 today (new shard counts and sizes), mid-fetch. Every arm uses the ORIGINAL files at gufo's pinned revision
   `38bb39ee` (sha256 verified on arrival against the oids in MANIFEST), which are the files every engine's published figure
   was measured on. The UD 3.1 quants are untested by these engines and are a separate follow-up, not part of E153.
2. **Arm S drafter.** `strata launch --plan` on these files selects **DFlash2** (its default for unsloth UD-IQ4_XS here,
   downloading a 1.2 GB drafter), not MTP as the arms table says. S runs the plan's default, so S is "Strata as shipped".
   Tuning: the plan's default `--tune skip`. P6's thresholds are unchanged (they come from MTP-era maintainer figures, so
   a miss is first read against the drafter change).
3. **Arm T runtime.** The pinned ROCm nightly is not installed (the pip install was blocked by this session's permissions),
   so T runs the declared fallback: **T-rocm714**, Talus v0.1.3 on Strata's bundled ROCm 7.14.1 with its shipped hipBLASLt
   100401 table. P5 is scored but any miss cannot be separated from the runtime change.
4. **Order.** Arms are run in readiness order across two window openings: L0, L1, S, T now (UD-IQ4_XS ready); G, H,
   H-gguf when UD-Q4_K_XL and Halogen's n-gram table finish. Same client, same prompts, relay down for each opening.

## Amendment 2 (2026-11-04 ~18:00, declared BEFORE L1's re-run, H and H-gguf)

1. **L1's draft file.** In opening 1, llama.cpp `5851a8e` could not load gufo's `mtp-...-shared-Q8_0.gguf` as `-md`
   (`check_tensor_dims: tensor 'token_embd.weight' not found`: the shared head borrows the main model's embeddings). The
   server exited at 35 s and the client was stopped at 665 s (rc 143, no records; banked as such). L1 re-runs with unsloth's
   standalone `MTP/mtp-Qwen3.8-Flash-Next-Q8_0.gguf` (rev `38bb39ee`, 4,137,429,120 B, sha256 `cd87e5d1...` verified on
   arrival). P9 and P10 are scored against this L1. If it also fails to load, L1 is reported as "llama.cpp mainline cannot
   run Flash-Next MTP from unsloth's files", and P9/P10 are unscorable.
2. **Halogen files** verified by `sha256sum` after the fetch script crashed before its own hash step (the script was edited
   while running; all three sizes were complete): v2 `71246c6a...`, ngram `3450acad...`, mtp `0f50e962...`, all equal to the
   HF oids in MANIFEST.
3. **Opening 2 order:** L1, H, H-gguf. Same client, prompts, relay down.

## Amendment 3 (2026-11-04 ~18:32, declared BEFORE H-gguf's re-run)

1. **L1 is a load failure, final.** With the standalone MTP head, llama.cpp `5851a8e` loads the draft model and then aborts in
   `llama_context::process_ubatch` with `GGML_ASSERT(buffer) failed` (ggml-backend.cpp:345) - not memory (MemAvailable
   114 GiB at the time). Per amendment 2, L1 is reported as "llama.cpp mainline cannot run Flash-Next MTP from unsloth's
   files on Vulkan"; **P9 and P10 are UNSCORABLE**. L0 (no drafter) is the llama.cpp baseline.
2. **H-gguf configuration.** Opening 2's H-gguf never started: the image looks for the tokenizer beside the checkpoint
   (`no tokenizer.json in /tokenizer`) and the GGUF was mounted at `/models/gguf`. It re-runs with `HALOGEN_TOKENIZER=
   /models/tokenizer`, the variable the error message names. No other change. Its banked opening-2 files are the failed start.
