# Local AI for a Small Firm - the data

This repository is the data package behind **[Local AI for a Small Firm: What a 128 GB Mini-PC Can Actually Do](https://humanspark.ai/local-ai/)** - independent research into what a EUR 3,680 on-premises mini-PC (GMKtec EVO-X2, Ryzen AI Max+ 395, 128 GB unified memory) can do for a small professional practice.

**If you want the findings, read the report, not this repo.** The plain-English argument, the verdict, and the practical guidance live on the website:

- [The Report](https://humanspark.ai/local-ai/) - the argument and the verdict
- [In Practice](https://humanspark.ai/local-ai/in-practice/) - which model for which job, setup, media results
- [The Evidence](https://humanspark.ai/local-ai/evidence/) - every finding, method, and correction, rendered readably

This repository exists so that the numbers on those pages do not have to be taken on trust. Start with the current release below, and read [WITHHELD.md](WITHHELD.md) for what is deliberately not here.

## Current release: r5.1 (findings through 26 September 2026)

r5.1 adds ten findings (F167 to F172 and F175 to F178) and five claims from testing published speed claims on the box - Bonsai, Halogen, Atlas and the models a chat and a comparison widget recommended - to the r5.0 release of 24 September 2026, which caught this repository up with findings F47 to F166. All are in [FINDINGS.md](FINDINGS.md), with the evidence behind them. The subjects range from text-to-speech engines on this GPU, through reasoning effort, tool use and agentic coding, to tests of published speed claims (a "73 tok/s" Bonsai figure that does not reproduce; Halogen's 32K prefill claim, which measures 81% of the published figure). [RELEASE-NOTES.md](RELEASE-NOTES.md) groups them by subject, lists the retractions and amendments, and says which published claims are under review.

Two things to know before relying on it:

- **The older claims have not been re-reviewed.** `claims.yml` gained five claims in r5.1 for the September tests (Bonsai speed, Halogen prefill, Atlas MLPerf latency, Atlas determinism, the recommended coding models); the 45 claims before them are unchanged since r4.6, and the header still reads release 4.0 and data freeze 2026-07-17, because those were last checked against the data on that date. Later findings bear on some of them (the long-context and ROCm-versus-Vulkan claims, the local reasoning-model claim, the tool-use claims). RELEASE-NOTES.md names each and the findings that bear on it. None is withdrawn here; none has been re-verified.
- **Not everything is here.** Verbose server logs, internal design documents, and two sets of files that contain private content are withheld, and four cited files do not exist anywhere. [WITHHELD.md](WITHHELD.md) lists every one with the reason.

## How to verify a claim

1. Open `claims.yml`. Every published number is a claim with an id, a plain-English statement, its value, and the evidence file path(s) that back it.
2. Follow the path. Raw benchmark outputs are in `results/`, evaluation outputs in `results/eval-pilot/` and `results/real-quality/`, text-to-speech evidence in `tts-bench/`, and the scripts that produced derived figures (such as the cost model) are in `tools/`.
3. Cross-check provenance. `MANIFEST.md` lists every model file used, with source repository, revision, byte size, and SHA256.

A build-time completeness check enforces that every file path cited in `FINDINGS.md`, `experiments.md`, `claims.yml`, or an evidence document under `results/` either exists in this package or is listed in `WITHHELD.md` with a reason. A release cannot ship a citation it cannot account for.

## What's here

- `claims.yml` - the claims registry: the contract between the published prose and this data
- `FINDINGS.md` - the findings register (F1 onward), including negative results, retractions and lessons
- `experiments.md` - pre-registrations and results; predictions were written down before each test ran, and the misses are published beside the hits
- `integrated-technical-results-v2.md` - the compiled technical results, including the corrections log
- `MANIFEST.md` - model provenance (source, revision, size, SHA256 for every model file)
- `PHASE-A-LOG.md` - the dated execution log, kept as written
- `results/` - benchmark, evaluation, tool-use, coding, and fine-tune outputs, including the pre-registration and results document for each experiment
- `tts-bench/` - the text-to-speech engine evidence
- `eval-suites/` - the evaluation suite definitions and data
- `tools/` - scripts referenced by published claims and findings
- `docs/` - design and measurement documents cited by the findings
- `RELEASE-NOTES.md` - what changed in each release
- `WITHHELD.md` - what is cited but not shipped, and why

## Method in one paragraph

Single machine, run from July to September 2026; the findings register in this release is current to 2026-09-24. Models served mainly with llama.cpp (Vulkan and ROCm backends), with other engines named in the findings that used them. Quality evaluation used deterministic fact-checkable suites plus a send-readiness assessment of realistic professional drafting tasks, graded by an independent judge model so no model family marks its own homework. Where a re-check showed a test itself was at fault, the correction is documented in the open rather than silently fixed, and predictions were written down before the runs that test them. Full method detail: [the Evidence page](https://humanspark.ai/local-ai/evidence/).

## Versioning

Releases are tagged and frozen. If a future measurement changes a claim, the claim is updated in `claims.yml` with its status field, the change is listed in `RELEASE-NOTES.md`, and the old value stays in the history.

## Licence and attribution

Data, findings, and documents: CC BY 4.0. Scripts in `tools/`: MIT. Reuse freely with attribution to Alastair McDermott / HumanSpark and a link to [humanspark.ai/local-ai](https://humanspark.ai/local-ai/).

## About

Research by [Alastair McDermott](https://humanspark.ai/), HumanSpark - AI adoption for expertise-heavy businesses. The benchmarking was run by an AI research assistant on the box itself; the analysis and writing were produced by Alastair working with Claude - [how this was made](https://humanspark.ai/local-ai/evidence/#how-this-was-made).

Questions about the research, or about what a machine like this could do in your practice: [humanspark.ai/call](https://humanspark.ai/call).
