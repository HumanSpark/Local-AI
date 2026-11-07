# File: tools/silence_bench.py
# Purpose: Measure when whisper INVENTS speech out of silence. Pre-reg: e41-...-prereg.md.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E40 found whisper large-v3-turbo fabricating speech over silence incidentally, on one
# real recording. This makes it a benchmark: synthetic fixtures with EXACT ground truth (we generate
# the silence, so we know precisely which regions contain no speech), swept across duration, silence
# type, position, model size, and VAD on/off.
#
# Scoring is deliberately simple and hard to fool: count transcript segments lying entirely inside a
# known-silent region. Any such segment is a FABRICATION - there is no speech there to transcribe,
# because we synthesised the region ourselves.
#
# Fixtures are built from numpy (silence) plus whisper.cpp's jfk.wav (the real-speech anchor, used
# where a condition needs speech in context). Nothing here depends on the meeting corpus, so this
# benchmark is publishable without any personal data.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parent.parent
WHISPER_CLI = REPO / "whisper.cpp/build/bin/whisper-cli"
VAD_MODEL = Path("/opt/models/staging/whisper/ggml-silero-v6.2.0.bin")
JFK = REPO / "whisper.cpp/samples/jfk.wav"
SR = 16000


def make_silence(seconds: float, kind: str, rng: np.random.Generator) -> np.ndarray:
    """Generate a silent region of a given character."""
    n = int(seconds * SR)
    if kind == "digital-zero":
        return np.zeros(n, dtype=np.float32)
    if kind == "noise-60db":
        return (rng.standard_normal(n) * (10 ** (-60 / 20))).astype(np.float32)
    if kind == "roomtone-45db":
        # pink-ish: low-passed white noise, the acoustic texture of an empty room
        w = rng.standard_normal(n)
        k = np.ones(64) / 64
        return (np.convolve(w, k, mode="same") * (10 ** (-45 / 20))).astype(np.float32)
    raise ValueError(f"unknown silence kind {kind!r}. hint: digital-zero|noise-60db|roomtone-45db")


def build_fixture(
    path: Path, duration: float, kind: str, position: str, rng: np.random.Generator
) -> list[tuple[float, float]]:
    """Write a fixture; return the list of (start, end) regions that are KNOWN-SILENT."""
    if position != "silence-only" and not JFK.exists():
        raise FileNotFoundError(
            f"speech anchor missing at {JFK}. hint: jfk.wav ships with whisper.cpp/samples."
        )
    speech = np.zeros(0, dtype=np.float32)
    if position != "silence-only":
        speech, sr = sf.read(str(JFK), dtype="float32")
        if sr != SR:
            raise ValueError(f"{JFK} is {sr} Hz, need {SR}. hint: resample the anchor.")
    sil = make_silence(duration, kind, rng)
    sp = len(speech) / SR

    if position == "silence-only":
        audio, silent = sil, [(0.0, duration)]
    elif position == "leading":
        audio, silent = np.concatenate([sil, speech]), [(0.0, duration)]
    elif position == "trailing":
        audio, silent = np.concatenate([speech, sil]), [(sp, sp + duration)]
    elif position == "sandwiched":
        audio = np.concatenate([speech, sil, speech])
        silent = [(sp, sp + duration)]
    else:
        raise ValueError(f"unknown position {position!r}. "
                         "hint: silence-only|leading|trailing|sandwiched")
    sf.write(str(path), audio, SR)
    return silent


def transcribe(wav: Path, model: Path, vad: bool, timeout_s: int = 1200) -> list[dict]:
    base = wav.with_suffix("")
    cmd = [str(WHISPER_CLI), "-m", str(model), "-f", str(wav),
           "--output-json", "--output-file", str(base), "--max-len", "60"]
    if vad:
        if not VAD_MODEL.exists():
            raise FileNotFoundError(f"VAD model missing at {VAD_MODEL}. hint: see MANIFEST.md.")
        cmd += ["--vad", "-vm", str(VAD_MODEL)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"whisper-cli exceeded {timeout_s}s on {wav}. "
                           "hint: raise the timeout for 300s fixtures.") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"whisper-cli failed (rc={proc.returncode}): {proc.stderr[-300:]}")
    js = base.with_suffix(".json")
    if not js.exists():
        raise FileNotFoundError(f"no JSON at {js}. hint: --output-json is required.")
    return json.loads(js.read_text())["transcription"]


def count_fabrications(segments: list[dict], silent: list[tuple[float, float]]) -> list[str]:
    """Any segment lying wholly inside a known-silent region is invented speech."""
    out = []
    for s in segments:
        a, b = s["offsets"]["from"] / 1000.0, s["offsets"]["to"] / 1000.0
        for ss, se in silent:
            if a >= ss - 0.05 and b <= se + 0.05:
                txt = s["text"].strip()
                if txt:
                    out.append(txt)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Benchmark whisper's tendency to invent speech over silence.",
        epilog="example: var/diar-venv/bin/python tools/silence_bench.py --out results.json",
    )
    ap.add_argument("--model", type=Path,
                    default=REPO / "whisper.cpp/models/ggml-large-v3-turbo.bin")
    ap.add_argument("--model-name", default="large-v3-turbo")
    ap.add_argument("--vad", action="store_true")
    ap.add_argument("--scratch", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--quick", action="store_true", help="short durations only")
    args = ap.parse_args()

    if not args.model.exists():
        raise FileNotFoundError(f"model missing at {args.model}. hint: check whisper.cpp/models/.")
    args.scratch.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)

    durations = [10, 30, 60] if args.quick else [5, 10, 30, 60, 120, 300]
    kinds = ["digital-zero", "noise-60db", "roomtone-45db"]
    positions = ["silence-only", "leading", "trailing", "sandwiched"]

    rows = []
    print(f"model={args.model_name}  vad={args.vad}\n")
    print(f"{'position':13s} {'silence type':14s} {'dur':>5s} {'fabricated':>11s}  sample text")
    print("-" * 92)
    for position in positions:
        for kind in kinds:
            for dur in durations:
                wav = args.scratch / f"{position}_{kind}_{dur}.wav"
                silent = build_fixture(wav, dur, kind, position, rng)
                segs = transcribe(wav, args.model, args.vad)
                fab = count_fabrications(segs, silent)
                rows.append({"position": position, "kind": kind, "duration": dur,
                             "n_fabricated": len(fab), "texts": fab,
                             "model": args.model_name, "vad": args.vad})
                sample = (fab[0][:44] if fab else "")
                flag = "  <<<" if fab else ""
                print(f"{position:13s} {kind:14s} {dur:4d}s {len(fab):11d}  {sample}{flag}")
                wav.unlink(missing_ok=True)
                (args.scratch / f"{position}_{kind}_{dur}.json").unlink(missing_ok=True)
    total = sum(r["n_fabricated"] for r in rows)
    print("-" * 92)
    print(f"TOTAL fabricated segments: {total} across {len(rows)} conditions")
    if args.out:
        args.out.write_text(json.dumps(rows, indent=1))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
