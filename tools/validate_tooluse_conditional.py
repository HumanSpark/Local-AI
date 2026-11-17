#!/usr/bin/env python3
# File: validate_tooluse_conditional.py
# Purpose: Validate the conditional tool-use graders against synthetic respondents before any model is scored.
# Project: sparkbench | Date: 2026-08-16
#
# Overview: The conditional category grew from 3 tasks to 13 on 2026-08-16
# because a single task moved the category score by 33%, and the routing
# guide's Mistral carve-out would have been confirmed or overturned on that.
# Ten new checks came with it, and an unvalidated check is worse than no check:
# it reports a number nobody can trust. Each respondent below is built to
# trigger exactly one verdict, including the E33 defect itself (a conditional
# flag applied unconditionally) and the dangerous branch (an email sent that
# should not have been). Exits non-zero if any check cannot tell a compliant
# answer from its named failure.
#
# Run: var/tooluse-venv/bin/python3 tools/validate_tooluse_conditional.py

from pathlib import Path

import importlib.util
import sys

spec = importlib.util.spec_from_file_location(
    "h", str(Path(__file__).resolve().parent / "tooluse_harness_v2.py"))
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)

TASKS = {t["id"]: t for t in h.TASKS}

def rec(calls):
    return {"called": [{"name": n, "args": a} for n, a in calls],
            "json_ok": True, "leaked": False, "final_text": ""}

DOC, SS, EM, RM, LK = ("create_word_document", "create_spreadsheet",
                       "send_email", "add_reminder", "lookup_client")
cases = [
    # (task, respondent, expected verdict, what the respondent represents)
    ("c4-date-before", rec([(DOC, {"filename":"hanlon-update.docx","title":"EXPEDITED completion update"})]), True,  "applies flag when condition holds"),
    ("c4-date-before", rec([(DOC, {"filename":"hanlon-update.docx","title":"Completion update"})]),            False, "misses a flag it should apply"),
    ("c5-date-after",  rec([(DOC, {"filename":"reddan-update.docx","title":"Completion update"})]),            True,  "correctly withholds the flag"),
    ("c5-date-after",  rec([(DOC, {"filename":"reddan-update.docx","title":"EXPEDITED completion update"})]),  False, "THE E33 DEFECT: flag applied unconditionally"),
    ("c5-date-after",  rec([]),                                                                                False, "called nothing at all"),
    ("c6-cat-litigation", rec([(LK,{"surname":"Kelly"}),(RM,{"title":"EXPEDITED REVIEW","due":"2 weeks"})]),    True,  "correct branch"),
    ("c6-cat-litigation", rec([(LK,{"surname":"Kelly"}),(RM,{"title":"ROUTINE REVIEW","due":"2 weeks"})]),      False, "wrong branch"),
    ("c7-cat-probate",    rec([(LK,{"surname":"Byrne"}),(RM,{"title":"ROUTINE REVIEW","due":"2 weeks"})]),      True,  "correct branch"),
    ("c7-cat-probate",    rec([(LK,{"surname":"Byrne"}),(RM,{"title":"EXPEDITED REVIEW","due":"2 weeks"})]),    False, "applied the litigation branch to probate"),
    ("c8-select-email",   rec([(LK,{"surname":"Murphy"}),(DOC,{"filename":"murphy-close.docx","title":"Closing"}),(EM,{"to":"x","subject":"s","body":"b"})]), True,  "sends when balance is zero"),
    ("c8-select-email",   rec([(LK,{"surname":"Murphy"}),(DOC,{"filename":"murphy-close.docx","title":"Closing"})]),                                          False, "omits an email it should send"),
    ("c9-select-no-email",rec([(LK,{"surname":"Kelly"}),(DOC,{"filename":"kelly-close.docx","title":"Closing"})]),                                            True,  "correctly withholds the email"),
    ("c9-select-no-email",rec([(LK,{"surname":"Kelly"}),(DOC,{"filename":"kelly-close.docx","title":"Closing"}),(EM,{"to":"x","subject":"s","body":"b"})]),   False, "SENDS AN EMAIL IT SHOULD NOT - the dangerous branch"),
    ("c10-compound-both", rec([(DOC,{"filename":"kelly-fee3.docx","title":"URGENT fee reminder"})]),            True,  "both conjuncts true"),
    ("c11-compound-one",  rec([(DOC,{"filename":"traynor-fee.docx","title":"Fee reminder"})]),                  True,  "one conjunct false, no flag"),
    ("c11-compound-one",  rec([(DOC,{"filename":"traynor-fee.docx","title":"URGENT fee reminder"})]),           False, "evaluated only the balance"),
    ("c12-arith-under",   rec([(SS,{"filename":"quote-a.xlsx","headers":["Item","Amount"],"rows":[["Fee","1850"],["VAT","425.50"],["Total","2275.50"]]})]),                          True,  "computed 2275.50, withheld the flag"),
    ("c12-arith-under",   rec([(SS,{"filename":"quote-a.xlsx","headers":["Item","Amount"],"rows":[["Fee","1850"],["VAT","425.50"],["Total","2275.50"],["APPROVAL REQUIRED",""]]})]), False, "added the flag without checking the total"),
    ("c13-arith-over",    rec([(SS,{"filename":"quote-b.xlsx","headers":["Item","Amount"],"rows":[["Fee","1900"],["VAT","437.00"],["Total","2337.00"],["APPROVAL REQUIRED",""]]})]), True,  "computed 2337, added the flag"),
    ("c13-arith-over",    rec([(SS,{"filename":"quote-b.xlsx","headers":["Item","Amount"],"rows":[["Fee","1900"],["VAT","437.00"],["Total","2337.00"]]})]),                          False, "missed a flag it should have added"),
    # E165 audit (task set v3): the lookup SYSTEM instructs is not an extra tool; anything else still is.
    ("n3-meeting", rec([(LK,{"surname":"Kelly"}),("schedule_meeting",{"title":"Kelly case review","when":"Tue 11am"})]), True,  "instructed lookup, then the booking"),
    ("n3-meeting", rec([("schedule_meeting",{"title":"Kelly case review","when":"Tue 11am"}),(EM,{"to":"x","subject":"s","body":"b"})]), False, "an unrequested email is still a failure"),
    ("n1-email",   rec([(LK,{"surname":"Byrne"}),(EM,{"to":"anne.byrne@example.com","subject":"s","body":"b"})]), True,  "instructed lookup, then the chaser"),
    ("n1-email",   rec([(LK,{"surname":"Byrne"})]),                                                                False, "looked up and sent nothing"),
]

# Every client a task names resolves (only e1/e2's deliberate misses do not), in the spellings models send.
lookups = [("O'Connor", "oconnor"), ("OConnor", "oconnor"), ("Mr Liam O'Connor", "oconnor"), ("Fitzgerald Ltd", "fitzgerald"),
           ("Doyle", "doyle"), ("Hanlon", "hanlon"), ("Reddan", "reddan"), ("Traynor", "traynor"), ("O'Brien", "obrien"),
           ("Kelly", "kelly"), ("Zelenko", None), ("Nakamura", None)]
for arg, want in lookups:
    got = h.lookup_key_or_none(arg)
    ok = got == want
    print(f"  {'ok  ' if ok else 'FAIL'} lookup {arg!r:22s} want={want} got={got}")
    if not ok:
        sys.exit(1)
assert h.CLIENT_DB["doyle"]["balance"] == 300 and h.CLIENT_DB["traynor"]["matter"] == "conveyancing", \
    "a v3 record disagrees with its task prompt. hint: c2 says EUR 300, c11 says conveyancing"

fails = 0
for tid, r, want, desc in cases:
    got = h.score(TASKS[tid], r)
    ok = got == want
    fails += (not ok)
    print(f"  {'ok  ' if ok else 'FAIL'} {tid:20s} want={str(want):5s} got={str(got):5s}  {desc}")
print(f"\n{len(cases)-fails}/{len(cases)} synthetic respondents scored correctly")
sys.exit(1 if fails else 0)
