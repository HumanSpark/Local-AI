# Smoke Test Usage Notes

Pulled-forward integration smoke: 3-way provider validation (local, OpenRouter, Mistral).
Test suite: 2 deterministic tests (extraction + format-constraint).
Date: 2026-07-11

## Test Results Summary

| Provider | Model | Pass | Fail | Error | Prompt Tokens | Completion Tokens | Total Tokens | Cost |
|----------|-------|------|------|-------|---|---|---|---|
| **Local** | Qwen3-30B-A3B-Q4_K_M | 2 | 0 | 0 | 310 | 10 | 320 | Free |
| **OpenRouter** | meta-llama/llama-3.1-8b-instruct | 1 | 1 | 0 | 300 | 7 | 307 | $2.49e-06 (measured) |
| **Mistral** | mistral-small-2506 | 2 | 0 | 0 | 315 | 10 | 325 | ~$7.87e-06 (est.) |

## Test-by-Test Breakdown

### Local: Qwen3-30B-A3B-Q4_K_M
- **smoke-extract-contract-fee**: PASS - correctly extracted "£18,750"
- **smoke-format-one-word**: PASS - responded with "True"
- Latency: <1s per test
- Token usage per test: ~160 tokens (prompt ~155, completion ~5)

### OpenRouter: meta-llama/llama-3.1-8b-instruct
- **smoke-extract-contract-fee**: PASS - correctly extracted "£18,750"
- **smoke-format-one-word**: FAIL - responded with "Yes, London is located in England." (multi-word)
- Latency: ~777ms for passing test, ~150ms for failing test
- Token usage:
  - Extraction test: 32 prompt + 3 completion = 35 tokens
  - Format test: ~268 prompt + 4 completion = ~272 tokens
  - Cost measured: $2.49e-06 total (0.0e0/prompt, 2.4e-7/completion tokens)

### Mistral: mistral-small-2506
- **smoke-extract-contract-fee**: PASS - correctly extracted "£18,750"
- **smoke-format-one-word**: PASS - responded with "True"
- Latency: <1s per test
- Token usage per test: ~160 tokens (prompt ~158, completion ~5)
- Cost estimate: (315+10 tokens) * API pricing (OpenRouter lists ~7.87e-06/token)

## Cost Projection Notes

- **Local**: No API cost (runs on sparknax, electricity only - not quantified for this exercise)
- **OpenRouter**: Measured cost from first run = $2.49e-06. Smoke scale: 2 requests. Projected Task 8 scale (3 suites × 3-4 models): ~15-20 requests → ~$3.7e-05 to $5e-05 (well under $150 cap)
- **Mistral**: Pricing ~same tier as OpenRouter cheap models. Projected: similar magnitude to OpenRouter

## Framework Integration Verified

✓ Local llama-server lifecycle (start, health-poll, graceful SIGTERM, cleanup)
✓ OpenRouter openai-compatible endpoint authentication and model selection
✓ Mistral openai-compatible endpoint authentication and model selection
✓ promptfoo config override for cloud providers (YAML temp file, working from suite directory)
✓ Token usage extraction from promptfoo JSON output
✓ File reference resolution (file:// refs in tests work correctly)

## Deviations & Findings

**F-ready**: Format-constraint test is borderline - OpenRouter's Llama 3.1 8B violates the "exactly one word" discipline, returning a full sentence. This is expected model behavior (instruct models often default to conversational); the test is working as designed. Qwen3 and Mistral small both comply (both return single-word or minimal responses).

## Next Steps (Task 3 onwards)

1. Pin cloud comparators (frontier + cheap on OpenRouter; mistral-large-2512 on Mistral)
2. Calculate full campaign spend projection from this smoke usage
3. Run capability suites (summarisation, instruction-following, long-context) across all models
4. Collect raw results and publish findings
