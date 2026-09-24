# Merging the suggested R&D programme into sparkbench's actual queue

# File: docs/2026-08-31-rd-programme-merge.md
# Purpose: Reconcile the 2026-08-31 suggested R&D programme with work already done and already queued.
# Project: sparkbench | Date: 2026-08-31
#
# Overview: The suggested programme carries 23 hypotheses across two tracks.
# Roughly a third of them describe things this repo already did, several are
# genuinely new and earn a place, and three belong to other projects or are
# blocked by platform reality. This page sorts them so nothing is planned twice
# and nothing good is lost. It is a reconciliation, not a replacement: the
# programme's own framing (Track A workload, Track B measurement) is adopted.

## 1. Already true - fold in as evidence, do not re-plan

These are not proposals here. They are findings or rules that exist, and the
merged programme should CITE them rather than schedule them.

| suggested | status in this repo |
|---|---|
| **B1** invalid states explicit (`truncated != wrong`) | **HARNESS-RULES Rule 13**, written 2026-08-31, gated in `run_ps_eval.py` and `run_coding_eval.py`, exit 3 with `--allow-truncation` as the declared override |
| **B3** positive controls | standing principle since E89 ("a control that cannot fail is not a control"); the `pr1` bank was validated this way today against five synthetic respondents |
| **B4** ruler models | **F117**. Both incumbents reproduced their *item-level* answers on a new build - the workhorse's `30 October 2026` and `107.56`, the 27B's N2 at `1 December 2026` |
| **B5** class generalisation is unsafe | **F118**. F80 restated as a fact about Qwen3-30B-A3B rather than about ~3B-active MoEs |
| **B10** configuration is the treatment | **HARNESS-RULES Rule 8** already says a benchmark measures a CONFIG. Kwaipilot `thinking off` is already registered as its own arm, not a repair |
| **A5** inventory-first | done 2026-08-31; the audit found Nemotron, which produced the day's best result |
| **A7** reasoning configuration | already registered (F119's closing note) |
| **B12** stopping rules | pre-registration has been mandatory here since E1; every `*-prereg.md` names falsifiers |

**The corpus in section 5 also largely exists**: registrations in
`results/*-prereg.md`, banks in `spikes/ps-eval/`, manifests in
`manifests/MANIFEST.md`, raw outputs in `results/raw/`, rules in
`docs/HARNESS-RULES.md`, findings in `docs/FINDINGS.md`. **Two pieces are
genuinely missing and are adopted below: a unified failure ontology, and
production outcomes.**

## 2. Adopted - merged into the existing queue

### Already pre-registered, unchanged by this merge

- **E93** (abliteration and abstention) satisfies most of **A4**. Its `pr1` bank
  already scores `missed_flag` and `over_flag` separately, which is A4's
  "unsupported-answer rate must never hide inside aggregate accuracy". Model is
  downloading.
- **E94** (three-model residency) is **A3**'s infrastructure half. A3's routing
  arm cannot run until E94 says whether three models can co-reside.

### Folded into E94 as additions

- **B6 matched-effort.** E94 H5 already re-runs Nemotron at matched effort. The
  programme's sharper contribution is the **scientific vs operational
  comparison** distinction - matched settings answer "which model is better",
  best-known-config answers "what should we deploy". **Adopted as a standing
  convention**: every prereg from here states which of the two it is running.
- **A2 opportunity cost.** E94 already measures memory occupancy and what
  remains possible with three models resident. Adding A2's *"time until SparkMax
  is again available"* costs nothing and is adopted.

### New experiments earned, in priority order

- **E95 - the patient-worker question (A1 + A2).** The programme is right that
  this is the most strategically important new work, and it is the same question
  both of today's reports flagged as possibly-wrong framing. **It needs a build**
  - an overnight queue runner and an acceptance-scoring rubric - so it is a
  project, not a window. See the open question below.
- **E96 - a harder cross-document tier (B7).** l3 at 9 distractors is saturated:
  three capable arms at 12/12 (F117 corollary). Contradictory documents and
  longer dependency chains are the two variants most likely to discriminate.
  Cheap, because the corpus generator already exists.
- **E97 - fault injection (B2).** Deliberately inject truncation, malformed
  response, empty response, missing output file, server interruption and scorer
  exception; assert the harness goes red. Rule 13 was written from one real
  case; this proves the class. Cheapest experiment on this list and it protects
  every later one.
- **B8 - public benchmark vs private bank correlation.** Not a separate
  experiment: a **column added to results** recording each model's public
  ranking where one exists, so the correlation accumulates. Kwaipilot is the
  motivating case (top of a public code subset, does not terminate here).
- **A6 coding completion / A11 quantisation.** Both real, both deferred behind
  the Kwaipilot `thinking off` arm, which is cheaper and answers whether the
  coding bank can measure that model at all.

### Adopted as method, not as experiments

- **B9 multi-dimensional suitability**, with its own discipline attached: *if a
  metric never changes a decision, stop collecting it.*
- **B11 inventory states.** Adopt the vocabulary
  `known / downloaded / verified / benchmarked / production-qualified /
  production-routed` in `manifests/MANIFEST.md`. Today's audit had to derive
  this by hand across three files.
- **The failure ontology**, unified across tiers rather than per-tier as now.
- **Scope tags on findings** (`run / configuration / model / family /
  architecture / general`), with the rule that moving outward one level needs
  new independent evidence. F118 is the worked example of the failure.
- **Decision gates**, including the fourth state: `NO DECISION - MEASUREMENT
  INVALID`. E92's H2 and H3 are already in exactly that state.

## 3. Not adopted here - and why

- **A8 staged OCR pipeline.** This is an application architecture, not a
  benchmark: PaddleOCR, a classifier, a routing layer. sparkbench measures; it
  does not host new pipelines. It also introduces a new dependency stack. Route
  to a golden-path project if it is wanted.
- **A9 background speech pipeline.** **sparkbench closed speech work on
  2026-07-29** and transferred its obligations to sparksynth; CLAUDE.md says
  narration is closed here in terms. Re-opening ASR in this repo would reverse a
  deliberate closure. Route to sparksynth / meeting-stt.
- **A10 NPU utility models.** Blocked by platform reality rather than by
  preference: AMD's own documentation states NPU and hybrid inference are
  supported on **Windows only**, with Linux NPU access via FastFlowLM alone.
  This fleet runs Linux. Worth a one-line re-check when that changes; not
  plannable now.

## 4. The guardrail is load-bearing and stays first

The suggested programme's own section 9 - *better benchmarking can become work
that produces no business value* - is the reason this repo was PARKED on
2026-08-30, one day before it reopened. That is not a hypothetical risk here; it
is the documented history.

**So the sequencing is deliberately smaller than the programme proposes.** 23
hypotheses is more than this box can run in windows of 45-75 minutes without
becoming the hobby the guardrail warns about. The merged queue is:

1. **E93** (running-ready), then the Nemotron and Kwaipilot follow-ups already
   earned - these close questions existing evidence has already paid for.
2. **E97** fault injection, because it is cheap and protects everything after.
3. **E94** three-model residency, which unlocks A3.
4. **E96** a harder cross-document tier, because l3 can no longer discriminate.
5. **E95** patient-worker, if and only if the build is authorised.

Everything else waits for one of those to produce a reason.
