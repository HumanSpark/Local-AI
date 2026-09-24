# File: target_speaker.py
# Purpose: "Is it Alastair or not?" - target-speaker detection, sidestepping the auto-k problem.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Alastair's real need is NOT "count and separate every speaker" - it is "when am I talking
# vs when is someone else talking". That is a BINARY, single-target problem: enroll one voiceprint
# (Alastair), then per window ask "does this match?" No clustering, no speaker count, no k. The whole
# E39/E40 auto-k failure mode disappears, because we never count anyone.
#
# Enrollment is acoustically INDEPENDENT of the test set (voiceprint from the GMKtec solo intro, which
# is not one of the ground-truthed calls) so there is no leakage. Validation uses the 4 Otter-labelled
# recordings, where every turn is tagged Alastair or another speaker, so "Alastair vs Other" has real
# ground truth. WeSpeaker ONNX embeddings, CPU, no torch.

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from spk_embed import SAMPLE_RATE as SR  # noqa: E402
from spk_embed import SpeakerEmbedder, load_wav  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WIN_S, HOP_S, ENERGY = 3.0, 1.5, 1e-3
TARGET = "Alastair McDermott"


def windows(audio, embedder, win_s=WIN_S, hop_s=HOP_S):
    win, hop = int(win_s * SR), int(hop_s * SR)
    times, embs = [], []
    for st in range(0, len(audio) - win + 1, hop):
        c = audio[st: st + win]
        if float(np.sqrt(np.mean(c ** 2))) < ENERGY:
            continue
        times.append((st / SR, (st + win) / SR))
        embs.append(embedder.embed(c))
    return times, (np.vstack(embs) if embs else np.zeros((0, 256)))


def enroll(wav: Path, embedder) -> np.ndarray:
    """Voiceprint = mean of L2-normalised window embeddings over enrollment audio."""
    _, E = windows(load_wav(wav), embedder)
    if len(E) == 0:
        raise ValueError(f"no usable window in enrollment {wav}. hint: check it is not silent.")
    v = E.mean(axis=0)
    return v / np.linalg.norm(v)


def load_labels(tsv: Path, duration: float):
    rows = []
    for line in tsv.read_text().splitlines():
        if not line.strip():
            continue
        t, spk = line.split("\t")
        m, s = t.split(":")
        rows.append((int(m) * 60 + int(s), spk))
    turns = [(rows[i][0], rows[i + 1][0] if i + 1 < len(rows) else duration, rows[i][1])
             for i in range(len(rows))]

    def at(sec):
        for a, b, spk in turns:
            if a <= sec < b:
                return spk
        return None

    return at


def main() -> None:
    ap = argparse.ArgumentParser(description="Target-speaker (Alastair vs Other) validation.")
    ap.add_argument("--enroll", type=Path,
                    default=REPO / "var/meetings/batch2/wav/GMKtec EVO-X2 intro video_2.wav")
    args = ap.parse_args()
    import soundfile as sf

    embedder = SpeakerEmbedder()
    vp = enroll(args.enroll, embedder)
    print(f"enrolled Alastair voiceprint from {args.enroll.name}\n")

    TESTS = [("survey", "Survey and Training Planning_2"),
             ("leadership", "AI Leadership Strategy Meeting_2"),
             ("dataimport", "Data Import Troubleshooting Meeting_2"),
             ("webinar", "AI in Legal Practice Webinar_2")]

    all_sim_tgt, all_sim_oth = [], []
    print(f"{'recording':14s} {'Alastair sim':>22s} {'Other sim':>22s} {'separation':>10s}")
    print(f"{'':14s} {'mean [p10]':>22s} {'mean [p90]':>22s}")
    print("-" * 72)
    per_rec = []
    for name, stem in TESTS:
        wav = REPO / "var/meetings/wav" / f"{stem}.wav"
        audio = load_wav(wav)
        at = load_labels(REPO / "var/meetings/truth" / f"{name}.tsv", len(audio) / SR)
        times, E = windows(audio, embedder)
        sims = E @ vp
        tgt = np.array([1 if at((a + b) / 2) == TARGET else 0 for a, b in times])
        st, so = sims[tgt == 1], sims[tgt == 0]
        if len(st) and len(so):
            sep = np.mean(st) - np.mean(so)
            all_sim_tgt += list(st); all_sim_oth += list(so)
            per_rec.append((name, st, so))
            print(f"{name:14s} {np.mean(st):6.3f} [{np.percentile(st,10):5.2f}]      "
                  f"{np.mean(so):6.3f} [{np.percentile(so,90):5.2f}]      {sep:+.3f}")

    st = np.array(all_sim_tgt); so = np.array(all_sim_oth)
    print("-" * 72)
    print(f"\nPOOLED: Alastair windows {len(st)}, Other windows {len(so)}")
    print(f"  Alastair sim: mean {st.mean():.3f}, p10 {np.percentile(st,10):.3f}")
    print(f"  Other sim:    mean {so.mean():.3f}, p90 {np.percentile(so,90):.3f}")

    # best single threshold (frame-level accuracy) - swept, then reported honestly
    print(f"\n{'threshold':>10s} {'accuracy':>9s} {'Alastair recall':>16s} {'Other recall':>13s}")
    best = (0, 0.0)
    for thr in np.arange(0.20, 0.66, 0.02):
        tp = (st >= thr).mean(); tn = (so < thr).mean()
        acc = ((st >= thr).sum() + (so < thr).sum()) / (len(st) + len(so))
        if acc > best[1]:
            best = (thr, acc)
        if abs(thr - round(thr, 2)) < 1e-9 and int(thr * 100) % 6 == 0:
            print(f"{thr:10.2f} {100*acc:8.1f}% {100*tp:15.1f}% {100*tn:12.1f}%")
    thr = best[0]
    tp = (st >= thr).mean(); tn = (so < thr).mean()
    print(f"\nBEST threshold {thr:.2f}: accuracy {100*best[1]:.1f}%  "
          f"(Alastair recall {100*tp:.1f}%, Other recall {100*tn:.1f}%)")
    print("NOTE: threshold chosen on the same data it is reported on - an upper bound. A held-out")
    print("      threshold would be slightly lower. The SEPARATION is the model-independent signal.")


if __name__ == "__main__":
    main()
