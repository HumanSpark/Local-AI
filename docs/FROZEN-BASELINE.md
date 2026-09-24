# File: docs/FROZEN-BASELINE.md
# Purpose: The exact models, quantisations, provenance, build and runtime settings every sparkbench headline figure was measured on.
# Project: sparkbench | Date: 2026-08-20
#
# Overview: A benchmark measures a CONFIG, not a box (Rule 8, F39). This file
# is that config, frozen at close-out. A new model is compared against these
# incumbents on these settings, or the comparison is not one.
#
# EVERY FIGURE IN THIS REPOSITORY THROUGH COMMIT df4696f WAS MEASURED ON KERNEL
# 7.0.0-28-generic. amdgpu is in-kernel and unpinned, so the driver is a live
# bench variable. E76 (2026-08-20) is the first experiment on 7.0.0-29-generic
# and carries the bridge that tests whether capability figures transfer.
#
# HASHES ARE COPIED FROM manifests/MANIFEST.md, WHICH IS THE AUTHORITY. They are
# upstream LFS object ids, verified against local files on arrival. They are not
# re-hashed here: hashing 63 GB of weights is the documented deadlock trigger
# (docs/memory-edge-deadlock.md) and must never overlap a bench run.

## The hardware and the stack

| | |
|---|---|
| host | **sparkmax** - GMKtec EVO-X2, Ryzen AI Max+ 395, 128 GB unified RAM |
| GPU | Radeon 8060S, gfx1151, **Vulkan / RADV** |
| Mesa | 25.2.8 - did NOT drift across either kernel move (F57) |
| kernel at close-out | `7.0.0-29-generic`, `canonical-livepatch` reporting `nothing-to-apply` |
| kernel for E1-E75 | **`7.0.0-28-generic`** |
| ROCm packages | pinned by `/etc/apt/preferences.d/repo-radeon-pin-600`, **load-bearing** - see F58 and the MOTD rule in CLAUDE.md |

## The build

| | |
|---|---|
| worktree | `llama.cpp/wt/b10435` |
| commit | **`9e40df63b`** - *jinja: fix quadratic cost in gather_string_parts (#27034)* |
| binary | `llama.cpp/wt/b10435/build/bin/llama-server` |
| serving | HTTP via `llama-server` only, never `llama-cli` (Rule 1) |

## The models

All four are Apache-2.0 per their repo cards.

### Qwen3-30B-A3B-Instruct-2507-Q4_K_M - THE INCUMBENT

The production workhorse. It serves **100% of measured relay traffic** (952
requests, 2026-07-19 to 2026-08-14) and it is the best local arm on the
knowledge-work bank.

| | |
|---|---|
| file | `/opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf` |
| repo | `unsloth/Qwen3-30B-A3B-Instruct-2507-GGUF` @ `eea7b2be5805a5f151f8847ede8e5f9a9284bf77` |
| size | 18,556,686,752 bytes |
| sha256 | `6c997b8af17debdfb01d890214400ccbab00db6acc0ba8da5de1cc906c4774d0` |
| quant | Q4_K_M, MoE (~3B active) |
| bench config | `-c 32768 -np 1`, temperature 0, no tool schema (F94) |
| production config | `-c 98304`, `--jinja`, port 8400, owned by `/var/lib/sparkrouter/serving.conf` |

### Qwen3.8-27B-Q4_K_M - the accuracy arm

Most accurate local arm without a deadline; unusable **with** one.

| | |
|---|---|
| file | `/opt/models/staging/Qwen3.8-27B-Q4_K_M.gguf` |
| repo | `lmstudio-community/Qwen3.8-27B-GGUF` @ `5a7da681f60570ab5b439a587e912d2e5eddb582` |
| size | 16,810,714,336 bytes |
| sha256 | `e00082f779fa385cee8c68a3ec8833a75778cc87272240b942f74e0b8243e520` |
| quant | Q4_K_M, dense, Gated DeltaNet hybrid (`general.architecture = qwen35`) |
| bench config | `-c 32768 -np 1`, `--spec-type draft-mtp --spec-draft-n-max 4` (F84's graduated operating point) |
| ⚠ **reasoning_effort MUST be declared** | its chat template resolves to `xhigh` when nothing is said. F71 measured that burning 100,000 tokens over 2h46m and returning nothing. Use `medium` |

### gpt-oss-120b-mxfp4 - the supervised-only arm

| | |
|---|---|
| files | `/opt/models/staging/gpt-oss-120b-mxfp4-0000{1,2,3}-of-00003.gguf` |
| repo | `ggml-org/gpt-oss-120b-GGUF` @ `d932fcea62f83e088d8f076a2cd2d7eb02dfa682` |
| sizes | 12,980,384 / 31,738,487,200 / 31,635,878,880 bytes (~63.4 GB) |
| sha256 | shard 1 `e2865eb6c1df7b2ffbebf305cd5d9074d5ccc0fe3b862f98d343a46dad1606f9`<br>shard 2 `346492f65891fb27cac5c74a8c07626cbfeb4211cd391ec4de37dbbe3109a93b`<br>shard 3 `66dca81040933f5a49177e82c479c51319cefb83bd22dad9f06dad45e25f1463` |
| quant | native MXFP4 MoE, non-expert tensors Q8_0 |
| ⚠ **>60 GiB regime** | 63.06 GiB GTT peak measured. Attended runs only. Read `docs/memory-edge-deadlock.md` first |
| ⚠ **decode hang undiagnosed** | 95% two-sided Wilson upper bound on the per-load fault rate is **2.98%**, from 125 clean cycles - **on 7.0.0-28 only**. The bound does not cross the kernel boundary |

### Qwen3-Coder-30B-A3B-Instruct-Q4_K_M - the named coding route

| | |
|---|---|
| file | `/opt/models/staging/Qwen3-Coder-30B-A3B-Instruct-Q4_K_M.gguf` |
| repo | `unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF` @ `b17cb02dd882d5b6ab62fc777ad2995f19668350` |
| size | 18,556,689,568 bytes |
| sha256 | `fadc3e5f8d42bf7e894a785b05082e47daee4df26680389817e2093056f088ad` |
| quant | Q4_K_M, MoE |
| ⚠ | scored **0 of 5** on real-repository coding tasks (E73). It remains the named route for bounded edits and is not a candidate for unsupervised work |

## The frozen instruments

| instrument | version | what it measures | frozen at |
|---|---|---|---|
| `spikes/kw-eval/kw_items.py` | E74 bank, 26 items | real multi-document knowledge work, 8 shapes | 2026-08-19 |
| `spikes/kw-eval/kw_corpus.py` | packs `s`=4 docs / `m`=6 / `l`=15 | the corpus the bank is keyed to | 2026-08-19 |
| `spikes/kw-eval/abstain_items.py` | **`e76-v1-2026-08-20`**, 21 items | abstention: 12 unanswerable, 9 reused controls | 2026-08-20 |
| `tools/score_kw_eval.py` | **`v2-2026-08-20`** | the mechanical matcher, shared by both banks | 2026-08-20 |
| `tools/score_abstain.py` | **`e76-agg-v1-2026-08-20`** | abstention aggregation over the same matcher | 2026-08-20 |
| `tools/typography.py` | **`typo-v1-2026-08-20`** | the F95 Unicode fold, imported by all three scorers | 2026-08-20 |
| `spikes/eval-pilot/score_keyed.py` | **`keyed-v2-2026-08-20`** | keyed table scoring | 2026-08-20 |
| `spikes/closed-record/check_keys.py` | **`keys-v2-2026-08-20`** | sealed-key normalisation and gate | 2026-08-20 |
| `tools/ch1_tasks.py` + `ch1_sandbox_guard.py` | 5 usable tasks, 39 guard tests | real-commit coding, held-out tests | 2026-08-19 |
| `spikes/ps-eval/` L1-L4 | - | sealed-key knowledge work, no LLM judge. **L1/L2/L3-hard are SATURATED** (F91) | 2026-08-17 |
| `tools/soak_load.py` | - | load/decode stability soak | 2026-08-19 |

**The three scorer fixes are prospective and were proven not to move any banked
result:** 8 E74 arm summaries re-score with 0 fields moved, 5 banked E10 element
sets unchanged, 30 banked closed-record runs unchanged in hits. Every scorer now
stamps its own version and the typography version into its output, so a re-score
can never be silently substituted for an original.

## The headline figures and the files that carry them

| figure | value | evidence |
|---|---|---|
| knowledge work completed locally within 40s | **20/24 = 83.3%** (95% CI 64.1-93.3%) | `results/raw/kw-workhorse-{s,m}.json` |
| best local, no deadline | 21/24 | `results/raw/kw-qwen38-{s,m}.json` |
| frontier comparator within 40s | 23/24 = 95.8% (79.8-99.3%) | `results/raw/kw-frontier-subagent-{s,m}.json` |
| unattended coding handed over | **0/20 = 0%** (0.0-16.1%) | `results/raw/ch1-*.json` |
| multi-model review beats best single model | **no** - every arm tied or lost, at 3.7-4.5x wall time | `results/raw/e75-*.json` |
| load/decode stability | 125 cycles, 0 failures, 2.98% Wilson upper bound **on 7.0.0-28** | `results/raw/e72-soak-gptoss120b-cold100.json` |
| unsupported assertions on unanswerable questions | see E76 in `results/experiments.md` | `results/raw/e76-*.json` |

**Per-arm totals are the SUM of the two packs.** `score_kw_eval.py` reports each
pack separately (11 items in `s`, 13 in `m`); the 24-item headline adds them.
Quoting a single pack's row as the headline understates it.

## The shared-hardware rules that outlive the programme

1. **One GPU consumer at a time** (Rule 9). A contended number is VOID, not
   noisy. `tools/relay_bench_window.sh` opens the maintenance window and
   **needs root** - `agent-spark` cannot run it.
2. **Never `pkill -x llama-server` while the gateway is up** - the relay's own
   process dies with it. Kill by PID.
3. **Serving flags have ONE writer**: `/var/lib/sparkrouter/serving.conf`. Never
   inline them into a unit's `ExecStart` (F39).
4. **Nothing above ~60 GiB unattended.** Read `docs/memory-edge-deadlock.md`.
5. **Heavy disk hashing must not overlap a near-edge load** - it is the classic
   deadlock trigger.
