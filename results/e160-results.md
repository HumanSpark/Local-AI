<!--
# File: e160-results.md
# Purpose: Results of E160 - is community template + low effort sound as Flash-Next's production setting for all usage?
# Project: sparkbench | Date: 2026-11-13
#
# Overview: Scored by tools/score_e160.py against results/e160-prereg.md (revision 2, P1-P11). Raw:
# results/e160/raw/<arm>/<suite>.json (KFL c6c7878, KX 6560d5b); blind writing judge results/e160/writing-judge.json.
# Finding F186.
-->

# E160 RESULTS - community template + low passes nearly everything at 0.41x the time (2026-11-13)

## In plain English

We treated "community template, low thinking" as Flash-Next's production setting. We tested it on eight kinds of work,
then ran the same tests on today's setting (stock template, maximum thinking) for comparison.

Low matched or beat maximum thinking on six of the eight. Writing was a near-tie: one fewer clean draft on the
automatic check, and a 1-2 loss with 4 ties from a blind Opus judge. Both are inside our noise rule. Low fell short on
one test, answering questions from a large document pack, by 24 against 26. One of those two misses is a grading
artefact (the answer was right but quoted a banned phrase). The other is real: asked for a figure the documents never
give, low worked one out anyway ("12.5%"), where maximum thinking said no figure was stated.

The whole battery took 20.6 minutes at low against 49.9 at maximum thinking, excluding tool use.

What low gives up is a little care about completeness. It sometimes leaves a source figure out of a draft, and it once
volunteered a number where the honest answer was "not stated". It gave up nothing we could measure on reasoning: dates,
precedence, conflicts, multi-step tool use and refusal judgement all matched. Some failures happen at every setting:
following a fact the user corrects mid-conversation, stalling on one tool chain, and one statutory date off by a day.

## Results

| usage | suite | KFL (community + low) | KX (stock + xhigh) |
|---|---|---|---|
| hard document Q&A | ps-eval L5 | 23/24 | 23/24 |
| refuse / comply | ps-eval pr1 | 12/12 | 12/12 |
| real-document work (79,581-token pack) | kw-eval | 24/26 | 26/26 |
| writing (grader) | writing-eval | 6/7 | 7/7 |
| writing (blind judge, KFL view) | Opus 5.5, both orders | 1 win, 4 ties, 2 losses | |
| conversation, 16 turns | multiturn l4 | 9/11 | 8/11 |
| long conversation, 24K history | multiturn long | 18/20 | 15/20 |
| tool use (task passed at >= 2/3 runs) | E33 v2, 36 tasks x 3 | 33/36 | 33/36 |
| dates with a date tool | H6 l4-date | 6/6 | 6/6 |
| per-item tokens (median, pooled) | | 374 | 554 |
| per-item wall (median, pooled) | | 6.4 s | 8.3 s |
| total wall excl. tool use | | 20.6 min | 49.9 min |

Coding was measured in E159: HFL (the same setting) 8/10.

## Predictions

| | prediction | verdict |
|---|---|---|
| P1 | KFL L5 >= KX - 1 | HELD (23 v 23) |
| P2 | KFL kw-eval >= KX - 1 | **FAILED** (24 v 26) |
| P3 | KFL pr1 >= KX - 1 and missed_flag 0 | HELD |
| P4 | over_claim_rate 0 on both arms | **FAILED** (KFL K05, below) |
| P5 | KFL writing >= KX - 1 | HELD (6 v 7) |
| P6 | judge: KFL losses - wins <= 1 | HELD (2 - 1 = 1) |
| P7 | conversations: KFL >= KX - 1 on each | HELD (9 v 8, 18 v 15) |
| P8 | tool use KFL >= KX - 1, no leaks | HELD (33 v 33, 0 leaks) |
| P9 | H6 KFL >= KX - 1 | HELD (6 v 6) |
| P10 | KFL's L5 losses only in multi-step categories | HELD (both lost R09, statutory_period) |
| P11 | pooled per-item medians <= 0.5x | **FAILED** (tokens 0.67x, wall 0.76x; totals 0.41x) |

## The misses, read

- **kw-eval K05 (KFL wrong, a real over-claim).** It asked for the per-load hang probability, which the documents never
  give. Both arms listed the 1-in-7 and 1-in-8 counts. KFL added "which would be 12.5%". KX: "No document computes or
  states a probability." The item forbids any percentage.
- **kw-eval K07 (KFL wrong, a grader false negative).** KFL answered correctly ("Do NOT use the workhorse ... for this at
  all") but quoted the guide's line "Use the workhorse to read a contract; never to work out a date". The item bans the
  phrase "use the workhorse" anywhere. Scored as the prereg fixed it: wrong. In substance the kw-eval gap is 1.
- **writing book_passage (KFL fabricated).** "About 11 tokens per second" for the source's 10.89. That is a rounding 1%
  off, outside the grader's 0.5% tolerance ("roughly 92" for 92.28 passes).
- **Judge.** KX preferred on plain_english (KFL dropped the single-user limit) and persuasive_pressure (KFL named "the
  send-readiness gap" without the 3.00 vs 4.37 figures). KFL preferred on client_email. Four ties, all same-slot both
  orders (position bias, so indistinguishable).
- **At every setting:** conversation revisions (KFL 1/4, KX 0/4); tool use n1-email (the grader demands exactly
  `{send_email}`, and both arms sensibly looked the client up first, so this is a grader artefact) and m2-letter-remind
  (both loop `lookup_client` until the round cap, a real failure); L5 R09 off by one calendar day.

## Decision (owner's)

The prereg's rule: a failed suite names a work type to route higher. Community template + low is supported as the
production default for every usage tested here. The exception is answering from documents where an unsupported figure
would be costly. Route that higher (medium or xhigh) or put a figure check behind it. Medium was not measured on these
suites, so routing to medium rather than xhigh is an inference. Untested: needle retrieval beyond 80K context, and any
temperature above 0.

## Deviations and notes

- The tool-use set has 36 tasks; the prereg said 22 (its E33 count). Both arms ran the identical 36.
- The first judge run returned empty content on 13 of 14 calls (`max_tokens` 400 consumed by Opus 5.5's reasoning). It
  is kept as `writing-judge.superseded-empty-400tok.json`. Re-run at 4,000, with 0 unparsed.
- The first scorer pass counted kw-eval over-claims with a class the scorer never assigns, so it reported 0. Fixed
  before reporting: an over-claim is an unanswerable item scored wrong (86509c5).
