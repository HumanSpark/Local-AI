# File: run_h6_date_arm.py
# Purpose: the H6 arm - run a graded question set with and without a deterministic date tool, and account for BOTH directions.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: H6 says delegating deterministic subproblems to deterministic tools
# improves reliability more cheaply than more model reasoning. Its falsifier
# (R&D programme, AMENDMENT 2) is two-sided, so this runner is too: it counts
# conversions AND new failures, and refuses to report either alone.
#
# THE DESIGN CONSTRAINT THAT MAKES IT A TEST RATHER THAN A DEMO. date_calc.py
# offers only add_period / last_day_of_month / date_diff. It has no helper that
# knows what a limitation period is. The model must still choose the anchor date,
# the number of months and whether a last-day-of-month step applies. So a wrong
# answer WITH a correct tool call is a real and expected outcome - and it is the
# one F92 predicts for P3, where both models read STAT-LIM's "corresponding day"
# as anchored on the period START (15 Sept 2020) rather than the ACCRUAL date.
#
# WHY ARGUMENTS ARE RECORDED, NOT JUST OUTCOMES. "The model called the tool" is
# not evidence the tool helped. The four failure classes below are only
# separable if the call arguments and the returned values are kept, so they are.
from __future__ import annotations

import argparse
import json
import random
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))

from date_calc import SCHEMAS, TOOL_SCHEMA, dispatch  # noqa: E402
from tool_router import (  # noqa: E402
    ROUTER_VERSION,
    fixed_router,
    model_router,
    rule_router,
)
from run_ps_eval import (  # noqa: E402
    DEFAULT_SERVER,
    PROMPT_TEMPLATE,
    TIERS,
    assert_full_offload,
    wait_healthy,
)

from corpus_l4 import build_pack_l4  # noqa: E402
from grade_multiturn import grade_multiturn  # noqa: E402
from questions import parse_response  # noqa: E402
from questions_l4 import QUESTIONS_L4, _dates  # noqa: E402

# The six questions whose answer is a DATE. Every one is "read the rule, then
# count" - which is exactly the split H6 is about.
DATE_IDS = ("P1", "P2", "P3", "B1", "N1", "N2")

# PROMPT_TEMPLATE and the tier table come from run_ps_eval so this arm cannot
# drift from the runs it is compared against. The local copy was verified
# byte-identical before deletion.

# Appended ONLY in the tool condition. It says the tool exists and says nothing
# about which dates or periods to use - naming those would be doing the legal
# reasoning for the model and would answer H6 by construction.
TOOL_PREAMBLE = """\

You have date-arithmetic tools available. Use them for any counting of days, \
months, years or hours rather than calculating by hand. You must still decide \
from the pack which date to count from and what period applies.
"""


def _post(base_url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    import urllib.request

    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _parse_args_blob(raw: Any) -> dict[str, Any] | None:
    """Tool arguments arrive as a dict or a JSON string depending on the model."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


def ask_one(
    base_url: str,
    prompt: str,
    *,
    use_tools: bool,
    max_tokens: int,
    timeout: float,
    max_rounds: int,
    tool_schema: list[dict[str, Any]] | None = None,
    thinking: str = "default",
) -> dict[str, Any]:
    """One question, running the tool loop to completion. Returns the transcript.

    `tool_schema` defaults to the frozen V1 set so every E67/E68 invocation
    keeps the exact configuration its banked result is attributed to (Rule 8).
    """
    messages: list[dict[str, Any]] = [{"role": "user", "content": prompt}]
    calls: list[dict[str, Any]] = []
    t0 = time.time()
    content = ""

    for _ in range(max_rounds):
        payload: dict[str, Any] = {
            "model": "x",
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
        }
        # Same mechanism as run_ps_eval.ask(). `default` is NOT neutral on
        # Qwen3.8 - its chat template resolves reasoning_effort to xhigh, which
        # F71 measured burning 100,000 tokens over 2h46m and returning nothing.
        # Any arm on that model must declare a setting.
        if thinking == "off":
            payload["chat_template_kwargs"] = {"enable_thinking": False}
        elif thinking in ("low", "medium", "xhigh"):
            payload["reasoning_effort"] = thinking
        elif thinking != "default":
            raise ValueError(
                f"unknown thinking mode {thinking!r}\n"
                f"hint: one of default, off, low, medium, xhigh - and `default` "
                f"is the MAXIMUM setting on Qwen3.8, not a neutral one"
            )
        if use_tools:
            payload["tools"] = tool_schema if tool_schema is not None else TOOL_SCHEMA
        msg = _post(base_url, payload, timeout)["choices"][0]["message"]
        content = msg.get("content") or ""
        tcs = msg.get("tool_calls") or []
        messages.append({"role": "assistant", "content": content, "tool_calls": tcs})
        if not tcs:
            break
        for tc in tcs:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            args = _parse_args_blob(fn.get("arguments"))
            record: dict[str, Any] = {"name": name, "arguments": args}
            if args is None:
                record["error"] = "arguments were not parseable JSON"
                result = "ERROR: arguments were not valid JSON"
            else:
                try:
                    value = dispatch(name, args)
                    record["result"] = value
                    result = str(value)
                except ValueError as exc:
                    # The tool raising is DATA, not a run failure: a model that
                    # asks for 72 hours from a bare date has made a real error
                    # and the arm must see it rather than crash.
                    record["error"] = str(exc)
                    result = f"ERROR: {exc}"
            calls.append(record)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "name": name,
                    "content": result,
                }
            )

    return {
        "content": content,
        "calls": calls,
        "wall_s": round(time.time() - t0, 2),
        "rounds": len([m for m in messages if m["role"] == "assistant"]),
    }


def classify(outcome: str, answer: str | None, calls: list[dict]) -> str:
    """Which of H6's failure classes this cell belongs to.

    Mechanical, and deliberately separates 'called the tool and still got it
    wrong' from 'ignored what the tool said' - they have opposite fixes.
    """
    made_call = bool(calls)
    if outcome == "correct":
        return "correct_with_tool" if made_call else "correct_without_tool"
    if not made_call:
        return "no_call"
    if any(c.get("error") for c in calls):
        return "tool_error"
    # Compare PARSED DATES, not substrings. The model answers in prose ("30
    # September 2026") while the tool returns ISO ("2026-09-30"), so a substring
    # test silently reports result_ignored for every obeyed call - which inverts
    # the diagnosis, because wrong_args and result_ignored have opposite fixes.
    # `_dates` is the grader's own parser and already handles both forms.
    answered = set(_dates(answer or ""))
    returned: set = set()
    for c in calls:
        value = c.get("result")
        if isinstance(value, str):
            returned |= set(_dates(value))
    if answered & returned:
        return "wrong_args"
    return "result_ignored"


def main() -> int:
    ap = argparse.ArgumentParser(
        description="H6: do deterministic date tools convert the known arithmetic failures?",
        epilog="examples:\n"
        "  %(prog)s --model /opt/models/staging/X.gguf --label h6-control --tools off \\\n"
        "      --out results/raw/h6-control.json\n"
        "  %(prog)s --model /opt/models/staging/X.gguf --label h6-tools --tools on \\\n"
        "      --out results/raw/h6-tools.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--model", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--tools",
        choices=["on", "off", "preamble-only", "routed"],
        required=True,
        help=(
            "on = preamble + tools in the payload; off = neither; "
            "preamble-only = the preamble WITHOUT the tools field, which "
            "separates 'the tool did it' from 'the prompt change did it' when "
            "a cell regresses without any call being made; "
            "routed = a per-question decision from --router, which is E80's "
            "question - E79 measured the tool as +3 on one band and -5 on the "
            "other, so whether it pays depends entirely on aiming it"
        ),
    )
    ap.add_argument(
        "--base-url",
        default=None,
        help="use an already-running server instead of launching one",
    )
    ap.add_argument("--server-bin", default=DEFAULT_SERVER)
    ap.add_argument("--server-extra", default="")
    ap.add_argument("--ctx", type=int, default=32768)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--port", type=int, default=8113)
    ap.add_argument("--load-timeout", type=float, default=600.0)
    ap.add_argument("--request-timeout", type=float, default=900.0)
    ap.add_argument("--max-rounds", type=int, default=6)
    ap.add_argument(
        "--tier",
        default="l4-date",
        choices=["l4-date", "l1", "l2", "l3", "l5"],
        help=(
            "l4-date = the six L4 date questions the tool is FOR (E67). "
            "l1/l2/l3 = a ps-eval tier the date tool is IRRELEVANT to, which "
            "turns the same runner into an interference test: any change there "
            "is the cost of OFFERING a tool, not of using one"
        ),
    )
    ap.add_argument(
        "--distractors",
        type=int,
        default=None,
        help="l3 only - distractor count, as in run_ps_eval",
    )
    ap.add_argument(
        "--schema-version",
        default="v1",
        choices=sorted(SCHEMAS),
        help=(
            "v1 = the three date primitives E67 and E68 were measured against, "
            "and the DEFAULT so those invocations are unchanged; v2 adds "
            "add_business_days, roll_to_business_day and weekday, which a bank "
            "whose periods are counted in Business Days against a holiday list "
            "needs before the tool can reach them at all"
        ),
    )
    ap.add_argument(
        "--router",
        default="rule",
        choices=["rule", "model", "fixed"],
        help="only with --tools routed. rule = deterministic patterns, no "
             "inference. model = one YES/NO call per question, which is the "
             "DEPLOYABLE router and is fitted to nothing. fixed = replay a "
             "decision map from --router-decisions, making no call at all - the "
             "control that isolates router traffic on the answering slot.",
    )
    ap.add_argument(
        "--router-base-url",
        default=None,
        help="only with --router model. Route using a DIFFERENT server than the "
             "one answering - the plan's H18 specialist-small-model arm. "
             "Defaults to the answering server.",
    )
    ap.add_argument(
        "--order",
        default="bank",
        choices=["bank", "reverse", "shuffle"],
        help="item order. E81 measured order as a LIVE VARIABLE in the "
             "multi-round tool loop: reverse changed two answers' text "
             "deterministically. `shuffle` needs --order-seed and is how the "
             "size of that effect gets bounded rather than asserted.",
    )
    ap.add_argument(
        "--order-seed",
        type=int,
        default=None,
        help="required with --order shuffle. The permutation is derived from "
             "this seed alone and is recorded in the output, so any run in the "
             "study can be reproduced exactly from its result file.",
    )
    ap.add_argument(
        "--interleave-dummy",
        action="store_true",
        help="before each item, issue the ROUTER-SHAPED request and DISCARD its "
             "answer. It shares no prefix with the pack, so it displaces the "
             "cached pack prefix without changing any routing decision. This "
             "isolates prefix displacement from the routing itself.",
    )
    ap.add_argument(
        "--router-decisions",
        default=None,
        help="only with --router fixed. JSON {question_id: bool} recorded from an "
             "earlier arm's per-item routing.offer_tool.",
    )
    ap.add_argument(
        "--router-thinking",
        default="off",
        choices=["default", "off", "low", "medium", "xhigh"],
        help="reasoning budget for the ROUTER call. Defaults to off: a router "
             "that thinks for 40 seconds costs more than the answer it is "
             "routing, which is the trap E75 found in disagreement-routing.",
    )
    ap.add_argument(
        "--thinking",
        default="default",
        choices=["default", "off", "low", "medium", "xhigh"],
        help="reasoning budget. `default` is NOT neutral on Qwen3.8 - its "
             "template resolves to xhigh (F71). Declare a setting on that model.",
    )
    ap.add_argument(
        "--allow-busy-gpu",
        action="store_true",
        help="proceed even though another llama-server holds the GPU. ONLY for a "
             "run whose pre-registration already declares every wall time VOID "
             "(Rule 9); the breach and the pids are recorded in the output.",
    )
    ap.add_argument("--only", default=None, help="comma-separated question ids")
    args = ap.parse_args()

    if args.tier == "l4-date":
        bank, grade = QUESTIONS_L4, grade_multiturn
        pack = build_pack_l4()
        default_ids = DATE_IDS
    else:
        tier = TIERS[args.tier]
        bank, grade = tier["questions"], tier["grade"]
        pack = tier["pack"](args.distractors) if args.tier == "l3" else tier["pack"]()
        default_ids = tuple(q["id"] for q in bank)

    ids = tuple(x.strip() for x in args.only.split(",")) if args.only else default_ids
    questions = [q for q in bank if q["id"] in ids]
    if args.order == "reverse":
        questions = list(reversed(questions))
    elif args.order == "shuffle":
        if args.order_seed is None:
            raise SystemExit(
                "--order shuffle needs --order-seed\n"
                "hint: an unseeded shuffle cannot be reproduced, and an order "
                "that cannot be reproduced cannot be a configuration"
            )
        random.Random(args.order_seed).shuffle(questions)
    missing = set(ids) - {q["id"] for q in questions}
    if missing:
        raise SystemExit(
            f"unknown question ids {sorted(missing)} for tier {args.tier}. "
            f"hint: this tier's bank is {list(default_ids)}"
        )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = out_path.with_suffix(".serverlog")

    proc = log_f = None
    base_url = args.base_url
    print(f"=== H6 date arm: {args.label}  tools={args.tools} ===")
    print(
        f"pack {len(pack):,} chars, {len(questions)} questions: {[q['id'] for q in questions]}"
    )

    busy_gpu: list[dict] = []
    if base_url is None:
        for name in ("llama-server", "llama-bench"):
            r = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
            if r.stdout.strip():
                if not args.allow_busy_gpu:
                    raise SystemExit(
                        f"FAIL: {name} already running (pids {r.stdout.split()}). "
                        f"hint: a busy GPU voids this run's timings. If the run's "
                        f"timings are ALREADY declared void, --allow-busy-gpu "
                        f"proceeds and records the breach in the output"
                    )
                # Same semantics as run_ps_eval.py's flag, deliberately. The
                # DEFAULT still refuses; this is for a run whose pre-registration
                # has already declared every wall time void because the account
                # cannot take the bench window. NOT added to soak_load.py,
                # latency_matrix.py, smoke_first_token.py or bisect_hang.py -
                # those exist to MEASURE timing, so a bypass there would let a
                # contended number be reported as a clean one. Ten other copies
                # of this guard were left alone.
                busy_gpu.append({"process": name, "pids": r.stdout.split()})
                print(
                    f"WARNING: {name} running (pids {r.stdout.split()}) and "
                    f"--allow-busy-gpu was passed. EVERY TIMING IN THIS RUN IS "
                    f"VOID (Rule 9). Correctness is not a contended quantity.",
                    file=sys.stderr,
                )
        cmd = [
            args.server_bin,
            "-m",
            args.model,
            "-c",
            str(args.ctx),
            "-np",
            "1",
            "--host",
            "127.0.0.1",
            "--port",
            str(args.port),
            "--no-webui",
            "-v",
            "--jinja",
        ]
        cmd += shlex.split(args.server_extra)
        print(f"server: {' '.join(cmd)}")
        log_f = log_path.open("w")
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
        base_url = f"http://127.0.0.1:{args.port}"

    results: list[dict] = []
    started = time.time()
    try:
        if proc is not None:
            wait_healthy(args.port, args.load_timeout)
            gate = assert_full_offload(log_path)
            print(f"full-offload gate: {gate}")
        else:
            gate = {"skipped": "external server - offload not gated by this run"}

        router_url = args.router_base_url or base_url
        fixed_decisions: dict[str, bool] = {}
        if args.router == "fixed" and args.tools == "routed":
            if not args.router_decisions:
                raise SystemExit(
                    "--router fixed needs --router-decisions\n"
                    "hint: a JSON map {question_id: bool} from an earlier arm's "
                    "per-item routing.offer_tool"
                )
            fixed_decisions = json.loads(Path(args.router_decisions).read_text())
        for i, q in enumerate(questions, 1):
            # The routing decision is made from the QUESTION ALONE, before the
            # pack is assembled. A router that had to read the record to decide
            # would cost about what answering costs, which is the trap E75 found
            # when disagreement-routing turned out not to be cheaper than the
            # work it routed.
            routing = None
            if args.tools == "routed":
                if args.router == "rule":
                    routing = rule_router(q["question"])
                elif args.router == "fixed":
                    routing = fixed_router(q["id"], fixed_decisions)
                else:
                    routing = model_router(
                        q["question"], router_url,
                        timeout=args.request_timeout,
                        thinking=args.router_thinking,
                    )
            offer = routing["offer_tool"] if routing is not None else (args.tools == "on")

            if args.interleave_dummy:
                # Fire the router-shaped request and throw the answer away. It
                # carries no pack, so it shares no prefix with the answering
                # prompt and displaces what the slot had cached. Nothing about
                # the routing decision changes - `routing` above is already
                # fixed - so anything that moves is displacement alone.
                try:
                    model_router(q["question"], base_url,
                                 timeout=args.request_timeout,
                                 thinking=args.router_thinking)
                except Exception as exc:  # noqa: BLE001 - the dummy must not kill the run
                    print(f"  dummy request failed on {q['id']}: {exc}")

            prompt = PROMPT_TEMPLATE.format(pack=pack, question=q["question"])
            if args.tools in ("on", "preamble-only") or offer:
                prompt += TOOL_PREAMBLE
            try:
                resp = ask_one(
                    base_url,
                    prompt,
                    use_tools=offer,
                    max_tokens=args.max_tokens,
                    timeout=args.request_timeout,
                    max_rounds=args.max_rounds,
                    tool_schema=SCHEMAS[args.schema_version],
                    thinking=args.thinking,
                )
            except Exception as exc:  # noqa: BLE001 - one question must not kill the run
                results.append(
                    {
                        "id": q["id"],
                        "outcome": "transport_failed",
                        "detail": str(exc),
                        "calls": [],
                        "class": "transport_failed",
                        "routing": routing,
                    }
                )
                print(f"  [{i}/{len(questions)}] {q['id']:3s} transport_failed: {exc}")
                continue
            answer, citation = parse_response(resp["content"])
            outcome = grade(q, answer)
            klass = classify(outcome, answer, resp["calls"])
            results.append(
                {
                    "id": q["id"],
                    "category": q.get("category"),
                    "outcome": outcome,
                    "class": klass,
                    "answer": answer,
                    "citation": citation,
                    "expected": str(q["expect"].get("want")),
                    "n_calls": len(resp["calls"]),
                    "calls": resp["calls"],
                    "rounds": resp["rounds"],
                    "wall_s": resp["wall_s"],
                    "routing": routing,
                }
            )
            call_note = (
                ", ".join(
                    f"{c['name']}({json.dumps(c.get('arguments'))})->{c.get('result', c.get('error', ''))}"
                    for c in resp["calls"]
                )
                or "-"
            )
            print(
                f"  [{i}/{len(questions)}] {q['id']:3s} {outcome:17s} {klass:20s} "
                f"ans={str(answer)[:24]:24s} {call_note[:110]}"
            )
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
            if log_f:
                log_f.close()

    classes: dict[str, int] = {}
    for r in results:
        classes[r["class"]] = classes.get(r["class"], 0) + 1
    summary = {
        "label": args.label,
        "tools": args.tools,
        # WHICH tool set, not just whether tools were on. V1 and V2 are
        # different configurations and a result attributed to "tools on" without
        # naming the schema cannot be compared to E67's (Rule 8, F39).
        "schema_version": args.schema_version if args.tools in ("on", "routed") else None,
        "router": args.router if args.tools == "routed" else None,
        "router_version": ROUTER_VERSION if args.tools == "routed" else None,
        "router_base_url": args.router_base_url if args.tools == "routed" else None,
        "router_thinking": args.router_thinking if args.tools == "routed" else None,
        "router_decisions": args.router_decisions if args.router == "fixed" else None,
        "order": args.order,
        "order_seed": args.order_seed,
        "order_ids": [q["id"] for q in questions],
        "interleave_dummy": args.interleave_dummy,
        "thinking": args.thinking,
        "rule9_breach_acknowledged": bool(busy_gpu),
        "rule9_busy_gpu": busy_gpu,
        "n_tools_offered": len(SCHEMAS[args.schema_version]) if args.tools == "on" else 0,
        "model": args.model,
        "tier": args.tier,
        "distractors": args.distractors,
        "ctx": args.ctx,
        "max_tokens": args.max_tokens,
        "max_rounds": args.max_rounds,
        "server_extra": args.server_extra,
        "pack_chars": len(pack),
        "question_ids": list(ids),
        "full_offload_gate": gate,
        "correct": sum(1 for r in results if r["outcome"] == "correct"),
        "total": len(results),
        "outcome_counts": {
            o: sum(1 for r in results if r["outcome"] == o)
            for o in sorted({r["outcome"] for r in results})
        },
        "class_counts": classes,
        "total_tool_calls": sum(r.get("n_calls", 0) for r in results),
        "wall_s": round(time.time() - started, 2),
        "results": results,
    }
    out_path.write_text(json.dumps(summary, indent=2))
    print(
        f"\n{summary['correct']}/{summary['total']} correct   "
        f"classes: {json.dumps(classes)}   calls: {summary['total_tool_calls']}"
    )
    print(f"written {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
