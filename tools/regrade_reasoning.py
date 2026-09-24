#!/usr/bin/env python3
# File: regrade_reasoning.py
# Purpose: Extract content from reasoning-model outputs and re-grade dual views (as-emitted vs content-extracted)
# Project: sparkbench | Date: 2026-07-11
#
# Overview: Reasoning models (MiniMax, Qwen3.5-397B local; Mistral magistral cloud)
# contaminate their outputs with thinking/reasoning text. This tool extracts the
# actual answer from three types of contamination and re-grades both views.
# Output: per-suite tables showing as-emitted scores, content-extracted scores,
# and any unextractable outputs (graded as-emitted with notation).

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional, TypedDict


class ExtractionResult(TypedDict):
    """Result of extracting content from reasoning output."""
    as_emitted: str
    content_extracted: str
    extraction_type: str  # 'local_thinking', 'magistral_partial', 'magistral_incomplete', 'unextractable'
    thinking_boundary: Optional[int]  # Index where thinking ends


def extract_local_thinking(output: str) -> ExtractionResult:
    """
    Extract answer from local models (MiniMax, Qwen397B) that emit "Thinking:" prose.

    Pattern: output starts with "Thinking:" or "Thinking Process:", followed by
    verbose internal reasoning/planning, then the actual structured answer begins.

    Boundary detection: first line that starts with structured-content markers:
    numbered items (1., 2., ...), bullet points (-, *), quoted text ("), or bold
    markdown (**). Everything before that line is thinking; everything from that
    line onward is the answer.

    Failure modes:
    - Output is pure thinking with no structured content (rare; marked unextractable)
    - Boundary markers in the thinking section (misjudged; accept as edge case)
    """
    if not output.strip().startswith(("Thinking:", "Thinking Process:")):
        return ExtractionResult(
            as_emitted=output,
            content_extracted=output,
            extraction_type="no_thinking_prefix",
            thinking_boundary=None,
        )

    lines = output.split('\n')
    thinking_end_idx = 0

    # Find the first line that looks like structured answer content
    for i, line in enumerate(lines):
        stripped = line.strip()

        # Skip empty lines and the thinking header itself
        if not stripped or stripped in ("Thinking:", "Thinking Process:"):
            continue

        # Check if this line starts with structured-content markers
        if any(stripped.startswith(marker) for marker in ['1.', '2.', '3.', '-', '*', '"', '**']):
            # Found the boundary - structured content begins here
            thinking_end_idx = i
            break

        # Also check for longer thinking content (paragraphs starting with letters)
        # but if we see a line that looks like real output (contains quotes, structured text),
        # treat it as answer start
        if stripped and (
            stripped.startswith('**') or
            re.match(r'^"[A-Z]', stripped) or
            re.match(r'^\d+\.\s+\*\*', stripped)  # numbered items with bold
        ):
            thinking_end_idx = i
            break

    # If we found a boundary, extract both views
    if thinking_end_idx > 0:
        thinking_section = '\n'.join(lines[:thinking_end_idx])
        answer_section = '\n'.join(lines[thinking_end_idx:]).strip()

        # Only extract if answer section is non-empty and substantial
        if answer_section and len(answer_section) > 50:
            return ExtractionResult(
                as_emitted=output,
                content_extracted=answer_section,
                extraction_type="local_thinking",
                thinking_boundary=thinking_end_idx,
            )

    # No clear boundary found - return unextractable
    return ExtractionResult(
        as_emitted=output,
        content_extracted=output,
        extraction_type="unextractable",
        thinking_boundary=None,
    )


def extract_magistral(output: Any) -> ExtractionResult:
    """
    Extract answer from Mistral magistral (cloud reasoning model) structured output.

    Magistral returns output as a JSON array with objects of type 'thinking' or 'text'.
    The array should contain 'text'-type items that hold the actual answer.

    Contamination type 1 (partial completion): output contains both thinking and text
    parts; extract only the text parts, concatenate them as the content-extracted view.

    Contamination type 2 (incomplete generation, finishReason='length'): output is
    ONLY thinking blocks, never reached the text generation phase. Marked as
    unextractable (the model was cut off mid-thinking).

    Failure modes:
    - Output is not a list (JSON parsing issue; unextractable)
    - All parts are thinking (cut off; unextractable)
    - Text parts are empty or whitespace-only (unextractable)
    """
    if not isinstance(output, list):
        return ExtractionResult(
            as_emitted=json.dumps(output) if isinstance(output, (dict, list)) else str(output),
            content_extracted=json.dumps(output) if isinstance(output, (dict, list)) else str(output),
            extraction_type="unextractable",
            thinking_boundary=None,
        )

    text_parts = []
    has_thinking = False

    for item in output:
        if isinstance(item, dict):
            if item.get('type') == 'thinking':
                has_thinking = True
            elif item.get('type') == 'text' and 'text' in item:
                text_parts.append(item['text'])

    # If we have text parts, extract them
    if text_parts:
        extracted_text = '\n'.join(text_parts).strip()

        if extracted_text and len(extracted_text) > 10:
            # Re-serialize as-emitted for comparison
            as_emitted_str = json.dumps(output)
            return ExtractionResult(
                as_emitted=as_emitted_str,
                content_extracted=extracted_text,
                extraction_type="magistral_partial",
                thinking_boundary=0,
            )

    # No text parts found - model was cut off mid-thinking
    as_emitted_str = json.dumps(output)
    return ExtractionResult(
        as_emitted=as_emitted_str,
        content_extracted=as_emitted_str,
        extraction_type="magistral_incomplete",
        thinking_boundary=None,
    )


def extract_reasoning_output(output: Any) -> ExtractionResult:
    """
    Dispatch to the appropriate extractor based on output type and content.
    """
    # Check if this is magistral's JSON array format
    if isinstance(output, list):
        return extract_magistral(output)

    # Otherwise, treat as local model text output
    if isinstance(output, str):
        return extract_local_thinking(output)

    # Fallback for unexpected types
    output_str = str(output)
    return ExtractionResult(
        as_emitted=output_str,
        content_extracted=output_str,
        extraction_type="unextractable",
        thinking_boundary=None,
    )


def regrade_results_file(
    input_file: Path, output_file: Path
) -> dict[str, Any]:
    """
    Load a results JSON, extract reasoning content, re-grade against both views,
    and write a summary.

    Returns: dict with:
      - 'as_emitted': {passed, total, score}
      - 'content_extracted': {passed, total, score}
      - 'unextractable_count': number of outputs marked unextractable
      - 'extraction_summary': dict of extraction_type -> count
    """
    with open(input_file) as f:
        data = json.load(f)

    results = data.get('results', {}).get('results', [])

    as_emitted_pass = 0
    as_emitted_total = 0
    extracted_pass = 0
    extracted_total = 0
    unextractable_count = 0
    extraction_summary = {}

    # Track per-test extraction details for later inspection
    extractions = []

    for result in results:
        if not result.get('success', False):
            # Already failed in the original run (e.g., scoring error)
            continue

        response = result.get('response', {})
        output = response.get('output')

        # Extract content
        extraction = extract_reasoning_output(output)
        extraction_summary[extraction['extraction_type']] = (
            extraction_summary.get(extraction['extraction_type'], 0) + 1
        )

        if extraction['extraction_type'] == 'unextractable':
            unextractable_count += 1
            # Grade as-emitted only
            if result.get('score', 0) > 0:
                as_emitted_pass += 1
            as_emitted_total += 1
        else:
            # We have both views to grade
            as_emitted_total += 1
            extracted_total += 1

            if result.get('score', 0) > 0:
                as_emitted_pass += 1

            # For extracted, we need to re-grade, but we don't have the grader here
            # The calling code will handle re-grading with the grader tool
            # For now, track that we have an extraction
            extractions.append({
                'test_idx': len(extractions),
                'name': result.get('testCase', {}).get('name'),
                'extraction_type': extraction['extraction_type'],
                'as_emitted_length': len(str(extraction['as_emitted'])),
                'extracted_length': len(str(extraction['content_extracted'])),
            })

    return {
        'as_emitted': {
            'passed': as_emitted_pass,
            'total': as_emitted_total,
            'score_percent': 100 * as_emitted_pass / as_emitted_total if as_emitted_total > 0 else 0,
        },
        'content_extracted': {
            'passed': extracted_pass,  # Will be filled in by re-grading
            'total': extracted_total,
            'score_percent': 0,  # Will be filled in by re-grading
        },
        'unextractable_count': unextractable_count,
        'extraction_summary': extraction_summary,
        'extractions_detail': extractions,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract reasoning content from model outputs and prepare for re-grading.",
        epilog="""
Examples:
  # Analyze a single results file
  %(prog)s results/deep-eval/e27-local-minimax-m27-summarisation.json

  # Output extraction summary
  %(prog)s --output extraction-summary.json results/deep-eval/*.json
        """,
    )
    parser.add_argument(
        'input_files',
        nargs='+',
        type=Path,
        help='Results JSON file(s) to analyze',
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output file for extraction summary (default: stdout)',
    )
    args = parser.parse_args()

    summary = {}

    for input_file in args.input_files:
        if not input_file.exists():
            print(f"Error: {input_file} not found", file=sys.stderr)
            sys.exit(1)

        result = regrade_results_file(input_file, input_file)
        summary[str(input_file)] = result

        print(f"{input_file.name}:")
        print(f"  As-emitted: {result['as_emitted']['passed']}/{result['as_emitted']['total']} "
              f"({result['as_emitted']['score_percent']:.1f}%)")
        print(f"  Unextractable: {result['unextractable_count']}")
        print(f"  Extraction types: {result['extraction_summary']}")
        print()

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary written to {args.output}")


if __name__ == '__main__':
    main()
