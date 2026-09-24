# File: tools/spk_embed.py
# Purpose: Speaker-embedding extractor (WeSpeaker ResNet34-LM ONNX) + cosine similarity helper.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: The identity-bearing component of the diarisation stack. Loads 16 kHz mono audio,
# computes Kaldi-compatible 80-bin fbank features (25ms window / 10ms shift, matching the model's
# training config exactly - see /opt/models/staging/wespeaker/config.yaml), applies WeSpeaker's
# mean normalisation, and runs the ONNX ResNet34 to produce a 256-dim speaker embedding.
# CPU-only via onnxruntime: no torch, no torchaudio, no ROCm - deliberately, so this cannot
# perturb var/ft-venv (F37's proven stack). Embedding a meeting's worth of windows is trivial
# compute; the GPU is not needed and is left free for llama-server.
#
# The feature pipeline is the risk surface: a mismatch against the training config yields
# embeddings that are silently wrong rather than obviously broken. tools/spk_embed_validate.py
# is the positive control that must pass before any diarisation result is believed.

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

MODEL_PATH = Path("/opt/models/staging/wespeaker/voxceleb_resnet34_LM.onnx")
SAMPLE_RATE = 16000


class SpeakerEmbedder:
    """WeSpeaker ResNet34-LM speaker embeddings from 16 kHz mono float audio."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"WeSpeaker ONNX model not found at {model_path}. "
                f"hint: fetch per manifests/MANIFEST.md "
                f"(Wespeaker/wespeaker-voxceleb-resnet34-LM, rev f0c48c29, "
                f"26,530,309 B, sha256 7bb2f06e...) and verify size+sha BEFORE use."
            )
        try:
            import onnxruntime as ort
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "onnxruntime is required. hint: use var/diar-venv/bin/python, "
                "not the system python or var/ft-venv."
            ) from exc

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        self._sess = ort.InferenceSession(
            str(model_path), sess_options=opts, providers=["CPUExecutionProvider"]
        )

    def _fbank(self, audio: np.ndarray) -> np.ndarray:
        """80-bin Kaldi fbank matching the model's training config exactly."""
        import kaldi_native_fbank as knf

        opts = knf.FbankOptions()
        opts.frame_opts.samp_freq = float(SAMPLE_RATE)
        opts.frame_opts.frame_length_ms = 25.0
        opts.frame_opts.frame_shift_ms = 10.0
        # dither=1.0 in the training config is a TRAINING augmentation; inference uses 0 so the
        # extractor is deterministic (a random dither would make embeddings irreproducible).
        opts.frame_opts.dither = 0.0
        opts.frame_opts.snip_edges = False
        opts.mel_opts.num_bins = 80
        fbank = knf.OnlineFbank(opts)
        # WeSpeaker feeds int16-scaled samples to Kaldi's fbank.
        fbank.accept_waveform(float(SAMPLE_RATE), (audio * 32768.0).tolist())
        fbank.input_finished()
        frames = [fbank.get_frame(i) for i in range(fbank.num_frames_ready)]
        if not frames:
            raise ValueError(
                "Audio too short to produce any fbank frame. "
                "hint: need at least ~25ms of audio; check the segment bounds."
            )
        feats = np.stack(frames).astype(np.float32)
        # WeSpeaker applies mean normalisation (CMN) over the utterance, no variance norm.
        return feats - feats.mean(axis=0, keepdims=True)

    def embed(self, audio: np.ndarray) -> np.ndarray:
        """Return an L2-normalised 256-dim embedding for one audio chunk."""
        if audio.ndim != 1:
            raise ValueError(
                f"expected mono 1-D audio, got shape {audio.shape}. "
                "hint: average channels or select one before calling."
            )
        feats = self._fbank(audio)[None, :, :]
        embs = self._sess.run(["embs"], {"feats": feats})[0][0]
        norm = np.linalg.norm(embs)
        if norm == 0:
            raise ValueError(
                "Zero-norm embedding - the model produced no signal. "
                "hint: the chunk is probably digital silence; screen segments by energy first."
            )
        return (embs / norm).astype(np.float32)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity of two L2-normalised embeddings."""
    return float(np.dot(a, b))


def load_wav(path: Path) -> np.ndarray:
    """Load a wav as 16 kHz mono float32, raising if the rate is wrong."""
    import soundfile as sf

    try:
        audio, sr = sf.read(str(path), dtype="float32", always_2d=False)
    except Exception as exc:
        raise OSError(
            f"could not read audio at {path}: {exc}. "
            "hint: expects a readable 16 kHz mono WAV (ffmpeg -ar 16000 -ac 1)."
        ) from exc
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != SAMPLE_RATE:
        raise ValueError(
            f"{path} is {sr} Hz, need {SAMPLE_RATE} Hz. "
            f"hint: ffmpeg -i {path} -ar 16000 -ac 1 out.wav"
        )
    return audio


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract a WeSpeaker speaker embedding from a 16 kHz mono WAV.",
        epilog="example: var/diar-venv/bin/python tools/spk_embed.py audio.wav",
    )
    parser.add_argument("wav", type=Path, help="16 kHz mono WAV file")
    args = parser.parse_args()

    emb = SpeakerEmbedder().embed(load_wav(args.wav))
    print(f"embedding dim={emb.shape[0]} norm={np.linalg.norm(emb):.4f}")
    print(f"first 8: {np.array2string(emb[:8], precision=4)}")


if __name__ == "__main__":
    main()
