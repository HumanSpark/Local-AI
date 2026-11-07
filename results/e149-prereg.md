# File: e149-prereg.md
# Purpose: Pre-registration for E149 - one arm testing the leading explanation for F175: Atlas served z-lab's DFlash drafter without its causal sliding-window layers.
# Project: sparkbench | Date: 2026-09-26
#
# Overview: E148's M3p accepted 0.064 tokens per 15-draft step (F175). Atlas HEAD reads the drafter's `causal`, `use_swa`
# and `swa_window_size` only from the nested `dflash_config` block of config.json (spark-model/src/weight_loader/
# dflash_loader.rs:138-146; from_weights.rs defaults causal to false and the window to none). z-lab's checkpoint declares
# its architecture at the top level instead (`layer_types` four sliding + one full, `sliding_window` 2048), which HEAD never
# reads for a drafter, and the M3p log confirms what ran: `causal=None, swa=None/None`. The GGUF that llama.cpp used in E147
# carries the same window (`dflash.attention.sliding_window 2048`, pattern TTTTF) and accepted 14 of 19 drafts in its probe.
# One arm, one change: the same weights through a config that supplies the three fields. Written before the run.

# E149 PRE-REGISTRATION - the drafter's sliding-window layers, declared to Atlas (2026-09-26)

## The question

Does F175's near-zero acceptance come from Atlas running the drafter's four causal sliding-window layers as non-causal full
attention? If declaring them recovers acceptance, F175's cause is a config-schema mismatch between the checkpoint and the engine,
not the hardware; if it does not, that explanation is retired and the ctx-window and HIP-kernel candidates remain.

## Arm

| arm | what changes from E148 M3p | what does not |
|---|---|---|
| **M4** | drafter directory `/opt/models/staging/qwen3.6-27b-dflash-swa/`: `model.safetensors` is a symlink to the E148 file (same bytes, sha256 `e0c050b34798...`); `config.json` is z-lab revision 0919688's with `dflash_config` gaining `"causal": true, "use_swa": true, "swa_window_size": 2048` | binary (patched HEAD, sha256 `083e7efd...`), target model, `serve-amd.sh` invocation, γ (16, `MODEL.toml`), `num_drafts` default, prefix caching, harness, 206 turns |

Known imperfection, declared: `use_swa` in HEAD forces the window on **every** drafter layer, and the checkpoint's fifth layer is
full attention. HEAD has no per-layer pattern for drafters, so M4 mis-declares one layer where M3p mis-declared four. The result
is read with that in mind; a per-layer patch is a later arm if M4 moves acceptance without reaching E147's level.

## Gates

- G1: the symlink resolves to the pinned bytes (size 3,460,432,504, sha256 `e0c050b34798...`); `config.json` differs from the
  original in exactly the three added fields and a note.
- G2: server answers `/v1/models` and its "DFlash/DSpark drafter loaded" line shows `causal=Some(true), swa=Some(true)/Some(2048)`.
  Any other value is VOID (the change did not take), quoted.
- G3: as E148, plus GTT before the window recorded this time (the script gains the line E148's lacked).

## Conditions

E148's exactly, one arm, with a wall-clock cap: the harness is killed **2,400 s after it starts**. At M3p's pace 206 turns
need 4,717 s; at M2's, 1,602 s. A capped run is not VOID: it is scored on the turns completed, paired against the same turns
of M0, M1p, M2 and M3p, and the acceptance table (`tools/e148_dflash_accept.py`) is computed from the full server log either way.
If the cap fires, P2 is scored on the paired subset and said so.

## Predictions (field named)

| # | field | prediction | basis |
|---|---|---|---|
| P1 | `M4.accepted_per_step` (mean, all logged verify steps) | >= 1.0 | M3p 0.064; declaring the window is the hypothesis; llama.cpp's probe accepted 0.74 of drafts with the same lineage |
| P2 | `M4/M3p` paired mean-latency ratio | <= 0.60 | if acceptance recovers, so does speed; M3p paid a 15-token verify per accepted token |
| P3 | `M4/M2` paired ratio | 0.80-1.50 | wide: Atlas's DFlash path is unmeasured when it works on this box |
| P4 | `M4.accuracy_inline` within 0.03 of M3p (0.631) | yes | greedy verification against the target; F84 |
| P5 | cap fires (harness killed at 2,400 s) | no | P2 implies about 40 minutes for 206 turns at most |
| P6 | `M4.accepted_per_step` in the 12,288-28,671 bucket | >= 0.5 | the collapse past 8K is the sliding-window signature; if it is the ctx window instead, this stays near 0.01 while P1 may still hold |

## Decision

- P1 held: F175's cause is the config-schema mismatch (checkpoint fields the engine does not read); register it, and the routing
  note is "Atlas's DFlash needs the drafter's attention pattern written into `dflash_config`".
- P1 falsified (< 0.3): retire this explanation; the next arm is `ATLAS_DFLASH_CTX_WINDOW` (E148's candidate 2). 0.3-1.0: partial,
  both remain live.
- P6 separates the two candidates whatever P1 does.

## Out of scope

Per-layer attention patterns (a code change), gamma, the ctx window, M3s (cannot serve DFlash on HIP), re-running M3p.

## Amendment 1 (2026-09-26 11:53, written during the run, before any result was read)

G2 passed on the loader line (`causal=Some(true), swa=Some(true)/Some(2048)`), but the next line shows the effective head:
`BlockDiffusionDraftHead loaded: ... causal=true, window=Some(4096)`. The engine's window argument takes precedence over the
config's `swa_window_size` (from_weights.rs: `window_size.or_else(config)`), so M4 runs causal sliding-window attention with a
**4,096-token window, not the checkpoint's 2,048**. The arm is not changed mid-window. Predictions and bands stand as written;
the result is read as "causal + SWA at 4096". If P1 holds partially, the window value is the next single-change arm
(`--dflash-window-size 2048`, or whichever flag from_weights takes it from), not a re-run of this one.
