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

**What works best right now, for each kind of job** (documents and writing, office tools, transcription, notes and memory,
voice, images, music, coding) and for engines: [capabilities/](capabilities/README.md). How it compares with frontier models: [FRONTIER.md](FRONTIER.md).

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

## What it does well, where it falls short, what I'd do

**What it does well now:** working from your own documents. Transcribing calls. Keeping an assistant's notes up to
date overnight. Everyday coding fixes. It costs nothing per use, and nothing leaves the building.

**Where it falls short:** client-ready drafts. The local model adds promises the notes don't support. Large,
multi-step software changes: it finishes about half, where frontier models finish all of them.

**What I'd do:** run routine and confidential work locally. Send client-facing drafts and big changes to a frontier
model, or have a person check them.

[How it compares with frontier models](FRONTIER.md) · [What works best for each job](capabilities/README.md) ·
[What changed in each release](RELEASE-NOTES.md)

## Current release: r6.2 (findings through 25 November 2026)

r6.2 adds [energy per answer](results/energy-per-answer.md), measured at the wall and compared with a fridge-freezer, the final Ling-3.2-air coding results, the newer HTR release, and a card for each engine with a project link. No earlier result changed.

- **Every claim carries a status and dates.** 26 current, 17 qualified, 18 historical and 3 superseded; [claims.md](claims.md) lists each, and [GLOSSARY.md](GLOSSARY.md#claim-status) explains the terms.
- **Not everything is here.** Verbose server logs, internal design documents and files with private content are withheld, among them the per-task records of the coding tests, which quote private repositories. [WITHHELD.md](WITHHELD.md) lists each with the reason.

## The five kinds of work I tested

Every test belongs to one of five tracks, ordered here by how much a firm leans on them.

| Track | The question | Where it stands |
|---|---|---|
| [Documents](tracks/documents.md) | Can it work from what you give it? | Yes. 25 of 26 answers right on a large document pack. The one miss was a figure the documents never state. |
| [Meetings](tracks/meetings.md) | Can it turn a private call into a record? | Yes, for transcripts. It tells the host from the other speakers on 97% of lines. It transcribes about 28 times faster than real time. |
| [Drafting](tracks/drafting.md) | Would a professional send it? | Not yet. Frontier models write better client drafts. A local draft needs a person to check every promise and figure. |
| [Running it](tracks/running-it.md) | Speed, capacity, cost, stability | It writes about 62 tokens a second. A token is roughly three-quarters of a word. It starts answering a long document in about 22s, on one machine at about 85 W. |
| [Unattended work](tracks/unattended-work.md) | Can it finish a long job alone? | Everyday coding fixes, yes, but slowly. Large changes, about half. Frontier models finish all of them. |

Each track page lists its claims with their evidence. The engine speed table is on the Running it page and the
coding chart on the Unattended work page.

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
