# Fish s2-pro MIOpen vocoder-tuning A/B (W3 T10, 2026-07-25)

**Question the T10 gate asked:** Fish s2-pro's decoder-bound RTF ~0.044x was hypothesised to be
tunable, because the container logs flood with MIOpen falling back to a no-workspace conv solver.
Alastair cleared **one bounded attempt** ("a little bit, not a huge amount"). This is that attempt.

**Answer: NO GAIN. The tuning arm is a null result - and the mechanism explains why, conclusively.**

## Headline

| Arm | proc_rtf (wall s per audio s) | RTF | vs baseline |
|---|---|---|---|
| **Baseline** (Stage 1, excerpt 01, MIOpen defaults) | 22.493x | 0.044x | - |
| **Tuned** measured mean (n=2) | **22.534x** | 0.0443x | **-0.18%** (marginally SLOWER) |
| Tuned, all three renders | 22.425 / 22.506 / 22.561 | | mean 22.497x, CV **0.30%** |

Against the broader Stage-1 nine-excerpt band (mean 22.896x, sd 0.400, CV 1.75%) the tuned mean of
22.534x sits **inside one standard deviation**. Every way of slicing it, the tuning changed nothing:
the difference is smaller than this engine's own run-to-run variation.

**Fish s2-pro remains ~25x slower than realtime on gfx1151.** The Stage-1 operational conclusion is
unchanged: ~180 GPU-hours for the 7 dark + 139 backfill posts.

## Why it is null: MIOpen tuned perfectly and was overruled anyway

This is the load-bearing result, and it is stronger than "tuning didn't help."

The tuning **worked**. MIOpen ran its exhaustive search and persisted a populated user find-db
(`miopen-user-finddb.txt`, copied here as evidence). That db records what the fallback actually
costs, in `solver:time_ms,workspace_bytes,algo` form:

```
GemmFwd1x1_0_1:0.0098895,0,...GEMM  ;  ConvDirectNaiveConvFwd:0.104933,0,...Direct    -> ~10x
GemmBwdRest:0.107961,102400,...GEMM  ;  ConvDirectNaiveConvBwd:7.08207,0,...Direct    -> ~65x
```

And yet the rejection warnings **still fire in the tuned arm** (`tuned-log-evidence.txt`):

```
Solver <GemmFwdRest>, workspace required: 886308864, provided ptr: 0 size: 0
Solver <GemmFwdRest>, workspace required: 765198336, provided ptr: 0 size: 0
Solver <GemmFwdRest>, workspace required: 721158144, provided ptr: 0 size: 0
   ... 12 distinct shapes, 8.6 MB to 886 MB required, every one given ptr: 0 size: 0
```

That is the whole story. **`MIOPEN_FIND_MODE` / `FIND_ENFORCE` govern which solver MIOpen selects
among those it is permitted to run. They cannot grant a workspace the caller declined to allocate.**
The fast GEMM solvers need up to 886 MB of scratch; PyTorch hands MIOpen a null pointer; MIOpen
rejects them at `EvaluateInvokers` and falls to the naive direct convolution - before, during, and
after tuning, identically.

So the bottleneck is **not** "MIOpen is untuned" (a config problem, cheap to fix). It is the
**PyTorch-to-MIOpen workspace contract** on this decoder path (a code problem, not reachable from
the environment). That relocation is the finding.

Corroborating: the LLM stage was untouched by tuning, as predicted - 8.14 / 8.35 / 8.50 tok/s tuned
against 8.49 tok/s at baseline. The decoder was the only variable, and it did not move.

## Method notes (what makes this comparison trustworthy)

- **The metric is proc_rtf, not wall.** s2-pro samples stochastically (`seed=None`), so audio length
  varies per render. The three tuned renders spanned **273.8-337.4s of wall (a 23% spread) while
  proc_rtf varied by only 0.30%** - the length-normalisation is doing exactly the job it was chosen
  for, and comparing raw wall times here would have been meaningless.
- **Identical request path.** `miopen_ab.py` copies the request dict verbatim from `run_fish.py`, the
  script that produced the baseline. A config difference must not be a difference between rulers.
- **The noise band is native, not borrowed.** Judged against Stage 1's own nine-excerpt spread for
  this engine and metric (CV 1.75%), NOT against F15's +/-1.5% - F15 was measured on llama-bench
  token throughput, a different metric on a different workload. (FINDINGS already records this exact
  substitution being caught once before, at F39.)
- **Warm-up excluded and declared.** The container self-warms at startup (`Generated 26 tokens in
  141.86 seconds, 0.18 tokens/sec` - that is torch.compile), so compile was already paid before any
  measured render, in both arms.
- **Warning COUNT is not comparable between arms.** Stage 1 called its logs "flooded" but saved only
  `generate_long`-filtered evidence, so no baseline count exists. The tuned arm shows 32. Warning
  *presence* is comparable; the number is not, and is not claimed as a reduction.
- **Production untouched.** sparkrelay reported `{"state":"serving"}` throughout; GTT returned to the
  20.24 GiB LLM-only baseline exactly on teardown.

## Deviation from HANDOFF.md's prescribed values (corrected, not followed)

The handoff specified `MIOPEN_FIND_MODE=3` ("NORMAL exhaustive") and `MIOPEN_FIND_ENFORCE=3`
("search + save to user db"). Both labels are wrong against the enums in the **shipped** header
(MIOpen 3.5.1, `/opt/rocm/include/miopen/miopen.h`):

| Prescribed | Actually means | Used instead |
|---|---|---|
| `FIND_MODE=3` | HYBRID (NORMAL is 1) | `NORMAL` (string form, no enum ambiguity) |
| `FIND_ENFORCE=3` | Search, **do NOT update db** | `4` = SearchDbUpdate (search AND persist) |

Running the prescribed `FIND_ENFORCE=3` would have re-tuned on every cold start and **never written
the user db**, making the `MIOPEN_USER_DB_PATH` mount inert - the run would have looked like a fair
test of tuning while testing nothing. The populated find-db banked here is the proof the corrected
values engaged. (A string in `libMIOpen.so` - `MIOPEN_FIND_MODE is set to NORMAL due to
MIOPEN_FIND_ENFORCE` - confirms the enforce policy forces NORMAL find regardless.)

## Disposition

**Tuning budget spent. Recommendation: stop here.** The owner authorised a bounded attempt; it ran,
it was measured properly, and it returned nothing. More importantly the evidence now shows *why*
further environment-level tuning cannot help - the lever is in the caller, not the config.

The remaining levers, recorded but explicitly NOT chased under this budget:

- **Workspace provision** (the real one): make the PyTorch side allocate a conv workspace, e.g.
  `torch.backends.cudnn.benchmark=True` and/or channels-last (`PYTORCH_MIOPEN_SUGGEST_NHWC=1`) on
  the decoder path. This requires patching upstream Fish code inside the container, not an env var,
  and would need its own timebox and its own A/B.
- **hipBLASLt** (`ROCBLAS_USE_HIPBLASLT=1`): forced OFF by `Dockerfile.rocm`, likely because it is
  unsupported on gfx1151. Riskier, separate experiment.

Neither changes the Stage-2 plan. Fish stays in the field for the **T13 listening pack on quality
grounds** (its throughput is already recorded and does not improve); the Stage-2 engines proceed as
gated.

## Evidence

- `miopen-ab.json` - the run record (all three renders, baseline reference embedded)
- `tuned-log-evidence.txt` - container env as actually set, workspace-rejection warnings by shape,
  LLM-stage rates
- `miopen-user-finddb.txt` - the persisted MIOpen user find-db proving the search ran and what the
  fallback costs
- `THROUGHPUT-ANALYSIS.md` - the Stage-1 decomposition this A/B tests
- Config: `fish-speech-tts/serve_fish.sh tuned`; harness: `fish-speech-tts/miopen_ab.py`
