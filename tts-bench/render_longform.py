#!/usr/bin/env python3
# File: tts-bench/render_longform.py
# Purpose: Render minutes-long narration with Chatterbox at a NAMED config, by sentence-chunking so no
#          single generate() call approaches the model's token ceiling.
# Project: sparkbench | Date: 2026-07-26
#
# Overview: The W3 narrator was settled on 2026-07-26 - VCTK p239 (SW England, female) cloned by
# Chatterbox - by a six-take reference/clone reel. The owner accepted both Chatterbox clones and neither
# VoxCPM2 clone, and his prior voice ranking broke the p233/p239 tie. This script produces the sustained
# sample that a 10-second take cannot answer for: does the voice hold across paragraphs.
#
# WHY CHUNKING IS MANDATORY, not a nicety: ChatterboxTTS.generate() hardcodes max_new_tokens=1000, and
# an over-long text does not raise - it runs to the ceiling and emits non-speech. That is F50 exactly
# (Fish s2-pro returned HTTP 200 and a well-formed 47s WAV that was a -48 dB noise floor). So the text
# is split on sentence boundaries into chunks well inside the ceiling, and every chunk's realised
# duration is reported so a chunk that hit the ceiling is visible as an outlier rather than silently
# averaged into the whole.
#
# WHY prepare_conditionals() IS CALLED ONCE: passing audio_prompt_path to generate() re-derives the
# speaker embedding on every call. Deriving it once and reusing the tensor means every chunk is
# conditioned identically, so any timbre wobble between chunks is sampling variance and not a
# re-computed embedding. It is also materially faster.
#
# Pace is NOT tuned here. Chatterbox exposes no speed parameter (verified against its own signature:
# text, repetition_penalty, min_p, top_p, audio_prompt_path, exaggeration, cfg_weight, temperature).
# Pace is emergent from how many speech tokens T3 emits, and with temperature=0.8 it is stochastic -
# so a pace difference is not a difference until the fixed-settings run-to-run spread is known. This
# script therefore renders at the config the owner actually accepted and reports the pace it realises.
#
# Data flow: text file -> sentence chunks -> per-chunk Chatterbox render (seeded per chunk index for
# reproducibility) -> concatenate with a short inter-sentence pause -> single WAV + a metrics JSON.
# Loudness normalisation, MP3 encoding and the intelligibility gate are deliberately NOT done here:
# they run outside the GPU container, so the expensive step is not repeated when a cheap one changes.
from __future__ import annotations

import argparse
import io
import json
import sys
import time
import wave
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

# Bypass Perth watermarking: it re-encodes the waveform, and an unwatermarked render is the honest
# artefact to measure. Same shim as the spike renders the owner judged, so this config matches those.
import perth


class _NoWatermark:
    def apply_watermark(self, wav, sample_rate=None, **kw):  # noqa: ARG002 - signature must match
        return wav


perth.PerthImplicitWatermarker = _NoWatermark

from chatterbox.tts import ChatterboxTTS  # noqa: E402 - must follow the watermark shim

# Chatterbox's own ceiling. Chunks are sized to stay well inside it; see the header.
MAX_NEW_TOKENS = 1000

# split_chunks MOVED to chunk_reuse.py on 2026-07-29 and re-exported here, so `from render_longform
# import split_chunks` keeps working and there is exactly one implementation. It moved because the
# splice path needs the same chunking on the HOST, and this module cannot be imported there - numpy,
# soundfile, torch, perth and chatterbox above are all container-only. Keeping the chunker beside them
# would have forced every test that touches it into f5-tts:rocm, including the null-splice
# byte-identity gate, which is worth far more running in the normal suite with no GPU.
from chunk_reuse import CHUNK_CHARS, reuse_plan, splice, split_chunks  # noqa: E402,F401 - facade


# Every config axis that must match before two renders may be spliced together. exaggeration,
# cfg_weight, temperature and seed change how the voice is produced; a mismatch joins two different
# voices mid-file. gap_ms is here too because it changes every join in the file, which is not a
# compatibility question the other four cover.
SPLICE_CRITICAL = ("exaggeration", "cfg_weight", "temperature", "seed", "gap_ms")


def load_reuse_sidecar(reuse_from: Path, args: argparse.Namespace) -> dict:
    """Load the sidecar beside `reuse_from` and REFUSE if its config is not spliceable with this run.

    The refusal is the point. Splicing chunks rendered at a different exaggeration, guidance,
    temperature or seed - or cloned from a different reference clip - joins two different voices in
    one file, and it does so without any error: the output is a well-formed WAV that simply changes
    voice partway through. That is F50's failure shape (a plausible artefact that no automated screen
    catches), so it is refused loudly at the top rather than discovered by ear later.
    """
    if not reuse_from.is_file():
        raise FileNotFoundError(
            f"--reuse-from names no such file: {reuse_from}. "
            f"hint: pass the PRE-LOUDNORM render from var/posts/audio/, not the delivered MP3, and "
            f"remember paths resolve inside the container where the repo is mounted at /app."
        )
    side_path = reuse_from.with_name(reuse_from.name + ".json")
    if not side_path.is_file():
        raise FileNotFoundError(
            f"no sidecar beside {reuse_from}: expected {side_path}. "
            f"hint: splicing needs the per-chunk texts and durations the renderer recorded; without "
            f"them neither the reuse plan nor the chunk boundaries can be computed. Re-render the "
            f"post in full to regenerate it."
        )

    sidecar = json.loads(side_path.read_text(encoding="utf-8"))
    old_cfg = sidecar["config"]
    for key in SPLICE_CRITICAL:
        current = getattr(args, key)
        if old_cfg[key] != current:
            raise ValueError(
                f"{reuse_from.name} was rendered with {key}={old_cfg[key]}, but this run uses "
                f"{key}={current}. "
                f"hint: splicing across configs joins two different voices mid-file. Either re-run "
                f"with {key}={old_cfg[key]} to match the existing audio, or re-render the post in "
                f"full at the new setting and do not reuse."
            )
    if sidecar["reference"] != str(args.ref):
        raise ValueError(
            f"{reuse_from.name} was cloned from reference {sidecar['reference']}, but this run uses "
            f"{args.ref}. "
            f"hint: the reference clip IS the voice - splicing across two of them changes speaker "
            f"mid-file. Pass --ref {sidecar['reference']} to match, or re-render in full."
        )
    return sidecar


def pcm_frames(audio, sample_rate: int) -> bytes:
    """Convert a rendered float waveform to raw PCM_16 frames exactly as a normal render would.

    Deliberately routed through soundfile rather than a hand-rolled float->int16 cast: the spliced
    file must be indistinguishable from one this script wrote end to end, and libsndfile's scaling and
    clipping behaviour is the thing that has to match. Doing the arithmetic ourselves would be a
    second implementation that could drift by a least-significant bit.
    """
    buf = io.BytesIO()
    sf.write(buf, audio, sample_rate, format="WAV", subtype="PCM_16")
    buf.seek(0)
    with wave.open(buf, "rb") as w:
        return w.readframes(w.getnframes())


def render_reusing(args: argparse.Namespace, chunks: list[str], sidecar: dict) -> int:
    """Render only the chunks whose text changed, and splice them into the existing audio."""
    old_rows = sidecar["per_chunk"]
    plan = reuse_plan([r["text"] for r in old_rows], chunks)
    sample_rate = sidecar["sample_rate"]
    to_render = [j for j, p in enumerate(plan) if p is None]
    reused_n = len(plan) - len(to_render)
    print(f"reuse plan: {reused_n}/{len(plan)} chunks reused from {args.reuse_from.name}, "
          f"{len(to_render)} to render", flush=True)

    t_start = time.time()
    rendered: dict[int, bytes] = {}
    new_rows: dict[int, dict[str, object]] = {}
    # LAZY, and load-bearing: a 100%-reuse splice must never touch the GPU. Any load on this box can
    # hit the amdgpu suballocator deadlock (docs/memory-edge-deadlock.md), so not loading is not an
    # optimisation - it is the difference between seconds and an attended run.
    if to_render:
        model = load_model(args.ckpt, args.ref, args.exaggeration)
        if model.sr != sample_rate:
            raise ValueError(
                f"the model renders at {model.sr} Hz but {args.reuse_from.name} is {sample_rate} Hz. "
                f"hint: splicing audio at two sample rates changes pitch and speed at the join; "
                f"re-render the post in full at {model.sr} Hz."
            )
        for j in to_render:
            # seed + j on the NEW index, exactly as a full render of this text would seed chunk j.
            audio, rows = render_chunks(model, [chunks[j]], exaggeration=args.exaggeration,
                                        cfg_weight=args.cfg_weight, temperature=args.temperature,
                                        seed=args.seed + j, gap_ms=args.gap_ms, progress=False)
            rendered[j] = pcm_frames(audio, sample_rate)
            new_rows[j] = rows[0]

    args.out.parent.mkdir(parents=True, exist_ok=True)
    splice(old_wav=args.reuse_from, plan=plan, rendered=rendered, gap_ms=args.gap_ms,
           sample_rate=sample_rate, out=args.out)

    rows_out: list[dict[str, object]] = []
    for j, old_index in enumerate(plan):
        row = dict(old_rows[old_index]) if old_index is not None else dict(new_rows[j])
        row["chunk"] = j + 1
        row["reused"] = old_index is not None
        rows_out.append(row)

    with wave.open(str(args.out), "rb") as w:
        total_s = w.getnframes() / sample_rate
    wall = time.time() - t_start
    total_words = sum(len(c.split()) for c in chunks)
    metrics = {
        "engine": "chatterbox", "reference": str(args.ref), "script": str(args.text),
        "reused_from": str(args.reuse_from),
        "config": {"exaggeration": args.exaggeration, "cfg_weight": args.cfg_weight,
                   "temperature": args.temperature, "seed": args.seed, "gap_ms": args.gap_ms,
                   "chunk_chars": CHUNK_CHARS, "max_new_tokens": MAX_NEW_TOKENS},
        "sample_rate": sample_rate, "chunks": len(chunks), "total_words": total_words,
        "audio_s": round(total_s, 2), "wall_s": round(wall, 1),
        "words_per_sec": round(total_words / total_s, 2), "rtf": round(wall / total_s, 3),
        "chunks_reused": reused_n, "chunks_rendered": len(to_render),
        "per_chunk": rows_out,
    }
    Path(str(args.out) + ".json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False),
                                             encoding="utf-8")
    print(f"\nwrote {args.out} - {total_s:.1f}s, {reused_n} chunks reused, "
          f"{len(to_render)} re-rendered in {wall:.1f}s wall")
    return 0


def load_model(ckpt: str, ref: Path, exaggeration: float):
    """Load Chatterbox and derive the speaker embedding ONCE, for reuse across every chunk and post."""
    model = ChatterboxTTS.from_local(ckpt, "cuda")
    model.prepare_conditionals(str(ref), exaggeration=exaggeration)
    return model


def render_chunks(model, chunks: list[str], *, exaggeration: float, cfg_weight: float,
                  temperature: float, seed: int, gap_ms: int,
                  progress: bool = True) -> tuple[np.ndarray, list[dict[str, object]]]:
    """Render each chunk with the model's already-prepared conditionals and concatenate.

    Shared by the single-script CLI below and render_batch.py, so the batch cannot drift from the
    config that was auditioned. Raises on any chunk failure rather than emitting a short render - a
    silently truncated post is the failure mode this whole pipeline is built to avoid.
    """
    gap = np.zeros(int(model.sr * gap_ms / 1000.0), dtype=np.float32)
    pieces: list[np.ndarray] = []
    rows: list[dict[str, object]] = []
    for i, chunk in enumerate(chunks):
        torch.manual_seed(seed + i)  # reproducible despite temperature sampling
        t0 = time.time()
        try:
            # No audio_prompt_path: reuse the conditionals prepared by load_model().
            wav = model.generate(chunk, exaggeration=exaggeration,
                                 cfg_weight=cfg_weight, temperature=temperature)
        except Exception as exc:
            raise RuntimeError(
                f"Chatterbox failed on chunk {i + 1}/{len(chunks)} ({len(chunk)} chars): "
                f"{type(exc).__name__}: {exc}. "
                f"hint: render the chunk alone to reproduce; if it is an OOM, lower CHUNK_CHARS rather "
                f"than retrying, because a shorter chunk is also further from the token ceiling."
            ) from exc
        audio = wav.squeeze(0).cpu().float().numpy()
        gen_s, dur_s = time.time() - t0, len(audio) / model.sr
        words = len(chunk.split())
        rows.append({"chunk": i + 1, "chars": len(chunk), "words": words,
                     "gen_s": round(gen_s, 2), "audio_s": round(dur_s, 2),
                     "words_per_sec": round(words / dur_s, 2), "rtf": round(gen_s / dur_s, 3),
                     "text": chunk})
        if progress:
            print(f"  chunk {i + 1:2d}/{len(chunks)}  {len(chunk):3d}ch {words:3d}w  "
                  f"gen={gen_s:5.1f}s audio={dur_s:5.2f}s  {words / dur_s:.2f} w/s", flush=True)
        pieces.append(audio)
        if i < len(chunks) - 1:
            pieces.append(gap)
    return np.concatenate(pieces), rows


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Render long-form narration with Chatterbox, sentence-chunked to stay inside its "
                    "hardcoded token ceiling.",
        epilog="example (inside the chatterbox container):\n"
               "  ./render_longform.py --text tts-bench/corpus/narrator-longform.txt \\\n"
               "      --ref stage2-sweep/out/refvoice/_parts_p239/p239_008.flac \\\n"
               "      --out stage2-sweep/out/refvoice/narrator_longform_p239.wav\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--text", type=Path, required=True, help="UTF-8 script; blank-line-separated paragraphs")
    ap.add_argument("--ref", type=Path, required=True, help="reference clip to clone (the voice)")
    ap.add_argument("--out", type=Path, required=True, help="destination WAV (metrics written alongside as .json)")
    ap.add_argument("--ckpt", default="/app/chatterbox-rocm/checkpoints/chatterbox-std",
                    help="local Chatterbox checkpoint dir (default: %(default)s)")
    ap.add_argument("--exaggeration", type=float, default=0.5, help="default: %(default)s (the accepted config)")
    ap.add_argument("--cfg-weight", type=float, default=0.5, help="default: %(default)s (the accepted config)")
    ap.add_argument("--temperature", type=float, default=0.8, help="default: %(default)s (library default)")
    ap.add_argument("--gap-ms", type=int, default=180, help="silence inserted between chunks (default: %(default)s)")
    ap.add_argument("--seed", type=int, default=20260726, help="base seed; chunk i uses seed+i (default: %(default)s)")
    ap.add_argument("--reuse-from", type=Path, default=None,
                    help="existing PRE-LOUDNORM render of this post; chunks whose text is unchanged "
                         "are spliced from it instead of re-rendered. Refuses if its config differs.")
    args = ap.parse_args()

    for path, what in ((args.text, "script text"), (args.ref, "reference clip")):
        if not path.is_file():
            raise FileNotFoundError(
                f"{what} not found: {path}. "
                f"hint: paths are resolved inside the container, where the repo is mounted at /app - "
                f"pass container paths, not host paths."
            )

    text = args.text.read_text(encoding="utf-8")
    chunks = split_chunks(text)
    total_words = len(text.split())
    print(f"script: {total_words} words in {len(chunks)} chunks (target <={CHUNK_CHARS} chars each)", flush=True)

    if args.reuse_from is not None:
        # Config compatibility is checked BEFORE anything is rendered or written, so an incompatible
        # reuse costs nothing and cannot leave a half-spliced file behind.
        sidecar = load_reuse_sidecar(args.reuse_from, args)
        return render_reusing(args, chunks, sidecar)

    model = load_model(args.ckpt, args.ref, args.exaggeration)
    print(f"conditioned on {args.ref.name} | exaggeration={args.exaggeration} "
          f"cfg_weight={args.cfg_weight} temperature={args.temperature}", flush=True)

    t_start = time.time()
    full, rows = render_chunks(model, chunks, exaggeration=args.exaggeration,
                               cfg_weight=args.cfg_weight, temperature=args.temperature,
                               seed=args.seed, gap_ms=args.gap_ms)
    total_s = len(full) / model.sr
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.out), full, model.sr)

    wall = time.time() - t_start
    metrics = {
        "engine": "chatterbox", "reference": str(args.ref), "script": str(args.text),
        "config": {"exaggeration": args.exaggeration, "cfg_weight": args.cfg_weight,
                   "temperature": args.temperature, "seed": args.seed, "gap_ms": args.gap_ms,
                   "chunk_chars": CHUNK_CHARS, "max_new_tokens": MAX_NEW_TOKENS},
        "sample_rate": model.sr, "chunks": len(chunks), "total_words": total_words,
        "audio_s": round(total_s, 2), "wall_s": round(wall, 1),
        "words_per_sec": round(total_words / total_s, 2), "rtf": round(wall / total_s, 3),
        "per_chunk": rows,
    }
    Path(str(args.out) + ".json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")

    paces = [float(r["words_per_sec"]) for r in rows]
    print(f"\nwrote {args.out} - {total_s:.1f}s, {total_words} words, "
          f"{total_words / total_s:.2f} w/s overall, RTF {wall / total_s:.3f}x")
    print(f"per-chunk pace spread: {min(paces):.2f}-{max(paces):.2f} w/s  "
          f"(a chunk far BELOW the rest is the token-ceiling tell - check it before shipping)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
