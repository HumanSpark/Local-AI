#!/usr/bin/env python3
# File: mmlu_eval.py
# Purpose: Deadlock-safe MMLU (multiple-choice world-knowledge) eval at scale.
# Project: sparkbench | Date: 2026-07-11
#
# Overview: Runs a balanced MMLU sample (question + 4 choices, answer = a letter)
# against each model via a per-model llama-server lifecycle at SMALL context
# (-c 4096 => tiny KV, deadlock-safe on near-edge weights; avoids F27's -c 32768).
# Gen is capped tiny (answer is one letter), so per-question cost is ~prompt+overhead
# regardless of model tg speed. Deterministic (temp 0), graded by the first A-D
# letter in the reply vs the correct index. Checkpoints after each model. Self-stops
# if a server never becomes healthy (no operator to recover a wedge overnight).
# A recognized benchmark at scale => a credible, discriminating score, unlike a
# 17-question suite. Usage: mmlu_eval.py <sample.json> <models-file> <out.json>
from __future__ import annotations
import json, re, subprocess, sys, time, urllib.request
from collections import defaultdict
from pathlib import Path

SERVER = "/home/agent-spark/sparkbench/llama.cpp/build/bin/llama-server"
PORT = 8199
CTX = 4096
HEALTH_TIMEOUT = 360
REQ_TIMEOUT = 60
LETTERS = ["A", "B", "C", "D"]


def vram_mb() -> int:
    try:
        out = subprocess.run(["rocm-smi", "--showmeminfo", "vram"], capture_output=True, text=True, timeout=15).stdout
        for ln in out.splitlines():
            if "Used Memory" in ln:
                return int(ln.split()[-1]) // (1024 * 1024)
    except Exception:
        pass
    return -1


def wait_idle(limit=700, timeout=150) -> bool:
    for _ in range(timeout // 5):
        mb = vram_mb()
        if 0 <= mb < limit:
            return True
        time.sleep(5)
    return False


def health_ok() -> bool:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=3)
        return True
    except Exception:
        return False


def prompt_for(q: dict) -> str:
    # Classic MMLU completion format: the letter is the next token after "Answer:".
    # We read the first-token logprobs (argmax over A/B/C/D) rather than generating -
    # fast, parse-free, and reasoning-model-agnostic (no chance to burn tokens on
    # chain-of-thought). Raw /completion => the chat template is bypassed.
    lines = [f"Question: {q['question'].strip()}", ""]
    for i, ch in enumerate(q["choices"]):
        lines.append(f"{LETTERS[i]}. {ch}")
    lines.append("Answer:")
    return "\n".join(lines)


def ask_letter(q: dict) -> str:
    body = json.dumps({
        "prompt": prompt_for(q), "n_predict": 1, "n_probs": 20, "temperature": 0,
    }).encode()
    req = urllib.request.Request(f"http://127.0.0.1:{PORT}/completion",
                                data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=REQ_TIMEOUT) as r:
        data = json.loads(r.read())
    cp = data.get("completion_probabilities") or []
    if not cp:
        # fallback: parse the generated content
        m = re.search(r"[ABCD]", (data.get("content") or "").upper())
        return m.group(0) if m else "?"
    best, best_lp = "?", -1e30
    for e in cp[0].get("top_logprobs", []):
        tok = (e.get("token") or "").strip().upper()
        if tok in ("A", "B", "C", "D") and e.get("logprob", -1e30) > best_lp:
            best, best_lp = tok, e["logprob"]
    return best


def run_model(label, path, sample, log):
    proc = subprocess.Popen(
        [SERVER, "-m", path, "--host", "127.0.0.1", "--port", str(PORT),
         "-c", str(CTX), "-np", "1", "--jinja", "--no-webui"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log(f"{label}: server pid={proc.pid} loading (-c {CTX})")
    t0 = time.time()
    while time.time() - t0 < HEALTH_TIMEOUT:
        if proc.poll() is not None:
            log(f"{label}: SERVER EXITED rc={proc.returncode} during load - skip")
            return {"label": label, "status": f"server-exit-{proc.returncode}", "score": None}
        if health_ok():
            break
        time.sleep(4)
    else:
        log(f"{label}: NEVER HEALTHY {HEALTH_TIMEOUT}s - possible wedge; kill + STOP")
        proc.kill()
        return None
    log(f"{label}: healthy in {int(time.time()-t0)}s; {len(sample)} questions")
    correct = 0
    by_subj = defaultdict(lambda: [0, 0])
    t1 = time.time()
    for i, q in enumerate(sample, 1):
        try:
            letter = ask_letter(q)
        except Exception:
            letter = "?"
        ok = (letter == LETTERS[q["answer"]])
        correct += ok
        by_subj[q["subject"]][0] += ok
        by_subj[q["subject"]][1] += 1
        if i % 100 == 0:
            log(f"{label}: {i}/{len(sample)} running score {correct}/{i}")
    dt = int(time.time() - t1)
    proc.terminate()
    try:
        proc.wait(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
    wait_idle()
    pct = round(100 * correct / len(sample), 1)
    log(f"{label}: MMLU-DONE {correct}/{len(sample)} = {pct}% ({dt}s)")
    return {"label": label, "status": "ok", "score": correct, "total": len(sample),
            "pct": pct, "by_subject": {k: v for k, v in by_subj.items()}}


def main() -> int:
    if len(sys.argv) < 4:
        sys.exit("usage: mmlu_eval.py <sample.json> <models-file> <out.json>")
    sample = json.load(open(sys.argv[1]))
    out_path = sys.argv[3]
    prog = Path(out_path).with_suffix(".log")

    def log(msg):
        with open(prog, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")

    models = []
    for ln in Path(sys.argv[2]).read_text().splitlines():
        ln = ln.strip()
        if ln and not ln.startswith("#") and "|" in ln:
            lbl, p = ln.split("|", 1)
            models.append((lbl.strip(), p.strip()))
    log(f"MMLU START {len(models)} models x {len(sample)} questions (-c {CTX})")
    if not wait_idle():
        log("WARN: GPU not idle at start")
    results = []
    for lbl, p in models:
        if not Path(p).exists():
            log(f"{lbl}: MISSING {p}")
            results.append({"label": lbl, "status": "missing", "score": None})
            continue
        res = run_model(lbl, p, sample, log)
        if res is None:
            results.append({"label": lbl, "status": "wedge-suspected", "score": None})
            log("STOPPING (possible GPU wedge, no overnight recovery)")
            break
        results.append(res)
        json.dump(results, open(out_path, "w"), indent=2)  # checkpoint
    lines = [f"# MMLU (balanced {len(sample)}-question sample, 0-shot, temp 0, -c {CTX})",
             "# Recognized multi-subject world-knowledge benchmark. Higher = better.", "",
             "| Model | MMLU score | % |", "|---|---|---|"]
    for r in sorted(results, key=lambda x: (x.get("pct") or -1), reverse=True):
        s = f"{r['score']}/{r.get('total','?')}" if r.get("score") is not None else r.get("status")
        pct = f"{r.get('pct')}%" if r.get("pct") is not None else "-"
        lines.append(f"| {r['label']} | {s} | {pct} |")
    Path(out_path).with_suffix(".md").write_text("\n".join(lines) + "\n")
    log("MMLU COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
