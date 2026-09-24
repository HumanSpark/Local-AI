# E91 PRE-REGISTRATION - does Flash-Next change any routing recommendation? (2026-08-31)

Written BEFORE any arm runs. Every prediction names the FIELD it is scored
against, so it reads only one way (the E64 rule - a prediction that matched two
fields at once scored as neither).

## The question

`reports/2026-07-16-local-model-routing-guide.md` names **Qwen3.8-27B** for
cross-document reasoning (F74) and for anything counted across a calendar
(F80), and names the **workhorse** as unsafe for the second. Qwen3.8-Flash-Next
is a ~180B MoE with ~6B active. It costs the whole box: 87.25 GiB of weights
against 121 GiB of RAM, so it cannot be co-resident with production and cannot
join a two-model serve.

**The only question worth 2 hours is therefore: does it beat the model the guide
already names, by enough to justify taking the whole box?** Not "is it good".

## THE RULER PROBLEM, and why two control arms exist

The incumbent figures (F74, F80) were measured on build `9e40df63b`.
**Flash-Next cannot run on that build at all** - `qwen4exp` landed upstream in
PR #27742 on 2026-08-27, and the pinned worktrees predate it. Flash-Next runs
only on `daef7b687` (build 1047).

E85 established that extrapolation safety is **per-axis**: the same build-770
numbers were SAFE for throughput and **UNSAFE for correctness**, where 0 of 24
became 2 of 24. Correctness is exactly the axis this experiment measures. So
comparing Flash-Next on the new build against frozen scores from the old one is
a two-rulers comparison and would be worthless.

**Both incumbents are therefore re-run on the NEW build in this session.** The
comparison is same-build or it is not made. This is the majority of the design
and most of its cost.

## Arms, in run order

Cheap and diagnostic first, so a broken instrument is found before the
expensive arm, and so a session that overruns still has its controls.

| # | arm | model | effort | why it is here |
|---|---|---|---|---|
| A | workhorse | Qwen3-30B-A3B-Instruct-2507-Q4_K_M | n/a | ruler check - must reproduce its known l4 floor |
| B | incumbent | Qwen3.8-27B-Q4_K_M | `low` | ruler check AND the model to beat |
| C | challenger | Qwen3.8-Flash-Next UD-IQ4_XS | `low` | matched to B's effort |
| D | challenger | Qwen3.8-Flash-Next UD-IQ4_XS | `medium` | **only if the clock allows** - F71 and today's sanity load both show effort dominates this family |

All arms: same build (`wt/daef7b6`, build 1047 `daef7b687`), same banks, same
grader, temperature 0, `-fa on -ctk q8_0 -ctv q8_0`.

## Banks - both frozen, both graded mechanically, no judge

- **l4, 15 questions** (`spikes/ps-eval/{corpus_l4,questions_l4}.py`). F80's
  instrument. Its eight **counted-period** items - `statutory_period`,
  `breach_clock`, `interest_calc`, `notice_period` - are where the workhorse
  scores 0 of 8 and Qwen3.8-27B 7 of 8. The sharpest discriminator this
  programme has.
- **l3, 12 questions, `--distractors 9`** (`corpus_l3`/`questions_l3`). F74's
  cross-document instrument. n=9 is chosen because it reproduces E41's arm
  byte-for-byte, so the pack is not a new variable.

## Predictions. The FIELD is named in each.

1. **PRIMARY: Flash-Next (arm C) scores >= 7 of 8 on the l4 counted-period
   categories.** Field: the summed `by_category[c]["correct"]` for
   `statutory_period`, `breach_clock`, `interest_calc`, `notice_period`.
   7 is the incumbent's measured score; at or above it is the only result that
   would move the guide.
2. **Flash-Next (arm C) scores >= 10 of 12 on l3.** Field: the l3 run's
   `correct` total.
3. **RULER CHECK: the workhorse (arm A) scores 0 or 1 of 8 on the l4
   counted-period categories.** Field: as prediction 1, arm A. F80 measured 0.
4. **RULER CHECK: Qwen3.8-27B (arm B) scores 6, 7 or 8 of 8 on the same.**
   Field: as prediction 1, arm B. F80 measured 7.
5. **Flash-Next (arm C) over-claims at most once.** Field: `over_claims`,
   which counts `underspecified` items answered rather than declined.
6. **Flash-Next (arm C) returns no empty answers and no format errors.**
   Field: `format_error` count, plus any result whose `content` is empty.
   Registered because today's sanity load returned `finish_reason: length`
   with empty `content` at the template's default effort - a real risk that
   `low` does not fully remove.

## Falsifier - and it gates the whole session

**If prediction 3 or prediction 4 fails, no Flash-Next number from this session
may be compared against F74 or F80.** A control that does not reproduce its own
known score means the build moved the instrument, and the honest output is then
a note that the ruler changed, not a verdict about the challenger. Say so in
the results file rather than quietly reporting arm C against frozen figures.

**Second falsifier, on the challenger:** if arm C scores at or below the
workhorse on l4 counted periods, the guide does not change and the answer to
the driving question is no - a model that costs the entire box and does not
beat a 15.66 GiB one on its own strongest axis is not a production candidate
here.

## What this experiment does NOT measure, declared up front

Speed, throughput, prefill curves, context ceiling, tool use, vision, coding.
All out of scope. **No timing from this session is a finding** - the arms load
different-sized models and the point is correctness. Vision in particular is
untested by anything here despite the model having a vision tower.

## Cost and window

One maintenance window, relay down for the whole session (Flash-Next cannot
share the box). Estimated: arm A ~5 min, arm B ~20 min, arm C ~40 min, arm D
~40 min if run. With load and collation, **80 min for A-C, ~2 h with D.**

Rule 9: the relay is DOWN for every arm, so the GPU is uncontended and the runs
are valid. `tools/e91/run_e91.sh` opens and closes the window itself and
restores the relay on any exit, including failure and Ctrl-C.
