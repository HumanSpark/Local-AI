# File: spikes/kw-eval/corpus.py
# Purpose: Assemble packs of REAL sparkbench documents at three context sizes for the KA-H1 knowledge-work instrument.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: The goal asks for real or representative work, including
# large-context and multi-document tasks, and for a more discriminating
# instrument once an existing one hits a ceiling. ps-eval's L1, L2 and L3-hard
# are all ceilings for strong arms (20/20, 12/12, 12/12 - F91) and its corpus is
# synthetic, so neither half of that requirement is met by extending it.
#
# THESE ARE REAL DOCUMENTS, not a simulation of some. They are this lab's own
# incident reports, findings register, harness rules, routing guide and
# programme plan - technical prose written to be acted on, by several hands,
# over months, with the inconsistencies that implies. That is what makes them
# usable: a corpus authored in one sitting to be answered has no conflicts in it
# to find.
#
# EVERY DOCUMENT POSTDATES THE ARMS' KNOWLEDGE CUTOFF, so no arm can have
# memorised an answer.
#
# THE THREE SIZES ARE THE SAME MATERIAL, GROWING. A question answerable in S
# must stay answerable in L, which is what makes the ladder a measurement of
# context handling rather than of three different tests.

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

# Ordered. Each pack is a prefix of this list, so L strictly contains M contains S.
DOCS: list[tuple[str, str]] = [
    ("memory-edge-deadlock", "docs/memory-edge-deadlock.md"),
    ("decode-hang", "docs/2026-08-19-gptoss120b-decode-hang.md"),
    ("harness-rules", "docs/HARNESS-RULES.md"),
    ("qwen38-report", "reports/2026-08-19-qwen38-programme-report.md"),
    ("routing-guide", "reports/2026-07-16-local-model-routing-guide.md"),
    (
        "rd-programme",
        "docs/plans/2026-08-19-rd-programme-inference-as-resource-allocation.md",
    ),
    ("reviewer-selection", "docs/2026-08-19-reviewer-selection.md"),
    ("kokoro-tuning", "docs/kokoro-tts-tuning.md"),
    ("qwen38-interim", "reports/2026-08-15-qwen38-interim.md"),
    ("legal-blueprint", "docs/legal-assistant-blueprint.md"),
    ("closevector-review", "reports/2026-08-11-closevector-legal-benchmark-review.md"),
    ("plain-english-summary", "reports/2026-08-16-plain-english-complete-summary.md"),
    ("session-sync", "docs/2026-08-17-session-sync-report.md"),
    ("campaign-final", "reports/2026-07-12-campaign-final-report.md"),
    ("claims-qa", "docs/claims-qa.md"),
]

# Sizes are named by DOCUMENT COUNT and reported in CHARS, never in tokens.
# CLAUDE.md records that chars/4 understates technical text by roughly 40% -
# the "12K" E10 log was 16,140 tokens for Qwen - so a token figure here would be
# a guess dressed as a measurement. The runner records the server's own
# prompt_tokens per request, and that is the number any context claim uses.
PACKS: dict[str, int] = {"s": 4, "m": 6, "l": 15}


def load_doc(name: str) -> str:
    """Read one document. A missing file is fatal - a silently short pack would
    make every item that needed it unanswerable and look like a model failure."""
    rel = dict(DOCS)[name]
    p = REPO / rel
    if not p.exists():
        raise FileNotFoundError(
            f"corpus document missing: {rel}\n"
            f"hint: the pack is defined by DOCS in spikes/kw-eval/corpus.py; "
            f"a renamed or deleted file must be corrected there, not skipped"
        )
    return p.read_text()


def build_pack(size: str = "m") -> str:
    """Concatenate the first N documents with explicit delimiters.

    Delimiters are named and uniform so a question can legitimately ask which
    document something came from - a citation requirement is only fair if the
    boundaries are visible.
    """
    if size not in PACKS:
        raise ValueError(
            f"unknown pack size {size!r}, expected one of {sorted(PACKS)}\n"
            f"hint: sizes are s/m/l, a growing prefix of the same list"
        )
    parts = []
    for name, rel in DOCS[: PACKS[size]]:
        parts.append(f"===== DOCUMENT: {name} ({rel}) =====\n\n{load_doc(name)}\n")
    return "\n".join(parts)


def pack_docs(size: str = "m") -> list[str]:
    """Which document names are present at this pack size."""
    return [name for name, _ in DOCS[: PACKS[size]]]


if __name__ == "__main__":
    for s in ("s", "m", "l"):
        pack = build_pack(s)
        print(
            f"{s}: {len(pack):>8,} chars  ~{len(pack) // 4:>7,} tokens (chars/4)  "
            f"{len(pack_docs(s))} docs: {', '.join(pack_docs(s))}"
        )
