# File: grade_heldout_subagent.py
# Purpose: grade subagent-transport held-out depth arms with the repo's OWN multiturn grader.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: mirrors run_multiturn_eval.py's grading path exactly - parse_response
# then grade_multiturn against the same turn["expect"] block - and rebuilds the
# crossover anchors the way that runner does, so the shallow/deep pairing is not
# re-derived here. Only the transport differed; nothing about scoring should.
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "spikes" / "ps-eval"))

import conversation_heldout as H  # noqa: E402
from grade_multiturn import grade_multiturn  # noqa: E402
from questions import parse_response  # noqa: E402

answers = [
    json.loads(x) for x in Path(sys.argv[1]).read_text().splitlines() if x.strip()
]
by_arm: dict[str, dict[int, dict]] = {}
for a in answers:
    by_arm.setdefault(a["arm"], {})[a["i"]] = a

arms = {}
for order in ("ab", "ba"):
    turns = H.build_turns(order)
    got = by_arm.get(order, {})
    graded = []
    for i, t in enumerate(turns):
        if not t.get("probe"):
            continue  # delivery turns are not graded
        if i not in got:
            graded.append(
                {
                    "id": t["id"],
                    "probe": t["probe"],
                    "outcome": "NOT_RUN",
                    "answer": None,
                    "citation": None,
                    "tool_uses": None,
                }
            )
            continue
        answer, citation = parse_response(got[i]["raw"])
        graded.append(
            {
                "id": t["id"],
                "probe": t["probe"],
                "outcome": grade_multiturn(t, answer),
                "answer": answer,
                "citation": citation,
                "tool_uses": got[i]["tool_uses"],
                "wall_s": round(got[i]["duration_ms"] / 1000, 2),
            }
        )
    arms[order] = graded

print(f"{'id':5s} {'probe':8s} | {'AB outcome':17s} {'BA outcome':17s}")
print("-" * 56)
held_out = [q for q in arms["ab"] if q["probe"] in ("shallow", "deep")]
for order in ("ab", "ba"):
    n = sum(1 for r in arms[order] if r["outcome"] == "correct")
    tot = len(arms[order])
    print(
        f"  {order.upper()}: {n}/{tot} correct   "
        f"outcomes: {json.dumps({o: sum(1 for r in arms[order] if r['outcome'] == o) for o in sorted({r['outcome'] for r in arms[order]})})}"
    )

# crossover: each held-out question appears shallow in one order, deep in the other
idx = {order: {r["id"]: r for r in arms[order]} for order in arms}
print("\ncrossover anchors (shallow -> deep, joined across orders):")
for qid in H.HELD_OUT_IDS:
    a, b = idx["ab"].get(qid), idx["ba"].get(qid)
    if not a or not b:
        continue
    sh = a if a["probe"] == "shallow" else b
    dp = a if a["probe"] == "deep" else b
    flag = "" if sh["outcome"] == dp["outcome"] else "   <- DIFFERS"
    print(f"  {qid:4s} shallow={sh['outcome']:17s} deep={dp['outcome']:17s}{flag}")

Path(sys.argv[2]).write_text(json.dumps(arms, indent=2))
print(f"\nwritten {sys.argv[2]}")
