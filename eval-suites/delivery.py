#!/usr/bin/env python3
# File: delivery.py
# Purpose: Decide what actually stopped a generation - the context window, the output ceiling,
#          or the model itself - from the server's own log rather than from a text heuristic.
# Project: sparkbench | Date: 2026-08-12
#
# Overview: The promptfoo eval path records no delivery status, which is why five weeks passed
# before anyone noticed that three of five E10 answers were cut off by the context window and two
# by max_tokens. parse_serverlog() pulls the three numbers llama-server prints (prompt tokens,
# per-slot context, decoded tokens) plus its own truncation flag; classify_delivery() names the
# binding constraint. Both are pure, so the classification is tested against runs whose ground
# truth is independently known. This is the five-way delivery vocabulary from the instrumentation
# uplift (task 2), which landed in serve_bench.py and never reached the promptfoo path.
# Plan: docs/plans/2026-08-12-closed-record-reasoning-PLAN.md task 1.

from __future__ import annotations

import re
from pathlib import Path

N_CTX_RE = re.compile(r"n_ctx_slot\s*=\s*(\d+)")
PROMPT_RE = re.compile(r"prompt eval time\s*=\s*[\d.]+\s*ms\s*/\s*(\d+)\s*tokens")
EVAL_RE = re.compile(r"^\s*eval time\s*=\s*[\d.]+\s*ms\s*/\s*(\d+)\s*tokens")
TRUNC_RE = re.compile(r"truncated\s*=\s*(\d)")


def parse_serverlog(path: str | Path) -> dict:
    """Read the per-slot context and one record PER REQUEST out of a llama-server log.

    Returns `{"n_ctx_slot": int | None, "tasks": [{"prompt_tokens", "decoded",
    "server_truncated"}, ...]}` in log order.

    One serverlog covers every request in a suite run - 17 for the pilot, 1 for E10. Collapsing
    them to a single prompt/decode pair reports the LAST request's prompt length for every
    answer in the file, which produced a 41-token prompt for a long-context test when this was
    first run. A per-request list is the only shape that can be matched back to an individual
    answer.

    Missing FIELDS come back as None rather than raising: a serverlog can legitimately be partial
    (a killed server, a run that never reached the timing summary), and that is a recordable
    "unknown" rather than a crash. A missing FILE does raise - that is a wiring error, not an
    expected absence.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"serverlog not found: {p}; "
            f"hint: eval serverlogs are written as <label>.serverlog beside <label>.json "
            f"in results/eval-pilot/"
        )
    n_ctx_slot: int | None = None
    tasks: list[dict] = []
    pending_prompt: int | None = None
    for line in p.read_text(errors="replace").splitlines():
        if (m := N_CTX_RE.search(line)) and n_ctx_slot is None:
            n_ctx_slot = int(m.group(1))
        if m := PROMPT_RE.search(line):
            pending_prompt = int(m.group(1))
            continue
        # "prompt eval time" and "eval time" share a suffix, so the decode line is matched only
        # after the pipe-delimited slot/task prefix is stripped and only when "eval time" starts
        # the remainder. Matching the prompt line here would report the PROMPT as the answer
        # length, which inverts the finding this module exists to record.
        tail = line.split("|")[-1] if "|" in line else line
        if m := EVAL_RE.match(tail):
            tasks.append(
                {
                    "prompt_tokens": pending_prompt,
                    "decoded": int(m.group(1)),
                    "server_truncated": False,
                }
            )
            pending_prompt = None
            continue
        if (m := TRUNC_RE.search(line)) and m.group(1) == "1" and tasks:
            tasks[-1]["server_truncated"] = True
    return {"n_ctx_slot": n_ctx_slot, "tasks": tasks}


def match_task(tasks: list[dict], completion_tokens: int) -> dict | None:
    """Find the server-side record for one answer, by its decode count.

    promptfoo does not record which server task served which test, and with more than one slot
    the requests can interleave, so ORDER is not a safe join key. The decode count is recorded on
    both sides of the seam and is a safe key when it is unique within the run.

    Returns None when no task matches or when several do. An ambiguous match is reported as no
    match on purpose: guessing which of two identical-length answers is which would put an
    unearned classification into the record, which is the defect this module exists to catch.
    """
    hits = [t for t in tasks if t["decoded"] == completion_tokens]
    return hits[0] if len(hits) == 1 else None


def classify_delivery(
    prompt_tokens: int | None,
    n_ctx_slot: int | None,
    completion_tokens: int,
    max_tokens: int,
) -> str:
    """Name the constraint that stopped this generation.

    Returns one of context_exhausted / output_ceiling / ambiguous_ceiling / natural_stop /
    unknown.

    Both ceilings are reported when both bind, rather than picking one by evaluation order. An
    answer that stopped at 1200 tokens with exactly 1200 tokens of context headroom is genuinely
    not attributable, and silently calling it one or the other is how the original E10 diagnosis
    went wrong - all five runs were attributed to max_tokens when three had hit the context
    window and would have re-truncated identically at a higher ceiling.

    Without server evidence an output-ceiling hit is still decidable, because max_tokens comes
    from the suite rather than the log. A short answer is NOT decidable that way - it could have
    stopped naturally or run out of context - so it is reported as unknown rather than assumed
    healthy.
    """
    hit_output_only = completion_tokens >= max_tokens
    if prompt_tokens is None or n_ctx_slot is None:
        return "output_ceiling" if hit_output_only else "unknown"
    headroom = n_ctx_slot - prompt_tokens
    hit_output = completion_tokens >= max_tokens
    hit_context = completion_tokens >= headroom
    if hit_output and hit_context:
        return "ambiguous_ceiling"
    if hit_output:
        return "output_ceiling"
    if hit_context:
        return "context_exhausted"
    return "natural_stop"
