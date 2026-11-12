<!--
# File: e158-results.md
# Purpose: Results of E158 - do newer local coding models beat Flash-Next's 9/10 on the frozen E156 bank?
# Project: sparkbench | Date: 2026-11-07
#
# Overview: Scored against results/e158-prereg.md (P1-P5, written 2026-11-06 before any arm ran; no amendments). Raw
# records: results/e158/raw/<arm>/<task>.json (OR35 37bc8e6, OR122 086620e, TS45 ac5e54a, RA f9efc66); per-task
# runner lines results/e158/raw/window.log; transcripts gitignored under results/e158/transcripts/<arm>. Comparators
# are the E156 arms as scored (results/e156-results.md), not re-run. Finding F185.
-->

# E158 RESULTS - Ornith 1.5 35B ties Flash-Next at 9/10; nothing beats it (2026-11-07)

## In plain English

We gave four newer local coding models the same 10 real fixes as last time's test, under the same rules. None beat
the best result so far, Flash-Next's 9 of 10. Ornith 1.5 35B matched it with 9. Tess 4.5 and KRAFTON's Raon-1 mini
solved 8 each, level with Claude Sonnet 5.5 and Opus 5.5. The surprise is Raon: it is a small preview model and we
expected 6 or fewer, but it solved 8 and was the fastest of the four.

Two results go the other way. Ornith's big 122B version solved only 6, fewer than its 35B sibling, and was the slowest.
And a fifth model, Tess 4, never ran: the current llama.cpp refuses to load its file.

Ten tasks is a small test. A one-task gap is not a ranking, so the fair summary is: two local setups at 9 (Flash-Next
and Ornith 35B), three local setups and both Claude models at 8 (Tess 4.5, Raon-1 mini, Qwen3.8-27B). One task,
d6d81ce51, has now beaten every local model we have tried. Only Sonnet has solved it.

## Results

| Arm | Setup | Solved | Median per task | Total time | GTT at ready (weights) |
|---|---|---|---|---|---|
| OR35 | Ornith-1.5-35B-A3B Q8_0, llama.cpp e14a7797 | **9/10** | 30.4 min | 4.98 h | 36,483 MiB (36,050) |
| TS45 | Tess-4.5-27B Q8_0 + MTP draft, llama.cpp e14a7797 | 8/10 | 43.4 min | 6.83 h | 40,463 MiB (27,271 + draft) |
| RA | Raon-1-mini-preview Q8_0, KRAFTON fork fb895662d | 8/10 | 20.0 min | 3.53 h | 29,079 MiB (29,271) |
| OR122 | Ornith-1.5-122B Q5_K_M, llama.cpp e14a7797 | 6/10 | 53.9 min (9 records) | 7.17 h (9 records) | 85,110 MiB (84,600) |
| TS4 | Tess-4-35B-A3B Q8_0-MTP-Q4D-Q4H-PV64K | did not load | - | - | - |

E156 comparators, same bank, not re-run: H Flash-Next on Halogen 9/10 (21.3 min), T27 Qwen3.8-27B on Talus 8/10
(23.6 min), S Sonnet 5.5 8/10 (2.5 min), O Opus 5.5 8/10 (5.3 min), Q Qwen3-Coder-30B 2/10 (2.5 min).

- **Offload:** every arm that ran had GTT in use at or above its weight file size, so all four were on the GPU. Speed
  figures stand. RA's GTT is 192 MiB (0.7%) below its file size. That gap was not investigated; at
  99% of the weights it is not a CPU fallback.
- **TS4:** upstream llama.cpp e14a7797 rejects the file: `wrong number of tensors; expected 756, got 754`. The file is
  built for the card's own fork. The runner logged `FAIL TS4: not ready after 900 s` and moved on. This is a result
  about the file and engine pairing, not about Tess 4.
- **OR122 clearmail-ea3f86782:** the task ran to the runner's outer 4,200 s kill (rc=124) and wrote no record. It is
  scored as a fail. Its time is not in the median or total, so both understate OR122's time.

### Per task (P = pass, . = fail, X = killed with no record)

| Task | OR35 | OR122 | TS45 | RA | H | T27 | S | O |
|---|---|---|---|---|---|---|---|---|
| clearmail-a5fc6d93b | P | P | P | P | P | P | P | P |
| clearmail-f7d71f21c | P | P | P | P | P | P | P | P |
| clearmail-ea3f86782 | P | X | P | P | P | P | P | P |
| sparkforge-baab4031f | P | P | P | P | P | P | P | P |
| sparkforge-99cb03e95 | P | . | P | . | P | P | . | . |
| sparkforge-49785eb67 | P | P | P | P | P | P | P | P |
| sparkforge-ccf81588b | P | . | . | P | P | . | . | P |
| workstation-dotfiles-d6d81ce51 | . | . | . | . | . | . | P | . |
| workstation-dotfiles-ad8324027 | P | P | P | P | P | P | P | P |
| workstation-dotfiles-08dad841c | P | P | P | P | P | P | P | P |

- **d6d81ce51:** failed by all seven local arms that ran across E156 and E158 (H, T27, Q, OR35, OR122, TS45, RA) and by
  Opus. Only Sonnet solved it.
- **OR35 and H** fail the same single task.
- **TS45 and T27** fail the same two tasks (ccf81588b, d6d81ce51). Tess-4.5 is a fine-tune of Qwen3.8-27B.
- **99cb03e95** has the weak test noted in E156 (it checks source text near gate calls). RA and OR122 fail it as both
  cloud models do. Without it: OR35 8, TS45 7, RA 8, OR122 6.

## Predictions

| # | Prediction | Field | Measured | Verdict |
|---|---|---|---|---|
| P1 | the best E158 arm solves at least 8 | max tasks solved over E158 arms | 9 (OR35) | HELD |
| P2 | no E158 arm solves more than H's 9 | tasks solved, each arm | max 9 | HELD |
| P3 | OR122 solves at least as many as OR35 | tasks solved | 6 vs 9 | FALSIFIED |
| P4 | TS45 solves at least T27's 8 | tasks solved | 8 | HELD |
| P5 | RA solves at most 6 | tasks solved | 8 | FALSIFIED |

P6, reported only: median wall minutes per task, in the results table above.

## How far to trust it

1. **One attempt per task at non-zero temperature, 10 tasks.** A one or two task gap is not a ranking. P3 and P5 are
   falsified by three and two tasks, which is a signal worth stating but not proof of an order.
2. **A result is a model plus its engine and settings.** Four arms share llama.cpp e14a7797; RA uses KRAFTON's fork;
   the E156 comparators H and T27 use Halogen and Talus. OR122's 6/10 may be the model, the Q5_K_M quantisation, or
   both. It was not separated.
3. **Speed is not compared across engines.** OR35 at 30.4 min against H at 21.3 min is two different engines.
4. **TS45 speculative decoding** (`--spec-type draft-mtp`) changes speed only. Its 43.4 min median is with it on.
5. **Same bank, same final prompts as E156**, so every limit in `results/e156-results.md` applies: our own code from
   three Tier B repos, prompts close to a specification, the weak test on 99cb03e95.
6. **Raon-1 mini is a preview** on a vendor fork. A later release or an upstream port may score differently.

## What it changes

- **Local coding default.** Two setups now share the top score: Flash-Next on Halogen (9/10, 21.3 min) and Ornith 1.5
  35B on llama.cpp (9/10, 30.4 min). The choice to replace Qwen3-Coder in the routing guide is the owner's.
- **Bigger is not better here.** Ornith 122B scored below Ornith 35B and took the longest. It is not a candidate.
- **Raon-1 mini** is a credible fast option at 8/10 and 20.0 min, with the preview and fork caveats.
- **Capability index.** The monthly index keeps H, T27 and Q (`results/capability-index/setups.json`). Adding OR35 is a
  later decision, not made here.
