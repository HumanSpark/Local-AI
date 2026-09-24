# Model manifest - /opt/models/staging

<!--
File: MANIFEST.md
Purpose: Section 4.6 provenance register - one entry per model artefact in the store.
Project: sparkbench | Date: 2026-07-03
#
# Overview: Every download records source URL, repo revision, filename,
# SHA256, quant, licence, and chat template notes BEFORE first use. Promotion
# to /opt/models/production copies the entry and re-verifies SHA256. Entries
# are append-only; deletions from disk keep the entry with a "removed" note
# ("re-downloadable" is made true by this file).
# Retention policy (Alastair, 2026-07-03): artefacts are KEPT unless disk
# space is desperate - re-downloads are expensive, and on-disk models stay
# available for re-benchmarks and Phase B quality comparisons. A failed
# throughput gate is not grounds for deletion.
-->

## fish-speech-1.5 (STAGING - SUPERSEDED 2026-07-25, never fetched)

> **SUPERSEDED by `fishaudio/s2-pro` below.** Real-data-first at T6 task time found the
> `fishaudio/fish-speech` repo has moved two generations on: its current inference code
> targets the S2 generation, and the S2-Pro flagship (4B Dual-AR) is now PUBLICLY
> downloadable at `fishaudio/s2-pro` - which T3 concluded it was not. The 1.5 pin was
> always a fallback for "S2 not downloadable"; that premise no longer holds, and s2-pro
> is the "~5B, brackets-from-above" candidate the WORKPLAN actually intended. This entry's
> own Open item pre-authorised the swap. fish-speech-1.5 was never fetched. Owner confirmed
> the s2-pro benchmark 2026-07-25 ("we are baselining and testing, so we are entitled").

- **Role:** W3 T6 - **full production candidate** (Fish Speech local), benchmarked
  per `docs/plans/2026-07-25-fish-speech-local-prep.md`. Its commercial-entitlement
  question (`docs/plans/2026-07-25-tts-licensing-gate.md`) is PENDING, which means
  **UNDETERMINED, not "leaning no"** (owner correction, 2026-07-25: "the licensing
  is NOT ruled out for fish") - Fish may win the selection; only the evidence text
  is outstanding, and Alastair is reading the account terms directly. Distinct from
  F5-TTS, which has an unambiguous public non-commercial licence and cannot win.
- **Source URL:** https://huggingface.co/fishaudio/fish-speech-1.5
- **Repo:** fishaudio/fish-speech-1.5
- **Revision (main @ pin time 2026-07-25):** 275a984d33c33659e39eed41ff5bcd6e67517f4c
- **Files, sizes, SHA256** (pinned from the HF API before fetch, per the
  download-integrity rule; the two large files are LFS objects whose OID is the
  content SHA256):
  - `firefly-gan-vq-fsq-8x1024-21hz-generator.pth` - 188,518,579 bytes -
    sha256 `01b81dbf753224a156c3fe139b88bf0b9a0f54b11bee864f95e66511c3ccd754`
  - `model.pth` - 1,275,908,030 bytes -
    sha256 `918dc960372cc1b77bbafb14c48ef7a1634ecf75d4eb85b78607223b780d6001`
    (1 of 74 VirusTotal engines flagged this file; ProtectAI/JFrog inconclusive -
    likely a generic pickle-deserialisation heuristic, not confirmed malicious;
    T6 loads with a safe/`weights_only` loader and re-scans the local copy anyway)
  - `config.json` - 697 bytes - sha256 (git blob, non-LFS)
    `3f8edf91f7a0b152e5f8c30fd412c5d7e22020b5` *(this is the git blob SHA1, not a
    content SHA256 - re-verify with a direct hash at fetch time; only the two LFS
    files above have a trustworthy content SHA256 from this API call)*
  - `special_tokens.json` - 30,964 bytes; `tokenizer.tiktoken` - 1,698,810 bytes
    (both non-LFS; hash at fetch time)
- **Licence:** `cc-by-nc-sa-4.0` (non-commercial, share-alike) - gated download,
  requires accepting non-commercial-use terms. Covers benchmark/research use.
- **Quant:** none (fp32/fp16 as published; `dual_ar` architecture, 1.5-generation).
- **Chat template:** n/a (TTS model, not a chat LLM).
- **Open item:** "S2.1" / any S2-generation self-host checkpoint was NOT found in
  public HF/GitHub listings - if Alastair's fish.audio account exposes a different
  download, this entry gets superseded before fetch, not assumed.

## fishaudio/s2-pro (W3 T6 Fish Speech candidate - FETCHED 2026-07-25)

- **Role:** W3 T6 - **full production candidate** (Fish Speech local), the 4B Dual-AR
  flagship that supersedes the fish-speech-1.5 pin above (real-data-first at task time;
  the repo moved on). Benchmarked per `docs/plans/2026-07-25-fish-speech-local-prep.md`
  and the W3 WORKPLAN. This is the "~5B, brackets-the-field-from-above" engine.
- **Licensing (verified live at the LICENSE.md, 2026-07-25):** **Fish Audio Research
  License** (not gated on HF). Grants Research + Non-Commercial use free, and names
  "evaluation and testing" explicitly as a Non-Commercial Purpose - so BENCHMARKING is
  unambiguously permitted (owner confirmed same day). **Commercial use (incl. business
  internal operations / revenue-generating products) requires a SEPARATE written licence
  from Fish Audio** - the public weights do NOT grant it. Whether Alastair's paid
  fish.audio commercial subscription constitutes that separate licence for self-hosted
  weights is the outstanding question he is querying with Fish (tracked in the licensing
  gate; must resolve before s2-pro could WIN the production selection - does NOT block
  Stage-1 testing). This SHARPENS the T1 "PENDING": the public route is non-commercial
  for this use; only the paid-account entitlement could clear it.
- **Source URL:** https://huggingface.co/fishaudio/s2-pro
- **Repo:** fishaudio/s2-pro
- **Revision (main @ pin time 2026-07-25):** 1de9996b6be38b745688de084d87a5633f714e4e
- **Files, sizes, SHA256** (pinned from the HF paths-info API before fetch, Rule 4; the
  three large files are LFS objects whose OID is the content SHA256, verified on arrival
  by `fetch_s2pro.py` which aborts on any size or sha mismatch):
  - `model-00001-of-00002.safetensors` - 4,986,872,984 B -
    sha256 `c4218e8ac93be83b35eee30b4f94cb2e9b5ecff40f3e21611438d2f4f8804aad`
  - `model-00002-of-00002.safetensors` - 4,136,876,104 B -
    sha256 `76738d23465deaac431433232c0762908cc99a6eddc3d49f67307d92680827be`
  - `codec.pth` - 1,871,099,728 B -
    sha256 `74fc41c5a7151c6f350af8bd7e5d6e3accfcc7f3dfbfac23afd35af07052bb2f`
  - `tokenizer.json` - 12,217,872 B -
    sha256 `f24e08099d45a8adf3f52f5f0b03276e433bb9d689bb15fcbcc48ce58744588b`
  - `config.json` (1,863 B), `model.safetensors.index.json` (32,686 B),
    `tokenizer_config.json` (860,832 B), `special_tokens_map.json` (101,864 B),
    `chat_template.jinja` (4,116 B) - non-LFS, size-checked; local sha256 recorded at
    fetch time as provenance.
- **Path:** `fish-speech-tts/repo/checkpoints/s2-pro/` (the container mount point;
  engine dir is gitignored like `kokoro-tts/`).
- **Quant:** none (safetensors as published, fp16/bf16; 4B Dual-AR, S2 generation).
- **Serving route:** upstream `docker/Dockerfile.rocm` (base image
  `docker.io/rocm/pytorch:rocm7.2.3_ubuntu24.04_py3.12_pytorch_release_2.9.1`, custom
  torch 2.9.1+rocm7.2.3) via rootless podman; `tools/api_server.py` on :8080. Native
  venv was not viable (no public torch wheel for ROCm 7.2 + gfx1151).
- **Chat template:** `chat_template.jinja` ships with the checkpoint (S2 is a
  multimodal/dual-AR model; template used by the server, not by us directly).

## SWivid/F5-TTS - F5TTS_v1_Base (W3 T7 research reference - FETCHED 2026-07-25)

- **Role:** W3 T7 - **RESEARCH REFERENCE ONLY** (quality yardstick; CANNOT be the production
  pick). MIT code / **cc-by-nc-4.0 weights** (non-commercial, no commercial route) - verified
  live at the GitHub license API + HF model card 2026-07-25. F5TTS_v1_Base is a DiT
  flow-matching model + vocos vocoder.
- **Source URL:** https://huggingface.co/SWivid/F5-TTS
- **Repo:** SWivid/F5-TTS | **Revision:** 84e5a410d9cead4de2f847e7c9369a6440bdfaca
- **Files, sizes, SHA256** (pinned from HF paths-info before fetch, verified on arrival by
  `f5-tts/fetch_f5.py`):
  - `F5TTS_v1_Base/model_1250000.safetensors` - 1,348,435,761 B -
    sha256 `670900fd14e6c458b95da6e9ed317cdb20dbaf7a1c02ac06a05475a9d32b6a38` (LFS oid, VERIFIED)
  - `F5TTS_v1_Base/vocab.txt` - 13,800 B -
    sha256 `2a05f992e00af9b0bd3800a8d23e78d520dbd705284ed2eedb5f4bd29398fa3c` (non-LFS, size-checked)
- **Auto-downloaded at runtime (small, allowed):** vocos vocoder `charactr/vocos-mel-24khz`
  (F5's decoder) into the container HF cache. Recorded here for provenance.
- **Path:** `f5-tts/checkpoints/F5TTS_v1_Base/` (gitignored engine dir).
- **Serving route:** `f5-tts:rocm` container built FROM the cached `rocm/pytorch:rocm7.2.3` base +
  `pip install f5-tts`; in-container batch (no HTTP server). NOTE: `torchcodec` (an f5-tts dep)
  links CUDA libnvrtc and cannot import on ROCm; torchaudio 2.9 hard-delegates I/O to it, so
  `run_f5_batch.py` routes `torchaudio.load/save` through `soundfile`. Reference = F5's OWN stock
  speaker `basic_ref_en.wav` (not Alastair's voice; cloning out of scope).
- **Result:** 9/9 excerpts, RTF mean 0.60x (~12x faster than Fish s2-pro on the same GPU).

## gpt-oss-120b-mxfp4 (3 shards)

- **Role:** Phase A step 5 stack-validation reference model (WORKPLAN 4.4 -
  benchmarked FIRST, compared against Section 3 community numbers)
- **Source URL:** https://huggingface.co/ggml-org/gpt-oss-120b-GGUF/resolve/main/gpt-oss-120b-mxfp4-0000{1,2,3}-of-00003.gguf
- **Repo:** ggml-org/gpt-oss-120b-GGUF
- **Revision (main @ download):** d932fcea62f83e088d8f076a2cd2d7eb02dfa682
- **Downloaded:** 2026-07-03 (resumable size-verified fetch,
  tools/fetch_gpt_oss_120b.sh; sizes pinned from HF API; no upstream
  SHA256 available - xet-backed repo - so these locally computed values
  are the provenance record)
- **Sizes:** 12,980,384 / 31,738,487,200 / 31,635,878,880 bytes (~63.4GB)
- **SHA256:**
  - shard 1: e2865eb6c1df7b2ffbebf305cd5d9074d5ccc0fe3b862f98d343a46dad1606f9
  - shard 2: 346492f65891fb27cac5c74a8c07626cbfeb4211cd391ec4de37dbbe3109a93b
  - shard 3: 66dca81040933f5a49177e82c479c51319cefb83bd22dad9f06dad45e25f1463
- **Quant:** native MXFP4 MoE (non-expert tensors Q8_0). Community
  reference tables label this artefact family "Q8" - divergence noted in
  docs/PHASE-A-LOG.md step 4c entry.
- **Licence:** Apache-2.0 (per repo card)
- **Chat template:** embedded (harmony format); not exercised by
  llama-bench; must be validated before any eval use.

## Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf

- **Role:** Discovery-matrix "Qwen mid-MoE workhorse" (WORKPLAN 4.4) -
  production-relevant instant-tier candidate; benchmarked FIRST in step 6
  per matrix order set by Alastair 2026-07-03.
- **Selection rationale (names versioned at execution, per 4.4):** Qwen
  publishes no official GGUF of the 2507 refresh (their A3B GGUF repos:
  original hybrid 30B-A3B, VL variants, and 80B Qwen3-Next - wrong class).
  The Instruct-2507 refresh is the current instruct-tuned 30B-A3B and the
  non-thinking variant fits instant-tier structured output. Chosen source:
  unsloth (high-trust quantizer; 511k downloads - the artefact the
  community actually benches). Thinking-2507 is a separate model,
  evaluated separately if ever needed.
- **Source URL:** https://huggingface.co/unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF/resolve/main/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf
- **Repo:** unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF
- **Revision (main @ pin, 2026-07-03):** eea7b2be5805a5f151f8847ede8e5f9a9284bf77
- **Size (HF API authority):** 18,556,686,752 bytes
- **SHA256 (upstream LFS oid - this repo publishes one, unlike the
  xet-backed gpt-oss repo):**
  6c997b8af17debdfb01d890214400ccbab00db6acc0ba8da5de1cc906c4774d0
  - local verification on arrival (2026-07-03): size exact match
    (18,556,686,752 bytes) AND local sha256sum identical to upstream oid.
    VERIFIED.
- **Quant:** Q4_K_M
- **Licence:** Apache-2.0 (per repo card)
- **Chat template:** embedded GGUF chat template (Qwen3 ChatML variant,
  instruct/non-thinking - no reasoning toggle in the 2507 Instruct line).
  Serve with --jinja; not exercised by llama-bench.

## GLM-4.5-Air-Q4_K_M (2 shards)

- **Role:** Discovery-matrix "quality-leaning middle" (WORKPLAN 4.4);
  matrix order #2 per Alastair 2026-07-03. Thinking and non-thinking
  modes evaluated SEPARATELY at eval time (llama-bench does not exercise
  templates, so throughput rows are per-artefact).
- **Selection rationale (names versioned at execution, per 4.4):** no
  official zai-org GGUF exists; unsloth is the high-trust leader (12.3k
  downloads). Execution-time check for a newer Air-class occupant: none -
  GLM-4.6/4.7 are 355B-class, GLM-4.7-Flash (2026-01) is 31B-class (a
  potential rival for the Qwen workhorse row, noted for Alastair, not an
  Air successor). Quant Q4_K_M chosen for first-pass comparability with
  the rest of the matrix (4.4 allows Q4-Q6; a richer quant is a later
  refinement if the model earns it).
- **Source URL:** https://huggingface.co/unsloth/GLM-4.5-Air-GGUF/resolve/main/Q4_K_M/GLM-4.5-Air-Q4_K_M-0000{1,2}-of-00002.gguf
  (repo stores shards in a Q4_K_M/ subfolder; staged FLAT in staging root)
- **Repo:** unsloth/GLM-4.5-Air-GGUF
- **Revision (main @ pin, 2026-07-03):** 506d64aa8c5cfe9dbbf00bc7a15739438f83204d
- **Sizes (HF API authority):** 50,000,746,752 / 22,975,001,632 bytes
  (~73.0GB total)
- **SHA256 (upstream LFS oids):**
  - shard 1: 3e7e5d25a6db33b7c90f8c5203d6f490d6c0a4f04a46f228af0e33727db5df5e
  - shard 2: ac6e50523d45c53faf3bf72d8fe109f3dd54bc6abe98a7773a3636112ead82a6
  - local verification on arrival (2026-07-03): sizes exact match
    (50,000,746,752 / 22,975,001,632 bytes) AND local sha256sums identical
    to upstream oids for both shards. VERIFIED.
- **Quant:** Q4_K_M
- **Licence:** MIT (per repo card)
- **Chat template:** embedded (GLM-4.5 template, thinking toggle). Serve
  with --jinja; validate before eval use.

## gpt-oss-20b-mxfp4.gguf

- **Role:** Step 7 Row A efficiency control (pre-registered fork in
  PHASE-A-LOG 2026-07-03: isolates whether gpt-oss-120b's 67%-of-ceiling
  is model-specific overhead or an MXFP4 quant tax on this box).
- **Source URL:** https://huggingface.co/ggml-org/gpt-oss-20b-GGUF/resolve/main/gpt-oss-20b-mxfp4.gguf
- **Repo:** ggml-org/gpt-oss-20b-GGUF
- **Revision (main @ pin, 2026-07-03):** e1dc459feff949ff451ce107337a2026daa80df8
- **Size (HF API authority):** 12,109,566,560 bytes (~11.3 GiB)
- **SHA256 (upstream LFS oid - available for this repo, unlike the
  xet-backed 120b at its download time):**
  be37a636aca0fc1aae0d32325f82f6b4d21495f06823b5fbc1898ae0303e9935
  - local verification on arrival (2026-07-03): size exact match
    (12,109,566,560 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** native MXFP4 MoE (same artefact family as the 120b
  reference row)
- **Licence:** Apache-2.0 (per repo card; API tags do not surface it)
- **Chat template:** embedded (harmony format); not exercised by
  llama-bench; validate before any eval use.

## Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf

- **Role:** Step 7 Row B workhorse challenger (35B total / 3B active
  hybrid MoE: Gated DeltaNet + Gated Attention, 256 experts, 8 routed +
  1 shared; multimodal - TEXT BENCH ONLY). Pre-registered in PHASE-A-LOG
  2026-07-03: tg128 d0 ~80-90 t/s; pp512 deliberately not predicted
  (Vulkan DeltaNet kernel-maturity measurement); default ubatch 512.
- **Selection rationale (names versioned at execution, per 4.4):** brief
  names the unsloth UD-Q4_K_XL as community standard; Q4_K family for
  matrix comparability. Non-MTP repo chosen (unsloth/Qwen3.6-35B-A3B-
  GGUF, 874k downloads) over the -MTP variant (734k) - the MTP head is a
  speculative-decoding artefact, not the matrix row.
- **Source URL:** https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF/resolve/main/Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf
- **Repo:** unsloth/Qwen3.6-35B-A3B-GGUF
- **Revision (main @ pin, 2026-07-03):** a483e9e6cbd595906af30beda3187c2663a1118c
- **Size (HF API authority):** 22,360,456,160 bytes (~20.8 GiB)
- **SHA256 (upstream LFS oid):**
  707a55a8a4397ecde44de0c499d3e68c1ad1d240d1da65826b4949d1043f4450
  - local verification on arrival (2026-07-03): size exact match
    (22,360,456,160 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** UD-Q4_K_XL (unsloth dynamic Q4_K family)
- **Licence:** Apache-2.0 (per API)
- **Chat template:** embedded; thinking on by default is an eval-time
  concern, not llama-bench's. Multimodal projector not exercised.

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## GLM-4.7-Flash-Q4_K_M.gguf

- **Role:** Step 7 Row C workhorse hedge (31.2B total / ~3-3.6B active
  pure-transformer MoE - no hybrid-kernel risk). Pre-registered in
  PHASE-A-LOG 2026-07-03: tg128 d0 ~75-90 t/s; pp512 expected in
  pure-MoE class (weak pp here is a genuine anomaly).
- **DATE GATE (scoring_func softmax->sigmoid fix, llama.cpp
  2026-01-21):** file lastCommit 2026-02-12T20:09:42Z per HF tree API -
  post-dates the fix, PASS. House build 067de937 (2026-07-03) also
  post-dates it; no rebuild needed.
- **Source URL:** https://huggingface.co/unsloth/GLM-4.7-Flash-GGUF/resolve/main/GLM-4.7-Flash-Q4_K_M.gguf
- **Repo:** unsloth/GLM-4.7-Flash-GGUF
- **Revision (main @ pin, 2026-07-03):** 0d32489ecb9db6d2a4fc93bd27ef01519f95474d
- **Size (HF API authority):** 18,312,339,808 bytes (~17.1 GiB)
- **SHA256 (upstream LFS oid):**
  29837ed2c0fc5f51981adf8ac8083fcf80743c598381f13e9f06cbad0498b174
  - local verification on arrival (2026-07-03): size exact match
    (18,312,339,808 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M. Optional second data point in same repo (NOT the
  matrix row, per brief): GLM-4.7-Flash-MXFP4_MOE.gguf
  (16,968,499,296 bytes, oid ecf4f3fd9448e45d01e1cacb54d9feaf30825
  3d77e97893fac22b78bd9d04c4e, same-dated) - becomes interesting if
  Row A's fork lands on "MXFP4 quant tax".
- **Licence:** MIT (per API)
- **Chat template:** embedded; validate before eval use.

## GLM-4.7-Flash-MXFP4_MOE.gguf

- **Role:** Step 7 addendum - quant-isolation pair, second leg (same
  model as Row C, quant varied). Pre-registered fork in PHASE-A-LOG
  2026-07-03: resolves whether the MXFP4 tax (Row A fork) is
  quant-intrinsic or gpt-oss-family overhead. Green-lit under the
  dual-purpose research reframe. NOT a matrix row.
- **Source URL:** https://huggingface.co/unsloth/GLM-4.7-Flash-GGUF/resolve/main/GLM-4.7-Flash-MXFP4_MOE.gguf
- **Repo:** unsloth/GLM-4.7-Flash-GGUF
- **Revision (main @ pin, 2026-07-03):** 0d32489ecb9db6d2a4fc93bd27ef01519f95474d
- **Date gate:** file lastCommit 2026-02-12T20:41:37Z - post-dates the
  2026-01-21 scoring_func fix, PASS.
- **Size (HF API authority):** 16,968,499,296 bytes (~15.8 GiB)
- **SHA256 (upstream LFS oid):**
  ecf4f3fd9448e45d01e1cacb54d9feaf308253d77e97893fac22b78bd9d04c4e
  - local verification on arrival (2026-07-03): size exact match
    (16,968,499,296 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** MXFP4_MOE (post-hoc community requant - NOT
  quantization-native like gpt-oss; caveat pre-declared in the log)
- **Licence:** MIT (per API)
- **Chat template:** embedded; validate before eval use.

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Qwen3-14B-Q4_K_M.gguf

- **Role:** Phase A step 4b mid-size smoke-test model; discovery-matrix
  "small fast baseline" candidate (WORKPLAN 4.4)
- **Source URL:** https://huggingface.co/Qwen/Qwen3-14B-GGUF/resolve/main/Qwen3-14B-Q4_K_M.gguf
- **Repo:** Qwen/Qwen3-14B-GGUF
- **Revision (main @ download):** 530227a7d994db8eca5ab5ced2fb692b614357fd
- **Downloaded:** 2026-07-03
- **Size:** 9,001,752,960 bytes
- **SHA256:** 500a8806e85ee9c83f3ae08420295592451379b4f8cf2d0f41c15dffeb6b81f0
- **Quant:** Q4_K_M
- **Licence:** Apache-2.0 (per repo card)
- **Chat template:** embedded GGUF chat template (Qwen3 ChatML variant,
  thinking/non-thinking toggle). Served with --jinja; modes must be
  evaluated separately per WORKPLAN 4.4.

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Qwen3-0.6B-Q8_0.gguf

- **Role:** Phase A step 4a tiny smoke-test model
- **Source URL:** https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q8_0.gguf
- **Repo:** Qwen/Qwen3-0.6B-GGUF
- **Revision (main @ download):** 23749fefcc72300e3a2ad315e1317431b06b590a
- **Downloaded:** 2026-07-03
- **Size:** 639,446,688 bytes
- **SHA256:** 9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031
- **Quant:** Q8_0
- **Licence:** Apache-2.0 (per repo card)
- **Chat template:** embedded GGUF chat template (Qwen3 ChatML variant;
  supports enable_thinking toggle). Smoke test uses raw completion, no
  template exercise.

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Qwen3-4B-Instruct-2507-Q4_K_M.gguf

- **Role:** Step 8 Block 2a - dense boundary case for the instant-tier
  "~4B active or fewer" claim (registered band tg128 d0 75-85; the 8K
  badge is a registered QUESTION). Newest instruct variant (2507
  refresh, non-thinking). Fetch doubles as the Block 3c contamination
  source, declared in PHASE-A-LOG step 8.
- **Source URL:** https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_K_M.gguf
- **Repo:** unsloth/Qwen3-4B-Instruct-2507-GGUF
- **Revision (main @ pin, 2026-07-04):** a06e946bb6b655725eafa393f4a9745d460374c9
- **Size (HF API authority):** 2,497,281,120 bytes (~2.33 GiB)
- **SHA256 (upstream LFS oid):**
  3605803b982cb64aead44f6c1b2ae36e3acdb41d8e46c8a94c6533bc4c67e597
  - local verification on arrival (2026-07-04): size exact match
    (2,497,281,120 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M
- **Licence:** Apache-2.0 (per repo card)
- **Chat template:** embedded; validate before eval use.

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Qwen3-8B-Q4_K_M.gguf

- **Role:** Step 8 Block 2b - second dense point within the Qwen
  family (registered band tg128 d0 37-43). No 2507 refresh exists for
  the 8B; base Qwen3-8B artefact.
- **Source URL:** https://huggingface.co/unsloth/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf
- **Repo:** unsloth/Qwen3-8B-GGUF
- **Revision (main @ pin, 2026-07-04):** a6adef130ffb23ddaf1a62fec9dced968c9bc482
- **Size (HF API authority):** 5,027,784,512 bytes (~4.68 GiB)
- **SHA256 (upstream LFS oid):**
  120307ba529eb2439d6c430d94104dabd578497bc7bfe7e322b5d9933b449bd4
  - local verification on arrival (2026-07-04): size exact match
    (5,027,784,512 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M
- **Licence:** Apache-2.0 (per repo card)
- **Chat template:** embedded; validate before eval use.
- **REMOVED FROM DISK** (noted 2026-08-17): the artefact is no longer in
  /opt/models/staging. The entry is kept per the append-only policy - it is what
  makes the file re-downloadable, and the pin above is sufficient to restore it
  byte-for-byte. The removal itself was never recorded at the time, which is the
  defect this note closes: an entry describing a file that is not there, with
  nothing saying so, reads as a present artefact.

## Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf

- **Role:** Step 8 Block 2c - dense FAMILY CONTROL (registered band
  tg128 d0 38-44; a result well off the Qwen 8B number flags the dense
  constant as family-contaminated). meta-llama origin repos are
  HF-gated; ungated community GGUF used per the step 8 pre-registration
  correction 6 (substitution rule).
- **Source URL:** https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf
- **Repo:** bartowski/Meta-Llama-3.1-8B-Instruct-GGUF
- **Revision (main @ pin, 2026-07-04):** bf5b95e96dac0462e2a09145ec66cae9a3f12067
- **Size (HF API authority):** 4,920,739,232 bytes (~4.58 GiB)
- **SHA256 (upstream LFS oid):**
  7b064f5842bf9532c91456deda288a1b672397a54fa729aa665952863033557c
  - local verification on arrival (2026-07-04): size exact match
    (4,920,739,232 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M
- **Licence:** Llama 3.1 Community License (per upstream model card)
- **Chat template:** embedded; validate before eval use.

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## DeepSeek-V2-Lite-Chat.Q4_K_M.gguf

- **Role:** Step 8 Block 2d - second MLA point (FINDINGS F12 fork:
  is MLA-MoE ~0.66 a constant class or Flash-specific?). SUBSTITUTION
  declared: the brief's implied bartowski repo does not exist (HF API
  401); mradermacher static-quant mirror is the highest-download
  ungated Q4_K_M of this model. Older model - support problems mean
  log and skip, no unattended debugging.
- **Source URL:** https://huggingface.co/mradermacher/DeepSeek-V2-Lite-Chat-GGUF/resolve/main/DeepSeek-V2-Lite-Chat.Q4_K_M.gguf
- **Repo:** mradermacher/DeepSeek-V2-Lite-Chat-GGUF
- **Revision (main @ pin, 2026-07-04):** 9ee9f1f8f39f673e1022e176d586aef4228f630d
- **Size (HF API authority):** 10,364,416,768 bytes (~9.65 GiB)
- **SHA256 (upstream LFS oid):**
  5d33e5f045c7a03351c319aafc8afdad94b69d07bb68f36dc9bb5af340b343a4
  - local verification on arrival (2026-07-04): size exact match
    (10,364,416,768 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M
- **Licence:** DeepSeek Model License (per upstream model card)
- **Chat template:** embedded; validate before eval use.
- **Pin-time derivation (house convention, feeds the F12 fork
  amendment in PHASE-A-LOG step 8):** 10.364e9 B / ~15.7e9 params =
  0.660 B/param; 2.4B active -> ~1.58 GB/token -> naive ceiling
  ~139 t/s (vs the brief's implied ~157).

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf

- **Role:** Step 9 gap-filler bench + Phase B coding-eval candidate
  (roadmap entry, Alastair 2026-07-04). Pre-registration gift: same
  arch (qwen3moe), same quant, near-identical bytes (within 3KB) as
  the workhorse Qwen3-30B-A3B-Instruct-2507 - registered tg128 d0
  band 90.5-94; deviation = coder-finetune finding, not physics.
- **Source URL:** https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF/resolve/main/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf
- **Repo:** unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF
- **Revision (main @ pin, 2026-07-04):** b17cb02dd882d5b6ab62fc777ad2995f19668350
- **Size (HF API authority):** 18,556,689,568 bytes (~17.3 GiB)
- **SHA256 (upstream LFS oid):**
  fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad
  - local verification on arrival (2026-07-04): size exact match
    (18,556,689,568 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M
- **Licence:** Apache-2.0 (per repo card)
- **Chat template:** embedded; Coder tool-call format - validate
  before Phase B eval use.

## Llama-4-Scout-17B-16E-Instruct-Q4_K_M (2 shards)

- **Role:** Capability survey Tier 1 #2 (briefing v2, 2026-07-04) -
  "Can I run Llama locally?" is the most common client question.
  MoE 109B total / 17B active, interleaved-attention (iRoPE) arch.
  Registered band: tg128 d0 15-20 (naive ~21.5 from 0.602 B/param x
  17B active; pure-MoE 0.84 central ~18; outside band = arch-factor
  finding per F9/F10). NOTE: ~60.9 GiB weights - AT the F6
  split-invocation line; bench with split -d invocations.
- **Source URL:** https://huggingface.co/unsloth/Llama-4-Scout-17B-16E-Instruct-GGUF/resolve/main/Q4_K_M/Llama-4-Scout-17B-16E-Instruct-Q4_K_M-0000{1,2}-of-00002.gguf
- **Repo:** unsloth/Llama-4-Scout-17B-16E-Instruct-GGUF (briefing's
  bartowski URL does not exist - 401; bartowski's org-prefixed repo
  exists but is 2GB larger; unsloth chosen for house-source
  consistency. Substitution logged.)
- **Revision (main @ pin, 2026-07-04):** 72a6853f56a66dc13a3a4b6bdc9cf7ee4c364b47
- **Size (HF API authority):** shard 1: 49,848,379,744 B; shard 2:
  15,511,520,608 B; total 65,359,900,352 B (~60.9 GiB)
- **SHA256 (upstream LFS oids):**
  - shard 1: fbe956902467171ed7c0c326e5d868771a84d46468d407abecd0f289297313f9
  - shard 2: e7330ae14527f08e8a44a6a573b45084052b8822c4b8a5179c5cad9cd6f6f795
  - local verification on arrival (2026-07-04): both shards size
    exact match AND local sha256sums identical to upstream oids.
    VERIFIED.
- **Quant:** Q4_K_M
- **Licence:** Llama 4 Community License (per upstream model card)
- **Chat template:** embedded; validate before eval use.

## Qwen3-32B-Q4_K_M.gguf

- **Role:** Survey Tier 1 #1 - the dense-vs-MoE within-family test
  (vs Qwen3-30B-A3B workhorse). Registered band: tg128 d0 10-12
  (naive 220/19.76 GB/token ~= 11.1; dense factor ~1.0, n=3).
- **Repo:** unsloth/Qwen3-32B-GGUF | **Revision (pin 2026-07-04):**
  931c84066f88693a02ab8de820cfcd066d913241
- **Size (HF API):** 19,762,150,048 B | **SHA256 (upstream oid):**
  8df67573b2c23484e02ec7af295e39bed7ee774f3771d5fda2978265b59370e7
  - local verification on arrival (2026-07-04): size exact match
    (19,762,150,048 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M | **Licence:** Apache-2.0

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf

- **Role:** Survey Tier 1 #3 - EU/data-sovereignty conversation
  anchor; also the Part 4 quant-ladder subject. Registered band:
  tg128 d0 14.5-16 (naive 220/14.33 ~= 15.4; dense ~0.95-1.0).
- **Repo:** unsloth/Mistral-Small-3.1-24B-Instruct-2503-GGUF |
  **Revision (pin 2026-07-04):** d63ca9416f5db4f54a78145fb9a025317a57289f
- **Size (HF API):** 14,333,910,592 B | **SHA256 (upstream oid):**
  6d670773c3908584349d41a5048d1472226b593c881fd394e8ac196c802e81e2
  - local verification on arrival (2026-07-04): size exact match
    (14,333,910,592 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M | **Licence:** Apache-2.0

## gemma-3-27b-it-Q4_K_M.gguf

- **Role:** Survey Tier 1 #4 - Google's offering; third dense point
  ~27B. Registered band: tg128 d0 12.5-13.8 (naive 220/16.55 ~= 13.3;
  dense ~0.95-1.0). Gemma-3 uses 5:1 local:global SWA - KV-light at
  depth, d0 tg unaffected.
- **Repo:** unsloth/gemma-3-27b-it-GGUF | **Revision (pin
  2026-07-04):** 7cd0121f2530b00e42c4df952d4cad4418c0b3c1
- **Size (HF API):** 16,546,688,736 B | **SHA256 (upstream oid):**
  f1b699659942c777bd3ec0bcb527d6ebf34ae14ca76e3af103d58d0c9cbdadee
  - local verification on arrival (2026-07-04): size exact match
    (16,546,688,736 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M | **Licence:** Gemma Terms of Use

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Qwen3-Embedding-0.6B-Q8_0.gguf

- **Role:** E16 embeddings probe - opens the RAG/retrieval capability
  axis. Official Qwen GGUF.
- **Repo:** Qwen/Qwen3-Embedding-0.6B-GGUF | **Revision (pin
  2026-07-04):** 370f27d7550e0def9b39c1f16d3fbaa13aa67728
- **Size (HF API):** 639,150,592 B | **SHA256 (upstream oid):**
  06507c7b42688469c4e7298b0a1e16deff06caf291cf0a5b278c308249c3e439
  - local verification on arrival (2026-07-04): size exact match
    (639,150,592 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q8_0 | **Licence:** Apache-2.0

## mmproj-F16.gguf (Gemma-3-27B vision projector)

- **Role:** E5 vision probe - enables Gemma-3-27B multimodal via
  llama-server --mmproj. Same repo/revision as the base model entry.
- **Repo:** unsloth/gemma-3-27b-it-GGUF | **Revision (pin
  2026-07-04):** 7cd0121f2530b00e42c4df952d4cad4418c0b3c1
- **Size (HF API):** 857,739,392 B | **SHA256 (upstream oid):**
  debe2545831a2566dcec81992b9aa8fa8381c5a0a3588c0b59a41cc9c610cfe7
  - local verification on arrival (2026-07-04): size exact match
    (857,739,392 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** F16 projector | **Licence:** Gemma Terms of Use

## phi-4-Q4_K_M.gguf

- **Role:** Survey Tier 1 #5 - "modest hardware floor" question
  (14.7B dense). Registered band: tg128 d0 23.5-25.5 (naive
  220/8.89 ~= 24.7; dense ~1.0 - sibling check: Qwen3-14B hit 100%).
- **Repo:** unsloth/phi-4-GGUF | **Revision (pin 2026-07-04):**
  5110b7771e8166d5530e73346a15aea096a8cb99
- **Size (HF API):** 8,890,306,112 B | **SHA256 (upstream oid):**
  01e1f25b3e6931054c6c2227b06f4969828434eebc299e8e171f55dab6814485
  - local verification on arrival (2026-07-04): size exact match
    (8,890,306,112 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M | **Licence:** MIT

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## DeepSeek-R1-Distill-Qwen-32B-Q4_K_M.gguf

- **Role:** Survey Tier 1 #6 - reasoning-model representative +
  second 32B dense point (Qwen2.5 base). Registered band: tg128 d0
  10-12 (naive 220/19.85 ~= 11.1; dense ~1.0). Throughput note:
  reasoning models pay their cost in TOKENS GENERATED (thinking
  traces), not t/s - flag for the survey narrative.
- **Repo:** unsloth/DeepSeek-R1-Distill-Qwen-32B-GGUF | **Revision
  (pin 2026-07-04):** 1938d05cc893a60f37be1dc16e7465038f4fca63
- **Size (HF API):** 19,851,335,584 B | **SHA256 (upstream oid):**
  ca171ca03554ee20cf67ad6b540610ae7eabb95af00c0abd36bb73542e140fb5
  - local verification on arrival (2026-07-04): size exact match
    (19,851,335,584 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M | **Licence:** MIT (per repo card)

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Qwen2.5-Coder-32B-Instruct-Q4_K_M.gguf

- **Role:** Survey Tier 2 #7 - dedicated coding model at dense-32B
  scale. Registered band: tg128 d0 10-12 (naive 220/19.85 ~= 11.1;
  dense ~1.0; expect ~= Qwen3-32B/R1 within noise).
- **Repo:** unsloth/Qwen2.5-Coder-32B-Instruct-GGUF | **Revision
  (pin 2026-07-04):** 638ed91307012a4234ffbec397be520624b4f8f3
- **Size (HF API):** 19,851,335,840 B | **SHA256 (upstream oid):**
  77691d25d120a4708c4b301784e3527d2738024b1cddb7ccc08b8bfdc018aaa3
  - local verification on arrival (2026-07-04): size exact match
    (19,851,335,840 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M | **Licence:** Apache-2.0

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## mixtral-8x7b-instruct-v0.1.Q4_K_M.gguf

- **Role:** Survey Tier 2 #9 - classic MoE reference (47B total,
  ~13B active). Registered band: tg128 d0 12-15 (naive:
  26.44GB/46.7B = 0.566 B/param x 12.9B active -> 7.3 GB/token ->
  ~30 x 0.84 = ~25?? NO - Mixtral active includes shared attention;
  2-of-8 experts + attention ~= 12.9B active -> 7.3GB/token ->
  naive ~30, pure-MoE 0.84 -> ~25. BAND 21-27, wide: 2023-era arch
  on a 2026 stack, kernel-vintage uncertainty declared). Substitution:
  bartowski repo does not exist (401); TheBloke classic used
  (frozen 2023 repo - GGUF vintage noted as a risk; skip-on-failure).
- **Repo:** TheBloke/Mixtral-8x7B-Instruct-v0.1-GGUF | **Revision
  (pin 2026-07-04):** fa1d3835c5d45a3a74c0b68805fcdc133dba2b6a
- **Size (HF API):** 26,441,533,376 B | **SHA256 (upstream oid):**
  9193684683657e90707087bd1ed19fd0b277ab66358d19edeadc26d6fdec4f53
  - local verification on arrival (2026-07-04): size exact match
    (26,441,533,376 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **STATUS: DOES NOT LOAD at llama.cpp 067de937** ("failed to load
  model") - Dec-2023 GGUF predates the modern MoE tensor layout. The
  pre-declared vintage risk fired. KEPT per retention rule as
  evidence ("GGUF archives age; re-conversion required"). Superseded
  by the mradermacher re-conversion below.

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Mixtral-8x7B-Instruct-v0.1.Q4_K_M.gguf (mradermacher re-conversion)

- **Role:** Survey Tier 2 #9 retry - the one-fix substitution after
  the TheBloke vintage failure. Same registered band 21-27 (wide).
- **Repo:** mradermacher/Mixtral-8x7B-Instruct-v0.1-GGUF | **Revision
  (pin 2026-07-04):** 92bb790b153033f0594934ee23bb0e12ba897f4e
- **Size (HF API):** 28,448,468,384 B | **SHA256 (upstream oid):**
  9f8d778c2eb8fd7f8426d03496aec30c46cf4076e98758818cc73d020ed01d44
  - local verification on arrival (2026-07-04): size exact match
    (28,448,468,384 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M | **Licence:** Apache-2.0
- **Quant:** Q4_K_M | **Licence:** Apache-2.0

## Phi-4-mini-instruct-Q4_K_M.gguf

- **Role:** Survey Tier 2 #10 - the absolute floor (3.8B dense).
  Registered band: tg128 d0 79-90 (naive 220/2.49 ~= 88.3; dense
  ~0.9-1.0 with small-model overhead per the 4B point's 0.89).
- **Repo:** unsloth/Phi-4-mini-instruct-GGUF | **Revision (pin
  2026-07-04):** 78eb92a46fc37e6b524df991ed9aca9bc6aa7b80
- **Size (HF API):** 2,491,874,272 B | **SHA256 (upstream oid):**
  88c00229914083cd112853aab84ed51b87bdf6b9ce42f532d8c85c7c63b1730a
  - local verification on arrival (2026-07-04): size exact match
    (2,491,874,272 bytes) AND local sha256sum identical to upstream
    oid. VERIFIED.
- **Quant:** Q4_K_M | **Licence:** MIT

- **REMOVED FROM DISK** (audited 2026-08-17): not present in /opt/models/staging.
  The entry is kept per the append-only policy - the pin above is what makes the
  artefact re-downloadable. WHY it was removed is not recorded and is not invented
  here; the retention rule says artefacts are kept unless disk space is desperate,
  so an unrecorded removal is itself the gap. Do not read this note as a verdict on
  the model.

## Mistral-Small-3.1-24B quant ladder (Part 4; same repo/revision as the Q4_K_M entry, rev d63ca941)

- **Role:** speed/size tradeoff curve on ONE model. Registered
  predictions (corridor, dense ~0.98 x 220/GB): Q5_K_M (16,763,985,472 B,
  oid cb86d837...) -> ~12.9 t/s; Q6_K (19,345,940,032 B, oid
  4a2c8bec...) -> ~11.1 t/s; Q8_0 (25,054,780,992 B, oid 6e237297...)
  -> ~8.6 t/s.
- **Q5_K_M verified 2026-07-04:** size exact, local sha256 identical
  to oid (hashed directly; chain-level hash prints only at invocation
  end). **Q6_K verified 2026-07-04** same method. **Q8_0 verified
  2026-07-04** same method - all three rungs size-exact + oid-matched.

## Kokoro-82M ONNX TTS (kokoro-v1.0.onnx + voices-v1.0.bin)

- **Role:** Local text-to-speech engine for the minisite audio (podcast +
  narrations), adopted after human testing found Piper-medium too flat
  (see results/audio-quality-verdict.md). British voices bm_george /
  bm_lewis (male), bf_emma (female); all synthesis stays on the box.
- **Origin:** github.com/thewh1teagle/kokoro-onnx release
  `model-files-v1.0` (Kokoro-82M by hexgrad). No upstream checksum is
  published, so per the download-integrity rule the locally computed
  SHA256 at verified-fetch time IS the provenance record.
- **kokoro-v1.0.onnx:** 325,532,387 B | sha256
  7d5df8ecf7d4b1878015a32686053fd0eebe2bc377234608764cc0ef3636a6c5
- **voices-v1.0.bin:** 28,214,398 B | sha256
  bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d
  - verified on arrival 2026-07-06: both byte counts exact-match the
    origin Content-Length; SHA256 computed locally via
    kokoro-tts/fetch_kokoro.py. VERIFIED.
- **Licence:** Apache-2.0. Model files gitignored (kokoro-tts/models/ +
  the global *.onnx rule); engine venv at kokoro-tts/venv (gitignored).

## Qwen3-235B-A22B-UD-Q3_K_XL (3 shards)

- **Role:** master-plan Tier 3 probe (docs/briefs/2026-07-05-sparkbench-
  master-plan.md #11), unblocked by the 2026-07-08 ttm.pages_limit
  increase (F26). First "upper limits" phase model - E19 pre-
  registration (results/experiments.md), used in the F25/F26 ROCm/Vulkan
  memory-ceiling investigation and now queued for standard throughput
  benchmarking.
- **Source URL:** https://huggingface.co/unsloth/Qwen3-235B-A22B-GGUF/resolve/main/UD-Q3_K_XL/Qwen3-235B-A22B-UD-Q3_K_XL-0000{1,2,3}-of-00003.gguf
- **Repo:** unsloth/Qwen3-235B-A22B-GGUF
- **Revision (main @ pin, 2026-07-08):** 09e11417ffdc30c1c63d0296a40fd8fde0abb180
- **Quant:** UD-Q3_K_XL (unsloth "Dynamic" mixed-precision quant, not a
  naive Q3_K_XL - chosen over plain Q3_K_M/Q4_K_M, both too large for
  the 112GiB ceiling, see E19 for the size comparison).
- **Sizes (HF API authority):** 49,966,873,920 / 49,935,284,896 /
  3,818,755,488 bytes (103,720,914,304 total = 96.60 GiB)
- **SHA256 (local, verified on arrival 2026-07-08 - no upstream oid
  confirmed for this repo, per download-integrity this locally computed
  hash is the provenance record):**
  - shard 1: 22650dab2363949c1b620b89e4896d3840d1d9365ca190af74ab92800d45a97f
  - shard 2: d4adbe8c470179362108f13bb85e974ec24c03a4c02f1e3d58f8f743ba5f0576
  - shard 3: bd209fa4a28f478ddc2ce7b30d7413e607d291282923cea118c14e159ca2ea3a
  - verified 2026-07-08: all three shards size-exact against the HF
    API-pinned bytes above (tools/fetch_hf_model.sh COMPLETE lines).
    VERIFIED.
- **Licence:** Apache-2.0 (per repo card).
- **Chat template:** embedded Jinja2, thinking/non-thinking toggle
  (standard Qwen3 family pattern); not exercised by llama-bench.

## Step-3.5-Flash-Q3_K_L (3 shards)

- **Role:** "upper limits" phase candidate, backfilled after Alastair
  asked what else could be tested (docs/briefs/2026-07-08-upper-limit-
  candidates.md Tier A #6). First StepFun-lab model in this project;
  genuinely config-free - `step35` architecture, official StepFun GGUF
  quantization built against mainline llama.cpp (b7966), no fork needed
  (unlike Hunyuan Hy3 / DeepSeek V4-Flash, both excluded on this
  ground).
- **Source URL:** https://huggingface.co/bartowski/stepfun-ai_Step-3.5-Flash-GGUF/resolve/main/stepfun-ai_Step-3.5-Flash-Q3_K_L/stepfun-ai_Step-3.5-Flash-Q3_K_L-0000{1,2,3}-of-00003.gguf
- **Repo:** bartowski/stepfun-ai_Step-3.5-Flash-GGUF
- **Revision (main @ pin, 2026-07-08):** a2943ef56a0a240bdfb9a2feee97a775f612476d
- **Quant:** Q3_K_L
- **Sizes (HF API authority):** 39,421,429,440 / 39,903,034,720 /
  14,367,862,304 bytes (93,692,326,464 total = 87.27 GiB)
- **SHA256 (local, verified on arrival 2026-07-08 - no upstream oid
  confirmed for this repo, locally computed hash is the provenance
  record):**
  - shard 1: 873126405c2554c20210a226c2631d2decafa2fea07428d6172607e5b6c2f3c5
  - shard 2: 4d6c0f52440ca755d8d41ebd2fd8473a09b66450a04dccab8ffa6e5e778f165d
  - shard 3: 48e54abd1c619d9dc28784e15d485dfc90758ada8343aaba5ecfd879f2ba4520
  - verified 2026-07-08: all three shards size-exact against the HF
    API-pinned bytes above (tools/fetch_hf_model.sh COMPLETE lines).
    VERIFIED.
- **Licence:** Apache-2.0 (per repo card).
- **Chat template:** not investigated yet - validate before any eval
  use beyond throughput benchmarking (llama-bench doesn't exercise it).

## CohereForAI_c4ai-command-a-03-2025-Q6_K (3 shards)

- **Role:** "upper limits" phase candidate, dense reference (docs/briefs/
  2026-07-08-upper-limit-candidates.md Tier A #5). Cohere's current
  dense flagship (Mar 2025) - one of only three surviving dense entries
  after the 2024-recency cuts (DBRX, Llama 3.3 70B).
- **Source URL:** https://huggingface.co/bartowski/CohereForAI_c4ai-command-a-03-2025-GGUF/resolve/main/CohereForAI_c4ai-command-a-03-2025-Q6_K/CohereForAI_c4ai-command-a-03-2025-Q6_K-0000{1,2,3}-of-00003.gguf
- **Repo:** bartowski/CohereForAI_c4ai-command-a-03-2025-GGUF
- **Revision (main @ pin, 2026-07-08):** 18437d7ebc40a6db851d830447af945dce2dd904
- **Quant:** Q6_K
- **Sizes (HF API authority):** 39,947,852,352 / 39,730,460,320 /
  11,437,084,640 bytes (91,115,397,312 total = 84.86 GiB)
- **SHA256 (local, verified on arrival 2026-07-08 - no upstream oid
  confirmed for this repo, locally computed hash is the provenance
  record):**
  - shard 1: b0f0f2bc6ecf56cc4709020910e5942006af0e3e60be4996a11422af5a235d95
  - shard 2: 42f4773dde0ef9381f47d17f1baff24dd20f4f7b27dbf15aa39290f111720f9e
  - shard 3: cb0901b1b4a8fd4384081cbbd7894369f48f49117972de6e76c6b3c0efd1dfdb
  - verified 2026-07-08: all three shards size-exact against the HF
    API-pinned bytes above (tools/fetch_hf_model.sh COMPLETE lines).
    VERIFIED.
- **Licence:** CC-BY-NC-4.0 - noncommercial. Benchmarking-only use;
  do not treat throughput numbers from this model as cleared for any
  commercial deployment recommendation.
- **Chat template:** not investigated yet - validate before any eval
  use beyond throughput benchmarking (llama-bench doesn't exercise it).

## Devstral-2-123B-Instruct-2512-UD-Q5_K_XL (2 shards)

- **Role:** "upper limits" phase candidate, dense reference (docs/briefs/
  2026-07-08-upper-limit-candidates.md Tier A #4). Coding-specialized
  dense model - contrasts directly against the already-tested Qwen-Coder
  MoE data points. Close to the only genuinely current (Dec 2025) large
  dense release found in this research pass.
- **Source URL:** https://huggingface.co/unsloth/Devstral-2-123B-Instruct-2512-GGUF/resolve/main/UD-Q5_K_XL/Devstral-2-123B-Instruct-2512-UD-Q5_K_XL-0000{1,2}-of-00002.gguf
- **Repo:** unsloth/Devstral-2-123B-Instruct-2512-GGUF
- **Revision (main @ pin, 2026-07-09):** 1f2bfbe35f7f9071d9b318374bf5eeffefab4459
- **Quant:** UD-Q5_K_XL (unsloth "Dynamic" mixed-precision quant)
- **Sizes (HF API authority):** 49,736,388,704 / 38,513,316,160 bytes
  (88,249,704,864 total = 82.19 GiB)
- **SHA256 (local, verified on arrival 2026-07-08/09 - no upstream oid
  confirmed for this repo, locally computed hash is the provenance
  record):**
  - shard 1: 933a8ad117450c778de7273c606d4a402cf83e85c06b3ac97010fe8a1281faca
  - shard 2: 7e178f1da653b3e9a33e22d1557608fbb0e5155e7285e858fd365d2537d27e43
  - verified 2026-07-09: both shards size-exact against the HF
    API-pinned bytes above (tools/fetch_hf_model.sh COMPLETE lines).
    VERIFIED.
- **Licence:** Mistral custom "License: other" (per repo card) - NOT a
  standard open licence. Check terms before any use beyond benchmarking;
  do not assume commercial-deployment clearance.
- **Chat template:** not investigated yet - validate before any eval
  use beyond throughput benchmarking (llama-bench doesn't exercise it).

## MiniMax-M2.7-UD-Q3_K_XL (4 shards)

- **Role:** "upper limits" phase candidate, MoE (docs/briefs/2026-07-08-
  upper-limit-candidates.md Tier A #1). 230B total / 10B active - the
  largest total-parameter MoE in this batch after Qwen3-235B, tests a
  different active/total ratio for the corridor model (F10).
- **Source URL:** https://huggingface.co/unsloth/MiniMax-M2.7-GGUF/resolve/main/UD-Q3_K_XL/MiniMax-M2.7-UD-Q3_K_XL-0000{1,2,3,4}-of-00004.gguf
- **Repo:** unsloth/MiniMax-M2.7-GGUF
- **Revision (main @ pin, 2026-07-09):** d2a05ccf69491b03db0cc40b335aec14bdaf7198
- **Quant:** UD-Q3_K_XL (unsloth "Dynamic" mixed-precision quant)
- **Sizes (HF API authority):** 8,237,824 / 49,700,999,584 /
  49,972,340,896 / 2,258,294,752 bytes (101,939,873,056 total =
  94.94 GiB)
- **SHA256 (local, verified on arrival 2026-07-08/09 - no upstream oid
  confirmed for this repo, locally computed hash is the provenance
  record):**
  - shard 1: dd5563b38555556275aad1965db5a1a04a07b87ab5ace4d279ffa7bcb9edee3e
  - shard 2: 81d8fdf184dd27b92aa7b76247dbec14cc707c8368a2ab01a0015d8debf17296
  - shard 3: 1513ead2c2904a4bbbdccc8fc32538bd23810e718a6b593b8dc177562388518e
  - shard 4: f598a689e9e8653e5ab5ede90b0c622ac0e057f4b399e37e0731c26abe266b52
  - verified 2026-07-09: all four shards size-exact against the HF
    API-pinned bytes above (tools/fetch_hf_model.sh COMPLETE lines).
    VERIFIED.
- **Licence:** "License: other" (per repo card) - custom, not a standard
  open licence. Check terms before any use beyond benchmarking.
- **Chat template:** not investigated yet - validate before any eval
  use beyond throughput benchmarking (llama-bench doesn't exercise it).

## command-a-plus-05-2026-Q3_K_M (3 shards)

- **Role:** "upper limits" phase candidate, MoE (docs/briefs/2026-07-08-
  upper-limit-candidates.md Tier A #3). 218B total / 25B active - highest
  active-parameter count in this batch, tests the corridor model (F10)
  at a different active-weight regime than the other Tier A MoEs.
- **Source URL:** https://huggingface.co/bartowski/command-a-plus-05-2026-GGUF/resolve/main/command-a-plus-05-2026-Q3_K_M/command-a-plus-05-2026-Q3_K_M-0000{1,2,3}-of-00003.gguf
- **Repo:** bartowski/command-a-plus-05-2026-GGUF
- **Revision (main @ pin, 2026-07-09):** a26ba921242484b5e1a8ac8519169fe7421c3ab3
- **Quant:** Q3_K_M
- **Sizes (HF API authority):** 39,125,669,280 / 39,634,282,208 /
  23,818,524,320 bytes (102,578,475,808 total = 95.53 GiB)
- **SHA256 (local, verified on arrival 2026-07-09 - no upstream oid
  confirmed for this repo, locally computed hash is the provenance
  record):**
  - shard 1: 588c532cb3ff49b92d049274fe4f9877b5fd6c929ae0b1454b33e7a0d90cc9b0
  - shard 2: 3829acea82bae69489fc2347a8b3bb8339681fd11c202bb1093ae6c0d67a2892
  - shard 3: 1c8f848486e7f121309398d830811379e94034d447b4fa9dc2c87ddab9c74a58
  - verified 2026-07-09: all three shards size-exact against the HF
    API-pinned bytes above (tools/fetch_hf_model.sh COMPLETE lines).
    VERIFIED.
- **Licence:** Apache-2.0 (Cohere's first fully open license, per repo
  card).
- **Chat template:** not investigated yet - validate before any eval
  use beyond throughput benchmarking (llama-bench doesn't exercise it).

## NVIDIA-Nemotron-3-Super-120B-A12B-UD-Q5_K_M (4 shards)

- **Role:** "upper limits" phase candidate, MoE (docs/briefs/2026-07-08-
  upper-limit-candidates.md Tier A #2). Hybrid Mamba-Transformer MoE -
  architecturally distinct from every other MoE in this batch (all
  standard Transformer-MoE). Last of the original 7 downloads - ALL 7
  DOWNLOADS COMPLETE as of 2026-07-09 00:45.
- **Source URL:** https://huggingface.co/unsloth/NVIDIA-Nemotron-3-Super-120B-A12B-GGUF/resolve/main/UD-Q5_K_M/NVIDIA-Nemotron-3-Super-120B-A12B-UD-Q5_K_M-0000{1,2,3,4}-of-00004.gguf
- **Repo:** unsloth/NVIDIA-Nemotron-3-Super-120B-A12B-GGUF
- **Revision (main @ pin, 2026-07-09):** 036038fb30334a2d56a146c6f0d4871ab5edccbb
- **Quant:** UD-Q5_K_M (unsloth "Dynamic" mixed-precision quant)
- **Sizes (HF API authority):** 7,872,576 / 49,055,956,864 /
  49,336,455,200 / 8,933,414,912 bytes (107,333,699,552 total =
  99.96 GiB). This is the CORRECTED total - see the 2026-07-08 fix in
  docs/briefs/2026-07-08-upper-limit-candidates.md (a manual-addition
  error originally had this at 116,333,699,552/108.34GiB); this
  independent byte-exact recompute at manifest time confirms the
  correction.
- **SHA256 (local, verified on arrival 2026-07-09 - no upstream oid
  confirmed for this repo, locally computed hash is the provenance
  record):**
  - shard 1: d1d07a4920c4a72e7ca9bb036826cbe330393ea8526604b7e0d3a31bc7ec50d6
  - shard 2: 26f94296c578157ccea3707d94db856f808d9c69b1f1a561fb4bc4d39ebab5b6
  - shard 3: a82c2e832bc4a15dec968823859bfe90a9883a8683a921560e3e73d4f46f2210
  - shard 4: fd984136cc63f5194f959087d6dab31d4b1f2659c43185cc1ea9e709f90ba6d3
  - verified 2026-07-09: all four shards size-exact against the HF
    API-pinned bytes above (tools/fetch_hf_model.sh COMPLETE lines).
    VERIFIED.
- **Licence:** "License: other" (per repo card) - custom, not a standard
  open licence. Check terms before any use beyond benchmarking.
- **Chat template:** not investigated yet - validate before any eval
  use beyond throughput benchmarking (llama-bench doesn't exercise it).

## Qwen3.5-397B-A17B-UD-IQ1_M (4 shards)

- **Role:** "upper limits" phase 8th candidate, added 2026-07-09 mid-
  campaign after Alastair reviewed a general web-search list of "best
  local models" (docs/briefs/2026-07-08-upper-limit-candidates.md
  "Round 4"). Largest total-parameter model in this project by a wide
  margin (397B). ALL 8 UPPER-LIMITS DOWNLOADS COMPLETE as of 2026-07-09
  01:24.
- **Source URL:** https://huggingface.co/unsloth/Qwen3.5-397B-A17B-GGUF/resolve/main/UD-IQ1_M/Qwen3.5-397B-A17B-UD-IQ1_M-0000{1,2,3,4}-of-00004.gguf
- **Repo:** unsloth/Qwen3.5-397B-A17B-GGUF
- **Revision (main @ pin, 2026-07-09):** da33c16fa4440f831149fcf53b98a22bc07785e5
- **Quant:** UD-IQ1_M (unsloth "Dynamic" mixed-precision quant, extreme
  low-bit - ~2.1-bit average). Chosen over UD-IQ2_XXS (106.98GiB, only
  ~5GiB headroom below the 112GiB ttm.pages_limit ceiling - same
  near-edge margin implicated in the F24 amdgpu SDMA deadlock) for
  safety margin, per Alastair's stated priority of a complete benchmark
  set over maximum quant quality.
- **Sizes (HF API authority):** 10,943,552 / 49,897,900,576 /
  49,924,410,496 / 6,986,622,432 bytes (106,819,877,056 total =
  99.48 GiB)
- **SHA256 (local, verified on arrival 2026-07-09 - no upstream oid
  confirmed for this repo, locally computed hash is the provenance
  record):**
  - shard 1: 19bb2dc33582a81373f61ba7c98708ce4d1ed7b5847d97ee75f549c74b537f15
  - shard 2: b91d0daad21e4134e4061c261180c988c0c0334fdddc9c3972496ba3a41fe9ff
  - shard 3: ecbcb88aad6f35acc5b01bddfc554c0f01d18d50c1aa7825f8aa224c8cba17bb
  - shard 4: 48654392c8f05da71eb6f79d25654ba4a480fe0c97b0489ea78aea2f993d5d0b
  - verified 2026-07-09: all four shards size-exact against the HF
    API-pinned bytes above (tools/fetch_hf_model.sh COMPLETE lines).
    VERIFIED.
- **Licence:** Apache 2.0 (per repo card).
- **Quality caveat for reporting:** ~2.1-bit average precision is well
  below every other model in this batch (~3.5-bit) and Section 2's
  established models (typically Q4_K_M/Q5_K_M). Any throughput number
  from this model needs an explicit quant-quality caveat in the report -
  do not present it alongside better-quantized models without that
  context, per the "no hand-waved discrepancies" discipline.
- **Chat template:** not investigated yet - validate before any eval
  use beyond throughput benchmarking (llama-bench doesn't exercise it).

## Qwen3-30B-A3B-Instruct-2507 quant ladder (E29 compression-vs-quality curve, 2026-07-11)

- **Source repo:** unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF (HF), same repo
  family as the banked Q4_K_M workhorse file. Purpose: the one-family-deep
  compression curve (plan Task 10/11; brief Section 6). Deviation declared:
  7 rungs fetched vs the plan's "target 6" - UD-IQ1_M added because it is
  the same ~1.75-bit class as the Qwen3.5-397B headline finding, UD-TQ1_0
  as the ternary floor (a load failure there is itself a finding).
- **Fetched 2026-07-11** via tools/fetch_hf_model.sh, strict sequential,
  sizes pinned from the HF API tree BEFORE fetch; every local sha256 equals
  the repo's LFS oid (checksum-exact provenance, stronger than size-only):
  - Q8_0.gguf - 32,483,932,576 B - sha256/oid 47514861adaa7ae7f32818fe54595c7cbed2753417ba78df53054fcf7b9dcd88
  - Q6_K.gguf - 25,092,532,640 B - sha256/oid b1a3ed3bc584d58d25253c408cbbf894f974dffa2df74e016469289e686ef701
  - Q3_K_M.gguf - 14,711,847,328 B - sha256/oid e145c9d2f5d11c9583eb099aa75100b7ab943e77d5240c9a2cd936f81c89ef43
  - Q2_K.gguf - 11,258,610,080 B - sha256/oid 50a46f567cf1f4d687f9d5b8d4641654e71a4cfb7b02baab479dedc0bd05d3d3
  - UD-IQ2_XXS.gguf - 10,341,814,688 B - sha256/oid aa0b04ac05f71aa94b542b074500b3de956608365e74f0e1d97ae0d6a6380269
  - UD-IQ1_M.gguf - 9,685,733,792 B - sha256/oid d527a854db2a1582a3ce746a17b1f42d860334ece18d385ede9e2e395058b39e
  - UD-TQ1_0.gguf - 8,094,142,880 B - sha256/oid 096637927b14939158966d17d929ce0aacba68bb2387e657e14168a5d76c425d
- **Licence:** Apache 2.0 (per repo card).
- **Curve context:** existing rung Q4_K_M (17.28 GiB, manifested 2026-07-03)
  completes the 8-point ladder Q8_0 -> TQ1_0.

## Mistral-Small-4-119B-2603 (UD-Q4_K_M, 3 shards) - big writing-model candidate

- **Source repo:** unsloth/Mistral-Small-4-119B-2603-GGUF (HF), subfolder
  UD-Q4_K_M. Purpose: the fastest big-Mistral MoE (119B total / ~6B active) as
  a drafting-quality candidate in the attended big-model writing test - the
  #2 pick on two independent 2026 "best local writing model" shortlists, and
  the lowest-active-param (=fastest) big model on either list.
- **Fetched 2026-07-13** via tools/fetch_hf_model.sh (sg models), strict
  sequential, sizes pinned from the HF API tree BEFORE fetch; every local
  sha256 equals the repo's LFS oid (checksum-exact provenance) and every size
  matches the authority:
  - UD-Q4_K_M-00001-of-00003.gguf - 7,875,616 B - sha256/oid fd3cc46082e4e64eb623eea4611b02583d1de4c20a59411bf1820925d5117dfe
  - UD-Q4_K_M-00002-of-00003.gguf - 49,299,298,464 B - sha256/oid f357d8dc029824fa4515ae60d7a8b7e108546763614f16c00a1b4ea0cd94145c
  - UD-Q4_K_M-00003-of-00003.gguf - 24,456,006,464 B - sha256/oid 9dc960d67fb1ef23029d24878b4cf6c63b743ab26cf9137402549591bd770c50
  - Total 73.76 GB (fits 128 GB unified RAM with -c 8192; well clear of the
    memory edge when the box is quiet - see docs/memory-edge-deadlock.md).
- **Licence:** Apache 2.0 (per repo card).

## Llama-3.3-70B-Instruct (Q4_K_M) - max tool-call-reliability local agent model

- **Source repo:** bartowski/Llama-3.3-70B-Instruct-GGUF (HF), ungated. Purpose: the community's
  highest well-formed-tool-call local model that fits 128GB unified RAM - the reliability arm for
  the Hermes local-agent test (vs Qwen3-Coder-30B the coding-agent default).
- **Fetched 2026-07-13** via tools/fetch_hf_model.sh (LIMIT_RATE 8M), size pinned from HF API,
  sha256 verified == HF LFS oid:
  - Llama-3.3-70B-Instruct-Q4_K_M.gguf - 42,520,398,816 B - sha256/oid 32df3baccb556f9840059b2528b2dee4d3d516b24afdfb9d0c56ff5f63e3a664
- **Licence:** Llama 3.3 Community License.

## ggml-small.en-tdrz.bin (tinydiarize)

- **Role:** Speaker-diarisation probe (2026-07-17). Whisper `small.en` fine-tuned to emit a
  speaker-TURN token, converted to ggml. Runs on the existing whisper.cpp Vulkan build via
  `-tdrz` - no rebuild, no new dependencies. Chosen because it is the only diarisation option
  fetchable on this box today: pyannote's weights are MIT but `gated: auto` and we hold no HF
  token (docs/plans/2026-07-17-diarisation-investigation.md).
- **Source URL:** https://huggingface.co/akashmjn/tinydiarize-whisper.cpp/resolve/d44ba793fc67e509623a88a409723311fa677744/ggml-small.en-tdrz.bin
- **Repo:** akashmjn/tinydiarize-whisper.cpp (gated: False, private: False)
- **Revision (pinned at download):** d44ba793fc67e509623a88a409723311fa677744
- **Downloaded:** 2026-07-17
- **Size (HF API authority):** 487,614,184 bytes - verified exact on arrival.
- **SHA256 (published upstream on the model card, verified on arrival):**
  ceac3ec06d1d98ef71aec665283564631055fd6129b79d8e1be4f9cc33cc54b4
  Both size and checksum matched before first use (Rule 4 / download-integrity).
- **Path:** /opt/models/staging/whisper/ggml-small.en-tdrz.bin
- **Licence:** MIT (per model card)
- **Caveat:** `small.en` - English-only, and the SMALL model, against our production
  large-v3-turbo. It marks speaker TURNS, not speaker IDENTITY; it cannot attribute speech to a
  named person. Not a drop-in upgrade - see the investigation doc.

## wespeaker-voxceleb-resnet34-LM (ONNX) - speaker EMBEDDING for identity diarisation

- **Role:** The identity-bearing half of the diarisation stack (2026-07-17). Produces a speaker
  embedding per speech window; clustering those embeddings is what turns "someone else is talking"
  into "this is the same person who spoke earlier". ONNX, so it runs under onnxruntime on CPU -
  no torch, no torchaudio, and therefore NO risk to var/ft-venv (F37's proven ROCm stack).
- **Why this repo:** pyannote/speaker-diarization-3.1 is `gated: auto` and we hold no HF token.
  But pyannote 3.1's own embedding model IS wespeaker-voxceleb-resnet34-LM, which pyannote
  MIRRORS from WeSpeaker. The upstream `Wespeaker/` original is ungated and additionally ships a
  ready-made ONNX export. The identity capability was never gated - only the pipeline wrapper
  around it was. No gate was bypassed: this is the authors' own public distribution.
- **Source URL:** https://huggingface.co/Wespeaker/wespeaker-voxceleb-resnet34-LM/resolve/f0c48c298fd835726c27956a5d617bad7115627e/voxceleb_resnet34_LM.onnx
- **Repo:** Wespeaker/wespeaker-voxceleb-resnet34-LM (gated: False, private: False)
- **Revision (pinned at download):** f0c48c298fd835726c27956a5d617bad7115627e
- **Downloaded:** 2026-07-17
- **Sizes (HF API authority) - verified exact on arrival, BEFORE first use:**
  - voxceleb_resnet34_LM.onnx - 26,530,309 B - sha256 == HF LFS oid
    7bb2f06e9df17cdf1ef14ee8a15ab08ed28e8d0ef5054ee135741560df2ec068
  - config.yaml - 1,673 B - sha256
    3cf7d3243464cd939083e29d2be65c2abcdd954c1a64559bad73b74ffdb0db3e
- **Path:** /opt/models/staging/wespeaker/
- **Licence:** CC-BY-4.0 (per model card). NOTE: attribution required, and CC-BY is a
  content licence - it is more permissive than the pyannote gate but carries an attribution
  obligation any published work must honour.

## ggml-silero-v6.2.0.bin (Silero VAD) - stops whisper HALLUCINATING over silence

- **Role:** Voice-activity detection for the transcription pass (2026-07-17). Not an accuracy
  nicety - a CORRECTNESS fix. Without VAD, whisper large-v3-turbo INVENTS SPEECH over silence: the
  35-min client call's 120s of opening dead air produced four fabricated "Thank you" segments, and
  a 180s clip of the same audio fabricated six, including "I'm going to go to the next meeting with
  Marina and Claire" - words nobody said. With `--vad` the transcript jumps cleanly from 4.1s to
  2:29.9, where speech actually resumes. A wrong speaker LABEL is visible to a reader; invented
  SPEECH is not. See results/diarisation/e40-vad-and-limits.md.
- **Why this repo:** whisper.cpp ships `models/for-tests-silero-v6.2.0-ggml.bin`, which works - but
  it is a TEST FIXTURE and nothing guarantees its retention or identity across checkouts. This is
  the canonical upstream publication of the same model, pinned and verified.
- **Source URL:** https://huggingface.co/ggml-org/whisper-vad/resolve/9ffd54a1e1ee413ddf265af9913beaf518d1639b/ggml-silero-v6.2.0.bin
- **Repo:** ggml-org/whisper-vad (gated: False, private: False)
- **Revision (pinned at download):** 9ffd54a1e1ee413ddf265af9913beaf518d1639b
- **Downloaded:** 2026-07-17
- **Size (HF API authority):** 885,098 bytes - verified exact on arrival, BEFORE first use.
- **SHA256 (== HF LFS oid, verified on arrival):**
  2aa269b785eeb53a82983a20501ddf7c1d9c48e33ab63a41391ac6c9f7fb6987
- **Path:** /opt/models/staging/whisper/ggml-silero-v6.2.0.bin
- **Licence:** MIT (Silero VAD; per the ggml-org/whisper-vad model card)

## AMI Meeting Corpus (test split, IHM + SDM) - the first REAL ground truth in the diarisation work

- **Role:** Human-annotated diarisation ground truth (2026-07-17). Every diarisation number in
  sparkbench so far (E38-E40, 3.51% segment error) was measured against an **Otter.ai** reference
  that Alastair estimates at ~98% - and which I hand-typed, dropping a turn that I then blamed on
  the model for two write-ups (see F44 / e39). AMI removes BOTH weaknesses: real human annotation,
  no hand transcription, and a public corpus so results are publishable without the SHAPE-only
  restriction our meeting recordings carry. It also removes the "every recording contains Alastair's
  voice" limit - AMI speakers are ones this embedder has never heard.
- **Source repo:** diarizers-community/ami (HF dataset, gated: **False**, private: False)
- **Revision (pinned at download):** 8cdaae2eaf968f3b000b6eb1204ab9b8db006ed0
- **Downloaded:** 2026-07-17. All six shards verified size + sha256 == HF LFS oid BEFORE first use:
  - ihm/test-00000-of-00003.parquet - 294,805,285 B
  - ihm/test-00001-of-00003.parquet - 320,717,753 B
  - ihm/test-00002-of-00003.parquet - 297,347,295 B
  - sdm/test-00000-of-00003.parquet - 328,468,433 B
  - sdm/test-00001-of-00003.parquet - 330,816,079 B
  - sdm/test-00002-of-00003.parquet - 313,385,370 B
  - TOTAL 1.89 GB (test split only; the train split is 19 shards and was NOT fetched - disk was at
    24 GB free, and the benchmark needs test only)
- **Path:** /opt/models/staging/ami/
- **Licence:** **CC-BY-4.0 - ATTRIBUTION REQUIRED.** Any published result using this corpus must
  credit the AMI Meeting Corpus. This is a licence obligation, not a courtesy.
- **Contents:** audio (16 kHz) + per-segment `timestamps_start` / `timestamps_end` / `speakers`.
  Two conditions: **IHM** (Individual Headset Microphone - close-talk, clean) and **SDM** (Single
  Distant Microphone - far-field, one mic in the room; the realistic meeting case).
- **Note:** the annotation contains genuinely OVERLAPPING segments (real crosstalk). Our stack
  assigns ONE speaker per window and therefore cannot represent overlap at all - AMI is the first
  test that can expose this.
- **No transcripts in this dataset**, so it scores DER only. WER against real ground truth needs a
  separate corpus (LibriSpeech test-clean) - not fetched yet.

## silero-vad.onnx (onnx-community) - FETCHED, VERIFIED, and NOT ADOPTED

- **Role:** attempted replacement for the energy gate in the speaker pass (E43). **Not used.**
- **Source:** https://huggingface.co/onnx-community/silero-vad (gated: False, MIT), rev
  e71cae966052b992a7eca6b17738916ce0eca4ec, `onnx/model.onnx` - 2,243,022 B, sha256 == LFS oid
  a4a068cd6cf1ea8355b84327595838ca748ec29a25bc91fc82e6c299ccdc5808. Verified on arrival.
- **Path:** /opt/models/staging/silero-vad/silero-vad.onnx
- **Why not adopted:** our onnxruntime port under-detects relative to whisper.cpp's C++
  implementation of the SAME Silero weights (60.9% vs 71.4% coverage on jfk.wav). Rather than debug
  our port, we use `whisper.cpp/build/bin/whisper-vad-speech-segments`, which is already built,
  already trusted (it is what kills the "Thank you" fabrication, F44), and uses the ggml Silero
  model already manifested above. Kept on disk (retention rule) and left manifested so the
  provenance survives if the ONNX path is revisited.
- **Note on the rejection:** the first rejection reason recorded was wrong. I rejected it because
  it scored 60.9% on jfk.wav where I "expected ~90%+" - but jfk.wav genuinely contains ~28% pause,
  and whisper.cpp's own VAD scores 71.4% on the same file with 4 segments that match the 4 phrases
  exactly. **My expectation was the faulty instrument, not the model.** The port may be fine; it is
  simply not needed.

## LibriSpeech test-clean (openslr/librispeech_asr) - true WER ground truth

- **Role:** The first TRUE WER measurement (2026-07-17). E42 compared model sizes against an
  Otter.ai transcript (~98% accurate, hand-copied by me), giving DISAGREEMENT rates with a ~2%
  floor - not WER. LibriSpeech is the standard ASR benchmark with real human transcripts, and it
  has a well-known published value (~2-3% for whisper large-v3), which makes it a HARNESS CHECK as
  well as a measurement - and it caught a bug that had inverted our result.
- **Source:** https://huggingface.co/datasets/openslr/librispeech_asr, `clean/test/0000.parquet`
- **Revision (pinned):** 71cacbfb7e2354c4226d01e70d77d5fca3d04ba1
- **Downloaded:** 2026-07-17. Size 350,452,636 B, sha256 == HF LFS oid
  7113aa4c3cf963fb54697145719a7725f984c8836d1c494a554cbb9f1a017df0. Verified before first use.
  Only test-clean fetched (the full corpus is 123 GB; disk was at 22 GB free).
- **Path:** /opt/models/staging/librispeech/test-clean-0000.parquet
- **Contents:** 2620 utterances, 16 kHz, with human reference text.
- **Licence:** CC-BY-4.0 (LibriSpeech) - attribution required in any published use.
- **Caveat for interpretation:** read speech from audiobooks. Clean, single-speaker, no crosstalk,
  no meeting acoustics. It is the EASY case: it validates the model COMPARISON, not the meeting use
  case. Our meeting-audio figure is ~10.6% disagreement vs Otter (E42), not 2.40%.

## Qwen3-TTS-12Hz-1.7B-CustomVoice (W3 Stage-2 TTS candidate)

- **Role:** First Stage-2 engine in the W3 TTS selection benchmark (T11). Discrete multi-codebook
  LM + a 12 Hz speech tokenizer, 1.7B. Chosen as the first Stage-2 stand-up because it is
  Apache-2.0 on BOTH code and weights and is by a wide margin the most-used model in the admitted
  field (~2.5M downloads vs ~24k for CosyVoice3).
- **Source:** https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice
- **Revision (pinned):** 0c0e3051f131929182e2c023b9537f8b1c68adfe
- **Downloaded:** 2026-07-25 via `qwen3-tts/fetch_qwen3tts.py`. 11 runtime files,
  4,520,159,586 B total (4.21 GiB), all size-verified against sizes pinned from the HF API tree
  endpoint at that revision, BEFORE first use. The two LFS files were additionally sha256-verified
  against their published oids:
  - `model.safetensors` 3,833,402,552 B, sha256 ==
    38b1d5971bdbd982b561cccec982669a53b0537c3cf5e9bd4778ed07bb2f5137 (matches HF LFS oid)
  - `speech_tokenizer/model.safetensors` 682,293,092 B, sha256 ==
    836b7b357f5ea43e889936a3709af68dfe3751881acefe4ecf0dbd30ba571258 (matches HF LFS oid)
  The 9 non-LFS files publish no oid; they are size-verified, and their locally computed sha256 at
  verified-fetch time IS the provenance record (see download-integrity.md rule 4). Full list in the
  fetch script's output. `.gitattributes` (1,519 B) and `README.md` (57,846 B) were deliberately not
  fetched, which is the whole of the 59,365 B difference from the repo's 4,520,218,951 B API total.
- **Path:** /home/agent-spark/sparkbench/qwen3-tts/checkpoints/Qwen3-TTS-12Hz-1.7B-CustomVoice
  (gitignored; engine dirs hold weights, the repo holds scripts)
- **Licence:** apache-2.0 on code AND weights, re-verified live at the HF API on 2026-07-25 -
  commercial-clear, PASSES the T1 licensing gate with no entitlement question attached (contrast
  Fish, which is PENDING, and F5-TTS, which is cc-by-nc-4.0 research-only).
- **VARIANT NOTE - the trap:** this is `-CustomVoice`, NOT the similarly-named `-Base`. Base is a
  3-second VOICE CLONE model with no stock voices; CustomVoice is the stock-timbre variant (9
  built-in speakers, of which Ryan and Aiden are English-native). The W3 WORKPLAN scopes voice
  cloning explicitly OUT, so Base is the wrong artefact for this benchmark despite its name reading
  like the default. Caught by reading the model card rather than inferring from the name.
- **Runtime caveat:** the model card recommends `attn_implementation="flash_attention_2"`.
  FlashAttention 2 has no gfx1151 build - the runner uses `sdpa` instead. FA2 is a memory/speed
  optimisation, not a correctness requirement.

## W3 voice-cloning REFERENCE AUDIO (2026-07-26)

The W3 field collapsed to three engines - Chatterbox, VoxCPM2, F5-TTS - that are all voice-CLONING
designs. The narration voice is therefore an **input** (a reference clip), not a property of the
engine, so the reference clips are benchmark artefacts in their own right and are recorded here.
**All reference audio is gitignored** (`stage2-sweep/out/`) per the owner's no-binaries-in-repo rule;
this manifest plus the per-clip JSON sidecars are the provenance record, and every clip is
regenerable from them.

### VCTK - licensed British-female candidates

- **Role:** commercially-usable British female reference voices, for the narration track. Sourced
  because the female-only rule (owner, 2026-07-26) left no usable reference on the box, and the
  owner chose "I source a licensed clip" over supplying one or cloning a synthetic voice.
- **Source:** `sanchit-gandhi/vctk` via the HF datasets-server (parquet-backed; the authoritative
  `CSTR-Edinburgh/vctk` repo is a loader script pointing at an ~11 GB Edinburgh DataShare zip,
  disproportionate for one clip). Fetched by `stage2-sweep/fetch_refvoice.py`.
- **Revision (pinned):** `73ef4ee7d49a6fed4ea1efd65f82b4c95faeb9de` - the signed asset URLs are
  revision-scoped, so this is the provenance anchor.
- **Licence:** **CC BY 4.0**, read from the authoritative CSTR repo README rather than a mirror's
  tag. Commercial use permitted **with attribution**. Required citation is carried in every sidecar:
  Yamagishi, Veaux & MacDonald, *CSTR VCTK Corpus* (v0.92), University of Edinburgh CSTR.
  **If a VCTK voice ships, the attribution ships with it.**
- **Speakers** - selected from the dataset's own gender/accent/region columns, never recalled ids.
  Each clip is the same four rainbow-passage utterances, so a listener comparing speakers hears
  timbre rather than different words:

  | Speaker | Gender/age | Region | Duration | sha256 (first 16) |
  |---|---|---|---|---|
  | p225 | F 23 | Southern England | 23.68s | `47b163be82d34c82` |
  | p228 | F 22 | Southern England | 26.45s | `b988774bbef23cab` |
  | p229 | F 23 | Southern England | 19.07s | `7c82b775548e69c1` |
  | p230 | F 22 | Stockton-on-tees | 23.34s | `bf358612fba13b23` |
  | p231 | F 23 | Southern England | 17.35s | `3483a219adf6e32e` |

- **TRAP, and it bit:** the metadata was initially read from `rows[0]` of a window that spans TWO
  speakers, reporting p227's data (M 38 Cumbria) under p228. Off by exactly one speaker. Fixed by
  filtering on `speaker_id` with an explicit gender assertion. The audio was correct throughout
  (proved by byte-identical sha256 across the re-fetch), but the code could have mixed two speakers
  into one reference clip.

### Owner-supplied recordings (test references, NOT for publication)

- **`uk-audio1.mp3`** 16,367,903 B, sha256 `a4662bc03ed48e94f611fa49...` - **REJECTED by the owner:
  contains audience clapping.** Also structurally poor for this use: 252 speech runs averaging
  1.60s (conversational), only 4 runs over 9s.
- **`uk-audio2.mp3`** 8,862,931 B, sha256 `cef2893043d6bc8ec959f343...` - usable; monologue-shaped
  (113 runs averaging 4.33s, 88% speech). Owner approved the 441.3-455.5s and 346.0-359.2s clips;
  156.8-170.7s was rejected for sibilance.
- **Source:** Alchemy (`McDermott, Alastair/Alchemy/`). **This box has no WebDAV credential and no
  `secret-tool`**, so the working route is via sparkline (which has both), then `scp`, verifying
  sha256 on both ends - byte sizes matched the remote listing exactly.

### The Recognized Authority podcast - the owner's own voice

- **Role:** reference for cloning the owner's own voice. Explicitly exempted from the female-only
  rule (owner: *"I am superseding the female only rule for ME and ME only"*).
- **Episode:** "Positioning Yourself as the Go-To Expert in Your Niche [Listener Question]", 18:58.
- **Source:** enclosure from the show's RSS feed `https://feed.pod.co/marketing-for-consultants`.
  **Do not scrape the episode page for this** - it embeds every episode's MP3, and the URL nearest
  the episode slug was a DIFFERENT episode than the feed's enclosure. The feed is the authority.
- **Verified:** 16,007,842 B on arrival == the enclosure's declared `length`, pinned BEFORE fetching.
  sha256 `5e7f4df9e9faccbe52d93c2a5b4ec1d76d314fd33f31c24f7858ace1260caa05`.
- **Clip extraction caveats:** the first ~10s is a **female voiceover intro** - a reference clip in
  someone else's voice is the one thing that must never happen, and no automated screen catches it
  (it is clean, well-levelled speech). Excluded via `--skip-start 25 --skip-end 75`. The episode
  also peaks at +0.71 dBFS with astats **flat factor 0.000000** - loud mastering, zero clipping;
  a peak-based screen would have rejected the whole episode.
- **Owner's clip ranking** (best first): 975.9-988.5s, 553.2-567.7s, 859.9-874.8s, 144.7-158.5s -
  *"all pretty decent"*.

### The Material-Outcome Test judge rubric (third-party, adopted 2026-08-11)

- **`spikes/eval-pilot/rubrics/material-outcome-test.md`** - LLM-judge prompt scoring answers by
  what materially changes for the client, not by polish or length. Body below the provenance block
  is a **verbatim** copy: 7,976 B, sha256
  `7e58b951cb86e4deba3b60fd01e9b9bd247ebe9883e1c9e43b24acffb1fd4667`, re-verified byte-identical
  on copy (2026-08-11).
- **Source:** https://legal-benchmarks.netlify.app/ release `CV-LRB-2026.08.10-R9`, files
  `evidence/series-1/eval_prompt.txt` and `evidence/series-2/eval_prompt.txt` - both series carry
  the identical file and both hashes were recomputed independently from the mirror.
- **Reuse basis:** the file's own header - *"An example evaluation prompt. A starting point, not
  scripture. Steal it, break it, improve it."* **The publication as a whole carries NO licence**,
  so this invitation is the only reuse grant and it covers this file alone. The 80 legal matters
  and their answer keys are NOT reproduced and must not be.
- **Do not edit in place.** A modified rubric goes in a new file so the disagreement between our
  variant and the original stays measurable.
- Review and evidence: `reports/2026-08-11-closevector-legal-benchmark-review.md`.

## Qwen3.8-27B-Q4_K_M.gguf

- **Role:** Qwen3.8 generation entrant, dense 27B (Gated DeltaNet hybrid:
  16 x (3 x linear_attention -> 1 x full_attention), `full_attention_interval
  = 4`, head_dim 256, GQA 24Q/4KV). Native vision-language model - **TEXT
  BENCH ONLY**, mmproj deliberately not fetched. Staged 2026-08-15 in
  response to the standing "bench on release" instruction.
- **Selection rationale (names versioned at execution, per 4.4):** four
  GGUF publishers were compared by reading each file's actual GGUF header,
  not their model cards. All three serious candidates convert to
  `general.architecture = qwen35`; they differ in quant recipe:
  - lmstudio-community (CHOSEN): 439 x Q4_K, 67 x Q6_K - the canonical
    `llama-quantize` Q4_K_M mix, matching the recipe behind the existing 28
    Q4_K_M entries in `results/model-survey.md`. Corridor-comparable.
  - unsloth: 456 x F32, 294 x Q4_K, 48 x Q5_K, 1 x Q8_0 - Unsloth Dynamic
    V3.0, self-labelled **preview**, plus a hand-edited chat template and 12
    re-uploads on release day. Two packaging confounds against the corridor
    (F39: a benchmark measures a CONFIG), so rejected for the baseline.
  - ggml-org: 288 x Q8_0, 193 x Q4_K, 17 x Q6_K, 17.67 GiB, and
    `block_count = 64` with the MTP head shipped as a separate file. A
    different quant point despite the same "Q4_K_M" label; rejected for the
    same comparability reason.
  Qwen's own `Qwen3.8-27B-FP8` was ruled out entirely: llama.cpp does not
  consume FP8 safetensors and vLLM is not viable on gfx1151 (F48). Same for
  the NVFP4 / MXFP4 / AWQ / MLX variants.
- **Source URL:** https://huggingface.co/lmstudio-community/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-Q4_K_M.gguf
- **Repo:** lmstudio-community/Qwen3.8-27B-GGUF
- **Revision (main @ pin, 2026-08-15):** 5a7da681f60570ab5b439a587e912d2e5eddb582
- **Size (HF API authority):** 16,810,714,336 bytes (~15.66 GiB)
- **SHA256 (upstream LFS oid):**
  e00082f779fa385cee8c68a3ec8833a75778cc87272240b942f74e0b8243e520
  - local verification on arrival (2026-08-15): size exact match
    (16,810,714,336 bytes, delta 0) AND local sha256 identical to upstream
    oid, computed twice by independent tools (script `sha256sum` and a
    separate Python `hashlib` pass). VERIFIED.
- **Quant:** Q4_K_M (canonical llama.cpp recipe; publisher states conversion
  with llama.cpp release b10430)
- **Licence:** Apache-2.0 (per API)
- **Header facts read directly from the file:** GGUF v3, 866 tensors,
  `qwen35.block_count = 65`, `nextn_predict_layers = 1` (the MTP head is
  INLINE in this file, unlike the ggml-org build - the README's "64 layers"
  plus the MTP head is what makes 65), `context_length = 262144`,
  `rope.freq_base = 1e7`, `tokenizer.ggml.pre = qwen35`.
- **Chat template:** embedded. Thinking is on by default for this model and
  is an eval-time concern, not llama-bench's.
- **Serving note:** `-c` must be passed explicitly and is DIVIDED BY `-np`
  (F20). The 262144 trained context will over-allocate KV if `-c 0` is used.

## Qwen3-8B-Q4_K_M.gguf (OFFICIAL Qwen repo, 2026-08-17 re-fetch for E52)

- **Role:** E52 - the SMALL-MODEL arm on the capability instruments. Every
  knowledge, legal and writing measurement in this repo has been taken on
  models of 24B and up; the 8B and 4B artefacts fetched in July were
  throughput-only (Step 8 Block 2b) and are no longer on disk. The recurring
  public question is whether a model that fits a laptop can do real document
  work, and nothing here answers it.
- **Source URL:** https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/main/Qwen3-8B-Q4_K_M.gguf
- **Repo:** Qwen/Qwen3-8B-GGUF - the **official Qwen publisher**, not a
  community requant.
- **Revision (main @ pin, 2026-08-17):** 7c41481f57cb95916b40956ab2f0b139b296d974
- **Size (HF API authority):** 5,027,783,488 bytes (~4.68 GiB)
- **SHA256 (upstream LFS oid):**
  d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785
  - verify on arrival: size exact match AND local sha256sum identical.
- **Quant:** Q4_K_M
- **Licence:** Apache-2.0 (per repo card, read from the HF API at pin time)
- **Chat template:** embedded; validate before eval use.

**This is a DIFFERENT artefact from the July entry above.** That one was
`unsloth/Qwen3-8B-GGUF` at 5,027,784,512 bytes; this is the official Qwen build
at 5,027,783,488 - **1,024 bytes smaller, and a different sha256.** Two
consequences, both stated so nobody has to rediscover them:

1. **Throughput measured on this artefact is NOT comparable to the July Step 8
   figures.** F29 says a benchmark result is a property of the whole
   measurement stack, and the quantiser is part of that stack. Any tg128
   comparison across these two files is a comparison of two things.
2. **The official repo was chosen deliberately over re-fetching the community
   build.** The capability instruments are the point rather than the throughput
   ladder, and provenance from the model's own publisher is worth more here
   than comparability to a July number - particularly for work that is meant to
   speak to whether "open weights" claims can be trusted at all.

**ARRIVAL VERIFICATION (2026-08-17).** Fetched and checked before first use, per
the download-integrity rule that completion is verified bytes and never an exit
code:

- size on disk **5,027,783,488 bytes** - exact match to the HF API authority.
- local `sha256sum` **d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785**
  - **identical to the upstream LFS oid pinned above. VERIFIED.**

## Kwaipilot_KAT-Coder-V2.5-Dev-Q4_K_M.gguf

- **Role:** E61 follow-on candidate - a 35B-A3B MoE built from Qwen3.6-35B-A3B
  with additional SFT/RL for agentic coding. Tests whether MoE workhorse speed
  can be kept while buying back dense-model quality through post-training.
  Publisher reports 69.4% SWE-bench Verified against 64.4% for the base.
- **Repo:** bartowski/Kwaipilot_KAT-Coder-V2.5-Dev-GGUF
- **Source URL:** https://huggingface.co/bartowski/Kwaipilot_KAT-Coder-V2.5-Dev-GGUF/resolve/main/Kwaipilot_KAT-Coder-V2.5-Dev-Q4_K_M.gguf
- **Size (HF API authority):** 21,391,448,480 bytes (19.92 GiB / 21.4 GB)
- **SHA256 (upstream LFS oid):** 4221c26e5663502d1c96fc901c9967d0e70ce2dcfaa5a9fb9280a46bd19e3c07
- **Xet hash (owner-supplied, not independently pinned):** 376b651341557cef659be5bfeb7ea0e0fe04fe71bddc185be74d329a636c07e3
- **File commit (owner-supplied):** 92f1c3541fae9cd3ccd0609fd94d74a36c1d12d7
- **Pinned:** 2026-08-19 from the HF API tree endpoint by this session. The size
  and oid **independently reproduce the owner-supplied values**, which is why
  both are recorded - agreement between two sources obtained separately is the
  provenance claim, not either one alone.
- **Downloaded:** queued 2026-08-19, `tools/fetch_hf_model.sh`, sequenced to
  finish BEFORE the near-edge gpt-oss-120b load (deadlock rule).
- **Quant:** Q4_K_M - chosen to match every other first-pass arm so quant does
  not become a second experimental variable.
- **Verify on arrival:** size exact match AND local sha256sum identical to the
  oid above.

## nvidia_Nemotron-3-Nano-30B-A3B-Q4_K_M.gguf

- **Role:** E61 follow-on candidate - a 30B-class MoE with ~3.5B active
  parameters and hybrid Mamba/attention layers. Backup general MoE, behind
  GLM-4.7-Flash in the funnel.
- **Repo:** bartowski/nvidia_Nemotron-3-Nano-30B-A3B-GGUF
- **Source URL:** https://huggingface.co/bartowski/nvidia_Nemotron-3-Nano-30B-A3B-GGUF/resolve/main/nvidia_Nemotron-3-Nano-30B-A3B-Q4_K_M.gguf
- **Size (HF API authority):** 24,655,899,872 bytes (22.96 GiB / 24.7 GB)
- **SHA256 (upstream LFS oid):** 378a2765fb2567f3cee90b2ced046eb01c4219d72d94d49f72e22ed5b1c124d2
- **Xet hash (owner-supplied, not independently pinned):** ea538b8d85ed9ac3a68ffd2949592152521d0eb0af51385221a9dd3df2cbabf7
- **File commit (owner-supplied):** dccc75cf3afbc8b97d147b9914a8df94886201ab
- **Pinned:** 2026-08-19 from the HF API tree endpoint by this session; size and
  oid independently reproduce the owner-supplied values.
- **Downloaded:** queued 2026-08-19, sequenced as above.
- **Quant:** Q4_K_M, same reason.
- **Verify on arrival:** size exact match AND local sha256sum identical.
- **Note:** this is Nemotron-3-**Nano**-30B-A3B. The backup store already holds
  Nemotron-3-**Super**-120B-A12B, a different model - do not conflate them.

## Qwen3.8-Flash-Next-UD-IQ4_XS-{00001,00002,00003}-of-00003.gguf

- **Role:** sparkbench reopened 2026-08-31 to test Qwen3.8-Flash-Next
  (`qwen4exp` architecture, ~180B total params, MoE). Downloaded and verified
  only - not yet loaded, run, or benchmarked. Requires production (sparkrouter)
  paused to have room to load at all; gated on owner permission.
- **Repo:** unsloth/Qwen3.8-Flash-Next-GGUF
- **Source URLs:** https://huggingface.co/unsloth/Qwen3.8-Flash-Next-GGUF/resolve/main/UD-IQ4_XS/Qwen3.8-Flash-Next-UD-IQ4_XS-{00001,00002,00003}-of-00003.gguf
- **Sizes (HF API authority):**
  - 00001-of-00003: 10,946,624 bytes
  - 00002-of-00003: 49,835,229,856 bytes
  - 00003-of-00003: 43,836,407,744 bytes
  - Total: 93,682,584,224 bytes (93.68 GB)
- **SHA256 (upstream LFS oid, matches local sha256sum on arrival):**
  - 00001-of-00003: 5ce89370720f8bf90890f439361282104c1aa1482d4013bb9a50923e758e71a4
  - 00002-of-00003: 577a38a2392b40ca2193cea502e1d92f60b8cd370675d308e0ec21885d9daaa7
  - 00003-of-00003: d4634e6d84f0ebb0940be15c90d3790bf6464e3dea3a1cddc567dc0e83ad8833
- **Pinned:** 2026-08-31 from the HF API (`?blobs=true`) by this session.
- **Downloaded:** 2026-08-31, `tools/fetch_hf_model.sh` (restored to its
  committed form - see `sparkbench-flash-next-recon-and-reopening-2026-08-31.md`
  on Alchemy for the near-miss where it was briefly overwritten).
- **Quant:** UD-IQ4_XS - the smallest unsloth quant with real headroom margin
  below the next size up (Q4_K_XL, 111.33 GB), chosen because every quant down
  to this one already requires production paused to fit in 121 GiB RAM.
- **Verify on arrival:** size exact match AND local sha256sum identical to the
  oids above - both confirmed for all three shards.
- **llama.cpp support:** requires a build at or after commit `daef7b687`
  (2026-08-31) - the `qwen4exp` architecture (PR #27742) is not in the
  project's other pinned worktrees (`067de9371`, `9e40df63b`). A new worktree,
  `llama.cpp/wt/daef7b6`, was built for this and is verified to carry it.

## Huihui-Qwen3.8-27B-abliterated-Q4_K.gguf

- **Role:** E93's treatment arm. An abliterated build of the model this repo
  already holds, so the pair differs by the abliteration and nothing else.
- **Repo:** huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF
- **Declared base:** `base_model:Qwen/Qwen3.8-27B` - our exact base
- **Source URL:** https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated-GGUF/resolve/main/Huihui-Qwen3.8-27B-abliterated-Q4_K.gguf
- **Size (HF API authority):** 16,810,714,400 bytes
- **SHA256 (upstream LFS oid):** 6c2c13cef89238c3604d756b07b3ef5fafebbd61095feb8553ff449c95e4c1c6
- **Pinned:** 2026-08-31 from the HF API (`?blobs=true`) before the fetch.
- **Downloaded and verified:** 2026-08-31, `tools/fetch_hf_model.sh`. Size and
  local sha256 both MATCH the pinned values.
- **Quant choice, and why it is not one of the other 25 in that repo:** our base
  `Qwen3.8-27B-Q4_K_M.gguf` is 16,810,714,336 bytes; this file is 64 bytes
  larger, which is the longer model-name string rather than any tensor
  difference. Abliteration alters weight VALUES and leaves shapes alone, so a
  near-identical size is the signature of the same architecture at the same
  quant recipe. Any other quant would have varied quantisation alongside the
  abliteration and confounded the only variable E93 isolates.
- **Scope note:** held for measurement only. E93 measures whether the model
  FLAGS a request, never the content it would produce otherwise.

## Qwen3.8-27B-GSQ-RCO-IQ3_S-mtp.gguf

- **Role:** the QUANT-LADDER arm. Same base model as our incumbent
  `Qwen3.8-27B-Q4_K_M.gguf`, at a much smaller quant, so the pair differs by
  the quantisation recipe and nothing else. Tests the community claim that
  GSQ-RCO holds Q4-class quality at ~11 GiB.
- **Repo:** ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF
- **Revision (main @ pin time 2026-09-04):** d562806dbafae37109975e970aae91b43e73b440
- **Source URL:** https://huggingface.co/ISTA-DASLab/Qwen3.8-27B-GSQ-RCO-GGUF/resolve/main/Qwen3.8-27B-GSQ-RCO-IQ3_S-mtp.gguf
- **Size (HF API authority):** 12,120,016,960 bytes
- **SHA256 (upstream LFS oid):** 58fd826723939933dc86f45b7fe04545cbc2de1c70f6fe2cdd3858c87a98c12f
- **Pinned:** 2026-09-04 from the HF API tree before the fetch.
- **Downloaded and verified:** 2026-09-04, `tools/fetch_hf_model.sh`. Size exact
  AND local sha256sum identical to the pinned oid. Both confirmed.
- **Licence:** apache-2.0 (repo cardData).
- **Quant choice, and why this one of the eight in that repo:** the repo ships
  IQ2_XS/IQ2_S/IQ3_XXS/IQ3_S, each with and without an MTP head. IQ3_S-mtp is
  the variant named in the community report being tested and the largest of the
  four recipes, so a null result cannot be blamed on having picked the most
  aggressive quant. `-mtp` is chosen because our incumbent comparison already
  has MTP characterised (F84/F85) and the head is separable at serve time.
- **Also in the repo, NOT fetched:** `imatrix-qwen3.8-27b.gguf` (13.6 MB) and
  per-file `tensor-allocation/*.rco-allocation.txt`. Fetch these before making
  any claim about WHY the recipe behaves as it does - they are the allocation
  evidence, and this entry does not assert a mechanism.

## ThinkingCap-Qwen3.6-27B-Q4_K_M-MTP.gguf

- **Role:** the CHALLENGER arm against our `smart` slot. A different base model
  (Qwen3.6 lineage, not 3.8) at the same quant recipe and near-identical file
  size, so it is a drop-in swap at the same memory footprint.
- **Repo:** protoLabsAI/ThinkingCap-Qwen3.6-27B-MTP-GGUF
- **Revision (main @ pin time 2026-09-04):** 8d19125abadeb758d8b89930d4b7412d6f4f0b0a
- **Source URL:** https://huggingface.co/protoLabsAI/ThinkingCap-Qwen3.6-27B-MTP-GGUF/resolve/main/ThinkingCap-Qwen3.6-27B-Q4_K_M-MTP.gguf
- **Size (HF API authority):** 16,810,713,408 bytes
- **SHA256 (upstream LFS oid):** 0ba445d2d0ca3ec32f429d83701b42f2ea828c934fc6378b836ffaf1b0760c75
- **Pinned:** 2026-09-04 from the HF API tree before the fetch.
- **Downloaded and VERIFIED:** 2026-09-04, `tools/fetch_hf_model.sh`. Size exact
  AND local sha256 identical to the pinned oid `0ba445d2...`. Both confirmed.
- **Probed from the GGUF header before first use (F124):** `general.architecture`
  = `qwen35` and `n_ctx_train` = 262,144 - **both identical to our incumbent**,
  which is why the file lands 928 bytes away at the same quant. That is shared
  ARCHITECTURE, not shared lineage: it declares
  `general.base_model.0 = Qwen/Qwen3.6-27B` against our Qwen3.8-27B, and carries
  `general.tags = [qwen3_6, token-efficient, efficient-thinking]`.
- ⚠️ **NO GRADED REASONING CONTROL.** Its chat template contains ZERO
  occurrences of `reasoning_effort`, `xhigh` or `medium`, against 6, 5 and 2 in
  our incumbent's; it carries only a binary `enable_thinking`. **Passing
  `--thinking low|medium|xhigh` to this model is silently inert** - the run
  would proceed at the model's default while the result file recorded the
  setting that was asked for. Any arm comparing it against Qwen3.8 is NOT
  effort-matched and cannot be made so.
- **Both this file and our incumbent ship embedded sampling defaults**
  (`general.sampling.temp` 1.0, `top_k` 20, `top_p` 0.95). Every eval in this
  repo, and production, runs at temperature 0 and overrides them.
- **Licence:** apache-2.0 (repo cardData).
- **Footprint note:** 16,810,713,408 bytes against our incumbent
  `Qwen3.8-27B-Q4_K_M.gguf` at 16,810,714,336 - a 928-byte difference, which is
  metadata string length, not tensors. This is what makes it a same-footprint
  swap rather than a size/quality trade dressed as a model comparison.
- **Provenance caution:** this is a THIRD-PARTY requant of
  `bottlecapai/ThinkingCap-Qwen3.6-27B`, not a first-party release. The
  publisher's own Q4_K_M (no MTP head) is 16,810,713,056 bytes. Any finding
  names the requantiser, because the MTP head is what differs and it is theirs.
- **Also in the repo, NOT fetched:** `mtp-head/mtp-ThinkingCap-Qwen3.6-27B-head-Q8_0.gguf`
  (3.16 GB standalone head) and `mmproj-...-f16.gguf` (vision projector, 928 MB).
  Fetch the standalone head only if the baked-in head needs separating out.

## Qwen3.8-27B-Q8_0.gguf

- **Role:** E105, the TOP of the quant ladder. Third point on the same base
  model alongside `Q4_K_M` (incumbent) and `GSQ-RCO-IQ3_S` (E104's 4/8). Asks
  whether Q4_K_M is below the knee of the quantisation curve - a question this
  box can ask and a 24 GiB-VRAM box cannot, because 27 GiB fits resident here.
- **Repo:** unsloth/Qwen3.8-27B-GGUF
- **Revision (main @ pin time 2026-09-05):** 4ca720788d1e01f1bff70c033e0d0028fd02e502
- **Source URL:** https://huggingface.co/unsloth/Qwen3.8-27B-GGUF/resolve/main/Qwen3.8-27B-Q8_0.gguf
- **Size (HF API authority):** 29,047,086,048 bytes
- **SHA256 (upstream LFS oid):** a680f44a06920e5d689774823782006aa3acc8db95750323373b24139b67e348
- **Pinned:** 2026-09-05 from the HF API tree BEFORE the fetch.
- **Downloaded and VERIFIED:** 2026-09-05, `tools/fetch_hf_model.sh`. Size exact
  AND local sha256 identical to the pinned oid. Both confirmed before first use;
  the E105 runner re-checks both and ABORTS rather than serving an unverified
  file, because a dead download process is not a completed download.
- **Licence:** apache-2.0 (repo cardData).
- **Quant choice:** plain `Q8_0`, not `UD-Q8_K_L` (28,045,695,904 B) or
  `UD-Q8_K_XL` (31,457,991,680 B). The unsloth dynamic variants mix precisions
  per tensor, which would confound "is 8-bit better than 4-bit" with "is
  unsloth's allocation better than uniform". Q8_0 is the uniform 8-bit point and
  is the one that makes the ladder a ladder.
- **NOT a test of INT8 W8A8.** The community report that prompted this runs
  `compressed-tensors` W8A8 on an A40 through vLLM with FLASHINFER. That is a
  different format, different hardware and a different kernel path; vLLM is not
  viable on gfx1151 (F48). No E105 result transfers to that claim.

## Qwen-Image-2.1 (official diffusers snapshot) - E136 arm D

- **Role:** E136, arm D (diffusers `QwenImage21Pipeline`, BF16). Released 2026-09-20.
- **Repo:** Qwen/Qwen-Image-2.1
- **Revision (main @ pin time 2026-09-21):** 790c92633540aa0cb11d9abf19eb46d861714758
- **Local path:** `/opt/models/staging/Qwen-Image-2.1/` - folder layout PRESERVED (diffusers
  needs it; each subfolder has its own `config.json`), fetched per folder with
  `DEST=... tools/fetch_hf_model.sh`.
- **Size (HF API authority):** 30.9 GiB total. Weights: text_encoder 4 shards
  (4,998,056,552 / 4,915,962,464 / 4,915,962,496 / 2,704,357,976 B), transformer 2 shards
  (9,968,332,504 / 4,261,951,904 B), vae 1,350,989,512 B.
- **SHA256:** all 8 LFS files (7 weight shards + processor/tokenizer.json) identical to the
  pinned upstream oids, checked 2026-09-21 before first use. Non-LFS configs (<12 MB each)
  are size-verified only; HF publishes no oid for them. `assets/qr.png` not fetched.
- **Licence:** "Qwen Research License Agreement" (repo `license: other`). Owner cleared
  2026-09-21 on Qwen's public statement that outputs are not part of the licensed Materials.

## Qwen-Image-2.1 single-file weights for stable-diffusion.cpp - E136 arm S and variant S-q8

- **Role:** E136 arm S (sd.cpp `c678dfe` Vulkan, BF16) and labelled variant S-q8 (Q8_0 DiT).
- **Repo 1:** Comfy-Org/Qwen-Image-2.1 @ ace0edeb3791a594ddfa36ed5f41a178a394e921, into
  `/opt/models/staging/Qwen-Image-2.1-comfy/` (flat):
  - `qwen_image_2.1_bf16.safetensors` 14,230,280,616 B, sha256 89f4158d066cc33906a199fca85634f766892dd78f49b6698dabf187ac86c4bc
  - `qwen3vl_8b_bf16.safetensors` 17,534,334,616 B, sha256 68bdc82bc1b66851162ae656225e7e2068166b603db19bd5d5a3b90eb12669a9
  - `qwen_image_2.1_vae_bf16.safetensors` 675,509,688 B, sha256 bb21f7473051e1ac368515dd3f2e15cd44d7a11748ee8823e1ddca3e4876b7c9
- **Repo 2:** leejet/Qwen-Image-2.1-GGUF @ cc11433936a06e9765f7c0c0b1f0436cfd2b9856:
  `/opt/models/staging/qwen_image_2.1-Q8_0.gguf` 7,687,155,744 B, sha256 f8b244b00937f0e444a40dbf7866460871b89b30142594973b6012d1b471dc0a
- **Verified:** sizes exact and local sha256 identical to the pinned oids for all four,
  2026-09-21, before first use.
- **Licence:** Comfy-Org repo `license: other` (repackaging of the Qwen weights, same terms as
  above); leejet GGUF declares none - it is a conversion of the same weights.

## Ternary Bonsai 2 27B (PrismML) + two DFlash2 drafters - E138

- **Role:** E138, testing a public "~73 tok/s in 10.1 GB on Strix Halo" claim. Needs the PrismML
  llama.cpp fork (`llama.cpp/wt/prism` @ `bdc23b56b4458b9f1655aec5287f3ab56ee8daaa`, Vulkan build);
  stock llama.cpp rejects both packings.
- **Repo 1:** prism-ml/Ternary-Bonsai-2-27B-gguf @ 6ed5e12bf84b7a63069882c91dd9e9218647d17b
  (released 2026-09-17, base Qwen/Qwen3.8-27B, ternary g128 + FP16 scales):
  - `Ternary-Bonsai-2-27B-PTQ1_0.gguf` 5,946,648,928 B, sha256 53107f530aa52eb00912263ab1ee29bd199261c87cd7b4ad4ca1318c1fe33ee3
  - `Ternary-Bonsai-2-27B-PQ2_0.gguf` 7,206,168,928 B, sha256 3907dc1658db1f78a9826bf8d5bcb8dc65db0d466388937af57f2294fae62ec1
- **Repo 2:** ProCreations/Ternary-Bonsai-2-27B-DFlash2 @ 4cfb6ad03268fed0f60ca96c1a659c0b1c77e50b
  (Bonsai-tuned DFlash2 head, pairs with repo 1 @ 6ed5e12):
  `Bonsai-2-27B-DFlash2-Q8_0.gguf` 2,056,415,104 B, sha256 9dd11c8adb910058faf9fb77b10d90c1c048a4f3c2887a890f592cbd882deb9a
- **Repo 3:** z-lab/Qwen3.8-27B-DFlash2-GGUF @ 2d9571f8ce46e151f61c6499c99dee6079e1d610 (generic
  Qwen3.8-27B drafter; also the incumbent's drafter arm):
  `Qwen3.8-27B-DFlash2-Q8_0.gguf` 2,056,414,816 B, sha256 c18e800daedc59ca68fd13b6a856d795746af6d399a9279ac6a277d1d422f87e
- **Verified:** sizes exact and local sha256 identical to the pinned oids for all four,
  2026-09-22, before first use. Logs: `results/e138/fetch-*.log`.
- **Licence:** Apache-2.0 on all three repos.

## halogen-qwen3.8-flash-next (Peonist) + halogen-flash-server image - E139

- **Role:** E139, testing halogen-flash-server's published "~1,424 tok/s prefill @ 32K" claim for
  Qwen3.8-Flash-Next. Arms H0/H0s run this checkpoint; arm G0 runs our unsloth UD-IQ4_XS (entry
  above) on the same engine with `mtp.hgn`.
- **Repo:** peonist-ai/halogen-qwen3.8-flash-next @ e053f488b120b99ed2525e6ac99f68c51b3b6179,
  into `/opt/models/staging/halogen-qwen3.8-flash-next/` (tokenizer in `tokenizer/`). Pinned
  2026-09-24 from the HF API tree:
  - `qwen38-flash-next-w4b.hgn` 124,068,083,904 B, sha256 9c116bbc01f77b7a15464c1a124eb3325b286089b8a2a6f2856c9b246a235bd6
  - `qwen38-flash-next-w4b.overlay.hgn` 2,572,466,560 B, sha256 1cdfc3a9f988955bfe9a71bb808d393030abbf9f99d34ffa1ef93815a49b39ab
  - `qwen38-flash-next-w4b.overlay-speed.hgn` 2,478,095,488 B, sha256 f49c8d14fa972c1db5115c714981e399585a6a98106a1a055d9e77026bb6de4c
  - `qwen38-flash-next-mtp.hgn` 1,523,566,720 B, sha256 0f50e9626df98168e7c6e0cc264e2a92b5184dd885a175a06628d979b5edceeb
  - `tokenizer/tokenizer.json` 12,809,320 B, sha256 0997f410c57a1f4e53b09e4be8f4a172d90edd9564368fb0847030937229b9f3
  - five other tokenizer files (non-LFS, size-verified only; HF publishes no oid)
  - NOT fetched: `qwen38-flash-next-vision.hgn` (vision is not tested), `halogen.jpg`
- **Image:** `ghcr.io/peonist-ai/halogen-flash-server:0.13.8` =
  sha256:6e626c979d536ab1edb07898e278be6686afd353758ea268817457f801d687dd (`:latest` the same
  digest on 2026-09-24). Engine is closed source under its own terms. Run by digest only.
- **Verified:** sizes exact and local sha256 identical to the pinned oids for all five LFS files
  (w4b, overlay, overlay-speed, mtp, tokenizer.json), 2026-09-24 02:50, before first use.
  Image pulled by digest (image id 1094701565c3, 3.57 GB). Log: `results/e139/fetch-2026-09-24.log`.
- **Licence:** weights Apache-2.0 (derivative of Qwen/Qwen3.8-Flash-Next, whose terms govern);
  engine closed source, Peonist LLC terms.

## jcbtc/Qwen3.8-Flash-CIRU-STRIX-Orca (CIRU/Crown packaging of OrcaRouter refusal-removed Qwen3.8-Flash-Next) - E144 candidate

- **Role:** candidate arm to test the "Orca vs native Halogen" panel (2026-09-24, owner-supplied
  screenshot): Orca decodes 56.2 vs 47.3 tok/s thinking-on, +2 HumanEval, 54/54 vs 48/54
  retrieval. NOT a like-for-like engine comparison: different weights (149 of 1,658 tensors
  changed, experts refit and requantised) AND a different runtime AND MTP. Not yet pre-registered;
  no first use until it is (E144).
- **Repo:** jcbtc/Qwen3.8-Flash-CIRU-STRIX-Orca @ 8a40c7e9d72f73eb20b802ed26a7ce92c1f351a5 (personal
  HF account, created 2026-09-09, licence qwen-community-1.0). Upstream weights
  orcarouter/Qwen3.8-Flash-Next-Uncensored @ 8336e613ea508b13c2159bd0f68965d97a606b95, refusal-removed
  by its own description; CIRU adds no safety layer. Pinned 2026-09-24 from the HF API (`?blobs=true`):
  - `Qwen3.8-Flash-CIRU-STRIX-Orca.gguf.part-00001-of-00002.part` 40,000,000,000 B, sha256 39f23a9eee100435b04c55cc72155921e8249037c2e6fe19e76801944ca29e7b
  - `...gguf.part-00002-of-00002.part` 39,397,818,912 B, sha256 ff436fc7ff1bf164a1d4c89d81acd922efba8dfc0e06dcbb159baf0806472eb1
  - `...Orca-MTP-Q8_0.gguf.part-00001-of-00001.part` 4,135,893,440 B, sha256 0af1741e45b930fb96a55f3ec8c701e59be5a807b8191a33bc2f643700a88f0e
  - `ple.payload.bin.part-00001-of-00002.part` 40,000,000,000 B, sha256 01b612307ef23e8542dd856eaa50318d472fbc3299fa26fdb4e885ccfc450152
  - `ple.payload.bin.part-00002-of-00002.part` 12,429,053,952 B, sha256 c2d6c2751f71a29df260c52de9e97ceb0161a622da982469658d2165ac48d70a
  - `ple/ple.scale.bf16` 2 B, sha256 c7c58bd6007672362da2106fdbfaf9f50629e4bdf8598169c598027394ef9791
  - `runtime/v4.4.1/qsa-window-hotfix/ciru-runtime-v4.4.1-qsa-hotfix-source.tar.gz` 42,407,064 B, sha256 8da92cecc53e577e4d2a29842a0b84ceb867e525bc8a4a938c036f1e4d107cea
  - non-LFS, size-verified only: `ple/ple.manifest.json` 115,213 B, `parts.json` 1,852 B, `assemble.py` 4,541 B, `run-server.sh` 10,079 B
  - Reconciliation: five weight parts = 135,962,766,304 B; + ple.manifest.json + ple.scale.bf16 =
    135,962,881,519 B = the README's stated core-package size, zero gap.
  - NOT fetched: prebuilt `ciru-runtime-v4.4.1-nixos-gfx1151.tar.gz` (build from reviewed source instead),
    vision projector (vision not tested).
- **Runtime:** the panel's "v4.4.1-qsa-hotfix" is the hotfix SOURCE above; only source exists for it. The
  README's setup installs a private ROCm 10 SDK. It must NOT touch apt or `/etc/apt/preferences.d/
  repo-radeon-pin-600` (F58, load-bearing).
- **Disk:** 127.9 GiB fetched plus ~124 GiB again if `assemble.py` restores the GGUFs beside the parts.

## E145 candidates - the models from a third-party 'approximate options for 128 GB' widget (pinned 2026-09-24, NOT yet fetched or used)

- **Role:** E145 arms, run through the E143 Aider harness. The widget's own scores ('intelligence', 'tasks/hr') have no stated method and are not evidence.
- **Lineage caveat:** the two `ornith-ai` repos declare no base model in their card metadata (GGUF architecture `qwen35moe`, licence MIT); their provenance beyond that is unverified.
- **ornith-1.0-35b-Q4_K_M.gguf** (widget option 3 (Ornith 1.0 35B Q4_K_M))
  - repo `ornith-ai/Ornith-1.0-35B-GGUF` @ 383064f72a1ef3087b779f268d3ca117eb989aac, licence mit
  - 21,166,757,760 B, sha256 ff25291b2599fb927a835e624d2b3540106af61761c3fa57ac4264046dbec002
- **Ornith-1.5-35B-Q4_K_M.gguf** (newer than the widget: Ornith 1.5, 35B-A3B)
  - repo `ornith-ai/Ornith-1.5-35B-A3B-GGUF` @ 12393612fd4f730ff5aadc23e9b8f9648aa49ceb, licence mit
  - 21,713,463,040 B, sha256 42739874cc2ccfdb8523b23fbe52e29b2a7555c8176737ca9ca0b5d59859d41f
- **Qwen3.6-27B-Q4_K_M.gguf** (GGUF stand-in for widget option 2 (Qwen3.6 27B OptiQ 4-bit is an MLX file this box cannot load))
  - repo `unsloth/Qwen3.6-27B-GGUF` @ 82d411acf4a06cfb8d9b073a5211bf410bfc29bf, licence apache-2.0
  - 16,817,244,384 B, sha256 5ed60d0af4650a854b1755bd392f9aef4872643dc25a254bc68043fa638392a0
- **Qwen3.6-35B-A3B-UD-Q4_K_M.gguf** (widget option 1 (Qwen3.6 35B A3B UD-Q4_K_M); E143 arm C ran the UD-Q4_K_XL quant of the same model)
  - repo `unsloth/Qwen3.6-35B-A3B-GGUF` @ a483e9e6cbd595906af30beda3187c2663a1118c, licence apache-2.0
  - 22,134,528,992 B, sha256 ac0e2c1189e055faa36eff361580e79c5bd6f8e76bffb4ce547f167d53e31a61
