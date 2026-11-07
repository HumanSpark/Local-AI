# File: corpus.py
# Purpose: Seeded professional-services engagement pack - the source documents for the PS knowledge-work eval.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: A fictional advisory engagement pack of six documents, written so
# that every question in questions.py has an OBJECTIVELY checkable answer.
# This exists because the knowledge-work evidence in results/ is office
# drafting scored by a frontier model as judge - subjective, and the ruler is
# itself a cloud model. What a KPMG/EY/Deloitte/BCG deployment is actually
# evaluated on is narrower and far more testable, and it is what this encodes:
#
#   RETRIEVAL     a fact stated once, answered with a clause citation
#   SUPERSESSION  an amendment changed it; using the stale figure is the
#                 real-world liability, and naive retrieval gets it wrong
#   COMPUTATION   arithmetic over a table that must be exactly right
#   CONFLICT      two documents disagree - does the model notice, or does it
#                 silently pick one?
#   UNANSWERABLE  the pack does not say, and the only correct answer is to
#                 say so
#
# THE LAST CATEGORY IS THE POINT. In professional services the cost function
# is violently asymmetric: a confident fabrication is a liability event,
# while "not in the pack" is a correct and billable answer. Public benchmarks
# rarely measure it because unanswerable items look like unfair questions.
# Here it is the headline metric - the over-claim rate - and it needs no LLM
# judge to grade.
#
# EVERY PLANTED FACT IS DELIBERATE. The amendment chain (MSA -> A1 -> A2),
# the board-minute figure that contradicts the financial table, and the
# policy clauses that conflict with the agreement are all seeded; see
# questions.py for what each one is testing. Do not "tidy" an inconsistency
# in these documents - the inconsistencies ARE the instrument.
#
# All entities, people and figures are fictional.

from __future__ import annotations

MSA = """\
DOCUMENT ID: MSA-2024

MASTER SERVICES AGREEMENT

between NORTHWIND LOGISTICS LIMITED, a company registered in Ireland
(company number 486213), whose registered office is at Unit 7, Eastgate
Business Park, Little Island, Co. Cork ("the Client")

and CALDERWOOD ADVISORY LLP, a limited liability partnership registered in
Ireland (partnership number LP4417), whose principal place of business is at
34 Merrion Square, Dublin 2 ("the Supplier")

Dated 1 March 2024

1. DEFINITIONS AND INTERPRETATION
1.1 "Services" means the advisory services described in Schedule A.
1.2 "Engagement Period" means the period from 1 April 2024 to 31 March 2026.
1.3 "Deliverable" means any report, model, presentation or other document
    prepared by the Supplier in the course of providing the Services.
1.4 "Business Day" means a day other than a Saturday, Sunday or public
    holiday in Ireland.
1.5 References to clauses are references to clauses of this Agreement.

2. FEES AND PAYMENT
2.1 The Client shall pay the Supplier a monthly retainer of EUR 42,000
    (forty-two thousand euro), exclusive of VAT.
2.2 Work requested by the Client beyond the scope of the retainer is charged
    at EUR 285 per consultant hour, exclusive of VAT.
2.3 The Supplier shall invoice monthly in arrears. Invoices are payable
    within 30 days of receipt.
2.4 Late payment accrues interest at 4% per annum above the European Central
    Bank main refinancing rate, accruing daily.
2.5 Reasonable travel and subsistence expenses are recoverable at cost,
    provided they are approved in advance in writing.

3. TERM AND TERMINATION
3.1 This Agreement commences on 1 April 2024 and continues for the
    Engagement Period unless terminated earlier in accordance with this
    clause 3.
3.2 Either party may terminate this Agreement for convenience by giving 90
    days written notice to the other party.
3.3 Either party may terminate this Agreement immediately by written notice
    if the other party commits a material breach which is not remedied
    within 20 Business Days of written notice requiring its remedy.
3.4 Termination does not affect any accrued rights or liabilities.

4. LIABILITY
4.1 The Supplier's aggregate liability arising out of or in connection with
    this Agreement, whether in contract, tort or otherwise, is limited to
    EUR 500,000.
4.2 Neither party is liable to the other for any indirect or consequential
    loss, loss of profit, or loss of anticipated savings.
4.3 Nothing in this Agreement limits or excludes liability for death or
    personal injury caused by negligence, or for fraud or fraudulent
    misrepresentation.

5. DATA PROTECTION
5.1 The Supplier acts as a data processor in respect of Client personal data
    processed under this Agreement, and the Client acts as data controller.
5.2 The Supplier shall retain Client personal data for no longer than 24
    months following termination or expiry of this Agreement, after which it
    shall be securely deleted.
5.3 The Supplier shall not engage any sub-processor without the Client's
    prior written approval.
5.4 The Supplier shall notify the Client of any personal data breach without
    undue delay and in any event within 48 hours of becoming aware of it.

6. SERVICE LEVELS
6.1 The Supplier shall acknowledge and respond to written queries from the
    Client within 2 Business Days.
6.2 The Supplier shall deliver the monthly reporting pack by the 10th
    calendar day of the following month.
6.3 Where the Supplier fails to meet clause 6.2 in three consecutive months,
    the Client is entitled to a service credit of 5% of the monthly retainer
    for each subsequent month in which the failure continues.

7. CHANGE CONTROL
7.1 No variation of this Agreement is effective unless it is in writing and
    signed by an authorised representative of each party.
7.2 The Client's authorised representative for the purposes of change
    control is the Chief Financial Officer.
7.3 The Supplier's authorised representative for the purposes of change
    control is the Engagement Partner named in Schedule A.

8. GOVERNING LAW AND JURISDICTION
8.1 This Agreement and any dispute arising out of it are governed by the
    laws of Ireland.
8.2 The courts of Ireland have exclusive jurisdiction to settle any dispute
    arising out of or in connection with this Agreement.

SCHEDULE A - THE SERVICES
A.1 Supply chain network review and quarterly benchmarking.
A.2 Monthly management reporting pack and commentary.
A.3 Ad hoc advisory support on operational efficiency initiatives.
A.4 The Engagement Partner is Ms Fiona Hartnett.
"""

AMENDMENT_1 = """\
DOCUMENT ID: AMD-1

AMENDMENT NO. 1 TO THE MASTER SERVICES AGREEMENT

Between Northwind Logistics Limited and Calderwood Advisory LLP

Dated 15 November 2024

The parties agree to amend the Master Services Agreement dated 1 March 2024
(the "Agreement") as follows, with effect from the dates stated.

1. Clause 2.1 of the Agreement is deleted and replaced with the following,
   with effect from 1 January 2025:
   "2.1 The Client shall pay the Supplier a monthly retainer of EUR 46,500
   (forty-six thousand five hundred euro), exclusive of VAT."

2. Clause 1.2 of the Agreement is deleted and replaced with the following:
   "1.2 'Engagement Period' means the period from 1 April 2024 to 30
   September 2026."

3. Save as expressly amended by this Amendment No. 1, all other terms of the
   Agreement remain in full force and effect.

Signed for and on behalf of Northwind Logistics Limited: D. Moriarty, Chief
Financial Officer.
Signed for and on behalf of Calderwood Advisory LLP: F. Hartnett, Engagement
Partner.
"""

AMENDMENT_2 = """\
DOCUMENT ID: AMD-2

AMENDMENT NO. 2 TO THE MASTER SERVICES AGREEMENT

Between Northwind Logistics Limited and Calderwood Advisory LLP

Dated 30 June 2025

The parties agree to amend the Master Services Agreement dated 1 March 2024,
as previously amended by Amendment No. 1 dated 15 November 2024 (together the
"Agreement"), as follows.

1. Clause 4.1 of the Agreement is deleted and replaced with the following:
   "4.1 The Supplier's aggregate liability arising out of or in connection
   with this Agreement, whether in contract, tort or otherwise, is limited to
   EUR 1,250,000."

2. Clause 3.2 of the Agreement is deleted and replaced with the following:
   "3.2 Either party may terminate this Agreement for convenience by giving
   120 days written notice to the other party."

3. Clause 5.2 of the Agreement is deleted and replaced with the following:
   "5.2 The Supplier shall retain Client personal data for no longer than 12
   months following termination or expiry of this Agreement, after which it
   shall be securely deleted."

4. Save as expressly amended by this Amendment No. 2, all other terms of the
   Agreement remain in full force and effect.

Signed for and on behalf of Northwind Logistics Limited: D. Moriarty, Chief
Financial Officer.
Signed for and on behalf of Calderwood Advisory LLP: F. Hartnett, Engagement
Partner.
"""

BOARD_MINUTES = """\
DOCUMENT ID: BM-EXTRACTS

NORTHWIND LOGISTICS LIMITED - EXTRACTS FROM BOARD MINUTES

Extract 1 - Meeting of the Board of Directors, 12 February 2025
Present: P. Sheridan (Chair), D. Moriarty (CFO), A. Nwosu, L. Brennan.

4.1 The Board NOTED revenue for the quarter ended 31 December 2024 of
    EUR 8.42 million.
4.2 The Board APPROVED capital expenditure of EUR 1.1 million for the fleet
    telematics replacement programme.
4.3 The CFO REPORTED that the retainer payable to Calderwood Advisory had
    increased to EUR 46,500 per month with effect from January 2025, in
    accordance with Amendment No. 1.
4.4 The Board NOTED that the telematics programme would be procured under
    the group procurement policy.

Extract 2 - Meeting of the Board of Directors, 4 September 2025
Present: P. Sheridan (Chair), D. Moriarty (CFO), A. Nwosu, L. Brennan,
        K. O'Halloran.

6.1 The Board NOTED gross margin for the six months ended 30 June 2025 of
    21.4%.
6.2 The Board APPROVED the extension of the Calderwood Advisory engagement
    to September 2026.
6.3 The Board NOTED that the aggregate liability cap under the advisory
    agreement had been raised to EUR 1.25 million.
6.4 The Board REQUESTED a review of supplier response times following
    complaints from the operations team.
"""

FINANCIAL_SUMMARY = """\
DOCUMENT ID: FIN-SUMMARY

NORTHWIND LOGISTICS LIMITED
QUARTERLY FINANCIAL SUMMARY (UNAUDITED)
All figures in EUR.

Quarter        Revenue        Cost of Sales    Gross Profit
2024 Q1        8,050,000      6,540,000        1,510,000
2024 Q2        8,310,000      6,700,000        1,610,000
2024 Q3        8,180,000      6,620,000        1,560,000
2024 Q4        8,420,000      6,780,000        1,640,000
2025 Q1        9,120,000      7,350,000        1,770,000
2025 Q2        9,480,000      7,610,000        1,870,000

Notes:
N.1 Gross profit is stated before administrative expenses and finance costs.
N.2 Figures for 2025 are unaudited and subject to year-end adjustment.
N.3 Quarters are calendar quarters. FY refers to the calendar year.
"""

INTERNAL_POLICY = """\
DOCUMENT ID: POL-3.1

NORTHWIND LOGISTICS LIMITED
DATA RETENTION AND PROCUREMENT POLICY
Version 3.1 - effective 1 January 2025

P-1  PURPOSE
P-1.1 This policy sets out mandatory requirements for the retention of data
      held by third parties and for the approval of procurement contracts.

P-2  SUPPLIER PERFORMANCE
P-2.1 Supplier performance is reviewed quarterly by the Operations Director.
P-2.2 Suppliers must provide a named escalation contact.
P-2.3 Suppliers must respond to queries classified as critical within 1
      business day.

P-4  DATA HELD BY THIRD PARTIES
P-4.1 Suppliers processing Northwind personal data must hold it only for as
      long as necessary for the contracted purpose.
P-4.2 All Northwind personal data held by a third-party processor must be
      deleted within 6 months of the termination of the relevant contract.
P-4.3 Deletion must be confirmed in writing to the Data Protection Officer.

P-6  PROCUREMENT APPROVALS
P-6.1 Procurement contracts with an annual value exceeding EUR 250,000
      require two authorised signatures.
P-6.2 Contracts below that threshold require one authorised signature.
P-6.3 The authorised signatory list is maintained by the Company Secretary.
"""

DOCUMENTS: dict[str, str] = {
    "MSA-2024": MSA,
    "AMD-1": AMENDMENT_1,
    "AMD-2": AMENDMENT_2,
    "BM-EXTRACTS": BOARD_MINUTES,
    "FIN-SUMMARY": FINANCIAL_SUMMARY,
    "POL-3.1": INTERNAL_POLICY,
}

# Document order matters: the amendments deliberately follow the MSA so that
# a model reading in order meets the superseded value FIRST. Presenting them
# the other way round would make the supersession items easier than the real
# task, where the base contract is always the bulkiest document in the pack.
PACK_ORDER = ["MSA-2024", "AMD-1", "AMD-2", "BM-EXTRACTS", "FIN-SUMMARY", "POL-3.1"]


# --------------------------------------------------------------------------
# DISTRACTORS - realistic bulk that answers nothing
# --------------------------------------------------------------------------
# gemini-3.7-flash scored 20/20 on the six-document pack, so the pack has a
# ceiling and cannot locate the frontier for strong models. A real engagement
# pack is not six documents, it is a data room. These add plausible bulk that
# contains NO answer to any question, so the questions stay identical and the
# only variable is how much irrelevant material must be read past.
#
# Each distractor is templated on a DIFFERENT counterparty with a DIFFERENT
# clause numbering scheme. Literal repetition would be trivially ignorable and
# would make a long pack EASIER than a short one, which is the opposite of the
# effect being measured.
#
# TODO: distractor mode is BUILT BUT NOT VALIDATED - do not score a model with it.
# Why: a distractor that plausibly answers a question would let a model source a
#   "correct" value from a document meant to answer nothing, and no score would
#   reveal it.
# Trigger: tools/validate_ps_eval.py, 2026-08-15 - reported six bare-value
#   collisions; the validator is now scoped to the core graders only.
#
# The first check attempted - assert the distractors' numbers are disjoint from
# the expected answers - is the WRONG instrument, and that is the useful part.
# 1, 2, 5, 6 and 12 fall out of "ARTICLE II" and ordinary clause numbering in
# any realistic contract, and grading only ever reads the MODEL's answer text,
# never the pack. What is actually needed is a SEMANTIC check: no distractor may
# specify a response time, a retention period, a liability cap or a notice
# period, because those are the four things the questions ask about.

_DISTRACTOR_TEMPLATE = """\
DOCUMENT ID: {doc_id}

SERVICES AGREEMENT - {counterparty}

between NORTHWIND LOGISTICS LIMITED ("the Client") and {counterparty}
("the Provider")

Dated {date}

ARTICLE I - SCOPE
1.1 The Provider shall supply {service} to the Client's {site} operation.
1.2 Volumes are forecast quarterly and are not a committed minimum.
1.3 The Provider shall nominate an account manager within 10 working days.

ARTICLE II - CHARGES
2.1 Charges are set out in the rate card at Appendix One and are reviewed
    annually each {month}.
2.2 Fuel surcharges are applied monthly by reference to the published index.
2.3 The Client shall settle undisputed sums within {payment} days of invoice.
2.4 Disputed sums must be notified within 15 working days with supporting
    detail.

ARTICLE III - DURATION
3.1 This agreement runs for an initial period of {years} years from the date
    above.
3.2 Renewal is automatic for successive periods of 18 months unless notice
    is served under Article III.3.
3.3 Either party may serve notice not to renew, {notice} months before the
    anniversary.

ARTICLE IV - PERFORMANCE
4.1 The Provider shall achieve on-time delivery of {otd}% measured monthly.
4.2 Persistent failure over two consecutive quarters is a material breach.
4.3 Performance is reviewed at a quarterly business review.

ARTICLE V - GENERAL
5.1 Neither party may assign without the other's written consent.
5.2 The agreement is governed by the laws of Ireland.
5.3 Notices are served on the registered office of each party.
5.4 This agreement supersedes all prior arrangements between the parties in
    respect of {service}.

APPENDIX ONE - RATE CARD SUMMARY
Lane {site} to Dublin Port: rate band {band}.
Lane Dublin Port to {site}: rate band {band}.
Additional handling: charged at the standard tariff.
Storage beyond {years} days: charged at the standard tariff.
"""

# Field values are chosen to avoid every number that appears in an expected
# answer (30, 48, 12, 24, 90, 120, 5, 6, 1, 2 as periods, and the money and
# percentage figures). Validated mechanically, not by eye.
_DISTRACTOR_SPECS = [
    {"counterparty": "Ardfinnan Freight Services Limited", "date": "8 May 2023",
     "service": "groupage haulage", "site": "Little Island", "month": "March",
     "payment": "45", "years": "3", "notice": "4", "otd": "97", "band": "CN"},
    {"counterparty": "Lough Derg Warehousing DAC", "date": "22 September 2023",
     "service": "bonded warehousing", "site": "Ringaskiddy", "month": "July",
     "payment": "60", "years": "4", "notice": "7", "otd": "98", "band": "BW"},
    {"counterparty": "Ballyvourney Cold Chain Limited", "date": "14 January 2024",
     "service": "temperature-controlled distribution", "site": "Mallow",
     "month": "October", "payment": "35", "years": "16", "notice": "9",
     "otd": "96", "band": "DS"},
    {"counterparty": "Sliabh Luachra Transport Co-operative", "date": "3 June 2024",
     "service": "final-mile delivery", "site": "Tralee", "month": "February",
     "payment": "75", "years": "7", "notice": "8", "otd": "94", "band": "AQ"},
    {"counterparty": "Kenmare Bay Logistics Limited", "date": "19 November 2024",
     "service": "container drayage", "site": "Fenit", "month": "August",
     "payment": "55", "years": "8", "notice": "11", "otd": "99", "band": "EK"},
    {"counterparty": "Glanmire Pallet Network Limited", "date": "27 February 2025",
     "service": "pallet network services", "site": "Carrigtwohill",
     "month": "December", "payment": "40", "years": "9", "notice": "13",
     "otd": "95", "band": "FG"},
]


def distractors(count: int) -> list[str]:
    """Render `count` distractor documents, cycling the specs if asked for more."""
    if count < 0:
        raise ValueError(
            f"distractor count {count} is negative. hint: 0 means the base pack"
        )
    out = []
    for i in range(count):
        spec = dict(_DISTRACTOR_SPECS[i % len(_DISTRACTOR_SPECS)])
        suffix = "" if i < len(_DISTRACTOR_SPECS) else f"-{i // len(_DISTRACTOR_SPECS) + 1}"
        spec["counterparty"] = spec["counterparty"] if not suffix else (
            spec["counterparty"].replace(" Limited", f" (No{suffix.strip('-')}) Limited")
        )
        out.append(_DISTRACTOR_TEMPLATE.format(doc_id=f"SVC{i + 1:02d}", **spec))
    return out


def build_pack(distractor_count: int = 0) -> str:
    """The engagement pack as one context blob.

    `distractor_count` 0 reproduces the ORIGINAL six-document pack byte for
    byte, so arms already run against it stay comparable. Distractors are
    interleaved around the real documents rather than appended, because
    burying the amendments in the middle of a data room is the realistic case
    and appending would leave the answer-bearing documents conveniently first.
    """
    real = [DOCUMENTS[doc_id] for doc_id in PACK_ORDER]
    if distractor_count == 0:
        ordered = real
    else:
        noise = distractors(distractor_count)
        ordered = []
        # deterministic interleave: spread the noise evenly between the real
        # documents, with the tail of the noise after the last real document
        per_gap = len(noise) // (len(real) + 1)
        extra = len(noise) - per_gap * (len(real) + 1)
        idx = 0
        for slot in range(len(real) + 1):
            take = per_gap + (1 if slot < extra else 0)
            ordered.extend(noise[idx:idx + take])
            idx += take
            if slot < len(real):
                ordered.append(real[slot])
    parts = []
    for doc in ordered:
        parts.append("=" * 70)
        parts.append(doc)
    parts.append("=" * 70)
    return "\n".join(parts)
