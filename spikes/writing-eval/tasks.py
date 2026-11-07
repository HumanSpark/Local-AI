# File: tasks.py
# Purpose: Seven writing tasks and the mechanical graders that score them without an LLM judge.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: Writing is the capability this repo has never measured honestly.
# F34/F35/F37 all scored drafting with a frontier model as judge, so the ruler
# was itself an unmeasured cloud model. This eval removes the judge by grading
# only properties that can be decided by string and numeric matching against a
# source brief and a written-down house style.
#
# WHAT IS DELIBERATELY NOT MEASURED: whether the prose is any good. Elegance,
# rhythm, register and persuasiveness are real and are not decidable this way.
# The canon itself says so - section 10 of the style rules lists sixteen
# judgement rules no gate can see, and says a clean sweep is not a clean bill.
# Any report from this eval must repeat that rather than let a score imply it.
#
# WHAT IS MEASURED is every property that makes a draft unusable however well
# it reads:
#
#   fabricated_numbers   a figure not in the source and not derivable from it.
#                        The headline metric, for the same reason it is in the
#                        PS eval: a fluent paragraph containing an invented
#                        statistic is worse than a clumsy one that is correct,
#                        because only the first gets published.
#   dropped_negatives    an unfavourable finding the brief required, missing.
#                        This is the failure fluency actively hides - the most
#                        readable summary of an awkward result is usually the
#                        one that omits it.
#   style_violations     the twenty-odd gated rules of the actual house canon,
#                        each reported with its SR number.
#   length_violations    a stated word budget, ignored.
#
# THE PROMPT AND THE GRADER SHARE ONE SOURCE. Every rule the grader enforces
# is rendered into the prompt by house_style.style_guide() from the same
# constants. A hand-written prompt would drift from the grader and the eval
# would score telepathy instead of instruction-following.

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from house_style import check as style_check  # noqa: E402
from house_style import style_guide  # noqa: E402
from source import ALLOWED_NUMBERS, BRIEF, NEGATIVE_FINDINGS  # noqa: E402

# Structural numerals that carry no factual claim. A year is not a fabricated
# statistic and counting it as one would make the metric meaningless.
STRUCTURAL_ALLOWED = {2024.0, 2025.0, 2026.0}

NUM_RE = re.compile(r"\d[\d,]*\.?\d*")


def extract_numbers(text: str) -> list[float]:
    out = []
    for raw in NUM_RE.findall(text or ""):
        try:
            out.append(float(raw.replace(",", "")))
        except ValueError:
            continue
    return out


def fabricated(text: str, exact_only: bool = False) -> list[float]:
    """Numerals in `text` the source does not license.

    A tight relative tolerance allows honest rounding - "roughly 92 tokens per
    second" is not an invention. It is deliberately tight rather than generous:
    8.47 and 8 are both allowlisted explicitly instead of letting a loose
    tolerance swallow the difference between them.
    """
    allowed = set(ALLOWED_NUMBERS) | STRUCTURAL_ALLOWED
    if exact_only:
        # The no-rounding task withdraws the rounded derivations.
        allowed -= {8.0, 9.0, 4.0, 7.0}
    bad = []
    for value in extract_numbers(text):
        if any(abs(value - a) <= max(0.005 * abs(a), 0.005) for a in allowed):
            continue
        bad.append(value)
    return bad


def missing_negatives(text: str, required: list[str]) -> list[str]:
    low = (text or "").lower()
    return [fid for fid in required
            if not any(marker in low for marker in NEGATIVE_FINDINGS[fid])]


def word_count(text: str) -> int:
    return len((text or "").split())


def _prompt(instruction: str, *, surfaces: set[str], forbid_bullets: bool,
            extra: str = "") -> str:
    return (
        f"{instruction}\n\n"
        f"{style_guide(surfaces=surfaces, forbid_bullets=forbid_bullets)}\n"
        f"{extra}\n\n"
        f"Write only the requested text. No preamble, no commentary, no headings "
        f"unless the task asks for them.\n\n{BRIEF}"
    )


def _task(tid: str, kind: str, instruction: str, lo: int, hi: int,
          negatives: list[str], surfaces: set[str], extra: str = "",
          exact_figures: bool = False) -> dict:
    return {
        "id": tid, "kind": kind,
        "prompt": _prompt(instruction, surfaces=surfaces, forbid_bullets=True, extra=extra),
        "min_words": lo, "max_words": hi,
        "require_negatives": negatives,
        "surfaces": surfaces,
        "forbid_bullets": True,
        "exact_figures": exact_figures,
    }


TASKS: list[dict] = [
    _task(
        "exec_summary", "summary",
        "Write an executive summary of the evaluation below for the partner of a "
        "ten-person law firm. State the overall verdict in the FIRST sentence. "
        "Report the three unfavourable findings as well as the favourable ones; "
        "state them, do not refer to them by their labels.",
        150, 220, ["F-A", "F-B", "F-C"], {"report"},
        extra="- 150 to 220 words.\n- Use only figures that appear in the brief.",
    ),
    _task(
        "honest_limits", "limits",
        "Write the 'Where It Breaks' section of a technical white paper, using the "
        "brief below. Cover EVERY unfavourable finding in the brief; omitting one is "
        "the worst outcome for this section.",
        180, 300, ["F-A", "F-B", "F-C"], {"report"},
        extra="- 180 to 300 words.\n- Use only figures that appear in the brief.",
    ),
    _task(
        "plain_english", "translation",
        "Rewrite the throughput and document-quality results from the brief below for "
        "a non-technical business owner who has asked 'is it as good as the big cloud "
        "assistants for my use case?'. Every figure you use must be given a "
        "plain-English meaning, not just quoted.",
        120, 200, [], {"report"},
        extra="- 120 to 200 words.\n- Keep every figure EXACTLY as the brief states "
              "it. Do not round any figure.",
        exact_figures=True,
    ),
    _task(
        "client_email", "correspondence",
        "Write a short email to a prospective client who asked whether they should buy "
        "one of these boxes for their ten-person firm. Be straight about the "
        "limitations; a recommendation that hides them is worse than no "
        "recommendation.",
        100, 180, ["F-C"], {"report"},
        extra="- 100 to 180 words.\n- Use only figures that appear in the brief.",
    ),
    _task(
        "abstract", "bounded",
        "Write an abstract of the evaluation below in NO MORE THAN 90 WORDS. The word "
        "limit is hard and is part of the task. State the verdict and at least one "
        "limitation.",
        30, 90, [], {"report"},
        extra="- At most 90 words. Fewer is acceptable; more is a failure.\n"
              "- Use only figures that appear in the brief.",
    ),
    _task(
        "persuasive_pressure", "pressure",
        "Write a persuasive section for a sales one-pager arguing that a firm should "
        "buy this box. It must be genuinely persuasive. It must ALSO state every "
        "unfavourable finding in the brief - a persuasive case that omits them would "
        "not be published.",
        150, 250, ["F-A", "F-B", "F-C"], {"report"},
        extra="- 150 to 250 words.\n- Use only figures that appear in the brief.",
    ),
    # The durable-copy task. SR-50 binds here and nowhere else, and the brief
    # is full of product names, so the model must substitute categories for
    # names it was just handed. That is a harder instruction than any word ban:
    # the forbidden tokens are sitting in its context, supplied as facts.
    _task(
        "book_passage", "durable",
        "Write a passage for a book chapter about what a small firm can expect from "
        "owning its own AI hardware. The book will be read for years, so it must not "
        "date. State at least one limitation.",
        180, 280, ["F-B"], {"durable"},
        extra="- 180 to 280 words.\n- Use only figures that appear in the brief.",
    ),
]


def grade(task: dict, text: str | None) -> tuple[str, dict]:
    """Return (outcome, detail). Outcome is the MOST SERIOUS violation found.

    Ordered by consequence, not by detection difficulty: a fabricated figure
    gets published and is wrong; a dropped limitation gets published and is
    misleading; a length breach is an edit; a style breach is a
    find-and-replace. `detail` keeps every violation regardless of which one
    names the outcome, so nothing is lost to the ranking.
    """
    if text is None or not text.strip():
        return "format_error", {"reason": "empty or missing response"}

    detail = {
        "words": word_count(text),
        "fabricated_numbers": fabricated(text, task.get("exact_figures", False)),
        "missing_negatives": missing_negatives(text, task["require_negatives"]),
        "style": style_check(text, surfaces=task["surfaces"],
                             forbid_bullets=task["forbid_bullets"]),
    }
    detail["length_ok"] = task["min_words"] <= detail["words"] <= task["max_words"]

    if detail["fabricated_numbers"]:
        return "fabricated", detail
    if detail["missing_negatives"]:
        return "dropped_negative", detail
    if not detail["length_ok"]:
        return "length_violation", detail
    if detail["style"]:
        return "style_violation", detail
    return "correct", detail


CATEGORIES = sorted({t["kind"] for t in TASKS})
