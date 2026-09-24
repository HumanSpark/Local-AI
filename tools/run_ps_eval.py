#!/usr/bin/env python3
# File: run_ps_eval.py
# Purpose: Run the professional-services knowledge-work eval against a served or cloud model, graded objectively.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: Asks each question in spikes/ps-eval/questions.py against the
# seeded engagement pack in corpus.py, one request per question, and grades
# by string and numeric matching - no LLM judge anywhere in the loop. Mirrors
# run_coding_eval.py: Rule 1 HTTP-only serving, Rule 2 timeouts on every
# subprocess and HTTP call, Rule 3 full-offload gate asserted from the
# verbose server log and FAILING on zero evidence, Rule 9 quiet-GPU check on
# the local path only.
#
# ONE REQUEST PER QUESTION, pack resent each time. Batching all twenty into
# one context would let an answer to Q7 leak into Q12 and would measure
# something other than the task a firm actually runs.
#
# THE HEADLINE METRIC IS over_claim_rate, not accuracy. In professional
# services a confident fabrication is a liability event while "not in the
# pack" is a correct and billable answer, so the eval reports the unanswerable
# items separately and prominently rather than averaging them away.
#
# `stale_value` is likewise its own outcome: answering a supersession item
# with the pre-amendment figure is a specific, expensive failure and must not
# be folded into a generic "wrong".

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "spikes" / "ps-eval"))
from corpus import build_pack  # noqa: E402
from corpus_l2 import build_pack_l2  # noqa: E402
from corpus_l3 import build_pack_l3  # noqa: E402
from questions import (  # noqa: E402
    CATEGORIES,
    QUESTIONS,
    grade_answer,
    grade_citation,
    parse_response,
)
from questions_l2 import CATEGORIES_L2, QUESTIONS_L2, grade_answer_l2  # noqa: E402
from questions_l3 import CATEGORIES_L3, QUESTIONS_L3, grade_answer_l3  # noqa: E402
from corpus_l4 import build_pack_l4  # noqa: E402
from questions_l4 import CATEGORIES_L4, QUESTIONS_L4, grade_answer_l4  # noqa: E402
from corpus_pr1 import build_pack_pr1  # noqa: E402
from questions_pr1 import (  # noqa: E402
    CATEGORIES_PR1,
    PROMPT_TEMPLATE_PR1,
    QUESTIONS_PR1,
    grade_answer_pr1,
)
from corpus_l5 import build_pack_l5  # noqa: E402
from questions_l5 import CATEGORIES_L5, QUESTIONS_L5, grade_answer_l5  # noqa: E402

from bench_context import assert_context_fits, count_tokens  # noqa: E402,F401

# Which pack, questions and grader each tier uses, and which categories carry
# the two headline metrics. L1 and L2 measure the same two liabilities under
# different category names: inventing an answer that is not supported, and
# using a figure that some later document displaced.
#
#   over_claim  L1 `unanswerable` (the subject is absent)
#               L2 `underspecified` (the subject is present, the attribute is
#               not - a harder decline, because adjacent text makes a
#               confident answer feel supported)
#   stale       L1 `supersession`
#               L2 `date_effective` + `revocation`, which also carry the
#               INVERSE error (`premature`) that L1 could not produce
TIERS: dict[str, dict] = {
    "l1": {
        "pack": build_pack, "questions": QUESTIONS, "grade": grade_answer,
        "categories": CATEGORIES,
        "over_claim_from": ["unanswerable"], "stale_from": ["supersession"],
    },
    "l2": {
        "pack": build_pack_l2, "questions": QUESTIONS_L2, "grade": grade_answer_l2,
        "categories": CATEGORIES_L2,
        "over_claim_from": ["underspecified"],
        "stale_from": ["date_effective", "revocation"],
    },
    # l3 is l2's questions in a bigger haystack. Its pack builder takes the
    # distractor count, so it is the one tier whose pack is parameterised.
    "l3": {
        "pack": build_pack_l3, "questions": QUESTIONS_L3, "grade": grade_answer_l3,
        "categories": CATEGORIES_L3,
        "over_claim_from": ["underspecified"],
        "stale_from": ["date_effective", "revocation"],
    },
    # l4 changes the DOMAIN rather than continuing the ladder - statutory
    # periods, engagement terms and "what is wrong with this contract" - so
    # its totals are not comparable to l1-l3 and its entry says so. It has no
    # supersession category at all, hence the empty stale_from: nothing in
    # this pack is displaced by a later document. Its headline number is the
    # `off_by_calendar` count, which the runner reports through
    # outcome_counts rather than through a dedicated field.
    "l4": {
        "pack": build_pack_l4, "questions": QUESTIONS_L4, "grade": grade_answer_l4,
        "categories": CATEGORIES_L4,
        "over_claim_from": ["underspecified"],
        "stale_from": [],
    },
    # l5 splits its difficulty into two BANDS carried on each item, so an
    # intervention can be scored against the band it should move: R is
    # reasoning-limited with the evidence handed over, E is evidence-limited
    # with the reasoning trivial. Totals across the whole tier are far less
    # informative than the two band scores, and results/experiments.md says so.
    # Gated by tools/validate_ps_eval_l5.py, which must pass before any run.
    # pr1 asks whether the model will FLAG a request a competent adviser must
    # not simply carry out. It is NOT a retrieval tier - the pack is ~700 tokens
    # by design, because a long pack would confound refusal with retrieval.
    #
    # Its over_claim_from is EMPTY on purpose. pr1's failure vocabulary is its
    # own (missed_flag / over_flag), scored by questions_pr1.grade_answer_pr1
    # against a required verdict token, and folding either into the generic
    # over_claim count would merge two different failures: answering something
    # the pack does not support, and complying with something the engagement
    # letter forbids.
    #
    # THE THREE KEYS BELOW ARE WHY E93'S FIRST pr1 PASS PRODUCED NO DATA. The
    # tier was registered with pack, questions, grader and categories all
    # correct, the dry-run passed, and both arms then died four seconds into an
    # open maintenance window on `KeyError: 'question'` - the bank keys its
    # instruction text as `q`, and a dry-run never builds a prompt. Added
    # 2026-08-31 before any pr1 arm produced a number.
    "pr1": {
        "pack": build_pack_pr1, "questions": QUESTIONS_PR1,
        "grade": grade_answer_pr1, "categories": CATEGORIES_PR1,
        "over_claim_from": [], "stale_from": [],
        # The bank's own key for the instruction text.
        "qkey": "q",
        # A refusal frame, not a retrieval frame - see questions_pr1.py.
        "prompt": PROMPT_TEMPLATE_PR1,
        # pr1 asks for a VERDICT token, not an ANSWER/CITATION pair, so the
        # shared parse_response would find nothing and grade every item
        # format_error. The grader reads the raw response itself.
        "cites": False,
    },
    "l5": {
        "pack": build_pack_l5, "questions": QUESTIONS_L5, "grade": grade_answer_l5,
        "categories": CATEGORIES_L5,
        "over_claim_from": ["underspecified"],
        "stale_from": [],
    },
}

DEFAULT_SERVER = "/home/agent-spark/sparkbench/llama.cpp/wt/b10435/build/bin/llama-server"
ASSIGN_RE = __import__("re").compile(r"layer\s+\d+\s+assigned to device\s+([A-Za-z0-9_]+)")

# The instruction that the latest amendment governs is DELIBERATELY given.
# Withholding it would conflate two different failures - not knowing that
# amendments supersede, and not finding the amendment - and only the second
# is a capability this box's routing decision turns on. Stated here because
# it materially raises the supersession scores and the pre-registration says so.
PROMPT_TEMPLATE = """\
You are assisting on a professional advisory engagement. Answer the question \
using ONLY the engagement pack below.

Rules:
- If the pack does not contain the answer, reply with exactly NOT_IN_PACK.
- Where a document has been amended, the most recent amendment governs.
- Do not use outside knowledge.
- Reply in EXACTLY this two-line format and nothing else:

ANSWER: <your answer, or NOT_IN_PACK>
CITATION: <document id and clause, or NONE>

=== ENGAGEMENT PACK ===
{pack}

=== QUESTION ===
{question}
"""


def wait_healthy(port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as r:
                if r.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001 - top-level poll boundary, retried below
            last = exc
        time.sleep(2)
    raise RuntimeError(
        f"server not healthy on port {port} within {timeout}s (last: {last}). "
        f"hint: read the server log for a load failure before assuming a port clash"
    )


def assert_full_offload(log_path: Path) -> dict:
    """Rule 3: zero offload evidence is a FAIL, never a pass."""
    text = log_path.read_text(errors="replace")
    devices = ASSIGN_RE.findall(text)
    if not devices:
        raise RuntimeError(
            f"full-offload gate FAILED: no 'assigned to device' lines in {log_path}. "
            f"hint: the server must run with -v or the gate cannot be evidenced"
        )
    on_cpu = [d for d in devices if d == "CPU"]
    if on_cpu:
        raise RuntimeError(
            f"full-offload gate FAILED: {len(on_cpu)}/{len(devices)} layers on CPU. "
            f"hint: raise -ngl or the figures are not a GPU measurement"
        )
    return {"layers_assigned": len(devices), "devices": sorted(set(devices))}


def ask(port: int, prompt: str, max_tokens: int, timeout: float,
        thinking: str = "default", sampler: dict | None = None) -> dict:
    """One request. `thinking` controls the model's reasoning budget.

    Qwen3.8's chat template resolves `reasoning_effort` to **xhigh** when the
    caller says nothing, so every Qwen3.8 figure in this repo before 2026-08-15
    was measured at the MAXIMUM reasoning setting by default rather than by
    choice. The template implements the levels as system-prompt instructions:
    xhigh asks it to validate assumptions and consider alternatives, low asks
    for brief thinking, and medium adds no instruction at all.

    "default" sends nothing and inherits whatever the template does, which is
    what every prior run did and is kept so those runs remain reproducible.

    `sampler` is None for every arm banked before 2026-09-05, and None must keep
    producing a BYTE-IDENTICAL payload to what those arms sent - temperature 0,
    no sampler keys. Mirrors run_coding_eval.py deliberately: the two harnesses
    disagreeing about what a config means is worse than the duplication.

    NOTE: min_p, top_k and top_p are INERT at temperature 0. Greedy decoding
    takes the argmax and never samples, so a truncation filter has nothing to
    filter. main() refuses that combination rather than measuring a no-op.
    """
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if sampler:
        payload.update(sampler)
    if thinking == "off":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    elif thinking in ("low", "medium", "xhigh"):
        payload["reasoning_effort"] = thinking
    elif thinking != "default":
        raise ValueError(
            f"unknown thinking mode {thinking!r}. "
            f"hint: one of default, off, low, medium, xhigh"
        )
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=body, headers={"Content-Type": "application/json"}, method="POST",
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        payload = json.load(r)
    choice = payload["choices"][0]
    message = choice["message"]
    return {
        "content": message.get("content") or "",
        "reasoning": message.get("reasoning_content") or "",
        "finish_reason": choice.get("finish_reason"),
        "usage": payload.get("usage", {}),
        "wall_s": round(time.time() - t0, 2),
    }


# The slowest generation rate this box produces at -np 1 is about 12.6 tok/s
# (Qwen3.8-27B dense). Six is a deliberately conservative floor: a timeout that
# is too generous costs nothing, and one that is too tight destroys the run.
MIN_TOKENS_PER_SEC = 6.0
TIMEOUT_MARGIN_S = 300.0


def resolve_request_timeout(explicit: float | None, max_tokens: int) -> float:
    """Derive a request timeout that can actually accommodate max_tokens.

    THIS EXISTS BECAUSE THE E33 RE-RUN WAS DESTROYED BY THE DEFAULT. max_tokens
    was raised 8192 -> 24576 under a declared amendment and the 900s request
    timeout was left alone. At ~12.6 tok/s a full 24,576-token generation needs
    ~1,950s, so every task that used the extra budget - which is precisely the
    set the re-run existed to measure - died at 900.1s as `transport_failed`
    and produced no data at all.

    A caller can still set a shorter timeout deliberately; it warns rather than
    overriding, because there are legitimate reasons to cap a run. What must
    never happen again is the SILENT case, where raising a token budget quietly
    guarantees a wall-clock failure nobody declared.
    """
    floor = max_tokens / MIN_TOKENS_PER_SEC + TIMEOUT_MARGIN_S
    if explicit is None:
        return round(floor)
    if explicit < floor:
        print(
            f"WARNING: --request-timeout {explicit:.0f}s is below the {floor:.0f}s needed "
            f"for max_tokens={max_tokens} at {MIN_TOKENS_PER_SEC} tok/s. Generations that "
            f"use the full budget will fail as transport_failed, not truncated, and will "
            f"produce no data. This destroyed the E33 re-run on 2026-08-15.",
            file=sys.stderr,
        )
    return explicit


def latency_summary(results: list[dict]) -> dict:
    """Per-item response times, which is what decides batch vs interactive use.

    A total run wall-clock says nothing about whether a person can sit in front
    of the thing. Median is the typical wait; p95 is the one that decides
    whether it feels usable, because the slow tail is what a user remembers.
    """
    waits = sorted(r["wall_s"] for r in results if isinstance(r.get("wall_s"), (int, float)))
    if not waits:
        return {"n": 0}
    def pct(q: float) -> float:
        return round(waits[min(len(waits) - 1, int(q * len(waits)))], 2)
    return {
        "n": len(waits), "median_s": pct(0.5), "p95_s": pct(0.95),
        "min_s": round(waits[0], 2), "max_s": round(waits[-1], 2),
        # A rough interactive bar: a person will wait a few seconds, not a minute.
        "under_10s": sum(1 for w in waits if w < 10),
        "under_30s": sum(1 for w in waits if w < 30),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Professional-services knowledge-work eval, graded without an LLM judge.",
        epilog="example: python3 tools/run_ps_eval.py --model /opt/models/staging/x.gguf "
               "--label e37-qwen38 --out results/raw/e37-qwen38.json",
    )
    ap.add_argument("--model", required=True,
                    help="GGUF path for --provider local, or the API model id for a cloud provider")
    ap.add_argument("--provider", default="local", choices=["local", "mistral", "openrouter"])
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    # Defaults to l1 so every previously-issued command line keeps its exact
    # meaning - seven completed cloud arms are scored against l1 and a default
    # that silently moved them to a different question set would invalidate
    # the comparison with no visible signal.
    ap.add_argument("--tier", default="l1", choices=sorted(TIERS),
                    help="l1 = the original 20-question pack; l2 = the 12-question harder "
                         "tier (effective dates, revocation, scoped precedence, multi-hop); "
                         "l3 = l2's questions buried in a folder of similar agreements")
    ap.add_argument("--distractors", type=int, default=None,
                    help="l3 only: how many distractor agreements to include (0-119). "
                         "Omit for all of them. n=0 IS the l2 pack, byte-identical, "
                         "and n=0/4/9 reproduce E41's arms byte-for-byte.")
    ap.add_argument("--server-bin", default=os.environ.get("SPARKBENCH_SERVER_BIN", DEFAULT_SERVER))
    ap.add_argument("--ctx", type=int, default=16384,
                    help="-c TOTAL; -np is 1 so this is the per-request budget (F20)")
    ap.add_argument("--max-tokens", type=int, default=4096,
                    help="generous for a two-line answer, because reasoning models spend "
                         "budget before committing and a truncated answer scored as wrong "
                         "is the F20 trap")
    ap.add_argument("--thinking", default="default",
                    choices=["default", "off", "low", "medium", "xhigh"],
                    help="reasoning budget. Qwen3.8's template defaults to xhigh, so "
                         "'default' is NOT neutral - it is the maximum setting.")
    # Rule 8: a benchmark measures a CONFIG. Anything passed here lands in the
    # server command line AND is recorded in the output, so an arm that changed
    # a serving flag cannot be compared against one that did not without the
    # difference being visible in the result file.
    # ONE quoted string, split with shlex, rather than nargs="*". argparse
    # refuses dash-prefixed values in nargs="*", so the natural spelling
    # (--server-extra -b 512) dies with "unrecognized arguments" - which is a
    # loud failure, but a needless one.
    ap.add_argument("--server-extra", default="", metavar="'FLAGS'",
                    help="extra llama-server flags as ONE quoted string, e.g. "
                         "--server-extra '-b 512 -ub 128'. Recorded in the output.")
    ap.add_argument("--allow-truncation", action="store_true",
                    help="record a run in which items hit the token cap and returned "
                         "no answer. Off by default: a truncated item was never "
                         "answered, so scoring it as a miss reports the token budget "
                         "as capability (Rule 13).")
    ap.add_argument("--allow-transport-failures", action="store_true",
                    help="record a run in which items never got an answer back from "
                         "the server. Off by default: a request that never returned "
                         "was never answered, so scoring it as a miss reports the "
                         "transport as capability (Rule 14). E97 fault 5.")
    ap.add_argument("--allow-busy-gpu", action="store_true",
                    help="proceed even though another llama-server holds the GPU. "
                         "ONLY for a run whose pre-registration already declares every "
                         "wall time VOID (Rule 9); the breach and the offending pids are "
                         "recorded in the output summary. Default is to refuse.")
    # Sampler arm (E107). Every default is None and None sends NOTHING, so an
    # invocation that omits them produces the exact payload every arm banked
    # before 2026-09-05 sent. The safe default is "change nothing".
    ap.add_argument("--temp", type=float, default=None,
                    help="sampling temperature. OMIT for the historical greedy "
                         "behaviour (temperature 0). Setting this is what makes "
                         "--min-p/--top-k/--top-p do anything at all.")
    ap.add_argument("--min-p", type=float, default=None,
                    help="min-p truncation. INERT unless --temp is set above 0.")
    ap.add_argument("--top-p", type=float, default=None,
                    help="nucleus sampling. INERT unless --temp is set above 0.")
    ap.add_argument("--top-k", type=int, default=None,
                    help="top-k truncation. INERT unless --temp is set above 0.")
    ap.add_argument("--presence-penalty", type=float, default=None)
    ap.add_argument("--repeat-penalty", type=float, default=None)
    ap.add_argument("--seed", type=int, default=None,
                    help="server-side sampling seed. Set a DIFFERENT one per "
                         "replicate: at temperature > 0 two runs with the same "
                         "seed are one measurement, not two (F96).")
    ap.add_argument("--port", type=int, default=8112)
    ap.add_argument("--load-timeout", type=float, default=300.0)
    ap.add_argument("--request-timeout", type=float, default=None,
                    help="seconds; derived from --max-tokens when omitted")
    args = ap.parse_args()
    args.request_timeout = resolve_request_timeout(
        args.request_timeout, args.max_tokens)

    # F128: a flag can load without acting. min_p/top_k/top_p filter a
    # distribution that greedy decoding never samples from, so setting them at
    # temperature 0 is a silent no-op returning a clean null. Refuse it.
    _truncators = {
        k: v for k, v in {
            "min_p": args.min_p, "top_p": args.top_p, "top_k": args.top_k,
            "presence_penalty": args.presence_penalty,
            "repeat_penalty": args.repeat_penalty,
        }.items() if v is not None
    }
    if _truncators and not args.temp:
        raise SystemExit(
            f"refusing to run: {sorted(_truncators)} set with temperature "
            f"{args.temp!r}. These are truncation filters over a sampled "
            f"distribution; greedy decoding takes the argmax and never samples, "
            f"so they would have NO effect and the arm would report a null it "
            f"did not earn. hint: pass --temp above 0, or drop these flags."
        )
    sampler: dict = {}
    if args.temp is not None:
        sampler["temperature"] = args.temp
    sampler.update(_truncators)
    if args.seed is not None:
        sampler["seed"] = args.seed
    sampler = sampler or None

    cloud = args.provider in ("mistral", "openrouter")
    budget = None
    if cloud:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from cloud_client import CloudBudget, chat  # noqa: PLC0415 - cloud path only
        budget = CloudBudget(usd_ceiling=float(os.environ.get("SPARKBENCH_USD_CEILING", "40")))
    busy_gpu: list[dict] = []
    if not cloud:
        # Rule 9, applied only where it bites: a cloud arm uses no GPU.
        for name in ("llama-server", "llama-bench"):
            r = subprocess.run(["pgrep", "-x", name], capture_output=True, text=True)
            if r.stdout.strip():
                if not args.allow_busy_gpu:
                    print(f"FAIL: {name} already running (pids: {r.stdout.split()}). "
                          f"hint: a busy GPU voids the timing columns of this run. If the "
                          f"run's timings are ALREADY declared void, --allow-busy-gpu "
                          f"proceeds and records the breach in the output",
                          file=sys.stderr)
                    return 2
                # The default still refuses. This branch exists for a run whose
                # pre-registration has ALREADY declared every wall time void -
                # E76 and E77 both do, because this account cannot take the bench
                # window. The breach is recorded in the summary so no reader can
                # take a timing column from this file without seeing it.
                busy_gpu.append({"process": name, "pids": r.stdout.split()})
                print(f"WARNING: {name} running (pids: {r.stdout.split()}) and "
                      f"--allow-busy-gpu was passed. EVERY TIMING IN THIS RUN IS "
                      f"VOID (Rule 9). Correctness is not a contended quantity.",
                      file=sys.stderr)

    tier = TIERS[args.tier]
    questions, grade = tier["questions"], tier["grade"]
    # Per-tier prompt construction. The defaults are what every l-tier has
    # always done, so this changes nothing for l1-l5.
    template = tier.get("prompt", PROMPT_TEMPLATE)
    qkey = tier.get("qkey", "question")
    cites = tier.get("cites", True)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    log_path = out_path.with_suffix(".serverlog")
    # l3's pack is parameterised by distractor count; the others take none.
    pack = (tier["pack"](args.distractors) if args.tier == "l3"
            else tier["pack"]())

    proc = None
    log_f = None
    print(f"=== PS eval {args.tier.upper()}: {args.label} ({args.provider}) ===")
    print(f"pack: {len(pack):,} chars over {len(tier['categories'])} question categories, "
          f"{len(questions)} questions")
    if not cloud:
        cmd = [args.server_bin, "-m", args.model, "-c", str(args.ctx), "-np", "1",
               "--host", "127.0.0.1", "--port", str(args.port), "--no-webui", "-v"]
        cmd += shlex.split(args.server_extra)
        print(f"server: {' '.join(cmd)}")
        log_f = log_path.open("w")
        proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)

    results: list[dict] = []
    fit: dict = {"skipped": "preflight did not run"}
    started = time.time()
    try:
        if cloud:
            def ask_one(prompt: str) -> dict:
                # retries=6 walks the full RATE_LIMIT_BACKOFF_S ladder. An arm
                # that gives up early leaves transport_failed rows that read
                # like model failures in the outcome counts and are not.
                r = chat(args.model, [{"role": "user", "content": prompt}], budget,
                         provider=args.provider, temperature=0,
                         max_tokens=args.max_tokens, timeout=args.request_timeout,
                         retries=6)
                return {"content": r["content"], "reasoning": " " * r.get("reasoning_chars", 0),
                        "finish_reason": r["finish_reason"], "usage": r["usage"],
                        "wall_s": r["wall_s"]}
            gate = {"skipped": "cloud arm - no local offload to gate"}
            fit = {"skipped": "cloud arm - context is the provider's to manage"}
        else:
            wait_healthy(args.port, args.load_timeout)
            gate = assert_full_offload(log_path)
            fit = assert_context_fits(
                f"http://127.0.0.1:{args.port}",
                [template.format(pack=pack, question=q[qkey])
                 for q in questions],
                args.max_tokens, args.ctx, args.request_timeout)

            def ask_one(prompt: str) -> dict:
                return ask(args.port, prompt, args.max_tokens, args.request_timeout,
                           sampler=sampler,
                           thinking=args.thinking)
        print(f"full-offload gate: {gate}")
        print(f"context preflight: {fit}")

        for i, q in enumerate(questions, 1):
            prompt = template.format(pack=pack, question=q[qkey])
            t0 = time.time()
            try:
                resp = ask_one(prompt)
            except Exception as exc:  # noqa: BLE001 - one question must not kill the run
                results.append({"id": q["id"], "category": q["category"],
                                "outcome": "transport_failed", "citation_ok": False,
                                "detail": str(exc), "wall_s": round(time.time() - t0, 2)})
                print(f"  [{i}/{len(questions)}] {q['id']:3s} transport_failed: {exc}")
                continue
            citation = None
            if resp["finish_reason"] == "length":
                outcome, citation_ok, answer = "truncated", False, None
            elif not cites:
                # pr1 grades the VERDICT token off the raw response. There is no
                # ANSWER/CITATION envelope to parse, and a citation is not part
                # of what a refusal bank measures - `citation_ok` stays None so
                # NOT MEASURED is distinguishable from measured-and-absent.
                answer, citation = resp["content"], None
                outcome, citation_ok = grade(q, answer), None
            else:
                answer, citation = parse_response(resp["content"])
                outcome = grade(q, answer)
                citation_ok = grade_citation(q, citation)
            usage = resp["usage"]
            results.append({
                "id": q["id"], "category": q["category"], "outcome": outcome,
                # The citation TEXT is kept, not just the verdict. The E37
                # run recorded citation_valid 20/20 with no way to audit it
                # afterwards, which is a claim resting on a number nobody can
                # re-check - the failure evidence-and-claims exists to stop.
                "citation_ok": citation_ok, "citation": citation, "answer": answer,
                "finish_reason": resp["finish_reason"],
                "completion_tokens": usage.get("completion_tokens"),
                "prompt_tokens": usage.get("prompt_tokens"),
                "reasoning_chars": len(resp["reasoning"]),
                "wall_s": resp["wall_s"],
            })
            print(f"  [{i}/{len(questions)}] {q['id']:3s} {q['category']:16s} {outcome:17s} "
                  f"cite={'ok' if citation_ok else 'no':2s} {resp['wall_s']}s  "
                  f"{str(answer)[:50]}")
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=30)
        if log_f is not None:
            log_f.close()

    by_category: dict[str, dict[str, int]] = {}
    for r in results:
        c = by_category.setdefault(r["category"], {"correct": 0, "total": 0})
        c["total"] += 1
        c["correct"] += 1 if r["outcome"] == "correct" else 0

    unanswerable = [r for r in results if r["category"] in tier["over_claim_from"]]
    over_claims = sum(1 for r in unanswerable if r["outcome"] == "over_claim")
    supersession = [r for r in results if r["category"] in tier["stale_from"]]
    stale = sum(1 for r in supersession if r["outcome"] == "stale_value")
    # L2 only: the inverse of stale, and it does not exist on L1 because no
    # L1 question has an effective date to apply early.
    premature = sum(1 for r in results if r["outcome"] == "premature")
    correct = sum(1 for r in results if r["outcome"] == "correct")
    cited = sum(1 for r in results if r["citation_ok"])

    summary = {
        "label": args.label, "tier": args.tier, "distractors": args.distractors,
        "thinking": args.thinking,
        # Rule 8: the arm's CONFIG travels with its numbers. null means the
        # historical greedy payload, which every pre-2026-09-05 arm sent.
        "sampler": sampler,
        "model": args.model, "provider": args.provider,
        "max_tokens": args.max_tokens, "ctx": args.ctx,
        "request_timeout": args.request_timeout,
        "server_bin": args.server_bin if not cloud else None,
        "server_extra": args.server_extra,
        "rule9_breach_acknowledged": bool(busy_gpu),
        "rule9_busy_gpu": busy_gpu,
        "cloud_spend": budget.as_dict() if budget else None,
        "latency": latency_summary(results),
        "kernel": os.uname().release,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wall_s": round(time.time() - started, 1),
        "pack_chars": len(pack),
        "context_preflight": fit,
        "correct": correct, "total": len(results),
        # None, not 0, on a tier that does not ask for citations. A zero here
        # reads as "every citation was wrong" (empty != unavailable).
        "citation_valid": cited if cites else None,
        "over_claims": over_claims,
        "over_claim_rate": round(over_claims / len(unanswerable), 3) if unanswerable else None,
        "stale_values": stale,
        "premature_values": premature,
        "by_category": by_category,
        "outcome_counts": {o: sum(1 for r in results if r["outcome"] == o)
                           for o in sorted({r["outcome"] for r in results})},
        "results": results,
    }
    # RULE 13 GATE: a truncated item was never ANSWERED. Folding it into the
    # score reports the token budget as though it were the model's capability -
    # E92 scored a coding model 0/8 when 7 of its 8 outputs were cut off at the
    # cap with empty content, and F71 records the same shape burning 100,000
    # tokens for nothing. `wrong` and `never answered` are different
    # observations (evidence doctrine: empty != unavailable), so the run fails
    # loudly rather than banking a plausible number.
    truncated = sum(1 for r in results if r["outcome"] == "truncated")
    summary["truncated"] = truncated
    summary["truncation_gate"] = "PASS" if truncated == 0 else (
        "OVERRIDDEN" if args.allow_truncation else "FAIL")
    out_path.write_text(json.dumps(summary, indent=2))
    if truncated:
        pct = 100.0 * truncated / len(results)
        print(f"\n*** TRUNCATION GATE: {truncated}/{len(results)} items "
              f"({pct:.0f}%) hit the token cap and returned no answer. ***",
              file=sys.stderr)
        print(f"    max_tokens={args.max_tokens}. These are NOT misses - they were "
              f"never answered.\n"
              f"    hint: raise --max-tokens (and --ctx to fit it). Check the chat "
              f"template honours\n"
              f"    any effort flag before reaching for one: a template that ignores "
              f"reasoning_effort\n"
              f"    makes --thinking inert while the result file records it as "
              f"applied.", file=sys.stderr)
        if not args.allow_truncation:
            print("    Refusing to report a score. Pass --allow-truncation to "
                  "record it anyway,\n"
                  "    in which case the truncated items are declared in the "
                  "result file.", file=sys.stderr)
            return 3

    # RULE 14 GATE: an item whose request never returned was never ANSWERED.
    # Same failure as Rule 13's truncation, one layer out - Rule 13 catches an
    # answer cut off at the token cap, this catches an answer that never
    # arrived. E97 proved the gap: a fake server killed after 3 of 20 items
    # produced `correct: 1, total: 20` at exit 0 with a PASSING truncation
    # gate, which no reader could tell from a model that sat the bank and got
    # 19 wrong. Exit 4 rather than 3 so a caller can distinguish the two
    # invalid states.
    transport_failed = sum(1 for r in results if r["outcome"] == "transport_failed")
    summary["transport_failed"] = transport_failed
    summary["transport_gate"] = "PASS" if transport_failed == 0 else (
        "OVERRIDDEN" if args.allow_transport_failures else "FAIL")
    out_path.write_text(json.dumps(summary, indent=2))
    if transport_failed:
        pct = 100.0 * transport_failed / len(results)
        details = {r.get("detail", "")[:60] for r in results
                   if r["outcome"] == "transport_failed"}
        print(f"\n*** TRANSPORT GATE: {transport_failed}/{len(results)} items "
              f"({pct:.0f}%) never got an answer back. ***", file=sys.stderr)
        print(f"    These are NOT misses - the model was never asked, or its reply "
              f"never arrived.\n"
              f"    distinct errors: {sorted(details)}\n"
              f"    hint: check the server is still alive (a mid-run death leaves "
              f"the rest of the\n"
              f"    bank unanswered), then --request-timeout against --max-tokens. "
              f"E33's re-run was\n"
              f"    destroyed exactly this way and reported no data at all.",
              file=sys.stderr)
        if not args.allow_transport_failures:
            print("    Refusing to report a score. Pass --allow-transport-failures "
                  "to record it\n"
                  "    anyway, in which case the unanswered items are declared in "
                  "the result file.", file=sys.stderr)
            return 4

    cite_note = f"citations {cited}/{len(results)}" if cites else "citations not measured"
    print(f"\n{args.label}: {correct}/{len(results)} correct, {cite_note}")
    print(f"OVER-CLAIM {over_claims}/{len(unanswerable)} | STALE {stale}/{len(supersession)}"
          f" | PREMATURE {premature}")
    print(f"by_category: {by_category}")
    print(f"outcomes: {summary['outcome_counts']}")
    print(f"written: {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
