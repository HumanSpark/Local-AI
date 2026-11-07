# File: tools/sparkrouter_discovery.py
# Purpose: Read the live serving identity of the production llama-server, so a client is
#          configured from what is actually running rather than from notes that have drifted.
# Project: sparkbench | Date: 2026-08-30
#
# Overview: Two public functions, both pure - they take payloads and return a dict, and never
# open a socket, so they are testable without a server.
#   parse_serving_flags(cmdline)  splits a llama-server command line into a flag map. A flag
#       followed by a non-flag token maps to that token; a flag followed by another flag (or
#       by nothing) maps to True; the leading binary path is not a flag.
#   describe(models, props, cmdline)  merges GET /v1/models, GET /props and the process
#       command line into the one dict a client needs, including the `openai/` model string
#       Aider wants and a `consistent` flag saying whether props and the process agree.
#
# `consistent` exists because props and `ps` are two rulers over the same fact. A config that
# says one thing while the process serves another is the failure this file is here to surface,
# so disagreement is reported rather than silently resolved in favour of either side.
#
# Provenance: the first implementation was written by the local Qwen3-30B-A3B workhorse through
# Aider against the read-only test (E90, T2, 13 of 13 assertions green on the first attempt).
# Its raw output is kept verbatim at results/raw/e90/T2-model-output-sparkrouter_discovery.py;
# this file is that logic with 26 ruff findings cleaned up. See results/e90-aider-workflow.md.
from __future__ import annotations

from typing import Any


def parse_serving_flags(cmdline: str) -> dict[str, str | bool]:
    """Split a llama-server command line into a flag map.

    Args:
        cmdline: the full command line, as `ps -o args= -C llama-server` prints it.

    Returns:
        Flag name to its value, or True for a flag that carries none.

    Raises:
        ValueError: the command line is empty or whitespace only.
    """
    if not cmdline.strip():
        raise ValueError(
            "empty command line, so no serving flags could be read. "
            "hint: check `ps -o args= -C llama-server` actually matched a process"
        )

    tokens = cmdline.split()
    flags: dict[str, str | bool] = {}

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not token.startswith("-"):
            i += 1  # the binary path, or a value already consumed below
            continue
        following = tokens[i + 1] if i + 1 < len(tokens) else None
        if following is None or following.startswith("-"):
            flags[token] = True
            i += 1
        else:
            flags[token] = following
            i += 2
    return flags


def describe(models: dict[str, Any], props: dict[str, Any], cmdline: str) -> dict[str, Any]:
    """Merge the live catalogue, server props and process command line into one description.

    Args:
        models: the body of `GET /v1/models`.
        props: the body of `GET /props`.
        cmdline: the llama-server process command line.

    Returns:
        model_id, n_ctx, n_ctx_train, build_info, total_slots, aider_model, flags,
        slots_explicit (True only when -np is set explicitly, which disables --kv-unified
        and quarters per-conversation context - F108), and consistent.

    Raises:
        LookupError: the catalogue is empty, so nothing is being served.
    """
    entries = models.get("data")
    if not entries:
        raise LookupError(
            "the model catalogue is empty, so no model is resident. "
            "hint: check GET /v1/models on the serving port, and that llama-server "
            "finished loading its weights"
        )

    entry = entries[0]
    meta = entry["meta"]
    flags = parse_serving_flags(cmdline)

    return {
        "model_id": entry["id"],
        "n_ctx": meta["n_ctx"],
        "n_ctx_train": meta["n_ctx_train"],
        "build_info": props["build_info"],
        "total_slots": props["total_slots"],
        "aider_model": f"openai/{entry['id']}",
        "flags": flags,
        "slots_explicit": "-np" in flags,
        "consistent": flags.get("-m") == props["model_path"],
    }
