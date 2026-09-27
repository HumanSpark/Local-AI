#!/usr/bin/env python3
# File: e146_harness_config.py
# Purpose: Write one E146 arm's MLCommons edge-agentic config from the reference config, changing ONLY the fields Amendment 1 declares.
# Project: sparkbench | Date: 2026-09-25
#
# Overview: Loads endpoints/examples/11_Edge_Agentic_Example/online_edge_full_run.yaml, sets model_params.name,
# model_params.tokenizer_name (a local snapshot, so nothing is fetched from Hugging Face), the endpoint,
# report_dir and num_trajectories_to_issue, points the dataset at its absolute path, and drops the BFCL
# accuracy dataset (a performance-only run: the accuracy phase is ~3 h and out of scope). It prints every
# changed field with old -> new so the diff against the reference is in the log, and refuses to write if
# any field it did not intend to change differs. Dependencies: PyYAML (installed in the harness venv).

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import yaml

REF = Path("/home/agent-spark/atlas-e146/endpoints/examples/11_Edge_Agentic_Example/online_edge_full_run.yaml")
DATASET = Path("/home/agent-spark/atlas-e146/endpoints/examples/11_Edge_Agentic_Example/agentic_coding_2.5h.jsonl")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate an E146 harness config from the MLCommons reference config.",
        epilog="example:\n  e146_harness_config.py --name Qwen3.6-27B-Q4_K_M --tokenizer /opt/models/staging/qwen3.6-27b-nvfp4 "
        "--endpoint http://127.0.0.1:8080 --trajectories 4 --report-dir /tmp/r --out /tmp/cfg.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--name", required=True, help="served model name (model_params.name)")
    ap.add_argument("--tokenizer", required=True, help="LOCAL tokenizer directory")
    ap.add_argument("--endpoint", required=True, help="server URL, e.g. http://127.0.0.1:8080")
    ap.add_argument("--trajectories", type=int, required=True, help="num_trajectories_to_issue (reference 20)")
    ap.add_argument("--report-dir", required=True, help="where the harness writes its report")
    ap.add_argument("--out", required=True, help="config file to write")
    args = ap.parse_args()

    ref = yaml.safe_load(REF.read_text())
    cfg = copy.deepcopy(ref)
    changes: list[tuple[str, object, object]] = []

    def setp(node: dict, key: str, new: object, label: str) -> None:
        changes.append((label, node.get(key), new))
        node[key] = new

    setp(cfg["model_params"], "name", args.name, "model_params.name")
    setp(cfg["model_params"], "tokenizer_name", args.tokenizer, "model_params.tokenizer_name")
    perf = [d for d in cfg["datasets"] if d.get("type") == "performance"]
    if len(perf) != 1:
        raise SystemExit(f"expected exactly one performance dataset, found {len(perf)}. hint: the reference config changed; re-read it")
    setp(perf[0], "path", str(DATASET), "datasets[agentic_coding].path")
    setp(perf[0]["agentic_inference"], "num_trajectories_to_issue", args.trajectories, "num_trajectories_to_issue")
    dropped = [d["name"] for d in cfg["datasets"] if d is not perf[0]]
    changes.append(("datasets (accuracy dropped)", [d["name"] for d in ref["datasets"]], [perf[0]["name"]]))
    cfg["datasets"] = [perf[0]]
    changes.append(("endpoint_config.endpoints", ref["endpoint_config"]["endpoints"], [args.endpoint]))
    cfg["endpoint_config"]["endpoints"] = [args.endpoint]
    setp(cfg, "report_dir", args.report_dir, "report_dir")

    # Refuse if anything else differs from the reference: the declared change list is the whole diff.
    intended = {"model_params", "datasets", "endpoint_config", "report_dir"}
    for key in ref:
        if key not in intended and ref[key] != cfg[key]:
            raise SystemExit(f"unintended difference in '{key}'. hint: only the declared fields may change")
    for key in ref["model_params"]:
        if key not in {"name", "tokenizer_name"} and ref["model_params"][key] != cfg["model_params"][key]:
            raise SystemExit(f"unintended difference in model_params.{key}. hint: temperature, seed and max_new_tokens are fixed")

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(yaml.safe_dump(cfg, sort_keys=False))
    print(f"wrote {args.out}; changes from the reference (dropped datasets: {dropped}):")
    for label, old, new in changes:
        print(f"  {label}: {old!r} -> {new!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
