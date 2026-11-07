# File: tools/spk_embed_validate.py
# Purpose: Positive control - prove the speaker embedder discriminates speakers before trusting it.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Runs the pre-registered predictions in results/diarisation/embedder-validation-prereg.md
# (committed c6e489d BEFORE this ran). Scores cosine similarity for same-speaker and
# different-speaker pairs drawn from REAL audio (jfk.wav, split in half) and synthetic audio
# (twospeaker.wav cut on exact ground-truth boundaries). The decisive output is the SEPARATION
# MARGIN: min(same) - max(different). Clustering can only work if the two populations separate;
# individual scores matter less than the gap between them.
#
# This exists because a wrong fbank pipeline yields embeddings that are silently wrong rather than
# obviously broken - still 256-dim, still normalised, still clusterable into noise.

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from spk_embed import SpeakerEmbedder, cosine, load_wav  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
JFK = REPO / "whisper.cpp/samples/jfk.wav"
TWOSPK = REPO / "results/diarisation/twospeaker.wav"
TRUTH = REPO / "results/diarisation/twospeaker-truth.json"
SR = 16000


def main() -> None:
    emb = SpeakerEmbedder()

    for p in (JFK, TWOSPK, TRUTH):
        if not p.exists():
            raise FileNotFoundError(
                f"required fixture missing: {p}. "
                "hint: jfk.wav ships with whisper.cpp; twospeaker.wav is built by the "
                "Kokoro fixture builder (see results/diarisation/tdrz-probe.md)."
            )

    # --- REAL audio: one human, split in half -> P1 (the load-bearing prediction) ---
    jfk = load_wav(JFK)
    mid = len(jfk) // 2
    e_jfk_a = emb.embed(jfk[:mid])
    e_jfk_b = emb.embed(jfk[mid:])

    # --- Synthetic: cut on exact ground-truth boundaries ---
    audio = load_wav(TWOSPK)
    script = json.loads(TRUTH.read_text())["script"]
    by_spk: dict[str, list[np.ndarray]] = {}
    for turn in script:
        chunk = audio[int(turn["start_s"] * SR) : int(turn["end_s"] * SR)]
        by_spk.setdefault(turn["speaker"], []).append(emb.embed(chunk))

    emma, george = by_spk["bf_emma"], by_spk["bm_george"]

    results = [
        ("P1", "jfk 1st half vs jfk 2nd half", "SAME (real)", cosine(e_jfk_a, e_jfk_b), ">", 0.5),
        ("P2", "bf_emma vs bm_george", "DIFFERENT", cosine(emma[0], george[0]), "<", 0.3),
        ("P3", "bf_emma turn0 vs turn1", "SAME (synth)", cosine(emma[0], emma[1]), ">", 0.5),
        ("P4", "bm_george turn0 vs turn1", "SAME (synth)", cosine(george[0], george[1]), ">", 0.5),
        ("P5", "jfk vs bm_george", "DIFFERENT (x-domain)", cosine(e_jfk_a, george[0]), "<", 0.3),
    ]

    print(f"{'ID':4s} {'pair':34s} {'truth':22s} {'cosine':>8s}  {'pred':>8s}  verdict")
    print("-" * 92)
    verdicts = {}
    for pid, pair, truth, val, op, thr in results:
        ok = (val > thr) if op == ">" else (val < thr)
        verdicts[pid] = ok
        print(f"{pid:4s} {pair:34s} {truth:22s} {val:8.4f}  {op:>2s}{thr:6.2f}  {'HIT' if ok else 'MISS'}")

    # --- P6: the decisive separation margin, computed over ALL pairs ---
    all_emb = [("jfk", e_jfk_a), ("jfk", e_jfk_b)]
    all_emb += [("bf_emma", e) for e in emma] + [("bm_george", e) for e in george]
    same, diff = [], []
    for i in range(len(all_emb)):
        for j in range(i + 1, len(all_emb)):
            (s1, a), (s2, b) = all_emb[i], all_emb[j]
            (same if s1 == s2 else diff).append(cosine(a, b))

    margin = min(same) - max(diff)
    verdicts["P6"] = margin > 0.2
    print("-" * 92)
    print(f"\nAll pairs: {len(same)} same-speaker, {len(diff)} different-speaker")
    print(f"  same-speaker      min={min(same):.4f} mean={np.mean(same):.4f} max={max(same):.4f}")
    print(f"  different-speaker min={min(diff):.4f} mean={np.mean(diff):.4f} max={max(diff):.4f}")
    print(f"\nP6 SEPARATION MARGIN = min(same) - max(diff) = "
          f"{min(same):.4f} - {max(diff):.4f} = {margin:+.4f}   "
          f"(pred > 0.20) -> {'HIT' if verdicts['P6'] else 'MISS'}")

    p1, p6 = verdicts["P1"], verdicts["P6"]
    print("\n" + "=" * 92)
    if p1 and p6:
        print("EXTRACTOR VALIDATED (P1 + P6 hold). Per the pre-registered disposition rule:")
        print("  -> proceed to build the clustering pipeline.")
    elif not p1:
        print("P1 FAILED -> the feature pipeline is wrong. Per the disposition rule: do NOT")
        print("  proceed and do NOT tune thresholds. Suspect fbank scaling / CMN / dither.")
    else:
        print("P1 held but P6 FAILED -> signal present but not separable. Investigate before")
        print("  building anything on top.")
    print("=" * 92)
    sys.exit(0 if (p1 and p6) else 1)


if __name__ == "__main__":
    main()
