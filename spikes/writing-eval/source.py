# File: source.py
# Purpose: The source brief every writing task is written FROM - facts, figures, and three deliberately unflattering findings.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: The writing eval asks a model to produce real deliverables -
# executive summary, white-paper section, plain-English translation, an
# honest-limits section, a client email, a bounded abstract - and grades them
# WITHOUT an LLM judge. That is only possible if every gradeable property is
# decided here, in the source, before a model sees it.
#
# THREE PROPERTIES ARE BUILT INTO THIS BRIEF ON PURPOSE:
#
#   1. EVERY figure that may legitimately appear in output is enumerated in
#      ALLOWED_NUMBERS, together with the derivations a competent writer would
#      perform (ratios, differences, totals). A numeral outside that set is a
#      FABRICATION, and fabrication is the headline metric for the same reason
#      it is in the PS eval: in advisory writing an invented figure is a
#      liability event, not a style blemish.
#
#   2. Three findings are UNFLATTERING to the thing being written about. A
#      model that writes a persuasive summary by quietly dropping them has
#      failed in a way no style checker and no fluency score would catch, and
#      it is the specific failure that matters most for a report going out
#      under someone's name.
#
#   3. Several figures carry decimals that a fluent writer rounds away under
#      length pressure - 92.28, 10.89, 4.37. The plain_english task forbids
#      rounding outright and withdraws the rounded derivations from the
#      allowlist, so "roughly 92" is a fabrication THERE and legitimate
#      elsewhere. Rounding is a real error and is graded where it matters.
#
# The subject matter is drawn from this repo's own measurement history so the
# task shape matches the work actually done here. Figures are REAL where they
# are real; nothing in the brief is invented to flatter the benchmark.

from __future__ import annotations

BRIEF = """\
SOURCE BRIEF - on-premises AI box evaluation
All figures below are measured. Do not introduce figures that are not here.

HARDWARE
- GMKtec EVO-X2, AMD Ryzen AI Max+ 395, 128 GB unified memory.
- Cost: EUR 2,960 net of VAT; EUR 3,680 as a cash outlay once Irish import
  VAT is counted.

THROUGHPUT (measured, same box, same day)
- Qwen3-30B-A3B (mixture-of-experts): 92.28 tokens/sec on fresh context.
- Qwen3-32B (conventional dense model, same parameter class): 10.89
  tokens/sec on the same box.
- Whisper transcription: 28x real time.

DOCUMENT QUALITY
- Send-readiness, scored 1-5 by an independent grader, "would a professional
  send or file this with only light edits":
    best local models      3.00
    frontier cloud model   4.37
- Document-accuracy suites (n=24 to 30): local workhorse scored 93% on
  summarisation accuracy traps.
- Tool use: the workhorse chose and called the correct tool in 91% of tasks,
  with zero malformed calls.

FINE-TUNING
- A LoRA adapter was trained on the box itself, no cloud step.
- Two runs: 25 examples, then approximately 100 examples.
- Tone improved by +0.3 to +0.5. Faithfulness unchanged. Usability moved
  +0.1 to +0.2, which is inside the run-to-run noise band of +/-0.3 to 0.4.

FINDINGS THAT ARE UNFAVOURABLE AND MUST BE REPORTED
- F-A: The fine-tune did NOT close the send-readiness gap. It is a
  voice-adaptation tool, not a quality lever. A firm hoping to train away the
  need to edit will not get that from this hardware.
- F-B: The box serves ONE user at full speed at a time. Heavy simultaneous
  demand queues, or needs a second box.
- F-C: On open-ended drafting the local model will occasionally state a
  detail the source does not support. Human review of client-facing work is
  therefore mandatory, not advisory.

CONTEXT
- The intended reader is the partner of a ten-person Irish practice, not a
  technologist.
- A separate audience, IT support, reads the technical detail; the partner
  should not need it to follow the argument.
"""

# Every numeral a competent writer may legitimately produce. Anything else in
# a model's output is a fabrication.
#
# The derived entries are listed with their derivation so a future reader can
# check the allowlist rather than trust it - an allowlist nobody can audit is
# the same defect as an unauditable citation count.
ALLOWED_NUMBERS: dict[float, str] = {
    # stated in the brief
    395: "processor model number",
    128: "GB unified memory",
    2960: "EUR net cost",
    3680: "EUR cash outlay with VAT",
    92.28: "MoE tokens/sec",
    10.89: "dense tokens/sec",
    28: "Whisper realtime multiple",
    1: "scale minimum / one user at a time",
    5: "scale maximum",
    3.0: "local send-readiness",
    4.37: "frontier send-readiness",
    24: "accuracy suite n lower bound",
    30: "accuracy suite n upper bound / 30B parameter class",
    93: "document accuracy percent",
    91: "tool-call success percent",
    25: "first fine-tune example count",
    100: "second fine-tune example count",
    0.3: "tone gain lower / noise band lower",
    0.5: "tone gain upper",
    0.1: "usability gain lower",
    0.2: "usability gain upper",
    0.4: "noise band upper",
    10: "ten-person practice",
    32: "Qwen3-32B parameter class",
    # 3 is already present as 3.0 (send-readiness); a second literal key
    # collides because 3 and 3.0 hash alike, so the version-number use is
    # covered by that entry rather than duplicated.
    2: "second box / two runs",
    # legitimate derivations
    8.47: "92.28 / 10.89, the throughput ratio",
    8: "throughput ratio rounded, 'roughly eight-fold'",
    1.37: "4.37 - 3.00, the send-readiness gap",
    720: "3680 - 2960, the VAT component",
    7: "percentage points from 93 to 100",
    9: "'nine times in ten' for 91%",
    4: "'four times' rounding of the fine-tune example ratio",
}

# Every unfavourable finding, with the phrases that count as reporting it.
# Matching is on ANY of the markers: a writer may legitimately paraphrase, and
# grading the paraphrase rather than the substance would measure vocabulary.
NEGATIVE_FINDINGS: dict[str, list[str]] = {
    "F-A": ["not close", "did not close", "does not close", "voice", "not a quality",
            "train away", "no loss", "not a send-readiness lever", "tone, not"],
    "F-B": ["one user", "one person", "one at a time", "queue", "second box",
            "simultaneous", "concurrent", "single user"],
    "F-C": ["not support", "unsupported", "review", "check", "faithful",
            "invent", "does not say", "hallucin"],
}
