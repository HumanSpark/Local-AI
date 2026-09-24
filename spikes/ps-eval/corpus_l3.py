# File: corpus_l3.py
# Purpose: Level-3 pack - the L2 documents buried in a realistic engagement folder of competing agreements.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: Qwen3.8 exhausted L1 (20/20) and L2 (12/12 on the unquantised
# arm). Both packs are about 3K tokens - three pages. Real professional work
# arrives as a folder: the master agreement, its amendments, and a dozen other
# contracts the same client has signed with other suppliers, all of which have
# their own liability caps, notice periods and retention rules.
#
# L3 CHANGES EXACTLY ONE VARIABLE: the size of the haystack. The questions,
# the reasoning they demand and the correct answers are IDENTICAL to L2. That
# is the whole design. A tier that made the questions harder AND the pack
# longer could not tell you which of the two caused a drop, and this
# experiment exists to isolate scale.
#
# THE DISTRACTORS ARE DELIBERATELY CONFUSABLE, and that is the point. Making
# them topic-free - an office lease, a pension summary - would test nothing:
# no model confuses a pension scheme with a services agreement. Each distractor
# is a services agreement between DIFFERENT parties with its OWN liability cap,
# its OWN notice period, its OWN retention rule and its OWN amendments. The
# question being asked is the one a firm actually gets wrong: given nine
# agreements that all have a liability cap, can you report the cap from the
# RIGHT one?
#
# WHICH MEANS THE QUESTIONS MUST NAME THEIR SCOPE. questions_l3.py rescopes
# every L2 question to name the agreement and the parties explicitly. This is
# the V1 lesson from E38 AMENDMENT 1 applied before the fact rather than
# after: a question whose scope is implied is a question a careful reader may
# answer differently from the key, and in a pack of nine agreements the
# implication disappears entirely.
#
# Distractor figures are drawn from DISJOINT ranges (see FIGURE_RANGES) so a
# wrong-document answer is identifiable as such rather than merely wrong -
# `wrong_document` is its own outcome in questions_l3.py.

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus_l2 import DOCUMENTS_L2, SEPARATOR  # noqa: E402

# Every distractor's figures come from these ranges. The real pack uses
# 42,000 / 46,500 / 51,000 retainers, 500,000 / 1,250,000 caps, 90/120 day
# notice and 6/12/24 month retention. Nothing below may collide with those.
FIGURE_RANGES = {
    "retainer": "18,750 to 37,400 - below the real pack's 42,000 floor",
    "cap": "150,000 to 415,000 and 2,100,000 to 3,400,000 - either side of the real 500,000 / 1,250,000",
    "notice": "30, 45, 60, 75, 180 days - never 90 or 120",
    "retention": "3, 9, 18, 36, 48 months - never 6, 12 or 24",
    "response": "3, 4, 5 business days - never 1 or 2",
}

_CORE_DISTRACTOR_SPECS = [
    ("DIS-01", "Northwind Logistics Limited", "Harbourgate Freight Systems Limited",
     "logistics systems integration", 24_800, 275_000, 60, 18, 4, "1 February 2024"),
    ("DIS-02", "Northwind Logistics Limited", "Callaghan Tax Partners LLP",
     "corporate tax advisory", 18_750, 150_000, 45, 36, 5, "12 September 2023"),
    ("DIS-03", "Northwind Logistics Limited", "Tramore Facilities Management Limited",
     "depot facilities management", 31_200, 415_000, 75, 9, 3, "3 June 2024"),
    ("DIS-04", "Northwind Logistics Limited", "Ardfinnan Insurance Brokers Limited",
     "insurance broking and claims handling", 22_400, 340_000, 30, 48, 5, "19 January 2025"),
    ("DIS-05", "Northwind Logistics Limited", "Beltra Digital Studio Limited",
     "brand and digital production", 27_600, 210_000, 60, 3, 4, "8 April 2024"),
    ("DIS-06", "Northwind Logistics Limited", "Clonmacnoise Recruitment Limited",
     "permanent and contract recruitment", 19_900, 195_000, 45, 18, 5, "27 November 2023"),
    ("DIS-07", "Northwind Logistics Limited", "Sliabh Aughty Energy Advisors Limited",
     "energy procurement advisory", 33_500, 2_100_000, 180, 36, 3, "14 July 2024"),
    ("DIS-08", "Northwind Logistics Limited", "Rossaveel Maritime Consulting Limited",
     "port operations consulting", 37_400, 3_400_000, 75, 48, 4, "2 October 2024"),
    ("DIS-09", "Northwind Logistics Limited", "Kilcolgan Software Services Limited",
     "warehouse management software support", 29_300, 385_000, 30, 9, 3, "22 May 2025"),
]

# ---------------------------------------------------------------------------
# E48 EXTENSION: distractors 10-119.
#
# E41 swept 0, 4 and 9 distractors and SATURATED - 12/12 at every size, zero
# `wrong_document`, and its registered falsifier fired. Its own text says the
# next probe has to go further out. Nine distractors is ~21K tokens against a
# model trained to 262,144, so the haystack was never the constraint; this
# extension exists to make it one.
#
# THE FIRST NINE SPECS ABOVE ARE LITERAL AND UNTOUCHED, and every arm E41 ran
# must stay byte-identical or it stops being a baseline. Two things protect
# that: the extension only ADDS ids, and build_pack_l3 now selects in
# DECLARATION order rather than by string sort - "DIS-10" sorts before
# "DIS-02" and would have silently reshuffled which distractors a small pack
# contains.
#
# The extra suppliers are COMBINATORIAL rather than typed out. 110 more
# hand-written tuples is 110 more chances to reuse a real figure, and that is
# the one error no score would reveal: a distractor sharing the real cap makes
# a wrong-document answer grade as correct. Places x trades guarantees the
# supplier names are unique by construction, and the figures are derived by
# index arithmetic that cannot leave the ranges in FIGURE_RANGES. The
# disjointness assertion at the bottom of this file still checks the result -
# generation is a reason to trust the input, not a reason to drop the check.
_EXTRA_PLACES = [
    "Ballyvaughan", "Carrickfergus", "Dunmanway", "Enniscorthy", "Glenbeigh",
    "Inchydoney", "Kinvara", "Lisdoonvarna", "Moneygall", "Newmarket",
    "Oughterard", "Portumna", "Rathmullan", "Skibbereen", "Termonfeckin",
    "Uggool", "Ventry", "Warrenpoint", "Youghal", "Ardglass",
    "Bunratty", "Cushendall",
]

_EXTRA_TRADES = [
    ("Analytics Limited", "supply chain analytics"),
    ("Legal Services Limited", "commercial legal support"),
    ("Fleet Maintenance Limited", "vehicle fleet maintenance"),
    ("Training Partners Limited", "workforce training and certification"),
    ("Environmental Consulting Limited", "environmental compliance consulting"),
]

_EXTRA_MONTHS = ["January", "February", "March", "April", "May", "June", "July",
                 "August", "September", "October", "November", "December"]


def _extra_specs() -> list[tuple]:
    """Distractors 10-119, deterministic and reproducible from this source.

    No randomness anywhere: a corpus that regenerated differently between two
    runs would make every scale comparison meaningless, and the difference
    would not show up in any score.
    """
    specs: list[tuple] = []
    for i, (place, (trade, subject)) in enumerate(
            (p, t) for p in _EXTRA_PLACES for t in _EXTRA_TRADES):
        # Every figure below is forced inside FIGURE_RANGES by construction.
        retainer = 18_750 + (i * 173) % 18_650            # 18,750 - 37,399
        if i % 4 == 3:
            cap = 2_100_000 + (i * 8_641) % 1_300_001     # 2.1M - 3.4M
        else:
            cap = 150_000 + (i * 4_931) % 265_001         # 150,000 - 415,000
        notice = (30, 45, 60, 75, 180)[i % 5]
        # Decorrelated from notice on purpose. Sharing i % 5 would make every
        # agreement with a 30-day notice also have a 3-month retention, so a
        # model could get retention right by reading the notice period.
        retention = (3, 9, 18, 36, 48)[(i // 5) % 5]
        response = (3, 4, 5)[i % 3]
        dated = (f"{1 + (i * 7) % 28} {_EXTRA_MONTHS[i % 12]} "
                 f"{2023 + (i % 3)}")
        specs.append((f"DIS-{i + 10}", "Northwind Logistics Limited",
                      f"{place} {trade}", subject,
                      retainer, cap, notice, retention, response, dated))
    return specs


_DISTRACTOR_SPECS = _CORE_DISTRACTOR_SPECS + _extra_specs()

_ids = [s[0] for s in _DISTRACTOR_SPECS]
if len(set(_ids)) != len(_ids):
    raise ValueError(
        f"duplicate distractor ids in _DISTRACTOR_SPECS ({len(_ids)} specs, "
        f"{len(set(_ids))} unique). "
        f"hint: two agreements sharing a DOCUMENT ID makes the pack ambiguous "
        f"and any citation ungradeable"
    )
_suppliers = [s[2] for s in _DISTRACTOR_SPECS]
if len(set(_suppliers)) != len(_suppliers):
    raise ValueError(
        f"duplicate supplier names in _DISTRACTOR_SPECS ({len(_suppliers)} specs, "
        f"{len(set(_suppliers))} unique). "
        f"hint: the tier asks the model to distinguish agreements BY PARTY, so "
        f"two agreements with the same supplier have no single right answer"
    )


def _distractor(doc_id: str, client: str, supplier: str, subject: str,
                retainer: int, cap: int, notice: int, retention: int,
                response: int, dated: str) -> str:
    """One realistic services agreement, structurally parallel to the MSA.

    Structurally parallel ON PURPOSE. A distractor written in a different
    format is skimmable; one that uses the same clause numbering as the real
    agreement forces the model to distinguish by PARTY rather than by shape,
    which is the discrimination the tier is testing.
    """
    return f"""\
DOCUMENT ID: {doc_id}

SERVICES AGREEMENT

between {client} ("the Client")
and {supplier} ("the Supplier")

Dated {dated}

1. SERVICES
1.1 The Supplier shall provide {subject} services as described in the
    Schedule to this Agreement.
1.2 The Supplier shall perform the Services with reasonable skill and care.

2. FEES AND PAYMENT
2.1 The Client shall pay the Supplier a monthly retainer of EUR {retainer:,},
    exclusive of VAT.
2.2 Invoices are payable within 30 days of receipt.

3. TERM AND TERMINATION
3.1 This Agreement continues until terminated in accordance with this clause.
3.2 Either party may terminate this Agreement for convenience by giving
    {notice} days written notice to the other party.

4. LIABILITY
4.1 The Supplier's aggregate liability arising out of or in connection with
    this Agreement is limited to EUR {cap:,}.
4.2 Neither party is liable for indirect or consequential loss.

5. DATA PROTECTION
5.1 The Supplier acts as a data processor in respect of Client personal data
    processed under this Agreement.
5.2 The Supplier shall retain Client personal data for no longer than
    {retention} months following termination or expiry of this Agreement.

6. SERVICE LEVELS
6.1 The Supplier shall acknowledge and respond to written queries from the
    Client within {response} Business Days.

7. CONFIDENTIALITY
7.1 Each party shall keep confidential all Confidential Information of the
    other party disclosed in connection with this Agreement, and shall not
    disclose it to any third party without prior written consent.
7.2 The obligations in clause 7.1 do not apply to information which is or
    becomes public through no breach of this Agreement, was lawfully in the
    receiving party's possession before disclosure, or is required to be
    disclosed by law or by a competent regulatory authority.
7.3 Each party shall limit disclosure of Confidential Information to those of
    its personnel and professional advisers who need to know it for the
    purposes of this Agreement, and shall procure that they are bound by
    obligations of confidentiality no less onerous than those in this clause.
7.4 The obligations in this clause survive termination or expiry of this
    Agreement without limit of time.

8. INTELLECTUAL PROPERTY
8.1 All intellectual property rights in materials created by the Supplier
    specifically for the Client in the course of providing the Services vest
    in the Client on creation, and the Supplier assigns all such rights to
    the Client with full title guarantee.
8.2 The Supplier retains all intellectual property rights in its
    pre-existing methodologies, templates, tools and know-how, and grants the
    Client a non-exclusive, royalty-free licence to use them to the extent
    necessary to enjoy the benefit of the Services.
8.3 The Supplier warrants that the Services and any deliverables will not
    infringe the intellectual property rights of any third party.
8.4 The Client grants the Supplier a limited licence to use Client materials
    solely for the purpose of providing the Services.

9. WARRANTIES AND UNDERTAKINGS
9.1 Each party warrants that it has full power and authority to enter into
    this Agreement and to perform its obligations under it.
9.2 The Supplier warrants that it holds, and will maintain throughout the
    term, all licences, permits and consents necessary to provide the
    Services.
9.3 The Supplier undertakes to comply with all applicable laws in the
    performance of the Services, including applicable data protection and
    anti-bribery legislation.
9.4 Except as expressly set out in this Agreement, all warranties, conditions
    and terms implied by statute or common law are excluded to the fullest
    extent permitted by law.

10. INSURANCE
10.1 The Supplier shall maintain professional indemnity insurance with a
     reputable insurer covering the Services, and shall produce evidence of
     cover on reasonable request.
10.2 The Supplier shall maintain employer's liability and public liability
     cover as required by law.
10.3 Maintaining insurance does not limit the Supplier's liability under
     this Agreement.

11. FORCE MAJEURE
11.1 Neither party is liable for any failure or delay in performing its
     obligations under this Agreement to the extent caused by an event beyond
     its reasonable control, including act of God, flood, fire, epidemic,
     industrial action not involving that party's own workforce, failure of
     public telecommunications networks, or the act of any government.
11.2 The affected party shall notify the other promptly and shall use
     reasonable endeavours to mitigate the effect of the event.
11.3 If the event continues for a continuous period exceeding three months,
     either party may terminate this Agreement by written notice.

12. ASSIGNMENT AND SUBCONTRACTING
12.1 Neither party may assign, transfer or otherwise deal with any of its
     rights or obligations under this Agreement without the prior written
     consent of the other, such consent not to be unreasonably withheld.
12.2 The Supplier may subcontract performance of any part of the Services
     with the Client's prior written consent, and remains responsible for the
     acts and omissions of any subcontractor as for its own.

13. NOTICES
13.1 Any notice under this Agreement must be in writing and delivered by
     hand, sent by pre-paid registered post, or sent by email to the address
     notified by the receiving party for that purpose.
13.2 A notice delivered by hand is deemed received on delivery; one sent by
     registered post is deemed received on the second Business Day after
     posting; one sent by email is deemed received on transmission, provided
     no delivery failure notification is received.

14. GENERAL
14.1 No variation of this Agreement is effective unless in writing and signed
     by an authorised representative of each party.
14.2 No failure or delay by a party in exercising any right under this
     Agreement constitutes a waiver of that right.
14.3 If any provision of this Agreement is found to be invalid or
     unenforceable, the remaining provisions continue in full force.
14.4 This Agreement constitutes the entire agreement between the parties in
     relation to its subject matter and supersedes all prior discussions,
     correspondence and understandings.
14.5 Nothing in this Agreement creates a partnership, joint venture or
     relationship of employer and employee between the parties.
14.6 A person who is not a party to this Agreement has no right to enforce
     any of its terms.
14.7 This Agreement is governed by the laws of Ireland and the courts of
     Ireland have exclusive jurisdiction.

SCHEDULE 1 - THE SERVICES
S1.1 The Supplier shall provide {subject} services as more particularly
     described in the statement of work agreed between the parties from time
     to time.
S1.2 The Supplier shall assign a named engagement lead who will act as the
     principal point of contact for the Client.
S1.3 The Supplier shall attend review meetings at the Client's premises or
     remotely as the parties agree.
S1.4 The Supplier shall provide a written progress report in advance of each
     review meeting, summarising work performed, work planned, and any matter
     requiring a decision by the Client.
S1.5 Any change to the scope of the Services must be agreed through the
     change control procedure and recorded in writing before the work is
     undertaken.

SCHEDULE 2 - CHANGE CONTROL
S2.1 Either party may request a change to the Services by written notice.
S2.2 The Supplier shall respond with an assessment of the effect of the
     proposed change on the fees, the timetable and the Services.
S2.3 No change takes effect until it has been agreed in writing by an
     authorised representative of each party.
S2.4 Where the parties fail to agree a change, the Agreement continues
     unaffected and the Services continue as previously agreed.

SCHEDULE 3 - DATA PROCESSING PARTICULARS
S3.1 Subject matter: the provision of {subject} services.
S3.2 Nature and purpose of processing: storage, retrieval, analysis and
     reporting in connection with the Services.
S3.3 Categories of data subject: employees, contractors and business contacts
     of the Client.
S3.4 Categories of personal data: name, business contact details, role, and
     such other data as the Client provides in connection with the Services.
S3.5 The Supplier shall implement appropriate technical and organisational
     measures to protect Client personal data against unauthorised or
     unlawful processing and against accidental loss or damage.
S3.6 The Supplier shall assist the Client in responding to requests from data
     subjects exercising their rights.
"""


DISTRACTORS: dict[str, str] = {
    spec[0]: _distractor(*spec) for spec in _DISTRACTOR_SPECS
}

# The real documents are NOT placed first. A pack whose answer always sits at
# the top measures reading order, not retrieval - and "the model reads the
# beginning of the context" is a known result that needs no new experiment.
# The interleave puts the master agreement roughly a third of the way in and
# scatters the amendments after it, which is how a real folder arrives.
_BASE_ORDER_L3 = [
    "DIS-01", "DIS-02", "DIS-03",
    "MSA-2024",
    "DIS-04", "DIS-05",
    "AMD-1", "AMD-2",
    "DIS-06", "DIS-07",
    "AMD-3", "SIDE-1",
    "DIS-08", "DIS-09",
    "BM-EXTRACTS", "FIN-SUMMARY", "POL-3.1",
]

# Where the extension's distractors go, as positions in _BASE_ORDER_L3. The
# obvious implementation - append them all after POL-3.1 - would put every
# real document in the first 8% of a 119-distractor pack and quietly turn the
# tier back into a reading-order test, which is the exact thing the interleave
# above exists to prevent. Eleven insertion points spread the extension either
# side of the real documents instead: two land before MSA-2024, so it still
# sits roughly a fifth of the way in at full size, and one lands after
# POL-3.1 so the pack does not end on a real document either.
_INSERT_AT = (0, 3, 4, 6, 8, 10, 12, 14, 15, 16, 17)

# Round-robin, so that ANY prefix of the declaration order is spread across
# all eleven points. Filling the points in turn would make the n=29 pack a
# front-loaded block rather than a folder, and the intermediate rungs are the
# ones that locate a boundary.
_INSERTIONS: dict[int, list[str]] = {at: [] for at in _INSERT_AT}
_extra_ids = [s[0] for s in _DISTRACTOR_SPECS[len(_CORE_DISTRACTOR_SPECS):]]
for _n, _did in enumerate(_extra_ids):
    _INSERTIONS[_INSERT_AT[_n % len(_INSERT_AT)]].append(_did)

PACK_ORDER_L3 = []
for _pos in range(len(_BASE_ORDER_L3) + 1):
    PACK_ORDER_L3.extend(_INSERTIONS.get(_pos, []))
    if _pos < len(_BASE_ORDER_L3):
        PACK_ORDER_L3.append(_BASE_ORDER_L3[_pos])

DOCUMENTS_L3: dict[str, str] = {**DOCUMENTS_L2, **DISTRACTORS}


def build_pack_l3(distractor_count: int | None = None) -> str:
    """The L3 pack. `distractor_count` trims the distractor set for a size sweep.

    Trimming preserves the interleave rather than truncating the tail, so a
    smaller pack is still a pack with the real documents buried in it rather
    than a pack with the real documents at the end.
    """
    keep = set(DISTRACTORS)
    if distractor_count is not None:
        if not 0 <= distractor_count <= len(DISTRACTORS):
            raise ValueError(
                f"distractor_count {distractor_count} outside 0..{len(DISTRACTORS)}. "
                f"hint: the corpus defines {len(DISTRACTORS)} distractor agreements"
            )
        # DECLARATION order, not sorted order. Sorting is a string sort, under
        # which "DIS-10" precedes "DIS-02", so once the corpus passed nine
        # agreements a sorted prefix would have silently changed WHICH
        # distractors every small pack contains - including E41's arms.
        keep = set(_ids[:distractor_count])
    order = [n for n in PACK_ORDER_L3 if n in DOCUMENTS_L2 or n in keep]
    missing = [n for n in order if n not in DOCUMENTS_L3]
    if missing:
        raise KeyError(
            f"PACK_ORDER_L3 names {missing} which are absent from DOCUMENTS_L3. "
            f"hint: add the document or remove it from PACK_ORDER_L3"
        )
    return SEPARATOR.join(DOCUMENTS_L3[n] for n in order)


# The values that identify a WRONG-DOCUMENT answer, per figure kind. A model
# that reports one of these has retrieved from a distractor, which is a
# different and more diagnostic failure than an arithmetic slip.
DISTRACTOR_FIGURES = {
    "retainer": sorted({s[4] for s in _DISTRACTOR_SPECS}),
    "cap": sorted({s[5] for s in _DISTRACTOR_SPECS}),
    "notice": sorted({s[6] for s in _DISTRACTOR_SPECS}),
    "retention": sorted({s[7] for s in _DISTRACTOR_SPECS}),
    "response": sorted({s[8] for s in _DISTRACTOR_SPECS}),
}

# Assert the disjointness the ranges above promise. A distractor that happens
# to reuse a real figure would make a wrong-document answer look correct, and
# no score would reveal it. Checked at import so it cannot rot.
_REAL_FIGURES = {
    "retainer": {42_000, 46_500, 51_000},
    "cap": {500_000, 1_250_000},
    "notice": {90, 120},
    "retention": {6, 12, 24},
    "response": {1, 2},
}
for _kind, _values in DISTRACTOR_FIGURES.items():
    _clash = set(_values) & _REAL_FIGURES[_kind]
    if _clash:
        raise ValueError(
            f"distractor {_kind} figures {sorted(_clash)} collide with the real pack. "
            f"hint: a colliding figure makes a wrong-document answer score as correct; "
            f"pick values outside {sorted(_REAL_FIGURES[_kind])} ({FIGURE_RANGES[_kind]})"
        )
