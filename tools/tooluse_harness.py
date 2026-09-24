# File: tools/tooluse_harness.py
# Purpose: Benchmark local models on office tool use (OpenAI function calling) - can a model correctly
#          call create_word_document to produce a real .docx, select among tools, and chain steps?
# Project: sparkbench | Date: 2026-07-14
#
# Overview: Points at any llama-server /v1/chat/completions endpoint served with --jinja. Offers two
# tools on every task (create_word_document - executed for real via python-docx; add_reminder - a
# distractor executed as a logged no-op) so tool SELECTION is tested. Runs an agentic loop (up to
# --max-rounds tool rounds, feeding tool results back so chaining can happen). Scores each task on
# CALL-VALID (right tool, JSON parses, required args present), COMPLETE (real on-task .docx or correct
# no-op), and SELECT (right tool set incl. the no-tool trap). Writes per-task records + a summary JSON.
# Content quality is spot-checked separately (not re-litigating send-readiness). See E32-preregistration.md.

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import docx  # python-docx (var/tooluse-venv)

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "results/tool-use/docs"
REMINDER_LOG = ROOT / "results/tool-use/reminders.log"

TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "create_word_document",
            "description": "Create a Microsoft Word (.docx) document on disk with a title and body paragraphs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "output filename ending in .docx"},
                    "title": {"type": "string", "description": "the document heading"},
                    "body_paragraphs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "the document body, one string per paragraph",
                    },
                },
                "required": ["filename", "body_paragraphs"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_reminder",
            "description": "Add a follow-up reminder to the practice diary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "due": {"type": "string", "description": "when the reminder is due, e.g. 'in 14 days'"},
                },
                "required": ["title", "due"],
            },
        },
    },
]

SYSTEM = (
    "You are a legal-practice assistant with access to tools. When the user asks you to produce or save "
    "a document, call create_word_document. When they ask for a reminder or follow-up, call add_reminder. "
    "For a task needing several actions, call each required tool. For a plain question that needs no file "
    "or reminder, just answer in text - do not call a tool."
)

# expect: which tool names SHOULD be called (set). empty set = no tool (text answer expected).
TASKS: list[dict[str, Any]] = [
    {
        "id": "01-delay-letter", "kind": "single",
        "prompt": "Draft a short, professional client letter apologising for a two-week delay on the Murphy "
                  "conveyancing file, and save it as a Word document named murphy-delay.docx.",
        "expect": {"create_word_document"},
    },
    {
        "id": "02-summary", "kind": "grounded",
        "prompt": "Here are the key terms of an engagement:\n"
                  "Client: Fitzgerald Ltd. Fee: EUR 4,500 fixed. Scope: commercial lease review and negotiation. "
                  "Term: 3 months from signature. Termination: either party on 14 days' written notice; fees due for "
                  "work done.\nWrite a plain-English summary a client would understand, and save it as summary.docx.",
        "expect": {"create_word_document"},
    },
    {
        "id": "03-extract", "kind": "grounded",
        "prompt": "From this engagement letter, extract the parties, the fee, the key dates, and the termination terms "
                  "as a clean structured document, and save it as engagement-terms.docx.\n\n"
                  "ENGAGEMENT LETTER: This letter confirms the engagement of Walsh & Co Solicitors by Deirdre O'Brien "
                  "in the matter of the sale of 14 Marley Grove. Our fee is EUR 1,800 plus VAT and outlay. Completion is "
                  "targeted for 30 September 2026. Either party may terminate on written notice; fees for work done to "
                  "date remain payable.",
        "expect": {"create_word_document"},
    },
    {
        "id": "04-attendance-note", "kind": "grounded",
        "prompt": "Draft an attendance note from these meeting notes and save it as attendance-note.docx.\n"
                  "NOTES: Call with client (Mr Byrne) 14/07, 15 min. Discussed probate timeline. He will send the death "
                  "cert and the will by Friday. We will apply for the grant once received. He asked about CAT thresholds; "
                  "advised to consult accountant. Next review in 3 weeks.",
        "expect": {"create_word_document"},
    },
    {
        "id": "05-email-and-copy", "kind": "single",
        "prompt": "Draft a polite chasing email to the client for the outstanding documents on the Byrne probate file, "
                  "and save a Word copy of it as byrne-chaser.docx.",
        "expect": {"create_word_document"},
    },
    {
        "id": "06-two-tools", "kind": "multi",
        "prompt": "Draft a fee reminder letter for the O'Connor matter and save it as oconnor-fee.docx, and also add a "
                  "reminder to follow up in 14 days.",
        "expect": {"create_word_document", "add_reminder"},
    },
    {
        "id": "07-conditional", "kind": "conditional",
        "prompt": "Draft a fee-reminder letter for the Kelly file. The outstanding balance is EUR 7,400. Save it as "
                  "kelly-fee.docx - and if the balance is over EUR 5,000, put the word URGENT in the document title.",
        "expect": {"create_word_document"},
        "check": "urgent_in_title",  # 7400 > 5000, so title MUST contain URGENT
    },
    {
        "id": "08-no-tool-trap", "kind": "no-tool",
        "prompt": "In one short paragraph, what does 'without prejudice' mean when written on a letter?",
        "expect": set(),  # correct behaviour: answer in text, NO tool call
    },
]


def _post(base_url: str, payload: dict[str, Any], timeout: int = 180) -> dict[str, Any]:
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.load(r)
    except (urllib.error.URLError, TimeoutError) as e:  # noqa: PERF203
        raise RuntimeError(
            f"chat/completions request failed against {base_url}: {e}. "
            "hint: is llama-server up on that port and started with --jinja?"
        ) from e


def _exec_tool(name: str, args: dict[str, Any], run_dir: Path) -> str:
    """Execute a tool call for real. Returns a short tool-result string."""
    if name == "create_word_document":
        fn = str(args.get("filename") or "untitled.docx")
        fn = re.sub(r"[^A-Za-z0-9._-]", "_", fn)
        if not fn.endswith(".docx"):
            fn += ".docx"
        paras = args.get("body_paragraphs") or []
        if isinstance(paras, str):
            paras = [paras]
        d = docx.Document()
        title = args.get("title")
        if title:
            d.add_heading(str(title), level=1)
        for p in paras:
            for chunk in str(p).split("\n"):
                d.add_paragraph(chunk)
        out = run_dir / fn
        d.save(out)
        nwords = sum(len(str(p).split()) for p in paras)
        return f"saved {fn} ({nwords} words, {len(paras)} paragraphs)"
    if name == "add_reminder":
        with REMINDER_LOG.open("a") as f:
            f.write(json.dumps(args) + "\n")
        return f"reminder added: {args.get('title')} due {args.get('due')}"
    return f"unknown tool {name}"


def _parse_args_json(raw: Any) -> tuple[dict[str, Any] | None, bool]:
    """Return (parsed_args, json_ok). llama.cpp returns arguments as a JSON string."""
    if isinstance(raw, dict):
        return raw, True
    if not isinstance(raw, str):
        return None, False
    try:
        return json.loads(raw), True
    except json.JSONDecodeError:
        return None, False


def run_task(base_url: str, task: dict[str, Any], run_dir: Path, max_rounds: int) -> dict[str, Any]:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": task["prompt"]},
    ]
    called: list[dict[str, Any]] = []
    json_ok_all = True
    final_text = ""
    docs_written: list[str] = []
    for _ in range(max_rounds):
        payload = {"model": "x", "messages": messages, "tools": TOOLS,
                   "tool_choice": "auto", "temperature": 0.2, "max_tokens": 1200}
        resp = _post(base_url, payload)
        msg = resp["choices"][0]["message"]
        tcs = msg.get("tool_calls") or []
        if not tcs:
            final_text = msg.get("content") or ""
            break
        messages.append({"role": "assistant", "content": msg.get("content") or "", "tool_calls": tcs})
        for tc in tcs:
            fn = tc["function"]["name"]
            args, json_ok = _parse_args_json(tc["function"].get("arguments"))
            json_ok_all = json_ok_all and json_ok
            called.append({"name": fn, "args": args, "json_ok": json_ok})
            result = "ERROR: could not parse arguments as JSON"
            if json_ok and args is not None:
                try:
                    result = _exec_tool(fn, args, run_dir)
                    if fn == "create_word_document" and result.startswith("saved"):
                        docs_written.append(result.split()[1])
                except Exception as e:  # noqa: BLE001
                    result = f"ERROR executing {fn}: {e}"
            messages.append({"role": "tool", "tool_call_id": tc.get("id", ""), "content": result})

    called_names = {c["name"] for c in called}
    expect: set[str] = task["expect"]
    # scoring
    call_valid = bool(called) and json_ok_all and called_names.issubset({t["function"]["name"] for t in TOOLS})
    select = called_names == expect
    complete = True
    if expect:
        complete = bool(docs_written) if "create_word_document" in expect else True
        if "add_reminder" in expect:
            complete = complete and any(c["name"] == "add_reminder" and c["json_ok"] for c in called)
    else:
        # no-tool trap: complete = answered in text AND called nothing
        complete = (not called) and bool(final_text.strip())
    # conditional check
    cond_ok = None
    if task.get("check") == "urgent_in_title":
        titles = [str((c.get("args") or {}).get("title", "")) for c in called if c["name"] == "create_word_document"]
        cond_ok = any("URGENT" in t.upper() for t in titles)
    return {
        "id": task["id"], "kind": task["kind"], "expect": sorted(expect),
        "called": called, "docs_written": docs_written, "final_text": final_text[:500],
        "score": {"call_valid": call_valid, "select": select, "complete": complete, "conditional": cond_ok},
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Benchmark a local model on office tool use (Word-doc creation via function calling).",
        epilog="Example: tooluse_harness.py --base-url http://127.0.0.1:8400 --label qwen3-30b",
    )
    ap.add_argument("--base-url", required=True, help="llama-server base URL (must be served with --jinja)")
    ap.add_argument("--label", required=True, help="short model label for output paths")
    ap.add_argument("--max-rounds", type=int, default=3, help="max agentic tool rounds per task")
    args = ap.parse_args()

    run_dir = DOCS_DIR / args.label
    run_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for task in TASKS:
        t0 = time.time()
        try:
            r = run_task(args.base_url, task, run_dir, args.max_rounds)
        except RuntimeError as e:
            print(f"  {task['id']}: RUN ERROR {e}", file=sys.stderr)
            r = {"id": task["id"], "error": str(e), "score": {}}
        r["seconds"] = round(time.time() - t0, 1)
        s = r.get("score", {})
        print(f"  {task['id']:20s} call_valid={s.get('call_valid')} select={s.get('select')} "
              f"complete={s.get('complete')} cond={s.get('conditional')} ({r['seconds']}s)")
        results.append(r)

    out = ROOT / f"results/tool-use/results-{args.label}.json"
    out.write_text(json.dumps({"label": args.label, "base_url": args.base_url, "results": results}, indent=2))
    n = len(results)
    cv = sum(1 for r in results if r.get("score", {}).get("call_valid"))
    se = sum(1 for r in results if r.get("score", {}).get("select"))
    co = sum(1 for r in results if r.get("score", {}).get("complete"))
    print(f"\n{args.label}: call_valid {cv}/{n}  select {se}/{n}  complete {co}/{n}  -> {out}")


if __name__ == "__main__":
    main()
