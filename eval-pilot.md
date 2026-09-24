# File: eval-pilot.md
# Purpose: Results matrix and prediction resolutions for the promptfoo eval pilot (spec: docs/plans/2026-07-04-eval-pilot.md).
# Project: sparkbench | Date: 2026-07-04
#
# Overview: First quality data for the instant-tier models - 17 tests
# (4 task types x short/long context), deterministic grading,
# temperature 0, llama-server lifecycle per model. Raw promptfoo JSONs
# + server logs in results/eval-pilot/. All servers reaped (ALL-CLEAN).

## Results matrix

| Model | Raw pass | Corrected* | Real failures | Wall time |
|---|---|---|---|---|
| gpt-oss-20b | 17/17 | 17/17 | none | 1m24s |
| Qwen3-Coder-30B | 17/17 | 17/17 | none | 1m27s |
| GLM-4.7-Flash | 17/17 | 17/17 | none | **7m13s** |
| Qwen3-30B-A3B | 16/17 | **17/17** | none (grader artifact) | 1m26s |
| Qwen3-4B-2507 | 14/17 | **15/17** | spam-triage x2 | 1m17s |

*Grader artifact: `extract-short-total` asserted the comma-formatted
"8,388.60"; two models answered the numerically-identical "8388.60".
Assertion bug, not model failure - EVAL-DESIGN LESSON: assert on
normalized values, or accept both formats. Fixed in the suite for
future runs (both formats now documented as acceptable).

## The one real capability failure

Qwen3-4B classified BOTH spam emails as "urgent" (prize scam and
crypto scam). Business shape: a 4B email triager pages you for
scams - urgency-bias in small models is exactly the failure mode a
triage deployment must test for. Every 20B+ model got all six
triage cases right.

## Prediction resolutions (registered in the spec before runs)

- **P1 (every model >=80% on short variants):** HOLDS after grader
  correction (worst: Qwen3-4B 10/12 = 83%); on raw grading the 4B
  lands 75% - the margin is entirely the grader artifact. Recorded
  both ways.
- **P2 (long-extraction separates the field): MISS - nobody failed
  ANY long variant.** Needle-retrieval from 12K tokens of real bench
  log is below the capability floor of even the 4B. Good news for
  clients (12K-context extraction is safe across the fleet); the
  separating eval needs harder long-context tasks (multi-hop,
  cross-reference, contradiction-finding) - noted for the suite's
  next iteration.
  **CORRECTION 2026-08-12: the substrate is not 12K tokens.** Measured
  from the tokenizer via the serverlogs, `data/long-log.txt` is 16,140
  tokens for the Qwen family and ~14,900 for GLM/gpt-oss - up to 34%
  over the figure quoted here, which was a chars/4 estimate. The
  direction of P2's verdict is unchanged (nobody failed a long
  variant) but its stated premise is wrong, and any claim of the form
  "12K-context extraction is safe" understates what was actually
  demonstrated. See F20.
- **P3 (4B shows the largest drop): PARTIAL** - it is the only model
  with real failures, but they are SHORT-context judgment failures
  (spam), not the predicted long-context failures. The small-model
  tax is judgment, not context reach.
- **P4 (Flash quality vs its audition case):** 17/17 - the strongest
  pilot-level support possible for the Phase A "quality + MIT
  licence" case. The cost is now measured elsewhere: 7m13s wall vs
  ~1m25s for every other model (the F8 prefill collapse on 12K
  prompts, in a real workload), plus F18's anti-scaling. Flash's
  niche on this box: high-quality SINGLE-USER assistant on short-to-
  medium context.

## Consulting-ready statements this pilot supports

> **Delivery status was never checked when these were written (noted 2026-08-12).** Of the 136
> stored answers behind the 17-test matrix, **24 stopped exactly on the 600-token `max_tokens`
> ceiling** and 36 more cannot be attributed to a request from the serverlog at all. None of the
> statements below has been contradicted, and the pass/fail matrix above is unchanged - but a
> pass on a ceiling-stopped answer establishes less than it appears to, which is exactly the
> defect that made `glm-4.7-flash` a recorded PASS on E10 with no table.
> Per-suite figures: `python3 spikes/eval-pilot/audit_ceiling.py`. Mechanism: F20.

- "Every model 20B+ we tested passed 100% of a mixed short/long task
  suite; the 4B passed everything except spam judgment."
- "12K-token document extraction is reliable across the whole fleet,
  including the 2.3GB model."
- "The quality question between the workhorse and GLM-Flash is a tie
  on this suite - the throughput and concurrency data (8.5x, F18)
  make the deployment decision instead."
- Machinery: the suite is reusable (spikes/eval-pilot/), runs 5
  models unattended in ~13 minutes, and grades deterministically.
