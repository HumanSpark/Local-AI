#!/usr/bin/env python3
# File: tools/production_probe.py
# Purpose: Nightly check that production (Halogen solo, through model-guard) is still as fast and as correct as it was.
# Project: sparkbench | Date: 2026-11-08
#
# Overview: Owner ask 2026-11-08: keep an eye on tok/s and output quality of the live service without touching it.
# Sends three fixed requests through the guard (127.0.0.1:8402) exactly as a client would - no restarts, no config:
#   prose  - local_smart, ~300-word explanation; pass = finished and ends with the DONE marker
#   code   - local_code, writes merge_intervals(); pass = the function passes 6 asserts run in a subprocess
#   needle - local_smart, ~30K-token synthetic record list (re-seeded EVERY run, retries included, so no prefix cache can serve it); pass =
#            exact record code returned. This is the prefill measurement.
#   tmpl_tool / tmpl_twin - E175's gbench chat-template pair (results/e175/cases, Apache-2.0): a prebuilt conversation
#            whose tool turn carries tracking code QX7R2M, and its plain-text twin. pass = QX7R2M and "delayed" in the
#            answer and none of production's template control strings (LEAKS, from the served froggeric v22.5 template).
#            tool FAIL + twin pass = the TEMPLATE dropped the tool result (E175/F200), noted on the tool row.
# Speed comes from the engine's own `timings` block (decode = predicted_per_second, prefill = prompt_per_second).
# A probe is FLAGGED when it fails its check or decodes >10% below the median of its last 14 good runs; a flagged
# probe is retried once after 5 min so a busy client is not reported as a regression. Appends one row per probe to
# results/production-probe/probe.csv, writes latest.txt, and exits 1 when anything stayed flagged so the timer's
# unit shows failed. Skips (exit 0, row recorded) when the guard is not "serving" - a bench window or vision pause.
# No alert is SENT: outbound mail is approved for the monthly capability key only.
#
# Usage: tools/production_probe.py [--dry-run] [--only prose,code,needle,tmpl_tool,tmpl_twin]
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import random
import re
import statistics
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "results" / "production-probe"
CSV_PATH = OUT / "probe.csv"
GUARD = "http://127.0.0.1:8402"
DROP = 0.90  # flag below 90% of the rolling median
HISTORY = 14
RETRY_WAIT_S = 300
FIELDS = [
    "utc",
    "probe",
    "status",
    "check",
    "model_name",
    "served",
    "decode_tps",
    "prefill_tps",
    "prompt_n",
    "predicted_n",
    "draft_accept",
    "cache_n",
    "wall_s",
    "baseline_decode",
    "kernel",
    "note",
]

PROSE = (
    "In about 300 words, explain to a small-business owner why keeping customer data on a local server "
    "rather than a cloud service can matter for privacy. Plain prose, no headings. "
    "End your answer with a final line containing only the word DONE."
)
CODE = (
    "Write a Python function merge_intervals(intervals) that takes a list of [start, end] integer pairs "
    "(possibly unsorted, possibly overlapping or touching) and returns a new list of merged [start, end] pairs "
    "sorted by start. Intervals that touch, like [1,2] and [2,3], merge. Reply with one ```python code block only."
)
CODE_TESTS = """
assert merge_intervals([]) == []
assert merge_intervals([[1,3],[2,6],[8,10],[15,18]]) == [[1,6],[8,10],[15,18]]
assert merge_intervals([[1,4],[4,5]]) == [[1,5]]
assert merge_intervals([[5,7],[1,2]]) == [[1,2],[5,7]]
assert merge_intervals([[1,10],[2,3],[4,5]]) == [[1,10]]
assert merge_intervals([[3,3]]) == [[3,3]]
print("PASS")
"""


TMPL_CASES = REPO / "results" / "e175" / "cases"
# Control strings of the SERVED template (/opt/sparkrouter/templates/qwen38-flash-next-froggeric-v22.5.jinja, since
# 2026-11-13) plus gbench's two plain strings. Any of them in the answer content = a template leak.
LEAKS = (
    "<|im_start|>",
    "<|im_end|>",
    "<|think_",
    "<tool_call>",
    "</tool_call>",
    "<tool_response>",
    "</tool_response>",
    "<tools>",
    "<function=",
    "</parameter>",
    "<think>",
    "</think>",
    "tool_call_id",
)


def tmpl_case(name: str) -> dict:
    """Load one gbench case; a missing or reshaped file is a harness error, never a skipped probe."""
    case = json.loads((TMPL_CASES / f"{name}.json").read_text())
    _ = case["conversation"]["messages"], case["golden_truth"]["expected_outputs"]
    return case


def needle_prompt(day: str) -> tuple[str, str]:
    """~30K tokens of records seeded per run: a same-day seed let the prefix cache serve 59,648 of 59,695 tokens (2026-11-08)."""
    rng = random.Random(day)
    colours = ["red", "teal", "amber", "violet", "slate", "olive", "coral", "ivory"]
    alnum = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    lines, codes = [], []
    for i in range(1, 1101):
        code = (
            "".join(rng.choice(alnum) for _ in range(3))
            + "-"
            + "".join(rng.choice(alnum) for _ in range(4))
        )
        codes.append(code)
        lines.append(
            f"Record {i:04d}: colour={rng.choice(colours)}, weight={rng.randint(10, 999)}kg, code={code}"
        )
    target = rng.randint(100, 1000)
    prompt = (
        "Here is a list of records.\n\n"
        + "\n".join(lines)
        + f"\n\nWhat is the code of Record {target:04d}? "
        "Reply with the code only."
    )
    return prompt, codes[target - 1]


def http_json(url: str, body: dict | None, timeout: float) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def chat(
    model: str,
    prompt: str,
    max_tokens: int,
    messages: list | None = None,
    extra: dict | None = None,
) -> tuple[dict, float]:
    t0 = time.monotonic()
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0,
        # Pinned (2026-11-13): production's default effort became low (sparkrouter halogen_effort.sh, F186/F187),
        # which shrank the prose answer from ~2,155 to ~450 tokens and its decode rate with it. This probe measures
        # the ENGINE against baselines recorded at xhigh, so it asks for xhigh explicitly (F39/Rule 8: a benchmark
        # measures a config - name it).
        "reasoning_effort": "xhigh",
        "messages": messages or [{"role": "user", "content": prompt}],
    }
    body.update(extra or {})
    r = http_json(f"{GUARD}/v1/chat/completions", body, timeout=900)
    return r, time.monotonic() - t0


def check_code(content: str) -> tuple[bool, str]:
    m = re.search(r"```(?:python)?\n(.*?)```", content, re.S)
    if not m:
        return False, "no python code block"
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "t.py"
        f.write_text(m.group(1) + "\n" + CODE_TESTS)
        try:
            p = subprocess.run(
                [sys.executable, "-I", str(f)],
                cwd=d,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            return False, "tests timed out after 20 s"
    if p.returncode == 0 and "PASS" in p.stdout:
        return True, ""
    return False, (p.stderr.strip().splitlines() or ["no output"])[-1][:120]


def run_probe(name: str, day: str) -> dict:
    if name == "prose":
        r, wall = chat("local_smart", PROSE, 3000)
    elif name == "code":
        r, wall = chat("local_code", CODE, 4000)
    elif name in ("tmpl_tool", "tmpl_twin"):
        case = tmpl_case(
            "template_tool_response"
            if name == "tmpl_tool"
            else "template_tool_response_twin"
        )
        extra = {k: case[k] for k in ("tools", "tool_choice") if k in case}
        r, wall = chat(
            "local_smart",
            "",
            3000,
            messages=case["conversation"]["messages"],
            extra=extra,
        )
    else:
        prompt, expect = needle_prompt(f"{day}-{time.time_ns()}")
        r, wall = chat("local_smart", prompt, 2000)
    choice = r["choices"][0]
    content = choice["message"]["content"] or ""
    t = r[
        "timings"
    ]  # KeyError here means the engine changed its response shape - surface it, do not guess
    if name == "prose":
        ok = choice["finish_reason"] == "stop" and content.strip().endswith("DONE")
        note = (
            ""
            if ok
            else f"finish={choice['finish_reason']}, ends {content.strip()[-30:]!r}"
        )
    elif name == "code":
        ok, note = check_code(content)
    elif name in ("tmpl_tool", "tmpl_twin"):
        missing = [w for w in ("QX7R2M", "delayed") if w.lower() not in content.lower()]
        leaked = [w for w in LEAKS if w in content]
        called = bool(choice["message"].get("tool_calls"))
        ok = not missing and not leaked and not called
        note = (
            ""
            if ok
            else f"missing {missing} leaked {leaked} tool_call={called} finish={choice['finish_reason']}"
        )
    else:
        ok = expect in content and len(content.strip()) < 40
        note = "" if ok else f"expected {expect}, got {content.strip()[:40]!r}"
    drafted = t.get("draft_n") or 0  # optional: absent when speculation is off
    return {
        "check": "pass" if ok else "FAIL",
        "served": r["model"],
        "decode_tps": round(t["predicted_per_second"], 1),
        "prefill_tps": round(t["prompt_per_second"], 1),
        "prompt_n": t["prompt_n"],
        "predicted_n": t["predicted_n"],
        "draft_accept": round(t["draft_n_accepted"] / drafted, 3) if drafted else "",
        "cache_n": t.get("cache_n", ""),
        "wall_s": round(wall, 1),
        "note": note,
    }


def baseline(probe: str) -> float | None:
    if not CSV_PATH.exists():
        return None
    with CSV_PATH.open() as f:
        rows = [
            r
            for r in csv.DictReader(f)
            if r["probe"] == probe and r["status"] == "ok" and r["check"] == "pass"
        ]
    vals = [float(r["decode_tps"]) for r in rows[-HISTORY:]]
    return statistics.median(vals) if vals else None


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Probe production speed and correctness through model-guard; one CSV row per probe.",
        epilog="examples:\n  tools/production_probe.py\n  tools/production_probe.py --dry-run --only code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="run the probes and print, but write nothing",
    )
    ap.add_argument(
        "--only",
        default="prose,code,needle,tmpl_tool,tmpl_twin",
        help="comma list of probes (default: all five)",
    )
    a = ap.parse_args()
    probes = a.only.split(",")
    utc = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    day = utc[:10]
    kernel = subprocess.run(
        ["uname", "-r"], capture_output=True, text=True, check=True
    ).stdout.strip()
    rows: list[dict] = []
    base = {"utc": utc, "kernel": kernel}

    try:
        health = http_json(f"{GUARD}/health", None, timeout=10)
        state = health["state"]
    except (OSError, KeyError, json.JSONDecodeError) as e:
        state = f"unreachable: {e}"
    if state != "serving":
        print(f"[probe] guard not serving ({state}); recording skip")
        rows = [
            dict(base, probe=p, status="skipped", note=str(state)[:120]) for p in probes
        ]
    else:
        for p in probes:
            bl = baseline(p)
            print(
                f"[probe] {p}: running (baseline decode {bl or 'none yet'})", flush=True
            )
            res = run_probe(p, day)
            flagged = res["check"] == "FAIL" or (
                bl is not None and res["decode_tps"] < DROP * bl
            )
            if flagged:
                print(
                    f"[probe] {p}: flagged ({res}); retrying once in {RETRY_WAIT_S} s",
                    flush=True,
                )
                if not a.dry_run:
                    time.sleep(RETRY_WAIT_S)
                res2 = run_probe(p, day)
                res2["note"] = (
                    f"retry; first: {res['decode_tps']} tok/s {res['check']} "
                    + res2["note"]
                ).strip()
                res = res2
                flagged = res["check"] == "FAIL" or (
                    bl is not None and res["decode_tps"] < DROP * bl
                )
            status = "FLAGGED" if flagged else "ok"
            print(
                f"[probe] {p}: {status} decode {res['decode_tps']} prefill {res['prefill_tps']} "
                f"check {res['check']} wall {res['wall_s']} s {res['note']}",
                flush=True,
            )
            rows.append(
                dict(
                    base,
                    probe=p,
                    status=status,
                    model_name=p,
                    baseline_decode=bl or "",
                    **res,
                )
            )

    by = {r["probe"]: r for r in rows}
    if (
        by.get("tmpl_tool", {}).get("check") == "FAIL"
        and by.get("tmpl_twin", {}).get("check") == "pass"
    ):
        by["tmpl_tool"]["note"] = (
            "TEMPLATE suspect: twin passed, tool turn lost (E175). "
            + by["tmpl_tool"]["note"]
        ).strip()
    if a.dry_run:
        # Bench runners call --dry-run as their "relay restored" gate, so a skip or a failed check must not exit 0
        # (until 2026-11-23 it did, and every runner logged VERIFIED on a 503 skip).
        bad = [f"{r['probe']}={r['status']}" for r in rows if r["status"] != "ok"]
        if bad:
            print(f"[probe] dry-run NOT ok: {', '.join(bad)}", flush=True)
            return 1
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    new = not CSV_PATH.exists()
    with CSV_PATH.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, restval="")
        if new:
            w.writeheader()
        w.writerows(rows)
    flagged = [r for r in rows if r["status"] == "FLAGGED"]
    summary = "\n".join(
        f"{r['utc']} {r['probe']:6} {r['status']:8} decode={r.get('decode_tps', '')} prefill={r.get('prefill_tps', '')} "
        f"check={r.get('check', '')} {r.get('note', '')}"
        for r in rows
    )
    (OUT / "latest.txt").write_text(summary + "\n")
    return 1 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())
