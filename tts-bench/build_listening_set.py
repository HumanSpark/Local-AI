#!/usr/bin/env python3
# File: tts-bench/build_listening_set.py
# Purpose: Assemble a loudness-normalised, blind-labelled listening set from whatever engines have already rendered.
# Project: sparkbench | Date: 2026-07-26
#
# Overview: W3's formal blind pack is T13, gated behind ALL Stage-2 engines being stood up (T11).
# That ordering delivers the owner's NUMBER-ONE criterion - speech quality - last, after many hours
# of throughput work he ranks second. This script pulls it forward: it builds a listening set from
# the audio already on disk, so "does anything actually sound better than Kokoro?" can be answered
# now and can steer the remaining engine work instead of being confirmed after it.
#
# Two things make the comparison fair rather than merely convenient:
#  * LOUDNESS NORMALISATION (ffmpeg loudnorm to -16 LUFS). Engines emit at very different levels and
#    the louder of two takes is reliably judged "better" - normalising removes the single biggest
#    confound in any informal A/B. Without this the test measures output gain, not speech quality.
#  * BLIND LABELS. Files are named by letter, with the mapping written to a SEPARATE key file, so a
#    reaction is not anchored by knowing which is the incumbent. The key is one file open away -
#    this is a debiasing aid, not a ritual.
#
# Labels are assigned by sha256 of the engine id (deterministic and reproducible, but not
# alphabetical - alphabetical ordering would leak that A is a good guess for the first engine).
# All outputs are 24 kHz mono WAV so no engine gains or loses from container/codec differences.
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
CORPUS = Path(__file__).parent / "corpus"
TARGET_LUFS = -16.0
SAMPLE_RATE = 24000


def discover(excerpt: str) -> dict[str, Path]:
    """Map engine-id -> rendered file for one excerpt, across every engine that has audio."""
    found: dict[str, Path] = {}
    for audio_dir in sorted(RESULTS.glob("*/audio")):
        engine = audio_dir.parent.name
        for f in sorted(audio_dir.iterdir()):
            if not f.name.startswith(excerpt):
                continue
            # filename shape: <key>__<voice>__s<N>.<ext>; only the first sample of each voice
            parts = f.stem.split("__")
            voice = parts[1] if len(parts) > 2 else "default"
            sample = parts[-1] if len(parts) > 2 else "s1"
            if sample != "s1":
                continue
            found[f"{engine}/{voice}"] = f
    if not found:
        raise FileNotFoundError(
            f"No rendered audio found for excerpt {excerpt!r} under {RESULTS}. "
            f"hint: engine audio lives in results/<engine>/audio/ and is gitignored - it exists "
            f"only on the box that rendered it."
        )
    return found


def normalise(src: Path, dst: Path) -> None:
    """Loudness-normalise to TARGET_LUFS mono WAV. Raises with a hint if ffmpeg fails."""
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
        "-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11",
        "-ar", str(SAMPLE_RATE), "-ac", "1", str(dst),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if proc.returncode != 0 or not dst.exists():
        raise RuntimeError(
            f"ffmpeg loudnorm failed for {src.name}: {proc.stderr.strip()[:300]}. "
            f"hint: check the source decodes at all (`ffprobe {src}`); a zero-length or truncated "
            f"render will fail here rather than silently produce a bad comparison file."
        )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Build a loudness-normalised blind listening set from already-rendered audio.",
        epilog="example:\n  ./build_listening_set.py 01-first-person-argument 02-technical-acronym-density\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("excerpts", nargs="+", help="corpus excerpt keys to include")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "listening",
                    help="output directory (default: tts-bench/listening)")
    args = ap.parse_args()

    out = args.out
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # One stable letter per engine ACROSS all excerpts, so a listener can track "C" between texts.
    engines: set[str] = set()
    for ex in args.excerpts:
        engines |= set(discover(ex))
    ordered = sorted(engines, key=lambda e: hashlib.sha256(e.encode()).hexdigest())
    letters = {e: chr(ord("A") + i) for i, e in enumerate(ordered)}
    if len(ordered) > 26:
        raise ValueError(
            f"{len(ordered)} engines exceeds the 26 single-letter labels. "
            f"hint: split the set across excerpts, or move to two-letter labels."
        )

    key: dict[str, dict] = {"target_lufs": TARGET_LUFS, "labels": letters, "excerpts": {}}
    for ex in args.excerpts:
        found = discover(ex)
        text = (CORPUS / f"{ex}.txt").read_text().strip()
        key["excerpts"][ex] = {"text": text, "renders": {}}
        for engine, src in sorted(found.items()):
            dst = out / f"{ex}__{letters[engine]}.wav"
            normalise(src, dst)
            key["excerpts"][ex]["renders"][letters[engine]] = {
                "engine": engine, "source_file": src.name,
            }
            print(f"{ex}  {letters[engine]}  <- {engine:28s} ({src.name})")

    (out / "ANSWER-KEY.json").write_text(json.dumps(key, indent=2) + "\n")

    sheet = [
        "# Blind listening sheet - W3 (pulled forward from T13)",
        "",
        f"All takes loudness-normalised to {TARGET_LUFS} LUFS, {SAMPLE_RATE} Hz mono, so level is not",
        "a confound. The same letter is the same engine across every excerpt.",
        "",
        "Score each take 1-5 on the axes that matter for long-form article narration:",
        "  NATURALNESS  - does it sound like a person reading, or a machine reciting?",
        "  PROSODY      - sentence-level rhythm and emphasis; does it land the argument?",
        "  ARTEFACTS    - buzzing, warble, clipping, dropped or slurred words (5 = none)",
        "  FATIGUE      - could you listen to 5 minutes of this? (5 = easily)",
        "",
        "Open ANSWER-KEY.json only after scoring.",
        "",
    ]
    for ex in args.excerpts:
        sheet.append(f"## {ex}")
        sheet.append("")
        sheet.append(f"> {key['excerpts'][ex]['text']}")
        sheet.append("")
        sheet.append("| Take | Naturalness | Prosody | Artefacts | Fatigue | Notes |")
        sheet.append("|---|---|---|---|---|---|")
        for letter in sorted(key["excerpts"][ex]["renders"]):
            sheet.append(f"| {letter} | | | | | |")
        sheet.append("")
    (out / "SCORING-SHEET.md").write_text("\n".join(sheet))

    print(f"\n{len(ordered)} engines x {len(args.excerpts)} excerpts -> {out}")
    print(f"  sheet: {out / 'SCORING-SHEET.md'}   key: {out / 'ANSWER-KEY.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
