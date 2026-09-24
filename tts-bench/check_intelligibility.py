#!/usr/bin/env python3
# File: tts-bench/check_intelligibility.py
# Purpose: Gate TTS renders on whether they are actually intelligible English, by ASR-vs-known-text WER.
# Project: sparkbench | Date: 2026-07-26
#
# Overview: Written because three garbled renders were shipped to the owner as candidates. Every
# existing screen passed them - duration 9.80s, 2.65 words/sec, mean -23.5 dB, sane flat factor -
# because those screens answer "does audio exist at a sane level", not "is this speech". A confidently
# fluent-sounding gibberish render satisfies all of them.
#
# WHY ASR IS LEGITIMATE HERE, when F44/F50 warn it lies: those incidents used ASR to decide whether
# near-silence contained speech, and Whisper hallucinated words onto a -48 dB noise floor. This does
# the opposite - it compares a transcript against text we ALREADY KNOW was requested, and asks whether
# they match. A hallucination makes the WER worse, not better, so the failure mode pushes toward
# rejecting a bad render rather than accepting one. The check is only ever used to REJECT, never as
# evidence that a render is good: low WER means intelligible, not well-spoken. Quality stays a human
# judgement.
#
# Data flow: run INSIDE the f5-tts container (it already carries a transformers ASR pipeline and the
# cached openai/whisper-large-v3-turbo weights) -> transcribe each render -> normalise both sides ->
# word-level edit distance -> WER. Above --max-wer the render is reported GARBLED and the exit code is
# non-zero, so a caller cannot ship it by ignoring stdout.
from __future__ import annotations

import argparse
import re
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from speakable import speakable  # noqa: E402


def normalise(text: str) -> list[str]:
    """Lowercase, spell numerals, strip punctuation and collapse whitespace, so WER measures WORDS.

    The `speakable` pass is applied to BOTH sides and it is not optional. Whisper renormalises spoken
    numbers back into numerals: a render that correctly says "the nineteenth of July, twenty twenty-six"
    transcribes as "the 19th of july 2026". Comparing a spelled-out reference against that numeralised
    hypothesis is not a like-for-like comparison, and it inflated a real 987-word narration from WER 0.01
    to 0.11 - pure measurement artefact.

    That inflation matters beyond tidiness: it DESENSITISES the gate. A genuinely garbled paragraph can
    hide inside a baseline of self-inflicted error, and this check exists precisely to catch garbling.
    Running both sides through the same speakable() pass makes "19th"/"nineteenth" and "2026"/"twenty
    twenty-six" agree, whichever side they came from.
    """
    t = speakable(text).lower().replace("’", "'").replace("—", " ")
    t = t.translate(str.maketrans("", "", string.punctuation.replace("'", "")))
    return [w for w in re.split(r"\s+", t) if w]


def wer(ref: list[str], hyp: list[str]) -> float:
    """Word error rate by Levenshtein distance. Own implementation to avoid a container dependency."""
    if not ref:
        raise ValueError(
            "Empty reference text - cannot compute WER. "
            "hint: pass the exact line the engine was asked to say via --expected."
        )
    prev = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        cur = [i] + [0] * len(hyp)
        for j, h in enumerate(hyp, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (r != h))
        prev = cur
    return prev[len(hyp)] / len(ref)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Reject TTS renders that are not intelligible English, by ASR-vs-expected WER.",
        epilog="example (inside the f5-tts container):\n"
               "  ./check_intelligibility.py --expected \"the line that was requested\" a.wav b.wav\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--expected", required=True, help="the exact text the engine was asked to speak")
    ap.add_argument("--max-wer", type=float, default=0.5,
                    help="above this the render is GARBLED (default 0.5 - generous, aimed at gibberish "
                         "rather than at small ASR slips)")
    ap.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args()

    missing = [f for f in args.files if not f.is_file()]
    if missing:
        raise FileNotFoundError(
            f"Render(s) not found: {[str(m) for m in missing]}. "
            f"hint: engine audio is gitignored and exists only on the box that rendered it."
        )

    import torch
    from transformers import pipeline

    dev = "cuda" if torch.cuda.is_available() else "cpu"
    asr = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3-turbo",
                   torch_dtype=torch.float16 if dev == "cuda" else torch.float32, device=dev)

    ref = normalise(args.expected)
    print(f"expected ({len(ref)} words): {' '.join(ref)}\n")

    failed = []
    for f in args.files:
        # Whisper's NATIVE long-form decoding, not the pipeline's chunk_length_s sliding window.
        # The window silently DROPPED a contiguous 72-word run from a 5.7-minute narration - 7% of the
        # file - and the gate charged it as error, giving WER 0.09 on audio that was fully intact
        # (proved by transcribing that exact 8-44s slice on its own, where every word was present).
        # Two harms, and the second is the dangerous one: spurious failures on long files, and an
        # inflated baseline that a genuinely garbled paragraph can hide inside. transformers warns
        # about chunk_length_s on seq2seq models in the log on every run; it was right.
        out = asr(str(f), return_timestamps=True,
                  generate_kwargs={"task": "transcribe", "language": "en"})["text"].strip()
        hyp = normalise(out)
        score = wer(ref, hyp)
        verdict = "GARBLED" if score > args.max_wer else "ok"
        if verdict == "GARBLED":
            failed.append(f.name)
        print(f"{f.name:34s} WER {score:5.2f}  {verdict}")
        print(f"    heard: {' '.join(hyp)[:150] or '(nothing)'}")

    if failed:
        print(f"\n{len(failed)} render(s) rejected as not intelligible: {failed}")
        print("hint: these must NOT be presented as engine output. A garbled render passes every "
              "duration/level/flat-factor screen, which is exactly why this gate exists.")
        return 1
    print(f"\nall {len(args.files)} render(s) intelligible (WER <= {args.max_wer})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
