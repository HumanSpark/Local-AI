#!/usr/bin/env python3
# File: tools/tool_router.py
# Purpose: Decide, per question, whether to offer the date tool at all - the classifier E79 said the tools branch needs before it can pay.
# Project: sparkbench | Date: 2026-08-28
#
# Overview: E79 measured the two halves of the trade on the production model.
# Offering the date tool on a band-R item GAINS an item 3 times in 12. Offering
# it on a band-E item LOSES one 5 times in 12 (6 counting one HTTP 500). So a
# router must be roughly twice as precise as it is sensitive before the tool
# pays for itself, and that asymmetry - not the routing accuracy on its own - is
# what this module exists to be measured against.
#
# TWO ROUTERS, DELIBERATELY DIFFERENT IN KIND.
#
#   rule  - deterministic patterns over the question text. No inference, no
#           latency, no model. AUTHORED WITH THE BANK VISIBLE, which is declared
#           in E80 rather than hidden: its accuracy on L5 is an upper bound on
#           what this style of router achieves, not an estimate of how it would
#           generalise to questions nobody had seen.
#   model - a model answers YES or NO to one question about the question. This
#           is the DEPLOYABLE one, it is not fitted to anything, and it can be
#           pointed at the answering model itself or at a smaller specialist
#           (the plan's H18).
#
# The router sees the QUESTION ONLY, never the pack. A router that had to read
# the whole record to decide would cost as much as answering, which is the same
# trap E75 found when disagreement-routing turned out not to be cheaper than the
# work it was routing.

from __future__ import annotations

import json
import re
import urllib.request
from typing import Any

ROUTER_VERSION = "tool-router-v1-2026-08-28"

# Counting language. Written from what band R IS - a period that must be walked
# or an amount that must be computed - and not from inspecting which L5 items
# each pattern happens to catch.
_COUNTING = re.compile(
    r"\b("
    r"how many (?:days|months|years|business days)"
    r"|last day|expire|expires|expiry"
    r"|fall due|falls due|due date"
    r"|business days?"
    r"|takes effect|take effect"
    r"|statute-barred|suspended"
    r"|for how many"
    r"|how much interest|interest is payable"
    r"|the total of"
    r")\b",
    re.IGNORECASE,
)

# Language that marks a question as being about WHICH document or WHETHER the
# record says something - the band a date tool cannot help and can only harm.
_LOOKUP = re.compile(
    r"\b("
    r"which (?:call-off|document|courts?|ones?)"
    r"|governing law|jurisdiction"
    r"|liability cap|contract value"
    r"|how many employees"
    r"|is that (?:belief )?correct"
    r"|give its document id"
    r")\b",
    re.IGNORECASE,
)

ROUTER_PROMPT = (
    "You are a router. Decide whether answering the question below will require "
    "COUNTING or CALCULATING - a number of days, a date arrived at by counting a "
    "period, or an arithmetic amount.\n\n"
    "Answer YES if it needs counting or calculation.\n"
    "Answer NO if it only needs finding, comparing or reporting information.\n\n"
    "Reply with one word: YES or NO.\n\n"
    "QUESTION: {question}"
)


def rule_router(question: str) -> dict[str, Any]:
    """Deterministic. Lookup language vetoes counting language.

    The veto direction is set by E79's asymmetry: a false positive costs about
    twice what a false negative does, so where both patterns fire the router
    declines the tool.
    """
    counting = bool(_COUNTING.search(question))
    lookup = bool(_LOOKUP.search(question))
    return {
        "offer_tool": counting and not lookup,
        "router": "rule",
        "signals": {"counting": counting, "lookup": lookup},
    }


def model_router(
    question: str,
    base_url: str,
    timeout: float = 120.0,
    max_tokens: int = 8,
    thinking: str = "default",
) -> dict[str, Any]:
    """One YES/NO call about the question. Never sees the pack.

    An unparseable reply is reported as such and treated as NO, because the
    asymmetry says a false negative is the cheaper error - and because inventing
    a decision would hide how often the router failed to make one.
    """
    payload: dict[str, Any] = {
        "model": "x",
        "messages": [
            {"role": "user", "content": ROUTER_PROMPT.format(question=question)}
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    if thinking == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    elif thinking in ("low", "medium", "xhigh"):
        payload["reasoning_effort"] = thinking

    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = (
            json.loads(r.read().decode())["choices"][0]["message"].get("content") or ""
        ).strip()

    low = raw.lower()
    said_yes = bool(re.search(r"\byes\b", low))
    said_no = bool(re.search(r"\bno\b", low))
    if said_yes and not said_no:
        decision, parsed = True, True
    elif said_no and not said_yes:
        decision, parsed = False, True
    else:
        decision, parsed = False, False
    return {
        "offer_tool": decision,
        "router": "model",
        "parsed": parsed,
        "raw": raw[:120],
    }


def fixed_router(question_id: str, decisions: dict[str, bool]) -> dict[str, Any]:
    """Replay a decision map recorded by an earlier arm. Makes NO call.

    This exists for E80's reopen condition. The literal control - a second copy
    of the answering model serving as router - needs about 65 GiB alongside the
    resident relay, over the ~60 GiB threshold in docs/memory-edge-deadlock.md,
    and this account cannot power-cycle the box. Replaying the decisions
    isolates the SAME variable more tightly: same model, same decisions, same
    prompts, and zero router traffic through the answering slot.

    Raises on a missing id rather than defaulting to False. A silently
    unrouted item would look like a correct NO and would quietly break the
    like-for-like the control exists to establish.
    """
    if question_id not in decisions:
        raise KeyError(
            f"no recorded routing decision for {question_id!r}\n"
            f"hint: the decisions file must cover every item in the run - it is "
            f"built from an earlier arm's per-item `routing.offer_tool`"
        )
    return {"offer_tool": decisions[question_id], "router": "fixed", "replayed": True}


ROUTERS = {"rule", "model", "fixed"}
