# File: envelope-worked-example.md
# Purpose: The E30 worked example - three solicitor-shaped questions against a ~46K-token document bundle at the measured usable limit.
# Project: sparkbench | Date: 2026-07-11
#
# Overview: Bundle = the four manifest-verified synthetic solicitor fixtures
# (engagement letter, case notes, attendance source, supply agreement)
# interleaved with background-paper filler to 21,046 words (~46K real-token
# class; served at -c 50176 on the Qwen3-30B workhorse, Vulkan, NP=1).
# Ground truth = the fixture fact manifests. Raw answers:
# e30-worked-example-raw.json; server log: e30-worked-example.serverlog.

| # | Question | Answer (verbatim) | Time | Grade |
|---|---|---|---|---|
| 1 | Initial term end date as finally agreed (supply agreement) | "31st March 2027" | 2m 38s (includes full bundle ingest) | CORRECT - and the supersession trap avoided (not the struck 30 June 2027) |
| 2 | Encroachment distance + surveyors (case notes) | "0.8 metres... Donnelly Surveyors", citing the FACTS section | 4.0s | CORRECT, grounded |
| 3 | Cross-document: engagement-letter fixed fee AND case-notes legal costs | "EUR 2,850... EUR 6,500" | 2.0s | CORRECT - a two-document join |

The timing pattern is the deployment story: one ~2.6-minute ingest of the
whole bundle, then seconds per question against the cached context. 3/3
correct, informally graded against the fixture manifests; n=3 - a
demonstration at the measured limit, not a statistic.
