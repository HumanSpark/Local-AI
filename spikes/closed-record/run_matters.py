#!/usr/bin/env python3
# File: run_matters.py
# Purpose: Put every closed-record matter to one served model and store the answers verbatim.
# Project: sparkbench | Date: 2026-08-12
#
# Overview: Sends each matter.md as a single user message to an OpenAI-compatible
# /v1/chat/completions endpoint and records the answer, the token usage and the server's own
# finish reason. It does no scoring - answers are stored raw so a key correction can be re-scored
# without re-running a model, which is the whole reason keyed scoring is cheaper than judging.
# Every HTTP call carries a timeout (HARNESS-RULES rule 2) and progress is printed per matter
# because a full pass takes minutes.
# Scoring: score_matter.py. Lifecycle: tools/run_closed_record.sh.

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
from bench_context import assert_context_fits, server_context  # noqa: E402


def matters(matters_dir: Path, only: list[str] | None = None,
            order: str = "sorted") -> list[tuple[str, str]]:
    """(name, prompt) for every matter, in a reproducible run order.

    `only` restricts the run to named matters, matched as a PREFIX so that
    "m11" selects "m11-limitation-clocks" without retyping the slug. A name
    that matches nothing RAISES rather than silently shrinking the run - a
    typo'd filter that quietly ran 2 matters instead of 3 would be scored as
    though the third had no answer.

    `order` defaults to "sorted", which is what every run before 2026-08-17
    did, so no earlier result changes meaning. "reverse" and "given" exist
    because F70 made run order a VARIABLE: a matter's answer depends on how
    many requests preceded it in the session, so permuting the order is how
    you put the same matter at a different sequence position without changing
    anything else about it.
    """
    if not matters_dir.exists():
        raise FileNotFoundError(
            f"matters directory not found: {matters_dir}; "
            f"hint: matters live in spikes/closed-record/matters/<id>-<slug>/"
        )
    found = []
    for path in sorted(matters_dir.glob("*/matter.md")):
        found.append((path.parent.name, path.read_text()))
    if not found:
        raise ValueError(
            f"no matter.md found under {matters_dir}; "
            f"hint: each matter directory needs matter.md and key.yaml"
        )
    if only:
        available = [n for n, _ in found]
        unmatched = [k for k in only if not any(n.startswith(k) for n in available)]
        if unmatched:
            raise ValueError(
                f"--only named {unmatched} which match no matter in {matters_dir}. "
                f"available: {', '.join(available)}; "
                f"hint: names are matched as a prefix, so 'm11' is enough - a "
                f"filter that matched nothing would silently shrink the run"
            )
        found = [(n, p) for n, p in found if any(n.startswith(k) for k in only)]
    if order == "reverse":
        found.reverse()
    elif order == "given":
        if not only:
            raise ValueError(
                "--order given requires --only to say what the order IS. "
                "hint: pass the matters in the sequence you want them run"
            )
        # Position in the --only list decides run order. F70 established that a
        # matter's ANSWER depends on how many requests preceded it, so order is
        # a variable, not a presentation detail.
        rank = {k: i for i, k in enumerate(only)}
        found.sort(key=lambda np: next(rank[k] for k in only if np[0].startswith(k)))
    elif order != "sorted":
        raise ValueError(
            f"unknown order {order!r}. hint: one of sorted, reverse, given"
        )
    return found


def read_api_key(env_var: str | None) -> str | None:
    """The API key for a hosted arm, from the environment only.

    Never accepted on the command line: argv is world-readable via `ps`. The local arm passes
    nothing and gets None, which sends no Authorization header at all - llama-server does not
    want one.
    """
    if not env_var:
        return None
    key = os.environ.get(env_var)
    if not key:
        raise RuntimeError(
            f"{env_var} is not set in the environment; "
            f"hint: export it from its config file in the calling shell - do not pass a key "
            f"as a command-line argument, argv is visible to every user via ps"
        )
    return key


# A generation cannot outrun the hardware. 6 tok/s is a deliberate floor well
# under Qwen3.8's measured ~12.6 tok/s, so the derived timeout has headroom
# rather than tracking the observed rate.
MIN_TOKENS_PER_SEC = 6.0
TIMEOUT_MARGIN_S = 300.0


def resolve_request_timeout(explicit: float | None, max_tokens: int) -> float:
    """Derive a request timeout that can actually accommodate max_tokens.

    THIS EXISTS BECAUSE THE E33 RE-RUN WAS DESTROYED BY A FIXED DEFAULT. That
    runner had max_tokens raised 8192 -> 24576 under a declared amendment while
    its 900s request timeout was left alone, so every task that used the extra
    budget - precisely the set the re-run existed to measure - died as
    `transport_failed` and produced no data.

    This file carried the identical defect with a 600s default until
    2026-08-15. E43 runs at max_tokens=24576, which needs ~4,400s; at 600s the
    long matters would all have failed, and the long matters are the ones F60
    says discriminate.

    A caller can still set a shorter timeout deliberately; it warns rather than
    overriding. What must never happen again is the SILENT case, where raising
    a token budget quietly guarantees a wall-clock failure nobody declared.
    """
    floor = max_tokens / MIN_TOKENS_PER_SEC + TIMEOUT_MARGIN_S
    if explicit is None:
        return round(floor)
    if explicit < floor:
        print(
            f"WARNING: --timeout {explicit:.0f}s is below the {floor:.0f}s needed for "
            f"max_tokens={max_tokens} at {MIN_TOKENS_PER_SEC} tok/s. Generations that use "
            f"the full budget will fail as transport_failed, not truncated, and will "
            f"produce no data at all.",
            file=sys.stderr,
        )
    return explicit


def ask(
    base_url: str,
    prompt: str,
    max_tokens: int,
    timeout: float,
    model: str | None = None,
    api_key: str | None = None,
    thinking: str = "default",
) -> dict:
    """One completion. Raises on transport failure rather than recording an empty answer.

    `thinking` controls the reasoning budget. Qwen3.8's chat template resolves
    reasoning_effort to xhigh when the caller says nothing, so "default" is the
    MAXIMUM setting rather than a neutral one - measured in E42, where it cost
    38% more tokens than `low` for an identical score.
    """
    body: dict = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": max_tokens,
    }
    if thinking == "off":
        body["chat_template_kwargs"] = {"enable_thinking": False}
    elif thinking in ("low", "medium", "xhigh"):
        body["reasoning_effort"] = thinking
    elif thinking != "default":
        raise ValueError(
            f"unknown thinking mode {thinking!r}. "
            f"hint: one of default, off, low, medium, xhigh"
        )
    # llama-server serves whatever model it was started with and ignores the field; a hosted
    # gateway routes on it and rejects the request without it.
    if model:
        body["model"] = model
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers=headers,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"request to {base_url} failed: {exc}; "
            f"hint: is llama-server up on that port, and was -c large enough for the prompt?"
        ) from exc


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Run every closed-record matter against one served model.",
        epilog="Example: python3 run_matters.py --label mistral-24b --out ../../results/"
        "closed-record/mistral-24b.json",
    )
    ap.add_argument("--base-url", default="http://127.0.0.1:8100")
    ap.add_argument(
        "--label", required=True, help="model label, recorded in the output"
    )
    ap.add_argument("--matters-dir", default=str(Path(__file__).parent / "matters"))
    ap.add_argument("--out", required=True)
    # 2000 was the default until 2026-08-15. At the reasoning level Qwen3.8
    # inherits by default it is far below what the model spends before it
    # answers, so it truncates and makes the corpus look harder than it is.
    ap.add_argument("--max-tokens", type=int, default=2000)
    ap.add_argument("--thinking", default="default",
                    choices=["default", "off", "low", "medium", "xhigh"],
                    help="reasoning budget; 'default' inherits the template's "
                         "xhigh for Qwen3.8 and is NOT neutral")
    # None, not 600.0: the timeout is DERIVED from --max-tokens unless a caller
    # sets it deliberately. See resolve_request_timeout.
    ap.add_argument("--timeout", type=float, default=None)
    ap.add_argument("--reps", type=int, default=1, help="repetitions per matter")
    ap.add_argument("--order", default="sorted", choices=["sorted", "reverse", "given"],
                    help="run order. 'sorted' is the historical default and keeps "
                         "every earlier run comparable; 'reverse' and 'given' exist "
                         "because F70 makes sequence position a variable")
    ap.add_argument("--only", default=None,
                    help="comma-separated matter names to run, prefix-matched "
                         "(e.g. 'm11,m12,m13'). Omit to run all. A name that "
                         "matches nothing is an error, not a smaller run")
    ap.add_argument(
        "--model",
        default=None,
        help="model id for a hosted gateway; omit for llama-server",
    )
    ap.add_argument(
        "--api-key-env",
        default=None,
        help="NAME of the env var holding the API key (never the key itself)",
    )
    args = ap.parse_args()
    bearer = read_api_key(args.api_key_env)

    only = [s.strip() for s in args.only.split(",") if s.strip()] if args.only else None
    todo = matters(Path(args.matters_dir), only, args.order)
    request_timeout = resolve_request_timeout(args.timeout, args.max_tokens)
    print(
        f"{args.label}: {len(todo)} matters x {args.reps} rep(s), "
        f"max_tokens={args.max_tokens}, thinking={args.thinking}, "
        f"request_timeout={request_timeout:.0f}s"
    )

    # Context preflight. This runner ATTACHES to a server someone else
    # started, so `-c` is not on its command line and has to be asked for. A
    # hosted gateway (--model set) manages its own context and has no
    # /props to read, so the check is skipped and SAYS it was skipped rather
    # than recording a pass it did not perform.
    if args.model:
        fit = {"skipped": "hosted gateway - context is the provider's to manage"}
    else:
        served_ctx = server_context(args.base_url)
        fit = assert_context_fits(
            args.base_url, [prompt for _, prompt in todo],
            args.max_tokens, served_ctx, request_timeout)
    print(f"context preflight: {fit}")

    records = []
    started = time.monotonic()
    for i, (name, prompt) in enumerate(todo, 1):
        for rep in range(args.reps):
            t0 = time.monotonic()
            resp = ask(
                args.base_url,
                prompt,
                args.max_tokens,
                request_timeout,
                args.model,
                bearer,
                args.thinking,
            )
            choice = resp["choices"][0]
            usage = resp["usage"]
            records.append(
                {
                    "matter": name,
                    "rep": rep,
                    "answer": choice["message"]["content"],
                    "finish_reason": choice.get("finish_reason"),
                    "prompt_tokens": usage["prompt_tokens"],
                    "completion_tokens": usage["completion_tokens"],
                    "seconds": round(time.monotonic() - t0, 1),
                    # Hosted gateways return their own usage extras (cost, cached tokens).
                    # Recorded verbatim so spend is evidenced rather than estimated.
                    "usage_raw": usage,
                }
            )
            print(
                f"  [{i}/{len(todo)}] {name} rep{rep}: "
                f"{usage['completion_tokens']} tok, {records[-1]['seconds']}s, "
                f"finish={choice.get('finish_reason')}"
            )

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "label": args.label,
                "model": args.model,
                "max_tokens": args.max_tokens,
                # E43's arms differ ONLY by thinking level, so a file that does
                # not carry it can be told apart only by its label (Rule 8).
                "thinking": args.thinking,
                "request_timeout": request_timeout,
                # Which matters ran. A subset run scored against the full
                # 13-matter total would understate by construction.
                "only": only,
                "matters_run": [n for n, _ in todo],
                "temperature": 0,
                "reps": args.reps,
                "records": records,
            },
            indent=1,
        )
    )
    print(f"{args.label}: done in {time.monotonic() - started:.0f}s -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
