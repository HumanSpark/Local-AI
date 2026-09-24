# Control: does `--jinja` change tool-use behaviour on this build? (2026-07-17)

# File: results/tool-use/jinja-default-control.md
# Purpose: The with/without-`--jinja` control that F39's original tool-use claim needed and never had.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: F39 (2026-07-16) claimed the production gateway could not do tool use because its systemd
# unit omitted `--jinja`. That was an inference from tooluse_harness.py's docstring, not a measurement -
# the pre-fix config was never exercised. This is the control that should have run first. It refutes
# the claim: `--jinja` defaults to ENABLED on this build, so the flag was a no-op and tool use worked
# all along. F39's tool-use half is retracted; its `-c` / KV half stands (measured, unaffected).

## The question

Does serving WITHOUT `--jinja` disable structured tool calls on this stack?

## Build under test

```
llama-server --version -> version: 200 (067de93)
--jinja, --no-jinja    whether to use jinja template engine for chat (default: enabled)
```

The help text already answers it: the default is **enabled**. `--jinja` on the command line makes an
existing default explicit; it does not turn anything on.

## Method

Same model (Qwen3-30B-A3B-Instruct-2507-Q4_K_M), same request, two endpoints, one difference:

| Endpoint | Flags | Role |
|---|---|---|
| 127.0.0.1:8402 | `-c 8192` (no `--jinja`) | reproduces the PRE-F39 production config |
| 127.0.0.1:8400 | `-c 49152 --jinja` | current production |

Request: a single `create_document` function-calling task via `/v1/chat/completions`, `tool_choice:
auto`, temperature 0. Scored on the only thing that matters here - did the server return a structured
`tool_calls` object, or did it fall back to prose?

## Result

| Endpoint | Structured `tool_calls`? | Function selected |
|---|---|---|
| WITHOUT `--jinja` (pre-F39 production) | **YES** | `create_document` |
| WITH `--jinja` (current production) | **YES** | `create_document` |

Identical behaviour. The flag is a no-op on this build.

## Conclusion

**F39's claim that "F38's tool-use capability was unavailable in production" is FALSE and is
retracted.** Production had the jinja path by default and could always do tool use. What F39 got
right is unaffected: the missing `-c` really did allocate 262144 tokens of KV (19.70 GiB reclaimed
by fixing it, measured), and the three-writer flag problem was a real latent bug - the next model
swap would have silently reverted `-c`.

## Why the error happened, and the rule it produces

`tools/tooluse_harness.py` says its endpoint "must be served with `--jinja`". That is a statement
about how the harness invokes a server, not evidence about what a server does without the flag. It
was read as the latter. The 2026-07-16 "proof run" then measured only the FIXED config (7/7 valid
tool calls) and was reported as though it demonstrated a restoration - but a passing test on the new
config says nothing about the old one.

The rule: **comparing two configurations means running both.** Asserting that a config difference
matters is itself a claim requiring measurement, and a flag's presence in a command line is not
evidence of its effect - a default can make it a no-op. This is the same suspect-the-ruler discipline
that caught the judge-truncation and letterhead-leakage artifacts in F34, applied one level up: the
ruler here was a docstring.
