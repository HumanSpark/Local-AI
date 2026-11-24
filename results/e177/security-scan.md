# E177 - manual pre-run check of the HTR engine image (2026-11-24)

Image `ghcr.io/hawgauto/vllm-htr@sha256:cbd537589cc7f2e6e9d73940d5da49a9d956ffbfd795277f54b15787284eeab5` (43.6 GB,
created 2026-11-17), pulled by the card's pinned digest with rootless podman. A hand-run version of the planned download
gate, checked against the T3 Code signatures (scouting/t3code/REPORT.md). Scope: the HTR-specific code
(`/opt/vllm-htr`, its `htr*` Python packages) plus vLLM's own telemetry switch; not the whole 43 GB (torch, ROCm, vLLM).

- Runs as UID 1000 (not root); entrypoint `/opt/venv/bin/vllm serve`.
- URLs in the HTR code: only `http://127.0.0.1` (the launcher's local health/warm-up POST to `/v1/completions`).
- No references to other tools' credential or identity files, no analytics SDKs or ingest keys, no base64/exec/eval
  patterns in the HTR packages.
- vLLM usage statistics are default-ON upstream (reports to vLLM's stats server); this image sets
  `VLLM_NO_USAGE_STATS=1`, and also `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, so it neither phones home nor
  fetches from Hugging Face. We will still pass `VLLM_NO_USAGE_STATS=1 DO_NOT_TRACK=1` explicitly at run time.
- Run with the card's hardening: `--security-opt no-new-privileges`, model mounted read-only, port bound to 127.0.0.1.

Verdict: nothing found that blocks a first start. Limits: static reading of the HTR layer only; no network capture yet.
