<!--
# File: results/e171-results.md
# Purpose: Results for E171 - Hy4-Flash SQ-96 on Strata 0.2.18 against production on the E167 coding bank.
# Project: sparkbench | Date: 2026-11-22
#
# Overview: scores the six pre-registered predictions (results/e171-prereg.md, 66ab0de) from results/e171/raw/HY/.
# Production comparison is E167 arm H (results/e167/raw/H/), same bank, same runner settings, 2026-11-18.
-->

# E171 RESULTS - Hy4-Flash on Strata (2026-11-22)

## In plain English

We ran Tencent's big new model on our ten hard coding tasks. It loaded and ran all day without trouble, but it is
slow here: about 24 words a second, a third of what its makers measured. Every task ran out its full hour. It
finished 3 of the 10, against production's 5. It solved three tasks production failed, and production solved five it
failed, and every one of those five took production more than 100 steps, a number Hy4 never reached inside an hour.
So this test says Hy4-Flash, as packed today, is too slow for our hour-per-task budget. It does not say the model is
less capable.

## Scores

| Prediction | Field | Value | Verdict |
|---|---|---|---|
| P1 loads | `HY.load_ok` | ready in 38 s, mem_guard 0 fires | HELD |
| P2 bigger is smarter | `HY.pass_count` >= 5 | 3 | FALSIFIED |
| P3 slower than production | `HY.wall_median_s` > 685 | 3,603 | HELD |
| P4 maintainer decode does not hold | `HY.speed.P8K.decode_tps` < 51 | 23.69 | HELD |
| P5 maintainer prefill does not hold | `HY.speed.P8K.prefill_tps` < 728 | 591.5 | HELD |
| P6 the disk is in the loop | `HY.engram_read_gib` > 1 | 16.2 (17,405,829,120 bytes) | HELD |

`HY.run_count` 10/10 (no task lost to the 19:00Z deadline; the last ended 18:52Z).

## Per task, against production (H, E167)

| Task | HY | HY turns | H | H turns | H wall s |
|---|---|---|---|---|---|
| clearmail-01d445d75 | pass | 30 | fail | 26 | 416 |
| clearmail-3d41463d0 | fail | 39 | pass | 106 | 660 |
| clearmail-7fe0a79c1 | fail | 47 | pass | 101 | 522 |
| another GPU job-390973aee | pass | 32 | fail | 23 | 461 |
| another GPU job-5ca87050b | fail | 28 | fail | 31 | 608 |
| sparkforge-22dee74e9 | fail | 40 | pass | 174 | 2,648 |
| sparkforge-625dcc2f8 | pass | 25 | fail | 26 | 710 |
| sparkforge-66de8e1d0 | fail | 29 | pass | 171 | 1,873 |
| workstation-dotfiles-a0d0e6f0d | fail | 29 | fail | 59 | 869 |
| workstation-dotfiles-ffaf96580 | fail | 29 | pass | 114 | 1,582 |

Every HY task stopped on `timeout` (wall 3,602-3,605 s); every H task stopped on `model-done`. HY: 0 malformed
calls, 0 length stops. HY's three passes are graded on the tree at the timeout.

The two arms' passes do not overlap. All five H passes took 101-174 turns; HY made 25-47 turns per hour. HY's three
passes are the tasks H gave up on early (23-26 turns). **The budget, not the model, is the binding constraint**: on
this evidence the bank cannot say whether HY would solve H's five given time.

## Speed (E163 block, thinking off, temperature 0)

P8K: prefill 591.5 tok/s, decode 23.69 tok/s, TTFT 12.59 s. P32K: prefill 586.2, decode 26.08. D1500: decode
31.66. Maintainer figures (51-60 decode, 728 prefill) were on SQ-64 with the page cache on; ours are SQ-96 with
`HY4_ENGRAM_ODIRECT=1` (declared deviation). How much of the gap each explains is not measured.

## Box health

Memory flat at ~28 GiB available from ~09:15Z to the end; swap untouched; no DeviceLost, no D-state hang; root
filesystem 104 GB free throughout (disk guard never fired). Relay restored 18:52:08Z, production probe passed.

## Limits

- One sample per task at temperature 0.9; ten tasks.
- Engine plus file plus config: Strata SQ-96 with O_DIRECT, not "Hy4-Flash".
- H's figures are from 2026-11-18, not re-run today.
- The 3,600 s cap was set for production-speed models; at HY's speed it censors every task.

## What would change the verdict

The same bank with no wall cap (or a turn cap matched to H's), and an O_DIRECT-off arm to price the safety
deviation. Both need another owner-present day (F193). Not queued.

Evidence: `results/e171/raw/HY/`, `results/e171/launch.out`, `results/e171/raw/mem_guard.log`,
`results/e171/disk_guard.log`. Finding: F197.
