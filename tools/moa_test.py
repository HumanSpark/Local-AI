#!/usr/bin/env python3
# File: moa_test.py
# Purpose: Mixture-of-Agents on the local model stable - do N diverse local proposers,
#          aggregated by a faithful local model, beat the best single local model on
#          real drafting? Training-free, exploits our diverse-model asset. Same 10 tasks
#          + frontier judge as every other quality run, so it slots into the comparison.
# Project: sparkbench | Date: 2026-07-13
# Usage: run via tools/run_moa_test.sh (gateway paused). All proposers <25GB - no edge.
#
# Overview: Phase 1 (propose) - each proposer model, loaded once, drafts all 10 tasks.
# Phase 2 (aggregate) - the aggregator (Mistral-24B, our most faithful) synthesizes the
# single best faithful version from the N anonymised drafts + the source. Phase 3 (judge)
# - frontier judge scores the aggregated output AND each proposer's own draft, so we can
# see MoA vs best-single directly. Aggregated output goes through deterministic_cleanup.

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import real_quality_run as R  # noqa: E402
import quality_pipeline as Q  # noqa: E402  (deterministic_cleanup)

OUT = R.ROOT / "results/real-quality/moa"
CTX = 16384
S = "/opt/models/staging"

# Diverse proposers (different families / architectures = different failure modes), all <25GB.
PROPOSERS = [
    ("mistral-24b", f"{S}/Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf"),
    ("qwen3-30b",   f"{S}/Qwen3-30B-A3B-Instruct-2507-Q4_K_M.gguf"),
    ("glm-4.7-flash", f"{S}/GLM-4.7-Flash-Q4_K_M.gguf"),
]
AGGREGATOR = ("mistral-24b-agg", f"{S}/Mistral-Small-3.1-24B-Instruct-2503-Q4_K_M.gguf")

AGG_TMPL = """You are a senior Irish solicitor acting as a SYNTHESISER over {n} independent drafts of the same task (plus the source document). Work in two steps, but OUTPUT ONLY the result of step 2.

STEP 1 (analyse silently - do NOT put this in your answer): identify where the drafts AGREE, where they CONTRADICT each other or the source, and what any of them is MISSING. Every fact, name, date and figure in the final MUST be supported by the source document; discard anything invented or unverifiable, and resolve every contradiction in favour of the source.

STEP 2 (this is your entire answer): produce the single best final work product - the most faithful, complete and correctly-formatted version a solicitor would send with only light edits. No preamble, no commentary, no mention of the drafts or of your analysis.

TASK:
---
{task}
---
{source_block}{drafts}

FINAL work product:"""


def gen(prompt: str, temp: float = 0.3) -> str:
    return R.chat(f"http://127.0.0.1:{R.PORT}/v1/chat/completions", None, "", prompt,
                  max_tokens=2500, temperature=temp)


def start_server(gguf: str, load_timeout: int = 300) -> subprocess.Popen:
    subprocess.run(["pkill", "-x", "llama-server"], check=False)
    time.sleep(2)
    srv = subprocess.Popen([str(R.SERVER), "-m", gguf, "-c", str(CTX), "-np", "1", "--jinja",
                            "--no-webui", "--host", "127.0.0.1", "--port", str(R.PORT)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(load_timeout):
        if srv.poll() is not None:
            raise RuntimeError(f"llama-server exited during load (code {srv.returncode})")
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{R.PORT}/health", timeout=2)
            R.log(f"  server healthy after {i}s")
            return srv
        except Exception:
            time.sleep(1)
    raise RuntimeError("server never healthy")


def sblock(src: str) -> str:
    return f"SOURCE DOCUMENT (be faithful to this):\n---\n{src}\n---\n" if src else ""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    reaggregate = len(sys.argv) > 1 and sys.argv[1] == "reaggregate"
    if reaggregate:
        # Reuse saved proposals (the expensive phase); re-run only aggregation + judging
        # with the current (improved) aggregator prompt. Proposals are aggregator-agnostic.
        prev = json.loads((OUT / "moa.json").read_text())
        proposals = prev["proposals"]
        R.log(f"=== REAGGREGATE: reusing {len(proposals)} saved proposal sets ===")
    else:
        # Phase 1: proposals (each proposer loaded once, drafts all tasks)
        proposals = {name: {} for name, _ in PROPOSERS}
        for name, gguf in PROPOSERS:
            R.log(f"=== PROPOSER {name} ===")
            srv = start_server(gguf)
            try:
                for tid, tp, dn in R.TASKS:
                    p = tp.format(doc=R.doc(dn)) if dn else tp
                    t0 = time.time()
                    proposals[name][tid], _ = Q.deterministic_cleanup(gen(p), tp)
                    R.log(f"  {name}/{tid} {time.time()-t0:.0f}s")
            finally:
                R.stop_server(srv)

    # Phase 2: aggregation (faithful aggregator synthesises from anonymised drafts)
    R.log(f"=== AGGREGATOR {AGGREGATOR[0]} ===")
    srv = start_server(AGGREGATOR[1])
    aggregated = {}
    try:
        for tid, tp, dn in R.TASKS:
            src = R.doc(dn) if dn else ""
            drafts = "\n".join(f"DRAFT {i+1}:\n---\n{proposals[n][tid]}\n---"
                               for i, (n, _) in enumerate(PROPOSERS))
            prompt = AGG_TMPL.format(n=len(PROPOSERS), task=tp, source_block=sblock(src), drafts=drafts)
            t0 = time.time()
            aggregated[tid], _ = Q.deterministic_cleanup(gen(prompt), tp)
            R.log(f"  agg/{tid} {time.time()-t0:.0f}s")
    finally:
        R.stop_server(srv)

    # Phase 3: judge aggregated + each proposer (frontier), same rubric
    R.log("  judging (frontier)...")
    task_of = {t[0]: t for t in R.TASKS}
    arms = {"moa_aggregated": aggregated, **{f"prop_{n}": proposals[n] for n, _ in PROPOSERS}}
    judged = {a: {} for a in arms}
    for a, outs in arms.items():
        for tid, out in outs.items():
            _, tp, dn = task_of[tid]
            src = R.doc(dn) if dn else ""
            try:
                judged[a][tid] = R.judge_rubric(tp, src, out)
            except Exception as e:
                judged[a][tid] = {"error": repr(e)}

    def mean(a: str, dim: str) -> float:
        v = [judged[a][t][dim] for t in judged[a] if isinstance(judged[a][t].get(dim), (int, float))]
        return round(sum(v) / len(v), 2) if v else 0.0

    dims = ["usability", "faithfulness", "completeness", "tone", "overall"]
    summary = {a: {d: mean(a, d) for d in dims} for a in arms}
    (OUT / "moa.json").write_text(json.dumps(
        {"proposers": [n for n, _ in PROPOSERS], "aggregator": AGGREGATOR[0],
         "summary": summary, "proposals": proposals, "aggregated": aggregated,
         "judged": judged}, indent=1))

    print("\n=== MIXTURE-OF-AGENTS (local stable, frontier-judged) ===")
    print(f"  {'arm':20s} {'use':>5s} {'faith':>6s} {'compl':>6s} {'tone':>5s} {'overall':>8s}")
    for a in ["moa_aggregated"] + [f"prop_{n}" for n, _ in PROPOSERS]:
        s = summary[a]
        print(f"  {a:20s} {s['usability']:5.2f} {s['faithfulness']:6.2f} {s['completeness']:6.2f} "
              f"{s['tone']:5.2f} {s['overall']:8.2f}")
    best_prop = max((summary[f"prop_{n}"]["usability"] for n, _ in PROPOSERS))
    moa = summary["moa_aggregated"]["usability"]
    print(f"  --> MoA usability {moa:.2f} vs best single proposer {best_prop:.2f} ({moa-best_prop:+.2f})")
    print("  reference: local plateau ~3.0-3.4 | frontier gpt-5.6-sol ~4.37")


if __name__ == "__main__":
    main()
