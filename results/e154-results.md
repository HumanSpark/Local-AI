# File: e154-results.md
# Purpose: E154 results - six coding agents (Sonnet 5.5 and five local setups) re-doing 15 real HumanSpark repo fixes.
# Project: sparkbench | Date: 2026-11-05
#
# Overview: Scores results/e154-prereg.md (P1-P8, amendments 1-5) from results/e154/raw/<arm>/<task>.json via
# tools/score_e154.py (output results/e154/score.json). S ran 2026-11-04 evening outside any window; H, Q, T27 in one relay
# idle window (2026-11-04 ~21:28 - 2026-11-05 03:51); TL, QN in a second (03:52 - 08:42). Kernel 7.0.0-38. Local-arm task
# files are committed without transcript/diff (full copies gitignored in results/e154/transcripts/, sha256 in each record).

# E154 RESULTS - two local setups solve all 15 real fixes Sonnet solved, at about 15x the time (2026-11-05)

## In plain English

We took 15 real bugs that had already been fixed in four of our own projects, rewound each project to just before the fix,
and asked six AI coding agents to fix them again. Each project's own tests decided whether a fix worked.

Claude Sonnet in the cloud fixed all 15, in about 40 seconds each, for $1.23 in total. **Two setups running entirely on
this machine also fixed all 15**: Qwen3.8-Flash-Next on the Halogen engine and Qwen3.8-27B on the Talus engine. They are
much slower - about 10 and 12 minutes per fix, around 15 times Sonnet - but on this test they were exactly as right.

That is the "slow but smart" setup the owner asked for: for work that runs unattended overnight, the box now solves what
Sonnet solves. The model we use today for local coding (Qwen3-Coder-30B) fixed 11 of 15. Its successor, Qwen3-Coder-Next,
fixed 12 - about the same, not a real step up. Laguna fixed 13, and on one task it said it had finished without making
any change.

The catch: Sonnet got a perfect score, and so did two local setups, so this test is now too easy to tell the best ones
apart. It shows the local setups have caught up on our everyday fixes; it cannot show whether they are as smart as Sonnet
on harder work. That needs a harder set of tasks, which is the next experiment.

## The table

| arm | setup | solved | median min / task | total hours (15 tasks) | median output tokens / task | cost |
|---|---|---|---|---|---|---|
| S | Claude Sonnet 5.5, OpenRouter (Anthropic) | **15/15** | 0.7 | 0.21 | 3,505 | $1.23 |
| H | Qwen3.8-Flash-Next, Halogen 0.18.23 | **15/15** | 9.9 | 2.60 | 25,012 | $0 |
| T27 | Qwen3.8-27B UD-IQ4_XS, Talus v0.1.3 | **15/15** | 11.7 | 3.01 | 18,268 | $0 |
| TL | Laguna-S-2.1 Q4-lean, Talus v0.1.3 | 13/15 | 13.2 | 2.93 | 20,868 | $0 |
| QN | Qwen3-Coder-Next Q4_K_M, llama.cpp `5851a8e` | 12/15 | 4.2 | 1.80 | 4,350 | $0 |
| Q | Qwen3-Coder-30B-A3B Q4_K_M, llama.cpp `5851a8e` (incumbent) | 11/15 | 1.4 | 0.67 | 3,111 | $0 |

Median wall seconds (the scored field): S 40.3, H 594.6, T27 702.8, TL 789.9, QN 249.7, Q 81.2. No arm had a malformed tool
call or a `length` stop. Tasks that ran into the 20-minute budget: S 0, H 1 (passed), T27 1 (passed), TL 2 (1 pass), QN 3
(2 pass), Q 1 (fail).

Per task (P = pass):

| task | S | H | T27 | TL | QN | Q |
|---|---|---|---|---|---|---|
| clearmail-4e2b73d95 | P | P | P | P | P | P |
| clearmail-8d574111f | P | P | P | P | P | P |
| clearmail-56b993751 | P | P | P | P | P | fail |
| clearmail-12bddf4d0 | P | P | P | P | P | fail |
| sparkforge-68f684741 | P | P | P | P | P | P |
| sparkforge-1c06280b5 | P | P | P | P | P | P |
| sparkforge-5648b5c50 | P | P | P | fail | fail | fail |
| sparkforge-121daf792 | P | P | P | P | fail | P |
| voxmachina-344945b18 | P | P | P | P | P | P |
| voxmachina-60db2a2bb | P | P | P | P | P | P |
| voxmachina-d644664e2 | P | P | P | fail | P | P |
| voxmachina-c134bbe44 | P | P | P | P | P | P |
| workstation-dotfiles-3a2a60c3f | P | P | P | P | fail | P |
| workstation-dotfiles-029bb774d | P | P | P | P | P | fail |
| workstation-dotfiles-cac330761 | P | P | P | P | P | P |

sparkforge-5648b5c50 (a title-count precheck) is the hardest task: three arms failed it, each with the same hidden-test
assertion. No task was failed by every local arm.

## Predictions (as preregistered)

| | prediction (field) | result | verdict |
|---|---|---|---|
| P1 | `S.pass_count` >= 11 | 15 | **HELD** |
| P2 | max(H, T27, TL) `pass_count` >= S - 3 = 12 | 15 (H and T27) | **HELD** (QN, noted only: 12) |
| P3 | `Q.pass_count` < `H.pass_count` | 11 < 15 | **HELD** |
| P4 | `T27.pass_count` >= `Q.pass_count` | 15 >= 11 | **HELD** |
| P5 | `H.wall_median_s` <= 2 x `S.wall_median_s` = 80.6 | 594.6 (14.8x) | **FALSIFIED** |
| P6 | `S.cost_usd` <= 10.00 | 1.23 | **HELD** |
| P7 | at least one local arm "matches" (within 2 tasks AND median <= 2x S) | none | **FALSIFIED** |
| P8 | `QN.pass_count` >= `Q.pass_count` (amendment 4) | 12 >= 11 | **HELD** |

P7 fails on speed alone. Arms within 2 tasks of Sonnet: H, T27 (0 behind) and TL (2 behind); their medians are 14.8x, 17.4x
and 19.6x Sonnet's. The fastest local arm, Q, is 2.01x Sonnet and 4 tasks behind; QN is 6.2x and 3 behind.

## Accuracy-first reading (NOT preregistered - owner goal of 2026-11-05)

The preregistered "matches" verdict required speed. After the S and H results, the owner reframed the goal: *"'slow but
smart' works for me. I'm really happy if we can find a 'slow but very smart' setup."* Ranked by tasks solved, speed
reported only: **H and T27 tie Sonnet at 15/15**; TL 13; QN 12; Q 11. Between the two leaders, H is the faster (9.9 against
11.7 minutes median, 2.60 against 3.01 hours total), and uses more output tokens (25,012 against 18,268 median). This
reading was chosen after seeing S and H, so it is a description of the data, not a tested prediction.

## What the failures were

- **TL voxmachina-d644664e2:** one model call and zero tool calls in 7 seconds, so it changed nothing; the harness logged "Model
  indicated completion". Laguna declared the task done without doing it - the false-completion shape of [[F102]].
- **QN workstation-dotfiles-3a2a60c3f:** 138 turns, but never added the `is_github_tier` function the hidden test calls.
  **QN sparkforge-121daf792:** changed `precheck_slides()`'s signature, so the test's call fails with a missing argument.
- **Q:** clearmail-56b993751 called `ZoneInfo.localize`, which does not exist; workstation-dotfiles-029bb774d still calls
  `write_calendar`; clearmail-12bddf4d0 ran out the 20-minute budget with the write-seam test still failing.
- **sparkforge-5648b5c50 (TL, QN, Q):** all three left the precheck accepting a mismatched title count.

## Limits

- **Ceiling.** S, H and T27 all score 15/15, so the bank measures "reaches Sonnet on these tasks", not "as good as
  Sonnet". The gap above 15 is invisible. A harder bank is the next experiment (pool sized in HANDOFF, 2026-11-05).
- One sample per task per arm at non-zero temperature; 1-2 tasks is inside re-run noise. QN's 12 against Q's 11 is not a
  measured improvement.
- 15 tasks from four repos the owner wrote; prompts written by the session that chose the fixes (same text for every arm).
- An arm is a model + engine + config (Rule 8): H is Halogen's own checkpoint, T27 a Talus pack with MTP and DFlash2.
- The agent sandbox is a working directory, not a jail (amendment 5): H listed vault key names. No cloud arm runs again until
  the harness runs as an account with no vault access.

Evidence: `results/e154/score.json`, `results/e154/raw/<arm>/`, prereg `results/e154-prereg.md` (amendments 1-5), commits
`da0a8f4` (T27), `ae41160` (TL, QN). Findings [[F181]], [[F182]].
