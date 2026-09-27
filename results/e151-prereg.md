# File: e151-prereg.md
# Purpose: Pre-registration for E151 - one arm testing whether Atlas's prefix cache is what starves its DFlash drafter on multi-turn work.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: E148-E150 measured the same acceptance curve for Atlas's DFlash drafter under three configurations (as shipped;
# causal SWA declared; context cap lifted to 36,864): about 2.3 accepted tokens per step under 4K context, near zero past
# 8K. Two facts written before this run point elsewhere. Atlas's own WARN at startup: "--enable-prefix-caching has a
# community-reported correctness regression on SM12.x with DFlash; outputs may be wrong on multi-turn cache hits". And
# M3p's log, split by turn: at the SAME 4-8K context, first turns of a conversation (no cache hit possible) accept 1.125
# per step and later turns 0.207. One arm, one variable: prefix caching off. Written before the run, while E150 runs.

# E151 PRE-REGISTRATION - Atlas DFlash with the prefix cache off (2026-09-26)

## The question

Does the drafter's acceptance recover on later turns when nothing is served from the prefix cache? If yes, F175's cause is the
cache/DFlash interaction Atlas warns about (the captured hidden states the drafter needs are not produced for cached prefix), and
Atlas's DFlash on this workload is slow either way: with the cache it drafts nothing, without it every turn re-prefills its
whole context (E146 amendment 3 measured 61 s per turn for MTP without the cache).

## Evidence in hand (M3p, E148, before this run)

| turns | context 0-4K | 4-8K | 8-12K | 12K+ |
|---|---|---|---|---|
| first turn of a conversation (4 turns, 81 steps) | 2.317 | 1.125 | - | - |
| later turns (202 turns, 4,079 steps) | 1.364 | 0.207 | 0.016 | 0.009 |

Same context bucket, 5.4x apart. First turns reach at most 5.2K of context, so the table cannot separate "later turn" from
"long context" beyond 8K; E151 can.

## Arm

| arm | what changes from E148 M3p | what does not |
|---|---|---|
| **M6** | `--enable-prefix-caching` removed from the `serve-amd.sh` invocation | binary, original drafter directory, γ 16, `num_drafts` default, `ATLAS_DFLASH_CTX_WINDOW` default 4,096, `SSM_SLOTS`/`SSM_CKPT_INTERVAL` as passed by the script, harness, 206 turns |

## Gates

- G1: drafter bytes match the pin.
- G2: server answers `/v1/models`; the log does NOT contain `Prefix caching: ENABLED`, and the drafter-loaded line is present.
  If the log shows caching enabled anyway, VOID.
- G3: kernel, Livepatch, GTT, Chatterbox as E149/E150; memory guard armed.

## Conditions

E148's, one arm, harness capped at **2,400 s**. Without the cache each turn re-prefills up to 28K tokens, so the cap will fire
early (E146's uncached MTP arm ran 61 s per turn: about 40 turns). The arm is about acceptance, not speed; it is scored
server-side (E149's method) and by the acceptance table split by first turn against later turns.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `M6.accepted_per_step`, later turns, 4,096-8,191 bucket | >= 0.8 | if the cache is the cause this matches the first-turn figure (1.125); if not, it stays near 0.2 |
| P2 | `M6.accepted_per_step`, later turns, 8,192+ | >= 0.5 | as P1; the collapse past 8K is entirely later turns in M3p |
| P3 | `M6.accepted_per_step`, first turns, 0-4K | 2.0-2.6 | unchanged from M3p (2.317): the cache cannot affect a first turn |
| P4 | cap fires | yes | re-prefill of 5-28K tokens per turn |
| P5 | `M6` server-side time per turn on the same first N turns vs M3p | 1.5-4.0x | re-prefill cost against verify savings; wide on purpose |

## Decision

- P1 and P2 held: the cause is the prefix-cache interaction; register it, and the Atlas verdict on this workload is "DFlash is not
  usable: drafts nothing with the cache, re-prefills without it". P3 is the control; if P3 moves, the arm is confounded and no
  cause is claimed.
- P1 and P2 falsified with P3 held: the cache is not the cause; the remaining candidate is the HIP kernel path, which this
  project does not pursue.

## Out of scope

The context cap (E150 answers it), gamma, `num_drafts`, `--dflash-window-size`, any second change, speed bands against M2.
