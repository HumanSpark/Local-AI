#!/usr/bin/env python3
# File: mtp_acceptance.py
# Purpose: Extract ACTUAL speculative-decoding draft behaviour from a llama-server log, rather than trusting the flag that was requested.
# Project: sparkbench | Date: 2026-08-19
#
# Overview: `--spec-draft-n-max N` is a request, not a guarantee. llama.cpp
# can clamp the draft length to what the draft head can actually produce, so an
# arm labelled `n-max 4` may be drafting fewer tokens per cycle, and reporting it
# as a 4-token arm would attribute a result to a setting that never took effect -
# Rule 8's failure mode with a new mechanism.
#
# `nextn_predict_layers` does NOT bound the draft length. llama.cpp's MTP drafter
# feeds the single NextN mechanism forward repeatedly and stops when the result
# reaches `n_max`, so a model with one NextN layer can still draft several
# tokens - which our own n-max 2 arm demonstrates, offering 2 from 1 layer. The
# field is reported below because it identifies the head, not because it caps
# anything.
#
# This reads the served log and reports what the server DID: the distribution of
# draft lengths actually offered, the acceptance rate, and the model's declared
# nextn layer count. Three separate facts, because they fail separately - a
# clamped draft length, a collapsed acceptance rate and a head that never loaded
# all look like "MTP did not help" from the outside.
#
# WHY ACCEPTANCE IS REPORTED AS TOKENS AND NOT AS EVENTS. An event that offers 2
# and accepts 1 is a partial win, not a loss. Counting events would make a 50%
# partial-acceptance regime look identical to a total failure, and the two have
# opposite conclusions.

from __future__ import annotations

import argparse
import collections
import re
import sys
from pathlib import Path

ACCEPT_RE = re.compile(r"accepted (\d+)/(\d+) draft tokens")
NEXTN_RE = re.compile(r"nextn_predict_layers\s+u32\s+=\s+(\d+)")
INIT_RE = re.compile(r"creating (\w+) draft context")
UNUSED_RE = re.compile(r"unused tensor.*nextn")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Actual MTP draft behaviour from a llama-server log.",
        epilog="example: python3 tools/mtp_acceptance.py "
               "results/raw/e59mtp2-20260819-qwen38-ab.serverlog",
    )
    ap.add_argument("logs", nargs="+")
    ap.add_argument("--n-max", type=int, default=None,
                    help="the --spec-draft-n-max that was REQUESTED, so the tool "
                         "can say whether llama.cpp clamped it. Without this the "
                         "offered lengths are reported without a verdict.")
    args = ap.parse_args()

    for path_s in args.logs:
        path = Path(path_s)
        if not path.exists():
            raise SystemExit(
                f"{path} does not exist. "
                f"hint: the serverlog sits beside the run JSON with a "
                f".serverlog suffix"
            )
        text = path.read_text(errors="replace")

        counts: collections.Counter = collections.Counter()
        for m in ACCEPT_RE.finditer(text):
            counts[(int(m.group(1)), int(m.group(2)))] += 1

        nextn = NEXTN_RE.search(text)
        impl = INIT_RE.search(text)
        unused = len(UNUSED_RE.findall(text))

        print(f"\n=== {path.name} ===")
        print(f"  draft implementation : {impl.group(1) if impl else 'NONE FOUND'}")
        print(f"  nextn_predict_layers : {nextn.group(1) if nextn else 'not reported'}")
        # The mechanical proof the flag engaged. Non-zero means llama.cpp loaded
        # the MTP tensors and then discarded them, i.e. speculation is OFF.
        print(f"  'unused tensor nextn' warnings : {unused}"
              f"{'   <- MTP did NOT engage' if unused else '   (0 = MTP engaged)'}")

        if not counts:
            print("  NO draft events found - either speculation is off or this "
                  "log predates the run")
            continue

        offered = sorted({d for _, d in counts})
        events = sum(counts.values())
        acc_tok = sum(a * n for (a, _), n in counts.items())
        off_tok = sum(d * n for (_, d), n in counts.items())
        # Only call it clamped against a REQUESTED value the caller supplied.
        # Judging it against a hard-coded number would report the n-max 2 arm as
        # clamped for offering exactly the 2 it asked for.
        note = ""
        if args.n_max is not None and max(offered) < args.n_max:
            note = f"   <- CLAMPED below the requested n-max {args.n_max}"
        elif args.n_max is not None:
            note = f"   (matches the requested n-max {args.n_max})"
        print(f"  draft lengths ACTUALLY offered : {offered}{note}")
        print(f"  {events:,} draft events, {off_tok:,} tokens offered, "
              f"{acc_tok:,} accepted")
        print(f"  ACCEPTANCE: {acc_tok / off_tok * 100:.1f}% of tokens "
              f"({'above' if acc_tok / off_tok > 0.6 else 'BELOW'} the 60% "
              f"threshold for speculation being worth it)")
        # Two different numbers, and conflating them understates the speedup.
        # Each verification step also emits the ordinary TARGET token, so the
        # tokens advanced per step is 1 + accepted drafts - which is llama.cpp's
        # own `mean len` semantics. Reporting only the draft figure treats the
        # free target token as if it did not happen.
        per_event = acc_tok / events
        print(f"  accepted draft tokens / event   : {per_event:.2f}")
        print(f"  EFFECTIVE tokens / verification : {1 + per_event:.2f}"
              f"   (= 1 target token + accepted drafts; llama.cpp 'mean len')")
        # NOT a ceiling. It assumes one multi-token verification costs the same
        # as one ordinary single-token decode, and llama.cpp verifies the drafted
        # tokens as a single target BATCH whose cost can differ from a one-token
        # step - especially on memory-bound hardware like this one. Calling it a
        # ceiling asserts a bound the implementation does not guarantee, which is
        # how a modelling assumption gets quoted later as a measurement.
        print(f"  idealised @ baseline-step cost  : {1 + per_event:.2f}x "
              f"(assumes a multi-token verify costs the same as one decode step; "
              f"NOT a bound)")
        for (a, d), n in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"    accepted {a}/{d}: {n:,} events ({n / events * 100:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
