# E92 RESULTS (2026-08-31): a 22.96 GiB model already on this disk walks a calendar as well as the 27B

Pre-registration: `results/e92-prereg.md`, written before any arm.
Raw: `results/raw/e92/`. Scorer: `tools/e92/score_e92.py`.
Build `daef7b687`, Vulkan RADV, `-fa on -ctk q8_0 -ctv q8_0`, relay down for
every arm. Controls are E91's arms - same build, same day, not re-measured.

## Hypotheses

| # | hypothesis | outcome |
|---|---|---|
| H1 | the vendor SWE-bench uplift does not transfer (Kwaipilot <= 7 of 8) | **HOLDS**, robust to truncation |
| H2 | Kwaipilot >= 3 of 8, matching Qwen3-Coder | **UNSCORABLE** |
| H3 | Kwaipilot solves `sliding_median` | **UNSCORABLE** |
| H4 | Nemotron-3-Nano scores 0-2 of 8 walked, landing with the workhorse | **FALSIFIED** - 7 of 8 |
| H5 | Nemotron l3 within 2 of the workhorse's | **FALSIFIED** - 4 ahead |
| H6 | Nemotron `tg128` within 25% of the workhorse's 92.28 | **FALSIFIED** - 64.52 |
| - | the queued community claim: dense >=27B runs at 10-14 t/s here | **CONFIRMED** - 12.59 |

## The result: F80's finding is about the WORKHORSE, not about the model class

| model | l4 walked | l4 total | l3 | tg128 | weights |
|---|---|---|---|---|---|
| workhorse Qwen3-30B-A3B | **0/8** | 6/15 | 4/12 | 92.28 | 17.28 GiB |
| **Nemotron-3-Nano-30B-A3B** | **7/8** | **14/15** | 8/12 | 64.52 | **22.96 GiB** |
| Qwen3.8-27B `low` | 7/8 | 14/15 | **12/12** | - | 15.66 GiB |
| Flash-Next `medium` (E91) | 7/8 | 14/15 | **12/12** | - | 87.25 GiB |

H4 was registered on the reading that F80's "small models cannot walk a
calendar" is a claim about **~3B-active MoEs as a class**. Nemotron-3-Nano is
31.58B total with ~3.5B active - the same class as the workhorse - and it scores
**7 of 8 where the workhorse scores 0 of 8**. The registered falsifier fired,
and the correct reading of F80 is now narrower: **it is a fact about
Qwen3-30B-A3B, not about small active-parameter counts.**

The verdict is robust to the one truncation in the walked set (N2, the
composition item nothing has ever solved): the true score is 7..8 and the band
was 0-2, so both bounds give the same answer.

**This model has been on this disk since 2026-08-19**, fetched for an E61
follow-on that never ran, and was found by an audit that separated "in the
manifest" from "on disk" from "measured".

## It is not a drop-in replacement, and the reason is the liability axis

Nemotron matches the capable tier on arithmetic and does **not** match it on
document discipline:

- **l3 cross-document: 8/12** against 12/12 for both Qwen3.8-27B and Flash-Next.
  It fails `precedence` (1/2), `multihop` (2/3) and `exhaustive` (0/1).
- **It OVER-CLAIMED on the unanswerable item** (`underspecified` 0/1) where both
  capable models correctly returned `NOT_IN_PACK`. It also produced one
  `stale_value` and one `over_applied`.

That over-claim is the F79/E76 liability shape - a confident answer where the
correct output was a decline - and in professional advisory work it is the
expensive failure, not a scoring detail. **A model that walks a calendar
perfectly and invents an answer when the pack is silent is not safer than the
workhorse, it is differently unsafe.**

**No routing-guide change is proposed on this run.** The arm ran at `default`
effort against the incumbent's `low`, so it is not effort-matched, and one run
with an over-claim on the single unanswerable item is not the basis for moving
advisory work onto a new model. What it justifies is a follow-up: Nemotron at
matched effort on l4, l3 and the E76 abstention bank.

## Kwaipilot does not terminate on this bank

| budget | truncated | completed |
|---|---|---|
| 4,096 tok | 7 of 8 | 1 error |
| **16,384 tok** | **6 of 8**, each consuming the entire budget | 1 error (292 tok), 1 wrong answer (10,691 tok) |

Quadrupling the budget bought one completed task. Six still burn every available
token and emit no code, so this reads as **non-termination rather than
insufficiency**, and a further doubling is unlikely to change it.

The Rule 13 gate therefore refuses a score, and **H2 and H3 are UNSCORABLE
rather than falsified**: passes are bounded 0..6, which straddles H2's `>= 3`
band, and `sliding_median` - H3's whole subject - was one of the truncated
tasks. Only H1 survives, because its `<= 7` verdict is the same at both bounds.

**H1 holding is worth stating carefully.** It says the vendor's claimed
SWE-bench uplift did not appear on this bank. It does **not** say the model is
bad at coding: an external leaderboard supplied by the owner puts KAT Coder top
of its code-specific subset at 8.0. Both can be true if the model's reasoning
does not terminate under this harness's prompt and cap, which is what was
measured.

**The next arm is a declared configuration change, not a repair.** Kwaipilot's
template honours `enable_thinking`, so `--thinking off` asks a genuinely
different question - can it code when not permitted to ruminate? That is
registered as its own arm rather than swapped in silently, because turning
thinking off changes what is measured (the routing guide records it costing
Qwen3-8B four points with every arithmetic item flipping wrong).

Kwaipilot's general document ability, incidentally, is intact: **12/15 on l4**,
double the workhorse's 6/15.

## Throughput, three architectures, one build

| model | architecture | tg128 | pp512 |
|---|---|---|---|
| Qwen3-30B-A3B | MoE, ~3B active | **92.28** | 1140.72 |
| Kwaipilot KAT-Coder (Qwen3.5-35B-A3B) | MoE, ~3B active | 70.00 | 984.04 |
| Nemotron-3-Nano-30B-A3B | hybrid Mamba-Transformer MoE | 64.52 | 890.83 |
| Qwen3.8-27B | **dense** | **12.59** | 294.57 |

H6 registered Nemotron within 25% of the workhorse and it came in 30% below, so
the hybrid Mamba-Transformer does cost throughput against a standard MoE of
comparable active parameters.

**The queued community claim is confirmed on our own hardware.** Two owner-supplied
sources put dense >=27B at 10-14 t/s on this chip; we measure **12.59**. A second
of their figures also lands - they claim 58-78 t/s for 35B-A3B and Kwaipilot,
a 35B-A3B derivative, measures 70.00. Their table was sourced from a Framework
Desktop rather than this box, so two independent confirmations materially raise
its credibility for the models we do not hold.

## What was NOT measured

Nemotron at matched effort, Nemotron on the E76 abstention bank, Kwaipilot with
thinking off, Kwaipilot on l3, vision on any arm, and long context beyond l3's
~21K tokens. Wall times from the eval arms are not throughput figures - only the
`llama-bench` legs above are.
