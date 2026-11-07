# File: questions_l5.py
# Purpose: Level-5 questions - twenty-four items split into a reasoning-limited band and an evidence-limited band, so an intervention can be scored against the band it should move.
# Project: sparkbench | Date: 2026-08-28
#
# Overview: Every item carries a `band`, and the band is the point of the tier.
#
#   band R - the evidence is HANDED OVER in the question. It names the clause,
#            the document and the trigger date. Nothing has to be found. What
#            is hard is walking the period or composing two constraints, which
#            F60 predicted and E54 measured: walked periods separated the arms
#            6/7, 4/7 and 0/7 while static analysis separated nothing.
#            **Context engineering cannot move this band and is not expected
#            to.** Tools can - tools/date_calc.py exists and is the H16 arm.
#
#   band E - the reasoning is one step the models do reliably. What is hard is
#            deciding WHICH of four parallel instruments governs, reconciling
#            an agreed chronology against an internal note that contradicts
#            it, or noticing the record never answers the question. **If the
#            programme's context-engineering branch has anything to offer on
#            this hardware, it has to show up here.**
#
# BAND R HANDS THE EVIDENCE OVER ON PURPOSE. An item that required finding the
# clause AND walking the period would confound the two bands, and the whole
# value of this tier is that it does not. Where a band-R question looks
# over-specified, that is the design.
#
# EVERY KEY IS DERIVED from corpus_l5's helpers. A hand-typed date on a
# calendar instrument is the one error no score can reveal, because a wrong
# date looks exactly like a right one. L4 caught two live defects that way.
#
# THE TRAP LISTS CARRY THE COMMON ERROR, NOT ONLY THE CLEVER ONE. L4's first
# run registered the errors it predicted - suspending a clock over a weekend,
# rolling past a holiday - and missed the plain off-by-one that actually
# happened, so its headline metric undercounted its own mechanism. Every date
# item here lists both neighbours.
#
# FIVE ITEMS ARE UNANSWERABLE and they are not padding. E76 measured the
# production model asserting a figure on 5 of 12 such questions, so this is
# measured headroom. The validator asserts each absence against the built pack.

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from corpus_l5 import (  # noqa: E402
    ACCEPTANCE_CO1_DAYS,
    ACCEPTANCE_CO2_AS_VARIED_DAYS,
    ACCEPTANCE_CO3_DAYS,
    CAP_CO1,
    CAP_CO2_AS_VARIED,
    CAP_FRAMEWORK_DEFAULT,
    DATA_REQUEST_RECEIVED,
    DELIVERY_SITE_A,
    DELIVERY_SITE_B,
    DELIVERY_SITE_C,
    EARLIER_ACCRUAL,
    INVOICE_AMOUNT,
    INVOICE_PAID,
    INVOICE_RECEIVED,
    NOTICE_SERVED,
    STANDSTILL_END,
    STANDSTILL_START,
    add_business_days,
    fixed_compensation,
    is_business_day,
    late_payment_days,
    late_payment_interest,
    months_after,
    years_after,
)
from questions import _matches, _numbers, parse_response  # noqa: E402, F401
from questions_l2 import _is_decline as _shared_is_decline  # noqa: E402

# The shared vocabulary is written in the singular past - "does not state",
# "not stated" - and misses the form models actually use for a multi-document
# pack: "the documents do not state", "the record does not contain". Scoring
# that as an over-claim would invert the single number this bank exists to
# produce. The shared list stays untouched: L2, L3 and L4 verdicts are banked
# against it and widening it would restate them without anyone asking.
_L5_EXTRA_DECLINE = (
    "do not state",
    "do not specify",
    "do not say",
    "do not contain",
    "do not address",
    "does not contain",
    "no information",
    "is not given",
    "are not given",
    "not provided",
    "nowhere in",
    "no mention",
)


def _is_decline(answer: str) -> bool:
    """The shared decline vocabulary, plus the plural and present-tense forms."""
    if _shared_is_decline(answer):
        return True
    low = (answer or "").lower()
    return any(p in low for p in _L5_EXTRA_DECLINE)


from questions_l4 import _dates, _off_by_one  # noqa: E402

CATEGORIES_L5 = [
    "acceptance_window",
    "payment_clock",
    "statutory_period",
    "composition",
    "which_instrument",
    "precedence",
    "conflict",
    "exhaustive",
    "underspecified",
]

BANDS = ("R", "E")

# --------------------------------------------------------------- derived keys

ACC_A = add_business_days(DELIVERY_SITE_A, ACCEPTANCE_CO1_DAYS)  # 2026-03-24
ACC_B = add_business_days(DELIVERY_SITE_B, ACCEPTANCE_CO2_AS_VARIED_DAYS)  # 2026-04-08
ACC_B_UNVARIED = add_business_days(DELIVERY_SITE_B, 12)  # 2026-04-16
ACC_C = add_business_days(DELIVERY_SITE_C, ACCEPTANCE_CO3_DAYS)  # 2026-05-11

# The plain-calendar error: counting calendar days instead of Business Days.
ACC_A_CALENDAR = DELIVERY_SITE_A + dt.timedelta(days=ACCEPTANCE_CO1_DAYS)
ACC_C_CALENDAR = DELIVERY_SITE_C + dt.timedelta(days=ACCEPTANCE_CO3_DAYS)
# The weekday error: counting Mon-Fri but ignoring the public holiday.
ACC_A_NO_HOLIDAY = ACC_A - dt.timedelta(days=1)
ACC_C_NO_HOLIDAY = ACC_C - dt.timedelta(days=3)  # 11 May Mon back over the weekend

DUE_DATE = INVOICE_RECEIVED + dt.timedelta(days=30)  # 2026-06-11
DAYS_LATE = late_payment_days(INVOICE_RECEIVED, INVOICE_PAID)  # 77
INTEREST = late_payment_interest(INVOICE_AMOUNT, DAYS_LATE)  # 393.99
FIXED_COMP = fixed_compensation(INVOICE_AMOUNT)  # 100
TOTAL_DUE = INTEREST + FIXED_COMP  # 493.99
# Counting from receipt rather than from the day after the due date.
DAYS_FROM_RECEIPT = (INVOICE_PAID - INVOICE_RECEIVED).days

DATA_ONE_MONTH = months_after(DATA_REQUEST_RECEIVED, 1)  # 2026-06-30
DATA_PARALLEL = months_after(DATA_REQUEST_RECEIVED, 3)  # 2026-08-31
DATA_SEQUENTIAL_TRAP = months_after(DATA_ONE_MONTH, 2)  # 2026-08-30

LIMITATION_PLAIN = years_after(EARLIER_ACCRUAL, 6)  # 2026-09-14
STANDSTILL_DAYS = (STANDSTILL_END - STANDSTILL_START).days + 1  # 275
LIMITATION_WITH_STANDSTILL = LIMITATION_PLAIN + dt.timedelta(days=STANDSTILL_DAYS)


def _last_business_day_of_month(year: int, month: int) -> dt.date:
    """The last Business Day of a month, per FA clause 4.1 and the pack calendar."""
    first_of_next = dt.date(year + (month == 12), month % 12 + 1, 1)
    day = first_of_next - dt.timedelta(days=1)
    while not is_business_day(day):
        day -= dt.timedelta(days=1)
    return day


NOTICE_TWO_MONTHS = months_after(NOTICE_SERVED, 2)  # 2026-10-12
NOTICE_EFFECTIVE = _last_business_day_of_month(
    NOTICE_TWO_MONTHS.year, NOTICE_TWO_MONTHS.month
)  # 2026-10-30
NOTICE_CALENDAR_MONTH_END = dt.date(
    NOTICE_TWO_MONTHS.year, NOTICE_TWO_MONTHS.month, 31
)  # 2026-10-31

# --------------------------------------------------------------------- items

QUESTIONS_L5: list[dict] = [
    # ============================================================== BAND R
    # The clause, the document and the trigger are all named. Only the walk
    # is left.
    {
        "id": "R01",
        "band": "R",
        "difficulty": "D1",
        "category": "payment_clock",
        "question": (
            "Invoice INV-8841 was received by the Client on 12 May 2026. Framework "
            "Agreement clause 5.1 says invoices fall due thirty days after receipt. "
            "On what date did INV-8841 fall due? Give the date."
        ),
        "cite_doc": ["FA-2025", "CHRON-1"],
        "cite_clause": ["5.1"],
        "expect": {
            "kind": "date",
            "want": DUE_DATE,
            "off_by_calendar": [
                months_after(INVOICE_RECEIVED, 1),
                *_off_by_one(DUE_DATE),
            ],
        },
    },
    {
        "id": "R02",
        "band": "R",
        "difficulty": "D2",
        "category": "statutory_period",
        "question": (
            "A data access request was received on 31 May 2026. STAT-1 section S.2 "
            "gives one month to answer, and Framework Agreement clause 4.3 states how "
            "a month-period expires. Applying only the ONE-MONTH period, what is the "
            "last day on which a response may be provided? Give the date."
        ),
        "cite_doc": ["STAT-1", "FA-2025"],
        "cite_clause": ["S.2", "4.3"],
        "expect": {
            "kind": "date",
            "want": DATA_ONE_MONTH,
            # NOTE: a "+30 days" trap was removed here. 31 May plus 30 days IS
            # 30 June, which is also the clamped one-month answer, so the
            # trap equalled the key and could detect nothing. This item
            # therefore tests clause 4.3's month-end clamp ONLY, and cannot
            # distinguish a model that counted 30 days and got lucky.
            "off_by_calendar": [dt.date(2026, 7, 1), *_off_by_one(DATA_ONE_MONTH)],
        },
    },
    {
        "id": "R03",
        "band": "R",
        "difficulty": "D3",
        "category": "acceptance_window",
        "question": (
            "The Site A sensor array was delivered on 11 March 2026 under CO-1, whose "
            "Acceptance Window is eight Business Days from Delivery. Apply Framework "
            "Agreement clauses 4.1 and 4.2 and the CAL-2026 holiday list. On what date "
            "does the Acceptance Window for Site A expire? Give the date."
        ),
        "cite_doc": ["CO-1", "FA-2025", "CAL-2026"],
        "cite_clause": ["4.1", "4.2"],
        "expect": {
            "kind": "date",
            "want": ACC_A,
            "off_by_calendar": [ACC_A_CALENDAR, ACC_A_NO_HOLIDAY, *_off_by_one(ACC_A)],
        },
    },
    {
        "id": "R04",
        "band": "R",
        "difficulty": "D3",
        "category": "acceptance_window",
        "question": (
            "The Site C sensor array was delivered on 28 April 2026 under CO-3, whose "
            "Acceptance Window is eight Business Days from Delivery. Apply Framework "
            "Agreement clauses 4.1 and 4.2 and the CAL-2026 holiday list. On what date "
            "does the Acceptance Window for Site C expire? Give the date."
        ),
        "cite_doc": ["CO-3", "FA-2025", "CAL-2026"],
        "cite_clause": ["4.1", "4.2"],
        "expect": {
            "kind": "date",
            "want": ACC_C,
            "off_by_calendar": [ACC_C_CALENDAR, ACC_C_NO_HOLIDAY, *_off_by_one(ACC_C)],
        },
    },
    {
        "id": "R05",
        "band": "R",
        "difficulty": "D3",
        "category": "acceptance_window",
        "question": (
            "The Site B sensor array was delivered on 30 March 2026. Take it as given "
            "that the Acceptance Window that applies to Site B is SIX Business Days "
            "from Delivery. Apply Framework Agreement clauses 4.1 and 4.2 and the "
            "CAL-2026 holiday list. On what date does that window expire? Give the date."
        ),
        "cite_doc": ["FA-2025", "CAL-2026"],
        "cite_clause": ["4.1", "4.2"],
        "expect": {
            "kind": "date",
            "want": ACC_B,
            "off_by_calendar": [
                ACC_B_UNVARIED,
                DELIVERY_SITE_B + dt.timedelta(days=6),
                ACC_B - dt.timedelta(days=1),
                ACC_B + dt.timedelta(days=1),
            ],
        },
    },
    {
        "id": "R06",
        "band": "R",
        "difficulty": "D3",
        "category": "payment_clock",
        "question": (
            "INV-8841 was received on 12 May 2026 and paid on 27 August 2026. Framework "
            "Agreement clause 5.1 gives thirty days to pay and clause 5.2 says interest "
            "runs from the day after the due date to the day of payment inclusive. For "
            "how many days does interest run? Give the number."
        ),
        "cite_doc": ["FA-2025", "CHRON-1"],
        "cite_clause": ["5.1", "5.2"],
        "expect": {
            "kind": "numeric",
            "values": [DAYS_LATE],
            "tol_abs": 0.5,
            "off_by_calendar": [DAYS_FROM_RECEIPT, DAYS_LATE - 1, DAYS_LATE + 1],
        },
    },
    {
        "id": "R07",
        "band": "R",
        "difficulty": "D4",
        "category": "payment_clock",
        "question": (
            "Using the same invoice - EUR 18,400 received 12 May 2026, paid 27 August "
            "2026 - and Framework Agreement clause 5.2 (Reference Rate 2.15% plus eight "
            "percentage points, 365-day basis), how much INTEREST is payable? Give the "
            "amount in euro."
        ),
        "cite_doc": ["FA-2025"],
        "cite_clause": ["5.2"],
        "expect": {
            "kind": "numeric",
            "values": [INTEREST],
            "tol_rel": 0.01,
            "off_by_calendar": [
                late_payment_interest(INVOICE_AMOUNT, DAYS_FROM_RECEIPT),
                INVOICE_AMOUNT * 0.08 * DAYS_LATE / 365,
            ],
        },
    },
    {
        "id": "R08",
        "band": "R",
        "difficulty": "D4",
        "category": "payment_clock",
        "question": (
            "For the same late payment, Framework Agreement clause 5.3 adds fixed "
            "compensation under the band table in STAT-1 section S.1. What is the TOTAL "
            "of interest plus fixed compensation? Give one amount in euro."
        ),
        "cite_doc": ["FA-2025", "STAT-1"],
        "cite_clause": ["5.2", "5.3", "S.1"],
        "expect": {
            "kind": "numeric",
            "values": [TOTAL_DUE],
            "tol_rel": 0.01,
            "partial": [INTEREST, FIXED_COMP],
            "off_by_calendar": [INTEREST + 70, INTEREST + 40],
        },
    },
    {
        "id": "R09",
        "band": "R",
        "difficulty": "D4",
        "category": "statutory_period",
        "question": (
            "The data access request received on 31 May 2026 was validly extended by the "
            "two further months in STAT-1 section S.3. Section S.3 and Framework "
            "Agreement clause 4.4 both state that the extension runs from the SAME date "
            "of receipt, in parallel, and that the later expiry governs. What is the last "
            "day on which a response may now be provided? Give the date."
        ),
        "cite_doc": ["STAT-1", "FA-2025"],
        "cite_clause": ["S.3", "4.3", "4.4"],
        "expect": {
            "kind": "date",
            "want": DATA_PARALLEL,
            "off_by_calendar": [
                DATA_SEQUENTIAL_TRAP,
                DATA_REQUEST_RECEIVED + dt.timedelta(days=90),
                # AMENDED 2026-08-28, after the E78 arms ran. The registered
                # traps carried the errors I PREDICTED - the sequential
                # reading, a 90-day count - and missed the one that happened:
                # Qwen3.8 answered 31 July, the TWO-month extension applied
                # alone with the parallel one-month period dropped. It scored a
                # generic `wrong` and the tier's own diagnostic missed its own
                # mechanism. This is the third time in this repository that a
                # trap list has held the clever errors and not the real one;
                # L4 recorded the same thing after its first run.
                # RELABELS ONLY: this moves Qwen3.8's R09 from `wrong` to
                # `off_by_calendar`. No `correct` count moves, on any arm.
                months_after(DATA_REQUEST_RECEIVED, 2),
                *_off_by_one(DATA_PARALLEL),
            ],
        },
    },
    {
        "id": "R10",
        "band": "R",
        "difficulty": "D5",
        "category": "statutory_period",
        "question": (
            "In the earlier 2019 dispute the cause of action accrued on 14 September "
            "2020. STAT-1 section S.4 gives six years. The parties executed a standstill "
            "running from 1 March 2023 to 30 November 2023 inclusive, and section S.5 "
            "says the period is suspended for its duration and resumes the day after it "
            "ends. On what date does the earlier claim become statute-barred? Give the date."
        ),
        "cite_doc": ["STAT-1", "BG-1"],
        "cite_clause": ["S.4", "S.5"],
        "expect": {
            "kind": "date",
            "want": LIMITATION_WITH_STANDSTILL,
            "wrong_trigger": [
                years_after(STANDSTILL_END, 6),
                years_after(dt.date(2023, 3, 2), 6),
            ],
            "off_by_calendar": [
                LIMITATION_PLAIN,
                LIMITATION_PLAIN + dt.timedelta(days=274),
                *_off_by_one(LIMITATION_WITH_STANDSTILL),
            ],
        },
    },
    {
        "id": "R11",
        "band": "R",
        "difficulty": "D2",
        "category": "statutory_period",
        "question": (
            "STAT-1 section S.5 says the limitation period is suspended for the duration "
            "of a standstill, counting neither the days before nor after it. The "
            "standstill in the earlier dispute ran from 1 March 2023 to 30 November "
            "2023 inclusive. For how many days was the period suspended? Give the number."
        ),
        "cite_doc": ["BG-1", "STAT-1"],
        "cite_clause": ["S.5"],
        "expect": {
            "kind": "numeric",
            "values": [STANDSTILL_DAYS],
            "tol_abs": 0.5,
            "off_by_calendar": [STANDSTILL_DAYS - 1, STANDSTILL_DAYS + 1, 270],
        },
    },
    {
        "id": "R12",
        "band": "R",
        "difficulty": "D5",
        "category": "composition",
        "question": (
            "Notice of termination for convenience was served on 12 August 2026 in "
            "respect of CO-3, whose Notice Period is two months. Framework Agreement "
            "clause 3.4 ALSO requires a termination for convenience to take effect on "
            "the last Business Day of a month, and states that clause 3.4 and the Notice "
            "Period are cumulative. Applying both, on what date does the termination "
            "take effect? Give the date."
        ),
        "cite_doc": ["FA-2025", "CO-3", "CHRON-1", "CAL-2026"],
        "cite_clause": ["3.4", "4.1"],
        "expect": {
            "kind": "date",
            "want": NOTICE_EFFECTIVE,
            "off_by_calendar": [
                NOTICE_TWO_MONTHS,
                NOTICE_CALENDAR_MONTH_END,
                *_off_by_one(NOTICE_EFFECTIVE),
            ],
        },
    },
    # ============================================================== BAND E
    # One step of reasoning. The work is locating, reconciling or noticing an
    # absence.
    {
        "id": "E01",
        "band": "E",
        "difficulty": "D1",
        "category": "which_instrument",
        "question": (
            "Which Call-Off Order governs the sensor array delivered to Site B (Ennis)? "
            "Give its document ID."
        ),
        "cite_doc": ["CO-2", "CHRON-1"],
        "cite_clause": [],
        "expect": {"kind": "choice", "want": "co-2", "aliases": ["call-off order 2"]},
    },
    {
        "id": "E02",
        "band": "E",
        "difficulty": "D3",
        "category": "precedence",
        "question": (
            "What Liability Cap applies to the Site B (Ennis) work? Give the amount in euro."
        ),
        "cite_doc": ["VAR-1", "CO-2", "FA-2025"],
        "cite_clause": ["2.1"],
        "expect": {
            "kind": "numeric",
            "values": [CAP_CO2_AS_VARIED],
            "tol_abs": 0.5,
            "partial": [320_000],
            "wrong_trigger": [CAP_FRAMEWORK_DEFAULT],
        },
    },
    {
        "id": "E03",
        "band": "E",
        "difficulty": "D3",
        "category": "precedence",
        "question": (
            "What Liability Cap applies to the Site A (Drogheda) work? Give the amount "
            "in euro."
        ),
        "cite_doc": ["CO-1", "FA-2025"],
        "cite_clause": ["2.2"],
        "expect": {
            "kind": "numeric",
            "values": [CAP_CO1],
            "tol_abs": 0.5,
            "wrong_trigger": [CAP_CO2_AS_VARIED, CAP_FRAMEWORK_DEFAULT],
        },
    },
    {
        "id": "E04",
        "band": "E",
        "difficulty": "D3",
        "category": "which_instrument",
        "question": (
            "CO-2 does not state a Notice Period. What Notice Period applies to CO-2, "
            "and which document supplies it?"
        ),
        "cite_doc": ["FA-2025", "CO-2"],
        "cite_clause": ["1.3", "3.3"],
        "expect": {
            "kind": "choice",
            "want": "three months",
            "aliases": ["3 months", "three-month", "three month"],
        },
    },
    {
        "id": "E05",
        "band": "E",
        "difficulty": "D4",
        "category": "exhaustive",
        "question": (
            "Of the three Call-Off Orders, HOW MANY state a Notice Period of their own, "
            "and which ones? Give the number and the document IDs."
        ),
        "cite_doc": ["CO-1", "CO-2", "CO-3"],
        "cite_clause": [],
        # Exhaustiveness rides on the COUNT, not on forbidding the excluded
        # document. A correct answer names CO-2 in order to exclude it, so a
        # `forbid` on "co-2" would mark the right answer wrong - the same trap
        # E76 AMENDMENT 1 found when a unit was put in `must_not_say`.
        "expect": {
            "kind": "set",
            "require": ["two", "co-1", "co-3"],
            "forbid": [],
            "aliases_for": {
                "two": [r"re:(?<!co-)(?<!\d)2\b", "2 of the three", "2 of 3"]
            },
        },
    },
    {
        "id": "E06",
        "band": "E",
        "difficulty": "D3",
        "category": "conflict",
        "question": (
            "On what date was the Site A sensor array delivered? The record contains two "
            "different dates. Give the date that governs."
        ),
        "cite_doc": ["CHRON-1", "NOTE-4"],
        "cite_clause": [],
        "expect": {
            "kind": "date",
            "want": DELIVERY_SITE_A,
            "wrong_trigger": [dt.date(2026, 3, 9)],
        },
    },
    {
        "id": "E07",
        "band": "E",
        "difficulty": "D4",
        "category": "conflict",
        "question": (
            "The operations team's file note records a belief that the Site B liability "
            "cap is the standard EUR 250,000 figure. Is that belief correct? Answer yes "
            "or no."
        ),
        "cite_doc": ["NOTE-4", "VAR-1", "CO-2"],
        "cite_clause": ["2.1"],
        "expect": {"kind": "yes_no", "want": "no"},
    },
    {
        "id": "E08",
        "band": "E",
        "difficulty": "D2",
        "category": "which_instrument",
        "question": (
            "Under which Call-Off Order was the array delivered on 28 April 2026, and "
            "what Acceptance Window does that Call-Off Order state? Give the document ID "
            "and the number of Business Days."
        ),
        "cite_doc": ["CO-3", "CHRON-1"],
        "cite_clause": [],
        "expect": {
            "kind": "set",
            "require": ["co-3", "eight"],
            "forbid": [],
            "aliases_for": {"eight": ["8 business", "8 bd"]},
        },
    },
    {
        "id": "E09",
        "band": "E",
        "difficulty": "D2",
        "category": "underspecified",
        "question": (
            "What is the governing law of the Framework Agreement, and which courts have "
            "jurisdiction over a dispute under it? Give the answer."
        ),
        "cite_doc": [],
        "cite_clause": [],
        "expect": {"kind": "underspecified"},
    },
    {
        "id": "E10",
        "band": "E",
        "difficulty": "D2",
        "category": "underspecified",
        "question": (
            "What is the contract value of CO-2 - the price the Client pays the Supplier "
            "under it? Give the figure."
        ),
        "cite_doc": [],
        "cite_clause": [],
        "expect": {"kind": "underspecified"},
    },
    {
        "id": "E11",
        "band": "E",
        "difficulty": "D3",
        "category": "underspecified",
        "question": (
            "Did the Site C sensor array pass acceptance testing? State the outcome."
        ),
        "cite_doc": [],
        "cite_clause": [],
        "expect": {"kind": "underspecified"},
    },
    {
        "id": "E12",
        "band": "E",
        "difficulty": "D3",
        "category": "underspecified",
        "question": (
            "How many employees does Northgate Systems Limited have? Give the number."
        ),
        "cite_doc": [],
        "cite_clause": [],
        "expect": {"kind": "underspecified"},
    },
]


def grade_answer_l5(question: dict, answer: str | None) -> str:
    """correct | partial | wrong | off_by_calendar | wrong_trigger | over_claim |
    format_error.

    The vocabulary is L4's, unchanged, so failure SHAPES stay comparable across
    the two tiers even though the totals are not a continuation of a ladder.
    """
    if answer is None:
        return "format_error"
    spec = question["expect"]
    kind = spec["kind"]

    if kind == "underspecified":
        return "correct" if _is_decline(answer) else "over_claim"

    # THE POSITIVE MATCH RUNS FIRST, AND THE ORDER IS THE WHOLE POINT.
    # L4 checks `_is_decline` before the kind branch, which is safe there. It is
    # NOT safe here: several band-E items concern a document that is SILENT on
    # something, so a correct answer says "CO-2 does not state a Notice Period,
    # so the Framework's three months applies" - and "does not state" is a
    # decline pattern. Checking decline first scores that `wrong`. Caught by
    # reading the decline vocabulary against the item text before any run, not
    # by seeing a model lose a point it had earned.
    verdict = _grade_by_kind(question, answer, spec, kind)
    if verdict == "correct":
        return verdict

    # No positive match. NOW a decline is a decline: wrong, and the SAFE
    # direction of wrong. Checked here rather than first, because a correct
    # answer explaining that a document is silent contains decline wording and
    # would otherwise lose the point it earned.
    if _is_decline(answer):
        return "wrong"

    return verdict


def _grade_by_kind(question: dict, answer: str, spec: dict, kind: str) -> str:
    """The kind-specific match. Returns `wrong` when nothing matches."""
    if kind == "date":
        found = _dates(answer)
        if not found:
            return "format_error"
        if spec["want"] in found:
            return "correct"
        for label in ("wrong_trigger", "off_by_calendar"):
            if any(c in found for c in spec.get(label, ())):
                return label
        return "wrong"

    if kind == "numeric":
        found = _numbers(answer)
        tol_rel, tol_abs = spec.get("tol_rel", 0.0), spec.get("tol_abs", 0.0)
        if _matches(found, spec["values"], tol_rel, tol_abs):
            return "correct"
        for label in ("wrong_trigger", "off_by_calendar", "partial"):
            targets = spec.get(label)
            if targets and _matches(found, targets, tol_rel, tol_abs):
                return label
        return "wrong"

    if kind == "yes_no":
        if _is_decline(answer):
            # "The record does not state" contains "not" and would otherwise
            # parse as "no" - scoring a decline correct on every no-answer item.
            return "wrong"
        low = answer.lower()
        said_yes = bool(re.search(r"\byes\b", low))
        said_no = bool(re.search(r"\bno\b|\bnot\b", low))
        if said_yes and not said_no:
            return "correct" if spec["want"] == "yes" else "wrong"
        if said_no and not said_yes:
            return "correct" if spec["want"] == "no" else "wrong"
        return "wrong"

    if kind == "choice":
        low = answer.lower()
        if re.search(rf"\(?\b{re.escape(spec['want'])}\b\)?", low):
            return "correct"
        if any(alias in low for alias in spec.get("aliases", ())):
            return "correct"
        return "wrong"

    if kind == "set":
        # An exhaustive list is only right if it is COMPLETE and CLEAN. Scoring
        # it on the required tokens alone would give full marks to an answer
        # that lists everything, which is the posture E54's defect_absent pair
        # exists to stop.
        low = answer.lower()
        aliases = spec.get("aliases_for", {})

        def present(token: str) -> bool:
            if token in low:
                return True
            for alias in aliases.get(token, ()):
                # An alias may be a regex, marked "re:". The count token needs
                # one: a bare "2" has to match "2; CO-1 and CO-3" and must NOT
                # match the "2" inside "CO-2", or an answer listing every
                # document would satisfy the count and the posture check would
                # stop working. Found in the pilot, where a fully correct
                # answer scored `partial`.
                if alias.startswith("re:"):
                    if re.search(alias[3:], low):
                        return True
                elif alias in low:
                    return True
            return False

        if not all(present(t) for t in spec["require"]):
            return "partial" if any(present(t) for t in spec["require"]) else "wrong"
        if any(present(t) for t in spec.get("forbid", ())):
            return "wrong"
        return "correct"

    raise ValueError(
        f"unknown expect kind {kind!r} for L5 question {question['id']}\n"
        f"hint: add a branch to grade_answer_l5, or fix the question's expect spec"
    )
