# File: hybrid_bench.py
# Purpose: Hybrid diarisation - pyannote/segmentation-3.0 as VAD, our WeSpeaker embeddings+clustering.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E46 showed pyannote beats our stack on IHM (6.5% vs 20.3%), and online calls map to IHM.
# The gap is false alarm (our Silero VAD) + confusion (our clustering). This tests swapping ONLY the
# VAD: pyannote/segmentation-3.0 supplies speech regions; everything downstream is our stack
# unchanged (3s/1s windows, WeSpeaker ONNX embeddings, complete-linkage AHC). Pre-reg: e47-...-prereg.
#
# Runs in var/pyannote-venv (has both pyannote/torch AND onnxruntime/kaldi_native_fbank for WeSpeaker).
# The reference construction, four DER policies, and window logic are copied verbatim from
# ami_bench.py so the ONLY variable vs our stack is the VAD. Also times the VAD + embed + cluster
# stages so speed (a stated priority) is measured, not assumed.

from __future__ import annotations

import argparse
import glob
import io
import os
import sys
import time
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))
from spk_embed import SAMPLE_RATE as SR  # noqa: E402
from spk_embed import SpeakerEmbedder  # noqa: E402

WINDOW_S, HOP_S = 3.0, 1.0
HALF_HOP = HOP_S / 2.0


def ref_annotation(starts, ends, speakers):
    from pyannote.core import Annotation, Segment

    ann = Annotation()
    for i, (s, e, spk) in enumerate(zip(starts, ends, speakers)):
        if e > s:
            ann[Segment(s, e), i] = spk
    return ann


def to_annotation(times, labels):
    """Hypothesis from window CENTRES (the E43 fix), merging consecutive same-label slices."""
    from pyannote.core import Annotation, Segment

    ann = Annotation()
    centres = [((s + e) / 2 - HALF_HOP, (s + e) / 2 + HALF_HOP) for s, e in times]
    cs, ce, cl = centres[0][0], centres[0][1], labels[0]
    for (s, e), l in zip(centres[1:], labels[1:]):
        if l == cl and s <= ce + 1e-6:
            ce = e
        else:
            ann[Segment(cs, ce)] = f"spk{cl}"
            cs, ce, cl = s, e, l
    ann[Segment(cs, ce)] = f"spk{cl}"
    return ann


def main() -> None:
    import soundfile as sf
    import torch
    import pyarrow.parquet as pq
    from pyannote.audio import Model
    from pyannote.audio.pipelines import VoiceActivityDetection
    from pyannote.metrics.diarization import DiarizationErrorRate
    from sklearn.cluster import AgglomerativeClustering

    ap = argparse.ArgumentParser(description="Hybrid: pyannote VAD + our embeddings/clustering.")
    ap.add_argument("--condition", choices=["ihm", "sdm"], required=True)
    ap.add_argument("--offset", type=int, default=3)
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--data", type=Path, default=Path("/opt/models/staging/ami"))
    args = ap.parse_args()

    tok = os.environ.get("HF_TOKEN")
    if not tok:
        raise SystemExit(
            "no HF_TOKEN in env. hint: export HF_TOKEN=\"$(python3 /opt/sparkvault/tools/vault_get.py HF_TOKEN)\" - "
            "it is vaulted in apps/sparkmax-host.sops.yaml and readable on sparkmax. "
            "Do NOT source a plaintext env file; the one this hint used to name held 32 "
            "live fleet credentials and was deleted on 2026-08-18."
        )
    shards = sorted(glob.glob(str(args.data / f"{args.condition}-test-*.parquet")))
    if not shards:
        raise FileNotFoundError(f"no AMI shards at {args.data}. hint: see MANIFEST.md.")

    print("loading pyannote/segmentation-3.0 as VAD ...", flush=True)
    seg = Model.from_pretrained("pyannote/segmentation-3.0", token=tok)
    vad = VoiceActivityDetection(segmentation=seg)
    vad.instantiate({"min_duration_on": 0.0, "min_duration_off": 0.0})
    embedder = SpeakerEmbedder()

    metrics = {
        "collar0.25 overlap-skipped": DiarizationErrorRate(collar=0.25, skip_overlap=True),
        "collar0.25 overlap-SCORED": DiarizationErrorRate(collar=0.25, skip_overlap=False),
        "collar0.0  overlap-skipped": DiarizationErrorRate(collar=0.0, skip_overlap=True),
        "collar0.0  overlap-SCORED": DiarizationErrorRate(collar=0.0, skip_overlap=False),
    }
    print(f"HYBRID (pyannote-seg VAD + WeSpeaker + complete AHC) | AMI {args.condition.upper()}\n")
    print(f"{'meeting':22s} {'min':>5s} {'DER(.25,skip)':>13s} {'vad_s':>6s} {'emb_s':>6s}", flush=True)
    print("-" * 60)

    seen = n = 0
    tot_audio = tot_vad = tot_emb = 0.0
    for shard in shards:
        t = pq.ParquetFile(shard).read()
        for i in range(t.num_rows):
            if seen < args.offset:
                seen += 1
                continue
            if n >= args.limit:
                break
            row = {c: t.column(c)[i].as_py() for c in t.column_names}
            audio, sr = sf.read(io.BytesIO(row["audio"]["bytes"]), dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            dur = len(audio) / sr
            k = len(set(row["speakers"]))

            t0 = time.time()
            vout = vad({"waveform": torch.from_numpy(audio).unsqueeze(0), "sample_rate": sr})
            regions = [(s.start, s.end) for s in vout.get_timeline()]
            t_vad = time.time() - t0

            t1 = time.time()
            win, hop = int(WINDOW_S * SR), int(HOP_S * SR)
            times, embs = [], []
            for st in range(0, len(audio) - win + 1, hop):
                a, b = st / SR, (st + win) / SR
                mid = (a + b) / 2
                if not any(rs <= mid <= re for rs, re in regions):
                    continue
                times.append((a, b))
                embs.append(embedder.embed(audio[st : st + win]))
            if not embs:
                print(f"{row['audio']['path'][:22]:22s} {dur/60:5.1f}   (no speech windows)")
                n += 1
                continue
            E = np.vstack(embs)
            labels = (np.zeros(len(embs), dtype=int) if len(embs) == 1
                      else AgglomerativeClustering(n_clusters=min(k, len(embs)),
                           metric="cosine", linkage="complete").fit_predict(E))
            t_emb = time.time() - t1

            hyp = to_annotation(times, labels)
            ref = ref_annotation(row["timestamps_start"], row["timestamps_end"], row["speakers"])
            for m in metrics.values():
                m(ref, hyp)
            d1 = DiarizationErrorRate(collar=0.25, skip_overlap=True)(ref, hyp)
            tot_audio += dur; tot_vad += t_vad; tot_emb += t_emb
            print(f"{row['audio']['path'][:22]:22s} {dur/60:5.1f} {100*d1:12.1f}% "
                  f"{t_vad:6.1f} {t_emb:6.1f}", flush=True)
            n += 1
        if n >= args.limit:
            break

    print("-" * 60)
    print(f"\nAGGREGATE over {n} meetings (HYBRID, {args.condition.upper()}):\n")
    print(f"{'scoring policy':28s} {'DER':>7s} {'miss':>7s} {'FA':>7s} {'conf':>7s}")
    print("-" * 60)
    for name, m in metrics.items():
        r = abs(m)
        det = m[:]
        tot = det["total"] or 1
        print(f"{name:28s} {100*r:6.1f}% {100*det['missed detection']/tot:6.1f}% "
              f"{100*det['false alarm']/tot:6.1f}% {100*det['confusion']/tot:6.1f}%")
    if tot_vad + tot_emb > 0:
        print(f"\nSPEED: {tot_audio/60:.0f} min audio | VAD {tot_vad:.0f}s + embed/cluster {tot_emb:.0f}s "
              f"= {tot_audio/(tot_vad+tot_emb):.0f}x real time (CPU; GPU free)")


if __name__ == "__main__":
    main()
