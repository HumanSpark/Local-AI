<!--
# File: e156-results.md
# Purpose: Results of E156 - on harder real repo work, how close do the best local setups get to Sonnet 5.5 and Opus 5.5?
# Project: sparkbench | Date: 2026-11-06
#
# Overview: Scored against results/e156-prereg.md (P1-P7 and the headline defined before any arm ran). Raw records:
# results/e156/raw/<arm>/<task>.json (cloud 7d8f64b, local 9e90488); full transcripts gitignored under
# results/e156/transcripts/<arm> with sha256 in each record. Findings F183, F184.
-->

# E156 RESULTS - harder bank: two local setups reach Sonnet and Opus (2026-11-06)

## In plain English

We gave five setups the same 10 real fixes from our own projects. These are bigger changes than last time, several
files and hundreds of lines each, and each fix was checked by the real project's own tests in a sealed container.
Flash-Next, running on this machine, got 9 right. Qwen3.8-27B, also local, got 8. Sonnet 5.5 and Opus 5.5 in the cloud
also got 8 each. Qwen3-Coder, the model we had been recommending for local coding, got only 2.

The local models are slow. Flash-Next took a median of 21 minutes per task against Sonnet's 2.5 minutes, roughly 8.6
times longer. They also cost nothing per task, where the cloud runs cost $2.82 (Sonnet) and $7.75 (Opus) for the 10
tasks. For unattended work you can batch, as in the owner's "slow but very smart" goal, the best local setup is now as
good as the cloud on our own code.

Two cautions. Ten tasks is a small test, so 9 against 8 does not show Flash-Next is better than Claude, only that it is
in the same place. And the one task both local leaders solved but both cloud models failed has weak tests: they check
the wording of the code around one call, not only what it does.

## Results

| Arm | Setup | Solved | Median per task | Total time | Cost |
|---|---|---|---|---|---|
| H | Qwen3.8-Flash-Next on Halogen 0.18.23 | **9/10** | 21.3 min | 3.50 h | $0 |
| T27 | Qwen3.8-27B on Talus v0.1.3 | **8/10** | 23.6 min | 4.52 h | $0 |
| S | Claude Sonnet 5.5 (OpenRouter, Anthropic only) | 8/10 | 2.5 min | 0.61 h | $2.82 |
| O | Claude Opus 5.5 (as S) | 8/10 | 5.3 min | 0.94 h | $7.75 |
| Q | Qwen3-Coder-30B-A3B on llama.cpp 5851a8e | 2/10 | 2.5 min | 0.96 h | $0 |

Costs are the scored task files only. Runs superseded by amendments 1-4 cost a further $1.32 (S) and $2.06 (O).

### Per task (P = pass)

| Task | S | O | H | T27 | Q |
|---|---|---|---|---|---|
| clearmail-a5fc6d93b | P | P | P | P | . |
| clearmail-f7d71f21c | P | P | P | P | P |
| clearmail-ea3f86782 | P | P | P | P | . |
| sparkforge-baab4031f | P | P | P | P | P |
| sparkforge-99cb03e95 | . | . | P | P | . |
| sparkforge-49785eb67 | P | P | P | P | . |
| sparkforge-ccf81588b | . | P | P | . | . |
| workstation-dotfiles-d6d81ce51 | P | . | . | . | . |
| workstation-dotfiles-ad8324027 | P | P | P | P | . |
| workstation-dotfiles-08dad841c | P | P | P | P | . |

- **Hardest task:** d6d81ce51. Only Sonnet solved it.
- **Two tasks split the cloud models:** 99cb03e95 and ccf81588b.
- **Qwen3-Coder:** it passed only the two tasks every arm passed. Its median of 19 turns and about 5,100 output tokens
  per task, against 104 turns and about 59,000 for Flash-Next, show it stopping early rather than running out of time.

## Predictions

| # | Prediction | Field | Measured | Verdict |
|---|---|---|---|---|
| P1 | the ceiling is broken | `S.pass_count` <= 9 | 8 | HELD |
| P2 | Opus is at least Sonnet | `O.pass_count` >= `S.pass_count` | 8 >= 8 | HELD |
| P3 | best local is close | max(H, T27) >= S - 2 | 9 >= 6 | HELD |
| P4 | the incumbent trails | `Q.pass_count` < max(H, T27) | 2 < 9 | HELD |
| P5 | the two leaders are level | abs(H - T27) <= 2 | 1 | HELD |
| P6 | cloud cost | S <= $10 and O <= $20 | $2.82, $7.75 | HELD |
| P7 | local is slow | `H.wall_median_s` >= 5 x `S.wall_median_s` | 1,275 s vs 5 x 149 s = 745 s | HELD |

**Headline, defined before the runs:**
- H and T27 both **reach Sonnet** and **reach Opus**: their `pass_count` is >= 8.
- Q reaches neither.
- Gate: not triggered. Neither cloud model scored 10/10, so the bank did not hit its ceiling.

## How far to trust it

1. **Prompts were corrected four times while the runs were under way** (amendments 1-4, five corrections to three
   tasks). Each time, the hidden tests required something the prompt never stated: patch targets, result keys, a
   variable-name allowlist, a list type, whole-module imports, empty-set behaviour. Every correction was made before any
   local arm reached that task. Cloud runs on the old prompts are kept under `raw/<arm>/superseded/` and every arm is
   scored on the final prompts. The automated prompt checks caught none of the five; reading the cloud failures caught
   them all (F184).
2. **Weak test on 99cb03e95.** Part of its tests check the source text near gate calls in `pipeline.py`. A correct fix
   written differently can fail them. Both cloud arms failed here and both local leaders passed, so this one task should
   not be read as a local advantage. Without it the score is H 8, T27 7, S 8, O 8, and the headline still holds for H.
3. **One sample per task** at non-zero temperature. A one or two task gap is not evidence of a ranking.
4. **The prompt author knew the fixes**, and the prompts state every new name the tests call. They are closer to a spec
   than an issue report, the same for every arm.
5. **Our own code.** These are 10 tasks from three of the owner's Tier B repos, not general coding.
6. **One transcript lost.** S's amendment-3 transcript for ad8324027 was overwritten when the amendment-4 run was
   stripped. That result was superseded and is not scored.
7. **A model result is a setup result.** Each arm is a model plus its engine and config (Rule 8).

## What it changes

- **Local coding default.** Qwen3-Coder-30B is no longer a sound local coding default. On E154's easier bank it solved
  11/15, and here 2/10. Flash-Next on Halogen is the strongest local setup measured, with Qwen3.8-27B on Talus level
  within noise. The routing guide change is the owner's call.
- **"Slow but very smart" exists.** On our own code, the best local setup matches the cloud on what it solves, at about
  8.6 times Sonnet's median time and no per-task cost.
- **Next:** E158 runs newer coding models (Ornith 1.5 35B and 122B, Tess 4.5 and 4, Raon-1 mini) on this frozen bank.
  See `results/e158-prereg.md`.
