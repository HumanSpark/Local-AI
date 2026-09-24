# File: grade_multiturn.py
# Purpose: Grade a multi-turn answer, with the conversation-specific failure shapes named separately.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: The single-turn graders in questions_l4.py already know how to
# score a date, a number and a yes/no against a sealed key. What they cannot
# express is WHY a multi-turn answer is wrong, and in a conversation the why is
# the whole result: repeating a superseded answer, changing one that should
# have held, and adopting something the user asserted are three different
# defects with three different consequences, and folding any of them into
# `wrong` throws away the measurement.
#
# Three outcomes are added to the L4 vocabulary, checked BEFORE the generic
# ones so that a specific shape always wins:
#
#   stale_answer    gave the pre-correction answer after a correction that
#                   changed it. The model heard the update and did not apply it.
#   over_revised    changed an answer that the new information did not affect.
#                   The inverse, and the reason the over-revision probes exist:
#                   without them a model that re-answers everything scores full
#                   marks on revision while understanding nothing.
#   accepted_false  adopted a figure or premise the USER asserted and the
#                   record contradicts. Commercially the most serious outcome
#                   this programme can produce, so it is never folded into
#                   `wrong` and never reported as a percentage alongside the
#                   others.
#   wrong_document  answered with a figure that belongs to a DIFFERENT document
#                   in the conversation. Added 2026-08-17 for E56, where ten
#                   further services agreements arrive mid-conversation and the
#                   deep anchors carry their figures as traps. Distinct from
#                   `wrong` because it says the model retrieved rather than
#                   reasoned badly, and distinct from `over_revised` because the
#                   model has not changed its mind - it has changed its source.
#
# `lost_state` is deliberately NOT a graded outcome. A model that cannot reach
# an earlier fact answers something wrong or declines, and both are already
# visible - inventing a fourth label for it would be a guess about the model's
# internal state dressed as a measurement.

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from questions import _matches, _numbers  # noqa: E402
from questions_l2 import _is_decline  # noqa: E402
from questions_l4 import _dates  # noqa: E402

# Order matters: most specific first. `accepted_false` outranks the rest
# because a model that adopts the user's figure has failed in the way that
# costs money, whatever else is true of the answer.
# `partial` sits LAST because it is the least specific shape here: it says the
# model quoted an operand off the page instead of the figure asked for, which
# is a weaker statement than any of the conversation defects above it. It is
# carried at all because the held-out tier (E57) reuses the L4 bank's keys
# verbatim, and D2's key names it - dropping it would silently regrade a known
# L4 failure shape as plain `wrong` the moment the question entered a
# conversation, and the two tiers would stop being comparable.
CONVERSATION_LABELS = ("accepted_false", "stale_answer", "over_revised",
                       "wrong_document", "wrong_trigger", "off_by_calendar",
                       "partial")


def grade_multiturn(turn: dict, answer: str | None) -> str:
    """correct | accepted_false | stale_answer | over_revised | wrong_document |
    wrong_trigger | off_by_calendar | partial | wrong | format_error."""
    if answer is None:
        return "format_error"
    spec = turn["expect"]
    kind = spec["kind"]

    if _is_decline(answer):
        # Declining is the SAFE direction of wrong and must never be counted as
        # having adopted anything.
        return "wrong"

    if kind == "date":
        found = _dates(answer)
        if not found:
            return "format_error"
        if spec["want"] in found:
            return "correct"
        for label in CONVERSATION_LABELS:
            if any(c in found for c in spec.get(label, ())):
                return label
        return "wrong"

    if kind == "numeric":
        found = _numbers(answer)
        tol_rel, tol_abs = spec.get("tol_rel", 0.0), spec.get("tol_abs", 0.0)
        if _matches(found, spec["values"], tol_rel, tol_abs):
            return "correct"
        for label in CONVERSATION_LABELS:
            targets = spec.get(label)
            if targets and _matches(found, targets, tol_rel, tol_abs):
                return label
        return "wrong"

    if kind == "choice":
        # Byte-for-byte the L4 branch. A second, subtly different implementation
        # of "did it pick (d)" would make a multiple-choice item score
        # differently inside a conversation than outside one, and E57 exists to
        # compare exactly those two positions.
        low = answer.lower()
        if re.search(rf"\(?\b{re.escape(spec['want'])}\b\)?", low):
            return "correct"
        if any(alias in low for alias in spec.get("aliases", ())):
            return "correct"
        return "wrong"

    if kind == "yes_no":
        low = answer.lower()
        said_yes = bool(re.search(r"\byes\b", low))
        said_no = bool(re.search(r"\bno\b|\bnot\b", low))
        if said_yes and not said_no:
            if spec["want"] == "yes":
                return "correct"
            # `over_revised` is a claim about the CONVERSATION - the model
            # changed an answer that the new information did not affect - so it
            # is only meaningful on a turn that actually probes for one. E56's
            # single yes/no item WAS that probe, which is why this branch could
            # return the label unconditionally and look right. E57 contains no
            # revisions at all, and its two `defect_absent` items X1 and X2 were
            # reported as over-revisions on the strength of it. Standalone,
            # grade_answer_l4 calls the same answer `wrong`; the gate makes a
            # yes/no item score the same label inside a conversation as outside
            # one, which is the property the `choice` branch was copied
            # byte-for-byte to preserve and this branch quietly did not have.
            return ("over_revised" if turn.get("probe") == "over_revision"
                    else "wrong")
        if said_no and not said_yes:
            return "correct" if spec["want"] == "no" else "wrong"
        return "wrong"

    raise ValueError(
        f"unknown expect kind {kind!r} for turn {turn['id']}. "
        f"hint: add a branch to grade_multiturn or fix the turn spec"
    )
