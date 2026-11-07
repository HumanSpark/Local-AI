# File: tools/adjudicate_dispute.py
# Purpose: Decide acoustically whether a reference transcript mis-attributed a long monologue block.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E38b found the 35-min client call was the one recording where our diarisation failed to
# beat the majority baseline (16.7% vs 15.3%). The suspect was the REFERENCE, not us: Otter gives
# speaker A an eight-minute unbroken block, inside which speaker B is visibly present in the text.
# I first said this needed a human to listen. It does not - we have a validated speaker embedder,
# so the question is answerable acoustically.
#
# Method: build a VOICEPRINT for each speaker from their UNDISPUTED turns only (short exchanges the
# reference is unambiguous about, well away from the disputed block), then classify each window
# INSIDE the disputed block against both voiceprints. If a contiguous stretch inside speaker A's
# block matches speaker B's voiceprint, the reference merged B into A's block and our detection of
# that change was scored as an error while being correct.
#
# This is only trustworthy because the extractor was validated independently on the synthetic
# fixture (embedder-validation.md) - its ability to separate voices was never in question; only the
# difficulty of the real-audio task was. The voiceprints are built from data OUTSIDE the disputed
# region, so the test cannot beg the question.

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from diarise_eval import load_reference  # noqa: E402
from spk_embed import SAMPLE_RATE as SR  # noqa: E402
from spk_embed import SpeakerEmbedder, load_wav  # noqa: E402

WINDOW_S = 3.0


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Adjudicate a disputed reference block using speaker voiceprints.",
        epilog="example: var/diar-venv/bin/python tools/adjudicate_dispute.py a.wav t.tsv "
               "--dispute-start 428 --dispute-end 915 --max-turn 90",
    )
    ap.add_argument("wav", type=Path)
    ap.add_argument("reference", type=Path)
    ap.add_argument("--dispute-start", type=float, required=True, help="seconds")
    ap.add_argument("--dispute-end", type=float, required=True, help="seconds")
    ap.add_argument("--max-turn", type=float, default=90.0,
                    help="turns longer than this are excluded from voiceprints (they may hide "
                         "the same merge bug we are testing for)")
    args = ap.parse_args()

    audio = load_wav(args.wav)
    ref = load_reference(args.reference, len(audio) / SR)
    emb = SpeakerEmbedder()

    # --- voiceprints from UNDISPUTED, SHORT turns outside the disputed window ---
    prints: dict[str, list[np.ndarray]] = {}
    for s, e, spk in ref:
        if e > args.dispute_start and s < args.dispute_end:
            continue                                    # overlaps the dispute - excluded
        if (e - s) < WINDOW_S or (e - s) > args.max_turn:
            continue                                    # too short to embed / too long to trust
        mid = (s + e) / 2
        chunk = audio[int((mid - WINDOW_S / 2) * SR) : int((mid + WINDOW_S / 2) * SR)]
        if len(chunk) < int(WINDOW_S * SR):
            continue
        if float(np.sqrt(np.mean(chunk**2))) < 1e-3:
            continue
        prints.setdefault(spk, []).append(emb.embed(chunk))

    voiceprints = {s: np.mean(v, axis=0) / np.linalg.norm(np.mean(v, axis=0))
                   for s, v in prints.items() if len(v) >= 3}
    if len(voiceprints) < 2:
        raise ValueError(
            f"need >=2 speakers with >=3 clean undisputed turns; got {list(prints)}. "
            "hint: raise --max-turn or widen the region outside the dispute."
        )

    print("Voiceprints built from UNDISPUTED turns only (outside the disputed block):")
    for s, v in voiceprints.items():
        print(f"  {s:24s} from {len(prints[s]):3d} turns")
    names = list(voiceprints)
    cross = float(voiceprints[names[0]] @ voiceprints[names[1]])
    print(f"\n  sanity: the two voiceprints score {cross:.3f} against each other "
          f"({'DISTINCT - test is meaningful' if cross < 0.5 else 'TOO SIMILAR - test is weak'})")

    who_ref = {}
    for s, e, spk in ref:
        who_ref[(s, e)] = spk
    disputed_owner = next((spk for s, e, spk in ref
                           if s <= args.dispute_start and e >= args.dispute_end), "?")
    print(f"\nReference attributes {args.dispute_start:.0f}-{args.dispute_end:.0f}s "
          f"entirely to: {disputed_owner}")
    print(f"\n{'time':>12s}  " + "  ".join(f"{n[:16]:>16s}" for n in names) + "   -> acoustic verdict")
    print("-" * 78)

    hop = 5.0
    verdicts = []
    t = args.dispute_start
    while t + WINDOW_S <= args.dispute_end:
        chunk = audio[int(t * SR) : int((t + WINDOW_S) * SR)]
        if float(np.sqrt(np.mean(chunk**2))) < 1e-3:
            t += hop
            continue
        e_w = emb.embed(chunk)
        scores = {n: float(e_w @ voiceprints[n]) for n in names}
        win = max(scores, key=scores.get)
        verdicts.append((t, win, scores))
        t += hop

    for t, win, scores in verdicts:
        mark = "" if win == disputed_owner else "   <== NOT the attributed speaker"
        print(f"{t:9.0f}s   " + "  ".join(f"{scores[n]:16.3f}" for n in names) + f"   {win}{mark}")

    other = sum(1 for _, w, _ in verdicts if w != disputed_owner)
    print("-" * 78)
    print(f"\n{other} of {len(verdicts)} windows inside the block match a DIFFERENT speaker "
          f"({100*other/len(verdicts):.0f}%)")
    if other / len(verdicts) > 0.10:
        print("\nVERDICT: the reference block is NOT one speaker. The reference merged another "
              "speaker into it,\n  so our change-detection there was scored as an ERROR while "
              "being CORRECT.")
    else:
        print("\nVERDICT: the block really is one speaker. The reference stands and the failure "
              "is OURS.")


if __name__ == "__main__":
    main()
