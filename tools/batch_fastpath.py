# File: batch_fastpath.py
# Purpose: Run the FAST diarisation path over a directory of real recordings; write attributed transcripts.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Alastair's real meeting archive (Zoom/Teams) - "run every single one through our system
# using the fast path." Fast path = our pure stack: whisper.cpp large-v3-turbo + VAD for text,
# Silero VAD + WeSpeaker + complete-linkage AHC for speakers. GPU for transcription/VAD, CPU for
# embeddings; ~60x real time, no torch.
#
# SPEAKER COUNT is unknown (no invite, no ground truth) and automatic estimation is our open problem
# (E39/E40). Here k is estimated per file by silhouette over a SUBSAMPLE (full silhouette is O(n^2)
# and these files reach ~6000 windows). Every estimate is FLAGGED provisional: Otter transcripts,
# arriving later, set the true count and allow re-scoring. The transcript itself needs no k and is
# the reliable half.
#
# Robustness at scale: each file is wrapped so one failure (bad audio, silence, crash) does not abort
# the batch. Real client audio -> outputs are gitignored; only per-file stats (duration, est-k, speaker
# share, timing) are safe to surface.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from spk_embed import SAMPLE_RATE as SR  # noqa: E402
from spk_embed import SpeakerEmbedder, load_wav  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WHISPER_CLI = REPO / "whisper.cpp/build/bin/whisper-cli"
WHISPER_MODEL = REPO / "whisper.cpp/models/ggml-large-v3-turbo.bin"
VAD_BINARY = REPO / "whisper.cpp/build/bin/whisper-vad-speech-segments"
VAD_GGML = Path("/opt/models/staging/whisper/ggml-silero-v6.2.0.bin")
WIN_S, HOP_S = 3.0, 2.0          # 2s hop (vs 1s) halves window count for hour-long files
KMAX = 8
SUBSAMPLE = 1500                  # cap for silhouette (O(n^2))


def transcribe(wav: Path, out_base: Path, timeout_s: int) -> list[dict]:
    cmd = [str(WHISPER_CLI), "-m", str(WHISPER_MODEL), "-f", str(wav), "--output-json",
           "--output-file", str(out_base), "--max-len", "60", "--vad", "-vm", str(VAD_GGML)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(f"whisper failed: {proc.stderr[-200:]}")
    return json.loads(out_base.with_suffix(".json").read_text())["transcription"]


def speech_regions(wav: Path, threshold: float = 0.10) -> list[tuple[float, float]]:
    proc = subprocess.run(
        [str(VAD_BINARY), "-np", "-vm", str(VAD_GGML), "-vt", str(threshold), "-f", str(wav)],
        capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        raise RuntimeError(f"VAD failed: {proc.stderr[-200:]}")
    out = []
    for line in proc.stdout.splitlines():
        if line.startswith("Speech segment"):
            a, b = line.split("start = ")[1].split(", end = ")
            out.append((float(a) / 100.0, float(b) / 100.0))
    return out


def estimate_k(E: np.ndarray) -> int:
    """Silhouette over k=1..KMAX on a subsample. Provisional - Otter will settle it."""
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score

    n = len(E)
    if n < 4:
        return 1
    idx = np.arange(n) if n <= SUBSAMPLE else np.random.default_rng(0).choice(n, SUBSAMPLE, replace=False)
    S = E[idx]
    best_k, best_s = 1, -1.0
    for k in range(2, min(KMAX, len(S) - 1) + 1):
        lab = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="complete").fit_predict(S)
        try:
            s = silhouette_score(S, lab, metric="cosine")
        except ValueError:
            continue
        if s > best_s:
            best_k, best_s = k, s
    # a very weak best silhouette suggests a single speaker (dictation/monologue)
    return best_k if best_s >= 0.15 else 1


def diarise(audio: np.ndarray, regions, embedder) -> tuple[list, int]:
    from sklearn.cluster import AgglomerativeClustering

    win, hop = int(WIN_S * SR), int(HOP_S * SR)
    times, embs = [], []
    for st in range(0, len(audio) - win + 1, hop):
        a, b = st / SR, (st + win) / SR
        mid = (a + b) / 2
        if not any(rs <= mid <= re for rs, re in regions):
            continue
        times.append((a, b))
        embs.append(embedder.embed(audio[st: st + win]))
    if not embs:
        return [], 0
    E = np.vstack(embs)
    k = estimate_k(E)
    labels = (np.zeros(len(embs), dtype=int) if k <= 1 else
              AgglomerativeClustering(n_clusters=min(k, len(embs)), metric="cosine",
                                      linkage="complete").fit_predict(E))
    half = HOP_S / 2
    timeline = [((a + b) / 2 - half, (a + b) / 2 + half, int(l)) for (a, b), l in zip(times, labels)]
    return timeline, int(max(labels) + 1) if len(labels) else 0


def attribute(segments: list[dict], timeline) -> list[dict]:
    for seg in segments:
        s, e = seg["offsets"]["from"] / 1000.0, seg["offsets"]["to"] / 1000.0
        votes: Counter = Counter()
        for ts, te, lab in timeline:
            ov = min(e, te) - max(s, ts)
            if ov > 0:
                votes[lab] += ov
        seg["speaker"] = votes.most_common(1)[0][0] if votes else None
    return segments


def main() -> None:
    ap = argparse.ArgumentParser(description="Batch fast-path diarisation over a wav directory.")
    ap.add_argument("--wav-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--timeout", type=int, default=3600)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    scratch = args.out_dir / "_whisper"
    scratch.mkdir(exist_ok=True)

    embedder = SpeakerEmbedder()
    stats = []
    wavs = sorted(args.wav_dir.glob("*.wav"))
    print(f"batch fast-path: {len(wavs)} files\n", flush=True)
    for wav in wavs:
        name = wav.stem
        t0 = time.time()
        try:
            audio = load_wav(wav)
            dur = len(audio) / SR
            segs = transcribe(wav, scratch / name, args.timeout)
            regions = speech_regions(wav)
            timeline, kfound = diarise(audio, regions, embedder)
            segs = attribute(segs, timeline)
            # write attributed transcript (gitignored - real client audio)
            lines = [f"# {name}  ({dur/60:.1f} min, ~{kfound} speakers [ESTIMATED - pending Otter])\n"]
            for s in segs:
                a = s["offsets"]["from"] / 1000.0
                spk = f"SPEAKER_{s['speaker']}" if s.get("speaker") is not None else "UNKNOWN"
                lines.append(f"[{int(a//60):02d}:{int(a%60):02d}] {spk}: {s['text'].strip()}")
            (args.out_dir / f"{name}.txt").write_text("\n".join(lines))
            speech = sum(e - s for s, e in regions)
            rt = dur / (time.time() - t0)
            share = Counter(s["speaker"] for s in segs if s.get("speaker") is not None)
            stats.append({"file": name, "min": round(dur / 60, 1), "est_k": kfound,
                          "speech_pct": round(100 * speech / dur), "rt": round(rt, 1),
                          "segments": len(segs)})
            print(f"  OK  {name[:40]:40s} {dur/60:5.1f}min  k~{kfound}  "
                  f"speech {100*speech/dur:3.0f}%  {rt:.0f}x RT", flush=True)
        except Exception as exc:
            stats.append({"file": name, "error": str(exc)[:120]})
            print(f"  FAIL {name[:40]:40s} {str(exc)[:60]}", flush=True)

    (args.out_dir / "batch-stats.json").write_text(json.dumps(stats, indent=1))
    ok = [s for s in stats if "error" not in s]
    print(f"\n{len(ok)}/{len(stats)} succeeded. stats -> {args.out_dir}/batch-stats.json", flush=True)


if __name__ == "__main__":
    main()
