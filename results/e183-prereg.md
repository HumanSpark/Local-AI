<!--
# File: results/e183-prereg.md
# Purpose: Pre-registration for E183 - does stock llama.cpp get DSpark's speed-up on Inkling-2-Mini without an experimental engine?
# Project: sparkbench | Date: 2026-11-26
#
# Overview: Written before any run. Spike from scouting/inference-optimisation-skill/REPORT.md (addendum 2026-11-24).
# Runner tools/run_e183_dspark.sh. Files restored from the lanhost archive and sha256-verified against MANIFEST E172
# (results/e183/restore.log, both OK).
-->

## In plain English

In E172, a small helper model called DSpark made Inkling about 2-2.5x faster at writing answers. That was only through
two experimental engines (AMD Loom and the CIRU runtime). This spike checks whether plain, stock llama.cpp gets the same
gain with the same helper file. If it does, the speed-up is available without an experimental engine.

## Configuration

- llama.cpp `b671865c7` (master 2026-11-26), Vulkan, built in var/engines/llama-b671865c7 (results/e183/build.log).
  `--spec-type draft-dspark` is in its --help.
- Target: unsloth `Inkling-2-Mini-UD-Q4_K_XL.gguf` (sha256 e62d463c...). Draft: `dspark-Inkling-2-Mini-Q8_0.gguf`
  (2ec78510...).
- Every arm: `-c 65536 -np 1 -fa on -ngl 999 --jinja`, as E172 IM.
- Arms: N0 no draft; D3 `--spec-type draft-dspark -ngld 999 --spec-draft-n-max 3` (llama.cpp default length);
  D7 the same with `--spec-draft-n-max 7` (CIRU card's K=7).
- Ruler: tools/e163_speed.py (E139 prompts, client-timed, thinking off via effort0), run twice per arm (r1, r2).

## Predictions (field named for each)

- P1 `D1500.decode_tps` for the better of D3 and D7 is >= 1.5x N0. DSpark's gain carries over to stock llama.cpp.
- P2 `P32K.decode_tps` for the better draft arm is lower relative to N0 than its D1500 gain. Speculative gains shrink
  after a long context.
- P3 `D1500.decode_tps` N0 is within 10% of E172 IM (26.59), the same file and flags on build 94f3af3d0.
- P4 `P8K.prefill_tps` for the draft arms is within 10% of N0. Drafting should not change prefill.
- A gap counts only if it exceeds the r1/r2 spread (memory speed-claims-need-spread).

## Known risk (scout, 2026-11-26)

llama.cpp issue #23126 reports draft-model speculation on Vulkan unified memory running far slower when `seq_rm` is
missing. If the draft arms come out slower than N0, that issue is the first suspect. It would be a finding, not a
reason to drop the arms.

## Amendment A1 (2026-11-26 14:16Z, before any measurement)

Attempt 1 (14:10Z) loaded nothing: all three arms failed at model load with `check_tensor_dims: tensor
'blk.24.attn_q.weight' not found`. The file used, `Inkling-2-Mini-UD-Q4_K_XL.gguf` (e62d463c...), is unsloth's
Loom-layout file (E172 arm IL). Mainline llama.cpp needs unsloth's `Mainline_Support/Inkling-2-Mini-UD-Q4_K_XL.gguf_file`
(17,629,760,736 B, sha256 e6427665..., MANIFEST E172), which is what E172 arm IM ran. Restored from the lanhost
archive and verified (results/e183/restore2.log). Attempt 2 uses it for every arm; P3 is now a like-for-like
comparison with IM (same file, same flags, newer build). Attempt-1 server logs kept as raw/attempt1-*.serverlog.
Open risk: the DSpark draft was only ever run beside the Loom-layout target; if llama.cpp refuses the pair, D3/D7
fail at load and that is the finding.

## Amendment A2 (2026-11-26 14:27Z, after N0, before any draft-arm number)

r2 repeats r1's prompts on the same server, so llama-server's prompt cache served them (N0 r2 P8K `cached_tokens`
7,982 of 7,986; prefill 22,460 tok/s). Decode is unaffected (N0 D1500 decode r1 28.86, r2 28.85). Scoring therefore
uses: decode fields from r1 and r2 (spread = |r1 - r2|); prefill and TTFT fields from r1 only (each arm restarts the
server, so every r1 is cache-cold). P4 is scored on r1. No re-run: the prefill question is answered by r1.

## Amendment A3 (2026-11-26 ~14:33Z, before any draft-arm measurement)

Attempt 2 measured N0 (r1, r2) but both draft arms failed at load: `tensor 'markov_w1.weight' has wrong shape;
expected 256, 200058, got 256, 201024`. The E172 draft is the Loom-layout file (unsloth now files it under
`Old_Support`). unsloth added a mainline draft on 2026-11-23: `Mainline_Support/dspark-Inkling-2-Mini-Q8_0.gguf_file`
(503,889,952 B, sha256 3da00cf7..., MANIFEST E183, verified on arrival). Attempt 3 runs ARMS="D3 D7" with it; N0 stands
from attempt 2 (same build, file and flags; each arm restarts the server, so no cross-arm cache). Finding already
banked: the E172 draft cannot be used on stock llama.cpp; only unsloth's later mainline file can.
