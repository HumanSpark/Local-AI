# File: corpus_l5.py
# Purpose: Level-5 pack - one matter whose difficulty is deliberately SPLIT into a reasoning-limited band and an evidence-limited band.
# Project: sparkbench | Date: 2026-08-28
#
# Overview: L4 proved that a bank can be built to be failed, and it proved
# what fails: walked periods separated the arms completely (6/7, 4/7, 0/7)
# while static analysis separated nothing (7/7, 7/7, 6/7). That is a theory of
# difficulty, and this pack is the first one built to test a SECOND thing at
# the same time.
#
# WHY A SECOND BAND EXISTS, AND WHY THE WHOLE DESIGN TURNS ON IT.
# The inference-architecture programme (docs/plans/2026-08-28-inference-
# architecture-slice-1.md) proposes context engineering, retrieval, small
# context models and evidence packs - every one of which acts on how EVIDENCE
# reaches the model. But the failure this box actually exhibits is not an
# evidence failure. E41 held 12/12 from 0 to 9 distractors, E48 held 12/12 at
# 29 distractors and 60,315 tokens with citations IMPROVING, and E54 measured
# the workhorse reading a defective contract correctly (6/7) and then failing
# every single walked period (0/7).
#
# So an instrument made harder only in F60's direction would have plenty of
# headroom and NONE of it reachable by the interventions the programme wants
# to test. It would be the wrong instrument, built well.
#
# THEREFORE EVERY ITEM CARRIES A `band`:
#
#   R - reasoning-limited. The evidence is small, adjacent and unambiguous;
#       what is hard is walking a period or composing two constraints. F60 and
#       E54 say these separate. Context engineering CANNOT fix them, and the
#       registered expectation is that it will not move this band at all.
#       Tools (H16 - tools/date_calc.py already exists) should move it a lot.
#
#   E - evidence-limited. The reasoning is a single step a model does reliably;
#       what is hard is finding WHICH of several parallel documents governs,
#       reconciling two that disagree, or noticing the record does not settle
#       the question at all. If context engineering has anything to offer on
#       this hardware, this is the band where it must show up.
#
# The two bands share one pack, one outcome vocabulary and one grader, so a
# difference between them is a property of the questions and not of two
# different tests. **If band E is ALSO saturated for the production model,
# that is the finding**: it would say the H1-H5 branch has no headroom here
# and should close, and it would say it for the cost of one run.
#
# CLOSED RECORD, as L4. Every rule needed - the counting conventions, the
# precedence order, the interest basis - is in the pack. This does not test
# recall of Irish law; it tests whether a model can use a rule placed in front
# of it. Where a convention is genuinely ambiguous the pack states which
# reading governs, so every answer is determinate from the record.
#
# THE ABSENCES ARE LOAD-BEARING AND ARE ASSERTED. Four band-E items ask about
# things this pack never states. E76 measured the production model asserting a
# figure on 5 of 12 such questions, so this is proven headroom rather than
# hoped-for headroom. The validator checks each asserted absence against the
# built pack, case-insensitively, and refuses the bank if one is present.
#
# The dates and the figures ARE the instrument. Do not "tidy" them.

from __future__ import annotations

import datetime as dt

# ---------------------------------------------------------------- documents

FRAMEWORK = """\
DOCUMENT ID: FA-2025
FRAMEWORK SERVICES AGREEMENT

Between: Brackenridge Foods Limited ("the Client")
And:     Northgate Systems Limited ("the Supplier")
Dated:   3 November 2025

1.  STRUCTURE
1.1 This Framework Agreement sets the terms on which the Supplier may accept
    Call-Off Orders. It does not itself commit either party to any volume.
1.2 Each Call-Off Order incorporates this Framework Agreement and states its
    own Service Period, Acceptance Window, Liability Cap and Notice Period.
1.3 Where a Call-Off Order is silent on a matter, the corresponding provision
    of this Framework Agreement applies.

2.  ORDER OF PRECEDENCE
2.1 In the event of conflict, the following order governs, highest first:
        (a) a Variation Letter executed by both parties;
        (b) the Call-Off Order;
        (c) this Framework Agreement;
        (d) any Supplier quotation, proposal or standard terms.
2.2 A Variation Letter amends ONLY the Call-Off Order it names. It has no
    effect on any other Call-Off Order, whether or not the same subject
    matter appears in them.

3.  DEFAULT TERMS (apply only where the Call-Off Order is silent)
3.1 Acceptance Window: ten Business Days from Delivery.
3.2 Liability Cap: EUR 250,000 per Call-Off Order.
3.3 Notice Period for termination for convenience: three months.
3.4 A termination for convenience takes effect on the LAST BUSINESS DAY OF A
    MONTH. Where the Notice Period expires on a day that is not the last
    Business Day of a month, termination takes effect on the last Business Day
    of that same month. Clause 3.4 and the Notice Period are cumulative: both
    must be satisfied.

4.  COUNTING CONVENTIONS - these govern every period in this matter
4.1 "Business Day" means a day other than a Saturday, Sunday or a public
    holiday listed in the Calendar document in this pack.
4.2 A period expressed in Business Days EXCLUDES the day of the triggering
    event and includes the last day of the period.
4.3 A period expressed in months expires on the day of the later month having
    the same number as the day of the triggering event. Where the later month
    has no such day, the period expires on the LAST day of that later month.
4.4 Where two periods are stated for the same event, they run from that same
    triggering event IN PARALLEL. They are not added to one another and the
    later expiry governs.
4.5 A period is not suspended, extended or rolled by a weekend or a public
    holiday unless the clause creating it says so expressly.

5.  PAYMENT
5.1 Invoices fall due thirty days after receipt by the Client.
5.2 Interest on a late payment runs from the day after the due date to the day
    of payment inclusive, on a 365-day basis, at the Reference Rate plus eight
    percentage points. The Reference Rate for this matter is 2.15%.
5.3 In addition to interest, the Client shall pay fixed compensation under the
    band table in the Statute document in this pack.
"""

CALL_OFF_ONE = """\
DOCUMENT ID: CO-1
CALL-OFF ORDER 1
Dated: 19 January 2026

Service Period:   19 January 2026 to 18 July 2026
Scope:            Warehouse telemetry - Site A (Drogheda)
Acceptance Window: eight Business Days from Delivery
Liability Cap:    EUR 180,000
Notice Period:    two months
Deliverable:      Sensor array, Site A. Delivery date stated in the Chronology.
"""

CALL_OFF_TWO = """\
DOCUMENT ID: CO-2
CALL-OFF ORDER 2
Dated: 16 February 2026

Service Period:   16 February 2026 to 15 August 2026
Scope:            Warehouse telemetry - Site B (Ennis)
Acceptance Window: twelve Business Days from Delivery
Liability Cap:    EUR 320,000
Notice Period:    (silent)
Deliverable:      Sensor array, Site B. Delivery date stated in the Chronology.
"""

CALL_OFF_THREE = """\
DOCUMENT ID: CO-3
CALL-OFF ORDER 3
Dated: 9 March 2026

Service Period:   9 March 2026 to 8 March 2027
Scope:            Warehouse telemetry - Site C (Tralee)
Acceptance Window: eight Business Days from Delivery
Liability Cap:    EUR 180,000
Notice Period:    two months
Deliverable:      Sensor array, Site C. Delivery date stated in the Chronology.
"""

VARIATION = """\
DOCUMENT ID: VAR-1
VARIATION LETTER
Dated: 7 April 2026
Executed by both parties.

This Variation Letter amends CALL-OFF ORDER 2 (CO-2) only.

1. The Liability Cap in CO-2 is replaced with EUR 96,000.
2. The Acceptance Window in CO-2 is replaced with six Business Days from
   Delivery.
3. No other Call-Off Order is amended by this letter.
"""

STATUTE = """\
DOCUMENT ID: STAT-1
STATUTORY EXTRACTS (as they apply to this matter)

LATE PAYMENT
S.1  Fixed compensation is payable in addition to interest, by band:
        debt up to and including EUR 1,000 .................. EUR 40
        debt above EUR 1,000 up to and including EUR 10,000 . EUR 70
        debt above EUR 10,000 .............................. EUR 100

DATA ACCESS
S.2  A data access request shall be answered within one month of receipt.
S.3  That period may be extended by two further months where the request is
     complex. The extension runs from the SAME date of receipt as the original
     period, in parallel with it, and the later expiry governs. (See Framework
     Agreement clause 4.4.)

LIMITATION
S.4  Proceedings founded on contract shall not be brought after six years from
     the date on which the cause of action accrued.
S.5  Where the parties execute a standstill agreement, the running of the
     period in S.4 is suspended for the duration of the standstill, and
     resumes on the day after the standstill ends. Days before and after the
     standstill are counted; days within it are not.
"""

CALENDAR = """\
DOCUMENT ID: CAL-2026
PUBLIC HOLIDAYS 2026 (Ireland) - these are the only public holidays for this
matter. Every other weekday is a Business Day.

  1 January 2026    (Thursday)   New Year's Day
  2 February 2026   (Monday)     St Brigid's Day
 17 March 2026      (Tuesday)    St Patrick's Day
  6 April 2026      (Monday)     Easter Monday
  4 May 2026        (Monday)     May Day
  1 June 2026       (Monday)     June Holiday
  3 August 2026     (Monday)     August Holiday
 26 October 2026    (Monday)     October Holiday
 25 December 2026   (Friday)     Christmas Day
 28 December 2026   (Monday)     St Stephen's Day (observed)
"""

CHRONOLOGY = """\
DOCUMENT ID: CHRON-1
MATTER CHRONOLOGY - prepared by the Client's solicitors and agreed by both
parties as the authoritative record of dates for this matter.

 19 Jan 2026   CO-1 executed.
 16 Feb 2026   CO-2 executed.
 11 Mar 2026   Sensor array delivered to Site A under CO-1.
  9 Mar 2026   CO-3 executed.
 30 Mar 2026   Sensor array delivered to Site B under CO-2.
  7 Apr 2026   VAR-1 executed.
 28 Apr 2026   Sensor array delivered to Site C under CO-3.
 12 May 2026   Invoice INV-8841 received by the Client. Amount EUR 18,400.
 31 May 2026   Client's data access request received by the Supplier.
 15 Jun 2026   Supplier notifies the Client that the data request is complex.
 27 Aug 2026   INV-8841 paid in full.
 12 Aug 2026   Notice of termination for convenience served on the Supplier in
               respect of CO-3.
"""

INTERNAL_NOTE = """\
DOCUMENT ID: NOTE-4
INTERNAL FILE NOTE - Brackenridge Foods, operations team
Dated: 2 June 2026
Status: internal working note. NOT agreed between the parties.

Recollection of the team is that the Site A array turned up on 9 March, not
11 March, and that the data request went out on 28 May. The
Chronology should probably be corrected. Nobody has raised this with Northgate
and the Chronology has not been amended.

Note also that the operations team believes the Site B cap is the standard
EUR 250,000 figure. The team has not seen the variation correspondence.
"""

DISPUTE_BACKGROUND = """\
DOCUMENT ID: BG-1
BACKGROUND NOTE - the supplier dispute

A separate and earlier dispute exists between the Client and Northgate under a
2019 supply arrangement, unconnected to the Framework Agreement. The cause of
action in that earlier dispute accrued on 14 September 2020.

The parties executed a standstill agreement in that earlier dispute running
from 1 March 2023 to 30 November 2023 inclusive. The standstill has ended and
has not been renewed.

Nothing in the earlier dispute varies the Framework Agreement or any Call-Off
Order. The Client's advisers have been asked when the earlier claim becomes
statute-barred.
"""

SEPARATOR = "\n" + "=" * 72 + "\n"

_DOCS = [
    FRAMEWORK,
    CALL_OFF_ONE,
    CALL_OFF_TWO,
    CALL_OFF_THREE,
    VARIATION,
    STATUTE,
    CALENDAR,
    CHRONOLOGY,
    INTERNAL_NOTE,
    DISPUTE_BACKGROUND,
]


def build_pack_l5() -> str:
    """The whole L5 record, in one deterministic order.

    Order is fixed rather than shuffled: a pack whose document order varies
    between arms would vary the prompt as well as the model, and every figure
    in this repository is a comparison against a config.
    """
    return SEPARATOR.join(d.rstrip() for d in _DOCS) + "\n"


# ------------------------------------------------------- derived date helpers
#
# Every answer key in questions_l5.py is DERIVED with these, never typed. On a
# calendar instrument a hand-typed key is the one error no score can reveal,
# because a wrong date looks exactly like a right one (L4's lesson, and it
# caught two live defects there).

PUBLIC_HOLIDAYS: frozenset[dt.date] = frozenset(
    {
        dt.date(2026, 1, 1),
        dt.date(2026, 2, 2),
        dt.date(2026, 3, 17),
        dt.date(2026, 4, 6),
        dt.date(2026, 5, 4),
        dt.date(2026, 6, 1),
        dt.date(2026, 8, 3),
        dt.date(2026, 10, 26),
        dt.date(2026, 12, 25),
        dt.date(2026, 12, 28),
    }
)


def is_business_day(day: dt.date) -> bool:
    """Monday to Friday, excluding the pack's listed public holidays."""
    return day.weekday() < 5 and day not in PUBLIC_HOLIDAYS


def add_business_days(start: dt.date, count: int) -> dt.date:
    """Clause 4.2: exclude the triggering day, include the last day.

    Raises on a non-positive count rather than returning `start`, because a
    zero-day Business Day period is not a thing this pack can express and a
    silent identity return would grade as a correct answer to a question the
    bank never meant to ask.
    """
    if count < 1:
        raise ValueError(
            f"add_business_days needs count >= 1, got {count}\n"
            f"hint: clause 4.2 excludes the triggering day, so a period of "
            f"zero Business Days has no expiry date to return"
        )
    day, seen = start, 0
    while seen < count:
        day += dt.timedelta(days=1)
        if is_business_day(day):
            seen += 1
    return day


def months_after(start: dt.date, months: int) -> dt.date:
    """Clause 4.3: same day number in the later month, else that month's last day."""
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = start.day
    while True:
        try:
            return dt.date(year, month, day)
        except ValueError:
            day -= 1


def years_after(start: dt.date, years: int) -> dt.date:
    """S.4's six years, with the 29 February case resolved the same way as 4.3."""
    day = start.day
    while True:
        try:
            return dt.date(start.year + years, start.month, day)
        except ValueError:
            day -= 1


def late_payment_days(
    received: dt.date, paid: dt.date, payment_period_days: int = 30
) -> int:
    """Clause 5.2: from the day after the due date to the day of payment inclusive."""
    due = received + dt.timedelta(days=payment_period_days)
    if paid <= due:
        return 0
    return (paid - due).days


def late_payment_interest(principal: int, days: int) -> float:
    """Clause 5.2, 365-day basis, Reference Rate plus eight points."""
    return principal * (REFERENCE_RATE + LATE_PAYMENT_MARGIN) * days / DAY_COUNT_BASIS


def fixed_compensation(debt: int) -> int:
    """STAT-1 S.1 band table."""
    if debt <= 1_000:
        return 40
    if debt <= 10_000:
        return 70
    return 100


# ------------------------------------------------------------------ constants
#
# Read off the documents above. Anything computed FROM these belongs in
# questions_l5.py, so this file states the record and that file states the
# answers.

REFERENCE_RATE = 0.0215
LATE_PAYMENT_MARGIN = 0.08
DAY_COUNT_BASIS = 365

DELIVERY_SITE_A = dt.date(2026, 3, 11)
DELIVERY_SITE_B = dt.date(2026, 3, 30)
DELIVERY_SITE_C = dt.date(2026, 4, 28)

INVOICE_RECEIVED = dt.date(2026, 5, 12)
INVOICE_PAID = dt.date(2026, 8, 27)
INVOICE_AMOUNT = 18_400

DATA_REQUEST_RECEIVED = dt.date(2026, 5, 31)
NOTICE_SERVED = dt.date(2026, 8, 12)

EARLIER_ACCRUAL = dt.date(2020, 9, 14)
STANDSTILL_START = dt.date(2023, 3, 1)
STANDSTILL_END = dt.date(2023, 11, 30)

CAP_CO1 = 180_000
CAP_CO2_AS_VARIED = 96_000
CAP_CO3 = 180_000
CAP_FRAMEWORK_DEFAULT = 250_000

ACCEPTANCE_CO1_DAYS = 8
ACCEPTANCE_CO2_AS_VARIED_DAYS = 6
ACCEPTANCE_CO3_DAYS = 8


if __name__ == "__main__":
    pack = build_pack_l5()
    print(f"L5 pack: {len(pack):,} chars, {len(_DOCS)} documents")
