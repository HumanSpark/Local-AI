# File: e138-prereg.md
# Purpose: Pre-registration for E138 - testing a public claim of ~73 tok/s from Ternary Bonsai 2 27B on Strix Halo.
# Project: sparkbench | Date: 2026-09-22
#
# Overview: The claim, what the public record already says about it, the arms (Bonsai 2 on the
# PrismML fork against the Qwen3.8-27B Q4_K_M incumbent, each with and without a DFlash2
# drafter), the four blocks (speed+memory, quality, agentic coding, pi harness), predictions
# that each name the field they are scored against, and the stop rules. Written before any run.

# E138 PRE-REGISTRATION - does Ternary Bonsai 2 27B do ~73 tok/s in 10.1 GB on this box? (2026-09-22)

## The claim (public post, owner-supplied 2026-09-22)

> "I just hit ~73 tokens/sec with Bonsai 2 27B on my Strix Halo. We're talking 98% FP16
> precision in only 10.1GB of RAM total. I've been using it all day for agentic coding and it
> rips. The trick is aggressive kernel optimization + dflash2 speculative decoding + pi harness
> adaptation. There is something magical about an unlimited Opus-class model running
> comfortably on your own desk."

Split into testable parts:

| # | part | testable here? |
|---|---|---|
| C1 | ~73 tok/s decode on Strix Halo | yes - same SoC (Ryzen AI Max+ 395, Radeon 8060S) |
| C2 | 10.1 GB RAM total | yes |
| C3 | "98% FP16 precision" | partly. The 98.2% is PrismML's own benchmark aggregate (83.9 vs 85.4, H100), not a precision figure. We test retention against OUR Q4_K_M incumbent, not FP16 |
| C4 | good for agentic coding all day | anecdote-grade only. The coding instrument is PARKED (F151) |
| C5 | the trick is kernels + DFlash2 + pi | the DFlash2 share is ablatable; "aggressive kernel optimization" is unspecified and cannot be reproduced |
| C6 | "Opus-class" | NO. The banks are saturated at the frontier (F153). Not scored |

## Public record at registration (so a miss can be told from a surprise)

- Model: `prism-ml/Ternary-Bonsai-2-27B-gguf` @ `6ed5e12`, released 2026-09-17, ternary Qwen3.8-27B,
  g128 FP16 scales. Files: PQ2_0 7,206,168,928 B; PTQ1_0 5,946,648,928 B. **Stock llama.cpp cannot
  load either**; the PrismML fork is required. Card lists CUDA, Metal, CPU. RTX 5090 PQ2_0 decode
  129.9 tok/s.
- Fork `PrismML-Eng/llama.cpp` branch `prism` @ `bdc23b56b` (2026-09-22). README: PQ2_0 is preferred
  on Metal/CUDA/HIP/CPU; **Vulkan has integer-dot mat-vec for PTQ1_0 only** (#238). Issue #224:
  Vulkan SEGFAULT loading ternary Bonsai 2 on Strix Halo at `9a9394a`, no fix linked. HEAD carries
  `a419d438a` "vulkan: decline GATED_DELTA_NET raw gates instead of computing them wrong".
- Best PUBLIC Strix Halo figures found: 32.758 tok/s weighted (Bonsai **v1** 27B, ROCm fork +
  DSpark drafter, `jcbtc/Ternary-Bonsai-27B-AMD-Strix-Halo`); 26.63 tok/s (Qwen3.8-27B UD-Q5_K_XL +
  DFlash2 n=4, Vulkan, `UntR/qwen27b-dflash2-on-strix-halo`). **Nothing public near 73.**
- Physics (F3): t/s ~= 220 GB/s / bytes read per token. PTQ1_0 5.95 GB -> **~37 tok/s AR ceiling**;
  PQ2_0 7.21 GB -> ~30. 73 tok/s therefore REQUIRES ~2x from speculation at near-ceiling kernels.
- 10.1 GB matches PQ2_0 (7.21) + a Q8_0 DFlash2 drafter (2.06) + KV, i.e. the claimed config is
  most likely PQ2_0 + Q8_0 drafter.

## Arms

| arm | model | drafter | build |
|---|---|---|---|
| **B0** | Bonsai 2 PTQ1_0 | none | prism `bdc23b56b`, Vulkan |
| **B1** | Bonsai 2 PTQ1_0 | `ProCreations/Ternary-Bonsai-2-27B-DFlash2` Q8_0 (Bonsai-tuned) | same |
| **B2** | Bonsai 2 PTQ1_0 | `z-lab/Qwen3.8-27B-DFlash2-GGUF` Q8_0 (generic) | same |
| B0p / B1p | Bonsai 2 PQ2_0 | none / ProCreations | same - the claimed file; Vulkan is not its preferred backend |
| **Q0** | Qwen3.8-27B Q4_K_M (incumbent) | none | production `daef7b6`, Vulkan |
| **Q1** | Qwen3.8-27B Q4_K_M | z-lab Q8_0 | same |

Speculative config for every drafter arm: `--spec-type draft-dflash --spec-draft-n-max 4 -ngld 999`
(the n=4 optimum in the UntR Strix Halo sweep). `-np 1`, `-c` explicit, `-fa on`.

**HIP fallback (owner-approved, bounded):** only if B0 cannot load or fails the offload gate on
Vulkan. One HIP build of the same fork commit, arms re-run on it, labelled. ROCm work is otherwise
still parked.

## Blocks, in run order

1. **Speed + memory** (the headline). `llama-bench -d 0,4096,8192 -o md` for B0, B0p, Q0 (tg128,
   pp512). Then llama-server decode, temperature 0, 512 generated tokens, two prompts: **CODE** = an
   edit request with a 3 KB Python file in context (agentic-shaped), **CHAT** = an open prose
   answer. Record `predicted_per_second`, draft acceptance, and peak memory as
   MemTotal-MemAvailable delta plus amdgpu `mem_info_gtt_used` + `mem_info_vram_used`.
2. **Quality** - the F144 protocol: `run_ps_eval.py --tier l5` (24), `run_coding_eval.py --task-set
   core` (15), `--task-set expert` (8, E104 config: `-c 32768 --max-tokens 24576 --thinking medium`).
   Incumbent figures are the banked F144 run (23/24, 15/15, 7/8). **Declared confound:** the banked
   incumbent ran on mainline builds, Bonsai runs on the fork. The incumbent is not re-run (~2 h on
   expert alone); if Bonsai lands within 1 of it everywhere, that is reported as indistinguishable
   on saturated banks, NOT as 98% retention.
3. **Agentic coding** - `tools/aider_task_runner.py` on `tools/aider-tasks.json` (the three E113
   repaired tasks), best Bonsai config serving. Verify-command pass count only; aider's exit code is
   not evidence.
4. **pi harness** - the pi coding agent (pi.dev) installed user-level, pointed at the same server,
   the same three tasks, the same verify commands. No "adaptation" recipe is published, so this runs
   pi with its documented llama.cpp settings; anything beyond that is labelled.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `B0.loads_vulkan` | YES, full offload (~60%) | #224 predates HEAD; `a419d438a` touches exactly the GDN path |
| P2 | `B0.llama_bench_tg128_d0` | 22-36 tok/s | 37 ceiling, low-bit kernels land below Q4_K's 84-100% |
| P3 | `B1.server_tps_CODE` | 35-60 tok/s - **NOT >= 70** | ~1.6-2x on the AR figure; nothing public near 73 |
| P4 | `B1.server_tps_CHAT` | below `B1.server_tps_CODE` by >= 20% | F85: MTP 2.08x structured vs 1.32x chat |
| P5 | `B1.server_tps_CODE / B2.server_tps_CODE` | > 1.0 | Bonsai-tuned drafter should accept more than the generic one |
| P6 | `B1.peak_mem_gib` (GTT+VRAM used, `-c 16384`) | 8.0-11.0 | 5.95 + 2.06 + KV + compute buffers |
| P7 | `B0.l5_correct` | 21-23 / 24 | F30: ternary floor keeps document tasks |
| P8 | `B0.expert_correct` | <= 5 / 8 (incumbent 7/8) | F144: IQ3_S already lost 3 on this bank; ternary is further down |
| P9 | `aider.pass_count` on Bonsai | <= incumbent's E113 2/3 | P8's reasoning |
| P10 | `pi.pass_count` vs `aider.pass_count` | equal | the harness does not change model capability on three tasks |

**C1 is scored as REPRODUCED only if any arm reaches >= 65 tok/s on `server_tps_CODE`.**

## Stop rules

- B0 segfaults on Vulkan -> record it (P1 falsified, #224 confirmed at HEAD), go to HIP fallback.
- HIP also fails -> C1 scored NOT REPRODUCIBLE on this box today; blocks 2-4 do not run.
- The offload gate finds any layer on CPU -> that arm's speed is void, not slow.
- Memory guard: kill if MemAvailable < 12 GiB (as E136).
- Any run concurrent with the gateway or another GPU job is void (Rule 9); the gateway is down for
  the whole window via `relay_bench_window.sh down`.

## AMENDMENT 1 - after the pre-window load checks (declared 2026-09-22, before any clean run)

Every figure below was measured WITH THE GATEWAY UP (its three models resident, idle). Timings
are void under Rule 9 and are stated only so the clean run cannot be read as a surprise that
was in fact already seen. Files: `results/e138/void-contended/`.

1. **P1 HELD.** PTQ1_0 loads and fully offloads on Vulkan at fork HEAD (130/130 layer
   assignments on Vulkan0, graph splits = 2, correct output). #224 does not reproduce at
   `bdc23b56b`.
2. **PTQ1_0 is the SLOW file on RADV, not the fast one.** Plain decode, contended: PTQ1_0
   **3.45 tok/s**, PQ2_0 **22.44 tok/s** - 6.5x. The README's "integer-dot mat-vec for PTQ1_0"
   (#238) is enabled for Intel Xe2 only. **PQ2_0 becomes the primary Bonsai file** (it is also
   the file 10.1 GB points to). PTQ1_0 stays as labelled arm B0 for the finding.
3. **The fork cannot load a DFlash2 drafter.** Both drafters fail with `wrong number of
   tensors; expected 81, got 58`: the fork's `draft-dflash` predates mainline's DFlash2 layout.
   Mainline `daef7b6` loads the same z-lab file and speculates. **Declared port:** mainline
   `b10f9ca58` (#27342, DFlash2) cherry-picked onto the fork in local branch `e138-dflash2`
   (`ffdb99564` + `bc77f590c`, a one-brace conflict fix). Seven files conflicted; every hunk
   was the fork's DFly/DSpark additions beside mainline's DFlash2 additions, kept both. A
   mis-merge can only cost acceptance or crash, never change an answer: the target verifies
   every drafted token. **All Bonsai arms run on this local build**, which is not a published
   binary.
4. Contended smoke on the port, 1 rep, 512 tokens: B1p (PQ2_0 + ProCreations) CODE **29.4**,
   CHAT **21.44** tok/s, acceptance 365/580 and 311/793, GPU +12.07 GiB. Q1 (mainline, Q4_K_M +
   z-lab) CODE 18.91, CHAT 16.08, 256 tokens.

### Arms, final

| arm | model | drafter | build |
|---|---|---|---|
| **B0p** | PQ2_0 | none | prism port `bc77f590c` |
| **B1p** | PQ2_0 | ProCreations Q8_0 | same |
| **B2p** | PQ2_0 | z-lab Q8_0 | same |
| B1p-n8 | PQ2_0 | ProCreations, `--spec-draft-n-max 8` | same - "aggressive", labelled extra |
| B0 | PTQ1_0 | none | same - the slow-path finding |
| **Q0** / **Q1** | Q4_K_M | none / z-lab | mainline `daef7b6` |

### Scoring changes, nothing else

- P2 is scored on **B0p** (`llama_bench_tg128_d0`). B0's PTQ1_0 figure is recorded, not scored.
- P3-P6 are scored on the **p** arms (B1p, B2p) in place of B1/B2. Ranges are UNCHANGED, even
  where the contended smoke already leans against them (P6 8.0-11.0 GiB vs 12.07 contended).
- Quality blocks run on **B0p** with no drafter: at temperature 0 the target decides every
  token, so quality is the target's property (F84).
- Agentic blocks serve the **B1p** config (the claimed one) at `-c 32768`; Aider AND pi both go
  through `tools/aider_probe.py` :8499 -> :8130, so their latency is measured the same way.
  pi 0.87.0 (`@earendil-works/pi-coding-agent`), `--no-context-files`, via the runner's new
  `--agent pi`.

## AMENDMENT 2 - the window is split (declared 2026-09-23, before any clean run)

Owner's call: run **block 1 only** (speed + memory) in the first window, ~45 min rather than
~3.5 h, so the gateway is down for less time. Blocks 2-4 (quality, agentic, pi) keep their
pre-registered configs and wait for a later window. Nothing else changes: the arms, the
predictions and the >= 65 tok/s bar for C1 are as registered. P7-P10 are simply unscored until
that second window runs.
