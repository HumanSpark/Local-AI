# File: tools/pyannote_bench.py
# Purpose: Score pyannote 3.1 on the SAME AMI harness as our stack - the honest head-to-head.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E44 put our stack at 20.2% DER (held out) vs pyannote's PUBLISHED ~9-11%. That comparison
# is a cross-paper hand-wave: different papers use different collars, overlap policies and subsets,
# and those choices move DER by more than the gap. This runs pyannote 3.1 on the identical AMI
# meetings, the identical pyannote.metrics DER, the identical four scoring policies, and the identical
# offset (so the same 13 held-out meetings we reported our number on). Only then is "ours vs theirs"
# a real number.
#
# Two things kept parallel to ami_bench.py on purpose:
#   - same reference construction (ref_annotation with track indices for overlap)
#   - same four metrics (collar {0, 0.25} x overlap {scored, skipped})
#
# Runs on CPU (torchcodec cannot decode on this AMD box; audio is fed in-memory as pyannote's own
# error message prescribes). Isolated var/pyannote-venv - NEVER var/ft-venv (F37 protection). The
# GPU stays free for llama-server throughout.
#
# pyannote is given the true speaker count via num_speakers, matching how we supply k to our stack -
# an apples-to-apples choice, since k is known from the meeting invite in deployment (E39/E40).

from __future__ import annotations

import argparse
import glob
import io
import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")


def ref_annotation(starts, ends, speakers):
    from pyannote.core import Annotation, Segment

    ann = Annotation()
    for i, (s, e, spk) in enumerate(zip(starts, ends, speakers)):
        if e > s:
            ann[Segment(s, e), i] = spk
    return ann


def main() -> None:
    import soundfile as sf
    import torch
    import pyarrow.parquet as pq
    from pyannote.audio import Pipeline
    from pyannote.metrics.diarization import DiarizationErrorRate

    ap = argparse.ArgumentParser(
        description="Score pyannote 3.1 on the AMI harness (same metric/collar/split as ours).",
        epilog="example: var/pyannote-venv/bin/python tools/pyannote_bench.py --condition ihm --offset 3",
    )
    ap.add_argument("--condition", choices=["ihm", "sdm"], required=True)
    ap.add_argument("--offset", type=int, default=3,
                    help="skip the first N meetings (default 3 = the held-out set we reported ours on)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--data", type=Path, default=Path("/opt/models/staging/ami"))
    ap.add_argument("--model", default="pyannote/speaker-diarization-3.1")
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
        raise FileNotFoundError(f"no AMI shards at {args.data}. hint: see manifests/MANIFEST.md.")

    print(f"loading {args.model} ...", flush=True)
    pipe = Pipeline.from_pretrained(args.model, token=tok)

    metrics = {
        "collar0.25 overlap-skipped": DiarizationErrorRate(collar=0.25, skip_overlap=True),
        "collar0.25 overlap-SCORED": DiarizationErrorRate(collar=0.25, skip_overlap=False),
        "collar0.0  overlap-skipped": DiarizationErrorRate(collar=0.0, skip_overlap=True),
        "collar0.0  overlap-SCORED": DiarizationErrorRate(collar=0.0, skip_overlap=False),
    }
    print(f"pyannote {args.model} | AMI {args.condition.upper()} | offset {args.offset}\n")
    print(f"{'meeting':22s} {'min':>5s} {'k':>2s} {'DER(0.25,skip)':>14s} {'DER(0.25,ovl)':>13s}", flush=True)
    print("-" * 62)

    seen = n = 0
    for shard in shards:
        t = pq.ParquetFile(shard).read()
        for i in range(t.num_rows):
            if seen < args.offset:
                seen += 1
                continue
            if args.limit and n >= args.limit:
                break
            row = {c: t.column(c)[i].as_py() for c in t.column_names}
            audio, sr = sf.read(io.BytesIO(row["audio"]["bytes"]), dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            k = len(set(row["speakers"]))
            wav = {"waveform": torch.from_numpy(audio).unsqueeze(0), "sample_rate": sr}
            out = pipe(wav, num_speakers=k)
            # pyannote 4.x returns DiarizeOutput. .speaker_diarization is the FULL output (can assign
            # overlapping speakers - a capability our single-label stack lacks). We score that: it is
            # pyannote's real capability and the honest "ours vs theirs".
            hyp = out.speaker_diarization
            ref = ref_annotation(row["timestamps_start"], row["timestamps_end"], row["speakers"])
            for m in metrics.values():
                m(ref, hyp)
            d1 = DiarizationErrorRate(collar=0.25, skip_overlap=True)(ref, hyp)
            d2 = DiarizationErrorRate(collar=0.25, skip_overlap=False)(ref, hyp)
            print(f"{row['audio']['path'][:22]:22s} {len(audio)/sr/60:5.1f} {k:2d} "
                  f"{100*d1:13.1f}% {100*d2:12.1f}%", flush=True)
            n += 1
        if args.limit and n >= args.limit:
            break

    print("-" * 62)
    print(f"\nAGGREGATE over {n} meetings (pyannote 3.1, {args.condition.upper()}):\n")
    print(f"{'scoring policy':28s} {'DER':>7s} {'miss':>7s} {'FA':>7s} {'conf':>7s}")
    print("-" * 60)
    for name, m in metrics.items():
        r = abs(m)
        det = m[:]
        tot = det["total"] or 1
        print(f"{name:28s} {100*r:6.1f}% {100*det['missed detection']/tot:6.1f}% "
              f"{100*det['false alarm']/tot:6.1f}% {100*det['confusion']/tot:6.1f}%")


if __name__ == "__main__":
    main()
