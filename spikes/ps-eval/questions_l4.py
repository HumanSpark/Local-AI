# File: questions_l4.py
# Purpose: Level-4 questions and graders - periods that must be WALKED, plus the adversarial "what is wrong" tier.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: Fifteen questions over corpus_l4.build_pack_l4, in nine
# categories, every one graded by date, numeric, choice or decline matching.
# No LLM judge anywhere.
#
# BUILT TO BE FAILED. Qwen3.8-27B has saturated every purpose-built
# instrument here - L1 20/20, L2 12/12, L3 12/12 at every scale. F60 is the
# only measured theory of what actually discriminates, and it is blunt: a
# second BASIS to select does not (m12 returned 4/5 from all three models and
# separated nothing), a period that must be WALKED does (m11 6/15, m13 7/15).
# So eleven of these fifteen require counting a period across a real calendar
# under a rule that changes what counts, and the calendar is in the pack.
#
# THE OUTCOME VOCABULARY IS L2's, PLUS TWO. This is deliberate: L4 changes
# the domain, so its TOTALS are not a continuation of the L1-L3 ladder, but
# its failure SHAPES still are. Two are added, for the same reason the tier
# exists (F20 - a wrong answer whose shape is diagnostic must not be folded
# into a generic `wrong`):
#
#   off_by_calendar  the right method, the wrong count. Treated a month as 30
#                    days, suspended an hours-period over a weekend, added two
#                    month-periods in sequence rather than to one trigger.
#                    This is F60's mechanism, isolated, and it is the single
#                    number this tier exists to produce.
#   wrong_trigger    counted correctly from the wrong event - from discovery
#                    rather than breach, from the invoice rather than the end
#                    of the payment period. Distinguishing it from
#                    off_by_calendar matters, because one is arithmetic and
#                    the other is reading, and they need different fixes.
#
# THE `defect_absent` CATEGORY IS NOT PADDING. It is the inverse of
# `defect_find`, and without it "what is wrong with this contract" rewards a
# posture: a model that always answers "yes, that is inconsistent" scores
# full marks on the adversarial category while understanding nothing. Both
# defect_absent items point at real mismatches which are nonetheless outside
# the scope of what the engagement letter requires to be passed down. This is
# the same discipline as L2's scoped-precedence pair.
#
# WHAT THIS TIER IS NOT. It is not longer - the pack is roughly 4K tokens.
# Length is E35's question and must not be conflated with this one.

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_l4 import (  # noqa: E402
    ACCRUAL_DATE,
    BREACH_AWARE,
    COMMENCEMENT_DATE,
    DISCOVERY_DATE,
    DSR_RECEIVED,
    EARLIER_CONTRACT_DATE,
    INVOICE_AMOUNT,
    INVOICE_PAID,
    INVOICE_RECEIVED,
    NOTICE_SERVED,
    end_of_month,
    fee_total,
    fixed_compensation,
    late_payment_days,
    late_payment_interest,
    months_after,
)
from questions import (  # noqa: E402
    _matches,
    _numbers,
    parse_response,  # noqa: F401 - re-exported so the runner imports one module
)
from questions_l2 import _is_decline  # noqa: E402

# --------------------------------------------------------------- date parsing
#
# Answers arrive as "28 February 2026", "2026-02-28", "28/02/2026" and
# "February 28, 2026". All four are the same answer and none is more correct,
# so the grader normalises rather than demanding a format - a model marked
# wrong for writing a date the way a solicitor writes it would be measuring
# instruction-following, which is F20's trap.

_MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], start=1)}
for _full, _i in list(_MONTHS.items()):
    _MONTHS[_full[:3]] = _i

_ISO_RE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DMY_RE = re.compile(r"\b(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{4})\b")
_TEXT_DMY_RE = re.compile(
    r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b")
_TEXT_MDY_RE = re.compile(
    r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b")


def _dates(text: str) -> list[dt.date]:
    """Every date in `text`, in the order found, deduplicated.

    Returns an empty list rather than raising: "no date in the answer" is a
    real outcome the grader has to score, not an error in the grader.
    """
    out: list[dt.date] = []

    def add(y: int, m: int, d: int) -> None:
        try:
            value = dt.date(y, m, d)
        except ValueError:
            return
        if value not in out:
            out.append(value)

    for y, m, d in _ISO_RE.findall(text):
        add(int(y), int(m), int(d))
    for d, m, y in _DMY_RE.findall(text):
        add(int(y), int(m), int(d))
    for d, name, y in _TEXT_DMY_RE.findall(text):
        if (month := _MONTHS.get(name.lower())) is not None:
            add(int(y), month, int(d))
    for name, d, y in _TEXT_MDY_RE.findall(text):
        if (month := _MONTHS.get(name.lower())) is not None:
            add(int(y), month, int(d))
    return out


# ------------------------------------------------------------------- answers
#
# Every key is DERIVED from the pack's dates. On a calendar instrument a
# hand-typed key is the one error no score can reveal: a wrong date looks
# exactly like a right one.

def _off_by_one(day: dt.date) -> list[dt.date]:
    """The day either side of `day`.

    Added 2026-08-17 after E54's first run. The registered `off_by_calendar`
    trap lists carried the errors that were PREDICTED - suspending a 72-hour
    clock over a weekend, rolling past a public holiday - and not the one that
    actually happened. Two models answered 5 April where the answer was 6
    April, a plain off-by-one in day counting, and both graded as a generic
    `wrong`, so the tier's headline metric undercounted its own mechanism.
    A trap list that only contains the clever errors misses the common one.
    """
    return [day - dt.timedelta(days=1), day + dt.timedelta(days=1)]


DSR_ONE_MONTH = months_after(DSR_RECEIVED, 1)                     # 2026-02-28
DSR_EXTENDED = months_after(DSR_RECEIVED, 3)                      # 2026-04-30
DSR_SEQUENTIAL_TRAP = months_after(DSR_ONE_MONTH, 2)              # 2026-04-28
BREACH_DEADLINE = BREACH_AWARE + dt.timedelta(hours=72)           # Mon 6 Apr
BREACH_WEEKEND_TRAP = BREACH_AWARE + dt.timedelta(hours=72, days=2)
BREACH_HOLIDAY_TRAP = BREACH_AWARE + dt.timedelta(hours=72, days=1)

INTEREST_DAYS = late_payment_days(INVOICE_RECEIVED, INVOICE_PAID)  # 77
INTEREST = round(late_payment_interest(INVOICE_AMOUNT, INTEREST_DAYS), 2)
COMPENSATION = fixed_compensation(INVOICE_AMOUNT)                  # 100
TOTAL_ADDITIONAL = round(INTEREST + COMPENSATION, 2)               # 493.99

LIMITATION_LAST_DAY = dt.date(ACCRUAL_DATE.year + 6, ACCRUAL_DATE.month, ACCRUAL_DATE.day)
LIMITATION_FROM_DISCOVERY = dt.date(
    DISCOVERY_DATE.year + 6, DISCOVERY_DATE.month, DISCOVERY_DATE.day)
LIMITATION_FROM_CONTRACT = dt.date(
    EARLIER_CONTRACT_DATE.year + 6, EARLIER_CONTRACT_DATE.month, EARLIER_CONTRACT_DATE.day)

NOTICE_PLAIN = end_of_month(months_after(NOTICE_SERVED, 3))        # 2026-11-30
FIRST_ANNIVERSARY = dt.date(
    COMMENCEMENT_DATE.year + 1, COMMENCEMENT_DATE.month, COMMENCEMENT_DATE.day)


def _first_month_end_on_or_after(day: dt.date) -> dt.date:
    """Earliest calendar month-end that is not before `day` (ENG 2.2 with 2.3)."""
    candidate = end_of_month(day)
    return candidate if candidate >= day else end_of_month(candidate + dt.timedelta(days=1))


NOTICE_GOVERNING = _first_month_end_on_or_after(max(NOTICE_PLAIN, FIRST_ANNIVERSARY))
FEES_TO_TERMINATION = fee_total(dt.date(2026, 9, 1), dt.date(2026, 12, 1))   # 106,800

# The subcontract's own cover is 350,000 rather than a round 500,000 for one
# reason: at 500,000 the SHORTFALL would have equalled the subcontract's own
# figure, so a model reading the cover straight off the page and never
# subtracting anything would have graded `correct`. That is E48's distractor
# trap - a figure that collides with a real answer is the one error no score
# can reveal. tools/validate_ps_eval_l4.py now asserts no such collision.
SUB_INSURANCE_REQUIRED = 1_000_000        # ENG clause 6, subcontractor limb
SUB_INSURANCE_ACTUAL = 350_000            # SUB clause 5
FIRM_INSURANCE = 2_000_000                # ENG clause 6, the Firm's own limb
SUB_INSURANCE_GAP = SUB_INSURANCE_REQUIRED - SUB_INSURANCE_ACTUAL   # 650,000
SUB_INSURANCE_WRONG_BASIS = FIRM_INSURANCE - SUB_INSURANCE_ACTUAL   # 1,650,000
# TWO years rather than three, for the same reason as the insurance figure
# above: at three the shortfall (6 - 3) would have equalled the subcontract's
# own retention period, and a model reading "three years" off the page would
# have graded `correct` without subtracting anything. The validator asserts
# the key differs from both operands.
SUB_RECORDS_REQUIRED_YEARS = 6            # ENG clause 5
SUB_RECORDS_ACTUAL_YEARS = 2              # SUB clause 4
SUB_RECORDS_SHORTFALL_YEARS = SUB_RECORDS_REQUIRED_YEARS - SUB_RECORDS_ACTUAL_YEARS  # 4

CATEGORIES_L4 = [
    "statutory_period", "breach_clock", "interest_calc",
    "notice_period", "fee_basis", "survival",
    "defect_find", "defect_absent", "underspecified",
]

QUESTIONS_L4: list[dict] = [
    # ------------------------------------------------- statutory_period (x3)
    {
        "id": "P1",
        "category": "statutory_period",
        "question": (
            "Ardmore Composites received a data subject access request. Under the "
            "one-month period in STAT-DP section A, and applying the counting rules in "
            "section C, what is the LAST DAY on which a response may be provided? "
            "Give the date."
        ),
        "cite_doc": ["STAT-DP", "CHRON"],
        "cite_clause": ["A", "C.1"],
        # 31 January has no corresponding day in February, so rule C.1 rolls it
        # back to the last day of the month - and February 2026 has 28 days.
        # Counting 30 or 31 days instead lands on 2 or 3 March.
        "expect": {"kind": "date", "want": DSR_ONE_MONTH,
                   "off_by_calendar": [DSR_RECEIVED + dt.timedelta(days=30),
                                       DSR_RECEIVED + dt.timedelta(days=31),
                                       *_off_by_one(DSR_ONE_MONTH)]},
    },
    {
        "id": "P2",
        "category": "statutory_period",
        "question": (
            "Assume the controller validly extends the response period by the two "
            "further months permitted by STAT-DP section A. What is the LAST DAY on "
            "which a response may then be provided? Give the date."
        ),
        "cite_doc": ["STAT-DP"],
        "cite_clause": ["A", "C.1", "C.2"],
        # Rule C.2 adds both periods to the SAME trigger: 31 January plus three
        # months, rolled back to 30 April. Counting them in sequence from the
        # 28 February expiry gives 28 April - the whole point of C.2.
        "expect": {"kind": "date", "want": DSR_EXTENDED,
                   "off_by_calendar": [DSR_SEQUENTIAL_TRAP,
                                       DSR_RECEIVED + dt.timedelta(days=90),
                                       *_off_by_one(DSR_EXTENDED)]},
    },
    {
        "id": "P3",
        "category": "statutory_period",
        "question": (
            "What is the LAST DAY on which the Firm may issue proceedings against "
            "Kilbeg Analytics in respect of the defective dataset? Give the date."
        ),
        "cite_doc": ["STAT-LIM", "CHRON"],
        "cite_clause": ["1", "2", "3"],
        # Three candidate trigger dates sit in CHRON on purpose: the breach, the
        # discovery, and the earlier contract. STAT-LIM paragraph 2 names which
        # governs, so choosing another is a reading failure, not arithmetic.
        "expect": {"kind": "date", "want": LIMITATION_LAST_DAY,
                   "wrong_trigger": [LIMITATION_FROM_DISCOVERY, LIMITATION_FROM_CONTRACT],
                   "off_by_calendar": [LIMITATION_LAST_DAY - dt.timedelta(days=1),
                                       LIMITATION_LAST_DAY + dt.timedelta(days=1)]},
    },
    # ----------------------------------------------------- breach_clock (x1)
    {
        "id": "B1",
        "category": "breach_clock",
        "question": (
            "By what date and time at the latest must the Firm notify the supervisory "
            "authority of the personal data breach? Give the date and the time."
        ),
        "cite_doc": ["STAT-DP", "CHRON", "CAL-2026"],
        "cite_clause": ["B", "C.3"],
        # 72 hours from 14:30 on Friday 3 April is 14:30 on Monday 6 April,
        # which is Easter Monday. Rule C.3 says the clock does not stop for the
        # weekend or the holiday, so both plausible professional errors -
        # excluding Saturday and Sunday, or rolling past the public holiday -
        # are named rather than folded into `wrong`.
        "expect": {"kind": "date", "want": BREACH_DEADLINE.date(),
                   "off_by_calendar": [BREACH_WEEKEND_TRAP.date(),
                                       BREACH_HOLIDAY_TRAP.date(),
                                       *_off_by_one(BREACH_DEADLINE.date())]},
    },
    # ---------------------------------------------------- interest_calc (x1)
    {
        "id": "I1",
        "category": "interest_calc",
        "question": (
            "The Firm paid Kilbeg Analytics' invoice K-2026-041 late. Under STAT-LP, "
            "what TOTAL additional amount is Kilbeg Analytics entitled to in respect "
            "of that invoice, comprising interest and fixed compensation? Give the "
            "amount in EUR to two decimal places."
        ),
        "cite_doc": ["STAT-LP", "CHRON"],
        "cite_clause": ["1", "2", "3", "4", "5"],
        # Interest runs from the day after the 30-day period expires, not from
        # the invoice date, on a 365-day basis at 10.15%. Four failure shapes
        # are separable and all four are named.
        "expect": {"kind": "numeric", "values": [TOTAL_ADDITIONAL], "tol_abs": 0.02,
                   # interest right, compensation omitted
                   "partial": [INTEREST],
                   "wrong_trigger": [
                       round(late_payment_interest(
                           INVOICE_AMOUNT, (INVOICE_PAID - INVOICE_RECEIVED).days), 2) + COMPENSATION,
                       round(late_payment_interest(
                           INVOICE_AMOUNT, (INVOICE_PAID - INVOICE_RECEIVED).days), 2)],
                   "off_by_calendar": [
                       round(late_payment_interest(
                           INVOICE_AMOUNT, INTEREST_DAYS, basis=360), 2) + COMPENSATION,
                       round(late_payment_interest(
                           INVOICE_AMOUNT, INTEREST_DAYS, basis=360), 2)]},
    },
    # ---------------------------------------------------- notice_period (x2)
    {
        "id": "N1",
        "category": "notice_period",
        "question": (
            "Disregarding clause 2.3 of the engagement letter entirely, on what date "
            "would the Client's notice of termination take effect under clauses 2.1 "
            "and 2.2? Give the date."
        ),
        "cite_doc": ["ENG-2025", "CHRON"],
        "cite_clause": ["2.1", "2.2"],
        # Two steps: three months from 12 August is 12 November, then clause 2.2
        # carries it to the last day of that month. Stopping at 12 November is
        # the single-step answer and is named.
        "expect": {"kind": "date", "want": NOTICE_PLAIN,
                   "off_by_calendar": [months_after(NOTICE_SERVED, 3),
                                       end_of_month(months_after(NOTICE_SERVED, 2)),
                                       *_off_by_one(NOTICE_PLAIN)]},
    },
    {
        "id": "N2",
        "category": "notice_period",
        "question": (
            "On what date does the Client's notice of termination ACTUALLY take "
            "effect, applying every relevant provision of clause 2? Give the date."
        ),
        "cite_doc": ["ENG-2025", "CHRON"],
        "cite_clause": ["2.1", "2.2", "2.3"],
        # Clause 2.3 blocks 30 November because the first anniversary of the
        # 1 December 2025 Commencement Date is 1 December 2026; clause 2.2 then
        # requires a month end, so the answer walks on to 31 December. Answering
        # 1 December applies 2.3 and forgets 2.2; answering 30 November misses
        # 2.3 altogether, which is N1's answer and is the trap the pair exists
        # to catch.
        "expect": {"kind": "date", "want": NOTICE_GOVERNING,
                   "off_by_calendar": [FIRST_ANNIVERSARY, NOTICE_PLAIN,
                                       *_off_by_one(NOTICE_GOVERNING)]},
    },
    # -------------------------------------------------------- fee_basis (x1)
    {
        "id": "F1",
        "category": "fee_basis",
        # REPAIRED 2026-08-17 after E54's first run. The original asked for the
        # fee "applying the date on which notice actually takes effect" AND
        # named the four months, which specified the period twice. A model that
        # derived and a model that read got different answers and both were
        # defensible - Qwen3.8 answered 79,200, exactly September to November,
        # the period implied by clause 2.2 alone. The question was withdrawn
        # from that run's score. The derivation clause is what goes, not the
        # named period: keeping it would double-penalise a model that already
        # lost N2, and this question exists to test the rate straddle, which is
        # a walked period in its own right. ONE variable per question.
        "question": (
            "What total fee is payable for the four calendar months September 2026 "
            "to December 2026 inclusive? Give the amount in EUR, exclusive of VAT."
        ),
        "cite_doc": ["ENG-2025"],
        "cite_clause": ["1.1", "1.2", "2.4"],
        # The period straddles the 1 October increase, so one month at 24,000
        # and three at 27,600. Multiplying either rate by four is the failure,
        # and both products are named. 79,200 - September to November, the
        # answer the ambiguous wording produced - is named too, so that if it
        # recurs it is visibly the same error rather than a fresh one.
        "expect": {"kind": "numeric", "values": [FEES_TO_TERMINATION], "tol_rel": 0.001,
                   "off_by_calendar": [4 * 24_000, 4 * 27_600, 3 * 24_000 + 27_600,
                                       fee_total(dt.date(2026, 9, 1), dt.date(2026, 11, 1))]},
    },
    # --------------------------------------------------------- survival (x1)
    {
        "id": "S1",
        "category": "survival",
        "question": (
            "Exactly one of the following obligations does NOT survive termination of "
            "the engagement. Which one? Answer with its letter.\n"
            "(a) Keeping the other party's confidential information confidential.\n"
            "(b) Retaining engagement records for six years.\n"
            "(c) Maintaining professional indemnity insurance.\n"
            "(d) Providing a named escalation contact.\n"
            "(e) Permitting the Client to inspect engagement records on reasonable notice."
        ),
        "cite_doc": ["ENG-2025"],
        "cite_clause": ["3.1", "3.2"],
        # (a) cl 4, (b) and (e) cl 5, (c) cl 6 all survive under 3.1; clause 7
        # is excluded by 3.2. The lookup anchor of the tier - every tier needs
        # one item that is not a walk, or a zero score says nothing about where
        # the difficulty is.
        "expect": {"kind": "choice", "want": "d",
                   "aliases": ["escalation contact", "escalation"]},
    },
    # ------------------------------------------------------ defect_find (x3)
    {
        "id": "D1",
        "category": "defect_find",
        "question": (
            "Clause 8 of the engagement letter requires the subcontract to impose "
            "obligations no less onerous than clauses 4, 5 and 6. Exactly one of the "
            "following requirements is ABSENT ENTIRELY from the subcontract, rather "
            "than present but weaker. Which one? Answer with its letter.\n"
            "(a) Keeping confidential information confidential for six years.\n"
            "(b) Retaining records after termination.\n"
            "(c) Maintaining professional indemnity insurance.\n"
            "(d) Notifying the Firm of any cancellation or non-renewal of insurance "
            "cover within five business days.\n"
            "(e) Permitting inspection of records on reasonable notice."
        ),
        "cite_doc": ["ENG-2025", "SUB-KILBEG"],
        "cite_clause": ["6", "8", "3", "4", "5"],
        # (a) SUB cl 3 matches. (b) SUB cl 4 is present at three years - weaker,
        # not absent, and that distinction is the question. (c) SUB cl 5 present
        # at 500,000 - again weaker. (e) SUB cl 4 second limb. (d) appears
        # nowhere in the subcontract.
        "expect": {"kind": "choice", "want": "d",
                   "aliases": ["cancellation", "non-renewal", "notify the firm"]},
    },
    {
        "id": "D2",
        "category": "defect_find",
        "question": (
            "By how many years does the subcontract's record-retention obligation fall "
            "short of what clause 8 of the engagement letter requires to be passed "
            "down? Give the number of years."
        ),
        "cite_doc": ["ENG-2025", "SUB-KILBEG"],
        "cite_clause": ["5", "8", "4"],
        "expect": {"kind": "numeric", "values": [SUB_RECORDS_SHORTFALL_YEARS],
                   "tol_abs": 0.01,
                   # answering the subcontract's own figure, or the required
                   # one, rather than the shortfall between them
                   "partial": [SUB_RECORDS_ACTUAL_YEARS, SUB_RECORDS_REQUIRED_YEARS]},
    },
    {
        "id": "D3",
        "category": "defect_find",
        "question": (
            "By how much, in EUR, does the Subcontractor's professional indemnity "
            "cover fall short of what clause 8 of the engagement letter requires to be "
            "passed down? Give the amount."
        ),
        "cite_doc": ["ENG-2025", "SUB-KILBEG"],
        "cite_clause": ["6", "8", "5"],
        # The engagement letter states TWO insurance figures: 2,000,000 for the
        # Firm and 1,000,000 for a subcontractor. Using the Firm's is the
        # obvious wrong basis and is named rather than folded into `wrong`.
        "expect": {"kind": "numeric", "values": [SUB_INSURANCE_GAP], "tol_rel": 0.001,
                   "wrong_trigger": [SUB_INSURANCE_WRONG_BASIS],
                   # quoting a figure off the page rather than the difference
                   "partial": [SUB_INSURANCE_REQUIRED, SUB_INSURANCE_ACTUAL]},
    },
    # ---------------------------------------------------- defect_absent (x2)
    {
        "id": "X1",
        "category": "defect_absent",
        "question": (
            "Clause 6 of the subcontract limits the Subcontractor's aggregate "
            "liability to EUR 500,000. Does that limit breach any requirement that "
            "clause 8 of the engagement letter imposes on the subcontract? Answer YES "
            "or NO."
        ),
        "cite_doc": ["ENG-2025", "SUB-KILBEG"],
        "cite_clause": ["8", "6"],
        # NO. Clause 8 requires pass-down of clauses 4, 5 and 6 of the
        # ENGAGEMENT LETTER - confidentiality, records, insurance. There is no
        # liability-cap requirement to pass down at all. A model that has just
        # been asked three times what is wrong with this contract will say YES,
        # and the 500,000 figure appearing in both the cap and the insurance
        # shortfall makes that easier to do.
        "expect": {"kind": "yes_no", "want": "no"},
    },
    {
        "id": "X2",
        "category": "defect_absent",
        "question": (
            "Clause 7 of the subcontract permits termination on one month's notice, "
            "where the engagement letter requires three months. Does the subcontract's "
            "notice period breach any requirement that clause 8 of the engagement "
            "letter imposes on the subcontract? Answer YES or NO."
        ),
        "cite_doc": ["ENG-2025", "SUB-KILBEG"],
        "cite_clause": ["8", "7", "2.1"],
        # NO, for the same reason and by a different route: termination notice
        # is not among clauses 4, 5 and 6. Two samples, because a single
        # inverse item cannot separate understanding from a coin toss.
        "expect": {"kind": "yes_no", "want": "no"},
    },
    # --------------------------------------------------- underspecified (x1)
    {
        "id": "U1",
        "category": "underspecified",
        "question": (
            "Is VAT chargeable on the fixed compensation for recovery costs payable "
            "under STAT-LP paragraph 5?"
        ),
        "cite_doc": [],
        "cite_clause": [],
        # The pack says fees are exclusive of VAT and that interest is computed
        # on the amount exclusive of VAT. It says nothing about the VAT
        # treatment of the fixed compensation. Adjacent text makes a confident
        # answer feel supported, which is what makes this a harder decline than
        # a subject that is simply absent.
        "expect": {"kind": "underspecified"},
    },
]


def grade_answer_l4(question: dict, answer: str | None) -> str:
    """correct | partial | wrong | off_by_calendar | wrong_trigger |
    over_claim | format_error."""
    if answer is None:
        return "format_error"
    spec = question["expect"]
    kind = spec["kind"]

    if kind == "underspecified":
        return "correct" if _is_decline(answer) else "over_claim"

    # Declining an answerable item is wrong, but it is the SAFE direction of
    # wrong and must never be counted as an over-claim.
    if _is_decline(answer):
        return "wrong"

    if kind == "date":
        found = _dates(answer)
        if not found:
            # A date question answered with no date at all is not a wrong date,
            # it is an unusable answer, and the two need different responses.
            return "format_error"
        if spec["want"] in found:
            return "correct"
        for label in ("wrong_trigger", "off_by_calendar"):
            if any(candidate in found for candidate in spec.get(label, ())):
                return label
        return "wrong"

    if kind == "yes_no":
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

    if kind == "numeric":
        found = _numbers(answer)
        tol_rel, tol_abs = spec.get("tol_rel", 0.0), spec.get("tol_abs", 0.0)
        if _matches(found, spec["values"], tol_rel, tol_abs):
            return "correct"
        # Most-specific first. Each is a NAMED failure whose shape says what
        # the model did wrong; folding any into `wrong` loses the diagnostic
        # this tier exists to produce.
        for label in ("wrong_trigger", "off_by_calendar", "partial"):
            targets = spec.get(label)
            if targets and _matches(found, targets, tol_rel, tol_abs):
                return label
        return "wrong"

    raise ValueError(
        f"unknown expect kind {kind!r} for L4 question {question['id']}. "
        f"hint: add a branch to grade_answer_l4 or fix the question spec"
    )
