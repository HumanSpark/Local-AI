<!--
# File: results/e165-prereg.md
# Purpose: Pre-registration for E165 - the test audit's re-runs of the suites whose prompts changed, on every arm.
# Project: sparkbench | Date: 2026-11-17
#
# Overview: Written and committed BEFORE any E165 run, after the corrected graders landed (9b6090c). Runner
# tools/run_e165.sh: arm Q through tools/cloud_proxy.py (ledger results/e165/raw/ledger.jsonl, ceiling $1.50); arms
# KFL KX HS LM through tools/run_e154_arms.sh in one idle window. Scorer tools/score_e165.py -> results/e165/score.json.
-->

# E165 PRE-REGISTRATION - re-running the corrected tests on every arm (2026-11-17)

## In plain English

The owner asked for an audit of the tests after E164 showed Qwen4 Max being marked down for doing what the test's
own instructions told it to do. The audit found the same kind of fault in five places, and some of them had been
marking production down too, for months. Where a fault was only in the marking, we re-marked the answers we already
had. Where the fault was in what the model was told, the old answers cannot be re-marked fairly, because the model
was answering a different question. Those tests have to be run again. This file fixes what we expect before we run
them, so the re-run cannot be read to suit us.

## What changed (committed at 9b6090c, before this file)

| suite | defect | fix | rescored how |
|---|---|---|---|
| tool use | 7 clients named by tasks missing from the pretend database; instructions say look up first and ask when information is missing | records added that agree with each prompt; letters-only surname match | re-run |
| tool use | no date anywhere; "in 14 days" invited a question | system prompt states today's date (Monday 16 November 2026) | re-run |
| tool use | `kind: tool` needed the EXACT tool set, failing the lookup the instructions require (KFL and KX lost n1 in 6 of 6 runs) | expected tools plus at most `lookup_client` | re-run |
| conversations | rules said anything contradicting the record loses to the record, so every arm rejected the "correction for the file" the revision probes score | rules separate a correction or new fact (apply it) from a claim about what the record says (record governs) | re-run |
| conversations | decline wording checked before a correct answer | positive match first, as L5 | old answers re-graded: no change on any arm |
| H6 / pack | STAT-LIM 3 "the corresponding day" read two ways (14 or 15 September) | names the accrual date | re-run |
| L5 | E07 correct "No" lost to the word "silent"; R09 key added the parallel months | leading Yes/No read first; R09 key 31 July | re-graded |
| writing | 10.89 rounded to 11 flagged; F-A paraphrase missed; 2 x box cost flagged | rounding allowed except where forbidden; markers; derivation | re-graded |
| kw-eval | K07 trap fired on a quotation of the source | quoted phrases are not assertions (scorer v3) | re-graded |
| drafting | every hard flag on E162/E164 a false positive | CHECKER 2026-11-17.1 | re-graded; now equals hand adjudication |

Re-graded results (already computed, not predictions): L5 KFL KX HS LM 23 -> 24, Q 22 -> 24; writing KFL 6 -> 7,
HS 6 -> 7, LM 4 -> 6, Q 6 -> 7, KX 7; kw KFL 24 -> 25, LM 25 -> 26. Drafting raw flags fall to the hand-adjudicated
set: one real drop (M C02), three borderline traps (L C06, L C09, M C09), one prompt defect (X C02).

## Re-run arms and settings

Each arm exactly as it ran in its own experiment; only the suite code differs. Suites: tool use v3 (36 tasks x 3
runs), mt-l4, mt-long, H6 l4-date with the date tool.

| arm | model, setting | source experiment | how |
|---|---|---|---|
| KFL | production Flash-Next, community template, effort low | E160 | Halogen image, idle window |
| KX | Flash-Next, stock template, effort xhigh | E160 | Halogen image, idle window |
| HS | Flash-Next, stock template, effort low | E163 | Halogen image, idle window |
| LM | Flash-Next on AMD HRX Loom, effort low | E163 | loom-serve via the model-field proxy, idle window |
| Q | qwen/qwen4-max, provider default | E164 | cloud_proxy, ceiling $1.50 (est. $0.59 from E164's ledger) |

## Predictions (each names its field in results/e165/score.json, `arms.<arm>.<suite>`)

- **P1:** Q `tooluse.corrected` >= 32 (v2: 24).
- **P2:** KFL `tooluse.corrected` >= 34 and KX `tooluse.corrected` >= 34 (v2: 33 each).
- **P3:** `m2-letter-remind` absent from `tooluse.failed` on at least 4 of the 5 arms (v2: failed on all 5).
- **P4:** `n1-email` absent from `tooluse.failed` for KFL and KX (v2: failed, exact-set rule).
- **P5:** `tooluse.leaks` = 0 on every arm.
- **P6:** mt-l4 turn T05 (the first revision probe) correct, i.e. absent from `mt-l4.lost`, on at least 4 of 5 arms
  (v2: lost on all 5).
- **P7:** No arm has an `accepted_false` outcome in `mt-l4.lost` or `mt-long.lost`. This is the safety check on the
  rule change: telling the model to apply corrections must not make it accept false claims (v2: none).
- **P8:** `mt-l4.corrected` >= `mt-l4.original` + 1 on every arm.
- **P9:** `h6.corrected` = 6 for KFL, KX and Q (v2: 6 each); at least one of HS and LM gains P3.
- **P10:** Q's E165 spend (ledger total) <= $1.00.

## Noise rule

E160's: one sample per item for conversations and H6, three runs per tool-use task; a difference of 2 or more items
is needed to call one arm better than another. A re-run can also LOSE items to sampling; such losses are reported,
not explained away.

## Known limits, declared now

- The re-run changes prompts, so v3 tool use, CONVERSATION_VERSION 2026-11-17.1 and CORPUS_L4_VERSION 2026-11-17.1
  results are not comparable with any earlier result on those suites. The original columns stay in every table.
- L5, pr1, writing and kw-eval are not re-run: their prompts did not change, so re-grading the saved answers is exact.
- kw-eval's K07 defect also undercounted older banked arms (Mistral Large, GLM-5.2, E87); they are noted, not
  restated.
- E162 task C02's wrong weekday in the prompt stays: fixing it would void six arms' banked drafts and their judge
  verdicts for one task, and it affected one draft (X) mildly.
- Q wall times are VOID as speed (cloud). Local arms run with the relay idled; production is unavailable for about
  two hours.
