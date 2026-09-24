#!/usr/bin/env python3
# File: gen_ctx_probe.py
# Purpose: Generate deterministic long-context envelope-rung probes with needle re-planting
# Project: sparkbench | Date: 2026-07-11
#
# Overview: Given a corpus and a target token size, deterministically truncate
# the corpus (via binary search of word counts) to match the target REAL token
# size (measured via tokenizer endpoint, or heuristic in --dry-run). Re-plant
# needle facts and multi-hop pairs at 25/50/75% word depths. Emit a promptfoo
# YAML with the probe tests and a corpus file for the rung.

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.request
from pathlib import Path
from typing import Any, Sequence


def load_corpus(corpus_path: str) -> str:
    """
    Load corpus text from file.

    Args:
        corpus_path: path to .txt file

    Returns:
        corpus text (str)

    Raises:
        FileNotFoundError: if corpus doesn't exist
    """
    path = Path(corpus_path)
    if not path.exists():
        raise FileNotFoundError(f"Corpus not found: {corpus_path}")

    return path.read_text(encoding="utf-8")


def load_needles(needles_path: str) -> list[dict[str, Any]]:
    """
    Load needle definitions from JSON.

    Args:
        needles_path: path to .json file with [{"id": "...", "sentence": "...", "answer_variants": [...]}, ...]

    Returns:
        list of needle dicts

    Raises:
        FileNotFoundError: if needles doesn't exist
        json.JSONDecodeError: if JSON is invalid
    """
    path = Path(needles_path)
    if not path.exists():
        raise FileNotFoundError(f"Needles file not found: {needles_path}")

    return json.loads(path.read_text(encoding="utf-8"))


def count_words(text: str) -> int:
    """Count whitespace-separated words in text."""
    return len(text.split())


def estimate_tokens_heuristic(text: str, factor: float = 2.2) -> int:
    """
    Estimate token count using word * factor heuristic.

    Args:
        text: text to estimate
        factor: words -> tokens conversion factor (default 2.2 for technical text)

    Returns:
        estimated token count (int)
    """
    words = count_words(text)
    return int(words * factor)


def tokenize_endpoint(
    text: str,
    endpoint: str,
) -> int:
    """
    Query tokenizer endpoint to get exact token count.

    Args:
        text: text to tokenize
        endpoint: llama-server /tokenize endpoint (e.g. http://127.0.0.1:8100/tokenize)

    Returns:
        token count (int)

    Raises:
        urllib.error.URLError: if endpoint unreachable
        json.JSONDecodeError: if response is not JSON
        KeyError: if response missing 'tokens' key
    """
    payload = json.dumps({"content": text}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    if "tokens" not in data:
        raise KeyError(f"Tokenizer response missing 'tokens' key: {data}")

    return len(data["tokens"])


def binary_search_truncate(
    corpus: str,
    target_tokens: int,
    tokenizer_fn,
    tolerance_pct: float = 2.0,
) -> str:
    """
    Binary search corpus truncation to match target token count.

    Args:
        corpus: full corpus text
        target_tokens: desired token count
        tokenizer_fn: function(text) -> token_count
        tolerance_pct: acceptable deviation (default 2%, range +/- pct of target)

    Returns:
        truncated corpus text within tolerance of target tokens

    Raises:
        ValueError: if no truncation can reach target (corpus too short)
    """
    words = corpus.split()
    lower = 0
    upper = len(words)
    tolerance = int(target_tokens * tolerance_pct / 100)

    best_truncation = None
    best_deviation = float("inf")

    max_iterations = 50
    iteration = 0

    while lower <= upper and iteration < max_iterations:
        iteration += 1
        mid = (lower + upper) // 2
        truncated = " ".join(words[:mid])
        actual_tokens = tokenizer_fn(truncated)
        deviation = abs(actual_tokens - target_tokens)

        if deviation < best_deviation:
            best_deviation = deviation
            best_truncation = truncated

        if actual_tokens < target_tokens - tolerance:
            lower = mid + 1
        elif actual_tokens > target_tokens + tolerance:
            upper = mid - 1
        else:
            # Within tolerance
            return truncated

    if best_truncation is None:
        raise ValueError(f"Could not truncate corpus to {target_tokens} tokens (corpus too short)")

    if best_deviation > tolerance:
        print(
            f"Warning: best truncation achieved {best_deviation} tokens deviation "
            f"(target {target_tokens}, tolerance {tolerance})",
            file=sys.stderr,
        )

    return best_truncation


def plant_needles(
    corpus: str,
    needles: list[dict[str, Any]],
) -> str:
    """
    Re-plant needles at 25/50/75% word depths and return augmented corpus.

    Args:
        corpus: truncated corpus text
        needles: list of {"id": "...", "sentence": "...", "answer_variants": [...]}

    Returns:
        corpus with needles planted at target depths (needles separated by newline)

    Raises:
        ValueError: if any needle string appears multiple times in corpus after planting
    """
    if not needles:
        return corpus

    words = corpus.split()
    total_words = len(words)

    # Calculate plant positions
    positions = [
        int(total_words * 0.25),  # 25%
        int(total_words * 0.50),  # 50%
        int(total_words * 0.75),  # 75%
    ]

    # Track which needles have been used (each needle once)
    needle_by_position: dict[int, dict[str, Any]] = {}
    for i, pos in enumerate(positions):
        if i < len(needles):
            needle_by_position[pos] = needles[i]

    # Build augmented corpus: plant needles at positions
    planted_sentences = []
    for pos in sorted(positions):
        if pos in needle_by_position:
            planted_sentences.append(needle_by_position[pos]["sentence"])

    # Verify each needle appears exactly once
    full_corpus = corpus + "\n" + "\n".join(planted_sentences)
    for needle in needles:
        needle_str = needle["sentence"]
        count = full_corpus.count(needle_str)
        if count != 1:
            raise ValueError(
                f"Needle '{needle_str[:50]}...' appears {count} times in corpus (expected 1)"
            )

    return full_corpus


def generate_promptfoo_yaml(
    needles: list[dict[str, Any]],
    corpus_path: str,
    llama_server_port: int = 8100,
) -> str:
    """
    Generate promptfoo YAML for the probe.

    Args:
        needles: list of {"id": "...", "sentence": "...", "answer_variants": [...]}
        corpus_path: path to corpus file (for relative reference in YAML)
        llama_server_port: local llama-server port (default 8100)

    Returns:
        YAML string (promptfoo format with local port provider, temp 0, max_tokens 200)
    """
    yaml_lines = []

    # Provider block
    yaml_lines.append("providers:")
    yaml_lines.append("  - id: local")
    yaml_lines.append(f"    type: openai")
    yaml_lines.append(f"    config:")
    yaml_lines.append(f"      apiBaseUrl: http://127.0.0.1:{llama_server_port}/v1")
    yaml_lines.append(f"      temperature: 0")
    yaml_lines.append(f"      max_tokens: 200")
    yaml_lines.append("")

    # Load corpus for context
    corpus_text = load_corpus(corpus_path)

    # Tests: one per needle (retrieval + format)
    yaml_lines.append("tests:")
    for needle in needles:
        needle_id = needle.get("id", "unknown")
        sentence = needle.get("sentence", "")
        answer_variants = needle.get("answer_variants", [])

        # Build question and assertions for this needle
        question = f"From the corpus, what is the answer to: {sentence}? Answer with a single sentence."

        yaml_lines.append(f"  - vars:")
        yaml_lines.append(f"      corpus: |")
        for line in corpus_text.split("\n"):
            yaml_lines.append(f"        {line}")
        yaml_lines.append(f"      question: {question}")
        yaml_lines.append(f"    prompt: |")
        yaml_lines.append(f"      Context: {{{{corpus}}}}")
        yaml_lines.append(f"      Question: {{{{question}}}}")
        yaml_lines.append(f"    provider: local")
        yaml_lines.append(f"    assert:")

        # Alternation for answer variants
        if answer_variants:
            alternation = " || ".join([f'output.includes("{v}")' for v in answer_variants])
            yaml_lines.append(f"      - type: javascript")
            yaml_lines.append(f"        value: '{alternation}'")
        else:
            # Fallback: just check that output is non-empty
            yaml_lines.append(f"      - type: javascript")
            yaml_lines.append(f"        value: 'output.length > 0'")

    return "\n".join(yaml_lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate deterministic long-context envelope-rung probes with needle re-planting",
        epilog="""
Examples:
  # Real run (requires tokenizer endpoint)
  %(prog)s --corpus corpus-86k.txt --target-tokens 16000 \\
    --tokenize-endpoint http://127.0.0.1:8100/tokenize \\
    --needles needles.json --out-yaml rung-16k.yaml --out-corpus rung-16k-corpus.txt

  # Dry-run (word*2.2 heuristic, no tokenizer)
  %(prog)s --dry-run --corpus corpus-86k.txt --target-tokens 16000 \\
    --needles needles.json --out-yaml rung-16k.yaml --out-corpus rung-16k-corpus.txt
        """,
    )

    parser.add_argument(
        "--corpus",
        required=True,
        help="Path to corpus text file",
    )
    parser.add_argument(
        "--target-tokens",
        type=int,
        required=True,
        help="Target token count for truncated corpus",
    )
    parser.add_argument(
        "--tokenize-endpoint",
        default="http://127.0.0.1:8100/tokenize",
        help="Tokenizer endpoint URL (default: http://127.0.0.1:8100/tokenize)",
    )
    parser.add_argument(
        "--needles",
        required=True,
        help="Path to needles JSON file",
    )
    parser.add_argument(
        "--out-yaml",
        required=True,
        help="Output path for promptfoo YAML",
    )
    parser.add_argument(
        "--out-corpus",
        required=True,
        help="Output path for truncated corpus with planted needles",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use word*2.2 heuristic instead of tokenizer endpoint (no network call)",
    )
    parser.add_argument(
        "--heuristic-factor",
        type=float,
        default=2.2,
        help="Word->token conversion factor for dry-run (default 2.2 for technical text)",
    )

    args = parser.parse_args()

    try:
        # Load inputs
        corpus = load_corpus(args.corpus)
        needles = load_needles(args.needles)

        # Choose tokenizer function
        if args.dry_run:
            def tokenizer_fn(text: str) -> int:
                return estimate_tokens_heuristic(text, args.heuristic_factor)

            print(
                f"Dry-run mode: using word*{args.heuristic_factor} heuristic (no tokenizer endpoint)",
                file=sys.stderr,
            )
        else:
            def tokenizer_fn(text: str) -> int:
                return tokenize_endpoint(text, args.tokenize_endpoint)

        # Truncate corpus to target tokens
        print(
            f"Binary-searching truncation to {args.target_tokens} tokens...",
            file=sys.stderr,
        )
        truncated = binary_search_truncate(corpus, args.target_tokens, tokenizer_fn)
        actual_tokens = tokenizer_fn(truncated)
        print(
            f"Truncated corpus: {count_words(truncated)} words -> {actual_tokens} tokens",
            file=sys.stderr,
        )

        # Plant needles
        print(f"Planting {len(needles)} needles at 25/50/75% depths...", file=sys.stderr)
        probed_corpus = plant_needles(truncated, needles)

        # Write probed corpus
        Path(args.out_corpus).write_text(probed_corpus, encoding="utf-8")
        print(f"Wrote probed corpus: {args.out_corpus}", file=sys.stderr)

        # Generate promptfoo YAML
        yaml = generate_promptfoo_yaml(needles, args.out_corpus)
        Path(args.out_yaml).write_text(yaml, encoding="utf-8")
        print(f"Wrote promptfoo YAML: {args.out_yaml}", file=sys.stderr)

        print("Success", file=sys.stderr)

    except (FileNotFoundError, ValueError, json.JSONDecodeError, urllib.error.URLError) as e:
        print(f"Error: {e}", file=sys.stderr)
        hint = getattr(e, "hint", None)
        if hint:
            print(f"Hint: {hint}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
