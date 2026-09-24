# File: tools/sparkrouter_discovery.py
# Purpose: Read the live serving identity from llama-server metadata and command line.
# Project: sparkbench | Date: 2026-08-30
#
# Overview: Implements the contract pinned by tests/test_sparkrouter_discovery.py.
# The helpers are pure: they accept already-fetched payloads and a command line,
# and return a single description dict for clients.

from __future__ import annotations

import shlex
from typing import Any


def parse_serving_flags(cmdline: str) -> dict[str, str | bool]:
    """Parse a llama-server command line into a flag map.

    Flags followed by a non-flag token take that token as a string value.
    Flags followed by another flag, or by nothing, map to True.
    """
    if not cmdline.strip():
        raise ValueError("hint: provide a non-empty llama-server command line")

    try:
        tokens = shlex.split(cmdline)
    except ValueError as exc:
        raise ValueError(f"hint: could not tokenize command line: {exc}") from exc

    if not tokens:
        raise ValueError("hint: provide a non-empty llama-server command line")

    if not tokens[0].startswith("-"):
        tokens = tokens[1:]

    flags: dict[str, str | bool] = {}
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not token.startswith("-"):
            i += 1
            continue

        if i + 1 < len(tokens) and not tokens[i + 1].startswith("-"):
            flags[token] = tokens[i + 1]
            i += 2
        else:
            flags[token] = True
            i += 1

    return flags


def describe(models: dict[str, Any], props: dict[str, Any], cmdline: str) -> dict[str, Any]:
    """Build the one dict a client needs from /v1/models, /props, and ps args."""
    data = models.get("data") or []
    if not data:
        raise LookupError("hint: the model catalogue is empty; start llama-server with a model")

    model = data[0]
    model_id = model.get("id")
    meta = model.get("meta") or {}

    flags = parse_serving_flags(cmdline)
    model_path_flag = flags.get("-m")
    props_model_path = props.get("model_path")
    consistent = isinstance(model_path_flag, str) and props_model_path == model_path_flag

    return {
        "model_id": model_id,
        "n_ctx": meta.get("n_ctx"),
        "n_ctx_train": meta.get("n_ctx_train"),
        "build_info": props.get("build_info"),
        "total_slots": props.get("total_slots"),
        "aider_model": f"openai/{model_id}",
        "flags": flags,
        "slots_explicit": "-np" in flags,
        "consistent": consistent,
    }
