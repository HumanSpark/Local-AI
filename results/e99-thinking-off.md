# E99 RESULT - both models terminate with thinking off, and one of them stops being the model F118 described (2026-08-31)

Scored against `results/e99-prereg.md`, written before any arm ran. Raw:
`results/raw/e99/`. Session log: `results/raw/session-20260831-2232.log`.
Build `daef7b687`, `-fa on -ctk q8_0 -ctv q8_0`, relay down for every arm,
one window held for the whole queue.

**Decision state: PRODUCTION CANDIDATE — rejected, for both models.** The
question was whether either can be routed to. The answer is no, and E99 says
why in a way the earlier arms could not.

## Result

| arm | score | truncated | gate | wall | control (`default`) |
|---|---|---|---|---|---|
| A Kwaipilot l4 `off` | **8/15** | **0** | PASS | **39.3 s** | 12/15, gate **FAIL**, 1 truncated |
| C Nemotron l4 `off` | **4/15** | **0** | PASS | **30.4 s** | 14/15, gate **FAIL**, 1 truncated (1134 s in E98) |
| B Kwaipilot expert coding `off` | **2/8 pass** | **0** | PASS | 99.9 s | no score ever obtained, 6 of 8 truncated |

All three arms exited 0. Every gate passed, including the Rule 14 transport
gate added earlier tonight.

## Hypotheses, each on the field it named

1. **PRIMARY - `--thinking off` makes them terminate.** Field:
   `truncation_gate` on A, B and C. **HOLDS, decisively, on all three.** Zero
   truncated items anywhere, inside the *same* 16,384-token budget that was
   insufficient at `default`. Nemotron went from consuming its entire budget on
   N2 to answering all 15 items in **30 seconds**.
2. **Kwaipilot's coding bank becomes measurable for the first time.** Field:
   arm B `truncated`, 6 -> 0. **HOLDS.** F119 could not report a coding score
   at all; there is now a quotable one, and it is **2/8**.
3. **The l4 scores FALL.** Field: `correct` on A and C. **HOLDS for Kwaipilot,
   FALSIFIED for Nemotron - it fell far further than registered.**
   - Kwaipilot 12 -> **8/15**, registered band 8-12. Holds, at the bottom edge.
   - Nemotron 14 -> **4/15**, registered band 9-14. **Outside the band.** The
     prediction was wrong and is recorded as wrong.
4. **Nemotron's N2 completes and is wrong.** Field: N2 `outcome` on arm C.
   **HOLDS.** N2 returned `31 August 2026`, graded `wrong`, in 1.66 s. The
   reasoning loop was not secretly saving that item - but see below, because
   the interesting part is what else went with it.
5. **Speed improves materially** - each arm under half its `default` wall.
   **HOLDS overwhelmingly.** Nemotron l4: **1134 s -> 30.4 s, a 37x
   reduction.**

## The finding: the capability and the termination are the same setting

**Nemotron scored 0 of 8 walked periods with thinking off.** At `default` it
scored 7 of 7 answered. That is not a degradation, it is the disappearance of
the exact capability F118 was written about:

| Nemotron-3-Nano, l4 | walked periods | l4 total | terminates? | score quotable? |
|---|---|---|---|---|
| `default` (E92, E98) | 7 of 7 **answered** | 14/15 | **no** - burns the whole budget on N2 | **no** - gate FAIL |
| `off` (E99) | **0 of 8** | 4/15 | **yes**, in 30 s | yes |

**So there is no configuration of this model that is both measurable and
good.** F118 established that Nemotron can walk a calendar where the workhorse
cannot - that finding stands, and E99 does not touch it. What E99 adds is that
the ability lives only in the configuration that does not stop, and a model
that cannot be relied on to finish cannot be routed to whatever it scores.

Kwaipilot degrades rather than collapses - 12 to 8 - but its own bank tells the
same story: **2 of 8 expert coding tasks pass**, in a repo whose motivating
interest was that it tops a public code subset (the programme's B8). One task
did not merely fail, it errored: `apply_patch` raised
`ValueError: Path does not exist: /a`.

## The failure mode Nemotron acquires, which a score hides

With thinking off, Nemotron flipped **both** `defect_absent` items to `YES` -
it now asserts defects that are not in the pack. At `default` it got both
right. Those items exist precisely to catch a model that invents problems, so
turning reasoning off did not just make it worse at arithmetic, it made it
**over-claim**. Its citation validity also fell, 15/15 to 13/15.

That is the F79/E76 failure this programme already prices as expensive in
advisory work, and it is invisible in the headline "4/15".

## What this changes

**Neither model is routable, and the routing guide needs no edit** - neither
was ever recommended in it. Concretely:

- **Nemotron-3-Nano is not a workhorse replacement.** F118's finding survives
  as a statement about capability; E99 adds that the capability is not
  deliverable. It costs 22.96 GiB against the incumbent's 15.66 GiB and, in the
  only configuration that terminates, scores 4/15 against the incumbent's
  14/15.
- **The queue's A6 (coding completion) and A11 (quantisation) follow-ups are
  dead behind Kwaipilot**, which was the condition the merge document set for
  them: they were deferred behind "the `thinking off` arm, which is cheaper and
  answers whether the coding bank can measure that model at all". It can, and
  the answer is 2/8.
- **`--thinking off` is a diagnostic, not a deployment setting**, for these two
  models. Prediction 3's falsifier - "if the scores hold or rise, `off` becomes
  the recommended configuration" - did not fire in the direction that would have
  made it a recommendation.

## Scope

**Scope tag: CONFIGURATION**, per model. Two models, one treatment, three arms,
one build, two banks. Nothing here licenses a claim about `enable_thinking`
generally or about either model family. F118 is this repo's worked example of
moving outward a level without new evidence - and this page is careful not to
repeat it in the other direction: **E99 does not falsify F118.** It measures a
different configuration.

Not measured: whether either model terminates on any other bank, throughput
under load, long context, tool use, or any intermediate reasoning setting -
there is none, because neither template carries `reasoning_effort`.

## Method notes worth keeping

- **One window for the whole queue.** `tools/session_bench.sh` opened the
  maintenance window once, ran three arms back to back, and restored the relay
  only at the end, verified by state. Per-experiment windows had been stopping
  and starting the relay between every experiment.
- **The queue's argument list is split with `xargs`, not by word-splitting.**
  Bare `$args` would have handed `--server-extra` the value `"-fa` and
  scattered the rest; caught before launch by printing argv.
- **The cheap arm answered the expensive question.** Three arms, 170 seconds
  total, against an estimate of up to two hours - because the treatment's whole
  effect is that the models stop generating. The uncertainty in the estimate
  *was* hypothesis 1.
