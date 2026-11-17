#!/usr/bin/env python3
# File: tools/run_e162.py
# Purpose: Run E162 - ten client-shaped tasks drafted by production Flash-Next (low/medium/xhigh) and two frontier models,
# checked mechanically and judged blind in pairs by two judges from neither contestant's family.
# Project: sparkbench | Date: 2026-11-15
#
# Overview: Three subcommands, each resumable and writing under results/e162/:
#   draft --arm A   one request per task (spikes/client-tasks/tasks.py), temperature 0, the task prompt as the only user
#                   message. Local arms go to PRODUCTION through model-guard (127.0.0.1:8402, name local_smart): L sends
#                   no effort (the guard's live default, low), M sends medium, X xhigh. Cloud arms go through
#                   tools/cloud_client.chat (OpenRouter key from the vault, spend ceiling). -> drafts-<arm>.json
#   grade           tasks.check() on every draft -> grade.json (dropped negatives, trap hits, fabrication candidates,
#                   length) and a printed table.
#   judge --judge M every pair of arms, every task, both orders, with judge_writing_pairwise's rubric and parser; a pair
#                   is decided only when both orders agree. -> judge-<slug>.json, written after every call.
# Prereg: results/e162-prereg.md. Arms and models are fixed there.
from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results/e162"
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "spikes/client-tasks"))
from cloud_client import CloudBudget, chat  # noqa: E402
from judge_writing_pairwise import build_prompt, combine, parse_verdict  # noqa: E402
from tasks import TASKS, check  # noqa: E402

GUARD = "http://127.0.0.1:8402/v1/chat/completions"
LOCAL = {"L": None, "M": "medium", "X": "xhigh"}
CLOUD = {
    "C": "anthropic/claude-sonnet-5.5",
    "G": "openai/gpt-6.1-sol",
    "Q": "qwen/qwen4-max",
}  # Q added for E164
LOCAL_MAX_TOKENS = 32768
CLOUD_MAX_TOKENS = 16000


def _load(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def _save(path: Path, data: dict) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1))
    tmp.replace(path)


def ask_local(effort: str | None, prompt: str) -> dict:
    body: dict = {
        "model": "local_smart",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": LOCAL_MAX_TOKENS,
    }
    if effort:
        body["reasoning_effort"] = effort
    req = urllib.request.Request(
        GUARD,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=5400) as r:
        d = json.load(r)
    ch = d["choices"][0]
    msg = ch["message"]
    return {
        "output": msg.get("content") or "",
        "reasoning_chars": len(
            msg.get("reasoning_content") or msg.get("reasoning") or ""
        ),
        "finish_reason": ch["finish_reason"],
        "usage": d["usage"],
        "served_model": d["model"],
        "wall_s": round(time.time() - t0, 2),
    }


def cmd_draft(args: argparse.Namespace) -> int:
    arm = args.arm
    path = OUT / f"drafts-{arm}.json"
    data = _load(path) or {
        "arm": arm,
        "model": CLOUD.get(arm, "production local_smart"),
        "effort": LOCAL.get(arm, "provider default"),
        "results": [],
    }
    done = {r["id"] for r in data["results"] if r.get("output")}
    data["results"] = [r for r in data["results"] if r["id"] in done]
    budget = CloudBudget(usd_ceiling=args.usd_ceiling)
    todo = [t for t in TASKS if t["id"] not in done]
    print(f"[{arm}] {len(done)} done, {len(todo)} to draft", flush=True)
    t_arm = time.time()
    for i, t in enumerate(todo, 1):
        print(
            f"[{arm}] {i}/{len(todo)} {t['id']} ({t['kind']}) ... elapsed {time.time() - t_arm:.0f}s",
            flush=True,
        )
        if arm in LOCAL:
            r = ask_local(LOCAL[arm], t["prompt"])
        else:
            c = chat(
                CLOUD[arm],
                [{"role": "user", "content": t["prompt"]}],
                budget,
                provider="openrouter",
                temperature=0,
                max_tokens=CLOUD_MAX_TOKENS,
                timeout=900,
                retries=6,
            )
            r = {
                "output": c["content"],
                "reasoning_chars": c["reasoning_chars"],
                "finish_reason": c["finish_reason"],
                "usage": c["usage"],
                "wall_s": c["wall_s"],
            }
        r["id"] = t["id"]
        r["outcome"] = (
            "ok"
            if r["output"] and r["finish_reason"] == "stop"
            else f"incomplete:{r['finish_reason']}"
        )
        r["think_leak"] = bool(re.search(r"</?think>", r["output"]))
        data["results"].append(r)
        _save(path, data)
        print(
            f"[{arm}]   {t['id']} {r['outcome']} {r['usage'].get('completion_tokens')} tok {r['wall_s']}s",
            flush=True,
        )
    if arm not in LOCAL:
        data["spend"] = budget.as_dict()
        _save(path, data)
    return 0


def cmd_grade(args: argparse.Namespace) -> int:
    report: dict = {}
    for path in sorted(OUT.glob("drafts-*.json")):
        d = json.loads(path.read_text())
        arm = d["arm"]
        by_id = {r["id"]: r for r in d["results"]}
        rows = {}
        for t in TASKS:
            if t["id"] not in by_id:
                raise KeyError(
                    f"{path.name}: no draft for {t['id']}. hint: finish `draft --arm {arm}` first"
                )
            r = by_id[t["id"]]
            rows[t["id"]] = {
                **check(t, r["output"]),
                "outcome": r["outcome"],
                "think_leak": r["think_leak"],
                "completion_tokens": r["usage"].get("completion_tokens"),
                "wall_s": r["wall_s"],
            }
        tot = {
            "dropped_negatives": sum(
                len(x["dropped_negatives"]) for x in rows.values()
            ),
            "trap_hits": sum(len(x["trap_hits"]) for x in rows.values()),
            "fabrication_candidates": sum(
                len(x["fabrication_candidates"]) for x in rows.values()
            ),
            "over_length": sum(x["over_length"] for x in rows.values()),
            "incomplete": sum(x["outcome"] != "ok" for x in rows.values()),
            "think_leaks": sum(x["think_leak"] for x in rows.values()),
            "wall_s_median": sorted(x["wall_s"] for x in rows.values())[len(rows) // 2],
            "wall_s_total": round(sum(x["wall_s"] for x in rows.values()), 1),
            "completion_tokens_total": sum(
                x["completion_tokens"] or 0 for x in rows.values()
            ),
        }
        report[arm] = {"totals": tot, "tasks": rows}
        print(f"{arm}: {tot}", flush=True)
    _save(OUT / "grade.json", report)
    return 0


def cmd_judge(args: argparse.Namespace) -> int:
    slug = args.judge.split("/")[-1]
    path = OUT / f"judge-{slug}.json"
    drafts = {}
    for p in sorted(OUT.glob("drafts-*.json")):
        d = json.loads(p.read_text())
        drafts[d["arm"]] = {r["id"]: r["output"] for r in d["results"]}
    arms = sorted(args.arms.split(",")) if args.arms else sorted(drafts)
    for a in arms:
        missing = [t["id"] for t in TASKS if not drafts.get(a, {}).get(t["id"])]
        if missing:
            raise KeyError(
                f"arm {a} lacks drafts for {missing}. hint: run `draft --arm {a}` to completion first"
            )
    data = _load(path) or {"judge": args.judge, "arms": arms, "records": []}
    seen = {(r["task"], r["x"], r["y"]) for r in data["records"]}
    budget = CloudBudget(usd_ceiling=args.usd_ceiling)
    pairs = list(itertools.combinations(arms, 2))
    n = len(pairs) * len(TASKS)
    print(
        f"{args.judge}: {len(TASKS)} tasks x {len(pairs)} pairs x 2 orders; {len(seen)}/{n} pairs done",
        flush=True,
    )
    k = len(seen)
    if args.redo_empty:
        # Amendment 1 (results/e162-prereg.md): an empty reply is a failed call, not a verdict. Each empty side is
        # re-asked AT MOST ONCE with the same prompt, draft order, temperature, timeout and retries; only max_tokens
        # changes. Successful verdicts are never touched. A side still empty after its retry, or not reached before the
        # ceiling, stays unparsed. The first pass is kept in rec["first_pass"]; its cost stays in data["spend"].
        prompts = {t["id"]: t["prompt"] for t in TASKS}
        stopped = ""
        for rec in data["records"]:
            if "first_pass" not in rec:
                # Records retried before this field existed: the retried side was empty and unparsed on the first pass.
                fp = {
                    k: rec[k] for k in ("verdict_xy", "verdict_yx", "raw_xy", "raw_yx")
                }
                for key in rec.get("redo", {}):
                    fp[f"verdict_{key}"], fp[f"raw_{key}"] = "unparsed", ""
                fp["outcome"] = combine(fp["verdict_xy"], fp["verdict_yx"])
                rec["first_pass"] = fp
            for key, first, second in (
                ("xy", rec["x"], rec["y"]),
                ("yx", rec["y"], rec["x"]),
            ):
                if rec["first_pass"][f"raw_{key}"].strip() or key in rec.get(
                    "redo", {}
                ):
                    continue
                if budget.as_dict()["usd_total"] >= args.usd_ceiling:
                    stopped = f"ceiling ${args.usd_ceiling} reached"
                    break
                r = chat(
                    args.judge,
                    [
                        {
                            "role": "user",
                            "content": build_prompt(
                                prompts[rec["task"]],
                                drafts[first][rec["task"]],
                                drafts[second][rec["task"]],
                            ),
                        }
                    ],
                    budget,
                    provider="openrouter",
                    temperature=0,
                    max_tokens=args.max_tokens,
                    timeout=600,
                    retries=6,
                )
                rec[f"raw_{key}"] = r["content"]
                rec[f"verdict_{key}"] = parse_verdict(r["content"])
                rec.setdefault("redo", {})[key] = {
                    "finish_reason": r["finish_reason"],
                    "max_tokens": args.max_tokens,
                    "completion_tokens": r["usage"].get("completion_tokens"),
                    "reasoning_chars": r["reasoning_chars"],
                    "content_chars": len(r["content"]),
                    "wall_s": r["wall_s"],
                }
                rec["outcome"] = combine(rec["verdict_xy"], rec["verdict_yx"])
                data["spend_redo"] = budget.as_dict()
                _save(path, data)
                print(
                    f"  redo {rec['task']} {rec['x']} v {rec['y']} [{key}]: {rec[f'verdict_{key}']} "
                    f"({r['finish_reason']}, {r['usage'].get('completion_tokens')} tok) -> {rec['outcome']}",
                    flush=True,
                )
            if stopped:
                break
        data["redo_stopped"] = stopped or "complete"
        _save(path, data)
        print(f"redo: {data['redo_stopped']}", flush=True)
    for t in TASKS:
        for x, y in pairs:
            if (t["id"], x, y) in seen:
                continue
            verdicts = []
            for first, second in ((x, y), (y, x)):
                r = chat(
                    args.judge,
                    [
                        {
                            "role": "user",
                            "content": build_prompt(
                                t["prompt"],
                                drafts[first][t["id"]],
                                drafts[second][t["id"]],
                            ),
                        }
                    ],
                    budget,
                    provider="openrouter",
                    temperature=0,
                    max_tokens=6000,
                    timeout=600,
                    retries=6,
                )
                verdicts.append((parse_verdict(r["content"]), r["content"]))
            k += 1
            outcome = combine(verdicts[0][0], verdicts[1][0])
            data["records"].append(
                {
                    "task": t["id"],
                    "x": x,
                    "y": y,
                    "outcome": outcome,
                    "verdict_xy": verdicts[0][0],
                    "verdict_yx": verdicts[1][0],
                    "raw_xy": verdicts[0][1],
                    "raw_yx": verdicts[1][1],
                }
            )
            data["spend"] = budget.as_dict()
            _save(path, data)
            print(
                f"  [{k}/{n}] {t['id']} {x} v {y}: {outcome} ({verdicts[0][0]}/{verdicts[1][0]})",
                flush=True,
            )
    # Every arm in the records, not only --arms: E164 judged into a file that also holds E162's M and X verdicts.
    tally = {
        a: {"win": 0, "tie": 0, "loss": 0}
        for a in sorted(
            {
                *arms,
                *(r["x"] for r in data["records"]),
                *(r["y"] for r in data["records"]),
            }
        )
    }
    for r in data["records"]:
        if r["outcome"] == "x":
            tally[r["x"]]["win"] += 1
            tally[r["y"]]["loss"] += 1
        elif r["outcome"] == "y":
            tally[r["y"]]["win"] += 1
            tally[r["x"]]["loss"] += 1
        elif r["outcome"] == "tie":
            tally[r["x"]]["tie"] += 1
            tally[r["y"]]["tie"] += 1
    data["tally"] = tally
    data["unparsed"] = sum(r["outcome"] == "unparsed" for r in data["records"])
    _save(path, data)
    print(json.dumps(tally), flush=True)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E162 client-shaped tasks: draft, grade, judge.",
        epilog="examples: tools/run_e162.py draft --arm L | tools/run_e162.py grade | "
        "tools/run_e162.py judge --judge x-ai/grok-4.7",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "results/e162",
        help="where drafts, grade and judge files live (E164 uses results/e164/drafting)",
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draft", help="draft every task for one arm (resumable)")
    d.add_argument("--arm", required=True, choices=[*LOCAL, *CLOUD])
    d.add_argument("--usd-ceiling", type=float, default=10.0)
    sub.add_parser("grade", help="mechanical checks on every drafts-*.json")
    j = sub.add_parser("judge", help="blind pairwise judging, both orders (resumable)")
    j.add_argument(
        "--judge",
        required=True,
        help="OpenRouter model id, not from a contestant's family",
    )
    j.add_argument("--arms", default="", help="comma list; default every drafted arm")
    j.add_argument("--usd-ceiling", type=float, default=30.0)
    j.add_argument(
        "--redo-empty",
        action="store_true",
        help="re-ask calls whose reply was empty (amendment 1)",
    )
    j.add_argument(
        "--max-tokens", type=int, default=16000, help="cap for --redo-empty calls"
    )
    args = ap.parse_args()
    global OUT  # noqa: PLW0603 - one module-level output root, set once here
    OUT = args.out_dir
    OUT.mkdir(parents=True, exist_ok=True)
    return {"draft": cmd_draft, "grade": cmd_grade, "judge": cmd_judge}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
