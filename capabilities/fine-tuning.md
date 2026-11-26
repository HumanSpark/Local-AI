# Fine-tuning (r6.4)

Training a model on the box on your own examples.

**Against the frontier:** Not comparable: cloud models can't be trained on this machine. ([how it compares](../FRONTIER.md))

## What works best now

- **In production:** nothing yet.

## Also tried

| Setup | Engine | Where it stands | Why |
|---|---|---|---|
| House-style LoRA on the July model (trained on the box) | llama.cpp | tried | Teaches the firm's tone reliably; does not make drafts send-ready. |

## The experiments behind this, best results first

| Experiment | Date | Result | What happened | Evidence |
|---|---|---|---|---|
| House-style fine-tune trained on the box (FT1) | 2026-07-13 | works, with caveats | Teaches tone reliably; does not lift send-readiness. | [FINDINGS.md#f37-2](../FINDINGS.md#f37-2) |

