# E92 PRE-REGISTRATION - the two MoE models this programme fetched and never ran (2026-08-31)

Written BEFORE any arm runs. Every hypothesis names the FIELD it is scored
against (the E64 rule).

## Why these two

An audit on 2026-08-31 separated "in the manifest" from "on disk" from
"measured". Three MoE models were fetched and never benchmarked; two are still
on disk and need no download:

| model | size | fetched | fetched FOR |
|---|---|---|---|
| Kwaipilot KAT-Coder-V2.5-Dev-Q4_K_M | 19.92 GiB | 2026-08-19 | E61 follow-on: does MoE speed survive coding SFT/RL? Vendor claims 69.4% SWE-bench against a 64.4% base |
| nvidia_Nemotron-3-Nano-30B-A3B-Q4_K_M | 22.96 GiB | 2026-08-19 | E61 follow-on: backup general MoE, behind GLM-4.7-Flash in the funnel |

**E61 never ran**, so both have sat untouched. The third, Mistral-Small-4-119B
(73.76 GB), was fetched for a writing-quality question, removed, and never run;
it is out of scope here because it needs re-fetching.

The audit's wider finding sets the shape of this experiment: **breadth of MoE
testing is good and depth is not.** Outside the workhorse, almost every MoE this
programme touched got throughput and nothing else, so "we tested it" mostly
means "we know its tok/s". These two get capability, and throughput only because
it is nearly free.

## The controls are already measured, on the same build

E91 ran the workhorse and Qwen3.8-27B on `daef7b687` earlier today against l4
and l3. **Those are the controls for arm B here** - same build, same banks, same
grader, same session. No control needs re-running, which is why this experiment
is cheap. If E91's l3 arms are still missing when this runs, l3 comparisons wait
for `run_e91_l3.sh` rather than being made against frozen figures from
`9e40df63b` (E85: build-to-build extrapolation is unsafe for correctness).

## Arms and banks

| arm | model | bank | why that bank |
|---|---|---|---|
| A | Kwaipilot KAT-Coder | `run_coding_eval.py --task-set expert` (8 tasks) | its actual claim is coding. The expert bank has published incumbents: Qwen3.8-27B 7/8, Qwen3-Coder 3/8 |
| A2 | Kwaipilot KAT-Coder | l4 (15 questions) | does a coding-specialised model retain general document ability, or has the SFT cost it? |
| B | Nemotron-3-Nano | l4 + l3 (`--distractors 9`, `--ctx 32768`) | a general MoE, so the general banks - and directly comparable to E91's arms |
| C | both | `llama-bench` canonical legs | joins them to `results/model-survey.md`, which is throughput-shaped |

## Hypotheses. The FIELD is named in each.

1. **PRIMARY: the vendor's SWE-bench uplift does not transfer. Kwaipilot scores
   at or below 7 of 8 on the expert bank.** Field: the expert run's pass count.
   Precedent is this programme's own repeated result - document-benchmark
   strength did not transfer to real repository work for the workhorse, and the
   C-H1 bank has defeated every arm ever pointed at it including cloud ones.
2. **Kwaipilot scores at least 3 of 8 on the expert bank**, matching
   Qwen3-Coder, the local coding incumbent. Field: as above. Below 3 and a
   coding-specialised model has lost to a general one on coding.
3. **Kwaipilot solves `sliding_median`.** Field: that task's individual
   outcome. It is the task with an explicit speed requirement, Qwen3-Coder
   solves it in 257 tokens and 3.25 s, and **Qwen3.8-27B never solves it at
   all**. A coding-specialised model failing it would say the specialisation is
   not the kind that helps here.
4. **DISCRIMINATING: Nemotron-3-Nano scores 0, 1 or 2 of 8 on l4's walked
   periods** - landing with the workhorse (0/8) rather than with Qwen3.8-27B
   (7/8). Field: summed `by_category` correct over `statutory_period`,
   `breach_clock`, `interest_calc`, `notice_period`, `fee_basis`. F80's claim is
   that a ~3B-active MoE cannot walk a calendar; Nemotron-Nano is 30B/A3B, the
   same class as the workhorse, so if F80 is about the CLASS this must hold.
5. **Nemotron-3-Nano's l3 total is within 2 of the workhorse's.** Field: l3
   `correct` total, against E91's arm A once `run_e91_l3.sh` has produced it.
6. **Nemotron-3-Nano's `tg128` is within 25% of the workhorse's 92.28 tok/s.**
   Field: `llama-bench` tg128 at depth 0. Same parameter class and quant, but it
   is a hybrid Mamba-Transformer rather than a standard MoE, so this is the
   weakest of the six and is registered as a check on whether the architecture
   costs throughput.

## Falsifiers

**On hypothesis 4, and this is the one worth running the experiment for:** if
Nemotron-3-Nano scores **5 or more of 8** on walked periods, then F80's finding
is about the WORKHOUSE specifically and not about small-active-parameter MoEs as
a class. That would change how the routing guide generalises its advice, and it
would mean a 22.96 GiB model already on this disk can do the one thing the guide
currently says costs you the 27B.

**On hypothesis 1:** if Kwaipilot scores 8 of 8, the vendor uplift transferred
completely, and the programme's standing "benchmark strength does not transfer"
result needs qualifying rather than repeating.

## What this does NOT measure

Long context, tool use, vision, abstention beyond what l4's single
`underspecified` item catches, and anything about Kwaipilot on l3. Timing from
the eval arms is not a finding - only the dedicated `llama-bench` legs are
throughput measurements, and those run in the same window with the relay down.

## Cost

Both models are ~20 GiB, so both fit alongside production on memory. They are
run in a maintenance window anyway: F41 measured that a concurrent bench and the
resident workhorse split one bandwidth budget 4.6:1 against the MoE, so a
contended run would void the throughput legs and degrade the live service for
its whole duration. Estimated 45-75 minutes total, gated behind E91 and its l3
re-run finishing.
