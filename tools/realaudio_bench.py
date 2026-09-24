# File: realaudio_bench.py
# Purpose: ours vs hybrid vs pyannote on the REAL Otter-referenced online calls - the deployment test.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E47 showed the hybrid (pyannote VAD + our embeddings) cuts AMI IHM error 48%. AMI IHM is
# a proxy for online calls; this is the direct test on Alastair's actual Zoom/Teams recordings.
#
# METRIC CHOICE - forced by the reference. The Otter references are speaker TURNS with no silence
# annotation: each turn runs to the next, so Otter thinks someone talks 100% of the time. Standard
# DER would therefore PENALISE a good VAD as "miss" (correct silence scored as missed speech), which
# is backwards. So we report the two things Otter CAN support honestly:
#   - COVERAGE: fraction of the recording each system labels as speech (completeness; lower is not
#     automatically better, but our energy-gate over-covered on AMI, so a drop toward truth is good).
#   - ATTRIBUTION ACCURACY: over each system's OWN detected speech, the duration-weighted fraction
#     where its speaker label maps (Hungarian) to Otter's speaker at that time. This is the
#     "who said it" quality that meeting notes need, and the metric where E47's clustering-cleanup
#     effect should show if it is real on this audio.
#
# Real client recordings = personal data: audio, transcripts and per-recording numbers stay in
# gitignored var/meetings/. Only aggregate, de-identified figures go in the committed writeup.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from spk_embed import SAMPLE_RATE as SR  # noqa: E402
from spk_embed import SpeakerEmbedder, load_wav  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
WIN_S, HOP_S = 3.0, 1.0
VAD_BINARY = REPO / "whisper.cpp/build/bin/whisper-vad-speech-segments"
VAD_GGML = Path("/opt/models/staging/whisper/ggml-silero-v6.2.0.bin")

RECORDINGS = [
    ("planning-4spk", "Survey and Training Planning_2", "survey"),
    ("client-call-2spk", "AI Leadership Strategy Meeting_2", "leadership"),
    ("client-call-2spk-b", "Data Import Troubleshooting Meeting_2", "dataimport"),
    ("webinar-multi", "AI in Legal Practice Webinar_2", "webinar"),
]


def load_reference(tsv: Path, duration: float):
    rows = []
    for line in tsv.read_text().splitlines():
        if not line.strip():
            continue
        t, spk = line.split("\t")
        m, s = t.split(":")
        rows.append((int(m) * 60 + int(s), spk))
    turns = [(rows[i][0], rows[i + 1][0] if i + 1 < len(rows) else duration, rows[i][1])
             for i in range(len(rows))]

    def at(sec: float):
        for a, b, spk in turns:
            if a <= sec < b:
                return spk
        return None

    # effective speakers = those holding >= 1% of reference time (drops Otter's ~2s singletons)
    span = {}
    for a, b, spk in turns:
        span[spk] = span.get(spk, 0.0) + (b - a)
    total = sum(span.values()) or 1
    eff = [s for s, v in span.items() if v / total >= 0.01]
    return at, eff


def silero_regions(wav: Path, threshold: float = 0.10):
    proc = subprocess.run(
        [str(VAD_BINARY), "-np", "-vm", str(VAD_GGML), "-vt", str(threshold), "-f", str(wav)],
        capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        raise RuntimeError(f"silero VAD failed: {proc.stderr[-200:]}")
    out = []
    for line in proc.stdout.splitlines():
        if line.startswith("Speech segment"):
            a, b = line.split("start = ")[1].split(", end = ")
            out.append((float(a) / 100.0, float(b) / 100.0))
    return out


def cluster_over_regions(audio, regions, k, embedder):
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
        return []
    labels = (np.zeros(len(embs), dtype=int) if len(embs) == 1
              else AgglomerativeClustering(n_clusters=min(k, len(embs)), metric="cosine",
                   linkage="complete").fit_predict(np.vstack(embs)))
    # (start, end, label) at hop granularity around each window centre
    half = HOP_S / 2
    return [((a + b) / 2 - half, (a + b) / 2 + half, int(l)) for (a, b), l in zip(times, labels)]


def score(segments, at, eff, duration):
    """coverage + duration-weighted attribution accuracy (Hungarian label->Otter speaker)."""
    from scipy.optimize import linear_sum_assignment

    if not segments:
        return 0.0, 0.0
    coverage = sum(e - s for s, e, _ in segments) / duration
    labels = sorted({l for _, _, l in segments})
    # build confusion (system label x Otter speaker) over speech time where Otter names an eff speaker
    M = np.zeros((len(labels), len(eff)))
    for s, e, l in segments:
        mid = (s + e) / 2
        g = at(mid)
        if g in eff:
            M[labels.index(l), eff.index(g)] += (e - s)
    if M.sum() == 0:
        return coverage, 0.0
    r, c = linear_sum_assignment(-M)
    acc = M[r, c].sum() / M.sum()
    return coverage, acc


def main() -> None:
    import soundfile as sf
    import torch
    from pyannote.audio import Model, Pipeline
    from pyannote.audio.pipelines import VoiceActivityDetection

    ap = argparse.ArgumentParser(description="ours/hybrid/pyannote on real Otter-referenced calls.")
    ap.add_argument("--systems", default="ours,hybrid,pyannote")
    ap.add_argument("--out", type=Path, default=REPO / "var/meetings/realaudio-results.json")
    args = ap.parse_args()
    systems = args.systems.split(",")
    import os
    tok = os.environ.get("HF_TOKEN")

    embedder = SpeakerEmbedder()
    seg_vad = pyann_pipe = None
    if "hybrid" in systems:
        seg_vad = VoiceActivityDetection(segmentation=Model.from_pretrained(
            "pyannote/segmentation-3.0", token=tok))
        seg_vad.instantiate({"min_duration_on": 0.0, "min_duration_off": 0.0})
    if "pyannote" in systems:
        pyann_pipe = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", token=tok)

    results = []
    for label, stem, truth in RECORDINGS:
        wav = REPO / "var/meetings/wav" / f"{stem}.wav"
        audio = load_wav(wav)
        dur = len(audio) / SR
        at, eff = load_reference(REPO / "var/meetings/truth" / f"{truth}.tsv", dur)
        k = len(eff)
        row = {"recording": label, "min": round(dur / 60, 1), "k": k}
        print(f"\n=== {label} ({dur/60:.1f} min, k={k}) ===", flush=True)

        if "ours" in systems:
            t0 = time.time()
            segs = cluster_over_regions(audio, silero_regions(wav), k, embedder)
            cov, acc = score(segs, at, eff, dur)
            row["ours"] = {"coverage": round(cov, 3), "attr_acc": round(acc, 3),
                           "rt": round(dur / (time.time() - t0), 1)}
            print(f"  ours     coverage {cov*100:4.0f}%  attribution {acc*100:5.1f}%", flush=True)

        if "hybrid" in systems:
            t0 = time.time()
            vout = seg_vad({"waveform": torch.from_numpy(audio).unsqueeze(0), "sample_rate": SR})
            regs = [(s.start, s.end) for s in vout.get_timeline()]
            segs = cluster_over_regions(audio, regs, k, embedder)
            cov, acc = score(segs, at, eff, dur)
            row["hybrid"] = {"coverage": round(cov, 3), "attr_acc": round(acc, 3),
                             "rt": round(dur / (time.time() - t0), 1)}
            print(f"  hybrid   coverage {cov*100:4.0f}%  attribution {acc*100:5.1f}%", flush=True)

        if "pyannote" in systems:
            t0 = time.time()
            out = pyann_pipe({"waveform": torch.from_numpy(audio).unsqueeze(0),
                              "sample_rate": SR}, num_speakers=k)
            segs = [(s.start, s.end, lbl) for s, _, lbl in
                    out.speaker_diarization.itertracks(yield_label=True)]
            cov, acc = score(segs, at, eff, dur)
            row["pyannote"] = {"coverage": round(cov, 3), "attr_acc": round(acc, 3),
                               "rt": round(dur / (time.time() - t0), 1)}
            print(f"  pyannote coverage {cov*100:4.0f}%  attribution {acc*100:5.1f}%", flush=True)

        results.append(row)

    args.out.write_text(json.dumps(results, indent=1))
    print(f"\nwrote {args.out} (gitignored - real client audio)")


if __name__ == "__main__":
    main()
