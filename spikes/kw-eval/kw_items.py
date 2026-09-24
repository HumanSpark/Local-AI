# File: spikes/kw-eval/items.py
# Purpose: The KA-H1 knowledge-work item bank, with a gate that verifies every item's ground truth against the real corpus.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: The goal names eight shapes of serious knowledge work - reading and
# comparing documents, extracting implications from several sources, finding
# conflicts between documents, summarising a complicated position, making
# recommendations, working with long context, identifying ambiguity or missing
# information, and drafting a reasoned professional response. Each item below
# names which shape it tests.
#
# EVERY ITEM CARRIES ITS EVIDENCE, AND THE GATE CHECKS IT. `evidence` is a list
# of exact substrings that must appear in the item's pack. If one is missing the
# item is REFUSED, because the answer key would then be something I remembered
# rather than something the corpus says. This is the same gate that caught two
# of my own AABR items, and it caught mistakes both times.
#
# NO TOOL SCHEMA. F94 measured the presence of a tool schema as a large,
# model-specific, non-monotonic variable - the workhorse lost three of twenty on
# a question set with no date question in it, as non-termination. An instrument
# that bakes tools into every item is no longer ranking the models.
#
# UNANSWERABLE ITEMS ARE NOT PADDING. "Identifying ambiguity or missing
# information" is one of the eight shapes, and a model that answers confidently
# from a corpus that does not settle the question has failed in the way that
# matters most for advisory work.

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kw_corpus import build_pack  # noqa: E402

CATEGORIES = (
    "compare",
    "implication",
    "conflict",
    "summarise",
    "recommend",
    "longctx",
    "ambiguity",
    "draft",
)

ITEMS: list[dict[str, Any]] = [
    {
        "id": "K01",
        "category": "compare",
        "pack": "s",
        "question": (
            "Two different amdgpu-related failures are described in this material. "
            "For EACH, state the VRAM figure observed, and say whether a hard power "
            "cycle was required."
        ),
        "expect": {
            "key": "2.00 GiB parked (power cycle required) vs 1.90 GiB never parked (no power cycle)",
            "must_contain_all": ["2.00", "1.90"],
            "must_not_say": ["both required a power cycle", "identical"],
        },
        "evidence": [
            "parks at **exactly 2.00 GiB**",
            "1.90 GiB, never parked",
            "The box was never at risk",
        ],
    },
    {
        "id": "K02",
        "category": "implication",
        "pack": "s",
        "question": (
            "A colleague proposes a monitor that raises an alarm whenever the "
            "llama-server process is in D (uninterruptible) state. Using this "
            "material, explain why that is a defect rather than a useful alarm."
        ),
        "expect": {
            "key": "D state is normal while a large model is read off disk - an ordinary "
            "page-cache wait - so the monitor alarms through every legitimate load "
            "and trains its reader to ignore it",
            "must_contain_any": [
                "folio_wait_bit_common",
                "page-cache",
                "page cache",
                "normal",
                "ordinary",
            ],
            "must_not_say": ["D state always means a deadlock"],
        },
        "evidence": ["folio_wait_bit_common", "trains its reader to ignore it"],
    },
    {
        "id": "K03",
        "category": "compare",
        "pack": "s",
        "question": (
            "Which numbered harness rule governs how many GPU consumers may run at "
            "once, and what does that rule say a contended measurement is?"
        ),
        "expect": {
            "key": "Rule 9; a contended number is VOID, not noisy",
            "must_contain_all": ["9", "VOID"],
        },
        "evidence": ["a contended number is VOID, not noisy"],
    },
    {
        "id": "K04",
        "category": "implication",
        "pack": "s",
        "question": (
            "The harness rules forbid re-creating the deadlock's known triggers "
            "during routine benching. Name the ONE trigger this material describes "
            "as confirmed, and say what the operative mechanism is said to be."
        ),
        "expect": {
            "key": "heavy disk I/O run concurrently with a near-edge GPU model load; "
            "the operative driver is memory pressure from the concurrent I/O",
            "must_contain_any": ["disk", "I/O", "IO"],
            "must_contain_all": ["memory pressure"],
        },
        "evidence": [
            "Never run heavy disk I/O concurrently with a near-edge GPU model",
            "MEMORY PRESSURE",
        ],
    },
    {
        "id": "K05",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "Based only on this material, what is the measured per-load probability "
            "that gpt-oss-120b will hang? Give the figure."
        ),
        "expect": {
            "key": "no rate is given - the fault is recorded as observed exactly "
            "once and unexplained",
            "is_unanswerable": True,
            "accept": [
                "cannot determine",
                "not stated",
                "no rate",
                "unexplained",
                "insufficient",
                "does not give",
                "once",
                "cannot be determined",
            ],
            # The trap: the material says the fault was seen ONCE. An arm that
            # divides one by something and reports a percentage has invented a
            # denominator the corpus never supplies.
            "must_not_say": ["%", "per cent", "percent"],
        },
        "evidence": ["observed exactly once", "unresolved"],
        "absent": ["one in five", "one in seven", "one in eight"],
    },
    {
        "id": "K06",
        "category": "conflict",
        "pack": "m",
        "question": (
            "This material contains advice that explicitly corrects an earlier "
            "recommendation. Identify which recommendation was corrected, and state "
            "what the correction was based on."
        ),
        "expect": {
            "key": "the conditional tool-call advice: the earlier 'Mistral only' guidance "
            "was measured on 3 tasks and inverts on 13",
            "must_contain_any": ["Mistral", "conditional"],
            "must_contain_all": ["3", "13"],
        },
        "evidence": [
            'the previous "Mistral only" advice was measured on 3 tasks and inverts on 13'
        ],
    },
    {
        "id": "K07",
        "category": "recommend",
        "pack": "m",
        "question": (
            "A client needs a statutory deadline counted across a calendar. Which "
            "model does this material tell you to use, and which does it explicitly "
            "tell you NOT to use for this?"
        ),
        "expect": {
            "key": "use Qwen3.8-27B; do not use the workhorse (Qwen3-30B-A3B) at all",
            "must_contain_all": ["Qwen3.8", "workhorse"],
            "must_not_say": ["use the workhorse"],
        },
        "evidence": ["Do **not** use the workhorse for this at all"],
    },
    {
        "id": "K08",
        "category": "compare",
        "pack": "m",
        "question": (
            "For a batch of hard coding problems, this material recommends a model "
            "and a specific setting. State the wall-time ratio against the "
            "alternative it is compared with, and both absolute wall-time figures."
        ),
        "expect": {
            "key": "94x; 6,223s against 66s",
            "must_contain_all": ["94", "6,223", "66"],
        },
        "evidence": ["94x the wall time", "6,223s against 66s"],
    },
    {
        "id": "K09",
        "category": "implication",
        "pack": "m",
        "question": (
            "This material identifies gpt-oss-120b as the strongest candidate for "
            "difficult work on one axis, while placing an operational restriction on "
            "it. State the restriction and the reason given for it."
        ),
        "expect": {
            "key": "it is disqualified from unattended use because the load/decode hang "
            "is unexplained",
            "must_contain_all": [["unattended", "supervis"], ["hang", "hung", "hangs"]],
        },
        "evidence": ["unattended"],
    },
    {
        "id": "K10",
        "category": "conflict",
        "pack": "m",
        "question": (
            "Does this material recommend Mistral-Small-24B for tool calls whose "
            "behaviour depends on a condition? Answer yes or no and give the "
            "supporting figure."
        ),
        "expect": {
            "key": "no - Mistral is the worst arm on the full set at 38%",
            "must_contain_all": ["38"],
            "must_not_say": ["yes, use Mistral", "Mistral is the best"],
        },
        "evidence": ["Mistral is the WORST arm on the full set (38%)"],
    },
    {
        "id": "K11",
        "category": "summarise",
        "pack": "m",
        "question": (
            "Summarise, in no more than four sentences, why this material argues that "
            "a latency figure on its own cannot be interpreted."
        ),
        "expect": {
            "key": "a latency number is interpretable only after establishing that the "
            "response completed the task; generated-token count is a diagnostic of "
            "non-answering",
            "must_contain_any": [
                "completed",
                "complete the task",
                "non-answer",
                "token",
                "did the work",
            ],
        },
        "evidence": ["A latency number is interpretable only after establishing"],
    },
    {
        "id": "K12",
        "category": "conflict",
        "pack": "l",
        "question": (
            "One document here is a detailed tuning playbook for a text-to-speech "
            "engine. Is the engine it tunes this project's canonical voice? Answer "
            "yes or no, name the ratified voice, and give the date it was chosen."
        ),
        "expect": {
            "key": "No. The ratified voice is Chatterbox cloning VCTK p239, chosen "
            "2026-07-26. The Kokoro document is a tuning playbook, not a decision.",
            "must_contain_all": ["Chatterbox", "p239", "2026-07-26"],
            # The trap is the document itself: it is detailed, confident, and
            # says so in its own words - "reads exactly like a settled decision".
            # An arm that answers "Kokoro" has been convinced by title and bulk
            # over a banner in the first three lines.
            "must_not_say": ["yes", "Kokoro is the canon", "Kokoro is the ratified"],
        },
        "evidence": [
            "THIS IS NOT THE CANON VOICE DECISION",
            "**Chatterbox cloning VCTK `p239`**",
            "2026-07-26",
            "reads exactly like a settled decision",
        ],
    },
    {
        "id": "K13",
        "category": "longctx",
        "pack": "l",
        "question": (
            "Two of these documents describe amdgpu failures. Name the VRAM park "
            "figure in bytes, and separately state which numbered harness rule "
            "governs how many GPU consumers may run at once."
        ),
        "expect": {
            "key": "2,147,483,648 bytes; Rule 9",
            "must_contain_all": ["2,147,483,648", "9"],
        },
        "evidence": ["2,147,483,648", "a contended number is VOID, not noisy"],
    },
    {
        "id": "K14",
        "category": "draft",
        "pack": "m",
        "question": (
            "Draft a short note (5 sentences maximum) to a colleague who wants to run "
            "a large model benchmark while a big download is in progress. Tell them "
            "whether to proceed and why, citing the specific risk."
        ),
        "expect": {
            "key": "do not proceed - heavy disk I/O concurrent with a near-edge load is "
            "the one confirmed deadlock trigger, and clearing it needs a hard "
            "power cycle",
            "must_contain_any": ["do not", "don't", "wait", "no"],
            "must_contain_all": ["power cycle"],
        },
        "evidence": [
            "hard power cycle",
            "Never run heavy disk I/O concurrently with a near-edge GPU model",
        ],
    },
    {
        "id": "K15",
        "category": "compare",
        "pack": "s",
        "question": (
            "Two models were given the same deterministic date calculator. Give the "
            "before-and-after score for EACH of them."
        ),
        "expect": {
            "key": "the fast everyday model went 0 of 6 to 4 of 6; gpt-oss-120b went "
            "5 of 6 to 4 of 6",
            "must_contain_all": [
                ["0 out of 6", "0/6", "0 of 6"],
                ["5 out of 6", "5/6", "5 of 6"],
            ],
            "must_not_say": ["both improved", "improved for both"],
        },
        "evidence": ["0 out of 6 to 4 out of 6", "5 out of 6"],
    },
    {
        "id": "K16",
        "category": "implication",
        "pack": "s",
        "question": (
            "A third experimental condition was run to isolate WHY offering a tool "
            "changed a model's behaviour. Describe that condition and state what it "
            "showed."
        ),
        "expect": {
            "key": "the model was told the tools existed but they were not attached; "
            "that changed nothing, so it is the attachment itself",
            "must_contain_all": [["attach", "attachment"]],
            "must_contain_any": ["changed nothing", "no change", "made no difference"],
        },
        "evidence": ["It is the attachment itself"],
    },
    {
        "id": "K17",
        "category": "compare",
        "pack": "s",
        "question": (
            "On twenty ordinary questions containing no dates at all, what happened to "
            "the everyday model once tools were attached? Give the score change and the "
            "number of tool calls."
        ),
        "expect": {
            "key": "14 out of 20 down to 11, with 68 tool calls",
            "must_contain_all": ["14", "11", "68"],
        },
        "evidence": ["14 out of 20 to 11", "68 tool calls"],
    },
    {
        "id": "K18",
        "category": "recommend",
        "pack": "s",
        "question": (
            "What practical consequence does this material draw for a service that "
            "offers tools on every request by default? State the price and the form it "
            "is paid in."
        ),
        "expect": {
            "key": "up to three questions in twenty for the model serving ~91% of "
            "traffic, and it is paid as NO ANSWER rather than a wrong one",
            "must_contain_all": [
                ["three", "3"],
                ["no answer", "not answer", "produced no"],
            ],
        },
        "evidence": ["paid as *no answer*"],
    },
    {
        "id": "K19",
        "category": "compare",
        "pack": "s",
        "question": (
            "Which numbered harness rule governs model downloads, and what is the "
            "name of the file each download must be recorded in before first use?"
        ),
        "expect": {
            "key": "Rule 4; manifests/MANIFEST.md",
            "must_contain_all": ["4", "manifest"],
        },
        "evidence": [
            "Rule 4: Model downloads are explicit and manifest-recorded",
            "manifests/MANIFEST.md",
        ],
    },
    {
        "id": "K20",
        "category": "ambiguity",
        "pack": "s",
        "question": (
            "What does it cost, in euros per year, to run this hardware? Answer from "
            "this material only."
        ),
        "expect": {
            "key": "the material does not give a running cost",
            "is_unanswerable": True,
            "accept": [
                "cannot determine",
                "not stated",
                "does not say",
                "no cost",
                "not given",
                "does not provide",
                "no figure",
            ],
        },
        "evidence": ["sparkmax"],
        "absent": ["euros per year", "per year", "electricity"],
    },
    {
        "id": "K21",
        "category": "recommend",
        "pack": "m",
        "question": (
            "For creating a Word document or driving office tools agentically, which "
            "model does this material recommend, and which model does it say refuses "
            "the task outright?"
        ),
        "expect": {
            "key": "Qwen3-30B-A3B; Mistral refuses without a hand-supplied tool template",
            "must_contain_all": [["Qwen3-30B", "workhorse"], ["Mistral"]],
            "must_contain_any": ["refus"],
        },
        "evidence": ["Mistral **refuses** these outright"],
    },
    {
        "id": "K22",
        "category": "implication",
        "pack": "m",
        "question": (
            "For a long advisory session with documents arriving as you go, which model "
            "is recommended? State the specific risk this material says changes over a "
            "long session - and say explicitly whether accuracy decayed."
        ),
        "expect": {
            "key": "Qwen3.8-27B; nothing decayed - what changes is resistance, the "
            "willingness to contradict you",
            "must_contain_all": [
                ["Qwen3.8"],
                ["resistance", "contradict", "push back", "adopt"],
            ],
            "must_not_say": ["accuracy decayed", "accuracy degraded"],
        },
        "evidence": ["exactly on my figure", "nothing decayed on any model"],
    },
    {
        "id": "K23",
        "category": "conflict",
        "pack": "m",
        "question": (
            "One model is described as the strongest on a document/knowledge "
            "evaluation whose strength then failed to carry over to agentic coding "
            "work. Name that model, and say what the material tells you to use "
            "instead for interactive coding."
        ),
        "expect": {
            "key": "the Qwen3-30B-A3B workhorse; use Qwen3-Coder-30B instead, with "
            "GLM-4.7-Flash as the fallback",
            "must_contain_all": [
                ["workhorse", "Qwen3-30B-A3B"],
                ["Qwen3-Coder", "Coder"],
            ],
        },
        "evidence": [
            "did not transfer to agentic coding",
            "**Qwen3-Coder-30B**, fallback **GLM-4.7-Flash**",
        ],
    },
    {
        "id": "K24",
        "category": "implication",
        "pack": "m",
        "question": (
            "If a model must fit in under 5 GiB, which one does this material recommend, "
            "and what are the TWO limits it names?"
        ),
        "expect": {
            "key": "Qwen3-8B with reasoning ON; its context tops out at 40,960 tokens "
            "against the 27B's 262,144, and enable_thinking false costs 4 points",
            "must_contain_all": [["8B"], ["40,960", "40960"]],
        },
        "evidence": ["40,960 tokens against the 27B"],
    },
    {
        "id": "K25",
        "category": "summarise",
        "pack": "m",
        "question": (
            "The R&D PROGRAMME document (not the harness rules) sets out a primary "
            "and a secondary metric that must always be reported together. Name "
            "both, and say why the secondary one cannot be quoted alone."
        ),
        "expect": {
            "key": "success-at-deadline and conditional TTCA; TTCA is undefined on a wrong "
            "answer and infinite on a hang, so a central tendency drops exactly the "
            "cases that matter",
            "must_contain_all": [
                ["success-at-deadline", "success at deadline"],
                ["ttca", "time to correct"],
            ],
        },
        "evidence": ["success-at-deadline", "conditional TTCA"],
    },
    {
        "id": "K26",
        "category": "draft",
        "pack": "m",
        "question": (
            "Draft a short note (5 sentences maximum) to a colleague who is about to put "
            "a single tokens-per-second figure in a client report. Tell them what is "
            "wrong with that and what to report instead."
        ),
        "expect": {
            "key": "tok/s is secondary and sometimes misleading; report whether the task "
            "completed, then success-at-deadline with conditional TTCA beside it",
            "must_contain_any": [
                "complet",
                "task outcome",
                "success-at-deadline",
                "correct answer",
            ],
        },
        "evidence": ["is now demonstrably secondary and sometimes actively misleading"],
    },
]


def gate(items: list[dict[str, Any]] | None = None) -> list[str]:
    """Refuse any item whose evidence is not present in its own pack.

    Returns the list of problems. An empty list means every item's ground truth
    is something the corpus actually says.
    """
    items = items if items is not None else ITEMS
    packs = {size: build_pack(size) for size in ("s", "m", "l")}
    problems: list[str] = []
    seen: set[str] = set()
    for it in items:
        if it["id"] in seen:
            problems.append(f"{it['id']}: duplicate id")
        seen.add(it["id"])
        if it["category"] not in CATEGORIES:
            problems.append(
                f"{it['id']}: unknown category {it['category']!r} (known: {CATEGORIES})"
            )
        if it["pack"] not in packs:
            problems.append(f"{it['id']}: unknown pack {it['pack']!r}")
            continue
        pack = packs[it["pack"]]
        for ev in it["evidence"]:
            if ev not in pack:
                problems.append(
                    f"{it['id']}: evidence not found in pack {it['pack']!r}: {ev!r}\n"
                    f"    hint: the answer key rests on text the corpus does not "
                    f"contain - fix the item or add the document"
                )
        exp = it["expect"]
        if not exp.get("is_unanswerable") and not any(
            k in exp for k in ("must_contain_all", "must_contain_any")
        ):
            problems.append(f"{it['id']}: answerable item with no mechanical check")
        if exp.get("is_unanswerable") and "accept" not in exp:
            problems.append(f"{it['id']}: unanswerable item with no accepted phrasings")
        # For an unanswerable item, "the corpus does not say" is a claim about
        # ABSENCE, and absence is the half a presence check cannot verify. An
        # item asserting a question is unsettled while the pack settles it
        # elsewhere would score every correct arm wrong.
        for missing in it.get("absent", []):
            if missing in pack:
                problems.append(
                    f"{it['id']}: text asserted ABSENT is present in pack "
                    f"{it['pack']!r}: {missing!r}\n"
                    f"    hint: the item claims the corpus does not settle this, "
                    f"but it does - the item is wrong, not the model"
                )
    return problems


def category_counts(items: list[dict[str, Any]] | None = None) -> dict[str, int]:
    items = items if items is not None else ITEMS
    out: dict[str, int] = {}
    for it in items:
        out[it["category"]] = out.get(it["category"], 0) + 1
    return out


def load_items(pack: str | None = None) -> list[dict[str, Any]]:
    """Items, gated. Refuses to hand back a bank that does not pass its own gate."""
    problems = gate()
    if problems:
        raise ValueError(
            "item bank failed its ground-truth gate:\n  "
            + "\n  ".join(problems)
            + "\nhint: every item's evidence must appear verbatim in its pack"
        )
    return [it for it in ITEMS if pack is None or it["pack"] == pack]


if __name__ == "__main__":
    probs = gate()
    print(f"{len(ITEMS)} items, categories: {category_counts()}")
    by_pack: dict[str, int] = {}
    for i in ITEMS:
        by_pack[i["pack"]] = by_pack.get(i["pack"], 0) + 1
    print(f"by pack: {by_pack}")
    print(
        f"unanswerable: {sum(1 for i in ITEMS if i['expect'].get('is_unanswerable'))}"
    )
    if probs:
        print(f"\nGATE REFUSED {len(probs)} problem(s):")
        for p in probs:
            print(f"  {p}")
        sys.exit(1)
    print("\nGATE PASSED - every item's evidence is present in its own pack")
