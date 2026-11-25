# E179 - HTR v0.2.5: same model, newer engine release (prereg, 2026-11-25)

## In plain English

The community HTR engine for production's model put out a new release on 24 Nov with 18 new routines written for
this chip. The model files are unchanged. Our test of the previous release (E177) found it 23% slower at writing than
production's Halogen engine and 37% slower at reading a long prompt, while solving 6 of 10 large changes against
production's 5. This re-test asks whether the new release closes the speed gap without losing that quality.

## Setup (only the image changes from E177)

- Image `ghcr.io/hawgauto/vllm-htr@sha256:daa6b2847bf9678e2de39b8b216105ffe13313e50db889f002f5f918e581d193`
  (htr-v0.2.5, published 2026-11-24T21:13:46Z); E177 used `sha256:cbd53758...` (v0.2.4).
- Model unchanged: hstolte/Qwen3.8-Flash-Next-HTR Htr5Core, the files verified for E177.
- Speed leg: tools/run_e179_htr025.sh, identical to E177's speed leg (tools/e163_speed.py, the E139 prompts, 40,960
  context, thinking auto-off), plus Halogen timed live the same night.
- Bank leg: the E167 hard bank on arm HT with `E154_HTR_IMG` set to the v0.2.5 digest, 3,600 s per task, podman,
  one attempt. **New tasks start only until 08:00 local** (owner: done by about 9 a.m.); tasks not started are run in
  a later window and the partial count is reported as partial.
- Over 60 GiB: run overnight on the owner's instruction (2026-11-25 01:27: "run the risky tests so that they should be
  complete by about 9 a.m."). Committed and pushed before and after each risky leg.

## Predictions (each names its field)

- P1: `summary.D1500.decode_tps` for HTR v0.2.5 is at least 49.0 (E177: 47.76; the maker reports +5.7% single-request).
- P2: `summary.D1500.decode_tps` stays below Halogen's same-night `summary.D1500.decode_tps`.
- P3: `summary.P32K.prefill_tps` is within 5% of E177's 923.6 (the release claims no prefill change).
- P4: on the tasks the bank leg completes, `passed` matches E177's result on at least 80% of them.

Image check before first start: the same static check as results/e177/security-scan.md, written to
results/e179/security-scan.md.
