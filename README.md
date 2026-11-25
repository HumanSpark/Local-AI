# Local AI for a Small Firm - the research record

I'm Alastair McDermott. I help professional firms adopt AI, and since July 2026 I've
been testing what a EUR 3,680 mini-PC can do on the work those firms do. I also use it
in my own work: it transcribes my calls, narrates my articles, runs a nightly memory
job for my assistant and can run my coding agents overnight. Those production
workflows run entirely on the machine. The research also uses cloud models, as
comparisons and as judges, and each results file says which.
This repository is the full record: every test, result, correction and the evidence
I can't publish. The plain-English version is at
[humanspark.ai/local-ai](https://humanspark.ai/local-ai/).

**If a colleague sent you here:** start with what production runs now, then check one
number yourself (five minutes, Python only).

**What works best right now, for each kind of job** (text, coding, office tools, speech, voice, images, music, memory)
and for engines: [capabilities/](capabilities/README.md). How it compares with frontier models: [FRONTIER.md](FRONTIER.md).

> [!NOTE]
> **The machine:** GMKtec EVO-X2 · AMD Ryzen AI Max+ 395 with Radeon 8060S · 128 GB
> unified memory (about 105 GB usable by the graphics) · 81-87 W while generating
> ([F180](FINDINGS.md#f180)) · measured July to 25 November 2026.

### What production runs now

| Job | Engine | Model or voice | In service since | Why (evidence) |
|---|---|---|---|---|
| Language model | Halogen 0.18.23 | Qwen3.8-Flash-Next, community template, effort `low` | 13 Nov 2026 | Same 8/10 as maximum effort at 5.8 vs 19.1 min per fix; matched it on most of eight everyday work types ([Settings comparison, E159](results/e159-results.md), [Production acceptance, E160](results/e160-results.md)) |
| Speech to text | whisper.cpp | Whisper large-v3-turbo + Silero VAD + host-versus-other tagging | 18 Jul 2026 | ([F44](FINDINGS.md#f44), [F45](FINDINGS.md#f45), [F46](FINDINGS.md#f46)) |
| Text to speech | Chatterbox | Cloned British voice; Kokoro fallback | 1 Aug 2026 | ([F56](FINDINGS.md#f56), [VOICES.md](VOICES.md)) |

## What changed recently

- **25 Nov 2026 - Claude on the ten large changes.** Claude Sonnet 5.5, Opus 5.5 and Fable 5.2 each solved all ten,
  at a median 3.3 to 7.1 min a change; production solves five at 11.4 min. Large, multi-step changes are frontier work
  ([Claude on the large changes, E178](results/e178-results.md), [F204](FINDINGS.md#f204),
  [how it compares](FRONTIER.md)).
- **24 Nov 2026 - two challengers; production kept.** Flash-Next compressed with the community HTR method, on its own
  vLLM build: 6/10 on ten large changes against production's 5/10, but slower (47.8 against 62.5 tok/s writing, 924
  against 1,462 tok/s reading a 32K prompt) ([HTR against Halogen, E177](results/e177-results.md), [F202](FINDINGS.md#f202)).
  Ling-3.2-air: 0/10 on the same changes, despite writing 37% faster than Flash-Next on llama.cpp; its results on the
  two easier coding banks are being measured ([Ling-3.2-air, E176](results/e176-results.md), [F203](FINDINGS.md#f203)).
- **22 Nov 2026 - a large challenger too slow for the budget.** Hy4-Flash (220B) on the Strata engine: about 24 tok/s,
  3/10 against production's 5/10, every task at its one-hour limit ([Hy4-Flash, E171](results/e171-results.md),
  [F197](FINDINGS.md#f197)).
- **21 Nov 2026 - the nightly memory job stays on production.** Fifty memory-keeping jobs with traps: production made
  1 mistake; Inkling-2-Mini none, but 6.5 times slower with no answer on 5 of 20 updates; Hy-Memory kept suggestions
  the person had turned down ([Memory extraction, E170](results/e170-results.md), [F196](FINDINGS.md#f196)).
- **19 Nov 2026 - tests hidden.** The same ten large changes without the tests in view: both local setups solved 1/10
  ([Hidden tests, E168](results/e168-results.md), [F195](FINDINGS.md#f195)).
- **18 Nov 2026 - where local falls short.** Ten large real changes: GPT-6.1 Sol 10/10 (about 2 min each, USD 1.95 in
  total), production 5/10 (about 11 min each) ([Large changes, E167](results/e167-results.md), [F194](FINDINGS.md#f194)).

## Current release: r6.0 (findings through 25 November 2026)

r6.0 adds [how it compares with frontier models](FRONTIER.md), with quality and speed kept apart, and the Claude results on the ten large coding changes: Claude Sonnet 5.5, Opus 5.5 and Fable 5.2 each solved all ten, where production solves five ([F204](FINDINGS.md#f204)). Each [capability page](capabilities/README.md) now says in one line how it compares with the frontier.

- **Every claim carries a status and dates.** 26 current, 17 qualified, 18 historical and 3 superseded: the 24 November review plus three frontier comparisons added on 25 November; [claims.md](claims.md) lists each, and [GLOSSARY.md](GLOSSARY.md#claim-status) explains the terms.
- **Not everything is here.** Verbose server logs, internal design documents and files with private content are withheld, among them the per-task records of the coding tests, which quote private repositories. [WITHHELD.md](WITHHELD.md) lists each with the reason.

## Five research tracks

Every experiment belongs to one track. Each track page lists that track's claims with their status, dates and
evidence; the experiment-by-experiment write-ups (why each was run, what would have changed the plan, what happened
and what I decided) are being added track by track.

| Track | The question | Why this kind of test | Current answer (date) |
|---|---|---|---|
| [Documents](tracks/documents.md) | Can it work from what you give it? | Supplied sources make answers checkable | 25/26 on a document pack; the miss was an invented figure (17 Nov) |
| [Drafting](tracks/drafting.md) | Would a professional send it? | Blind pairwise judging of client-style briefs | GPT-6.1 Sol clearly ahead; local losses are unsupported promises and omissions (15 Nov) |
| [Meetings](tracks/meetings.md) | Can it make a private call into a record? | Real calls, line-level scoring | 97.2% host-vs-other lines on 4 calls; transcription about 28x real time on a clean clip (Jul) |
| [Unattended work](tracks/unattended-work.md) | Can it finish a long job alone? | Coding, because project tests decide pass/fail | 15/15 for the best local setups and Claude on the first 15 fixes; 5/10 vs 10/10 for GPT-6.1 Sol on ten larger changes; 1/10 with tests hidden (5-19 Nov) |
| [Running it](tracks/running-it.md) | Speed, capacity, cost, stability | Engines, concurrency, power, stress | Halogen: 86 tok/s writing code and 18.7 s to first token at 32K in the 4 Nov engine comparison; 62.5 tok/s and 22.4 s timed live on 24 Nov ([what changed between them](tracks/running-it.md#two-speed-measurements)); concurrency only measured on the July engine |

The coding chart and the five-engine speed table are in the Unattended work and Running it pages, each with the
harder result beside the attractive one.

## Check one number yourself

The drafting comparison (E162), as published in release r5.18. Python 3 only, no
other installs, a few seconds.

    git clone https://github.com/HumanSpark/Local-AI && cd Local-AI
    git checkout r5.18
    python3 tools/score_e162.py
    git diff --exit-code results/e162/score.json && echo "score.json reproduced"

The scorer rewrites `results/e162/score.json` from the saved judge decisions, so the
`git diff` compares what you just produced with the committed result. Expected: the
script prints a line beginning `agreement {'identical': 67, 'of': 100` (the two judges
agreed on 67 of 100 comparisons), and the last command prints `score.json
reproduced`. What that proves: the published drafting scores follow from the saved
judgements. What it doesn't: a new model run, or a human view of draft quality.
(Checked 2026-11-25 in a clean clone at tag r5.18.)

## What you can check, and what you can't

| Access | Meaning | Examples |
|---|---|---|
| Inspect | The outputs are here to read | Drafts, transcripts, scored answers |
| Recalculate | Scores rebuild from saved records | E162 drafting scores, the cost model |
| Rerun | Inputs are public; a new run is possible | Public benchmark suites |
| Private | Summaries only, with the reason | Coding tasks from private projects ([WITHHELD.md](WITHHELD.md)) |

## Planning your own pilot

What this record can't tell you about your firm, and what to measure: how many people
ask at the same moment and with what size of document; acceptable queue time; your
task mix; review time per approved output; the data path end to end.

## Navigating the record

[By capability](capabilities/README.md) · [Engines](capabilities/engines.md) · [Against the frontier](FRONTIER.md) · [Glossary](GLOSSARY.md) (every code and model name) · [Findings register](FINDINGS.md) ·
[Experiments index](results/README.md) · [Claims](claims.md) ([claims.json](claims.json)) ·
[Release history](RELEASE-NOTES.md) · [Licence](LICENSE) and [citation](CITATION.cff)
