<!--
# File: e162-results.md
# Purpose: Results of E162 - on client-shaped drafting, how close is production Flash-Next (low, medium, xhigh) to
# Claude Sonnet 5.5 and GPT-6.1 Sol, judged blind in pairs and checked mechanically?
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Scored against results/e162-prereg.md (P1-P10, decision rule, amendment 1) by tools/score_e162.py, which
# writes results/e162/score.json. Drafts results/e162/drafts-<arm>.json, mechanical checks results/e162/grade.json,
# verdicts results/e162/judge-grok-4.7.json and results/e162/judge-kimi-k3.1-pro.json, hand adjudication
# results/e162/adjudication.json. Finding F189.
-->

# E162 RESULTS - on client drafting, GPT-6.1 Sol beats production at every effort; the gap is accuracy, not polish (2026-11-15)

## In plain English

We gave the local model ten realistic jobs for invented businesses, the kind a firm hands an assistant: a proposal
section, meeting actions, a reply to an angry customer, a contract explained in plain English, and so on. Claude
Sonnet 5.5 and OpenAI's GPT-6.1 Sol did the same jobs. Two judges from other AI companies compared every pair of drafts
without knowing who wrote which.

GPT won clearly. Against the local model it won 7 to 9 more jobs than it lost, at every effort level and with both
judges. Claude beat the local model's everyday setting (low) with both judges, but against the higher efforts the
judges disagreed.

The judges' main reasons were about accuracy. When the local model lost, it was usually because it added something
the notes did not support or left out something the reader needed. For example, it told a client their timetable
would fit a deadline that the notes never said it would fit. It also promised an angry customer a follow-up that
nobody had offered. Polish and style mattered less.

Our automatic checks caught none of that. They look for invented figures and a few planted over-claims, and on those
every model was clean once each flag was checked by hand. GPT's eight "invented figures" were all correct conversions
from thousands of euros into euros. So the local model was not making up numbers. It was making promises and judgements
the notes did not support.

Thinking harder helped. Medium and xhigh each beat low with both judges, which we had predicted would not happen. They
still lost to GPT by the same margin.

What it means: drafts that go to a client under your name are frontier-model work, or local drafts that a person edits
before sending. That is the rule we wrote down before the run, and the results triggered it.

## Arms and run

| arm | model | how called | drafts | time for 10 | cost |
|---|---|---|---|---|---|
| L | production Flash-Next, Halogen, community template | guard, no effort sent (live default low) | 10/10 ok | 171 s | local |
| M | same | `reasoning_effort: medium` | 10/10 ok | 232 s | local |
| X | same | `reasoning_effort: xhigh` | 10/10 ok | 692 s | local |
| C | `anthropic/claude-sonnet-5.5` | OpenRouter, provider default | 10/10 ok | 97 s | $0.14 |
| G | `openai/gpt-6.1-sol` | OpenRouter, provider default | 10/10 ok | 91 s | $0.05 |

`halogen_effort_check.py` printed LOW DEFAULT LIVE before L and after X. Kernel 7.0.0-42-generic; Halogen image
`ghcr.io/peonist-ai/halogen-flash-server@sha256:b53c96edc042b1d9570cda2771c5002527f94d6aca0c8704a4475aa621d355ff`.
Production stayed up, so local wall times are indicative.

## Blind pairwise verdicts (net = tasks decided for the first arm minus for the second, of 10; decided = both orders agree)

| pair | grok-4.7 | kimi-k3.1-pro |
|---|---|---|
| G over L | **+7** | **+8** |
| G over M | **+7** | **+9** |
| G over X | **+7** | **+9** |
| C over L | **+3** | **+7** |
| C over M | +1 | +4 |
| C over X | -2 | +4 |
| G over C | +5 | +4 |
| M over L | +4 | +2 |
| X over L | +5 | +4 |
| X over M | +2 | +1 |

Judge agreement: identical outcome on 67 of 100 pair-tasks (0.67; 0.684 over the 98 both resolved).

## Completion and cost of judging (amendment 1)

| judge | calls answered, first pass | after one retry | pair-tasks resolved, first pass | after retry | cost first pass | retries | total |
|---|---|---|---|---|---|---|---|
| grok-4.7 | 198/200 | 200/200 | 98/100 | 100/100 | $7.53 | $0.15 | $7.68 |
| kimi-k3.1-pro | 149/200 | 198/200 | 61/100 | 98/100 | $8.66 | $4.26 | $12.92 |

Total judging cost $20.60. Drafting cost $0.19. Total cloud spend for E162 is $20.79, against the prereg's estimate of
under $20.

- **Why Kimi returned empty replies is not established.** The first pass recorded no finish_reason. Of the 51 retries,
  48 finished normally (`stop`). Token counts are known for 46 of them, which ran 2,484 to 14,475 completion tokens.
  - 32 used more than the original 6,000 cap, which fits the idea that reasoning used up the cap.
  - 14 answered in under 6,000 tokens, which the original cap would have allowed. Exhaustion does not explain those.
    Run-to-run variation at temperature 0, or a provider-side fault, would.
  - The 2 retries without counts ran before amendment 1 added that field.
  - 3 retries hit the new 16,000 cap (`length`). C05 C v G still gave a verdict. C02 M v X and C08 C v G came back empty
    again, and those 2 pair-tasks stay unresolved under the stopping rule.
- **The conclusions do not depend on the retries.** On first-pass verdicts alone, G leads L, M and X by 7/7, 7/6 and
  7/9 (grok/kimi), and C leads L by 4/4. The decision rule fires either way. The retries changed one prediction's margin
  but not its verdict: Kimi's M over L is +1 on the first pass and +2 after. P3 fails on grok's +4 regardless.
- The Kimi spend includes $0.13 from a first retry process. It was stopped after 2 calls so that amendment 1's metadata
  fields could be added, and it is not in the file's `spend_redo`.

## Mechanical checks, raw and adjudicated

| arm | dropped awkward facts (of 20) | invented figures raw | adjudicated real | over-claim traps raw | adjudicated real (borderline) |
|---|---|---|---|---|---|
| L | 1 | 0 | 0 | 3 | 0 (2) |
| M | 1 | 0 | 0 | 1 | 0 (1) |
| X | 1 | 1 | 0 | 0 | 0 |
| C | 1 | 3 | 0 | 1 | 0 |
| G | 1 | 8 | 0 | 1 | 0 |

Each verdict is in `results/e162/adjudication.json`:

- **GPT's 8 figures are false positives.** The source table is in € thousands. GPT wrote each figure out in euros, for
  example €74,000 for "74", and every conversion is correct.
- **Claude's 3 figures are false positives.** They are gross-profit figures labelled "By our calculation", and they
  match the sum over the stores (€36.3k, 5.5%; Athlone €51.6k).
- **xhigh's date is our task's fault.** C02's prompt calls 13 November 2026 a Thursday, but it is a Friday. xhigh used
  the real calendar for "Monday 16 November".
- **The three C08 trap hits are false positives.** They restate the contract's "CPI plus 3 percentage points".
- **Three trap hits are borderline.**
  - L C06: "so this does not happen again".
  - L C09 and M C09: "if Zapier goes down / breaks". This is a conditional risk the notes do not raise, but it is not
    a claim that Zapier is unreliable.

**The checker missed what the judges caught.** Two of the judges' cited errors were checked by hand against the low
drafts, and both are real:

- **C01:** low says "A 6-week pilot at Trim, followed by a phased rollout ... fits within that window". The notes give
  the pilot and the March 2027 deadline, but never say one fits the other.
- **C03:** low leaves out the €2,400 deposit and why it is not refundable. It also promises that the operations manager
  "will come back to you" and that it will follow up "shortly", which the notes do not offer.

Neither is a planted trap, and the dropped-fact check passed C03 because the draft mentions the operations manager.
These are unsupported commitments and missing context, a kind of error a regex cannot see. Only two cases were
spot-checked; there is no full count.

## Predictions

| | prediction | verdict |
|---|---|---|
| P1 | net(C over L) >= 2 on both judges | HELD (+3, +7) |
| P2 | net(G over L) >= 2 on both judges | HELD (+7, +8) |
| P3 | \|net(M over L)\| <= 1 on both | **FAILED** (+4, +2: medium beat low) |
| P4 | \|net(X over L)\| <= 2 on both | **FAILED** (+5, +4: xhigh beat low) |
| P5 | L dropped <= 3 and <= C + 2 | HELD (1; C 1) |
| P6 | trap hits <= 2 for L and C (raw) | **FAILED** (L 3 raw; adjudicated 0 real, 2 borderline) |
| P7 | invented figures <= 3 every arm (raw) | **FAILED** (G 8 raw; adjudicated 0 real for every arm) |
| P8 | judge agreement >= 0.60 | HELD (0.67) |
| P9 | L time <= 0.5 x X | HELD (171 s v 692 s) |
| P10 | no incomplete drafts, no think leaks | HELD |

P6 and P7 failed on raw counts, as registered. Both failures come from checker false positives, not from the drafts.

## Decision (the prereg's rule)

GPT leads every local effort by 2 or more on both judges (L +7/+8, M +7/+9, X +7/+9), so the third branch applies.
**Client-facing drafting is recorded as a frontier job, or a local draft edited by a person before it goes out.** The
routing guide now says so.

- **Claude does not reach that bar against every effort.** Against M, grok gives +1. Against X the judges disagree
  (grok -2, kimi +4), so the result is "not shown".
- **The second branch, routing client drafting to a higher local effort, does not apply.** Medium and xhigh beat low,
  but neither comes within 1 of GPT.
- **Higher effort still helps for local drafting.** For work that stays in-house, medium or xhigh writes better drafts
  than low with both judges (M +4/+2, X +5/+4 over L). This is a measured result, unlike the earlier routing note for
  document answers, which was a judgement.

## Limits

- **Small sample.** Ten tasks and one draft per arm per task, so a net of 1 or 2 is within noise.
- **Two judges.** Both are from families other than the contestants', and their agreement was 0.67.
- **Fictional tasks.** The businesses are invented, the tasks are short, and no real client data was involved.
- **Arms had their own defaults.** Cloud arms ran at their provider's default effort, and local max_tokens differed
  from cloud (32,768 against 16,000). No draft hit either cap.
- **Task defect.** C02's weekday is wrong in the prompt, which may have confused every arm on that task.

## Evidence files

Prereg `results/e162-prereg.md`. Drafts `results/e162/drafts-L.json`, `results/e162/drafts-M.json`,
`results/e162/drafts-X.json`, `results/e162/drafts-C.json`, `results/e162/drafts-G.json`. Mechanical checks
`results/e162/grade.json`. Verdicts `results/e162/judge-grok-4.7.json`, `results/e162/judge-kimi-k3.1-pro.json`.
Score `results/e162/score.json`. Adjudication `results/e162/adjudication.json`. Logs `results/e162/run.log`,
`results/e162/judge-kimi-redo.log`, `results/e162/judge-grok-redo.log`. Tasks `spikes/client-tasks/tasks.py`; runner
`tools/run_e162.py`, `tools/run_e162.sh`; scorer `tools/score_e162.py`.
