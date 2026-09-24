# File: docs/DEFERRED-REGISTER.md
# Purpose: Every piece of registered sparkbench work that was NOT run, why, what would justify running it, and which kind of question it is.
# Project: sparkbench | Date: 2026-08-20
#
# Overview: A registered experiment may be closed UNRUN/DEFERRED. Nothing here
# was run and abandoned; nothing here is a failure. Each entry names the
# uncertainty it would reduce, the reason it was not worth the GPU time or the
# risk at close-out, the condition that would reopen it, and its class -
# CAPABILITY, EFFICIENCY, RELIABILITY or INFRASTRUCTURE.
#
# THE PROGRAMME WAS CLOSED WITH THIS LIST NON-EMPTY, ON PURPOSE. Work was not
# run merely to empty it. Both headline questions are answered and none of the
# items below would change either answer; they would refine numbers whose
# decisions are already made.

**Status: sparkbench is DORMANT as of 2026-08-20.** Read `README.md` for what
wakes it and `docs/NEW-MODEL-INTAKE.md` for how to test a new model against the
frozen baseline. Nothing in this file is a queue to work through.


## 1. Extended coding suite - the remaining 10-15 C-H1 tasks

| | |
|---|---|
| **class** | CAPABILITY |
| **registered as** | E73's stopping rule, CONTINUE branch |
| **why not run** | The rule fired its **STOP** branch, not its CONTINUE branch. Spread in `completed_correct` across four very different arms was **0**, against a registered threshold of 2. Authoring ten more tasks of the same shape measures the same zero more precisely, and the registration says so in advance: *"the instrument does not separate four very different arms and rebuilding it is the work, not extending it."* |
| **what would justify it** | A new model completing **at least one** C-H1 task under `docs/NEW-MODEL-INTAKE.md` step 6. One completion turns a discrimination question back into a rate question, and only then do more tasks buy anything. |
| **what it would NOT change** | The 0% headline. Twenty cells with a 0.0-16.1% Wilson interval already rule out anything usable; more tasks narrow the ceiling, they do not move the decision. |

## 2. Knowledge-work bank expansion past 26 items

| | |
|---|---|
| **class** | CAPABILITY |
| **registered as** | E74's own caveat - *"the interval is wide - n=24"* |
| **why not run** | The 95% Wilson interval on 20/24 is 59.5-90.8%, roughly 31 points wide. Halving it needs roughly **four times** the items, so 24 items would have to become about 96 - each one requiring a gated ground-truth key derived from the real corpus. That is a multi-day authoring job whose output is a narrower interval around a number the routing decision does not depend on: the decision is "the workhorse serves the Think tier", and it survives anywhere in 59-91%. |
| **what would justify it** | A published claim that turns on the *precise* rate rather than its order of magnitude - a client engagement quoting a completion percentage, or a comparison between two models whose intervals overlap and whose ranking matters. |
| **cheaper alternative first** | Add items only in the categories where the bank is thin (`draft` and `summarise` have 2 each), rather than scaling uniformly. |

## 3. KA-H4 arm C - counting moved outside the model

| | |
|---|---|
| **class** | CAPABILITY |
| **registered as** | `docs/plans/2026-08-19-rd-programme-inference-as-resource-allocation.md`, with a prediction registered against it |
| **why not run** | **Its result was predicted and the prediction is the point.** F92 diagnosed gpt-oss-120b's date failure as `add_period(date="2020-09-14", years=6, days=1)` - a flawless answer to the wrong question. The error is in SELECTING the anchor and the period, not in counting them. Arm C moves the counting out of the model and leaves the selecting in, so it removes malformed calls (measured at **0-1 per cell**, i.e. almost none) and nothing else. The registered prediction is that arm C's `boundary` score lands within +/-2 of arm B's. Running it to confirm a null is the lowest-value GPU time in the programme. |
| **what would justify it** | A model whose AABR failures are **malformed calls** rather than wrong arguments. That inverts F92's diagnosis and makes arm C the discriminating arm rather than a confirmatory one. |
| **the registered prediction, preserved** | *Arm C's `boundary` is within +/-2 of arm B's for the same model. If arm C beats arm B by 3 or more, F92's diagnosis is wrong and THAT is the finding.* |

## 4. KA-H3 - context and KV cache reuse

| | |
|---|---|
| **class** | EFFICIENCY |
| **registered as** | H4 in the original programme, re-registered as KA-H3 with the same 25% threshold |
| **why not run** | It is an efficiency question and the programme ran out of *capability* questions first. It also has a measured competitor: F74's prefill effect and E60's MTP result already deliver 2x on documents and 1.3x on chat, banked and deployed. KV reuse would be additive to those, and the tier it helps - repeated queries over one unchanged pack - is **3.9% of measured relay traffic** (E58's mix: 869 of 952 requests are under 1,000 prompt tokens). |
| **what would justify it** | A real workload that re-queries one large unchanged context repeatedly - a document-review session, a long agent loop over one repository. E58's traffic mix says that workload does not exist here today; a new one would change that. |
| **threshold, preserved** | 25% reduction in time-to-answer on the repeated-context tier, or it is not worth the serving complexity. |

## 5. CLOSED 2026-08-28 - the `l` pack was RUN; gpt-oss on it is skipped permanently

**The `l` pack is no longer deferred.** E84 ran it on qwen38 at 71,739 prompt
tokens, `-c 131072`, GPU peak **28.71 GiB** - the >60 GiB regime was never
entered, because the arm chosen was the one with headroom rather than the one
with the biggest weights. That was this item's own stated cheaper route.

**Result: no capability degradation from context content.** With `-c` held at
131,072 across packs s/m/l, the same 11 questions score **9/11 at every size**,
spread 0, while **every answer is rewritten** at the `l` pack. KA-H2 closes, at a
resolution of 11 items - which bounds the loss at under roughly 2 of 11 and does
NOT license retiring the context-engineering hypotheses.

**⚠ OWNER DECISION 2026-08-28: gpt-oss-120b on the `l` pack is SKIPPED
PERMANENTLY.** Not pending, not blocked on a window. It would need roughly
**75 GiB** (about 59 GiB weights plus a ~16 GiB KV cache at 131K) against the
**~68 GiB** that deadlocked in F24 and reproduced in C1; it is not the production
model; and E83 put its coding record at 1 of 5, on the one task three arms pass.
Do not resurrect this from the original entry below.

E84 also found that the banked KA-H1 ladder was never a ladder - each pack was
asked only the questions it introduced - and fixed it with `--item-packs`.
Full entry: E84 in `results/experiments.md`.

### Original entry, 2026-08-20, retained for the reasoning

## 5. Large-context testing - the `l` pack and KA-H2

| | |
|---|---|
| **class** | CAPABILITY, gated on RELIABILITY |
| **registered as** | KA-H2; the `l` pack (15 documents, 263,339 chars, roughly `-c 131072`) exists in `spikes/kw-eval/kw_corpus.py` and has never been run |
| **why not run** | **It enters the >60 GiB regime.** `docs/memory-edge-deadlock.md` records an unkillable amdgpu suballocator deadlock in that regime needing a physical power cycle, and the rule is that such runs happen **attended, box quiet**. The account that would run it cannot power-cycle the machine. E48 also already walked the long-context ladder to 236,122 tokens and found the prefill wall, so the remaining question is narrower than it looks. |
| **what would justify it** | An attended session with the owner present, **or** a model whose weights leave enough headroom that a 131K KV cache stays under 60 GiB. The second is the cheaper route and it is a model-selection criterion, not an experiment. |
| **preconditions, non-negotiable** | Read `docs/memory-edge-deadlock.md` first. Relay down. Nothing else on the box. Someone able to reach the power button. |

## 6. S-H1 - dual residency

| | |
|---|---|
| **class** | INFRASTRUCTURE, gated on RELIABILITY |
| **registered as** | S-H1, "sits on the memory edge - see correction 6" |
| **why not run** | Same regime as item 5, and its premise weakened during the programme. Dual residency exists to avoid a model swap; E58 measured the swap cost and F82 settled the routing question in favour of **one resident workhorse plus named routing**, which needs no second resident model. E34's router work already measured two models resident at 41.04 GiB with 0.04s switching, so the mechanism is known - what is unmeasured is whether it is safe at the sizes now in use. |
| **what would justify it** | A workload that genuinely interleaves two models per request. The measured relay traffic is **100% served by the workhorse** across 952 requests and 15 active days, so that workload does not exist yet. |

## 7. gpt-oss-120b decode-hang root cause

| | |
|---|---|
| **class** | RELIABILITY |
| **registered as** | open since 2026-08-19, `docs/2026-08-19-gptoss120b-decode-hang.md` |
| **why not run** | **It was bounded instead of explained, and the bound is the actionable half.** E71 and E72 ran 125 controlled cycles with zero failures, putting a 95% two-sided Wilson upper bound of **2.98%** on the per-load fault rate. Root-causing it means bisecting a fault observed **exactly once** and never reproduced in 125 attempts, in a driver whose full `dmesg` trace needs sudo and is lost across the power cycle that recovery requires. That is an open-ended kernel investigation with no reproduction. |
| **what would justify it** | A **second** occurrence - which makes it reproducible and gives the bisect something to bisect. Or gpt-oss-120b becoming the production model, which would make a ~3% ceiling on unattended use unacceptable rather than merely noted. |
| **⚠ the bound does NOT cross the kernel boundary** | All 125 cycles ran on `7.0.0-28-generic`. The box now runs `7.0.0-29-generic` and amdgpu is in-kernel. **Before any unattended gpt-oss-120b use on the current kernel, re-establish the bound** - see item 8. |

## 8. The gpt-oss-120b cold-load bridge on kernel 7.0.0-29

| | |
|---|---|
| **class** | RELIABILITY |
| **registered as** | F57 ADDENDUM 2, "what must happen after the reboot" |
| **why not run** | It requires loading a 63 GiB model, which is the >60 GiB regime of items 5 and 6, unattended, on a driver whose behaviour in that regime is exactly what is unknown. The check designed to measure a risk should not be the thing that realises it. **E76 carried a cheaper bridge instead**: nine E74 items were reused verbatim as controls and their verdicts compared across the kernel boundary, which tests capability transfer at roughly 20 GiB rather than 63. |
| **what would justify it** | Any attended session that intends to use gpt-oss-120b. It is step 2 of `docs/NEW-MODEL-INTAKE.md` for that model specifically. |
| **the banked figures to bridge against** | E72, 100 cold loads on `7.0.0-28`: **22.02s median load, 0.87s median TTFT, 63.06 GiB GTT peak**, very tight spread. A handful of iterations of `tools/soak_load.py` either reproduces those or does not. |

## 9. The C-H1 frontier comparator arm

| | |
|---|---|
| **class** | INFRASTRUCTURE |
| **status** | **NOT NEEDED - closed, not deferred.** Recorded here so a future reader does not resurrect it from E73's stopping rule. |
| **why** | The rule asked for a frontier arm to check the harness before blaming the models. `results/raw/ch1-validation.json` does that job better: for all five usable tasks the **real commit's own change passes its own held-out tests inside the same sandbox, by the same grader**, and the reverted state fails them. That is deterministic, model-free, and fixes the reference solution instead of sampling one. |

## 11. E36 - the cloud reference arms, and the quantisation isolator

| | |
|---|---|
| **class** | CAPABILITY |
| **registered as** | E36, 2026-08-15, with predictions. Never run |
| **why not run** | It needs a paid endpoint serving `qwen/qwen3.8-27b` unquantised. The OpenRouter credit expired and the key file was removed in August (commit `49ffe47`). |
| **the gap it leaves, stated plainly** | **Where a local arm underperforms, this repository cannot say whether the cause is the model or our Q4_K_M quantisation of it.** Every local-vs-local comparison remains valid; every "the model is weak here" reading is confounded with the stack. |
| **what would justify it** | Any working cloud credit and one afternoon. It is the cheapest unrun item on this list and the only one that removes a confound rather than refining a number. |

## 12. E35 - exact-needle recall for the hybrid at 64K and 128K

| | |
|---|---|
| **class** | CAPABILITY, gated on RELIABILITY at the 128K rung |
| **registered as** | E35, 2026-08-15, with a discriminating prediction. Never run |
| **why not run** | The long-context work went a different and harder route: E48 took the ladder to roughly 236,000 tokens measuring reasoning over 119 distractors. The 128K rung of E35 also sits in the >60 GiB regime of item 5. |
| **what would justify it** | An attended session, or a model whose weights leave room for a 128K KV cache under 60 GiB. Also: any claim that this hybrid architecture is good at long-range *retrieval*, which is precisely what compression should hurt and what has never been measured here. |
| **the prediction, preserved** | *At 128K, Qwen3.8's recall does not exceed the control's by more than 1 needle. If it scores 5/5, compression costs nothing for exact retrieval at this scale and the hybrid is strictly better on both axes.* |

## 13. Three branches E76 opened and did not follow

Recorded so they are not lost and not pursued. The close-out rule was that E76
must not spawn exploratory work, and it did not.

| branch | class | what it would ask | what would justify it |
|---|---|---|---|
| **the reviewer is blind to ABSENT topics** | CAPABILITY | arm D accepted four confident answers about the machine's Ubuntu release, headcount, disk capacity and Python version - none of which the sources mention at all. Checking a claim against sources and noticing a claim has no source may be different capabilities | a review layer being proposed again for any purpose. This is the question that would decide it |
| **hedge-then-assert** | instrument | the one repair arm D made declines and then derives "less than 1/13" from real corpus text. `trap_pattern` catches that shape on the ten new items; the two carried E74 items have none, deliberately | expanding the abstention bank. Give every unanswerable item a trap pattern |
| **the decision rule did not survive a third arm** | instrument | E76's registered rule half-fired on two branches because it was written for two arms and three ran. The adjudication is stated in the entry with its reasoning, but the rule should have had a tie-break | writing any future decision rule. Register the tie-break with the rule, not after seeing the numbers |

## 10. Open owner questions

Neither blocks anything and both are recorded in `QUESTIONS-FOR-ALASTAIR.md`.

| | class | why it stays open |
|---|---|---|
| **Q2** instant-tier convention (does the ~70 t/s line apply at d0 only, or also at 8K?) | INFRASTRUCTURE | a naming convention for badges, not a measurement. Both readings are carried in the results log |
| **Q4** results-package publication scope | INFRASTRUCTURE | a licensing and content decision that is the owner's. Scaffolding is ready (`results/INDEX.md`, `tools/build_results_zip.sh`) |

`DEFERRED-ROOT.md` separately holds the one item needing sudo - a Node.js
install decision that the user-level install makes optional.

## 14. Third-party 128GB token-speed claims, unverified (recorded 2026-08-31)

**Why:** these are the only external figures we hold for this hardware class on
models we have not benchmarked, and three of the five names are a generation we
have never tested. If they are roughly right they change which models are worth
downloading at all; if they are wrong the error matters, because a reader could
take them for measurements.

**Trigger:** supplied by the owner mid-session on 2026-08-31 during the E91
Flash-Next run. Not measured here, not from any sparkbench run.

| model, as supplied | claimed avg. token speed |
|---|---|
| Qwen3.5-35B-A3B MoE | ~50 tok/s |
| GPT-OSS:120B MoE | ~35 tok/s |
| Qwen3.5-122B-A10B MoE | ~22 tok/s |
| Gemma-4-E4B MoE | ~50 tok/s |
| Qwen3.5-27B Dense | ~10 tok/s |

**Status: CLAIMS, not measurements.** No source, no serving config, no context
depth, no quant named - and this programme's own Rule 8 says a benchmark
measures a CONFIG, so a bare tok/s figure with none of those attached cannot be
compared against anything in `results/`. Do not quote them in any report.

**What is worth noting anyway:** the shape agrees with F41. The one dense entry
is ~5x slower than the MoE entries of similar or larger total size, which is
exactly the memory-bandwidth story F41 measured directly - a dense model reads
far more weight per token, and this box is bandwidth-bound. Agreement on shape
is weak corroboration; it is not evidence for any individual number.

**What would justify following up:** a decision about whether to fetch any of
these. `GPT-OSS:120B` we already hold, so its ~35 tok/s claim is the cheapest
one to check and the only one testable without a download. The Qwen3.5 and
Gemma-4 names do not match anything in `manifests/MANIFEST.md` and would each
need pinning and fetching first - and the retention rule means a download is
kept, so that is a real commitment rather than a trial.

## 15. Strix Halo community tips - what is testable here, and what conflicts (2026-08-31)

**Why:** two owner-supplied community sources describe configuration for this
exact chip (GMKtec EVO-X2, Ryzen AI Max+ 395, 128 GB unified). Some of it
corroborates findings we already hold, some is testable and untested, and on one
point the two sources **directly contradict each other**. Recorded so the
contradiction is not resolved by whichever was read most recently.

**Trigger:** supplied 2026-08-31 during the E91 run - a forum post and
`missionslog.com/en/gmktec-evo-x2-mini-pc/` (fetched, read-only).

### Corroborates what we already measured - no action

- **"Vulkan is often faster than ROCm on AMD; always try it."** Asserted, not
  measured, in both sources. It is also our standing configuration and E88/F106
  measured this box at or above its hardware class on Vulkan RADV. Agreement, no
  new information.
- **"MoE models are Strix Halo's superpower - active parameters determine
  throughput, not total size."** This is F41, which we measured directly with a
  control. Their dense entries sit ~5x below MoE entries of similar total size,
  which is the same shape. Weak corroboration of a finding we already own.

### ⚠️ DIRECT CONFLICT - BIOS memory carve-out

| source | advice |
|---|---|
| forum post | UMA Frame Buffer Size **512 MB**, keep IOMMU enabled |
| missionslog | reserve **~96 GB** as VRAM (~107 GB usable of 128) |
| an earlier post in the same thread | `UMA_SPECIFIED`, **96 G** |

These are opposite strategies: a small carve-out leaving a large dynamic GTT
pool, versus a large fixed VRAM reservation. **We are evidently on the first
one** - every figure this programme records is GTT-shaped, and F109 reached
105.15 GiB of GTT, which a 512 MB fixed carve-out permits and a 96 GB fixed one
would not describe. A commenter asked exactly this question in the forum thread
("is there a measurable performance difference between a 96G fixed UMA carve-out
and 1G + GTT shared pool?") and received no answer.

**Testable, and genuinely open.** It would need a BIOS change and a reboot, so it
is owner-only and disruptive, and it must not be attempted casually - the memory
configuration is the substrate every figure in `results/` sits on, and changing
it invalidates cross-run comparison exactly the way a build change does (E85).
**If it is ever tested, it is a full re-baseline, not a leg.**

### Testable and untested

- **"Dense models >= 27B are impractical on this chip (<14 tok/s)."** Their two
  independent tables give ~10-14 tok/s for a dense 27B. We hold a dense 27B
  (Qwen3.8-27B) and have never measured its `tg128` - E91 gives wall-clock per
  question, which is not tok/s. **One `llama-bench` leg settles it** and would
  join the model-survey table. Cheapest open item here.
- **"116 tok/s for Qwen3.6-35B-A3B via a ROCmFPX fork with MTP."** Third-party
  fork, unverified, and we no longer hold that model. Related to the parked ROCm
  question and to `stew675`'s dispatch-overhead work (DEFERRED item on ROCm);
  note that these two sources give **different mechanisms** for ROCm being slow -
  the forum post says unified-memory layer-splitting with mismatched precision,
  `stew675` measured per-kernel dispatch gaps. At most one is right, and we have
  measured neither.

### Not applicable to us

LM Studio, AnythingLLM, Open WebUI, Cherry Studio, Unsloth as a runner,
OmniRoute, WanGP. This fleet serves through sparkrouter and llama-server
directly and settled its local coding client at F112-F115 (Aider via
`tools/local-code`). SearXNG for RAG is plausible but is not a sparkbench
question.

**Their speed tables are not comparable to ours regardless.** No context depth,
no serving flags, and the numbers are sourced to a public sweep on a **Framework
Desktop**, a different machine. Rule 8: a benchmark measures a CONFIG. Do not
quote them against `results/`.
