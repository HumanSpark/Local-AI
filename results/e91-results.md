# E91 RESULTS (2026-08-31): Flash-Next matches the incumbent and never beats it, for 5.6x the memory and the whole box

Pre-registration: `results/e91-prereg.md`, written before any arm ran.
Raw: `results/raw/e91/`. Scorer: `tools/e91/score_e91.py`.
Build: `daef7b687` (build 1047), Vulkan RADV, `-fa on -ctk q8_0 -ctv q8_0`,
relay down for every arm (Rule 9 satisfied - the GPU was uncontended).

## The table

| arm | l4 walked | l4 total | l4 wall | l3 | l3 wall | weights |
|---|---|---|---|---|---|---|
| A workhorse Qwen3-30B-A3B | **0/8** | 6/15 | 15.1s | **4/12** | 60.4s | 17.28 GiB |
| B Qwen3.8-27B `low` | **7/8** | 14/15 | 803.6s | **12/12** | 598.3s | 15.66 GiB |
| C Flash-Next `low` | 6/8 | 13/15 | 523.0s | **12/12** | 413.8s | **87.25 GiB** |
| D Flash-Next `medium` | **7/8** | 14/15 | 681.5s | **12/12** | 469.1s | **87.25 GiB** |

## Predictions

| # | prediction | outcome |
|---|---|---|
| P1 | Flash-Next (effort-matched, arm C) >= 7 of 8 walked | **FALSIFIED** - 6/8 |
| P2 | Flash-Next >= 10 of 12 on l3 | HOLDS - 12/12 |
| P3 | workhorse reproduces 0-1 of 8 walked | HOLDS - 0/8 |
| P4 | Qwen3.8-27B reproduces 6-8 of 8 walked | HOLDS - 7/8 |
| P5 | Flash-Next over-claims at most once | HOLDS - 0 |
| P6 | Flash-Next returns no empty answers, no format errors | HOLDS - 0 and 0 |

**P1 is falsified as written and is not rescued by arm D.** The prediction named
the effort-matched arm, because that is the only comparison that isolates the
model from its reasoning budget. Arm D was registered as optional and
exploratory. The honest statement is: **falsified at matched effort, parity one
effort tier up.**

## The rulers held, and they held item-for-item

This experiment could only say anything if the build had not moved the
instrument. `qwen4exp` merged upstream on 2026-08-27, Flash-Next cannot run on
the older pinned builds at all, and E85 established that build-to-build
extrapolation is unsafe for correctness. Both controls were therefore re-run.

They did not merely reproduce their scores. They reproduced their **individual
items**:

- **The workhorse returned its documented wrong answers verbatim** - `30 October
  2026` for the one-month statutory period and `107.56` for the interest
  calculation, both quoted in F82 as its known failures. On l3 it failed
  `precedence 0/2` and `multihop 0/3`, which is word-for-word what the routing
  guide records for it.
- **Qwen3.8-27B's single miss was N2**, answered `1 December 2026` - the
  composition question F80 names as "its single remaining miss in the entire
  tier" and which the routing guide says "has never moved". It did not move, on
  a build that did not exist when that sentence was written.

**Unregistered but worth stating:** the workhorse's l3 total of 4/12 sits one
below F74's frozen 5/12, inside single-run noise, and its failure *shape* is
identical. Three independent reproductions in one session is stronger evidence
that the instrument survived the build change than the two registered checks
alone.

## What decides parity is the effort tier, and it is one item

Flash-Next at `low` and at `medium` differ on exactly one question:

| item | `low` | `medium` | correct |
|---|---|---|---|
| F1 `fee_basis` | EUR 79,200 - `off_by_calendar` | **EUR 106,800** - correct | EUR 106,800 |

Everything else is identical, N2 included. So the whole gap between "one point
below the incumbent" and "level with the incumbent" is a single item that a
higher reasoning budget recovers - which is F71's finding (effort dominates this
family) demonstrated more cleanly than F71's own evidence, because here nothing
else varies.

## l3 is saturated and cannot separate these models

Three arms scored 12/12 with zero over-claims and near-perfect citations. The
axis where Flash-Next's capacity was most likely to tell is the one where both
capable models are already at ceiling. This is the known pattern that an
instrument two models both saturate cannot reveal its own confounds; l3 at 9
distractors is now a workhorse-vs-capable discriminator, not a
capable-vs-capable one. **A harder cross-document tier would be needed to
separate Flash-Next from Qwen3.8-27B on this axis, and it has not been built.**

## The verdict

**No routing change.** Flash-Next is genuinely capable - far above the workhorse
on both banks, 12/12 on cross-document work, zero over-claims, perfect citations,
and faster per query than the dense 27B at every setting (413-682s against
598-804s), which is the MoE active-parameter advantage showing up honestly.

It also never beats the model it would displace. It matches it, at `medium`,
having needed a higher effort tier to get there - and matching costs **87.25 GiB
against 15.66 GiB**, 5.6x, and the whole machine, because nothing else can be
resident beside it. The second registered falsifier (scoring at or below the
workhorse) did not fire; this is not a dud. It is simply not a displacing model
on these axes.

**The one place this may still be wrong** is the framing. The routing guide is
written latency-first, and on that framing Flash-Next loses on cost. The
2026-08-31 SparkMax workload briefing argues the opposite optimisation target -
useful work completed per day, unattended, with confidentiality preserved -
under which a model that answers 14/15 and 12/12 overnight on a box nobody is
waiting at is judged differently. **This experiment measured capability per
query, not work completed per day**, and does not settle that.

## What was NOT measured

Speed as a finding (the eval arms' wall times are not benchmark figures; no
`llama-bench` leg ran on Flash-Next), long context beyond the l3 pack's ~21K
tokens, tool use, vision - which this model has and nothing here exercised -
coding, and abstention beyond the single `underspecified` item per bank.
