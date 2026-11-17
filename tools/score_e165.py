#!/usr/bin/env python3
# File: tools/score_e165.py
# Purpose: Score E165 (test audit): every arm's original suite scores beside the corrected graders' and the re-runs'.
# Project: sparkbench | Date: 2026-11-17
#
# Overview: Arms KFL KX (E160), HS LM (E163) and Q (E164). For each, ORIGINAL is the banked score as the experiment
# reported it. CORRECTED comes two ways, and the output says which. (1) Re-graded: the same saved answers through the
# fixed graders - L5 (grade_answer_l5, GRADER_VERSION 2026-11-17.1), writing (tasks.grade), kw-eval (score_kw_eval v3),
# and the OLD conversation answers through the reordered grade_multiturn (isolates the grader change from the prompt
# change). (2) Re-run: suites whose PROMPT changed - tool use v3, mt-l4, mt-long, H6 - read from results/e165/raw/<arm>,
# graded at run time by the corrected code. Drafting: every banked draft (E162 L C G M X, E164 Q) through
# CHECKER_VERSION 2026-11-17.1, flag counts before and after. A missing re-run file is reported as "not run", never 0.
# Writes results/e165/score.json and prints the tables.

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path("/home/bench/sparkbench")
for sub in ("tools", "spikes/ps-eval", "spikes/writing-eval", "spikes/client-tasks"):
    sys.path.insert(0, str(ROOT / sub))

import score_kw_eval  # noqa: E402
import conversation_l4  # noqa: E402
import conversation_long  # noqa: E402
from grade_multiturn import grade_multiturn  # noqa: E402
from questions_l5 import QUESTIONS_L5, grade_answer_l5  # noqa: E402
import importlib.util  # noqa: E402

import tasks as client_tasks  # noqa: E402  (spikes/client-tasks is first on the path)


def _load_writing_tasks():  # two modules are named tasks.py; load the writing one by path under its own name
    spec = importlib.util.spec_from_file_location(
        "writing_tasks", ROOT / "spikes/writing-eval/tasks.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_wt = _load_writing_tasks()
WRITING_TASKS, grade_writing = _wt.TASKS, _wt.grade

ARMS = {"KFL": "e160", "KX": "e160", "HS": "e163", "LM": "e163", "Q": "e164"}
NEW = ROOT / "results/e165/raw"
OUT = ROOT / "results/e165/score.json"
L5 = {q["id"]: q for q in QUESTIONS_L5}
WRITING = {t["id"]: t for t in WRITING_TASKS}
TURNS = {
    "mt-l4": {t["id"]: t for t in conversation_l4.GRADED},
    "mt-long": {t["id"]: t for t in conversation_long.GRADED},
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def old(arm: str, suite: str) -> dict:
    return load(ROOT / f"results/{ARMS[arm]}/raw/{arm}/{suite}.json")


def tooluse_score(d: dict) -> dict:
    return {
        "tooluse": sum(r["success_rate"] >= 2 / 3 for r in d["results"]),
        "n": len(d["results"]),
        "leaks": sum(r["leak_runs"] for r in d["results"]),
        "failed": sorted(r["id"] for r in d["results"] if r["success_rate"] < 2 / 3),
    }


def conv_score(d: dict) -> dict:
    graded = [r for r in d["results"] if r["graded"]]
    return {
        "correct": sum(r["outcome"] == "correct" for r in graded),
        "n": len(graded),
        "lost": {r["id"]: r["outcome"] for r in graded if r["outcome"] != "correct"},
    }


def arm_scores(arm: str) -> dict:
    s: dict = {}
    l5 = old(arm, "l5")["results"]
    s["l5"] = {
        "original": sum(r["outcome"] == "correct" for r in l5),
        "corrected": sum(
            grade_answer_l5(L5[r["id"]], r["answer"]) == "correct" for r in l5
        ),
        "how": "re-graded",
        "n": len(l5),
    }
    w = old(arm, "writing")["results"]
    s["writing"] = {
        "original": sum(r["outcome"] == "correct" for r in w),
        "corrected": sum(
            grade_writing(WRITING[r["id"]], r["output"])[0] == "correct" for r in w
        ),
        "how": "re-graded",
        "n": len(w),
    }
    kw = ROOT / f"results/{ARMS[arm]}/raw/{arm}/kw.json"
    if kw.exists():
        rows = score_kw_eval.score_file(kw)
        orig = {"KFL": 24, "KX": 26, "HS": 26, "LM": 25}[
            arm
        ]  # as reported under scorer v2 (E160 F186, E163 F190)
        s["kw"] = {
            "original": orig,
            "corrected": rows["correct"],
            "how": "re-graded",
            "n": rows["n"],
        }
    else:
        s["kw"] = {"original": None, "corrected": None, "how": "not run (prereg)"}
    for conv in ("mt-l4", "mt-long"):
        d = old(arm, conv)
        regraded = sum(
            grade_multiturn(TURNS[conv][r["id"]], r["answer"]) == "correct"
            for r in d["results"]
            if r["graded"]
        )
        entry = {
            "original": conv_score(d)["correct"],
            "regraded_old_answers": regraded,
            "n": conv_score(d)["n"],
        }
        new = NEW / arm / f"{conv}.json"
        entry.update(
            {
                "corrected": conv_score(load(new))["correct"],
                "lost": conv_score(load(new))["lost"],
                "how": "re-run",
            }
            if new.exists()
            else {"corrected": None, "how": "not run"}
        )
        s[conv] = entry
    t_old = tooluse_score(old(arm, "tooluse"))
    new = NEW / arm / "tooluse.json"
    s["tooluse"] = {
        "original": t_old["tooluse"],
        "original_failed": t_old["failed"],
        "n": t_old["n"],
        **(
            {
                "corrected": (t := tooluse_score(load(new)))["tooluse"],
                "failed": t["failed"],
                "leaks": t["leaks"],
                "how": "re-run",
            }
            if new.exists()
            else {"corrected": None, "how": "not run"}
        ),
    }
    h_old = old(arm, "h6-date")["results"]
    new = NEW / arm / "h6-date.json"
    s["h6"] = {
        "original": sum(r["outcome"] == "correct" for r in h_old),
        "n": len(h_old),
        **(
            {
                "corrected": sum(
                    r["outcome"] == "correct" for r in load(new)["results"]
                ),
                "how": "re-run",
            }
            if new.exists()
            else {"corrected": None, "how": "not run"}
        ),
    }
    return s


def drafting() -> dict:
    out = {}
    tasks = {t["id"]: t for t in client_tasks.TASKS}
    for arm in "LCGMXQ":
        base = ROOT / ("results/e164/drafting" if arm == "Q" else "results/e162")
        before = load(base / "grade.json")[arm]["tasks"]
        flags = {"before": {}, "after": {}}
        for r in load(base / f"drafts-{arm}.json")["results"]:
            c = client_tasks.check(tasks[r["id"]], r["output"])
            for k in ("dropped_negatives", "trap_hits", "fabrication_candidates"):
                if before[r["id"]][k]:
                    flags["before"].setdefault(k, []).append(r["id"])
                if c[k]:
                    flags["after"].setdefault(k, []).append(r["id"])
        out[arm] = flags
    return out


def main() -> int:
    if not client_tasks.__file__.endswith("client-tasks/tasks.py"):
        raise RuntimeError(
            "tasks resolved to writing-eval for the client checker. hint: import order in this file"
        )
    res = {"arms": {a: arm_scores(a) for a in ARMS}, "drafting": drafting()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2, default=str))
    print(f"{'suite':10s}" + "".join(f"{a:>16s}" for a in ARMS))
    for suite in ("l5", "writing", "kw", "mt-l4", "mt-long", "tooluse", "h6"):
        cells = []
        for a in ARMS:
            e = res["arms"][a][suite]
            c = "-" if e["corrected"] is None else e["corrected"]
            cells.append(
                f"{e['original']} -> {c}" if e["original"] is not None else "not run"
            )
        print(f"{suite:10s}" + "".join(f"{x:>16s}" for x in cells))
    for a in ARMS:
        for conv in ("mt-l4", "mt-long"):
            e = res["arms"][a][conv]
            if e["regraded_old_answers"] != e["original"]:
                print(
                    f"  {a} {conv}: grader change alone moves old answers {e['original']} -> {e['regraded_old_answers']}"
                )
    print("\ndrafting flags (task ids), before -> after:")
    for arm, f in res["drafting"].items():
        print(f"  {arm}: {f['before']} -> {f['after']}")
    print(f"-> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
