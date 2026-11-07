# File: tools/wer_bench.py
# Purpose: Measure transcription DISAGREEMENT vs an Otter.ai reference, across models/configs.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E41 measured what whisper does with SILENCE and found the failure MODE inverts with
# model size (small emits self-declaring [BLANK_AUDIO]; large emits plausible "Thank you."). It said
# NOTHING about transcription accuracy on actual speech - every E41 fixture was silent. This is the
# missing half: does model size change quality on real speech, and by how much?
#
# WHAT THIS MEASURES - AND WHAT IT CANNOT
# The reference is an Otter.ai transcript, which Alastair estimates at ~98% accurate (2026-07-17).
# So this is NOT word error rate against truth: it is a DISAGREEMENT RATE with Otter, and it carries
# a FLOOR of roughly Otter's own error (~2%). A PERFECT transcript would still score ~2% here, by
# correctly differing from Otter's mistakes. Consequences, stated up front so nobody reads the
# number as accuracy:
#   - The absolute number is an upper bound on true WER, not an estimate of it.
#   - Comparing two models is still valid (same reference, same floor) but the gap is COMPRESSED,
#     and biased toward whichever model happens to resemble Otter more.
#   - A model scoring BELOW ~2% would be suspicious, not excellent.
#
# Normalisation follows standard ASR-eval practice (lowercase, strip punctuation, collapse
# whitespace, expand common contractions) because raw text comparison would score punctuation and
# casing differences as word errors and swamp the real signal.

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WHISPER_CLI = REPO / "whisper.cpp/build/bin/whisper-cli"
VAD_MODEL = Path("/opt/models/staging/whisper/ggml-silero-v6.2.0.bin")

CONTRACTIONS = {
    "won't": "will not", "can't": "cannot", "n't": " not", "'re": " are",
    "'ve": " have", "'ll": " will", "'d": " would", "'m": " am",
}


def normalise(text: str) -> str:
    """Standard ASR-eval normalisation: the comparison is about WORDS, not typography."""
    t = text.lower()
    for k, v in CONTRACTIONS.items():
        t = t.replace(k, v)
    t = re.sub(r"[^a-z0-9\s]", " ", t)      # strip punctuation entirely
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def transcribe(wav: Path, model: Path, vad: bool, out_dir: Path, timeout_s: int = 2400) -> str:
    base = out_dir / f"{wav.stem}-{model.stem}-{'vad' if vad else 'novad'}"
    cmd = [str(WHISPER_CLI), "-m", str(model), "-f", str(wav),
           "--output-json", "--output-file", str(base), "--max-len", "60"]
    if vad:
        if not VAD_MODEL.exists():
            raise FileNotFoundError(f"VAD model missing at {VAD_MODEL}. hint: see MANIFEST.md.")
        cmd += ["--vad", "-vm", str(VAD_MODEL)]
    if not base.with_suffix(".json").exists():
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"whisper-cli exceeded {timeout_s}s on {wav}. "
                               "hint: raise --timeout for long recordings.") from exc
        if proc.returncode != 0:
            raise RuntimeError(f"whisper-cli failed (rc={proc.returncode}): {proc.stderr[-300:]}")
    segs = json.loads(base.with_suffix(".json").read_text())["transcription"]
    return " ".join(s["text"] for s in segs)


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Transcription disagreement vs an Otter.ai reference (NOT true WER - see header).",
        epilog="example: var/diar-venv/bin/python tools/wer_bench.py audio.wav ref.txt",
    )
    ap.add_argument("wav", type=Path)
    ap.add_argument("reference", type=Path, help="plain-text reference transcript")
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    for p in (args.wav, args.reference):
        if not p.exists():
            raise FileNotFoundError(f"missing {p}. hint: check var/meetings/ paths.")
    try:
        import jiwer
    except ImportError as exc:
        raise ImportError("jiwer required. hint: var/diar-venv/bin/pip install jiwer") from exc

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ref = normalise(args.reference.read_text())
    print(f"reference: {len(ref.split())} words (Otter.ai, ~98% accurate -> FLOOR ~2%)\n")

    configs = [
        ("large-v3-turbo", REPO / "whisper.cpp/models/ggml-large-v3-turbo.bin", False),
        ("large-v3-turbo +VAD", REPO / "whisper.cpp/models/ggml-large-v3-turbo.bin", True),
        ("small", REPO / "whisper.cpp/models/ggml-small.bin", False),
        ("small +VAD", REPO / "whisper.cpp/models/ggml-small.bin", True),
    ]
    print(f"{'config':22s} {'words':>6s} {'DISAGREE':>9s} {'sub':>6s} {'del':>6s} {'ins':>6s}")
    print("-" * 62)
    for name, model, vad in configs:
        if not model.exists():
            print(f"{name:22s} (model missing at {model} - skipped)")
            continue
        hyp = normalise(transcribe(args.wav, model, vad, args.out_dir))
        m = jiwer.process_words(ref, hyp)
        print(f"{name:22s} {len(hyp.split()):6d} {100*m.wer:8.1f}% "
              f"{m.substitutions:6d} {m.deletions:6d} {m.insertions:6d}")
    print("-" * 62)
    print("\nDISAGREE = disagreement with Otter, NOT accuracy. A perfect transcript would still")
    print("score ~2% here by correctly differing from Otter's own errors. Compare configs to each")
    print("other; do not read the absolute number as word error rate.")


if __name__ == "__main__":
    main()
