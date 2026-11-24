#!/usr/bin/env python3
# File: tools/run_e170.py
# Purpose: Run and score E170 - memory-extraction jobs (the nightly "propose memory entries" shape) across local models.
# Project: sparkbench | Date: 2026-11-21
#
# Overview: Reads spikes/memory-tasks/bank.json (50 tasks: 30 extract, 20 update; ground truth by construction).
#   run   --arm F|I|H --url <chat/completions URL> [--model NAME]  -> results/e170/out-<arm>.json (resumable)
#   grade                                                          -> results/e170/score.json + a printed table
# Arm F is production Flash-Next through model-guard (no effort sent = the live default, low). Arms I and H are
# Inkling-2-Mini and Hy-Memory on a sparkbench llama-server started separately (one at a time). Every call:
# temperature 0, one sample, bounded timeout. Replies are parsed for the first JSON object after removing any
# think block or code fence; an unparseable reply is kept raw and scored as a miss, never coerced.
# Scoring is mechanical against the bank: precision/recall/F1 on confirmed (key, value) facts; trap hits by kind
# (stale, colleague, hypothetical, rejected); promoted suggestions; and for update, whole-memory exact matches,
# stale values kept, changes applied and unchanged entries lost.
from __future__ import annotations

import argparse
import datetime
import json
import re
import statistics
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BANK = ROOT / "spikes" / "memory-tasks" / "bank.json"
OUT = ROOT / "results" / "e170"
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

RULES = """Rules:
- Only facts the USER states about themselves or their own business.
- Not facts about other people (colleagues, other companies), not hypotheticals, not things they only considered,
  turned down or used to have.
- If the user corrects themselves, keep only the corrected value.
- Use only these keys, with these value formats:
{keys}
- Write integers without currency symbols or commas, dates as YYYY-MM-DD, weekdays as a single day name."""

EXTRACT = """You maintain a long-term memory about the user of an assistant. Read the conversation and list the facts it
gives about the user.

{rules}
- If the ASSISTANT proposes something and the user neither accepts nor rejects it (for example "maybe"), include it
  with status "suggestion". Everything the user states as true gets status "confirmed".

Reply with JSON only, in exactly this shape:
{{"facts": [{{"key": "...", "value": ..., "status": "confirmed"}}]}}

Conversation:
{conv}"""

UPDATE = """You maintain a long-term memory about the user of an assistant. Here is the memory as stored now, then a
new conversation. Return the complete updated memory.

{rules}
- Keep every stored entry the conversation does not change. Replace a value the user says has changed. Add new facts.

Reply with JSON only: one object mapping each key to its value.

Stored memory:
{mem}

Conversation:
{conv}"""


def prompt_for(task: dict, keys: dict) -> str:
    rules = RULES.format(keys="\n".join(f"  {k}: {v}" for k, v in keys.items()))
    conv = "\n".join(f"{c['role']}: {c['text']}" for c in task["conversation"])
    if task["job"] == "extract":
        return EXTRACT.format(rules=rules, conv=conv)
    return UPDATE.format(rules=rules, mem=json.dumps(task["memory_before"]), conv=conv)


def chat(url: str, model: str, prompt: str, max_tokens: int) -> dict:
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0,
            "max_tokens": max_tokens}
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=1800) as r:
        d = json.load(r)
    ch = d["choices"][0]
    msg = ch["message"]
    return {"output": msg.get("content") or "", "reasoning_chars": len(msg.get("reasoning_content") or ""),
            "finish_reason": ch["finish_reason"], "usage": d.get("usage"), "served_model": d.get("model"),
            "wall_s": round(time.time() - t0, 2)}


def cmd_run(args: argparse.Namespace) -> int:
    bank = json.loads(Path(args.bank).read_text())
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"out-{args.arm}.json"
    done = json.loads(path.read_text()) if path.exists() else {}
    for i, t in enumerate(bank["tasks"], 1):
        if t["id"] in done:
            continue
        r = chat(args.url, args.model, prompt_for(t, bank["keys"]), args.max_tokens)
        done[t["id"]] = r
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(done, indent=1))
        tmp.replace(path)
        print(f"[{args.arm}] {i}/{len(bank['tasks'])} {t['id']} {r['wall_s']}s finish={r['finish_reason']} "
              f"out={len(r['output'])}ch", flush=True)
    return 0


def parse_json(text: str) -> object | None:
    """First JSON object in the reply after dropping think blocks and fences. None = unparseable (scored a miss)."""
    t = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    t = re.sub(r"```(?:json)?", "", t)
    start = t.find("{")
    while start != -1:
        depth = 0
        for j in range(start, len(t)):
            depth += {"{": 1, "}": -1}.get(t[j], 0)
            if depth == 0:
                try:
                    return json.loads(t[start:j + 1])
                except json.JSONDecodeError:
                    break
        start = t.find("{", start + 1)
    return None


def norm(key: str, v: object) -> str:
    s = str(v).strip().lower().replace("€", "").replace(",", "")
    if key in ("day_rate_eur", "team_size"):
        m = re.search(r"\d+", s)
        return m.group(0) if m else s
    if key == "meeting_day":
        return next((d for d in DAYS if s.startswith(d[:3])), s)
    if key == "project_deadline":
        for fmt in ("%Y-%m-%d", "%d %B %Y", "%B %d %Y", "%d/%m/%Y"):
            try:
                return datetime.datetime.strptime(s.title() if "%B" in fmt else s, fmt).date().isoformat()
            except ValueError:
                pass
    return s


def grade_extract(t: dict, parsed: object) -> dict:
    truth = {(k, norm(k, v)) for k, v in t["truth"].items()}
    sugg = {(k, norm(k, v)) for k, v in t["suggestion"].items()}
    conf, as_sugg, bad_keys = set(), set(), 0
    facts = parsed.get("facts") if isinstance(parsed, dict) else None
    for f in facts if isinstance(facts, list) else []:
        if not isinstance(f, dict) or "key" not in f or "value" not in f:
            bad_keys += 1
            continue
        kv = (str(f["key"]), norm(str(f["key"]), f["value"]))
        (as_sugg if str(f.get("status", "confirmed")).lower() == "suggestion" else conf).add(kv)
    traps = {"stale": 0, "colleague": 0, "hypothetical": 0, "rejected": 0}
    for w in t["wrong"]:
        kv = (w["key"], norm(w["key"], w["value"]))
        if kv in conf or (w["trap"] == "rejected" and kv in as_sugg):
            traps[w["trap"]] += 1
    return {"valid": isinstance(facts, list), "tp": len(conf & truth), "fp": len(conf - truth),
            "fn": len(truth - conf), "promoted": len(conf & sugg), "suggestion_kept": len(as_sugg & sugg),
            "bad_items": bad_keys, **traps}


def grade_update(t: dict, parsed: object) -> dict:
    ok = isinstance(parsed, dict)
    out = {str(k): norm(str(k), v) for k, v in parsed.items()} if ok else {}
    truth = {k: norm(k, v) for k, v in t["truth"].items()}
    changed = set(t["changed"])
    new = set(truth) - set(t["memory_before"])
    keep = set(truth) - changed - new
    traps = sum(1 for w in t["wrong"] if w["trap"] != "stale" and out.get(w["key"]) == norm(w["key"], w["value"]))
    return {"valid": ok, "exact": out == truth,
            "changed_applied": sum(out.get(k) == truth[k] for k in changed), "changed_total": len(changed),
            "stale_kept": sum(out.get(k) == norm(k, t["memory_before"][k]) for k in changed),
            "unchanged_lost": sum(out.get(k) != truth[k] for k in keep),
            "new_added": sum(out.get(k) == truth[k] for k in new), "trap_hits": traps,
            "spurious_keys": len(set(out) - set(truth))}


def cmd_grade(args: argparse.Namespace) -> int:
    bank = json.loads(Path(args.bank).read_text())
    out_dir = Path(args.out)
    score: dict = {"bank_seed": bank["seed"], "arms": {}}
    for path in sorted(out_dir.glob("out-*.json")):
        arm = path.stem.split("-", 1)[1]
        runs = json.loads(path.read_text())
        rows = {}
        for t in bank["tasks"]:
            if t["id"] not in runs:
                continue
            parsed = parse_json(runs[t["id"]]["output"])
            g = grade_extract(t, parsed) if t["job"] == "extract" else grade_update(t, parsed)
            rows[t["id"]] = {**g, "wall_s": runs[t["id"]]["wall_s"]}
        ex = [r for k, r in rows.items() if k.startswith("X")]
        up = [r for k, r in rows.items() if k.startswith("U")]
        tp, fp, fn = (sum(r[x] for r in ex) for x in ("tp", "fp", "fn"))
        p = tp / (tp + fp) if tp + fp else 0.0
        rc = tp / (tp + fn) if tp + fn else 0.0
        extract = {"tasks": len(ex), "valid": sum(r["valid"] for r in ex), "tp": tp, "fp": fp, "fn": fn,
                   "precision": round(p, 3), "recall": round(rc, 3),
                   "f1": round(2 * p * rc / (p + rc), 3) if p + rc else 0.0,
                   **{x: sum(r[x] for r in ex) for x in ("stale", "colleague", "hypothetical", "rejected",
                                                          "promoted", "suggestion_kept", "bad_items")}}
        extract["trust_errors"] = sum(extract[x] for x in ("stale", "colleague", "hypothetical", "rejected",
                                                             "promoted"))
        update = {"tasks": len(up), "valid": sum(r["valid"] for r in up), "exact": sum(r["exact"] for r in up),
                  **{x: sum(r[x] for r in up) for x in ("changed_applied", "changed_total", "stale_kept",
                                                         "unchanged_lost", "new_added", "trap_hits",
                                                         "spurious_keys")}}
        walls = [r["wall_s"] for r in rows.values()]
        score["arms"][arm] = {"extract": extract, "update": update,
                              "wall_s_median": round(statistics.median(walls), 2) if walls else None,
                              "wall_s_total": round(sum(walls), 1), "tasks": rows}
    (out_dir / "score.json").write_text(json.dumps(score, indent=1))
    print("arm | X f1 | P | R | trust err (stale/coll/hypo/rej/promo) | X valid | U exact | U stale kept | "
          "U unchanged lost | U traps | median s")
    for arm, a in score["arms"].items():
        e, u = a["extract"], a["update"]
        print(f"{arm} | {e['f1']} | {e['precision']} | {e['recall']} | {e['trust_errors']} "
              f"({e['stale']}/{e['colleague']}/{e['hypothetical']}/{e['rejected']}/{e['promoted']}) | "
              f"{e['valid']}/{e['tasks']} | {u['exact']}/{u['tasks']} | {u['stale_kept']} | {u['unchanged_lost']} | "
              f"{u['trap_hits']} | {a['wall_s_median']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__ or "E170 runner",
                                 epilog="examples:\n  run_e170.py run --arm F --url http://127.0.0.1:8402/v1/chat/"
                                        "completions --model local_smart\n  run_e170.py grade",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank", default=str(BANK), help="bank JSON (E172 uses spikes/memory-tasks/bank_e170b.json)")
    ap.add_argument("--out", default=str(OUT), help="directory for out-<arm>.json and score.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run one arm over the bank (resumable)")
    r.add_argument("--arm", required=True, help="F (production), I (Inkling-2-Mini), H (Hy-Memory)")
    r.add_argument("--url", required=True, help="OpenAI-compatible chat/completions URL")
    r.add_argument("--model", default="local", help="model name sent in the request")
    r.add_argument("--max-tokens", type=int, default=16384, help="per-call output cap")
    sub.add_parser("grade", help="score every out-*.json against the bank")
    args = ap.parse_args()
    return cmd_run(args) if args.cmd == "run" else cmd_grade(args)


if __name__ == "__main__":
    raise SystemExit(main())
