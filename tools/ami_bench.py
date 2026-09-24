# File: tools/ami_bench.py
# Purpose: Score the primary diarisation config against AMI - real human ground truth, standard DER.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: The first evaluation of our stack that does not rest on a reference I typed by hand.
# Every prior diarisation number (E38-E40, 3.51% duration-weighted segment error) was measured
# against an Otter.ai transcript (~98% accurate, hand-copied, one dropped turn that I blamed on the
# model for two write-ups) across four recordings that all contain the same voice. AMI removes all
# of it: human annotation, public corpus, unseen speakers, a far-field condition, and 17% overlapped
# speech that our single-label-per-window design cannot represent at all.
#
# Two deliberate choices that remove ME as a variable:
#   1. DER comes from pyannote.metrics (the standard implementation), not from my code.
#   2. The reference comes from the corpus, not from my typing.
#
# Reported four ways because the number moves enormously with scoring policy, and papers differ:
# {collar 0.0, collar 0.25} x {overlap scored, overlap skipped}. Quoting one number without its
# policy is how DER figures become incomparable - see the E42/F17 lesson about flattering metrics.
#
# Speaker count is SUPPLIED from the reference (k is an input in deployment - the meeting invite
# lists attendees; automatic estimation is unsolved, see E39/E40).

from __future__ import annotations

import argparse
import glob
import io
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from spk_embed import SAMPLE_RATE as SR  # noqa: E402
from spk_embed import SpeakerEmbedder  # noqa: E402

WINDOW_S, HOP_S, ENERGY_FLOOR = 3.0, 1.0, 1e-3


def load_meeting(row: dict) -> tuple[np.ndarray, list, list, list]:
    import soundfile as sf

    audio, sr = sf.read(io.BytesIO(row["audio"]["bytes"]), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != SR:
        raise ValueError(f"{row['audio']['path']} is {sr} Hz, expected {SR}. "
                         "hint: AMI from diarizers-community should already be 16 kHz.")
    return audio, row["timestamps_start"], row["timestamps_end"], row["speakers"]


def speech_mask(audio: np.ndarray, wav_path: Path, threshold: float = 0.5) -> list[tuple[float, float]]:
    """Silero VAD speech regions via whisper.cpp's whisper-vad-speech-segments.

    E43 finding: the energy gate (RMS > 1e-3) is NOT a VAD. On AMI it produced 20.2% FALSE ALARM of
    a 29.2% DER - 69% of all error - because breathing, paper and keyboards clear a volume
    threshold. Confusion was only 8.7%, so the speaker model was never the problem.

    Uses whisper.cpp's own VAD binary rather than our onnxruntime port: same Silero weights, but the
    C++ implementation is the one that demonstrably works here (it is what kills the "Thank you"
    fabrication, F44). Our ONNX port under-detected relative to it (60.9% vs 71.4% on jfk.wav).
    Rejected alternative, recorded so it is not retried: whisper's SEGMENTS as a mask cover 97-98.5%
    of a recording vs 65-83% real speech - they span pauses between words by design.

    Output timestamps are CENTISECONDS (1/100 s), per the tool's own usage note.
    """
    import subprocess

    binary = Path(__file__).resolve().parent.parent / "whisper.cpp/build/bin/whisper-vad-speech-segments"
    vad_model = Path("/opt/models/staging/whisper/ggml-silero-v6.2.0.bin")
    for p in (binary, vad_model):
        if not p.exists():
            raise FileNotFoundError(
                f"missing {p}. hint: build with `cmake --build build --target "
                "whisper-vad-speech-segments`; model per manifests/MANIFEST.md."
            )
    try:
        proc = subprocess.run(
            [str(binary), "-np", "-vm", str(vad_model), "-vt", str(threshold), "-f", str(wav_path)],
            capture_output=True, text=True, timeout=1800,
        )
    except subprocess.TimeoutExpired as exc:
        raise TimeoutError(f"VAD exceeded 1800s on {wav_path}. hint: check the GPU is not wedged.") from exc
    if proc.returncode != 0:
        raise RuntimeError(f"VAD failed (rc={proc.returncode}): {proc.stderr[-300:]}")
    regions = []
    for line in proc.stdout.splitlines():
        if not line.startswith("Speech segment"):
            continue
        try:
            body = line.split("start = ")[1]
            a, b = body.split(", end = ")
            regions.append((float(a) / 100.0, float(b) / 100.0))   # centiseconds -> seconds
        except (IndexError, ValueError) as exc:
            raise ValueError(f"could not parse VAD line {line!r}: {exc}. "
                             "hint: the tool's output format may have changed.") from exc
    if not regions:
        raise ValueError(f"VAD found no speech in {wav_path}. hint: check the audio is not silent.")
    return regions


def diarise_windows(audio: np.ndarray, k: int, embedder: SpeakerEmbedder,
                    mask: list[tuple[float, float]] | None = None):
    """Our primary config: 3s/1s windows, complete-linkage AHC at supplied k.

    mask=None reproduces the energy-gate behaviour (the E43 control). mask=<VAD regions> is the
    fixed config: windows are kept only where a real VAD says there is speech.
    """
    from sklearn.cluster import AgglomerativeClustering

    win, hop = int(WINDOW_S * SR), int(HOP_S * SR)
    times, embs = [], []
    for st in range(0, len(audio) - win + 1, hop):
        a, b = st / SR, (st + win) / SR
        c = audio[st : st + win]
        if mask is None:
            if float(np.sqrt(np.mean(c**2))) < ENERGY_FLOOR:
                continue
        else:
            # keep the window only if its CENTRE lies inside a VAD speech region
            mid = (a + b) / 2
            if not any(s <= mid <= e for s, e in mask):
                continue
        times.append((a, b))
        embs.append(embedder.embed(c))
    if not embs:
        raise ValueError("every window below the energy floor. hint: check the audio is not silent.")
    E = np.vstack(embs)
    if len(embs) == 1 or k <= 1:
        labels = np.zeros(len(embs), dtype=int)
    else:
        labels = AgglomerativeClustering(
            n_clusters=min(k, len(embs)), metric="cosine", linkage="complete"
        ).fit_predict(E)
    return times, labels


def to_annotation(times, labels):
    """Build the hypothesis from window CENTRES, not window spans.

    E43 bug (mine): emitting each window as its full 3s span (start, start+3) and merging
    overlapping ones glues a ~3s tail onto every speech region, because a 3s window is a decision
    about its CENTRE - not a claim that all 3 seconds belong to that speaker. That manufactured
    false alarm the system never committed: measured coverage 92.9% of the recording from an
    energy gate that kept 92.9% of WINDOWS, yet DER reported 40.7% FA. Each window now contributes
    only the HOP-width slice it actually decides.
    """
    from pyannote.core import Annotation, Segment

    ann = Annotation()
    half = HOP_S / 2.0
    centres = [((s + e) / 2.0 - half, (s + e) / 2.0 + half) for s, e in times]
    cur_s, cur_e, cur_l = centres[0][0], centres[0][1], labels[0]
    for (s, e), l in zip(centres[1:], labels[1:]):
        if l == cur_l and s <= cur_e + 1e-6:
            cur_e = e
        else:
            ann[Segment(cur_s, cur_e)] = f"spk{cur_l}"
            cur_s, cur_e, cur_l = s, e, l
    ann[Segment(cur_s, cur_e)] = f"spk{cur_l}"
    return ann


def ref_annotation(starts, ends, speakers):
    from pyannote.core import Annotation, Segment

    ann = Annotation()
    for i, (s, e, spk) in enumerate(zip(starts, ends, speakers)):
        if e > s:
            ann[Segment(s, e), i] = spk      # track index keeps overlapping segments distinct
    return ann


def main() -> None:
    from pyannote.metrics.diarization import DiarizationErrorRate
    import pyarrow.parquet as pq

    ap = argparse.ArgumentParser(
        description="Score the primary diarisation config against AMI with standard DER.",
        epilog="example: var/diar-venv/bin/python tools/ami_bench.py --condition ihm",
    )
    ap.add_argument("--condition", choices=["ihm", "sdm"], required=True)
    ap.add_argument("--limit", type=int, default=None, help="first N meetings only")
    ap.add_argument("--offset", type=int, default=0,
                    help="skip the first N meetings. The VAD threshold was tuned on the first 3, "
                         "so --offset 3 gives a genuinely HELD-OUT report set (13 meetings).")
    ap.add_argument("--data", type=Path, default=Path("/opt/models/staging/ami"))
    ap.add_argument("--vad", action="store_true",
                    help="gate windows with Silero VAD instead of the energy floor (E43: the "
                         "energy floor causes 20.2%% false alarm = 69%% of all DER)")
    ap.add_argument("--vad-threshold", type=float, default=0.5,
                    help="Silero threshold. LOWER = more speech kept = less miss, more false "
                         "alarm. This is the FA/miss dial (default 0.5 = Silero's own default)")
    ap.add_argument("--scratch", type=Path,
                    default=Path("/tmp/claude-1001/-home-agent-spark-sparkbench/ami-scratch"))
    args = ap.parse_args()

    shards = sorted(glob.glob(str(args.data / f"{args.condition}-test-*.parquet")))
    if not shards:
        raise FileNotFoundError(f"no AMI shards at {args.data}. hint: see manifests/MANIFEST.md.")

    embedder = SpeakerEmbedder()
    metrics = {
        "collar0.25 overlap-skipped": DiarizationErrorRate(collar=0.25, skip_overlap=True),
        "collar0.25 overlap-SCORED": DiarizationErrorRate(collar=0.25, skip_overlap=False),
        "collar0.0  overlap-skipped": DiarizationErrorRate(collar=0.0, skip_overlap=True),
        "collar0.0  overlap-SCORED": DiarizationErrorRate(collar=0.0, skip_overlap=False),
    }
    print(f"AMI {args.condition.upper()} test | primary config: WeSpeaker + 3s/1s + complete linkage"
          f" + supplied k\n")
    print(f"{'meeting':22s} {'min':>5s} {'k':>2s} {'DER(0.25,skip)':>14s} {'DER(0.25,ovl)':>13s}")
    print("-" * 62)
    n = 0
    seen = 0
    for shard in shards:
        t = pq.ParquetFile(shard).read()
        for i in range(t.num_rows):
            if seen < args.offset:
                seen += 1
                continue
            if args.limit and n >= args.limit:
                break
            row = {c: t.column(c)[i].as_py() for c in t.column_names}
            audio, st, en, spk = load_meeting(row)
            k = len(set(spk))
            mask = None
            if args.vad:
                import soundfile as sf
                args.scratch.mkdir(parents=True, exist_ok=True)
                wp = args.scratch / row["audio"]["path"]
                if not wp.exists():
                    sf.write(str(wp), audio, SR)
                mask = speech_mask(audio, wp, args.vad_threshold)
            times, labels = diarise_windows(audio, k, embedder, mask)
            hyp = to_annotation(times, labels)
            ref = ref_annotation(st, en, spk)
            for m in metrics.values():
                m(ref, hyp)
            d1 = DiarizationErrorRate(collar=0.25, skip_overlap=True)(ref, hyp)
            d2 = DiarizationErrorRate(collar=0.25, skip_overlap=False)(ref, hyp)
            print(f"{row['audio']['path'][:22]:22s} {len(audio)/SR/60:5.1f} {k:2d} "
                  f"{100*d1:13.1f}% {100*d2:12.1f}%")
            n += 1
        if args.limit and n >= args.limit:
            break

    print("-" * 62)
    print(f"\nAGGREGATE over {n} meetings ({args.condition.upper()}):\n")
    print(f"{'scoring policy':28s} {'DER':>7s} {'miss':>7s} {'FA':>7s} {'conf':>7s}")
    print("-" * 60)
    for name, m in metrics.items():
        r = abs(m)
        det = m[:]
        tot = det["total"] or 1
        print(f"{name:28s} {100*r:6.1f}% {100*det['missed detection']/tot:6.1f}% "
              f"{100*det['false alarm']/tot:6.1f}% {100*det['confusion']/tot:6.1f}%")
    print("-" * 60)
    print("\nmiss = reference speech we labelled as nobody (incl. overlap we cannot represent)")
    print("FA   = we labelled speech where the reference has none")
    print("conf = we labelled speech as the WRONG speaker")


if __name__ == "__main__":
    main()
