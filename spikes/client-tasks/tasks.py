# File: spikes/client-tasks/tasks.py
# Purpose: E162's ten client-shaped professional tasks (fictional businesses, synthetic inputs) and their mechanical checks.
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Each task is what a small professional-services firm or an owner-run business actually asks an assistant
# to do: a proposal section from discovery notes, actions from a meeting, a complaint reply, a staff policy summary, a
# board summary from a table, an incident notice, a job ad, a contract explainer, a decision memo, a case-study post.
# Every business, person and figure is invented; nothing quotes a real client (the cloud arms see these prompts).
#
# Each task plants three things a send-ready answer must handle, and that a judge can miss:
#   negatives  facts the reader would rather not hear (a constraint, our own fault, a restriction). Each is a list of
#              regex alternatives; a draft that matches none has DROPPED it.
#   traps      things the source deliberately does not give and a fluent writer tends to supply (a price, a pension
#              rate, a tax relief, "never again"). A match is an over-claim.
#   numbers    every figure in a draft must appear in the source or in the task's `derived` list (sums, dates worked
#              out from the source). Others are FABRICATION CANDIDATES. Integers 0-10 are ignored (list numbering,
#              "two days"); years in the source are allowed by the source rule.
#   word_limit the brief's stated budget; over it by more than 10% is a length violation.
# check(task, draft) returns those four fields. It never decides quality: that is the blind judges' job (E162 prereg).
from __future__ import annotations

import re

HOUSE = (
    "House style: plain British/Irish English, short sentences, no jargon, no exclamation marks. "
    "Use only facts given below. If something the reader would want is not given, say it is to be confirmed "
    "rather than supplying it."
)

TASKS: list[dict] = [
    {
        "id": "C01",
        "kind": "proposal section",
        "word_limit": 400,
        "prompt": f"""You are drafting for a small AI consultancy. Write the "Our understanding and proposed approach"
section of a proposal to the client below, from our discovery-call notes. At most 400 words. {HOUSE}

DISCOVERY CALL NOTES (Wed 5 Nov 2026, 45 min, with Orla Brennan, practice manager)
- Client: Kilbride Veterinary Group. Three clinics: Navan, Trim, Kells. 11 vets, 19 support staff.
- Phones are the pain. Roughly 640 inbound calls a week across the three clinics. Orla estimates about 38% of
  after-hours calls go unanswered or to a voicemail nobody checks until morning.
- Most calls are routine: appointment booking and changes (about half), repeat prescriptions, "is this an
  emergency?" questions. Emergencies must still reach the on-call vet immediately - non-negotiable for Orla.
- Wants: an assistant that answers after hours, books routine appointments, sends reminders, and routes anything
  that might be an emergency straight to the on-call vet's mobile.
- Practice management system is VetLink 4. Orla confirmed VetLink 4 has no API. Bookings would need a daily
  export/import or staff entering them by hand. She was disappointed by this.
- Timeline: they would like it live before the spring vaccination rush in March 2027.
- We suggested a 6-week pilot at one clinic (Trim, the smallest) before rolling out to all three.
- Budget: not discussed. Orla will raise it with the two partners.
- Data: client records include owner names, addresses and phone numbers. Orla asked where call recordings would
  be stored. We said we would come back to her on that.
""",
        "derived": [],
        "negatives": [
            (
                "no API: bookings need export/import or manual entry",
                [r"no api", r"(manual|by hand|export|import)"],
            ),
        ],
        "traps": [
            ("a price or fee", r"€\s?\d|\d\s?(euro|eur)\b"),
            (
                "a storage answer the notes leave open",
                r"(stored|hosted|kept) (securely )?(in|on) (the )?(eu|ireland|europe|azure|aws|our servers)",
            ),
        ],
    },
    {
        "id": "C02",
        "kind": "meeting actions + follow-up email",
        "word_limit": 350,
        "prompt": f"""Turn this meeting transcript into (1) an action list with owner and due date for each action and
(2) a short follow-up email to the attendees. At most 350 words in total. {HOUSE}

MEETING: Harbour Print & Packaging, weekly operations, Thursday 13 November 2026, 9:00-9:25.
Attendees: Declan (MD), Sinead (production), Tomasz (dispatch), Aoife (accounts).

Declan: Right, quick one. Sinead, the Murphy's Bakery boxes?
Sinead: Run finishes tomorrow. Proofs were signed off Monday. We'll have all 4,000 done by Friday afternoon.
Declan: Tomasz, can we get them out Monday?
Tomasz: That's the problem. The van failed its NCT on Tuesday - brakes. It's off the road until the 21st at the
earliest. I can book a courier for Monday but it's about double what we'd normally pay.
Declan: Book the courier. Murphy's matter more than the cost. Tomasz, do that today.
Tomasz: Will do.
Declan: Aoife, where are we with the Clarke & Sons invoice?
Aoife: 67 days overdue. €8,420. I've emailed twice. I'll ring their finance person by Tuesday.
Declan: Good. And if they don't commit to a date, tell me and I'll ring Michael Clarke myself.
Sinead: One more thing - the blue ink supplier has gone quiet. We've about two weeks' stock left.
Declan: Someone needs to chase them.
(Nobody takes it. Meeting moves on.)
Declan: Last thing, the Christmas closing dates. I'll send those round by end of next week.
Meeting ends 9:25.
""",
        "derived": ["14", "17", "18", "20", "21"],
        "negatives": [
            (
                "van off the road (failed NCT) until the 21st at the earliest",
                [r"(van|nct)", r"21"],
            ),
            (
                "ink supplier chase has NO owner agreed",
                [
                    r"(no owner|unassigned|not assigned|nobody|no one|tbc|to be confirmed|needs an owner|owner to be|not yet assigned)"
                ],
            ),
        ],
        "traps": [
            (
                "ink chase assigned to a named person",
                r"(sinead|tomasz|aoife|declan)[^\n]{0,60}(chase|contact|follow up)[^\n]{0,40}ink|ink[^\n]{0,80}(owner|who)[:\s|]*(sinead|tomasz|aoife|declan)",
            ),
        ],
    },
    {
        "id": "C03",
        "kind": "complaint reply",
        "word_limit": 250,
        "prompt": f"""Reply to this customer complaint on behalf of the company, using the internal notes and policy. At
most 250 words. Be honest about what was our fault. Offer only what the policy allows without manager approval.
{HOUSE}

CUSTOMER EMAIL (from Niamh Doyle, Mon 10 Nov 2026)
"I took two days off work for my kitchen installation on 6 and 7 November and nobody turned up on the first day.
On the second day one fitter arrived at 2pm and said the worktops weren't in. Nobody rang me. I want to know what
happened, when my kitchen will actually be fitted, and frankly I want my deposit back."

INTERNAL NOTES (Ardee Kitchens, customer care)
- Order K-2291. Deposit paid: €2,400.
- Day 1 (6 Nov): our scheduler double-booked the two-person fitting team onto another job. Our fault. Nobody rang
  the customer.
- Day 2 (7 Nov): one fitter sent to start carcasses, but the quartz worktops had not arrived from our supplier
  (supplier delay, their fault, but we knew on 5 Nov and should have told the customer).
- New install date: to be confirmed once worktops arrive. Supplier now says week of 24 November.

POLICY (customer care, no approval needed)
- Goodwill gesture up to €150 (voucher or account credit).
- Deposits are non-refundable once materials are ordered (they were ordered on 20 Oct). A refund request must go to
  the operations manager; customer care may not promise one.
- Always give the customer a named contact.
""",
        "derived": [],
        "negatives": [
            (
                "admits the double-booking / our scheduling error",
                [
                    r"(double[- ]book|scheduling (error|mistake)|our (mistake|error|fault))"
                ],
            ),
            (
                "deposit refund cannot be promised (goes to operations manager)",
                [
                    r"(operations manager|non-refundable|cannot (promise|refund)|can't (promise|refund)|not able to refund|unable to refund|refer|pass(ed)? (your|this|it) (request )?(on|to))"
                ],
            ),
        ],
        "traps": [
            (
                "a goodwill offer above €150",
                lambda d: any(v > 150 and v != 2400 for v in _euros(d)),
            ),
            (
                "a promised refund",
                r"(we will|we'll|happy to|going to) (refund|return) (your|the) deposit",
            ),
            (
                "a specific install day the notes do not give",
                r"(monday|tuesday|wednesday|thursday|friday|saturday),? (2[4-9]|30) nov",
            ),
        ],
    },
    {
        "id": "C04",
        "kind": "staff policy summary",
        "word_limit": 300,
        "prompt": f"""Summarise this policy for all staff as a short email from HR. At most 300 words. Staff should know
exactly what applies to them after one read. {HOUSE}

HYBRID WORKING POLICY - Corrib Engineering Ltd (effective 1 January 2027)
1. Scope. Applies to all employees whose role can be done remotely in part, as agreed with their line manager.
   Employees in their first six months (probation) are not eligible; they work from the office full time.
2. Office attendance. A minimum of two days a week in the Galway office. One of those must be Tuesday (team day).
   The second day is agreed with the line manager.
3. Core hours. Whether at home or in the office, employees must be available between 10:00 and 15:00.
4. Approval. Hybrid working starts only after (a) the line manager approves in writing and (b) the employee
   completes the home-office health and safety self-assessment form. Both are required.
5. Equipment. The company provides a laptop and headset. A one-off home-office allowance of up to €300 is paid on
   receipts, for a desk, chair or monitor.
6. Expenses. Travel between home and the office is not reimbursed. The company does not pay home utility bills.
7. Data. Confidential client drawings may not be printed at home.
8. Review. The company may review or withdraw hybrid working for any employee or team with four weeks' written
   notice, for example where business needs change or performance drops.
Questions: hr@corrib-eng.example
""",
        "derived": [],
        "negatives": [
            (
                "can be reviewed or withdrawn with four weeks' notice",
                [r"(withdraw|review)", r"(four|4) weeks"],
            ),
            (
                "probation staff (first six months) not eligible",
                [r"(probation|first (six|6) months)"],
            ),
            (
                "travel and utilities not paid",
                [
                    r"(travel|utilit|bills)[^.]{0,80}(not|n't)|(not|n't)[^.]{0,80}(travel|utilit|bills)"
                ],
            ),
        ],
        "traps": [
            (
                "the Revenue e-working tax relief (not in the policy)",
                r"(e-?working relief|tax relief|revenue|30\s?%|30 per ?cent)",
            ),
            (
                "a daily working-from-home allowance (not in the policy)",
                r"(€\s?3\.20|per day allowance|daily allowance)",
            ),
        ],
    },
    {
        "id": "C05",
        "kind": "board summary from a table",
        "word_limit": 250,
        "prompt": f"""Write a board summary of the third quarter from this table, for the directors of a three-store garden
centre business. At most 250 words. Lead with what the board most needs to know. {HOUSE}

Q3 2026 vs Q3 2025 (July-September), revenue in € thousands, gross margin %

| Store | Q3 2025 revenue | Q3 2026 revenue | Q3 2025 margin | Q3 2026 margin |
|---|---|---|---|---|
| A - Mullingar | 612 | 655 | 41.0% | 40.2% |
| B - Tullamore | 488 | 503 | 39.5% | 38.9% |
| C - Athlone | 530 | 456 | 40.8% | 36.1% |
| Total | 1,630 | 1,614 | 40.5% | 38.6% |

Notes from the finance manager:
- Store C's drop follows the opening of a competitor (a national chain) 2 km away in June 2026.
- Store C ran heavier discounting in August to hold footfall; that explains most of its margin fall.
- Online click-and-collect, launched in May, is included in each store's figures and is not reported separately.
- No one-off items in either year.
""",
        # differences (+43, +15, -74, -16), % changes (7.0, 3.1, 14.0, 1.0 and finer), margin points (0.8, 0.6, 4.7, 1.9)
        "derived": [
            "43",
            "15",
            "74",
            "16",
            "7.0",
            "7.03",
            "3.1",
            "3.07",
            "14.0",
            "13.96",
            "14",
            "13.9",
            "1.0",
            "0.98",
            "0.8",
            "0.6",
            "4.7",
            "1.9",
            "1.6",
            "1.61",
            "1.63",
        ],
        "negatives": [
            (
                "Store C revenue fell about 14%",
                [r"(athlone|store c)", r"(14|13\.9|74)"],
            ),
            ("total margin fell (40.5% to 38.6%)", [r"38\.6"]),
            (
                "total revenue down despite A and B growing",
                [
                    r"(1,?614|total revenue (fell|down|dropped|declined)|down 1(\.0)?%|16k|€16,?000)"
                ],
            ),
        ],
        "traps": [
            (
                "weather given as a cause (not in the notes)",
                r"weather|rain|drought|heatwave",
            ),
            (
                "a click-and-collect figure (not reported separately)",
                r"click[- ]and[- ]collect[^.]{0,60}\d",
            ),
        ],
    },
    {
        "id": "C06",
        "kind": "customer incident notice",
        "word_limit": 200,
        "prompt": f"""Write the notice an accountancy firm will email to all its clients about yesterday's client-portal
outage, from the technical log below. Clients are business owners, not IT people. At most 200 words. {HOUSE}

INCIDENT LOG - Feeney & Walsh Chartered Accountants, client portal (Fri 14 Nov 2026)
- 08:55 Portal begins refusing connections. Browsers show a security warning.
- 09:20 Cause identified: the portal's TLS certificate expired at 08:55. Auto-renewal had been failing silently
  since October because of a changed DNS record.
- 10:40 Certificate renewed, but cached errors persisted for some users.
- 14:55 All checks green. Portal fully available. Total disruption: about 6 hours.
- Data: no unauthorised access. The certificate expiry blocked connections; it did not expose data. Logs reviewed by
  our IT provider.
- Uploads: 4 client uploads made between 08:50 and 08:55 did not complete. Those clients have been identified and
  must resubmit their documents. They will be contacted individually by Monday 17 November.
- Fix: renewal monitoring added; an alert now goes to two people 30 days before any certificate expires.
- No deadlines affected: the 14 Nov ROS filing for affected clients was completed by staff by phone/email.
""",
        "derived": [],
        "negatives": [
            (
                "some uploads failed and must be resubmitted",
                [
                    r"(resubmit|re-submit|upload again|re-upload|send (them|it|your documents) again)"
                ],
            ),
        ],
        "traps": [
            (
                "a promise it can never happen again",
                r"(never|not) (happen|occur) again|will not recur|won't recur|cannot happen again",
            ),
            (
                "a claim that no uploads were affected or lost",
                r"no (uploads|documents|files|data) (were|was) (lost|affected)",
            ),
            (
                "compensation the log does not offer",
                r"(compensat|refund|discount|credit)",
            ),
        ],
    },
    {
        "id": "C07",
        "kind": "job advertisement",
        "word_limit": 300,
        "prompt": f"""Write a job advertisement from the partners' notes below, for the firm's website and LinkedIn. At
most 300 words. Be accurate about the job, including the less attractive parts. {HOUSE}

PARTNERS' NOTES - Office Manager, Gallagher Quinn Solicitors, Dundalk
- Small practice: 3 partners, 4 solicitors, 5 support staff. Mainly conveyancing, probate, family law.
- Role: run the office day to day. Supervise the two receptionists. Manage the diary system, file closing and
  archiving, supplier contracts, IT liaison with our outside provider, and the accounts system for client money
  (with training - must be comfortable with numbers and confidentiality).
- Experience: at least three years in an office management or senior admin role. Legal experience is a plus, not
  required.
- Salary: €42,000 to €46,000 depending on experience.
- Hours: 9:00-17:30 Monday to Friday. One evening a week (Thursday) on reception until 19:00 for late
  appointments - time off in lieu.
- After a six-month probation: one day a week from home possible.
- Pension: to be confirmed with the partners - do not state a rate.
- Start: January 2027.
- Apply: CV and short cover note to careers@gqsolicitors.example by 5 December 2026.
""",
        "derived": ["17:30", "19:00", "9:00"],
        "negatives": [
            (
                "Thursday evening reception cover until 19:00 / 7pm",
                [r"(thursday|evening)", r"(19:00|7\s?pm|7:00|19\.00|7\.00)"],
            ),
            (
                "home working only after a six-month probation",
                [r"(probation|six months|6 months)"],
            ),
        ],
        "traps": [
            ("a pension rate", r"pension[^.]{0,60}\d+\s?%|\d+\s?%[^.]{0,40}pension"),
            (
                "benefits the notes never list",
                r"(health insurance|vhi|laya|bonus|annual leave of|\d{2} days('| )?(annual )?leave)",
            ),
        ],
    },
    {
        "id": "C08",
        "kind": "contract clause explainer",
        "word_limit": 300,
        "prompt": f"""The owner of a small hotel has asked: "Before I sign, what does this contract actually commit me to?
Anything I should worry about?" Write a plain-English email back, at most 300 words. You are not a solicitor: say
where they should get legal advice rather than giving it. {HOUSE}

EXTRACT - Linen and laundry services agreement, Brightwash Services Ltd and the Customer
4.1 Term. The initial term is 24 months from 1 March 2025. The agreement then renews automatically for successive
    12-month periods unless either party gives written notice at least 90 days before the renewal date.
4.2 Exclusivity. During the term the Customer shall obtain all linen hire and laundry services for the Premises
    solely from Brightwash.
6.1 Charges. Charges increase on each anniversary of the start date by the Consumer Price Index (CPI) plus 3
    percentage points, subject to a maximum increase of 8% in any year.
6.4 Minimum volume. The Customer shall pay for a minimum of 900 kg of laundry per month whether or not used.
9.2 Liability. Brightwash's total liability under this agreement shall not exceed the charges paid by the Customer
    in the 12 months before the claim.
9.3 Brightwash is not liable for loss of business or loss of profits, including from late delivery.
""",
        # renewal 1 March 2027 (24 months from 1 March 2025); 90 days before it is 1 December 2026
        "derived": ["2026", "2027"],
        "negatives": [
            (
                "exclusivity: cannot use another provider during the term",
                [
                    r"(exclusiv|solely|only (use|from) brightwash|cannot use (another|any other)|can't use (another|any other))"
                ],
            ),
            ("minimum 900 kg paid whether used or not", [r"900"]),
            (
                "liability capped / no loss-of-business cover",
                [r"(liabilit|loss of (business|profit))"],
            ),
        ],
        "traps": [
            (
                "a legal conclusion that a clause is unenforceable or illegal",
                r"(unenforceable|illegal|unlawful|void)",
            ),
            (
                "a CPI figure the extract never gives",
                r"cpi[^.]{0,40}(is|of|at|currently|running)[^.]{0,10}\d",
            ),
        ],
    },
    {
        "id": "C09",
        "kind": "decision memo",
        "word_limit": 350,
        "prompt": f"""Write a one-page decision memo to the managing director recommending ONE of the two CRM options below,
with the trade-offs stated fairly. At most 350 words. Show the annual cost of each. {HOUSE}

COMPARISON NOTES - CRM replacement, Shannon Freight Forwarding (25 users)
| | Option A: Pipewell | Option B: Larchmont CRM |
|---|---|---|
| Price | €18 per user per month | €29 per user per month |
| Contract | monthly, cancel any time | 12-month minimum commitment |
| Xero integration | none built in; via Zapier, about €60 per month extra | built in |
| Customs-document fields | custom fields, set up by us (about 3 days of Ciara's time) | template exists |
| Data migration from old system | CSV import, we do it | vendor does it, included |
| Support | email only, business hours | phone + email, business hours |
| Trial feedback (6 staff, 2 weeks) | 4 preferred Pipewell's interface | 2 preferred Larchmont |

The accounts team (Gerard) says the Xero link is essential: they re-key every invoice today.
""",
        # A: 18x25x12 = 5,400 + Zapier 60x12 = 720 -> 6,120 (510/month); B: 29x25x12 = 8,700 (725/month); gap 2,580 (215/month)
        "derived": [
            "5400",
            "720",
            "6120",
            "450",
            "510",
            "8700",
            "725",
            "2580",
            "215",
            "216",
            "348",
            "11",
        ],
        "negatives": [
            (
                "Larchmont needs a 12-month minimum commitment",
                [r"12[- ]month", r"(minimum|commit|lock)"],
            ),
            (
                "staff preferred Pipewell's interface in the trial",
                [
                    r"(4 (of|out of) 6|four of (the )?six|preferred pipewell|pipewell'?s interface)"
                ],
            ),
        ],
        "traps": [
            (
                "a Zapier reliability claim the notes never make",
                r"zapier[^.]{0,80}(unreliable|break|fail|outage)",
            ),
        ],
    },
    {
        "id": "C10",
        "kind": "case-study social post",
        "word_limit": 180,
        "prompt": f"""Write a LinkedIn post for our consultancy about this client result, from the case-study notes. At most
180 words. The client has approved the quote below and nothing else. Credible, not hype. {HOUSE}

CASE-STUDY NOTES - Reilly Joinery, Cavan (custom kitchens and wardrobes, 14 staff)
- Problem: quotes took about 3 working days because the owner priced every job from scratch in a spreadsheet.
- What we did: built a quoting template from their last 200 jobs, with standard units and finishes priced in, and
  trained the office manager to use it. Six weeks, finished in September 2026.
- Result: about 70% of quotes now go out the same day. The other 30% (unusual layouts, bespoke finishes) still
  need the owner and take about as long as before.
- Approved quote from Fintan Reilly, owner: "Most quotes go out the same day now. Not every job fits the template,
  and that's fine - those are the ones that need me anyway."
- Not approved for publication: revenue figures, win-rate figures, staff names other than Fintan.
""",
        "derived": [],
        "negatives": [
            (
                "about 30% still need the owner / not every job fits",
                [r"(30\s?%|not every job|still need|bespoke|unusual)"],
            ),
        ],
        "traps": [
            (
                "a revenue or win-rate figure (not approved)",
                r"(revenue|win[- ]rate|conversion|sales)[^.]{0,40}\d|\d+\s?%[^.]{0,30}(more|increase|growth|revenue|wins)",
            ),
            (
                "hype words",
                r"(game[- ]chang|revolutioni|transform(ed|ative)|skyrocket)",
            ),
        ],
    },
]

NUM_RE = re.compile(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?")


def _norm(tok: str) -> str:
    t = tok.replace(",", "")
    if "." in t:
        t = t.rstrip("0").rstrip(".")
    return t


def _numbers(text: str) -> list[str]:
    return [_norm(m.group(0)) for m in NUM_RE.finditer(text)]


def _euros(text: str) -> list[float]:
    return [
        float(m.replace(",", "")) for m in re.findall(r"€\s?(\d[\d,]*(?:\.\d+)?)", text)
    ]


def check(task: dict, draft: str) -> dict:
    """Mechanical fields for one draft: dropped negatives, trap hits, fabrication candidates, length."""
    low = draft.lower()
    dropped = [
        name
        for name, pats in task["negatives"]
        if not all(re.search(p, low) for p in pats)
    ]
    traps = [
        name
        for name, pat in task["traps"]
        if (pat(draft) if callable(pat) else re.search(pat, low))
    ]
    allowed = set(_numbers(task["prompt"])) | {_norm(d) for d in task["derived"]}
    allowed |= {a.lstrip("-") for a in allowed}
    fab = []
    for n in _numbers(draft):
        bare = n.lstrip("-")
        try:
            if float(bare) <= 10 and float(bare).is_integer():
                continue
        except ValueError as exc:
            raise ValueError(
                f"unparseable number token {n!r}. hint: NUM_RE matched a non-number"
            ) from exc
        if n not in allowed and bare not in allowed:
            fab.append(n)
    words = len(re.findall(r"\b[\w'’-]+\b", draft))
    return {
        "dropped_negatives": dropped,
        "trap_hits": traps,
        "fabrication_candidates": sorted(set(fab)),
        "words": words,
        "over_length": words > task["word_limit"] * 1.10,
    }
