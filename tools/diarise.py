# File: tools/diarise.py
# Purpose: Attributed-transcript pipeline - large-v3-turbo for text + WeSpeaker for identity.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Two INDEPENDENT passes over the same audio, joined only at the end on timestamps:
#   text pass    - whisper.cpp large-v3-turbo -> segments with text + start/end (quality untouched)
#   speaker pass - a SLIDING WINDOW over the raw audio -> WeSpeaker embedding per window ->
#                  agglomerative clustering -> a speaker timeline -> assigned to text by overlap
# The speaker model never sees a word and the transcription model never sees a speaker, so adding
# identity costs NOTHING in transcription accuracy. That is why we do NOT use tinydiarize: tdrz IS
# the transcription model (small.en), so it trades transcript quality for speaker marks, and it
# only marks TURNS rather than identity.
#
# WHY THE SLIDING WINDOW (this was a real bug, kept as a comment because it is non-obvious):
# v1 embedded each WHISPER segment. Whisper returns segments sized for transcription convenience -
# on a 36s two-speaker fixture it returned two 30s segments, each spanning BOTH speakers. Each
# embedding was therefore an average of two voices; two such mixtures resemble each other, so the
# pipeline reported ONE speaker. Whisper segments are not speaker-homogeneous and must never be the
# diarisation unit. The speaker pass owns its own windowing.
#
# CLUSTERING: complete linkage, speaker count SUPPLIED (--speakers), not discovered.
#
# Both of those are E39 findings, and both overturn what this file did before:
#
# 1. LINKAGE. v2 used average linkage. On a recording where one speaker holds 85% of the audio,
#    average linkage prefers to SPLIT the dominant speaker in two rather than isolate the minority
#    speaker - both give "k=2", and cleaving a big diffuse cluster is cheaper by MEAN distance.
#    Complete linkage merges on WORST-CASE distance, so it refuses to unite anything containing a
#    far-apart pair and the minority speaker survives. Measured over 147 min of real audio:
#    average 11.2% mean DER, complete 5.1% - against a supervised ceiling of 4.4%. On the recording
#    that failed outright it is 16.7% -> 3.2%. One word.
#
# 2. SPEAKER COUNT. Discovering k is UNSOLVED here - silhouette, a ">=2% of windows" rule, and
#    spectral eigengap all failed across the corpus (best automatic chooser: 9.5% mean DER vs 5.1%
#    with the true k). Given the true k, complete linkage reaches the supervised ceiling. So k is
#    an input: in deployment the attendee count is known from the meeting invite. Passing --speakers
#    turns an unsolved research problem into a parameter. Without it we fall back to k=3, which was
#    the least-bad constant measured - a GUESS, and logged as one.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from spk_embed import SAMPLE_RATE as SR  # noqa: E402
from spk_embed import SpeakerEmbedder, load_wav  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WHISPER_CLI = REPO / "whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL = REPO / "whisper.cpp/models/ggml-large-v3-turbo.bin"
# VAD is MANDATORY, not optional. Without it whisper large-v3-turbo hallucinates over silence -
# it invented four "Thank you" segments across 120s of dead air on a real client call, and six
# fabricated lines on a 180s clip of the same audio. Invented SPEECH is worse than a wrong speaker
# label: a reader can spot a mislabelled turn, but not words nobody said. (E40)
VAD_MODEL = Path("/opt/models/staging/whisper/ggml-silero-v6.2.0.bin")

VAD_BINARY = REPO / "whisper.cpp/build/bin/whisper-vad-speech-segments"
# The speaker pass gates on a REAL VAD, not on volume. E43 measured the old energy gate
# (RMS > 1e-3) against AMI's human ground truth: it caused 20.2% FALSE ALARM of a 29.2% DER -
# 69% of all error - because breathing, paper and keyboards clear a volume threshold and get
# assigned a speaker. Switching to Silero: DER 29.2% -> 14.4%, and confusion fell 8.7% -> 3.0%
# as a bonus, because cleaner windows make better clusters.
VAD_THRESHOLD = 0.10   # tuned on 3 AMI meetings, reported on 13 held out. 0.05-0.15 is a FLAT
                       # plateau (all within 0.5 DER points), so this is not a fitted magic
                       # number; there is a sharp knee at 0.20 where miss climbs.
DEFAULT_SPEAKERS = 3   # least-bad constant when the count is unknown (9.5% mean DER). A GUESS.
WINDOW_S = 3.0   # 1.5s halves the usable margin on real audio (E38: same-speaker sim .78 vs .85)
HOP_S = 1.0      # resolution of the speaker timeline


def transcribe(wav: Path, timeout_s: int = 900) -> list[dict]:
    """Run whisper.cpp large-v3-turbo and return its segments (text + timestamps)."""
    if not WHISPER_CLI.exists() or not WHISPER_MODEL.exists():
        raise FileNotFoundError(
            f"whisper-cli or large-v3-turbo model missing ({WHISPER_CLI}, {WHISPER_MODEL}). "
            "hint: build whisper.cpp and fetch ggml-large-v3-turbo.bin into whisper.cpp/models/."
        )
    out_base = wav.with_suffix("")
    if not VAD_MODEL.exists():
        raise FileNotFoundError(
            f"VAD model missing at {VAD_MODEL}. hint: fetch per manifests/MANIFEST.md "
            "(ggml-org/whisper-vad, rev 9ffd54a1, 885,098 B, sha256 2aa269b7...). This is NOT "
            "optional - without VAD whisper fabricates speech over silence."
        )
    cmd = [
        str(WHISPER_CLI), "-m", str(WHISPER_MODEL), "-f", str(wav),
        "--output-json", "--output-file", str(out_base),
        # Force short segments so text can be attributed at turn granularity rather than in
        # 30s blocks. Without this whisper emits one segment per decode window.
        "--max-len", "60",
        "--vad", "-vm", str(VAD_MODEL),
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(
            f"whisper-cli exceeded {timeout_s}s on {wav}. "
            "hint: raise --timeout for long recordings, or check the GPU is not wedged."
        ) from exc
    if proc.returncode != 0:
        raise RuntimeError(
            f"whisper-cli failed (rc={proc.returncode}): {proc.stderr[-500:]}. "
            "hint: confirm the wav is 16 kHz mono."
        )
    js = out_base.with_suffix(".json")
    if not js.exists():
        raise FileNotFoundError(
            f"whisper produced no JSON at {js}. "
            "hint: --output-txt silently drops structured fields; this pipeline needs --output-json."
        )
    return json.loads(js.read_text())["transcription"]


def speech_regions(wav: Path, threshold: float = VAD_THRESHOLD) -> list[tuple[float, float]]:
    """Silero speech regions via whisper.cpp's VAD tool. Timestamps are centiseconds."""
    if not VAD_BINARY.exists() or not VAD_MODEL.exists():
        raise FileNotFoundError(
            f"VAD missing ({VAD_BINARY}, {VAD_MODEL}). hint: build with `cmake --build build "
            "--target whisper-vad-speech-segments` in whisper.cpp; model per manifests/MANIFEST.md. "
            "This is NOT optional: without a real VAD, false alarm is ~69% of diarisation error."
        )
    try:
        proc = subprocess.run(
            [str(VAD_BINARY), "-np", "-vm", str(VAD_MODEL), "-vt", str(threshold), "-f", str(wav)],
            capture_output=True, text=True, timeout=1800,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"VAD exceeded 1800s on {wav}. hint: check the GPU is not wedged.") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"VAD failed (rc={proc.returncode}): {proc.stderr[-300:]}")
    regions = []
    for line in proc.stdout.splitlines():
        if line.startswith("Speech segment"):
            body = line.split("start = ")[1]
            a, b = body.split(", end = ")
            regions.append((float(a) / 100.0, float(b) / 100.0))
    if not regions:
        raise ValueError(
            f"VAD found no speech in {wav}. hint: check the recording is not silent, or lower "
            f"--vad-threshold (currently {threshold})."
        )
    return regions


def speaker_timeline(
    audio: np.ndarray, wav: Path, speakers: int = DEFAULT_SPEAKERS
) -> list[tuple[float, float, int]]:
    """Slide a window over VAD-confirmed speech and cluster into (start, end, speaker) spans."""
    from sklearn.cluster import AgglomerativeClustering

    win, hop = int(WINDOW_S * SR), int(HOP_S * SR)
    if len(audio) < win:
        raise ValueError(
            f"audio is shorter than one {WINDOW_S}s window. "
            "hint: diarisation needs at least a couple of seconds of speech."
        )

    regions = speech_regions(wav)
    embedder = SpeakerEmbedder()
    windows, embeddings = [], []
    for start in range(0, len(audio) - win + 1, hop):
        a, b = start / SR, (start + win) / SR
        # Keep the window only where a real VAD says its CENTRE is speech.
        mid = (a + b) / 2
        if not any(s <= mid <= e for s, e in regions):
            continue
        windows.append((a, b))
        embeddings.append(embedder.embed(audio[start : start + win]))

    if not embeddings:
        raise ValueError(
            "no window fell inside a VAD speech region. "
            f"hint: check the recording, or lower VAD_THRESHOLD (currently {VAD_THRESHOLD})."
        )

    if len(embeddings) == 1:
        labels = np.zeros(1, dtype=int)
    else:
        labels = AgglomerativeClustering(
            n_clusters=min(speakers, len(embeddings)),
            metric="cosine", linkage="complete",
        ).fit_predict(np.vstack(embeddings))

    return [(s, e, int(lab)) for (s, e), lab in zip(windows, labels)]


def assign_speakers(segments: list[dict], timeline: list[tuple[float, float, int]]) -> list[dict]:
    """Attribute each text segment to the speaker holding the most of its duration."""
    for seg in segments:
        s, e = seg["offsets"]["from"] / 1000.0, seg["offsets"]["to"] / 1000.0
        votes: Counter[int] = Counter()
        for ws, we, lab in timeline:
            overlap = min(e, we) - max(s, ws)
            if overlap > 0:
                votes[lab] += overlap
        seg["speaker"] = f"SPEAKER_{votes.most_common(1)[0][0]}" if votes else None
    return segments


def diarise(wav: Path, speakers: int = DEFAULT_SPEAKERS, timeout_s: int = 900) -> tuple:
    audio = load_wav(wav)
    segments = transcribe(wav, timeout_s=timeout_s)
    timeline = speaker_timeline(audio, wav, speakers=speakers)
    return assign_speakers(segments, timeline), timeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Attributed transcript: large-v3-turbo for text, WeSpeaker for speaker identity.",
        epilog="example: var/diar-venv/bin/python tools/diarise.py meeting.wav --json out.json",
    )
    parser.add_argument("wav", type=Path, help="16 kHz mono WAV")
    parser.add_argument("--speakers", type=int, default=DEFAULT_SPEAKERS,
                        help=f"number of speakers (default {DEFAULT_SPEAKERS} - a GUESS). Supply the "
                             "real count from the meeting invite: with it the system runs at ~5%% DER, "
                             "near the supervised ceiling; without it, ~9.5%%. Automatic estimation "
                             "is UNSOLVED (E39).")
    parser.add_argument("--timeout", type=int, default=900, help="whisper timeout, seconds")
    parser.add_argument("--json", type=Path, default=None, help="write annotated segments here")
    args = parser.parse_args()

    segs, timeline = diarise(args.wav, speakers=args.speakers, timeout_s=args.timeout)
    speakers = sorted({lab for _, _, lab in timeline})
    print(f"# {args.wav.name}: {len(speakers)} speaker(s) discovered "
          f"from {len(timeline)} windows, {len(segs)} text segments\n")
    for s in segs:
        start, end = s["offsets"]["from"] / 1000.0, s["offsets"]["to"] / 1000.0
        print(f"[{start:6.2f}-{end:6.2f}] {s['speaker'] or 'UNKNOWN':11s} {s['text'].strip()}")
    if args.json:
        args.json.write_text(json.dumps({"segments": segs, "timeline": timeline}, indent=1))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
