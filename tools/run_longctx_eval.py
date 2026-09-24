#!/usr/bin/env python3
# File: run_longctx_eval.py
# Purpose: E35 - needle-at-depth retrieval quality at 8K/32K/64K/128K, tokenizer-measured, local or cloud.
# Project: sparkbench | Date: 2026-08-15
#
# Overview: F62 established that Qwen3.8-27B's SPEED barely decays with depth
# (-3.6% d0->d8192, the flattest on this box) because only 1 layer in 4 grows
# a KV cache. That says nothing about whether its ANSWERS hold up. This
# measures quality: build a corpus of real project prose to a target token
# length, plant five uniquely-identifiable sentinel facts at 5/25/50/75/95%
# depth, then ask five questions against that ONE corpus.
#
# WHY ONE CORPUS PER LENGTH AND NOT ONE PER NEEDLE: identical prefixes let
# llama-server's prompt cache serve every question after the first, so a 128K
# leg pays its ~460s prefill once instead of five times. It also removes
# corpus variation as a confound between depths.
#
# TOKEN BUDGETS COME FROM THE TOKENIZER, never chars/4 - the CLAUDE.md rule
# exists because technical text runs ~40% over that estimate. This calls the
# server's own /tokenize endpoint to size the corpus, so the "128K" leg is
# 128K to that model's tokenizer rather than to an assumption.
#
# Grading is exact-substring on a sentinel that cannot occur naturally
# (a nonsense token plus a random-looking number), so there is no grader
# artifact of the kind that cost the eval pilot a point in 2026-07.
#
# CLOUD PATH (--provider mistral|openrouter, added 2026-09-22): same corpus,
# needles and questions, sent through cloud_client.chat (the one choke point
# for spend ceilings and the confidential-material refusal). A provider has no
# /tokenize, so tokens are measured from its own usage.prompt_tokens on a
# probe call, minus the chat template's overhead - still the model's tokenizer,
# never chars/4. Sizing uses a sampled chars-per-token ratio so an 8K leg does
# not pay to measure the whole 1.5 MB source; the finished corpus is then
# measured once, authoritatively. Every question's reported prompt_tokens is
# checked against that figure: a provider that silently trims context gets
# `context_truncated`, never a wrong answer.

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path("/home/agent-spark/sparkbench")
DEFAULT_SERVER = str(ROOT / "llama.cpp/wt/b10435/build/bin/llama-server")
ASSIGN_RE = re.compile(r"layer\s+\d+\s+assigned to device\s+([A-Za-z0-9_]+)")

# Depth fractions and their sentinels. Values are fixed (not random) so a
# re-run is byte-comparable - determinism is the point at temperature 0 (F59).
NEEDLES = [
    (0.05, "ZARVOX", "418293"),
    (0.25, "QUILNAR", "570164"),
    (0.50, "BRIMSKAY", "832705"),
    (0.75, "DWENTHOL", "296481"),
    (0.95, "FRALIQUE", "651037"),
]
NEEDLE_TMPL = ("Operational note: the {name} calibration constant for this deployment "
               "is {value}. Record it exactly as written.")


def corpus_source() -> str:
    """Real project prose, so the distractor text is in-domain rather than lorem."""
    parts = []
    for rel in ("docs/FINDINGS.md", "results/experiments.md", "results/model-survey.md",
                "docs/HARNESS-RULES.md", "results/capability-probes.md"):
        p = ROOT / rel
        if p.exists():
            parts.append(p.read_text(errors="replace"))
    if not parts:
        raise RuntimeError("no corpus sources found. hint: run from a populated sparkbench checkout")
    return "\n\n".join(parts)


def count_tokens(port: int, text: str, timeout: float = 300.0) -> int:
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/tokenize",
        data=json.dumps({"content": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return len(json.loads(r.read().decode())["tokens"])


def build_corpus(port: int, target_tokens: int) -> tuple[str, int]:
    """Grow real prose to ~target tokens, measured by the model's own tokenizer."""
    src = corpus_source()
    per_copy = count_tokens(port, src)
    if per_copy == 0:
        raise RuntimeError("tokenizer returned 0 tokens for the corpus source")
    # Leave room for needles, question and answer.
    budget = int(target_tokens * 0.92)
    # Ceiling division, not floor: floor gives 1 copy whenever the source is
    # shorter than the budget, which silently under-delivers a long leg (the
    # 128K leg would have measured ~100K and been recorded as 128K).
    copies = max(1, -(-budget // per_copy))
    text = "\n\n".join(f"--- section {i + 1} ---\n{src}" for i in range(copies))
    got = count_tokens(port, text)
    # Trim by characters to land near budget without another tokenize loop.
    if got > budget:
        text = text[: int(len(text) * (budget / got))]
        got = count_tokens(port, text)
    if got < int(target_tokens * 0.80):
        raise RuntimeError(
            f"corpus only reached {got} tokens against target {target_tokens}. "
            f"hint: add sources to corpus_source() - a leg must not be labelled with a length it did not reach"
        )
    return text, got


def make_cloud_counter(chat_fn):
    """Token counter for a cloud model: probe prompt_tokens, subtract template overhead.

    chat_fn(text) sends ONE user message and returns the cloud_client.chat
    result. The overhead (role markers, BOS, system preamble) is measured once
    from a one-character message and cached, so every count is the text's own
    tokens to that provider's tokenizer, give or take the one "." token.
    """
    overhead: list[int] = []

    def count(text: str) -> int:
        if not overhead:
            # usage["prompt_tokens"] not .get(): a provider that omits it
            # cannot be sized, and a default would label a leg with a guess.
            overhead.append(chat_fn(".")["usage"]["prompt_tokens"] - 1)
        return chat_fn(text)["usage"]["prompt_tokens"] - overhead[0]

    return count


def build_corpus_cloud(count, target_tokens: int, sample_chars: int = 60_000) -> tuple[str, int]:
    """Grow real prose to ~target tokens for a cloud model, paying for as few tokens as possible.

    The chars-per-token ratio comes from a sample spread across the whole
    source (five evenly spaced slices), because the source mixes registers:
    FINDINGS.md prose and experiments.md tables tokenize differently. The
    finished text is then measured for real and held to the same 80% floor
    as the local path.
    """
    src = corpus_source()
    if len(src) <= sample_chars:
        sample = src
    else:
        width = sample_chars // 5
        step = (len(src) - width) // 4
        sample = "".join(src[i * step: i * step + width] for i in range(5))
    sample_tokens = count(sample)
    if sample_tokens <= 0:
        raise RuntimeError(f"provider measured {sample_tokens} tokens for a {len(sample)}-char sample. "
                           f"hint: check the probe call's usage block")
    char_ratio = len(sample) / sample_tokens
    budget = int(target_tokens * 0.92)
    chars_needed = int(budget * char_ratio)
    copies = max(1, -(-chars_needed // len(src)))
    text = "\n\n".join(f"--- section {i + 1} ---\n{src}" for i in range(copies))[:chars_needed]
    got = count(text)
    if got > budget:
        text = text[: int(len(text) * (budget / got))]
        got = count(text)
    if got < int(target_tokens * 0.80):
        raise RuntimeError(
            f"corpus only reached {got} tokens against target {target_tokens} "
            f"(sample ratio {char_ratio:.2f} chars/token). "
            f"hint: a leg must not be labelled with a length it did not reach - the sample "
            f"ratio does not hold for the full text; widen sample_chars"
        )
    return text, got


def classify_outcome(content: str, finish_reason: str | None, expected: str, *,
                     prompt_tokens: int | None, corpus_tokens: int | None) -> str:
    """Score one needle. corpus_tokens=None skips the truncation check (local path).

    A prompt measured SHORTER than the corpus means the provider dropped
    context before the model saw it. That is neither a pass nor a wrong
    answer: the depth the row claims was never tested.
    """
    if corpus_tokens is not None and prompt_tokens is not None and prompt_tokens < corpus_tokens:
        return "context_truncated"
    if expected in content.replace(",", ""):
        return "pass"
    return "truncated" if finish_reason == "length" else "wrong"


def insert_needles(text: str) -> str:
    lines = text.split("\n")
    n = len(lines)
    # Insert deepest-first so earlier indices stay valid.
    for frac, name, value in sorted(NEEDLES, key=lambda x: -x[0]):
        idx = min(n - 1, max(0, int(n * frac)))
        lines.insert(idx, NEEDLE_TMPL.format(name=name, value=value))
    return "\n".join(lines)


def wait_healthy(port: int, timeout: float) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=5) as r:
                if r.status == 200:
                    return
        except Exception as exc:  # noqa: BLE001 - poll boundary
            last = exc
        time.sleep(3)
    raise RuntimeError(f"server not healthy within {timeout}s (last: {last}). "
                       f"hint: a big -c can take minutes to allocate KV; raise --load-timeout")


def assert_full_offload(log_path: Path) -> dict:
    text = log_path.read_text(errors="replace")
    devices = ASSIGN_RE.findall(text)
    if not devices:
        raise RuntimeError(f"full-offload gate FAILED: no 'assigned to device' lines in {log_path}")
    cpu = [d for d in devices if d == "CPU"]
    if cpu:
        raise RuntimeError(f"full-offload gate FAILED: {len(cpu)}/{len(devices)} layers on CPU")
    return {"layers_assigned": len(devices), "devices": sorted(set(devices))}


def ask(port: int, prompt: str, timeout: float, max_tokens: int = 256) -> dict:
    body = json.dumps({
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0, "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",
                                 data=body, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    ch = d["choices"][0]
    return {"content": ch["message"].get("content") or "",
            "reasoning_chars": len(ch["message"].get("reasoning_content") or ""),
            "finish_reason": ch.get("finish_reason"),
            "usage": d.get("usage", {}),
            "wall_s": round(time.time() - t0, 1)}


def main() -> int:
    ap = argparse.ArgumentParser(
        description="E35 long-context needle-at-depth quality eval (local llama-server or a cloud API).",
        epilog=("examples:\n"
                "  run_longctx_eval.py --model /opt/models/staging/X.gguf --label x --out results/e35/x.json\n"
                "  run_longctx_eval.py --provider openrouter --model deepseek/deepseek-v4.1-flash "
                "--label v41f --out results/eNNN/v41f.json --lengths 8192,32768 --max-tokens 8192"),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True,
                    help="GGUF path for --provider local, or the API model id for a cloud provider")
    ap.add_argument("--provider", default="local", choices=["local", "mistral", "openrouter"])
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lengths", default="8192,32768,65536,131072")
    ap.add_argument("--max-tokens", type=int, default=256,
                    help="answer budget per question (default 256, the E35 value). A reasoning "
                         "cloud model can spend 256 on its chain and return nothing - raise it")
    ap.add_argument("--usd-ceiling", type=float, default=5.0,
                    help="cloud only: stop the run once spend reaches this (default $5)")
    ap.add_argument("--server-bin", default=os.environ.get("SPARKBENCH_SERVER_BIN", DEFAULT_SERVER))
    ap.add_argument("--port", type=int, default=8120)
    ap.add_argument("--load-timeout", type=float, default=900.0)
    ap.add_argument("--request-timeout", type=float, default=3600.0)
    args = ap.parse_args()

    cloud = args.provider != "local"
    budget = None
    if cloud:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from cloud_client import CloudBudget, chat  # noqa: PLC0415 - cloud path only
        budget = CloudBudget(usd_ceiling=args.usd_ceiling)

        def cloud_chat(text: str, max_tokens: int = 16) -> dict:
            # retries=6 walks the full 429/503 ladder, as run_ps_eval does.
            return chat(args.model, [{"role": "user", "content": text}], budget,
                        provider=args.provider, temperature=0, max_tokens=max_tokens,
                        timeout=args.request_timeout, retries=6)

        # One counter for the whole run: the template overhead is a property
        # of the model, measured once.
        cloud_count = make_cloud_counter(cloud_chat)
    else:
        # Rule 9, applied only where it bites: a cloud arm uses no GPU.
        for p in ("llama-server", "llama-bench"):
            if subprocess.run(["pgrep", "-x", p], capture_output=True, text=True).stdout.strip():
                print(f"FAIL: {p} already running - a contended run is void (Rule 9)", file=sys.stderr)
                return 2

    lengths = [int(x) for x in args.lengths.split(",")]
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    legs = []

    for target in lengths:
        leg = {"target_tokens": target, "results": []}
        proc = log_f = None
        if cloud:
            print(f"\n=== {args.label} ({args.provider}) @ target {target} tokens ===", flush=True)
        else:
            # -c must cover corpus + question + answer with headroom; -np 1 so -c
            # is NOT divided (F20). +4096 covers the needles, prompt and reply.
            ctx = target + 4096
            leg["ctx"] = ctx
            log_path = out_path.with_suffix(f".{target}.serverlog")
            cmd = [args.server_bin, "-m", args.model, "-c", str(ctx), "-np", "1",
                   "--host", "127.0.0.1", "--port", str(args.port), "--no-webui", "-v"]
            print(f"\n=== {args.label} @ target {target} tokens (-c {ctx}) ===", flush=True)
            log_f = log_path.open("w")
            proc = subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)
        try:
            if cloud:
                leg["offload_gate"] = {"skipped": "cloud arm - no local offload to gate"}
                body, _ = build_corpus_cloud(cloud_count, target)
                body = insert_needles(body)
                corpus_tokens = cloud_count(body)
                if corpus_tokens < int(target * 0.80):
                    raise RuntimeError(f"corpus with needles measured {corpus_tokens} tokens against "
                                       f"target {target}. hint: a leg must not be labelled with a "
                                       f"length it did not reach")
                leg["corpus_tokens_measured"] = corpus_tokens
            else:
                wait_healthy(args.port, args.load_timeout)
                leg["offload_gate"] = assert_full_offload(log_path)
                body, actual = build_corpus(args.port, target)
                body = insert_needles(body)
                leg["corpus_tokens_measured"] = count_tokens(args.port, body)
                corpus_tokens = None  # llama-server refuses an oversized prompt; no silent trim
            print(f"corpus: {leg['corpus_tokens_measured']} tokens (target {target})", flush=True)
            for frac, name, value in NEEDLES:
                q = (f"{body}\n\n---\nUsing ONLY the document above, state the {name} calibration "
                     f"constant. Reply with the number and nothing else.")
                t0 = time.time()
                try:
                    if cloud:
                        resp = cloud_chat(q, max_tokens=args.max_tokens)
                    else:
                        resp = ask(args.port, q, args.request_timeout, args.max_tokens)
                except Exception as exc:  # noqa: BLE001 - one depth must not kill the leg
                    if cloud and "budget ceiling" in str(exc):
                        raise
                    leg["results"].append({"depth": frac, "needle": name, "outcome": "transport_failed",
                                           "detail": str(exc), "wall_s": round(time.time() - t0, 1)})
                    print(f"  depth {frac:>4}: transport_failed {exc}", flush=True)
                    continue
                prompt_tokens = resp["usage"].get("prompt_tokens")
                outcome = classify_outcome(resp["content"], resp["finish_reason"], value,
                                           prompt_tokens=prompt_tokens, corpus_tokens=corpus_tokens)
                row = {
                    "depth": frac, "needle": name, "expected": value, "outcome": outcome,
                    "answer": resp["content"][:200], "wall_s": resp["wall_s"],
                    "prompt_tokens": prompt_tokens,
                    "reasoning_chars": resp["reasoning_chars"],
                }
                if cloud:
                    row["completion_tokens"] = resp["usage"].get("completion_tokens")
                    row["cost_usd_reported"] = resp["usage"].get("cost")
                leg["results"].append(row)
                print(f"  depth {frac:>4} {name:9s}: {outcome:17s} {resp['wall_s']}s "
                      f"({prompt_tokens} prompt tok)", flush=True)
        except Exception as exc:  # noqa: BLE001 - a failed length must not kill the sweep
            leg["error"] = str(exc)
            print(f"LEG FAILED at {target}: {exc}", file=sys.stderr, flush=True)
            if cloud and "budget ceiling" in str(exc):
                legs.append(leg)
                break
        finally:
            if proc is not None:
                proc.terminate()
                try:
                    proc.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=60)
                log_f.close()
        passed = sum(1 for r in leg["results"] if r.get("outcome") == "pass")
        leg["passed"] = passed
        leg["total"] = len(leg["results"])
        print(f"--- {target}: {passed}/{len(leg['results'])} needles found", flush=True)
        if cloud:
            print(f"    spend so far: ${budget.usd_est:.4f} over {budget.calls} calls", flush=True)
        legs.append(leg)
        if not cloud:
            time.sleep(5)

    summary = {"label": args.label, "model": args.model, "provider": args.provider,
               "max_tokens": args.max_tokens,
               "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "legs": legs}
    if cloud:
        summary["budget"] = budget.as_dict()
    else:
        summary["server_bin"] = args.server_bin
        summary["kernel"] = os.uname().release
    out_path.write_text(json.dumps(summary, indent=2))
    print(f"\nwritten: {out_path}")
    for leg in legs:
        print(f"  {leg['target_tokens']:>7}: {leg.get('passed', 0)}/{leg.get('total', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
