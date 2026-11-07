#!/usr/bin/env python3
# File: audit_ceiling.py
# Purpose: Report, for every stored eval answer, whether it finished or was cut off - and by
#          which ceiling.
# Project: sparkbench | Date: 2026-08-12
#
# Overview: Joins each stored promptfoo JSON to its llama-server log (prompt tokens, per-slot
# context) and to its suite YAML (max_tokens), then classifies the binding constraint via
# delivery.classify_delivery(). Suite ceilings are READ from the YAML rather than hardcoded, so
# editing a suite cannot silently invalidate the audit. The eight cloud arms stored in the same
# directory are excluded by name - they run through a different provider block and their ceilings
# do not live in these files. Written to scope the F20 ceiling re-run; kept because the promptfoo
# path had no delivery status at all, which is why the E10 truncation went five weeks unnoticed.
# Plan: docs/plans/2026-08-12-closed-record-reasoning-PLAN.md task 2.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from delivery import classify_delivery, match_task, parse_serverlog

ROOT = Path(__file__).resolve().parents[2]

# Filename prefix -> suite yaml. Checked in order, so longer prefixes come first.
PREFIX_SUITE: list[tuple[str, str]] = [
    ("e10-", "e10-generation.yaml"),
    ("e9-", "e9-contradiction.yaml"),
    ("e8-", "e8-32k.yaml"),
    ("hardlong-", "hardlong.yaml"),
]
DEFAULT_SUITE = "promptfooconfig.yaml"

# Cloud/frontier arms stored alongside the local pilot runs. Their provider config is not in
# spikes/eval-pilot, so this audit has no ceiling to compare them against.
NON_PILOT = {
    "cohere-command-a",
    "command-a-plus",
    "command-a-rerun",
    "minimax-m2.7",
    "minimax-m2.7-rerun",
    "qwen3-235b-a22b",
    "qwen3-235b-a22b-rerun",
    "qwen3.5-397b-a17b",
}


def suite_ceiling(suite_dir: Path, suite_file: str) -> int:
    p = suite_dir / suite_file
    if not p.exists():
        raise FileNotFoundError(
            f"suite yaml not found: {p}; "
            f"hint: eval suites live in spikes/eval-pilot/ - see e10-generation.yaml"
        )
    doc = yaml.safe_load(p.read_text())
    return int(doc["providers"][0]["config"]["max_tokens"])


def suite_for(stem: str) -> str | None:
    """Which suite produced this run file, or None when it is not a local pilot run."""
    if stem in NON_PILOT:
        return None
    for prefix, suite in PREFIX_SUITE:
        if stem.startswith(prefix):
            return suite
    return DEFAULT_SUITE


def audit_dir(eval_dir: Path, suite_dir: Path) -> list[dict]:
    """One record per stored answer, carrying the constraint that stopped it.

    Each answer is matched to its own server-side task record by decode count. An answer with no
    serverlog, or whose decode count matches several tasks, keeps `prompt_tokens = None` and is
    classified on what remains decidable - an output-ceiling hit needs only the suite's
    max_tokens. Dropping such answers silently would make the audit look more complete than it
    is.
    """
    ceilings = {s: suite_ceiling(suite_dir, s) for _, s in PREFIX_SUITE}
    ceilings[DEFAULT_SUITE] = suite_ceiling(suite_dir, DEFAULT_SUITE)

    records: list[dict] = []
    for path in sorted(eval_dir.glob("*.json")):
        stem = path.stem
        suite = suite_for(stem)
        if suite is None:
            continue
        ceiling = ceilings[suite]
        log_path = path.with_suffix(".serverlog")
        log = (
            parse_serverlog(log_path)
            if log_path.exists()
            else {"n_ctx_slot": None, "tasks": []}
        )
        doc = json.loads(path.read_text())
        for r in doc["results"]["results"]:
            completion = r["tokenUsage"]["completion"]
            task = match_task(log["tasks"], completion)
            prompt_tokens = task["prompt_tokens"] if task else None
            records.append(
                {
                    "file": stem,
                    "suite": suite,
                    "test": r["testCase"].get("description", f"idx{r['testIdx']}"),
                    "ceiling": ceiling,
                    "completion": completion,
                    "prompt_tokens": prompt_tokens,
                    "n_ctx_slot": log["n_ctx_slot"],
                    "server_truncated": bool(task and task["server_truncated"]),
                    "matched_task": task is not None,
                    "classification": classify_delivery(
                        prompt_tokens, log["n_ctx_slot"], completion, ceiling
                    ),
                    "success": r["success"],
                }
            )
    return records


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Classify what stopped every stored eval answer.",
        epilog="Example: python3 audit_ceiling.py --eval-dir ../../results/eval-pilot",
    )
    ap.add_argument("--eval-dir", default=str(ROOT / "results/eval-pilot"))
    ap.add_argument("--suite-dir", default=str(ROOT / "spikes/eval-pilot"))
    args = ap.parse_args()

    records = audit_dir(Path(args.eval_dir), Path(args.suite_dir))
    files = {r["file"] for r in records}
    print(f"{len(records)} stored answers across {len(files)} run files\n")

    print("=== by suite ===")
    print(
        f"{'suite':<26} {'ceil':>5} {'n':>4}  ctx-exh  out-ceil  ambig  natural  unknown"
    )
    for suite in dict.fromkeys([DEFAULT_SUITE] + [s for _, s in PREFIX_SUITE]):
        sub = [r for r in records if r["suite"] == suite]
        if not sub:
            continue
        counts = {
            k: sum(1 for r in sub if r["classification"] == k)
            for k in (
                "context_exhausted",
                "output_ceiling",
                "ambiguous_ceiling",
                "natural_stop",
                "unknown",
            )
        }
        print(
            f"{suite:<26} {sub[0]['ceiling']:>5} {len(sub):>4} "
            f"{counts['context_exhausted']:>8} {counts['output_ceiling']:>9} "
            f"{counts['ambiguous_ceiling']:>6} {counts['natural_stop']:>8} "
            f"{counts['unknown']:>8}"
        )

    cut = [r for r in records if r["classification"] not in ("natural_stop", "unknown")]
    print(f"\n=== {len(cut)} answers stopped by a ceiling ===")
    for r in sorted(cut, key=lambda r: (r["classification"], r["file"])):
        print(
            f"  {r['classification']:<18} {r['file']:<28} {r['test']:<26} "
            f"{r['completion']:>5}/{r['ceiling']:<5} prompt={r['prompt_tokens']} "
            f"ctx={r['n_ctx_slot']} pass={r['success']}"
        )

    unknown = [r for r in records if r["classification"] == "unknown"]
    if unknown:
        print(f"\n=== {len(unknown)} answers with no serverlog evidence ===")
        for f in sorted({r["file"] for r in unknown}):
            print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
