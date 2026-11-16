# Release Notes - sparkbench-data-r5.10

Data package for the Local AI resource. sparkbench ships evidence, findings, and the claims registry;
reader-facing prose is the owner's and webby renders it (sparkbench docs/REPORT-STANDARD.md).

## This release (r5.10)

- **Findings:** 190 in FINDINGS.md, newest F190.
- **Claims:** 60 active in claims.yml.
- **New finding F190 (E163): AMD's agent-ported HRX Loom engine beats llama.cpp, but not production Halogen.**
  AMD announced on 2026-11-13 that coding agents ported 51 models, including our production Flash-Next, to its new
  Loom engine in four days. We ran Loom (dev build 0.2.0.dev0), upstream llama.cpp `9fba51d` on the same GGUF, and
  production's Halogen engine, all timed by one client.
  - Against llama.cpp the claim holds: 2.69x on 32K-token prefill (979 against 364 tok/s), 1.49x on decode.
  - Against Halogen it does not: about level on 32K prefill (979 against 879, Halogen's runs spread 791 to 1,239),
    0.61x at 8K and 0.72x on decode.
  - On the E160 suites at effort low, Loom matched Halogen on document Q&A, refuse/comply, kw-eval and conversation,
    and fell behind on writing (4 against 6 of 7, derived figures) and tool use (28 against 33 of 36). On conditional
    tool tasks it looked the client up and then stopped.
  - The prereg rule: production stays on Halogen.
- **Two transport amendments are disclosed.** Loom rejects requests with no or an unknown `model` and serves
  `/healthz` rather than `/health`, so the suites reached it through a small proxy that fixed only those. One suite
  (L5) sent no item before the second fix and was re-run whole.
- New evidence: `results/e163-prereg.md`, `results/e163-results.md`, `results/e163/score.json`, the three arms'
  `speed.json` files and the suite results.

## Changed claims (old -> new)

- (none.)

## Retracted claims

- (none.)

## Completeness

Every path cited by FINDINGS.md, experiments.md, claims.yml, and the results/ evidence documents exists
in this package - the build fails otherwise. Internal plans and briefs are excluded from that rule: they
record intent, not evidence, and legitimately reference runs that were proposed and never produced.

Exception, declared: the paths listed in WITHHELD.md are cited but not shipped, each with its
reason (internal design documents; files the source repository keeps out of git).
