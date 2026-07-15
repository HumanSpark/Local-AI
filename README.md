# Local AI for a Small Firm - the data

This repository is the complete data package behind **[Local AI for a Small Firm: What a 128 GB Mini-PC Can Actually Do](https://humanspark.ai/local-ai/)** - independent research into what a EUR 3,680 on-premises mini-PC (GMKtec EVO-X2, Ryzen AI Max+ 395, 128 GB unified memory) can do for a small professional practice.

**If you want the findings, read the report, not this repo.** The plain-English argument, the verdict, and the practical guidance live on the website:

- [The Report](https://humanspark.ai/local-ai/) - the argument and the verdict
- [In Practice](https://humanspark.ai/local-ai/in-practice/) - which model for which job, setup, media results
- [The Evidence](https://humanspark.ai/local-ai/evidence/) - every finding, method, and correction, rendered readably

This repository exists so that none of it has to be taken on trust. Every number published on those pages traces to a raw file here.

## How to verify a claim

1. Open `claims.yml`. Every published number is a claim with an id, a plain-English statement, its value, and the evidence file path(s) that back it.
2. Follow the path. Raw benchmark outputs are in `results/`, evaluation outputs in `results/eval-pilot/` and `results/real-quality/`, and the scripts that produced derived figures (such as the cost model) are in `tools/`.
3. Cross-check provenance. `MANIFEST.md` lists every model file used, with source repository, revision, byte size, and SHA256.

A build-time completeness check enforces that every file path cited in `FINDINGS.md`, `experiments.md`, or `claims.yml` exists in this package. A release cannot ship a citation it cannot back.

## What's here

- `claims.yml` - the claims registry: the contract between the published prose and this data
- `FINDINGS.md` - the findings register (F1 onward), including negative results and lessons
- `experiments.md` - pre-registrations and results; predictions were written down before each test ran, and the misses are published beside the hits
- `integrated-technical-results-v2.md` - the compiled technical results, including the corrections log
- `MANIFEST.md` - model provenance (source, revision, size, SHA256 for every model file)
- `PHASE-A-LOG.md` - the dated execution log, kept as written
- `results/` - raw benchmark, evaluation, tool-use, and fine-tune outputs
- `eval-suites/` - the evaluation suite definitions and data
- `tools/` - scripts referenced by published claims
- `RELEASE-NOTES.md` - what changed in each release
- `docs/` - working design documents cited by the findings, published as-is for completeness

## Method in one paragraph

Single machine, single continuous run, 3-14 July 2026, data frozen 2026-07-14. Models served with llama.cpp (Vulkan and ROCm backends). Quality evaluation used deterministic fact-checkable suites plus a send-readiness assessment of realistic professional drafting tasks, graded by an independent judge model so no model family marks its own homework. Where a re-check showed a test itself was at fault, the correction is documented in the open rather than silently fixed. Full method detail: [the Evidence page](https://humanspark.ai/local-ai/evidence/).

## Versioning

Releases are tagged and frozen. Release 4.0 restructures the published reporting into three pages; the underlying data is unchanged from Release 3.1 and remains frozen at 2026-07-14. If a future measurement changes a claim, the claim is updated in `claims.yml` with its status field, the change is listed in `RELEASE-NOTES.md`, and the old value stays in the history.

## Licence and attribution

Data, findings, and documents: CC BY 4.0. Scripts in `tools/`: MIT. Reuse freely with attribution to Alastair McDermott / HumanSpark and a link to [humanspark.ai/local-ai](https://humanspark.ai/local-ai/).

## About

Research by [Alastair McDermott](https://humanspark.ai/), HumanSpark - AI adoption for expertise-heavy businesses. The benchmarking was run by an AI research assistant on the box itself; the analysis and writing were produced by Alastair working with Claude - [how this was made](https://humanspark.ai/local-ai/evidence/#how-this-was-made).

Questions about the research, or about what a machine like this could do in your practice: [humanspark.ai/call](https://humanspark.ai/call).
