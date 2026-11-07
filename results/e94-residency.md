# E94 RESULT - three models resident is viable, and the cost is prefill, not memory (2026-09-01)

Scored against `results/e94-prereg.md` including **amendment 1**, declared
2026-08-31 22:48 before any arm ran. Raw: `results/raw/e94/`. Build
`daef7b687`, kernel 7.0.0-29, router mode via `--models-preset`, relay down for
every arm, one window held per queue.

**Decision state: PRODUCTION CANDIDATE.** Three models can be held resident at
production context with switching free and residency free. llama.cpp still
labels router mode experimental, so per the pre-registration this is a case for
a proposal to sparkrouter, not a change to it.

**All arms are complete**, including the asymmetric configuration, which is
now the recommended one and is measured rather than proposed.

## The trio, and why aliases rather than names

| alias | model | weights |
|---|---|---|
| `fast` | Qwen3-30B-A3B-Instruct-2507 | 17.28 GiB |
| `smart` | Qwen3.8-27B-Q4_K_M | 15.66 GiB |
| `code` | Qwen3-Coder-30B-A3B-Instruct | 17.28 GiB |

**The INI section name is the alias**, because llama.cpp's router routes on the
requested model name. So `[fast]` is what a caller sends as `{"model": "fast"}`.
The aliases are roles rather than model names deliberately: the models change
week to week and the callers must not.

Amendment 1 replaced Nemotron-3-Nano with Qwen3-Coder after E99 rejected it, and
that **lowered** total weights from 55.90 to 50.22 GiB - so H1's threshold got
harder to breach, not easier, which is the property that matters when an arm
changes after registration.

## Result

### Memory: three models resident, at every context tested

| context per model | GTT, all three resident | delta over baseline |
|---|---|---|
| 32,768 | 58.65 GiB | 53.63 |
| 65,536 | 63.07 GiB | 58.05 |
| 98,304 (production) | **67.53 GiB** | 62.51 |
| 131,072 | 71.93 GiB | 66.91 |
| **262,144 (max trained)** | **89.89 GiB** | 84.87 |

Baseline before any load was 5.02 GiB. All five rungs loaded and served.

**The slope is about 0.045 GiB per 1,000 tokens per model** and is close to
linear. A naive all-layer key-value formula predicts far more, which is A14's
point: parameter count and file size did not predict this and the measurement
did.

### Switching: free, at every rung

Six ordered pairs at each of three rungs, 18 measurements. The switch is the
second request; its excess over that alias's own solo minimum is the cost of
having just served a different model.

| context | worst excess | median excess |
|---|---|---|
| 32,768 | +0.022 s | +0.003 s |
| 65,536 | +0.026 s | +0.002 s |
| 98,304 | +0.015 s | +0.006 s |

**Several excesses are negative**, which puts the switching cost inside
run-to-run noise rather than merely small.

### Residency: an idle resident model costs the active one nothing

| `fast` | best tok/s |
|---|---|
| alone, 98,304 | **83.74** |
| with two others resident, 98,304 | 83.33 |
| with two others resident, 131,072 | 83.61 |
| with two others resident, 262,144 | 83.06 |

`fast` alone occupied 20.69 GiB against 62.51 for all three, so the other two
models were genuinely loaded.

### Usable context: the full allocation, not merely the allocation

| context | largest prompt SERVED | fraction of allocation |
|---|---|---|
| 98,304 | 98,116 tokens, all three aliases | 0.998 |
| 131,072 | 130,852 tokens, all three aliases | 0.998 |
| 262,144 | **261,827 tokens**, `smart` alone | 0.999 |

The missing 0.2% is the search's own headroom for the answer
(`max_tokens` + 64), not a refusal. **There is no ceiling below the allocation
at any size tested.**

**A ceiling reported at 262,144 on 2026-09-01 is RETRACTED.** The first attempt
returned `HTTP 500: Context size has been exceeded` at 131,813 tokens and was
read as a ceiling at 49% of the allocation. That run was contaminated: the
client gave up after 1,800 s on the top probe, the server kept prefilling it,
and every later probe queued behind the backlog - walls FELL as prompts GREW,
from 1,379 s at 2,047 tokens to 38.8 s at 129,550. A clean re-run with a
7,200 s client timeout served 261,827 tokens in 3,546 s. **The registered
prediction for that re-run - a genuine refusal near 131,072 - is FALSIFIED.**

Whether three models sharing the pool reproduces the refusal is open, and is
what the asymmetric arm tests.

## Hypotheses, each on the field it named

1. **All three resident below 75 GiB at 32,768 each.** Field:
   `mem_info_gtt_used` delta. **HOLDS** - 53.63 GiB, and still only 62.51 at
   production's 98,304.
2. **Switching under 0.5 s.** Field: wall time of a request to X immediately
   after one to Y, minus that request's solo latency. **HOLDS** - worst case
   +0.026 s, 19x inside the band.
3. **Residency is free.** **HOLDS, on a substituted ruler, and that is declared
   rather than glossed.** The prereg named `tg128` against F118's solo 92.28
   within +/-3%. `llama-bench` measures pure decode; this runner measures an HTTP
   request end to end, so comparing them would have been two rulers. The
   substitute is like-for-like: the same request path, one model resident against
   three. 83.74 alone against 83.06-83.61 resident is inside F15's +/-1.5% noise.
   **The registered comparison against 92.28 was NOT performed.**
4. **Context ceiling at least 32,768 per model with three resident.** Field: the
   largest `-c` at which all three load and serve. **HOLDS, by a wide margin** -
   the full allocation serves at 98,304 and 131,072, and all three load at
   262,144.
5. **and 6.** Withdrawn in amendment 1: H5's matched-effort arm cannot exist
   (F124) and H6's bank cannot load (U02).

## The finding the memory figures do not show: prefill

The context-ceiling probes are the first long-prompt measurements this
programme has taken, and they change the recommendation.

| prompt | configuration | wall to first answer | prefill rate |
|---|---|---|---|
| 3,976 tokens | 1 model, production (F111) | ~3.9 s | **1,024.60 tok/s** |
| 32,644 tokens | 3 resident, asymmetric | 95 s | 344.5 tok/s |
| 98,116 tokens | 3 resident, uniform | 734 s | 133.6 tok/s |
| 130,852 tokens | 3 resident, uniform | 1,281 s | 102.2 tok/s |
| **261,827 tokens** | 1 resident | **3,546 s** | **73.8 tok/s** |

```
TIME TO FIRST OUTPUT TOKEN

  3,976 tok |#                                             |   3.9 s   1024.6 tok/s
 32,644 tok |#                                             |   2 min    344.5 tok/s
 98,116 tok |##########                                    |  12 min    133.6 tok/s
130,852 tok |#################                             |  21 min    102.2 tok/s
261,827 tok |##############################################|  59 min     73.8 tok/s
```

Configurations differ across the points and are named in the table above, so
this is a curve over PROMPT LENGTH rather than a single controlled sweep. It is
monotonic across all five, and residency was separately measured as free
(H3), which is why the points are comparable at all.

**The rate column is CONFIRMED (E100).** `llama-server`'s own `prompt eval time`
agrees with these client-derived rates within 0.9% on four arms, and within 0.1%
on the 261,827-token request. A live progress counter read during the run
suggested 104.7-116.4 tok/s and was wrong - both samples sat at 27-36% of the
same prefill and the rate is not constant across a prompt (F137). The registered
prediction that the client wall was a composite is FALSIFIED; no correction was
needed.

**The curve is superlinear**, which is what a capacity table cannot show:

| step | prompt grows | wait grows |
|---|---|---|
| 3,976 -> 98,116 | x24.7 | **x188** |
| 98,116 -> 130,852 | x1.33 | x1.74 |
| 130,852 -> 261,827 | **x2.00** | **x2.77** |

Doubling the prompt costs nearly three times the wait. A full-context request
is twelve minutes at 98,304, twenty-one at 131,072 and **fifty-nine minutes at
262,144**.

So the memory question and the usability question have different answers.
Memory says all three models can hold 262,144 tokens each. Prefill says almost
nobody should send one.

**This is the number that should govern the context decision, and it was not in
the pre-registration.** E94 was designed around whether three models fit. They
do, comfortably. What decides the configuration is what a long prompt costs to
serve, and that only appeared because the ceiling search had to send real
full-length prompts to find out whether the allocation was usable.

## What this changes

**Run three models resident, not two.** 67.53 GiB at production context leaves
53 GiB spare, switching is inside noise, and an idle model taxes the active one
by nothing measurable. The two-model cap in F40 rested on the memory boundary
F109 retracted.

**Do not raise context uniformly.** Uniform 262,144 costs 89.89 GiB and buys a
capability whose prefill nobody will wait for. The better spend is asymmetric,
because only one alias sees long inputs:

| alias | proposed context | reason |
|---|---|---|
| `smart` | 262,144 | document and advisory work, where long inputs actually arrive and a wait is tolerable |
| `code` | 65,536 | a repository's worth of files, rarely more |
| `fast` | 32,768 | short interactive turns, sub-second answers |

`tools/e94/models-asym.ini` carries that configuration and **it is now
MEASURED** (F138):

| alias | allocated | served | wall | prefill |
|---|---|---|---|---|
| `fast` | 32,768 | 32,644 | 95 s | 347.5 tok/s |
| `code` | 65,536 | 65,380 | 348 s | 188.5 tok/s |
| `smart` | 262,144 | **261,827** | 3,544 s | 74.0 tok/s |

**All three resident: 68.10 GiB** - 0.57 GiB more than uniform 98,304 and
**21.8 GiB less than uniform 262,144**, with the document model on four times
the context and the other two answering in under a second.

**It also falsified the last live alternative for the retracted ceiling.** The
`HTTP 500` at 131,813 - exactly half of 262,144 - had two candidate causes once
the queue contamination was found: the contamination itself, or three models
sharing the pool. `smart` served 261,827 tokens with two other models resident,
so **sharing is falsified and contamination is the whole explanation.**

## Scope, and what is not claimed

**Scope tag: PLATFORM.** One trio, one build, one kernel, router mode only.

- **Concurrent inference on two or three models at once was deliberately not
  tested.** F41 already measured that as a fixed bandwidth budget split 4.6:1
  against the mixture-of-experts model. E94 measures residency and switching,
  not parallelism.
- **The 262,144 result now holds in both configurations** - `smart` alone
  (3,546 s) and `smart` with two other models resident (3,544 s). Residency is
  free at maximum context, confirmed by the server's own accounting.
- **Router mode is experimental upstream.** A positive result here is a case for
  a proposal to sparkrouter, not a change to it. `serving.conf` has one writer
  and it is not this repo (F39).

## Method notes worth keeping

- **The unexplained HTTP 400 was the tokenizer, not a context refusal.** In
  router mode `/tokenize` returns 400 unless the request names a model. Three
  arms failed on it and the first reading was "context ceiling", which would
  have entered the record as a finding. F125.
- **A poll needs detection for the negative outcome.** `wait_healthy` watched
  only for health and waited the full 900 s twice on a router that had exited
  in 39 ms with `number of models to load on startup (3) exceeds models_max (1)`.
- **A zombie is not a busy GPU.** A crashed arm left a defunct `llama-server`
  its parent never reaped. It holds nothing and cannot be killed, but `pgrep -x`
  matches it, so the window guard blocked every subsequent bench while telling
  the truth about the process table.
- **The ceiling search was verified against a known answer before it ran on the
  GPU** - a fault in the E97 fake server with a hard 5,000-token limit, which
  the search bracketed at 4,883 served / 5,358 refused.
- **The per-arm timeout was raised from 7,200 s to 21,600 s** after the 262,144
  arm was projected to need ~7,800 s. A timeout must not be the thing that
  decides a result.
