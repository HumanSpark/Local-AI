# How it compares with frontier models

## In plain English

The big AI labs run their models on racks of data-centre accelerators, and their models are far larger than anything
that fits in this machine's 128 GB of memory. Anthropic does not publish the size of its models or the hardware they
run on, but the gap in scale is enormous. This record does not claim that one EUR 3,680 mini-PC drawing about 85 W
beats that.

The question here is narrower: for which kinds of work is a local model good enough, and what does it cost in time?

**Where local is good enough:** everyday and medium-sized coding fixes, where it matched Anthropic's models on whether
the job got done. It is slower, roughly 4 to 15 times per task, so it suits work nobody is waiting for.

**Where frontier models are clearly better:** client drafting, where the local model adds promises the notes don't
support or leaves out what the reader needs, and large, multi-step software changes, where Anthropic's models finished
all ten and the local model five.

**What I'd do:** keep routine and confidential work on the box, especially overnight batches and first drafts a person
checks; send client-facing drafts and big changes to a frontier model.

## Side by side

Anthropic's models are the main comparison; OpenAI's GPT-6.1 Sol is shown where it was the only frontier model run.
Local means production: Qwen3.8-Flash-Next on Halogen.

| Work | Local result | Frontier result | Local time per task | Frontier time per task | Cloud cost | What we'd do | Evidence |
|---|---|---|---|---|---|---|---|
| 10 client drafting jobs, judged blind (15 Nov 2026) | behind | Claude Sonnet 5.5 beat the everyday setting; judges split at higher settings. GPT-6.1 Sol clearly ahead. | - | - | - | frontier, or check every promise and figure | [results/e162-results.md](results/e162-results.md) |
| 15 everyday real fixes (5 Nov 2026) | 15/15 | Claude Sonnet 5.5: 15/15 | 9.9 min (the setting before 13 Nov) | 40s | USD 1.23 for all 15 | good enough locally | [results/e154-results.md](results/e154-results.md) |
| 10 bigger fixes (6 Nov 2026) | 9/10 (8/10 at the everyday setting) | Claude Sonnet 5.5: 8/10; Claude Opus 5.5: 8/10 | 21.3 min (5.8 at the everyday setting) | 2.5 min; 5.3 min | USD 2.82; USD 7.75 | good enough locally | [results/e156-results.md](results/e156-results.md) |
| 10 large changes, tests visible (18 and 25 Nov 2026) | 5/10 | Claude Sonnet 5.5, Opus 5.5 and Fable 5.2: 10/10 each; GPT-6.1 Sol: 10/10 | 11.4 min | 3.3, 6.8 and 7.1 min; 2.1 min | GPT-6.1 Sol USD 1.95; the Claude runs used a Claude Code subscription | frontier work | [results/e178-results.md](results/e178-results.md) |

## Limits

One attempt per task, so a difference of one task is within noise. Cloud times include no queueing and cloud costs are
API list prices on the day. The hard-bank runs of Anthropic's models were made as Claude Code subagents: the same tasks
and grading, but Claude Code's own tools instead of our test harness (see the experiment record). Knowledge-work test
banks no longer separate strong models (F153), so they are not used for this comparison.
