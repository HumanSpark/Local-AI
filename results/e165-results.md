<!--
# File: results/e165-results.md
# Purpose: Results of E165 - the owner-ordered test audit: defects found, graders corrected, every arm re-scored or re-run.
# Project: sparkbench | Date: 2026-11-17
#
# Overview: Scored against results/e165-prereg.md (P1-P10) by tools/score_e165.py -> results/e165/score.json. Fixes
# at 9b6090c, prereg 4f68284, re-run raw results/e165/raw/<arm>/ (KFL 8a3b5c1, KX 7386214, HS and LM banked by the
# runner), Q's billed calls in results/e165/raw/ledger.jsonl. Finding F192; addenda on F190 and F191.
-->

# E165 RESULTS - the tests were marking models down for following their own instructions; corrected, every arm passes tool use and the conversation gaps close (2026-11-17)

## In plain English

E164 showed Qwen4 Max losing tool-use marks for asking a sensible question that the test's own instructions told it
to ask. The owner asked for the tests to be audited and corrected properly. The audit found the same kind of fault in
five places, and most of them had been marking production down too, in some cases since the tests were written.

The two biggest were in what the model was told. The tool-use test asked for letters to seven clients who were not in
its pretend client database, while telling the model to look clients up first and to ask when information is missing.
Models that obeyed both instructions failed. The conversation test told the model that anything the user says that
contradicts the record loses to the record, then marked it wrong for not applying the user's "correction for the
file". Every model obeyed and every model was marked wrong. Smaller faults were in the marking: a correct "No" scored
as a refusal because the explanation used the word "silent", an answer key that was itself wrong, and a writing
checker that called "about 11" an invention when the source said 10.89.

Corrected, every model scores 36 of 36 on tool use, and every model now applies a correction when told one without
accepting the false claims the test also plants. The practical consequences: Qwen4 Max's tool-use gap was entirely
the test; AMD's Loom engine had no tool-use problem either; and production's setting, chosen on these suites in
November, stands, because the corrected scores leave the comparison where it was. The tool-use test is now too easy
to tell these models apart, which is the next problem, not a reason to keep the broken version.

## What was wrong, and what changed (9b6090c)

| suite | defect | whose marks it cost | fix |
|---|---|---|---|
| tool use | 7 clients named by tasks absent from the 3-client database; SYSTEM says look up first, ask when information is missing | every arm (m2 failed on all 5) | records added that agree with each prompt; letters-only surname match |
| tool use | no date given; "in 14 days" invited a question | Q, LM (n2) | SYSTEM states "Today is Monday 16 November 2026" |
| tool use | `kind: tool` passed only on the EXACT tool set, failing the lookup SYSTEM instructs | KFL, KX 6/6 runs of n1; Q n3 | expected tools plus at most `lookup_client` |
| conversations | RULES: a statement contradicting the record loses to it; revision probes score applying the user's correction | every arm (T05 lost by all 5) | RULES separate a correction or new fact (apply) from a claim about what the record says (record governs) |
| conversations | decline wording checked before a correct answer | none observed | positive match first (as L5) |
| H6 / L4 pack | STAT-LIM 3 "the corresponding day" read as 14 or 15 September | HS, LM (P3) | names the accrual date |
| L5 | E07: correct leading "No" scored a decline for "silent" | Q | leading Yes/No read first |
| L5 | R09 key added the parallel months (31 Aug); item and FA 4.4 forbid it | every arm (all answered 31 Jul) | key 31 July |
| writing | 10.89 -> "about 11" flagged (1.0% > 0.5% tolerance) | KFL, HS, LM | rounding to whole or 1 dp allowed except where forbidden |
| writing | F-A "without closing that gap" missed; 2 x EUR 3,680 flagged | Q; LM | marker; derivation |
| kw-eval | K07 trap "use the workhorse" fired on a quotation of the source | KFL, LM (and older arms) | scorer v3: quoted phrases are not assertions |
| drafting checker | every hard flag a false positive (C08 CPI regex, C05 units, 12-hour times, 3 paraphrases) | all six arms | CHECKER 2026-11-17.1 |

Every fix has a regression check in its validator (`validate_ps_eval_l5`, `validate_multiturn`,
`validate_tooluse_conditional`, `validate_writing_eval`, new `validate_client_tasks`), each shown FAILING on the
pre-fix code and passing after. All six validators pass.

## Original and corrected scores

Re-graded = the saved answers through the corrected graders. Re-run = the suite's prompt changed, so the arm ran it
again (E165, same model, server and effort as its source experiment).

| suite | how | KFL | KX | HS | LM | Q |
|---|---|---|---|---|---|---|
| L5 document Q&A (24) | re-graded | 23 -> **24** | 23 -> **24** | 23 -> **24** | 23 -> **24** | 22 -> **24** |
| writing (7) | re-graded | 6 -> **7** | 7 | 6 -> **7** | 4 -> **6** | 6 -> **7** |
| kw-eval (26) | re-graded | 24 -> **25** | 26 | 26 | 25 -> **26** | not run |
| refuse/comply pr1 (12) | unchanged | 12 | 12 | 12 | 12 | 12 |
| conversation l4 (11) | re-run | 9 -> **10** | 8 -> **10** | 9 -> **10** | 8 -> **10** | 10 -> **11** |
| conversation long (20) | re-run | 18 -> **20** | 15 -> **19** | 18 -> **20** | 17 -> **19** | 19 -> **20** |
| tool use (36 tasks, >= 2/3 runs) | re-run | 33 -> **36** | 33 -> **36** | 33 -> **36** | 28 -> **36** | 24 -> **36** |
| H6 dates (6) | re-run | 6 | 6 | 5 -> **6** | 4 -> **5** | 6 |

Arms: KFL production (community template, effort low); KX stock template, xhigh; HS stock template, low; LM AMD HRX
Loom, low; Q Qwen4 Max (cloud, provider default). The grader reorder alone moves none of the old conversation
answers, so every conversation change above comes from the corrected rules.

**Tool use v3:** every arm passes every one of the 36 tasks in every run (540 runs, 0 failures, 0 leaks). The
suite no longer separates these arms.

**What the arms still lose (all genuine):** T02/N2 (notice date under clause 2; 1 December for 31 December) - KX and
LM in both conversations, LM in H6; T14 (interest sum EUR 493.93 for 493.99) - KFL and HS in conversation l4; L5 and
kw items were already at or near ceiling. K05 stays lost by KFL (it turned "1 in 8" into "12.5%", the invented rate
the item's trap exists for).

**Drafting checker:** raw flags fall from 18 to 5 across the six arms, and the five left are exactly the hand
adjudication: one real dropped fact (M C02, the van off the road), three borderline traps (L C06, L C09, M C09), and
the prompt-defect flag on X C02.

## Predictions

| | prediction (field) | result |
|---|---|---|
| P1 | Q `tooluse.corrected` >= 32 | HELD (36) |
| P2 | KFL and KX `tooluse.corrected` >= 34 | HELD (36, 36) |
| P3 | `m2-letter-remind` passes on >= 4 of 5 arms | HELD (5 of 5) |
| P4 | `n1-email` passes for KFL and KX | HELD |
| P5 | `tooluse.leaks` = 0 on every arm | HELD |
| P6 | mt-l4 T05 correct on >= 4 of 5 arms | HELD (5 of 5) |
| P7 | no `accepted_false` on any arm, either conversation | HELD (0) |
| P8 | `mt-l4.corrected` >= original + 1 on every arm | HELD (+1, +2, +1, +2, +1) |
| P9 | `h6.corrected` = 6 for KFL, KX, Q; HS or LM gains P3 | HELD (both gain P3) |
| P10 | Q spend <= $1.00 | HELD ($0.64) |

## What this changes

- **F191 (Qwen4 Max):** its tool-use gap (24 vs 33) was entirely test defects; corrected it is 36/36, level with
  production, and it leads every suite but kw-eval (not run). The drafting result (+2 over production, -1 vs Sonnet,
  -6 vs GPT-6.1 Sol) is unaffected: the judge never used the checker.
- **F190 (Loom):** "trails Halogen on tool tasks" (28 vs 33) was the test; corrected both are 36/36. Its remaining
  differences from Halogen are speed and one date item (N2/T02), not tool use.
- **F186/F187 (production setting, E160):** KFL and KX stay within the noise rule of each other on every corrected
  suite (largest gap: conversation long 20 vs 19). The decision stands.
- **The suites are now at ceiling** for every arm on tool use, L5 and pr1. They can show a model losing ground, not
  gaining it. A harder tool-use bank is the follow-up (owner's "slow but very smart" goal), not part of this audit.

## Limits

- One sample per conversation and H6 item: KFL losing T14 this time is sampling, and gains of 1 are within E160's
  noise rule. The tool-use and conversation changes are large and uniform across arms, which sampling does not explain.
- The new versions (tool use v3, CONVERSATION_VERSION and CORPUS_L4_VERSION 2026-11-17.1) are not comparable with
  earlier results on those suites; every table keeps the original column.
- kw-eval K07 also undercounted older banked arms (Mistral Large, GLM-5.2, E87 arms A and B: K07 wrong -> correct
  under scorer v3, no other cell moved in 879 files). Those findings are not restated here.
- E162 task C02's wrong weekday stays (fixing it voids six arms' drafts and verdicts for one task).
- Local arms ran with the relay idled (18:56-20:49Z); the runner restored production.
