# Qwen3-TTS-12Hz-1.7B-CustomVoice - W3 T11 Stage-2 results (2026-07-25)

**Engine:** `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`, rev `0c0e3051`, Apache-2.0 on code AND weights.
Discrete multi-codebook LM + 12 Hz speech tokenizer. Container built FROM the cached
`rocm/pytorch:rocm7.2.3` base; `attn_implementation="sdpa"` (FlashAttention 2 has no gfx1151 build).
Stock built-in timbres only - the two English natives, **Ryan** and **Aiden**. No voice cloning.
GPU: sparkmax gfx1151 (Radeon 8060S), ROCm 7.2.4, with the production Qwen3-30B LLM resident
throughout (sparkrelay `{"state":"serving"}` for the whole run).

## Headline

**Serves cleanly on ROCm - 18/18 renders OK across both voices, zero failures, zero retries.** At
**RTF ~0.102x it is 2.3x faster than Fish s2-pro but still ~9.8x slower than realtime**, and on
throughput alone it does not solve the backfill problem.

| Engine | RTF | Projected GPU-hours for 7 dark + 139 backfill posts |
|---|---|---|
| Kokoro-82M (incumbent, CPU) | ~8x | ~1 |
| F5-TTS (research reference only) | 0.60x | ~13 |
| **Qwen3-TTS 1.7B CustomVoice** | **0.102x** | **~78** |
| Fish s2-pro | 0.044x | ~180 |

Throughput is one axis of seven. **Quality is entirely unmeasured** and is what this engine is
really in the field for - the T13 blind listening pack decides it. Model load takes 169s (one-time
per process, not per request).

## Per-excerpt (mean of the two voices)

| Excerpt | Words | Audio s | Wall s | RTF |
|---|---|---|---|---|
| 01-first-person-argument | 43 | 13.84 | 136.0 | 0.1018 |
| 02-technical-acronym-density | 40 | 25.56 | 256.1 | 0.1001 |
| **03-numbers-and-percentages** | 62 | 27.56 | 98.4 | **0.2838** |
| 04-quotation | 12 | 4.64 | 44.8 | 0.1035 |
| 05-short-emphatic | 3 | 1.56 | 15.8 | 0.0989 |
| 06-long-multiclause | 53 | 23.48 | 228.4 | 0.1028 |
| **07-list-as-prose** | 59 | 34.08 | 162.5 | **0.2100** |
| 08-unusual-names | 20 | 7.92 | 76.9 | 0.1031 |
| 09-inline-emphasis | 34 | 16.76 | 162.7 | 0.1031 |

The two voices track each other almost exactly (per-excerpt RTF agrees to within ~2% on 7 of 9),
so voice choice is not a throughput variable here.

## RTF is FLAT with length - a mid-run hypothesis, tested and REFUTED

While the run was still in flight, an interim reading of the first three excerpts suggested RTF was
improving with audio length (0.099x on a 1.7s clip vs 0.258x on a 29s clip), which would have meant
a large fixed per-request overhead - and would have implied this short-excerpt corpus systematically
understates engines on the real long-form workload.

**The full 18 renders refute it.** Excluding the two outlier excerpts below, RTF is
**0.1019x with a standard deviation of 0.0020 - CV 2.0% - across audio durations from 1.44s to
27.76s**, a 19x length range. A 1.44s clip (0.0991x) and a 27.76s clip (0.0975x) are
indistinguishable. There is no measurable fixed overhead in the per-request path.

The apparent trend was an artefact of a 3-point sample that happened to include excerpt 03, which is
an outlier for an unrelated reason. Recorded here because the wrong version was stated aloud before
the data was in, and because it is the standing lesson: **do not read a trend off a partial run.**

## UNEXPLAINED: two excerpts run 2.4x faster, reproducibly

Not dismissed, not waved through - named and quantified, per the no-hand-waved-discrepancies rule.

- **14 of 18 renders: RTF 0.1019 (sd 0.0020, CV 2.0%)** - extremely tight.
- **4 of 18 renders: RTF 0.2469** - excerpts **03-numbers-and-percentages** and
  **07-list-as-prose**, on **both** voices. **2.4x faster.**

It is reproducible and text-dependent, not noise: the same two excerpts, on two independent voices,
land in the same fast mode. The distribution is bimodal, not a spread - nothing sits between 0.104
and 0.205.

Two candidate explanations were tested against the data and **both fail**:
- *"More audio produced per word"* - audio-per-word varies only 2.0x (CV 21.2%) and does not line up
  with the fast pair (excerpt 02 has the HIGHEST audio-per-word at 0.639 and is in the SLOW group).
- *"Constant work per word, ratio moved"* - wall-per-word varies 4.0x (CV 35.8%), so it is not flat
  either.

Strongest surviving hypothesis, **untested**: 03 (62 words) and 07 (59 words) are the two longest
excerpts by word count, and `qwen-tts` exposes batch inference as a first-class feature. An internal
chunking threshold near ~55 words that switches long inputs onto a batched generation path would
produce exactly this bimodal 2.4x step. That is a guess about a mechanism, not a finding.

**TODO: resolve the bimodal RTF step before Qwen3-TTS is scored at T14.**
`Why:` if a batched path is 2.4x faster and is reachable for ALL inputs, this engine's real
throughput is ~0.25x not ~0.10x - a 2.4x error in the headline number that feeds the selection, and
~78 GPU-hours becomes ~32. `Trigger:` this run (2026-07-25); the 4-of-18 bimodal split above.
`How:` log generated token/chunk counts per request in `run_qwen3tts.py` (it currently records
neither - the gap that prevented resolving this in-run) and re-render 03 and 06 with chunking forced
on and off.

## Operational

- **Coexistence fine.** The resident Qwen3-30B production LLM was never paused; the relay answered
  `{"state":"serving"}` throughout and GTT returned to the 20.24 GiB LLM-only baseline on teardown.
- **Serving is batch-in-container**, not an HTTP server (same shape as F5-TTS) - the engine has no
  persistent server mode in this route.
- **No crashes, no OOM, no MIOpen-related failures.** Contrast Fish, which needed a bespoke
  container and still only reached 0.044x.

## The MIOpen workspace signature appears here too

Qwen3-TTS emits the **same** `Solver <GemmFwdRest> ... provided ptr: 0 size: 0` workspace-rejection
warnings as Fish (19.6 MB to 147 MB required, all refused), despite a completely different
architecture. So the signature is a PyTorch-on-ROCm-wide behaviour on this box, **not** a property of
Fish's DAC decoder.

Critically, **its presence does not predict throughput**: Fish emits it at 0.044x, Qwen at 0.102x -
2.3x apart. It is a tax both pay, not the thing that separates them. This *reinforces* F47's core
claim (architecture decides, not the accelerator) rather than adding a competing one.

Whether F5-TTS (0.60x, the fastest GPU engine) also emits it is **UNKNOWN** - its captured log is a
15-line tail, not full stderr. Not claimed either way.

## Evidence

- `metrics.json` - 18 records, lib_bench shape
- `audio/` - 18 WAVs (gitignored; feeds the T13 blind listening pack)
- Engine: `qwen3-tts/{fetch_qwen3tts.py, Dockerfile.qwen3tts, run_qwen3tts.py}`
- Provenance: `manifests/MANIFEST.md` (rev + both LFS sha256 oids, verified before first use)
