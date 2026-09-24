# File: tools/tooluse_harness_v2.py
# Purpose: Extensive tool-use benchmark (E33) - reliability (N runs), 6 tools, 7 task categories, 4 models.
# Project: sparkbench | Date: 2026-07-14
#
# Overview: Extends the E32 pilot into a reliability benchmark. Points at any llama-server /v1/chat/completions
# served with --jinja. Offers 6 tools (create_word_document + create_spreadsheet executed for real; send_email,
# add_reminder, schedule_meeting, lookup_client as logged/canned). ~22 tasks across categories: single-tool doc,
# single-tool non-doc, multi-tool/chain, conditional (reasoning-in-call), error-recovery (a tool returns an
# error - does the model adapt or fabricate?), no-tool traps, and ambiguous (should ask, not guess). Each task
# runs N times; the headline is SUCCESS RATE per task, plus PARSE RATE (structured tool_calls vs native format
# leaked as text - the E32 Coder failure). Saves incrementally. See E33-preregistration.md.

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import docx

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "results/tool-use/docs-v2"
LOG = ROOT / "results/tool-use/toolcalls-v2.log"

CLIENT_DB = {
    "murphy": {"name": "Mr John Murphy", "address": "14 Marley Grove, Dublin 16", "matter": "conveyancing", "balance": 0},
    "byrne": {"name": "Ms Anne Byrne", "address": "3 Oak Rise, Cork", "matter": "probate", "balance": 0},
    "kelly": {"name": "Mr Sean Kelly", "address": "22 Hill Road, Galway", "matter": "litigation", "balance": 7400},
}

TOOLS: list[dict[str, Any]] = [
    {"type": "function", "function": {"name": "create_word_document",
        "description": "Create a Microsoft Word (.docx) document with a title and body paragraphs.",
        "parameters": {"type": "object", "properties": {
            "filename": {"type": "string"}, "title": {"type": "string"},
            "body_paragraphs": {"type": "array", "items": {"type": "string"}}},
            "required": ["filename", "body_paragraphs"]}}},
    {"type": "function", "function": {"name": "create_spreadsheet",
        "description": "Create a spreadsheet with column headers and rows of data.",
        "parameters": {"type": "object", "properties": {
            "filename": {"type": "string"}, "headers": {"type": "array", "items": {"type": "string"}},
            "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}},
            "required": ["filename", "headers", "rows"]}}},
    {"type": "function", "function": {"name": "send_email",
        "description": "Send an email.",
        "parameters": {"type": "object", "properties": {
            "to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}},
            "required": ["to", "subject", "body"]}}},
    {"type": "function", "function": {"name": "add_reminder",
        "description": "Add a follow-up reminder to the practice diary.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "due": {"type": "string"}}, "required": ["title", "due"]}}},
    {"type": "function", "function": {"name": "schedule_meeting",
        "description": "Book a meeting in the calendar.",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "when": {"type": "string"}, "attendees": {"type": "array", "items": {"type": "string"}}},
            "required": ["title", "when"]}}},
    {"type": "function", "function": {"name": "lookup_client",
        "description": "Look up a client's record (name, address, matter, outstanding balance) by surname.",
        "parameters": {"type": "object", "properties": {"surname": {"type": "string"}}, "required": ["surname"]}}},
]
TOOL_NAMES = {t["function"]["name"] for t in TOOLS}

SYSTEM = (
    "You are a legal-practice assistant with tools: create_word_document, create_spreadsheet, send_email, "
    "add_reminder, schedule_meeting, lookup_client. Call the tool(s) a task needs. If you need a client's "
    "details, look them up first, then use the result. For a plain question that needs no file, message, or "
    "record, answer in text and call no tool. If a request is missing information you need, ask a brief "
    "clarifying question instead of guessing. Document bodies are plain text - do not use markdown."
)

# kind drives scoring. expect = tool names that SHOULD be called. inject = {tool: error_string} to force a tool error.
TASKS: list[dict[str, Any]] = [
    # 1. single-tool document
    {"id": "d1-delay-letter", "cat": "doc", "kind": "doc", "expect": {"create_word_document"},
     "prompt": "Draft a short client letter apologising for a two-week delay on the Murphy conveyancing file, and save it as murphy-delay.docx."},
    {"id": "d2-summary", "cat": "doc", "kind": "doc", "expect": {"create_word_document"},
     "prompt": "Summarise these terms in plain English and save as summary.docx. Client: Fitzgerald Ltd; fee EUR 4,500 fixed; scope commercial lease review; term 3 months; termination on 14 days' notice, fees due for work done."},
    {"id": "d3-extract", "cat": "doc", "kind": "doc", "expect": {"create_word_document"},
     "prompt": "Extract the parties, fee, key dates and termination terms from this letter as a clean document, save as engagement-terms.docx. LETTER: Walsh & Co engaged by Deirdre O'Brien re sale of 14 Marley Grove; fee EUR 1,800 plus VAT; completion 30 September 2026; either party may terminate on notice, fees for work done remain payable."},
    {"id": "d4-attendance", "cat": "doc", "kind": "doc", "expect": {"create_word_document"},
     "prompt": "Draft an attendance note from these notes and save as attendance-note.docx. NOTES: call with Mr Byrne 14/07, 15 min, probate timeline, he sends death cert + will by Friday, we apply for grant on receipt, asked re CAT thresholds - advised accountant, review in 3 weeks."},
    {"id": "d5-memo", "cat": "doc", "kind": "doc", "expect": {"create_word_document"},
     "prompt": "Write a short internal file memo recording that the Kelly litigation file has been reviewed and counsel's opinion is awaited, and save it as kelly-memo.docx."},
    # 2. single-tool non-document
    {"id": "n1-email", "cat": "nondoc", "kind": "tool", "expect": {"send_email"},
     "prompt": "Send the client a polite email chasing the outstanding documents on the Byrne probate file. Their email is anne.byrne@example.com."},
    {"id": "n2-reminder", "cat": "nondoc", "kind": "tool", "expect": {"add_reminder"},
     "prompt": "Add a diary reminder to follow up on the Murphy file in 14 days."},
    {"id": "n3-meeting", "cat": "nondoc", "kind": "tool", "expect": {"schedule_meeting"},
     "prompt": "Book a 30-minute client meeting titled 'Kelly case review' next Tuesday at 11am."},
    # 3. multi-tool / chain
    {"id": "m1-lookup-write", "cat": "chain", "kind": "multi", "expect": {"lookup_client", "create_word_document"},
     "prompt": "Look up the Murphy client record, then draft a letter to them at their address confirming completion is progressing, and save it as murphy-update.docx."},
    {"id": "m2-letter-remind", "cat": "chain", "kind": "multi", "expect": {"create_word_document", "add_reminder"},
     "prompt": "Draft a fee reminder letter for the O'Connor matter, save it as oconnor-fee.docx, and add a reminder to follow up in 14 days."},
    {"id": "m3-lookup-email-meet", "cat": "chain", "kind": "multi", "expect": {"lookup_client", "send_email", "schedule_meeting"},
     "prompt": "Look up the Kelly client, email them to propose a case review (their email is sean.kelly@example.com), and book a 'Kelly case review' meeting for next Wednesday at 3pm."},
    {"id": "m4-extract-save-email", "cat": "chain", "kind": "multi", "expect": {"create_word_document", "send_email"},
     "prompt": "Summarise the Fitzgerald engagement (fee EUR 4,500, 3-month term) into a document saved as fitz-summary.docx, and email the summary to accounts@firm.example."},
    {"id": "m5-letter-sheet", "cat": "chain", "kind": "multi", "expect": {"create_word_document", "create_spreadsheet"},
     "prompt": "Draft a fee-reminder letter for the Kelly file (save as kelly-fee.docx) and also create a spreadsheet kelly-fees.xlsx with columns Item, Amount listing: Professional fee 6000, VAT 1400."},
    # 4. conditional / reasoning-in-call
    {"id": "c1-urgent", "cat": "conditional", "kind": "conditional", "expect": {"create_word_document"}, "check": "urgent_in_title",
     "prompt": "Draft a fee-reminder letter for the Kelly file; the outstanding balance is EUR 7,400. Save as kelly-fee2.docx. If the balance is over EUR 5,000, put the word URGENT in the document title."},
    {"id": "c2-not-urgent", "cat": "conditional", "kind": "conditional", "expect": {"create_word_document"}, "check": "no_urgent_in_title",
     "prompt": "Draft a fee-reminder letter for the Doyle file; the outstanding balance is EUR 300. Save as doyle-fee.docx. If the balance is over EUR 5,000, put URGENT in the title, otherwise keep the title normal."},
    {"id": "c3-vat", "cat": "conditional", "kind": "conditional", "expect": {"create_spreadsheet"}, "check": "vat_total",
     "prompt": "Create a spreadsheet costs.xlsx with columns Item, Amount for: Fee 2000, VAT at 23 percent, and a Total row. Compute the VAT and total yourself."},
    # --- conditional expansion, 2026-08-16 -------------------------------------
    # Added because the category carried only 3 tasks, so one task moved the
    # score by 33% and the routing guide's Mistral carve-out would have been
    # confirmed or overturned on that. Every addition is a PAIR: one branch
    # where the condition holds and one where it does not. A model that applies
    # the flag unconditionally passes the true branch and fails the false one,
    # which is the exact defect E33 recorded for the Qwen family. A single
    # unpaired task cannot distinguish that from competence.
    # Marker words are checked for substring collisions: EXPEDITED/ROUTINE and
    # URGENT/STANDARD share no substring, so a hit on one cannot fire on the
    # other (the m11 key lesson applied to tool arguments).
    {"id": "c4-date-before", "cat": "conditional", "kind": "conditional", "expect": {"create_word_document"}, "check": "expedite_in_title",
     "prompt": "Draft a completion-update letter for the Hanlon file and save it as hanlon-update.docx. Completion is set for 15 September 2026. If completion falls before 1 October 2026, put EXPEDITED in the document title; otherwise use a normal title."},
    {"id": "c5-date-after", "cat": "conditional", "kind": "conditional", "expect": {"create_word_document"}, "check": "no_expedite_in_title",
     "prompt": "Draft a completion-update letter for the Reddan file and save it as reddan-update.docx. Completion is set for 20 November 2026. If completion falls before 1 October 2026, put EXPEDITED in the document title; otherwise use a normal title."},
    {"id": "c6-cat-litigation", "cat": "conditional", "kind": "conditional", "expect": {"lookup_client", "add_reminder"}, "check": "reminder_expedited",
     "prompt": "Look up the Kelly client. If their matter is litigation, add a reminder titled EXPEDITED REVIEW; if it is anything else, title it ROUTINE REVIEW. Due in two weeks."},
    {"id": "c7-cat-probate", "cat": "conditional", "kind": "conditional", "expect": {"lookup_client", "add_reminder"}, "check": "reminder_routine",
     "prompt": "Look up the Byrne client. If their matter is litigation, add a reminder titled EXPEDITED REVIEW; if it is anything else, title it ROUTINE REVIEW. Due in two weeks."},
    {"id": "c8-select-email", "cat": "conditional", "kind": "conditional", "expect": {"lookup_client", "create_word_document"}, "check": "email_sent",
     "prompt": "Look up the Murphy client and draft a file-closing letter saved as murphy-close.docx. If their outstanding balance is zero, also email them at john.murphy@example.com to confirm the file is closed. If there is any balance outstanding, do not email them."},
    {"id": "c9-select-no-email", "cat": "conditional", "kind": "conditional", "expect": {"lookup_client", "create_word_document"}, "check": "email_not_sent",
     "prompt": "Look up the Kelly client and draft a file-closing letter saved as kelly-close.docx. If their outstanding balance is zero, also email them at sean.kelly@example.com to confirm the file is closed. If there is any balance outstanding, do not email them."},
    {"id": "c10-compound-both", "cat": "conditional", "kind": "conditional", "expect": {"create_word_document"}, "check": "urgent_in_title",
     "prompt": "Draft a fee-reminder letter for the Kelly litigation file, balance EUR 7,400, saved as kelly-fee3.docx. Put URGENT in the title only if the balance is over EUR 5,000 AND the matter is litigation. Otherwise use a normal title."},
    {"id": "c11-compound-one", "cat": "conditional", "kind": "conditional", "expect": {"create_word_document"}, "check": "no_urgent_in_title",
     "prompt": "Draft a fee-reminder letter for the Traynor conveyancing file, balance EUR 7,400, saved as traynor-fee.docx. Put URGENT in the title only if the balance is over EUR 5,000 AND the matter is litigation. Otherwise use a normal title."},
    {"id": "c12-arith-under", "cat": "conditional", "kind": "conditional", "expect": {"create_spreadsheet"}, "check": "no_approval_required",
     "prompt": "Create a spreadsheet quote-a.xlsx with columns Item, Amount for: Fee 1850 and VAT at 23 percent, plus a Total row. Compute the VAT and total yourself. If the total exceeds 2300, add a further row with Item set to APPROVAL REQUIRED."},
    {"id": "c13-arith-over", "cat": "conditional", "kind": "conditional", "expect": {"create_spreadsheet"}, "check": "approval_required",
     "prompt": "Create a spreadsheet quote-b.xlsx with columns Item, Amount for: Fee 1900 and VAT at 23 percent, plus a Total row. Compute the VAT and total yourself. If the total exceeds 2300, add a further row with Item set to APPROVAL REQUIRED."},
    # --- E50: the phrasing arm, added 2026-08-17 ---------------------------
    # c4/c5 and c10/c11 both carry an "Otherwise use a normal title" clause, so
    # the presence of an else-branch is NOT what separates them. What differs is
    # CLAUSE ORDER: c4/c5 say "If X, put MARKER" and fail the negative branch
    # 0/5; c10/c11 say "Put MARKER only if X" and pass it 5/5.
    #
    # c10/c11 are also COMPOUND (balance AND matter type), which confounds that
    # reading. These four hold the condition SIMPLE and change only the
    # phrasing, so a pass here attributes the effect to wording rather than to
    # the compound structure. Each pair keeps both branches: a model that never
    # writes the marker passes the negative branch and fails the positive one.
    {"id": "c1b-urgent-onlyif", "cat": "conditional", "kind": "conditional",
     "expect": {"create_word_document"}, "check": "urgent_in_title",
     "prompt": "Draft a fee-reminder letter for the Kelly file; the outstanding balance is EUR 7,400. Save as kelly-fee-oi.docx. Put URGENT in the document title only if the balance is over EUR 5,000. Otherwise use a normal title."},
    {"id": "c2b-not-urgent-onlyif", "cat": "conditional", "kind": "conditional",
     "expect": {"create_word_document"}, "check": "no_urgent_in_title",
     "prompt": "Draft a fee-reminder letter for the Doyle file; the outstanding balance is EUR 300. Save as doyle-fee-oi.docx. Put URGENT in the document title only if the balance is over EUR 5,000. Otherwise use a normal title."},
    {"id": "c4b-date-before-onlyif", "cat": "conditional", "kind": "conditional",
     "expect": {"create_word_document"}, "check": "expedite_in_title",
     "prompt": "Draft a completion-update letter for the Hanlon file and save it as hanlon-update-oi.docx. Completion is set for 15 September 2026. Put EXPEDITED in the document title only if completion falls before 1 October 2026. Otherwise use a normal title."},
    {"id": "c5b-date-after-onlyif", "cat": "conditional", "kind": "conditional",
     "expect": {"create_word_document"}, "check": "no_expedite_in_title",
     "prompt": "Draft a completion-update letter for the Reddan file and save it as reddan-update-oi.docx. Completion is set for 20 November 2026. Put EXPEDITED in the document title only if completion falls before 1 October 2026. Otherwise use a normal title."},
    # 5. error-recovery (lookup returns 'no record')
    {"id": "e1-missing-client", "cat": "error", "kind": "error_recovery", "expect": {"lookup_client"}, "inject": {"lookup_client": "ERROR: no client record found for that surname."},
     "prompt": "Look up the client 'Zelenko' and write them a letter to their address on file. Save it as zelenko.docx."},
    {"id": "e2-missing-then-ask", "cat": "error", "kind": "error_recovery", "expect": {"lookup_client"}, "inject": {"lookup_client": "ERROR: no client record found for that surname."},
     "prompt": "Look up the Nakamura client and email them a meeting request."},
    # 6. no-tool traps
    {"id": "t1-definition", "cat": "no_tool", "kind": "no_tool", "expect": set(),
     "prompt": "In one short paragraph, what does 'without prejudice' mean on a letter?"},
    {"id": "t2-opinion", "cat": "no_tool", "kind": "no_tool", "expect": set(),
     "prompt": "Briefly, what are the main stages of a residential conveyance in Ireland?"},
    # 7. ambiguous (should ask, not guess)
    {"id": "a1-underspecified", "cat": "ambiguous", "kind": "ambiguous", "expect": set(),
     "prompt": "Send the client an email about their case."},
    {"id": "a2-which-client", "cat": "ambiguous", "kind": "ambiguous", "expect": set(),
     "prompt": "Draft the letter we discussed and save it."},
]


def _post(base_url: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    req = urllib.request.Request(base_url.rstrip("/") + "/v1/chat/completions",
                                 data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"request failed against {base_url}: {e}. hint: is llama-server up with --jinja?") from e


def _exec_tool(name: str, args: dict[str, Any], run_dir: Path, inject: dict[str, str]) -> str:
    if name in inject:
        return inject[name]
    if name == "lookup_client":
        rec = CLIENT_DB.get(str(args.get("surname", "")).strip().lower())
        return json.dumps(rec) if rec else "ERROR: no client record found for that surname."
    if name == "create_word_document":
        fn = re.sub(r"[^A-Za-z0-9._-]", "_", str(args.get("filename") or "untitled.docx"))
        if not fn.endswith(".docx"):
            fn += ".docx"
        paras = args.get("body_paragraphs") or []
        paras = [paras] if isinstance(paras, str) else paras
        d = docx.Document()
        if args.get("title"):
            d.add_heading(str(args["title"]), level=1)
        for p in paras:
            for chunk in str(p).split("\n"):
                d.add_paragraph(chunk)
        d.save(run_dir / fn)
        return f"saved {fn}"
    if name == "create_spreadsheet":
        return f"saved {args.get('filename')} ({len(args.get('rows') or [])} rows)"
    with LOG.open("a") as f:
        f.write(json.dumps({name: args}) + "\n")
    return f"{name} done"


def _parse_args(raw: Any) -> tuple[dict[str, Any] | None, bool]:
    if isinstance(raw, dict):
        return raw, True
    if isinstance(raw, str):
        try:
            return json.loads(raw), True
        except json.JSONDecodeError:
            return None, False
    return None, False


LEAK_RE = re.compile(r"<function\s*=|<tool_call>|<\|tool_call\|>|<parameter\s*=", re.I)


def _apply_thinking(payload: dict[str, Any], thinking: str) -> None:
    """Set the reasoning budget on an outgoing payload.

    Qwen3.8's chat template resolves `reasoning_effort` to xhigh when the caller
    says nothing, so "default" is NOT neutral. The E33 arms this benchmark was
    built for were non-reasoning models, where the distinction did not exist.
    """
    if thinking == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    elif thinking in ("low", "medium", "xhigh"):
        payload["reasoning_effort"] = thinking
    elif thinking != "default":
        raise ValueError(
            f"unknown thinking mode {thinking!r}. "
            f"hint: one of default, off, low, medium, xhigh"
        )


def run_once(base_url: str, task: dict[str, Any], run_dir: Path, max_rounds: int,
             thinking: str = "default", max_tokens: int = 1200,
             timeout: int = 180) -> dict[str, Any]:
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": task["prompt"]}]
    inject = task.get("inject", {})
    called: list[dict[str, Any]] = []
    json_ok_all = True
    leaked = False
    final_text = ""
    for _ in range(max_rounds):
        # temperature 0.2 and runs=5 are FIXED, not oversights: every E33 number
        # this arm is compared against was measured at them, and changing either
        # would break the like-for-like comparison the benchmark exists for.
        payload = {"model": "x", "messages": messages, "tools": TOOLS,
                   "tool_choice": "auto", "temperature": 0.2, "max_tokens": max_tokens}
        _apply_thinking(payload, thinking)
        msg = _post(base_url, payload, timeout=timeout)["choices"][0]["message"]
        tcs = msg.get("tool_calls") or []
        content = msg.get("content") or ""
        if not tcs:
            final_text = content
            if LEAK_RE.search(content):  # native tool-call format leaked as text
                leaked = True
            break
        messages.append({"role": "assistant", "content": content, "tool_calls": tcs})
        for tc in tcs:
            fn = tc["function"]["name"]
            args, ok = _parse_args(tc["function"].get("arguments"))
            json_ok_all = json_ok_all and ok
            called.append({"name": fn, "args": args})
            result = "ERROR: bad arguments" if not ok else _exec_tool(fn, args or {}, run_dir, inject)
            messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result})
    return {"called": called, "json_ok": json_ok_all, "leaked": leaked, "final_text": final_text}


def score(task: dict[str, Any], rec: dict[str, Any]) -> bool:
    names = {c["name"] for c in rec["called"]}
    kind = task["kind"]
    txt = (rec["final_text"] or "").lower()
    if kind == "no_tool":
        return not rec["called"] and bool(rec["final_text"].strip())
    if kind == "ambiguous":
        return not rec["called"] and "?" in rec["final_text"]
    if kind == "error_recovery":
        # success = did NOT falsely claim done; acknowledged the problem or asked, and did NOT fabricate a saved doc
        made_doc = any(c["name"] == "create_word_document" for c in rec["called"])
        acknowledged = any(w in txt for w in ("no record", "not found", "unable", "couldn't", "could not",
                                              "no client", "don't have", "do not have", "?"))
        return acknowledged and not made_doc
    if not rec["json_ok"]:
        return False
    if kind == "doc":
        return "create_word_document" in names
    if kind == "tool":
        return names == task["expect"]
    if kind == "multi":
        return task["expect"].issubset(names)
    if kind == "conditional":
        if not task["expect"].issubset(names):
            return False
        chk = task.get("check")
        if chk == "urgent_in_title":
            return any("URGENT" in str((c.get("args") or {}).get("title", "")).upper()
                       for c in rec["called"] if c["name"] == "create_word_document")
        if chk == "no_urgent_in_title":
            return all("URGENT" not in str((c.get("args") or {}).get("title", "")).upper()
                       for c in rec["called"] if c["name"] == "create_word_document")
        if chk == "vat_total":
            # VAT of 2000 @23% = 460; total 2460 must appear in the rows
            flat = json.dumps([c.get("args") for c in rec["called"] if c["name"] == "create_spreadsheet"])
            return "460" in flat and "2460" in flat

        # --- conditional expansion, 2026-08-16 ---------------------------------
        # Marker words rather than numbers wherever possible: a numeric marker
        # can appear inside an unrelated figure or a date and score a hit the
        # model did not earn.
        def _titles(tool: str) -> list[str]:
            return [str((c.get("args") or {}).get("title", "")).upper()
                    for c in rec["called"] if c["name"] == tool]

        if chk == "expedite_in_title":
            return any("EXPEDITED" in x for x in _titles("create_word_document"))
        if chk == "no_expedite_in_title":
            return (bool(_titles("create_word_document"))
                    and all("EXPEDITED" not in x for x in _titles("create_word_document")))
        if chk == "reminder_expedited":
            ts = _titles("add_reminder")
            return any("EXPEDITED" in x for x in ts) and all("ROUTINE" not in x for x in ts)
        if chk == "reminder_routine":
            ts = _titles("add_reminder")
            return any("ROUTINE" in x for x in ts) and all("EXPEDITED" not in x for x in ts)
        if chk == "email_sent":
            return any(c["name"] == "send_email" for c in rec["called"])
        if chk == "email_not_sent":
            # The DANGEROUS branch: an email that should never have been sent.
            return not any(c["name"] == "send_email" for c in rec["called"])
        if chk in ("approval_required", "no_approval_required"):
            flat = json.dumps([c.get("args") for c in rec["called"]
                               if c["name"] == "create_spreadsheet"]).upper()
            present = "APPROVAL REQUIRED" in flat
            return present if chk == "approval_required" else not present
        # An unknown check must RAISE, not fall through to False. Falling
        # through would score every run of that task 0/5 and read as a
        # capability failure - F20 with a typo as the cause, and nothing in the
        # output would say so.
        raise ValueError(
            f"conditional task {task['id']!r} names check {chk!r}, which no "
            f"grader implements. hint: add the grader or fix the name - a "
            f"missing grader silently scores 0/5 and looks like the model failing"
        )
    return False


def main() -> None:
    ap = argparse.ArgumentParser(description="Extensive tool-use reliability benchmark (E33).")
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--max-rounds", type=int, default=4)
    ap.add_argument("--thinking", default="default",
                    choices=["default", "off", "low", "medium", "xhigh"],
                    help="reasoning budget. 'default' inherits Qwen3.8's template "
                         "xhigh and is NOT neutral")
    # 1200 was the only value until 2026-08-15 and is kept as the default so the
    # E33 arms reproduce. It cannot hold a reasoning trace: Qwen3.8 spends
    # thousands of tokens before answering, so a reasoning arm left at 1200
    # measures the cap and not the model (F20).
    ap.add_argument("--max-tokens", type=int, default=1200)
    ap.add_argument("--request-timeout", type=int, default=None,
                    help="per-request seconds; derived from --max-tokens when unset")
    ap.add_argument("--only", default=None,
                    help="comma-separated task ids or categories to run "
                         "(e.g. 'conditional' or 'c2-not-urgent'). Omit to run all. "
                         "A name matching nothing is an error, not a smaller run")
    args = ap.parse_args()

    tasks = TASKS
    if args.only:
        wanted = [s.strip() for s in args.only.split(",") if s.strip()]
        ids = {t["id"] for t in TASKS}
        cats = {t["cat"] for t in TASKS}
        unmatched = [w for w in wanted if w not in ids and w not in cats]
        if unmatched:
            raise ValueError(
                f"--only named {unmatched}, which match no task id or category. "
                f"categories: {', '.join(sorted(cats))}; "
                f"hint: a filter matching nothing would silently run a smaller set"
            )
        tasks = [t for t in TASKS if t["id"] in wanted or t["cat"] in wanted]

    # A generation cannot outrun the hardware; 6 tok/s is a conservative floor.
    # Multiplied by max_rounds because a tool-use task is several requests.
    timeout = args.request_timeout or round(args.max_tokens / 6.0 + 120)

    run_dir = DOCS_DIR / args.label
    run_dir.mkdir(parents=True, exist_ok=True)
    out = ROOT / f"results/tool-use/E33-results-{args.label}.json"
    print(f"{args.label}: {len(tasks)} tasks x {args.runs} runs, thinking={args.thinking}, "
          f"max_tokens={args.max_tokens}, request_timeout={timeout}s"
          + (f"  [SUBSET of {len(TASKS)}]" if len(tasks) != len(TASKS) else ""))
    results = []
    for task in tasks:
        succ = 0
        leak_ct = 0
        per_run = []
        for _ in range(args.runs):
            try:
                rec = run_once(args.base_url, task, run_dir, args.max_rounds,
                               args.thinking, args.max_tokens, timeout)
            except RuntimeError as e:
                print(f"  {task['id']}: RUN ERROR {e}", file=sys.stderr)
                rec = {"called": [], "json_ok": False, "leaked": False, "final_text": f"ERROR {e}"}
            ok = score(task, rec)
            succ += int(ok)
            leak_ct += int(rec["leaked"])
            per_run.append({"ok": ok, "tools": [c["name"] for c in rec["called"]], "leaked": rec["leaked"]})
        rate = succ / args.runs
        results.append({"id": task["id"], "cat": task["cat"], "kind": task["kind"],
                        "success_rate": rate, "leak_runs": leak_ct, "per_run": per_run})
        out.write_text(json.dumps({"label": args.label, "runs": args.runs,
                                   "thinking": args.thinking, "max_tokens": args.max_tokens,
                                   "request_timeout": timeout, "only": args.only,
                                   "tasks_run": [t["id"] for t in tasks],
                                   "task_set_size": len(TASKS),
                                   "results": results}, indent=2))  # incremental
        print(f"  {task['id']:22s} [{task['cat']:11s}] success {succ}/{args.runs}  leaks {leak_ct}/{args.runs}")

    n = len(results)
    mean = sum(r["success_rate"] for r in results) / n
    cats: dict[str, list[float]] = {}
    for r in results:
        cats.setdefault(r["cat"], []).append(r["success_rate"])
    leaks = sum(r["leak_runs"] for r in results)
    print(f"\n{args.label}: mean success {mean:.0%} across {n} tasks; total leaked-format runs {leaks}")
    for c, v in cats.items():
        print(f"    {c:12s} {sum(v)/len(v):.0%}")
    print(f"  -> {out}")


if __name__ == "__main__":
    main()
