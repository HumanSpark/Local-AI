#!/usr/bin/env python3
# File: e103_p0_control.py
# Purpose: E103's P0 control - prove reasoning_effort is INERT on ThinkingCap, not partially honoured.
# Project: sparkbench | Date: 2026-09-04
#
# Overview: ThinkingCap's chat template contains zero occurrences of
# reasoning_effort. That is strong evidence the parameter does nothing, but the
# template is not the server: llama.cpp could error on an unknown key, or a
# future build could map it. This asks the SERVER, twice, and compares
# completion_tokens. Registered threshold: inert iff both requests succeed and
# the token counts differ by less than 5%.
#
# Equal token counts confirm INERTNESS. They do not mean the model is efficient -
# that is P4's question and a different measurement entirely.

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

PROMPT = ("Implement a function that converts an integer to a Roman numeral and "
          "back, and explain your reasoning about edge cases before you write it.")
THRESHOLD = 0.05


def ask(port: int, extra: dict, timeout: float = 1800.0) -> tuple[int, str, str]:
    payload = {"messages": [{"role": "user", "content": PROMPT}],
               "temperature": 0, "max_tokens": 8192, **extra}
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode())
    m = d["choices"][0]["message"]
    text = (m.get("reasoning_content") or "") + "\n" + (m.get("content") or "")
    return (d["usage"]["completion_tokens"], d["choices"][0]["finish_reason"], text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8113)
    a = ap.parse_args()

    print("P0: does ThinkingCap honour reasoning_effort?")
    try:
        bare, fr_bare, t_bare = ask(a.port, {})
        print(f"  no parameter          : completion_tokens={bare} finish={fr_bare}")
    except urllib.error.HTTPError as e:
        print(f"  FAIL - the BARE request errored: {e}. Nothing can be concluded "
              f"about the parameter; the server or model is the problem.")
        return 2

    try:
        low, fr_low, t_low = ask(a.port, {"reasoning_effort": "low"})
        print(f"  reasoning_effort=low  : completion_tokens={low} finish={fr_low}")
    except urllib.error.HTTPError as e:
        print(f"  RESULT: the server REJECTS reasoning_effort ({e}).")
        print("  That is NOT inertness - it is a hard refusal, and arm A's config "
              "must change rather than silently omitting the parameter.")
        return 3

    # A pair of generations that BOTH hit the token cap have equal
    # completion_tokens by construction, not by agreement. Comparing those
    # counts proves nothing - it is the same degenerate-equality trap that made
    # E101's C1 "pass" on two identical 3-character failures. Refuse it.
    if fr_bare == "length" and fr_low == "length":
        print(f"  INCONCLUSIVE - both generations hit the {8192}-token cap "
              f"(finish_reason=length), so their token counts are equal BY "
              f"CONSTRUCTION and cannot show whether the parameter acted.")
        print("  Falling back to the stronger comparison: the generated TEXT.")
        if t_bare == t_low:
            print("  P0 HELD on TEXT - byte-identical generations at temperature 0. "
                  "The parameter is inert.")
            print("  NOTE: inert does not mean efficient. Token efficiency is P4.")
            return 0
        print("  P0 FALSIFIED on TEXT - the generations DIFFER, so the parameter "
              "changed something. Per the registration, STOP and re-derive every "
              "config assumption in E103 before running any arm.")
        return 1

    delta = abs(low - bare) / bare if bare else 1.0
    print(f"  relative difference   : {delta:.3%} (threshold {THRESHOLD:.0%})")
    if delta < THRESHOLD:
        print("  P0 HELD - the parameter is INERT. Both arms run at the model's "
              "own default, and the arms are not effort-matched (declared).")
        print("  NOTE: inert does not mean efficient. Token efficiency is P4.")
        return 0
    print("  P0 FALSIFIED - the parameter CHANGED the generation, so the template "
          "reading was wrong. Per the registration, STOP: re-derive every config "
          "assumption in E103 before running any arm.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
