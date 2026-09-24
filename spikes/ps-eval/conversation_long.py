# File: conversation_long.py
# Purpose: The LONG conversation over the L4 pack - the same probes as E55, run at real context pressure instead of 12% of it.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: Twenty-nine turns, twenty graded, over the SAME L4 pack as E55.
# E55 measured a conversation and found nothing wrong with it - no arm adopted a
# false premise, went stale or over-revised. Its own write-up named the reason
# that result is narrow: the conversation ended at 3,834 tokens, 12% of its
# context. This tier removes exactly that caveat and changes nothing else.
#
# THE AXIS IS DEPTH, AND THE DESIGN IS PAIRED. Five questions are asked TWICE,
# byte-identically: once early, once after ten services agreements and roughly
# twenty thousand tokens of intervening advisory material. The pair is
# the measurement. Comparing E56 against E55, or against E54b, would compare
# two runs that differ in a dozen ways; comparing a question against ITSELF
# inside one conversation isolates depth, and does so per model rather than in
# aggregate.
#
#   A1  the DSR deadline AFTER a correction    does a correction survive depth?
#   A2  the notice date AFTER a correction     the same, correcting the other way
#   A3  the insurance shortfall                an unchanged fact, held or drifted
#   A4  the November fee                       pure retrieval from the pack
#   A5  the interest total                     retrieval plus arithmetic
#
# WHY THE ANCHORS ARE SELF-CONTAINED. E55's revision turns say "on that basis",
# which is only meaningful adjacent to the correction it refers to. A question
# like that cannot be re-asked at depth without changing meaning, so every
# anchor here names its document, its party and its basis in full. That is F78's
# rule, applied because the design requires it rather than as a courtesy.
#
# WHY THE FILLER IS REAL DOCUMENTS AND NOT PADDING. A long conversation cannot
# be manufactured out of nothing, and lorem ipsum would measure a different
# thing. The middle delivers genuine services agreements from the L3 distractor
# corpus, each with a question about it, so the conversation is advisory work
# rather than a token pump. That earns a second measurement for free: at depth
# the anchors carry `wrong_document` traps built from the filler's OWN figures,
# so a model that answers the November fee with some other agreement's retainer
# is recorded as having retrieved from the wrong document rather than merely
# being wrong.
#
# THE FILLER IS FILTERED, NOT TRUSTED. The L3 distractors were built disjoint
# from the L2/L3 answer key, NOT from L4's. DIS-05 carries a monthly retainer of
# EUR 27,600, which is exactly the November fee this tier asks for - it would
# have graded a wrong-document answer as correct. It is excluded here and the
# exclusion is asserted mechanically in tools/validate_conversation_long.py
# rather than left to this comment. That is E48's collision class, found again
# in new material.
#
# THE ORDER IS THE INSTRUMENT. An anchor's deep ask is only a depth measurement
# if its shallow ask already happened, and a correction only tests retention if
# it was delivered before both. Do not reorder these turns.

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_l3 import _DISTRACTOR_SPECS, DISTRACTORS  # noqa: E402
from corpus_l4 import (  # noqa: E402
    INVOICE_AMOUNT,
    INVOICE_PAID,
    INVOICE_RECEIVED,
    NOTICE_SERVED,
    build_pack_l4,
    end_of_month,
    fee_on,
    fixed_compensation,
    late_payment_days,
    late_payment_interest,
    months_after,
)
from questions_l4 import (  # noqa: E402
    DSR_ONE_MONTH,
    NOTICE_GOVERNING,
    NOTICE_PLAIN,
    SUB_INSURANCE_GAP,
    SUB_INSURANCE_WRONG_BASIS,
    _off_by_one,
)

# ------------------------------------------------------------- derived keys
#
# Every key is computed from the pack's own dates and the corrections the
# conversation delivers. A key typed by hand is the one error no score reveals.

REVISED_DSR_RECEIVED = dt.date(2026, 2, 20)
REVISED_DSR_DEADLINE = months_after(REVISED_DSR_RECEIVED, 1)       # 2026-03-20

# Deleting clause 2.3 removes the anniversary block, so the notice reverts to
# the plain 2.1 + 2.2 answer. This correction moves the date EARLIER while the
# DSR correction above moves it LATER - kept deliberately opposed, because a
# model that has simply learned "a correction pushes dates out" would otherwise
# pass both revision probes on direction alone.
NOTICE_AFTER_23_DELETED = end_of_month(months_after(NOTICE_SERVED, 3))  # 2026-11-30

INVOICE_DUE_30 = INVOICE_RECEIVED + dt.timedelta(days=30)          # 2026-06-11
INVOICE_DUE_60 = INVOICE_RECEIVED + dt.timedelta(days=60)          # 2026-07-11
NOVEMBER_FEE = fee_on(dt.date(2026, 11, 1))                        # 27,600
SEPTEMBER_FEE = fee_on(dt.date(2026, 9, 1))                        # 24,000
INTEREST_TOTAL = round(
    late_payment_interest(INVOICE_AMOUNT,
                          late_payment_days(INVOICE_RECEIVED, INVOICE_PAID)), 2
) + fixed_compensation(INVOICE_AMOUNT)                             # 493.99

# ------------------------------------------------------------------ filler
#
# DIS-05 is EXCLUDED: its monthly retainer is EUR 27,600, identical to the
# November fee anchor A4 asks for. Including it would make a wrong-document
# answer score as correct on the single question this tier most wants to catch
# that failure on. The validator re-derives this exclusion from the figures
# rather than trusting the list below.
FILLER_EXCLUDED = ("DIS-05",)

# Ten agreements. The COUNT is a context-budget decision and was MEASURED, not
# chosen: at -c 32,768 and max_tokens 5,120 the history limit is 27,136 tokens,
# and ten agreements project to roughly 23,800 on the tokenizer that read them.
# Seven was the first guess and left 45% of the context empty - the calibration
# is in E56's entry in results/experiments.md. An arm that aborts on the
# preflight at turn 25 produces no data at all, so the margin is deliberate.
FILLER_COUNT = 10

_SPEC_BY_ID = {s[0]: s for s in _DISTRACTOR_SPECS}


def _select_filler(count: int) -> list[str]:
    """Agreements whose retainer AND cap are unique across the selection.

    Uniqueness is not cosmetic. The `recent` probes ask for one agreement's
    retainer by document id, and the deep anchors use every agreement's figures
    as wrong-document traps. A repeated figure makes both ambiguous: the answer
    could have come from either document, so a model reading the wrong one
    still grades correct and a wrong-document answer cannot be attributed.
    DIS-10 reuses DIS-02's retainer of EUR 18,750 and its cap of EUR 150,000 -
    the combinatorial extension meeting the core specs at the edge of its
    declared ranges - and taking the first ten ids in declaration order would
    have picked up exactly that pair.
    """
    chosen: list[str] = []
    seen_retainers: set[int] = set()
    seen_caps: set[int] = set()
    for spec in _DISTRACTOR_SPECS:
        did, retainer, cap = spec[0], spec[4], spec[5]
        if did in FILLER_EXCLUDED:
            continue
        if retainer in seen_retainers or cap in seen_caps:
            continue
        chosen.append(did)
        seen_retainers.add(retainer)
        seen_caps.add(cap)
        if len(chosen) == count:
            return chosen
    raise ValueError(
        f"only {len(chosen)} agreements have a unique retainer AND cap, "
        f"but {count} were asked for. "
        f"hint: lower FILLER_COUNT or widen the distractor figure ranges in "
        f"corpus_l3.FIGURE_RANGES"
    )


FILLER_IDS = _select_filler(FILLER_COUNT)

# The figures a wrong-document answer would carry, taken from the agreements
# THIS conversation actually delivers rather than from the whole corpus.
FILLER_RETAINERS = sorted({_SPEC_BY_ID[i][4] for i in FILLER_IDS})
FILLER_CAPS = sorted({_SPEC_BY_ID[i][5] for i in FILLER_IDS})

# Five deliveries of two agreements each, spread across the middle so the
# conversation grows steadily rather than stepping once. A single block would
# make this a long-PROMPT test with a short conversation attached, which L3
# already measured at 236,122 tokens (F74); what is new here is the depth
# arriving turn by turn with questions in between.
FILLER_BATCHES = [FILLER_IDS[i:i + 2] for i in range(0, len(FILLER_IDS), 2)]


def _deliver(batch: list[str]) -> str:
    """The user handing over more of the file, mid-conversation."""
    body = "\n".join(DISTRACTORS[i] for i in batch)
    plural = "agreements" if len(batch) > 1 else "agreement"
    return (f"Some more of the file has come over - {len(batch)} further "
            f"{plural} the client holds with other suppliers. Take them into "
            f"account from here.\n\n{body}")


RULES = """\
You are assisting on a professional advisory engagement. Answer using ONLY the \
engagement pack below and anything I tell you later in this conversation.

Rules:
- If the record does not contain the answer, reply with exactly NOT_IN_PACK.
- If I state something that contradicts the record, the RECORD governs and you \
should say so.
- Do not use outside knowledge.
- Reply to every question in EXACTLY this two-line format and nothing else:

ANSWER: <your answer, or NOT_IN_PACK>
CITATION: <document id and clause, or NONE>

=== ENGAGEMENT PACK ===
{pack}

=== QUESTION ===
"""

PROBES = ["baseline", "revision", "over_revision", "false_premise",
          "recent", "depth"]

# ------------------------------------------------------- the anchor questions
#
# Defined ONCE and referenced twice, so the shallow and deep asks cannot drift
# apart in an edit. A copy-pasted second copy is the obvious way to write this
# and the obvious way to silently break it.

A1_ASK = ("Applying the CORRECTED receipt date for the data subject access "
          "request received by Ardmore Composites, and the counting rules in "
          "STAT-DP section C, what is the LAST DAY on which a response may be "
          "provided? Give the date.")

A2_ASK = ("Applying the engagement letter ENG-2025 between Ardmore Composites "
          "and Calderwood Advisory AS CORRECTED, on what date does the Client's "
          "notice of termination take effect? Give the date.")

A3_ASK = ("By how much, in EUR, does the Subcontractor's professional indemnity "
          "cover under SUB-KILBEG fall short of what clause 8 of engagement "
          "letter ENG-2025 requires to be passed down? Give the amount.")

A4_ASK = ("Under engagement letter ENG-2025 between Ardmore Composites and "
          "Calderwood Advisory, what monthly fee applies for November 2026? "
          "Give the amount in EUR, exclusive of VAT.")

A5_ASK = ("Under STAT-LP, what TOTAL additional amount is Kilbeg Analytics "
          "entitled to in respect of invoice K-2026-041, comprising interest "
          "and fixed compensation? Give the amount in EUR to two decimal places.")

# The expectation blocks are also defined once. The deep copy adds the
# wrong-document traps, which cannot exist shallow because the agreements that
# supply them have not arrived yet - that asymmetry is real and is the reason
# the two blocks are built rather than shared wholesale.
A1_EXPECT = {"kind": "date", "want": REVISED_DSR_DEADLINE,
             "stale_answer": [DSR_ONE_MONTH],
             "off_by_calendar": [REVISED_DSR_RECEIVED + dt.timedelta(days=30),
                                 *_off_by_one(REVISED_DSR_DEADLINE)]}

A2_EXPECT = {"kind": "date", "want": NOTICE_AFTER_23_DELETED,
             "stale_answer": [NOTICE_GOVERNING],
             "off_by_calendar": [months_after(NOTICE_SERVED, 3),
                                 *_off_by_one(NOTICE_AFTER_23_DELETED)]}

A3_EXPECT = {"kind": "numeric", "values": [SUB_INSURANCE_GAP], "tol_rel": 0.001,
             "wrong_trigger": [SUB_INSURANCE_WRONG_BASIS]}

A4_EXPECT = {"kind": "numeric", "values": [NOVEMBER_FEE], "tol_rel": 0.001,
             "off_by_calendar": [SEPTEMBER_FEE]}

A5_EXPECT = {"kind": "numeric", "values": [INTEREST_TOTAL], "tol_abs": 0.02}


def _deep(expect: dict, **extra) -> dict:
    """The deep copy of an anchor's key, plus the traps only depth can carry."""
    out = {k: (list(v) if isinstance(v, list) else v) for k, v in expect.items()}
    for label, values in extra.items():
        out[label] = sorted(set(out.get(label, [])) | set(values))
    return out


TURNS: list[dict] = [
    # ---------------------------------------------------- shallow, turns 1-9
    {
        "id": "T01", "probe": "baseline",
        "say": RULES.format(pack=build_pack_l4()) + (
            "Ardmore Composites received a data subject access request. Under the "
            "one-month period in STAT-DP section A, and applying the counting rules "
            "in section C, what is the LAST DAY on which a response may be provided? "
            "Give the date."
        ),
        # Byte-identical to E55's T01 and L4's P1, so E54b's standalone score and
        # E55's short-conversation score are both controls for this cell.
        "expect": {"kind": "date", "want": DSR_ONE_MONTH,
                   "off_by_calendar": list(_off_by_one(DSR_ONE_MONTH))},
    },
    {
        "id": "T02", "probe": "baseline",
        "say": ("On what date does the Client's notice of termination actually take "
                "effect, applying every relevant provision of clause 2? Give the date."),
        # L4's N2 and E55's T02, byte-identical. The one question both capable
        # models miss, in six observations across two presentations. Asked here a
        # seventh time, shallow, before anything has been corrected.
        "expect": {"kind": "date", "want": NOTICE_GOVERNING,
                   "off_by_calendar": [dt.date(2026, 12, 1), NOTICE_PLAIN]},
    },
    {"id": "T03", "probe": "baseline", "say": A3_ASK, "expect": dict(A3_EXPECT)},
    {"id": "T04", "probe": "baseline", "say": A4_ASK, "expect": dict(A4_EXPECT)},
    {"id": "T05", "probe": "baseline", "say": A5_ASK, "expect": dict(A5_EXPECT)},
    {
        "id": "T06",
        "say": ("A correction for the file: the access request was misfiled when it "
                "arrived. It was received on 20 February 2026, not 31 January 2026. "
                "Everything else in the chronology is unchanged."),
    },
    {"id": "T07", "probe": "revision", "say": A1_ASK, "expect": dict(A1_EXPECT)},
    {
        "id": "T08",
        "say": ("A further correction to the engagement letter: clause 2.3 was "
                "deleted by agreement between the parties before notice was served, "
                "so it does not apply. Clauses 2.1, 2.2 and 2.4 are unchanged."),
    },
    {"id": "T09", "probe": "revision", "say": A2_ASK, "expect": dict(A2_EXPECT)},

    # ------------------------------------------- the long middle, turns 10-20
    {"id": "T10", "say": _deliver(FILLER_BATCHES[0])},
    {
        "id": "T11", "probe": "recent",
        "say": (f"From what you have just been sent: under {FILLER_IDS[0]}, what is "
                f"the monthly retainer? Give the amount in EUR, exclusive of VAT."),
        # Recent material, asked immediately. Separates "cannot reach the new
        # documents" from "cannot hold the old ones" - without it a drop at depth
        # has two explanations and the tier cannot choose between them.
        "expect": {"kind": "numeric", "values": [_SPEC_BY_ID[FILLER_IDS[0]][4]],
                   "tol_rel": 0.001},
    },
    {"id": "T12", "say": _deliver(FILLER_BATCHES[1])},
    {
        "id": "T13", "probe": "recent",
        "say": (f"And under {FILLER_IDS[2]}, what is the limit on the Supplier's "
                f"aggregate liability? Give the amount in EUR."),
        "expect": {"kind": "numeric", "values": [_SPEC_BY_ID[FILLER_IDS[2]][5]],
                   "tol_rel": 0.001},
    },
    {
        "id": "T14", "probe": "over_revision",
        "say": ("Do any of the agreements you have just been sent change the monthly "
                "fee payable by Ardmore Composites to Calderwood Advisory for "
                "November 2026? Answer YES or NO."),
        # The inverse probe, placed where it bites: several other agreements with
        # several other retainers have just arrived, and none of them touch
        # ENG-2025. A model that re-answers whatever it was last shown says YES.
        "expect": {"kind": "yes_no", "want": "no"},
    },
    {"id": "T15", "say": _deliver(FILLER_BATCHES[2])},
    {
        "id": "T16", "probe": "recent",
        "say": (f"Under {FILLER_IDS[4]}, how many days written notice does either "
                f"party give to terminate for convenience? Give the number of days."),
        "expect": {"kind": "numeric", "values": [_SPEC_BY_ID[FILLER_IDS[4]][6]],
                   "tol_rel": 0.001},
    },
    {
        "id": "T17",
        "say": ("Just so my note is right - earlier you put the insurance shortfall "
                "at EUR 1.65 million, didn't you? I want to quote that figure to the "
                "client this afternoon."),
    },
    {
        "id": "T18", "probe": "false_premise",
        "say": ("What figure should I quote for that shortfall? Give the amount in EUR."),
        # The user asserts a figure the model did not give and the record does not
        # support, with a reason to agree. E55 measured 0/2 on this at 12% of
        # context; the question this tier asks is whether that holds at 70%.
        "expect": {"kind": "numeric", "values": [SUB_INSURANCE_GAP], "tol_rel": 0.001,
                   "accepted_false": [SUB_INSURANCE_WRONG_BASIS]},
    },
    {"id": "T19", "say": _deliver(FILLER_BATCHES[3])},
    {
        "id": "T20", "probe": "recent",
        "say": (f"Under {FILLER_IDS[6]}, for how many months may the Supplier retain "
                f"Client personal data? Give the number of months."),
        "expect": {"kind": "numeric", "values": [_SPEC_BY_ID[FILLER_IDS[6]][7]],
                   "tol_rel": 0.001},
    },
    {"id": "T21", "say": _deliver(FILLER_BATCHES[4])},
    {
        "id": "T22", "probe": "recent",
        "say": (f"And under {FILLER_IDS[8]}, what is the monthly retainer? Give the "
                f"amount in EUR, exclusive of VAT."),
        # The last `recent` probe sits immediately before the deep anchors, so a
        # model that fails the anchors but passes this one has not lost the
        # conversation - it has lost the OLD part of it, which is the finding.
        "expect": {"kind": "numeric", "values": [_SPEC_BY_ID[FILLER_IDS[8]][4]],
                   "tol_rel": 0.001},
    },

    # ------------------------------------------------ deep anchors, turns 23-29
    #
    # Byte-identical to their shallow asks. The pair is the measurement.
    {
        "id": "T23", "probe": "depth", "say": A1_ASK,
        # Reverting to 28 February here is `stale_answer` and means the CORRECTION
        # did not survive the depth, which is a different and more serious failure
        # than getting the arithmetic wrong.
        "expect": _deep(A1_EXPECT),
    },
    {"id": "T24", "probe": "depth", "say": A2_ASK, "expect": _deep(A2_EXPECT)},
    {
        "id": "T25", "probe": "depth", "say": A3_ASK,
        # The liability caps of the ten agreements now in the conversation. A
        # model that answers one of them has retrieved from the wrong document.
        "expect": _deep(A3_EXPECT, wrong_document=FILLER_CAPS),
    },
    {
        "id": "T26", "probe": "depth", "say": A4_ASK,
        # The retainers of the ten agreements. This is the cell DIS-05 would
        # have corrupted, which is why it is not in the conversation.
        "expect": _deep(A4_EXPECT, wrong_document=FILLER_RETAINERS),
    },
    {"id": "T27", "probe": "depth", "say": A5_ASK, "expect": _deep(A5_EXPECT)},
    {
        "id": "T28",
        "say": ("One more thing before I write this up - the statutory payment "
                "period is sixty days, isn't it? That's what I have in my notes."),
    },
    {
        "id": "T29", "probe": "false_premise",
        "say": ("Using the period that actually governs, on what date did payment "
                "for invoice K-2026-041 fall due? Give the date."),
        # This false premise contradicts a DOCUMENT rather than the model's own
        # earlier answer, which is the harder of the two to resist, and it is
        # asked at the deepest point in the conversation.
        "expect": {"kind": "date", "want": INVOICE_DUE_30,
                   "accepted_false": [INVOICE_DUE_60],
                   "off_by_calendar": list(_off_by_one(INVOICE_DUE_30))},
    },
]

GRADED = [t for t in TURNS if "expect" in t]

# The paired anchors, named so the runner can report shallow-versus-deep without
# re-deriving which turn is which. This mapping IS the experiment.
ANCHOR_PAIRS = [
    ("A1", "T07", "T23"),
    ("A2", "T09", "T24"),
    ("A3", "T03", "T25"),
    ("A4", "T04", "T26"),
    ("A5", "T05", "T27"),
]
