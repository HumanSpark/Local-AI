#!/usr/bin/env python3
# File: real_quality_run.py
# Purpose: Weekend "is it actually any good?" run - real professional use cases, quality-judged.
# Project: sparkbench | Date: 2026-07-12
#
# Overview: Answers the solicitor's question ("it drafts a letter in 20 seconds, but is it any
# GOOD?") by generating real drafting/summarising/extraction outputs from local + cloud models
# over realistic legal documents, then judging each on a quality RUBRIC (faithfulness,
# completeness, tone, usability, overall) with an INDEPENDENT frontier judge (claude-opus-4.8 -
# not one of the comparators), plus a blind local-vs-frontier pairwise preference. Loops until a
# stop time for variance + a soak/reliability signal. HARNESS-RULES: HTTP via llama-server only,
# timeouts on every call, one model on GPU at a time (gateway paused by the wrapper), banks each
# iteration to forge. All raw outputs are saved for human review - the rubric is the scalable
# proxy; your own eyes on results/real-quality/samples-*.md are the ground truth.
# Usage: run under tools/run_real_quality.sh (which pauses the gateway and restores on exit).

from __future__ import annotations

import datetime
import json
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path("/home/agent-spark/sparkbench")
SERVER = ROOT / "llama.cpp/build/bin/llama-server"
DATA = ROOT / "spikes/deep-eval/data"
OUT = ROOT / "results/real-quality"
PORT = 8100
STOP = datetime.datetime(2026, 7, 13, 8, 0, 0)  # Monday morning

LOCAL_MODELS = [
    ("qwen3-30b-workhorse", "/opt/models/staging/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf"),
    ("mistral-24b-q4-best", "/opt/models/staging/Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf"),
]
# (name, provider, model-id). provider in {openrouter, mistral}.
CLOUD_MODELS = [
    ("gpt-5.4-mini", "openrouter", "openai/gpt-5.4-mini"),
    ("gpt-5.6-sol", "openrouter", "openai/gpt-5.6-sol"),
    ("mistral-large-2512", "mistral", "mistral-large-2512"),
]
JUDGE = ("openrouter", "anthropic/claude-opus-4.8")  # independent: not a comparator
FRONTIER_FOR_PAIRWISE = "gpt-5.6-sol"  # best local is judged head-to-head against this
BEST_LOCAL_FOR_PAIRWISE = "mistral-24b-q4-best"


def vaultval(key: str) -> str:
    """The vaulted value, or "" when the vault cannot answer.

    Empty is a documented outcome the callers already branch on (see the
    `if not OPENROUTER_KEY` guard below): a host with no vault, or no recipient
    identity, skips the cloud arms rather than failing the whole run.
    """
    r = subprocess.run(
        ["python3", "/opt/sparkvault/tools/vault_get.py", key],
        capture_output=True, text=True,
    )
    return r.stdout if r.returncode == 0 else ""


# Was `~/.config/openrouter.env`, DELETED on 2026-08-18 - so this read "" and every
# OpenRouter arm ran keyless without saying so. The per-app vault key is authoritative;
# the old file is not re-created. Same for mistral.
OPENROUTER_KEY = vaultval("SPARKBENCH_OPENROUTER_API_KEY")
# The `or envval(~/.config/mistral.env, ...)` tail that used to sit here was dead in
# both directions: the file does not exist on sparkline or sparkmax (checked
# 2026-08-21), so it could only ever return "", and if it HAD returned something it
# would have masked a vault failure behind a stale plaintext copy - the failure mode
# credential-handling.md names. The comment above already claimed "same for mistral";
# now the code agrees with it.
MISTRAL_KEY = vaultval("SPARKBENCH_MISTRAL_API_KEY")


def doc(name: str) -> str:
    return (DATA / name).read_text()


# Real professional use cases. doc=None -> generative task (no source document).
TASKS = [
    ("draft-client-letter-delay",
     "You are a solicitor. Using the case notes below, draft a short, professional letter to the "
     "client updating them on a delay in their matter: explain the reason for the delay, reassure "
     "them, and set out the next steps and a realistic timeframe. Warm but professional.\n\n{doc}",
     "case-notes.txt"),
    ("summarise-agreement-plain",
     "Summarise the following agreement in plain English for a non-lawyer client, in under 250 "
     "words, covering the key obligations, the term, and any risks the client should note.\n\n{doc}",
     "long-agreement.txt"),
    ("extract-engagement-terms",
     "Extract, as a clear bulleted list, the parties, the fee arrangement, the key dates or "
     "deadlines, and the termination terms from the following engagement letter.\n\n{doc}",
     "contract.txt"),
    ("attendance-note",
     "Write a formal attendance note (file note) from the following record of a client meeting, "
     "in the style a solicitor would place on the file.\n\n{doc}",
     "attendance-source.txt"),
    ("review-flag-clauses",
     "Review the following agreement and list the clauses the client should pay particular "
     "attention to before signing, each with a one-line reason why it matters to them.\n\n{doc}",
     "long-agreement.txt"),
    ("client-email-chase",
     "Draft a polite but firm email to the client requesting the outstanding information or "
     "documents referenced in the case notes below, so their matter can proceed.\n\n{doc}",
     "case-notes.txt"),
    ("explain-terms-plain",
     "Explain, in plain English a non-lawyer would understand, what the fee and termination terms "
     "in the following engagement letter mean for the client in practice.\n\n{doc}",
     "contract.txt"),
    ("status-update",
     "Write a short status update to the client summarising where their matter currently stands "
     "and what happens next, based on the case notes below.\n\n{doc}",
     "case-notes.txt"),
    ("engagement-letter-draft",
     "Draft a standard client engagement letter for a new residential conveyancing matter for a "
     "client named Sarah Byrne, purchasing a property at 14 Oakfield Road, Galway. Include the "
     "scope of work, the fee (a fixed fee of EUR 1,200 plus VAT and outlays), and standard terms.",
     None),
    ("decline-conflict",
     "Draft a short, professional letter declining to act for a prospective client because of a "
     "conflict of interest, without disclosing any confidential details of the conflict.",
     None),
]

RUBRIC = """You are a senior solicitor assessing whether an AI-drafted work product is good enough to USE.
TASK GIVEN TO THE MODEL:
---
{task}
---
{source_block}
MODEL'S OUTPUT:
---
{output}
---
Score the output on each dimension from 1 (poor) to 5 (excellent):
- faithfulness: no invented facts; consistent with the source document where one is given, otherwise internally consistent and plausible.
- completeness: addresses everything the task asked for.
- tone: appropriate professional register for a solicitor writing to a client.
- usability: would a solicitor SEND or FILE this with only light edits? (this is the key judgement)
- overall: overall quality as a usable work product.
Reply with ONLY a JSON object, no prose, exactly:
{{"faithfulness":N,"completeness":N,"tone":N,"usability":N,"overall":N,"comment":"one short sentence"}}"""

PAIRWISE = """You are a senior solicitor. Two AI systems produced a work product for the same task. Judge which is better as a usable professional output (faithful, complete, right tone, ready to send with light edits).
TASK:
---
{task}
---
{source_block}
OUTPUT A:
---
{a}
---
OUTPUT B:
---
{b}
---
Reply with ONLY a JSON object: {{"winner":"A" or "B" or "tie","reason":"one short sentence"}}"""


def log(m: str) -> None:
    print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)


def http_json(url: str, payload: dict, headers: dict, timeout: int = 300) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def chat(url: str, model: str | None, key: str, prompt: str, max_tokens: int = 2000,
         temperature: float = 0.3) -> str:
    payload = {"messages": [{"role": "user", "content": prompt}], "temperature": temperature,
               "max_tokens": max_tokens}
    if model:
        payload["model"] = model
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    d = http_json(url, payload, headers)
    return d["choices"][0]["message"]["content"].strip()


def gen_local(prompt: str) -> str:
    return chat(f"http://127.0.0.1:{PORT}/v1/chat/completions", None, "", prompt)


def gen_cloud(provider: str, model: str, prompt: str, temperature: float = 0.3) -> str:
    if provider == "openrouter":
        return chat("https://openrouter.ai/api/v1/chat/completions", model, OPENROUTER_KEY, prompt,
                    temperature=temperature)
    return chat("https://api.mistral.ai/v1/chat/completions", model, MISTRAL_KEY, prompt,
                temperature=temperature)


def judge_rubric(task_prompt: str, source: str, output: str) -> dict:
    # Full source to the judge - truncating it makes a faithful summary of the untruncated tail
    # look like fabrication (the artifact that wrecked the first run). Deterministic judge (temp 0).
    sblock = f"SOURCE DOCUMENT (the full document the output must be faithful to):\n---\n{source}\n---\n" if source else ""
    prompt = RUBRIC.format(task=task_prompt, source_block=sblock, output=output)
    j = parse_json(gen_cloud(JUDGE[0], JUDGE[1], prompt, temperature=0.0))
    dims = ["faithfulness", "completeness", "tone", "usability"]
    if "overall" not in j and all(isinstance(j.get(d), (int, float)) for d in dims):
        j["overall"] = round(sum(j[d] for d in dims) / len(dims), 2)  # derive if judge omitted it
    return j


def judge_pairwise(task_prompt: str, source: str, a: str, b: str) -> dict:
    sblock = f"SOURCE DOCUMENT:\n---\n{source}\n---\n" if source else ""
    prompt = PAIRWISE.format(task=task_prompt, source_block=sblock, a=a, b=b)
    return parse_json(gen_cloud(JUDGE[0], JUDGE[1], prompt, temperature=0.0))


def parse_json(raw: str) -> dict:
    raw = raw.strip()
    if "```" in raw:
        raw = raw.split("```")[1].lstrip("json").strip() if raw.count("```") >= 2 else raw
    s, e = raw.find("{"), raw.rfind("}")
    if s >= 0 and e > s:
        try:
            return json.loads(raw[s:e + 1])
        except Exception:
            pass
    return {"error": "unparseable", "raw": raw[:200]}


def start_server(gguf: str) -> subprocess.Popen:
    subprocess.run(["pkill", "-x", "llama-server"], check=False)
    time.sleep(2)
    srv = subprocess.Popen([str(SERVER), "-m", gguf, "-c", "8192", "-np", "1", "--jinja",
                            "--no-webui", "--host", "127.0.0.1", "--port", str(PORT)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(180):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=2)
            return srv
        except Exception:
            time.sleep(1)
    raise RuntimeError("llama-server never healthy")


def stop_server(srv: subprocess.Popen) -> None:
    srv.terminate()
    try:
        srv.wait(timeout=15)
    except Exception:
        srv.kill()
    subprocess.run(["pkill", "-x", "llama-server"], check=False)
    time.sleep(2)


def bank(iteration: int) -> None:
    for args in (["git", "-C", str(ROOT), "add", "results/real-quality/"],
                 ["git", "-C", str(ROOT), "commit", "-q", "-m",
                  f"[R&D] real-quality run: iteration {iteration} banked (weekend soak + quality)"]):
        subprocess.run(args, check=False, timeout=120)
    subprocess.run(["git", "-C", str(ROOT), "push", "-q", "origin", "main"], check=False, timeout=180)


def render_samples(iteration: int, outputs: dict) -> None:
    """Human-readable sample of full outputs for the 'is it any good' eyeball check."""
    lines = [f"# Real-quality samples - iteration {iteration}\n"]
    for tid, _, _ in TASKS[:4]:
        lines.append(f"\n## Task: {tid}\n")
        for model in ["qwen3-30b-workhorse", "mistral-24b-q4-best", "gpt-5.6-sol"]:
            o = outputs.get(model, {}).get(tid, "")
            lines.append(f"\n### {model}\n\n{o[:1500]}\n")
    (OUT / f"samples-iter{iteration:04d}.md").write_text("\n".join(lines))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not OPENROUTER_KEY:
        raise SystemExit("missing OPENROUTER_API_KEY")
    iteration = 0
    agg_path = OUT / "summary.json"
    agg = json.loads(agg_path.read_text()) if agg_path.exists() else {"iterations": 0, "models": {}}

    while datetime.datetime.now() < STOP:
        iteration += 1
        log(f"=== iteration {iteration} (stop at {STOP}) ===")
        outputs: dict = {}

        # --- generate: local models (GPU, one at a time) ---
        for name, gguf in LOCAL_MODELS:
            if datetime.datetime.now() >= STOP:
                break
            outputs[name] = {}
            try:
                srv = start_server(gguf)
                for tid, tprompt, dname in TASKS:
                    prompt = tprompt.format(doc=doc(dname)) if dname else tprompt
                    try:
                        outputs[name][tid] = gen_local(prompt)
                    except Exception as e:
                        outputs[name][tid] = f"[gen-error: {e!r}]"
                    log(f"  local {name}/{tid} done")
                stop_server(srv)
            except Exception as e:
                log(f"  LOCAL {name} failed: {e!r}")
                subprocess.run(["pkill", "-x", "llama-server"], check=False)

        # --- generate: cloud models ---
        for name, prov, mid in CLOUD_MODELS:
            outputs[name] = {}
            for tid, tprompt, dname in TASKS:
                prompt = tprompt.format(doc=doc(dname)) if dname else tprompt
                try:
                    outputs[name][tid] = gen_cloud(prov, mid, prompt)
                except Exception as e:
                    outputs[name][tid] = f"[gen-error: {e!r}]"
            log(f"  cloud {name} done")

        # --- judge: rubric per output + pairwise (workhorse vs frontier) ---
        judged: dict = {}
        for name in outputs:
            judged[name] = {}
            for tid, tprompt, dname in TASKS:
                src = doc(dname) if dname else ""
                out = outputs[name].get(tid, "")
                try:
                    judged[name][tid] = judge_rubric(tprompt, src, out)
                except Exception as e:
                    judged[name][tid] = {"error": repr(e)}
        pairwise = {}
        for tid, tprompt, dname in TASKS:
            src = doc(dname) if dname else ""
            a = outputs.get(BEST_LOCAL_FOR_PAIRWISE, {}).get(tid, "")
            b = outputs.get(FRONTIER_FOR_PAIRWISE, {}).get(tid, "")
            try:
                pairwise[tid] = judge_pairwise(tprompt, src, a, b)  # A=local, B=frontier
            except Exception as e:
                pairwise[tid] = {"error": repr(e)}

        # --- persist + aggregate ---
        rec = {"iteration": iteration, "ts": datetime.datetime.now().isoformat(),
               "outputs": outputs, "judged": judged, "pairwise_local_vs_frontier": pairwise}
        (OUT / f"iter-{iteration:04d}.json").write_text(json.dumps(rec, indent=1))
        render_samples(iteration, outputs)

        for name in judged:
            dims = ["faithfulness", "completeness", "tone", "usability", "overall"]
            vals = {d: [] for d in dims}
            for tid in judged[name]:
                j = judged[name][tid]
                for d in dims:
                    if isinstance(j.get(d), (int, float)):
                        vals[d].append(j[d])
            m = agg["models"].setdefault(name, {d: [] for d in dims})
            for d in dims:
                if vals[d]:
                    m[d].append(round(sum(vals[d]) / len(vals[d]), 2))
        wins = sum(1 for v in pairwise.values() if v.get("winner") == "A")
        losses = sum(1 for v in pairwise.values() if v.get("winner") == "B")
        ties = sum(1 for v in pairwise.values() if v.get("winner") == "tie")
        agg.setdefault("pairwise_local_vs_frontier", []).append(
            {"iteration": iteration, "local_wins": wins, "frontier_wins": losses, "ties": ties})
        agg["iterations"] = iteration
        agg_path.write_text(json.dumps(agg, indent=1))
        log(f"  iteration {iteration}: local-vs-frontier wins={wins} losses={losses} ties={ties}")
        bank(iteration)

    log(f"STOP reached; {iteration} iterations complete")


if __name__ == "__main__":
    main()
