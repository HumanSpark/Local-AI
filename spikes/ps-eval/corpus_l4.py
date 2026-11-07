# File: corpus_l4.py
# Purpose: Level-4 pack - statutory periods, engagement terms and a defective subcontract, built to be FAILED.
# Project: sparkbench | Date: 2026-08-17
#
# Overview: Every purpose-built instrument in this repo is saturated for
# Qwen3.8-27B - L1 20/20, L2 12/12, L3 12/12 at every scale to 236,122 tokens.
# A ceiling ranks nothing, so this tier is built to the one theory of
# difficulty this programme has actually measured.
#
# THE THEORY IS F60, AND IT IS THE WHOLE DESIGN. Across thirteen legal
# matters, what discriminated was never a second BASIS to select - selecting
# the right basis from a record is something these models do reliably. What
# discriminated was a period that had to be WALKED: a calendar counted across
# a public holiday, a day-count applied from a start date that itself had to
# be derived. m11-limitation-clocks scored 6/15 and m13-interest-two-clocks
# 7/15 on that mechanism, against m08's 15/15 without it. F60's closing line
# is the instruction this file follows: "a future corpus should be built on
# periods that must be counted, not on additional bases."
#
# So every hard item here requires counting a period across a real calendar
# under a rule that changes what counts.
#
# WHAT IS DIFFERENT ABOUT L4, DECLARED BECAUSE IT WEAKENS THE COMPARISON.
# L1 -> L2 -> L3 held the domain fixed (one engagement pack) and raised the
# reasoning demanded. L4 changes the DOMAIN, to the three the owner picked:
# Irish/EU statutory specifics, professional-services engagement terms, and
# adversarial "what is wrong with this contract". A lower L4 score is
# therefore partly evidence about a new domain and not purely about
# capability, and it must never be reported as though the ladder continued.
# Two things limit the damage: the outcome vocabulary is L2's, so the FAILURE
# SHAPES stay comparable even where the totals do not; and one category
# (`defect_absent`) is the direct inverse of another, so a model cannot score
# by adopting a posture.
#
# CLOSED RECORD, DELIBERATELY. The statutory extracts and the counting rules
# are IN the pack. This tier does not test whether a model remembers what
# Article 12(3) says - that would confound recall with reasoning and only the
# second bears on the routing decision. It tests whether, given the rule in
# front of it, the model can walk the period. Where a rule has a genuine
# professional ambiguity (when a month-period expires, when interest starts
# running), the pack states which reading governs, so every answer is
# determinate from the record rather than from a convention the grader and
# the model might not share.
#
# The dates are the instrument. Do not "tidy" them.

from __future__ import annotations

import datetime as dt

# ---------------------------------------------------------------- documents

STATUTE_DATA_PROTECTION = """\
DOCUMENT ID: STAT-DP

EXTRACTS - DATA PROTECTION: TIME LIMITS
Prepared for the engagement file. Extracts are reproduced for working
purposes and the counting rules in section C govern their application.

A. RESPONSE TO A DATA SUBJECT REQUEST

   The controller shall provide information on action taken on a request
   without undue delay and in any event within ONE MONTH of receipt of the
   request. That period may be extended by TWO FURTHER MONTHS where
   necessary, taking into account the complexity and number of the requests.
   The controller shall inform the data subject of any such extension within
   one month of receipt of the request, together with the reasons for the
   delay.

B. NOTIFICATION OF A PERSONAL DATA BREACH

   In the case of a personal data breach, the controller shall without undue
   delay and, where feasible, not later than SEVENTY-TWO HOURS after having
   become aware of it, notify the personal data breach to the supervisory
   authority.

C. COUNTING RULES (these govern for all purposes of this file)

   C.1 A period expressed in MONTHS expires at the end of the day in the
       final month which bears the same number as the day on which the
       triggering event occurred. Where the final month has no day of that
       number, the period expires at the end of the LAST DAY of that month.

   C.2 Where a period expressed in months is extended by a further period
       expressed in months, the two are added to the SAME triggering event
       and counted once. They are not counted in sequence from the expiry of
       the first period.

   C.3 A period expressed in HOURS runs continuously from the moment of the
       triggering event. It is not suspended by a weekend, by a public
       holiday, or outside business hours.

   C.4 A period expressed in DAYS excludes the day of the triggering event
       and includes the final day.
"""

STATUTE_LATE_PAYMENT = """\
DOCUMENT ID: STAT-LP

EXTRACTS - LATE PAYMENT IN COMMERCIAL TRANSACTIONS

1. PAYMENT PERIOD. Where the contract does not fix a date or period for
   payment, the payment period is THIRTY DAYS following the date of receipt
   by the debtor of the invoice.

2. INTEREST. Where payment is not made within the payment period, the
   creditor is entitled to interest from the day following expiry of the
   payment period, up to and including the day on which payment is made.

3. RATE. The rate is the reference rate plus EIGHT PERCENTAGE POINTS. The
   reference rate applicable to the period covered by this file is
   2.15 per cent per annum.

4. BASIS. Interest is calculated on a simple basis on the amount outstanding
   exclusive of VAT, using a year of THREE HUNDRED AND SIXTY-FIVE days.

5. FIXED COMPENSATION. In addition to interest, the creditor is entitled to
   fixed compensation for recovery costs, as follows:

      debt less than EUR 1,000 .................... EUR 40
      debt of EUR 1,000 up to EUR 10,000 .......... EUR 70
      debt of EUR 10,000 or more .................. EUR 100

   The fixed compensation is payable once per debt and does not itself bear
   interest.
"""

STATUTE_LIMITATION = """\
DOCUMENT ID: STAT-LIM

EXTRACTS - LIMITATION OF ACTIONS

1. An action founded on simple contract shall not be brought after the
   expiration of SIX YEARS from the date on which the cause of action
   accrued.

2. For the purposes of this file, the cause of action on a claim for
   defective performance accrues on the date of the BREACH, not on the date
   the breach is discovered and not on the date of the contract.

3. The period begins on the day after the cause of action accrued and
   expires at the end of the corresponding day in the sixth year following.
   Proceedings issued on that day are in time; proceedings issued on the
   following day are out of time.
"""

CALENDAR = """\
DOCUMENT ID: CAL-2026

PUBLIC HOLIDAYS, IRELAND, 2026

   Thursday 1 January .......... New Year's Day
   Monday 2 February ........... St Brigid's Day
   Tuesday 17 March ............ St Patrick's Day
   Monday 6 April .............. Easter Monday
   Monday 4 May ................ May holiday
   Monday 1 June ............... June holiday
   Monday 3 August ............. August holiday
   Monday 26 October ........... October holiday
   Friday 25 December .......... Christmas Day
   Saturday 26 December ........ St Stephen's Day

NOTE. Good Friday (3 April 2026) is NOT a public holiday in Ireland. It is
listed here because it is commonly assumed to be one.

2026 is not a leap year. February 2026 has 28 days.
"""

ENGAGEMENT_LETTER = """\
DOCUMENT ID: ENG-2025

ENGAGEMENT LETTER

Between Ardmore Composites Limited (the "Client") and Calderwood Advisory
LLP (the "Firm")

Dated 3 November 2025. Commencement Date: 1 December 2025.

1. FEES

   1.1 The Client shall pay the Firm a monthly fee of EUR 24,000, exclusive
       of VAT, invoiced monthly in arrears.

   1.2 With effect from 1 October 2026 the monthly fee increases to
       EUR 27,600, exclusive of VAT.

   1.3 Where no payment date is agreed for a particular invoice, the
       statutory payment period applies.

2. TERMINATION

   2.1 Either party may terminate this engagement for convenience on THREE
       MONTHS' written notice.

   2.2 Notice under clause 2.1 takes effect on the LAST DAY OF THE CALENDAR
       MONTH in which the three-month period expires.

   2.3 Notice under clause 2.1 may not take effect before the first
       anniversary of the Commencement Date.

   2.4 The Client shall pay the monthly fee for each complete calendar month
       up to and including the month in which notice takes effect, at the
       rate in force in that month.

3. SURVIVAL

   3.1 Clauses 4 (Confidentiality), 5 (Records) and 6 (Professional
       Indemnity Insurance) survive termination.

   3.2 Clause 7 (Escalation Contact) does not survive termination.

4. CONFIDENTIALITY. Each party shall keep the other's confidential
   information confidential for six years after termination.

5. RECORDS. The Firm shall retain engagement records for six years after
   termination and shall permit the Client to inspect them on reasonable
   notice.

6. PROFESSIONAL INDEMNITY INSURANCE. The Firm shall maintain professional
   indemnity insurance of not less than EUR 2,000,000 per claim, and shall
   procure that any subcontractor engaged on Client work maintains cover of
   not less than EUR 1,000,000 per claim and notifies the Firm in writing of
   any cancellation or non-renewal of that cover within five business days.

7. ESCALATION CONTACT. The Firm shall provide a named escalation contact
   and shall notify the Client of any change within five business days.

8. SUBCONTRACTING. The Firm may subcontract with the Client's prior written
   consent. The Firm shall procure that each subcontract imposes on the
   subcontractor obligations no less onerous than those in clauses 4, 5 and
   6 of this engagement letter.

Signed for Ardmore Composites Limited: L. Nagle, Finance Director.
Signed for Calderwood Advisory LLP: F. Hartnett, Engagement Partner.
"""

SUBCONTRACT = """\
DOCUMENT ID: SUB-KILBEG

SUBCONTRACT FOR SPECIALIST ANALYTICAL SERVICES

Between Calderwood Advisory LLP (the "Firm") and Kilbeg Analytics Limited
(the "Subcontractor")

Dated 9 February 2026.

1. SERVICES. The Subcontractor shall provide data analysis services in
   support of the Firm's engagement with Ardmore Composites Limited.

2. FEES. EUR 9,400 per month, exclusive of VAT, invoiced monthly in arrears
   and payable within thirty days of receipt of invoice.

3. CONFIDENTIALITY. The Subcontractor shall keep the Firm's and the Client's
   confidential information confidential for six years after termination.

4. RECORDS. The Subcontractor shall retain records relating to the services
   for TWO YEARS after termination and shall permit the Firm to inspect
   them on reasonable notice.

5. INSURANCE. The Subcontractor shall maintain professional indemnity
   insurance of not less than EUR 350,000 per claim.

6. LIABILITY. The Subcontractor's aggregate liability under this subcontract
   is limited to EUR 500,000.

7. TERMINATION. Either party may terminate on one month's written notice.

8. GOVERNING LAW. This subcontract is governed by the laws of Ireland.

9. NOTICES. Notices must be in writing and delivered by hand or by
   registered post to the address of the receiving party set out above.

Signed for Calderwood Advisory LLP: F. Hartnett, Engagement Partner.
Signed for Kilbeg Analytics Limited: S. Devane, Director.
"""

CHRONOLOGY = """\
DOCUMENT ID: CHRON

ENGAGEMENT CHRONOLOGY - AGREED FACTS

   14 September 2020  Kilbeg Analytics delivered a defective dataset under an
                      earlier, separate contract with the Firm. This is the
                      date of the breach. The Firm did not discover the
                      defect until 2 March 2023, and the earlier contract was
                      itself dated 11 May 2019.

   12 May 2026        The Firm received Kilbeg Analytics' invoice number
                      K-2026-041 for EUR 18,400, exclusive of VAT. No payment
                      date was agreed for that invoice.

   31 January 2026    Ardmore Composites received a data subject access
                      request from a former employee. Ardmore notified the
                      Firm the same day.

   3 April 2026       At 14:30 the Firm became aware of a personal data
                      breach affecting Client personal data.

   12 August 2026     The Client served written notice of termination for
                      convenience under clause 2.1 of the engagement letter.

   27 August 2026     The Firm paid invoice K-2026-041 in full.
"""

DOCUMENTS_L4: dict[str, str] = {
    "STAT-DP": STATUTE_DATA_PROTECTION,
    "STAT-LP": STATUTE_LATE_PAYMENT,
    "STAT-LIM": STATUTE_LIMITATION,
    "CAL-2026": CALENDAR,
    "ENG-2025": ENGAGEMENT_LETTER,
    "SUB-KILBEG": SUBCONTRACT,
    "CHRON": CHRONOLOGY,
}

# The chronology sits LAST on purpose. Every dated question has to reach it,
# so a model that stops reading early fails on the trigger date rather than
# on the counting - and the two are separable in the outcome vocabulary,
# because a missed trigger produces a `wrong` while a missed calendar rule
# produces `off_by_calendar`.
PACK_ORDER_L4 = [
    "ENG-2025", "SUB-KILBEG",
    "STAT-DP", "STAT-LP", "STAT-LIM", "CAL-2026",
    "CHRON",
]

SEPARATOR = "\n" + "=" * 72 + "\n"


def build_pack_l4() -> str:
    """The L4 pack, assembled in PACK_ORDER_L4."""
    missing = [name for name in PACK_ORDER_L4 if name not in DOCUMENTS_L4]
    if missing:
        raise KeyError(
            f"PACK_ORDER_L4 names {missing} which are absent from DOCUMENTS_L4. "
            f"hint: add the document to DOCUMENTS_L4 or remove it from PACK_ORDER_L4"
        )
    return SEPARATOR.join(DOCUMENTS_L4[name] for name in PACK_ORDER_L4)


# ---------------------------------------------------------------- derivation
#
# Every answer below is COMPUTED from the dates in the documents. A key typed
# by hand is a key that disagrees with the pack after the first edit, and on
# a calendar instrument that disagreement is invisible - a wrong date looks
# exactly like a right one.

REFERENCE_RATE = 0.0215
LATE_PAYMENT_MARGIN = 0.08
DAY_COUNT_BASIS = 365

MONTHLY_FEE_SCHEDULE: list[tuple[str, int]] = [
    ("2025-12-01", 24_000),   # ENG 1.1
    ("2026-10-01", 27_600),   # ENG 1.2
]


def months_after(date: dt.date, months: int) -> dt.date:
    """`date` plus `months` calendar months under counting rule C.1.

    Where the target month has no day of the same number, the period expires
    on the last day of that month - which is the rule that makes February the
    instrument rather than an inconvenience.
    """
    year = date.year + (date.month - 1 + months) // 12
    month = (date.month - 1 + months) % 12 + 1
    day = date.day
    while True:
        try:
            return dt.date(year, month, day)
        except ValueError:
            # 31 January + 1 month has no 31 February; walk back to the 28th.
            day -= 1
            if day < 28:
                raise ValueError(
                    f"cannot roll {date} forward {months} months into "
                    f"{year}-{month:02d}. hint: the month arithmetic is wrong, "
                    f"not the calendar"
                ) from None


def end_of_month(date: dt.date) -> dt.date:
    """The last day of `date`'s calendar month (ENG clause 2.2)."""
    if date.month == 12:
        return dt.date(date.year, 12, 31)
    return dt.date(date.year, date.month + 1, 1) - dt.timedelta(days=1)


def late_payment_days(received: dt.date, paid: dt.date, payment_period_days: int = 30) -> int:
    """Days interest runs: day after the payment period expires, to payment.

    STAT-LP paragraphs 1 and 2, read with counting rule C.4. Raises rather
    than returning a negative or zero count, because an invoice paid inside
    its period carries no interest at all and a question that assumes one is
    a bug in the question.
    """
    due = received + dt.timedelta(days=payment_period_days)
    days = (paid - due).days
    if days <= 0:
        raise ValueError(
            f"invoice received {received} and paid {paid} was inside its "
            f"{payment_period_days}-day period. hint: no interest arises, so "
            f"this question has no numeric answer"
        )
    return days


def late_payment_interest(principal: int, days: int,
                          rate: float = REFERENCE_RATE + LATE_PAYMENT_MARGIN,
                          basis: int = DAY_COUNT_BASIS) -> float:
    """Simple interest under STAT-LP paragraphs 3 and 4."""
    return principal * rate * days / basis


def fixed_compensation(debt: int) -> int:
    """STAT-LP paragraph 5's three bands."""
    if debt < 1_000:
        return 40
    if debt < 10_000:
        return 70
    return 100


def fee_on(date: dt.date) -> int:
    """The monthly fee in force on `date` (ENG clauses 1.1 and 1.2)."""
    iso = date.isoformat()
    current = None
    for effective, value in MONTHLY_FEE_SCHEDULE:
        if effective <= iso:
            current = value
    if current is None:
        raise ValueError(
            f"no fee in force on {iso}: the schedule starts at "
            f"{MONTHLY_FEE_SCHEDULE[0][0]}. hint: the question asks about a "
            f"date before the Commencement Date"
        )
    return current


def fee_total(first_month: dt.date, last_month: dt.date) -> int:
    """Fees for every complete calendar month from `first_month` to `last_month`.

    ENG clause 2.4. Both arguments are taken as month markers; the day is
    ignored. The rate is the one in force IN each month, so a period that
    straddles 1 October 2026 is charged at two rates and cannot be answered
    by multiplying one rate by a month count.
    """
    total = 0
    year, month = first_month.year, first_month.month
    while (year, month) <= (last_month.year, last_month.month):
        total += fee_on(dt.date(year, month, 1))
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return total


# ------------------------------------------------------------ trigger dates
#
# Read out of CHRON once, so the questions and the graders cannot drift apart
# from the pack or from each other.
DSR_RECEIVED = dt.date(2026, 1, 31)
BREACH_AWARE = dt.datetime(2026, 4, 3, 14, 30)
INVOICE_RECEIVED = dt.date(2026, 5, 12)
INVOICE_PAID = dt.date(2026, 8, 27)
INVOICE_AMOUNT = 18_400
ACCRUAL_DATE = dt.date(2020, 9, 14)
DISCOVERY_DATE = dt.date(2023, 3, 2)
EARLIER_CONTRACT_DATE = dt.date(2019, 5, 11)
NOTICE_SERVED = dt.date(2026, 8, 12)
COMMENCEMENT_DATE = dt.date(2025, 12, 1)
