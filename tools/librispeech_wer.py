# File: tools/librispeech_wer.py
# Purpose: TRUE WER against human ground truth - validates or refutes E42's Otter-based figure.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E42 compared whisper model sizes using an Otter.ai transcript as reference, which
# Alastair estimates at ~98% accurate and which I hand-copied. That gave DISAGREEMENT rates with a
# ~2% floor, not WER - a perfect transcript would still have scored ~2%. LibriSpeech test-clean is
# the standard ASR benchmark with real human transcripts, so this is the first true WER we have.
#
# LibriSpeech is read speech (audiobooks): clean, single-speaker, no crosstalk, no meeting acoustics.
# It is the EASY case and its WER will be far better than any meeting number - it validates the
# model COMPARISON (large vs small), not the meeting use case.

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
WHISPER_CLI = REPO / "whisper.cpp/build/bin/whisper-cli"
VAD_MODEL = Path("/opt/models/staging/whisper/ggml-silero-v6.2.0.bin")


def normalise(text: str) -> str:
    """LibriSpeech references are uppercase, unpunctuated. Match that."""
    t = text.lower()
    t = re.sub(r"[^a-z0-9\s']", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def main() -> None:
    import numpy as np
    import pyarrow.parquet as pq
    import soundfile as sf

    ap = argparse.ArgumentParser(
        description="True WER on LibriSpeech test-clean (real human transcripts).",
        epilog="example: var/diar-venv/bin/python tools/librispeech_wer.py --limit 300",
    )
    ap.add_argument("--model", type=Path, default=REPO / "whisper.cpp/models/ggml-large-v3-turbo.bin")
    ap.add_argument("--model-name", default="large-v3-turbo")
    ap.add_argument("--vad", action="store_true")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--data", type=Path,
                    default=Path("/opt/models/staging/librispeech/test-clean-0000.parquet"))
    args = ap.parse_args()
    for p in (args.model, args.data, WHISPER_CLI):
        if not p.exists():
            raise FileNotFoundError(f"missing {p}. hint: see manifests/MANIFEST.md.")
    try:
        import jiwer
    except ImportError as exc:
        raise ImportError("jiwer required. hint: var/diar-venv/bin/pip install jiwer") from exc

    t = pq.ParquetFile(args.data).read()
    refs, hyps = [], []
    # ONE utterance per whisper call. The first version batched 10 utterances into a single wav
    # separated by 1s gaps, to amortise process startup - and whisper DROPPED audio, producing
    # 16.23% WER on LibriSpeech test-clean where the published figure for this model is ~2-3%,
    # with 511 deletions vs 55 insertions. Worse, the broken harness reported small BEATING large,
    # which was the hypothesis under test: a bug that confirms what you hoped is the most dangerous
    # result there is. Single utterances transcribe verbatim. Slower, correct.
    with tempfile.TemporaryDirectory() as td:
        for i in range(min(args.limit, t.num_rows)):
            row = {c: t.column(c)[i].as_py() for c in t.column_names}
            audio, sr = sf.read(io.BytesIO(row["audio"]["bytes"]), dtype="float32")
            if sr != 16000:
                raise ValueError(f"utterance {i} is {sr} Hz, expected 16000.")
            wav = Path(td) / f"u{i}.wav"
            sf.write(str(wav), audio, sr)
            base = str(wav)[:-4]
            cmd = [str(WHISPER_CLI), "-m", str(args.model), "-f", str(wav), "-nt",
                   "--output-txt", "--output-file", base]
            if args.vad:
                cmd += ["--vad", "-vm", str(VAD_MODEL)]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if proc.returncode != 0:
                raise RuntimeError(f"whisper failed on utterance {i}: {proc.stderr[-200:]}")
            txt = Path(base + ".txt")
            hyps.append(normalise(txt.read_text()) if txt.exists() else "")
            refs.append(normalise(row["text"]))
            wav.unlink(missing_ok=True)
            txt.unlink(missing_ok=True)
    m = jiwer.process_words(refs, hyps)
    words = sum(len(r.split()) for r in refs)
    print(f"{args.model_name:22s} vad={str(args.vad):5s} "
          f"words={words:6d} WER={100*m.wer:6.2f}%  "
          f"sub={m.substitutions:5d} del={m.deletions:5d} ins={m.insertions:5d}")


if __name__ == "__main__":
    main()
