<!--
# File: e163-results.md
# Purpose: Results of E163 - AMD's agent-ported HRX Loom engine against production Halogen and llama.cpp on Flash-Next.
# Project: sparkbench | Date: 2026-11-16
#
# Overview: Scored against results/e163-prereg.md (P1-P8, amendments 1 and 1b) by tools/score_e163.py, which writes
# results/e163/score.json. Speed: results/e163/raw/<arm>/speed.json (tools/e163_speed.py). Quality: the E160 suites
# under results/e163/raw/LM and HS, graded by score_e160.arm_fields unchanged. Finding F190.
-->

# E163 RESULTS - AMD's Loom beats llama.cpp by 2.7x on long prompts, but not production Halogen; on tool tasks it asks where Halogen acts (2026-11-16)

## In plain English

On 2026-11-13 AMD announced that coding agents had ported 51 models to its new HRX Loom engine in four days. The
announcement said the ports ran long prompts about 1.5 times faster than llama.cpp. One of the 51 is our production
model, so we ran it on this box against llama.cpp and against Halogen, the engine we use in production.

AMD's claim against llama.cpp holds, and by more than they said. On a 32,000-token document Loom read the prompt 2.7
times faster than the newest llama.cpp, and it wrote answers 1.5 times faster.

Against Halogen it is mixed, and not good enough to switch. Loom read the 32,000-token document about as fast as
Halogen, slightly faster on the median. On an 8,000-token document Halogen was 1.6 times faster, and Halogen writes
answers 1.4 times faster.

On quality, Loom matched Halogen on reading documents and answering questions. On tool tasks it scored lower, 28 of
36 against 33, but the transcripts show why, and it is not a fault. When a client lookup came back empty, or when it
did not know today's date, Loom stopped and asked the user, which is what the test's own instructions say to do when
information is missing. Halogen pressed on and did the task, and the test rewards that. Loom also had two more writing
drafts flagged for adding figures the source did not give: it converted tokens into words and doubled a price.

What it means: production stays on Halogen, because Halogen is faster where it counts and Loom would also force a
change of chat template. Loom is worth watching: a four-day agent port that already matches Halogen on long prompts is
impressive, and its tool calling works.

## Arms and run

| arm | engine | weights | what ran |
|---|---|---|---|
| LM | loom-serve, hrx-loom 0.2.0.dev0 (hrx-system `314238a8`) | unsloth UD-Q4_K_XL + MTP Q8_0 (rev `766911a6`) | speed + E160 suites at low |
| LC | upstream llama.cpp `9fba51d` (2026-11-16), AMD's 1-stream flags | the same files | speed only |
| HS | production's Halogen image (digest `b53c96ed...`), stock template | Halogen's own checkpoint | speed + E160 suites at low |

Windows 05:41-07:28Z and 07:29-07:36Z on 2026-11-16, kernel 7.0.0-42-generic. Production was down for both and back
at 07:37Z (`halogen_effort_check.py`: LOW DEFAULT LIVE). An unscored smoke ran 05:37-05:39Z. No cloud spend.

## Speed (client-timed, median; E139's prompts, thinking off)

| field | LM Loom | LC llama.cpp | HS Halogen |
|---|---|---|---|
| prefill, 8K prompt (tok/s) | 968 | 433 | 1,579 |
| prefill, 32K prompt (tok/s) | 979 | 364 | 879 |
| decode, short prompt (tok/s) | 40.8 | 27.4 | 56.3 |
| decode after a 32K prompt (tok/s) | 37.4 | 23.6 | 49.9 |

- **The ruler agrees with the servers.** llama.cpp and Halogen report their own timings. The client figures agree with
  them within 1-2% on every request. Loom reports none, which is why the client times all three.
- **Halogen's 32K prefill is noisy.** Its three runs gave 879, 791 and 1,239 tok/s. E139 measured 1,152 server-side in
  September. Loom's three were 952, 979 and 1,020. The median favours Loom by 1.11x. With that spread, "about the same
  at 32K" is the fair reading.
- **Loom's first request after load took 38 s to first token**, a one-off warm-up (the P8K rep 0 row). Every later
  request was steady. The medians do not include it.
- **AMD's own figure did not quite reproduce.** Loom gave 979 tok/s at 32K against the card's 1,196, 18% lower. Short-
  prompt decode matched the card (40.8 against 41.9).

## Quality (E160 suites, effort low; KFL = production's E160 arm, reference only)

| suite | LM Loom | HS Halogen (stock) | KFL production (community, 2026-11-13) |
|---|---|---|---|
| L5 hard document Q&A | 23/24 | 23/24 | 23/24 |
| pr1 refuse / comply | 12/12 | 12/12 | 12/12 |
| kw-eval real documents | 25/26 | 26/26 | 24/26 |
| writing grader | **4/7** | 6/7 | 6/7 |
| conversation l4 | 8/11 | 9/11 | 9/11 |
| conversation long | 17/20 | 18/20 | 18/20 |
| H6 dates with a date tool | 4/6 | 5/6 | 6/6 |
| tool use (tasks passed at >= 2/3 runs) | **28/36** | 33/36 | 33/36 |

Tool calls leaked into text: 0 on both. Over-claims: 0 on L5 for both. Median completion tokens per item: LM 397, HS 367.

**What Loom lost on tool use.** It failed five tasks that Halogen passed. Halogen also failed c2 and c2b; production
passes them on the community template, so those two look template-related.

| task | Loom, 3 runs | Halogen |
|---|---|---|
| c4-date-before, c4b-date-before-onlyif, c5b-date-after-onlyif | called `lookup_client`, then stopped without creating the document (9 of 9 runs) | lookup then `create_word_document`, 3/3 each |
| n2-reminder | called no tool (3 of 3 runs) | `add_reminder`, 3/3 |
| n1-email | passed 1 run; in 2 it looked the client up first, then sent | 3/3 |

**Transcripts (diagnostic re-run, unscored, 08:53-09:00Z).** The harness keeps only the tools called, so the five
tasks were run again, 3 runs each on both engines, with the proxy recording every request and response
(`results/e163/raw/transcripts/{LM,HS}.jsonl`). The re-run reproduced the pattern: Loom c4 and c4b 0/3, c5b 2/3,
n2 2/3, n1 3/3; Halogen 3/3 on all but c4b (2/3).

- **The tool result is not lost.** In c4 the task's `lookup_client` returns "ERROR: no client record found for that
  surname". Loom's reasoning reads the error, works out the condition correctly (15 September is before 1 October, so
  EXPEDITED), then decides it lacks the client's details and asks for them. Halogen, on the same error, decides it has
  enough and writes the letter with the EXPEDITED title.
- **n2:** Loom says it does not know today's date and asks which date to use; Halogen picks one and calls
  `add_reminder`.
- **The task's own system prompt supports Loom's choice:** "If a request is missing information you need, ask a brief
  clarifying question instead of guessing." The grader scores these tasks as success only when the document or
  reminder is created.

So Loom's tool-use deficit is a behaviour difference: it asks where Halogen acts. It is not a tool-protocol defect.
Whether the difference comes from the weights (unsloth's GGUF against Halogen's checkpoint) or Loom's chat program
is not established. A first attempt at this re-run (08:44-08:52Z) went through a stale proxy with no logging and is
kept aside (`results/e163/raw/transcripts/first-attempt-no-log/`); its pass/fail matched. Its extra H6 miss (N2) is a wrong date, "1 December 2026" for 31 December. Both engines missed P3 by one day,
as production does.

**What Loom lost on writing.** Two drafts that Halogen passed were flagged for figures not in the source. Both are
derived, not invented facts:

- plain_english: "roughly 60 words per second" and "about 7 words per second", converted from tokens per second with
  a ratio the source does not give.
- client_email: "doubles the outlay to EUR 7,360", twice the box price.

The house style says to use only the facts given, and the registered score is the grader's 4/7. The third flag
(book_passage) was shared by both arms.

## Predictions

| | prediction | verdict |
|---|---|---|
| P1 | LM 32K prefill >= 1.5x LC | HELD (2.69x) |
| P2 | LM 32K prefill within 15% of AMD's 1,196 | **FAILED** (979, 18% lower) |
| P3 | LM decode >= 1.1x LC | HELD (1.49x) |
| P4 | LM 32K prefill <= HS | **FAILED** (1.11x; HS spread 791-1,239) |
| P5 | LM decode <= 0.7x HS | **FAILED** (0.72x) |
| P6 | every suite LM >= HS - 1 | **FAILED** (writing 4 vs 6) |
| P7 | LM tool use >= HS - 1 and no leaks | **FAILED** (28 vs 33; 0 leaks) |
| P8 | no LM suite stops on a transport error after the amendments | HELD |

P4 and P5 failed in Loom's favour: I predicted it would be further behind Halogen than it was.

## Decision (the prereg's rule)

Loom is slower than Halogen on decode (0.72x) and 8K prefill (0.61x), so the second branch applies: **production stays on
Halogen.** P6 and P7 failed as well, so the third branch also applies: the losses are recorded per item above. The
owner chose to capture transcripts before deciding on a report to AMD. They show a behaviour difference, not a
defect, so no report is recommended; nothing has been sent.

The routing guide gains one line: AMD's 1.5x is measured against llama.cpp; on this box Loom roughly matches Halogen
on 32K prompts, trails it elsewhere, and on tool tasks asks clarifying questions where Halogen acts.

## Limits

- **One sample per item** (tool use: 3 runs per task). The noise rule needs a gap of 2 items; writing (2) and tool use
  (5) pass it, the others do not.
- **Different weights.** Halogen serves its own checkpoint; Loom serves unsloth's GGUF. LM vs HS is engine plus file.
  Only LM vs LC is engine-only, and that is speed only.
- **Template.** Loom renders the stock template; production uses the community one. HS ran stock to match. Loom
  cannot yet run the community template, so a production switch would also change the template.
- **A development build.** hrx-loom 0.2.0.dev0 from a CI artifact that expires 2026-11-22. A later build may differ.
- **Tool-use transcripts cover five tasks only** (the ones Loom lost), from an unscored re-run.

## Evidence files

Prereg `results/e163-prereg.md`. Score `results/e163/score.json` (`tools/score_e163.py`). Speed
`results/e163/raw/{LM,LC,HS}/speed.json`. Suites `results/e163/raw/{LM,HS}/*.json`, tool use also
`results/tool-use/E33-results-e160-{LM,HS}.json`. Smoke `results/e163/raw/LM-smoke.jsonl`. Window log
`results/e163/raw/window.log`. Proxy `tools/e163_model_proxy.py` (log `results/e163/raw/LM/proxy.log`). Install record
`results/e163/loom-install.json`. Inputs in `manifests/MANIFEST.md` (E163 section).
