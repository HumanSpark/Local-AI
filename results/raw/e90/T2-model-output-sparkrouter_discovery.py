# File: tools/sparkrouter_discovery.py
# Purpose: Extract serving identity and configuration from a running llama-server process.
# Project: sparkbench | Date: 2026-08-30
#
# Overview: Implements two public functions:
#   parse_serving_flags(cmdline: str) -> dict[str, str | bool]
#       Splits a llama-server command line into a flag map.
#       - A flag followed by a non-flag token maps to that token as a string.
#       - A flag followed by another flag (or nothing) maps to True.
#       - The leading binary path is not considered a flag.
#       - An empty or whitespace-only cmdline raises ValueError with 'hint' in message.
#
#   describe(models: dict, props: dict, cmdline: str) -> dict
#       Returns a comprehensive dict of serving configuration and identity.
#       Keys include: model_id, n_ctx, n_ctx_train, build_info, total_slots,
#       aider_model (model_id prefixed with 'openai/'), flags (parsed flag map),
#       slots_explicit (True if -np is present), and consistent (True if props['model_path']
#       matches -m value from cmdline).
#       Raises LookupError with 'hint' in message if models['data'] is empty.

from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple, Union
from pathlib import Path


def parse_serving_flags(cmdline: str) -> Dict[str, Union[str, bool]]:
    """
    Parse a llama-server command line into a dictionary of flags and their values.

    Args:
        cmdline: A string representing the full command line used to start the server.

    Returns:
        A dictionary mapping each flag to its value (string) or True if it's a bare flag.

    Raises:
        ValueError: If the cmdline is empty or contains only whitespace.
    """
    if not cmdline or not cmdline.strip():
        raise ValueError("Empty or whitespace-only command line. Hint: check the process args.")

    # Split the cmdline into tokens, preserving spaces around flags
    tokens = cmdline.strip().split()
    flags: Dict[str, Union[str, bool]] = {}

    i = 0
    while i < len(tokens):
        token = tokens[i]
        if not token.startswith("-"):
            # Skip the binary path (first non-flag token)
            i += 1
            continue

        # If this is the last token, it's a bare flag
        if i + 1 >= len(tokens):
            flags[token] = True
            break

        next_token = tokens[i + 1]
        # If the next token starts with "-", it's another flag, so this is a bare flag
        if next_token.startswith("-"):
            flags[token] = True
        else:
            # Otherwise, it's a value
            flags[token] = next_token
            i += 1  # Skip the next token

        i += 1

    return flags


def describe(models: Dict[str, Any], props: Dict[str, Any], cmdline: str) -> Dict[str, Any]:
    """
    Describe the current serving configuration and identity.

    Args:
        models: A dictionary containing the models list, including 'data' with model info.
        props: A dictionary containing server properties like 'model_path', 'build_info', 'total_slots'.
        cmdline: The full command line used to start the server.

    Returns:
        A dictionary with keys:
            - model_id: The path of the served model.
            - n_ctx: The context length.
            - n_ctx_train: The training context length.
            - build_info: The build info string.
            - total_slots: The total number of slots.
            - aider_model: The model_id prefixed with 'openai/'.
            - flags: The parsed flag map from cmdline.
            - slots_explicit: True if -np is present in cmdline.
            - consistent: True if props['model_path'] matches the -m value from cmdline.

    Raises:
        LookupError: If models['data'] is empty.
    """
    if not models.get("data"):
        raise LookupError("Empty model catalogue. Hint: check the server's /v1/models endpoint.")

    model_data = models["data"][0]
    model_id = model_data["id"]
    n_ctx = model_data["meta"]["n_ctx"]
    n_ctx_train = model_data["meta"]["n_ctx_train"]
    n_params = model_data["meta"]["n_params"]
    size = model_data["meta"]["size"]
    ftype = model_data["meta"]["ftype"]

    build_info = props["build_info"]
    total_slots = props["total_slots"]
    model_path = props["model_path"]

    # Parse the flags
    flags = parse_serving_flags(cmdline)

    # Determine if slots are explicit
    slots_explicit = "-np" in flags

    # Check consistency between props and cmdline
    m_value = flags.get("-m")
    consistent = m_value is not None and m_value == model_path

    # Construct the aider model string
    aider_model = f"openai/{model_id}"

    return {
        "model_id": model_id,
        "n_ctx": n_ctx,
        "n_ctx_train": n_ctx_train,
        "build_info": build_info,
        "total_slots": total_slots,
        "aider_model": aider_model,
        "flags": flags,
        "slots_explicit": slots_explicit,
        "consistent": consistent,
    }
