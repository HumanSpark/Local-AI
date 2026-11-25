# E179 - pre-run check of the HTR v0.2.5 engine image (2026-11-25)

Image `ghcr.io/hawgauto/vllm-htr@sha256:daa6b2847bf9678e2de39b8b216105ffe13313e50db889f002f5f918e581d193` (43.6 GB,
created 2026-11-24 15:05 -0600), pulled by digest with rootless podman. Same scope and method as
results/e177/security-scan.md: the HTR code under `/opt/vllm-htr` (271 files, 32 native kernel binaries) plus the
image's environment, read from the mounted image without running it.

- Runs as UID 1000; entrypoint `/opt/venv/bin/vllm serve` (unchanged from v0.2.4).
- Environment sets `VLLM_NO_USAGE_STATS=1`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`.
- URLs in the HTR code: only documentation links (GitHub HawgAuto/vllm-htr and HTR, the Hugging Face model card) and
  `http://127.0.0.1` (the launcher's local health check and warm-up). No other hosts.
- URLs inside the native binaries (`strings`): the ROCm LLVM repository and pybind11 documentation only.
- Pattern search (base64 decode, exec/eval, raw sockets, HTTP POST, credential or identity paths, analytics SDKs):
  three hits, all benign - PyTorch's `.eval()` in `python/htr/lmhead.py` and `ast.literal_eval` in two tests.

Verdict: nothing found that blocks a first start. Run with the same hardening as E177 (no-new-privileges, model
read-only, port on 127.0.0.1, usage statistics off). Limits: static reading of the HTR layer only; no network capture.
