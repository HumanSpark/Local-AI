# File: tools/diarise_eval.py
# Purpose: Score our diarisation against a reference (Otter.ai) - DER + speaker-count methods.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: Frame-level DER against a reference TSV of "M:SS<TAB>speaker" turn starts (segment end =
# next start). Embeds 3s sliding windows, clusters at each candidate k, and reports the optimal
# cluster->speaker assignment (Hungarian) so cluster IDs need not match reference labels. Also scores
# the two speaker-COUNT choosers that disagreed on the first recording (>=2%-of-windows vs
# silhouette) so the choice can be validated across recordings rather than on n=1.
#
# The reference is Otter.ai, a commercial system - NOT human ground truth. Its own errors are inside
# any DER reported here. Reference TSVs live in gitignored var/meetings/truth/ (real personal data).

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from spk_embed import SAMPLE_RATE as SR  # noqa: E402
from spk_embed import SpeakerEmbedder, load_wav  # noqa: E402

WINDOW_S, HOP_S, ENERGY_FLOOR = 3.0, 1.0, 1e-3


def load_reference(tsv: Path, duration: float) -> list[tuple[float, float, str]]:
    rows = []
    for line in tsv.read_text().splitlines():
        if not line.strip():
            continue
        try:
            t, spk = line.split("\t")
            parts = [int(x) for x in t.split(":")]
        except ValueError as exc:
            raise ValueError(
                f"bad reference line in {tsv}: {line!r}. hint: expected 'M:SS<TAB>Speaker'."
            ) from exc
        secs = parts[0] * 60 + parts[1] if len(parts) == 2 else parts[0] * 3600 + parts[1] * 60 + parts[2]
        rows.append((secs, spk))
    return [(rows[i][0], rows[i + 1][0] if i + 1 < len(rows) else duration, rows[i][1])
            for i in range(len(rows))]


def embed_windows(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    emb = SpeakerEmbedder()
    win, hop = int(WINDOW_S * SR), int(HOP_S * SR)
    if len(audio) < win:
        raise ValueError(f"audio shorter than one {WINDOW_S}s window. hint: need a few seconds.")
    times, embs = [], []
    for st in range(0, len(audio) - win + 1, hop):
        c = audio[st : st + win]
        if float(np.sqrt(np.mean(c**2))) < ENERGY_FLOOR:
            continue
        times.append(st / SR + WINDOW_S / 2)
        embs.append(emb.embed(c))
    if not embs:
        raise ValueError("all windows below the energy floor. hint: check the recording is not silent.")
    return np.array(times), np.vstack(embs)


def evaluate(wav: Path, tsv: Path, kmax: int = 8) -> None:
    from scipy.optimize import linear_sum_assignment
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score

    audio = load_wav(wav)
    ref = load_reference(tsv, len(audio) / SR)
    times, E = embed_windows(audio)

    def ref_at(t: float) -> str | None:
        for s, e, spk in ref:
            if s <= t < e:
                return spk
        return None

    gt_all = [ref_at(t) for t in times]
    keep = [i for i, g in enumerate(gt_all) if g and g != "Unknown"]
    gt = [gt_all[i] for i in keep]
    true_speakers = sorted(set(gt))

    print(f"\n{'='*78}\n{wav.name}")
    print(f"  {len(audio)/SR/60:.1f} min | {len(E)} windows | reference: {len(true_speakers)} speakers "
          f"({len(ref)} turns)")
    counts = {s: sum(1 for g in gt if g == s) for s in true_speakers}
    print("  reference speaker share: " +
          ", ".join(f"{s}={100*c/len(gt):.1f}%" for s, c in sorted(counts.items(), key=lambda x: -x[1])))

    # MAJORITY BASELINE: what a system that always emits the dominant speaker would score.
    # DER is meaningless without it - on a one-presenter recording a BROKEN single-label system
    # posts a spectacular DER. Never report DER without this number beside it.
    baseline_der = 100 - 100 * max(counts.values()) / len(gt)
    print(f"  ** MAJORITY BASELINE: DER {baseline_der:.1f}% "
          f"(a system that always says '{max(counts, key=counts.get)}' and nothing else) **")

    print(f"\n  {'k':>2s} {'DER':>7s} {'acc':>7s} {'vs base':>8s}  {'>=2% clusters':>14s} {'silhouette':>11s}")
    best = (None, 1e9)
    for k in range(2, kmax + 1):
        lab = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average").fit_predict(E)
        sil = silhouette_score(E, lab, metric="cosine")
        nbig = int((np.bincount(lab) >= len(E) * 0.02).sum())
        p = [lab[i] for i in keep]
        cls = sorted(set(p))
        M = np.zeros((len(true_speakers), len(cls)))
        for g, pi in zip(gt, p):
            M[true_speakers.index(g), cls.index(pi)] += 1
        r, c = linear_sum_assignment(-M)
        acc = M[r, c].sum() / len(gt)
        der = 100 - acc * 100
        if der < best[1]:
            best = (k, der)
        delta = baseline_der - der
        verdict = f"{delta:+6.1f}"
        print(f"  {k:2d} {der:6.1f}% {acc*100:6.1f}% {verdict:>8s}  {nbig:14d} {sil:11.4f}")
    print(f"\n  best achievable: DER {best[1]:.1f}% at k={best[0]}   "
          f"(reference says k={len(true_speakers)})")
    if best[1] >= baseline_der:
        print(f"  ** WORSE THAN THE MAJORITY BASELINE ({baseline_der:.1f}%) - on this recording the "
              f"system adds NOTHING over always guessing the dominant speaker. **")
    else:
        print(f"  beats the majority baseline ({baseline_der:.1f}%) by {baseline_der-best[1]:.1f} points")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Score diarisation against an Otter.ai reference transcript.",
        epilog="example: var/diar-venv/bin/python tools/diarise_eval.py a.wav truth.tsv",
    )
    ap.add_argument("wav", type=Path)
    ap.add_argument("reference", type=Path, help="TSV of 'M:SS<TAB>Speaker' turn starts")
    ap.add_argument("--kmax", type=int, default=8)
    args = ap.parse_args()
    for p in (args.wav, args.reference):
        if not p.exists():
            raise FileNotFoundError(f"missing {p}. hint: check var/meetings/ paths.")
    evaluate(args.wav, args.reference, args.kmax)


if __name__ == "__main__":
    main()
