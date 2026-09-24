# File: tools/vad.py
# Purpose: A REAL voice-activity detector (Silero ONNX) for the speaker pass.
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E43 measured our diarisation against AMI (real human ground truth) and found DER is
# dominated by FALSE ALARM - 20.2% of a 29.2% DER on close-talk, i.e. ~69% of all error. Confusion
# was only 8.7%, so the speaker model was never the problem: the SPEECH DETECTOR was.
#
# What we had was not a VAD. It was `RMS > 1e-3` - a volume threshold. On real meeting audio,
# breathing, paper, keyboards and room tone all clear it and get assigned a speaker. It was never
# visible before because every Otter-based number SKIPPED regions with no reference speaker, so
# false alarm was structurally unmeasurable (see E43 / F45).
#
# Two rejected alternatives, recorded so they are not retried:
#   - whisper's segments as a speech mask: they cover 97-98.5% of a recording (vs 65-83% actual
#     speech) because segments span the pauses BETWEEN words by design. Using them made FA worse
#     (40.7% -> 59.5%). Whisper segments are transcription units, not speech regions.
#   - whisper.cpp's --vad: fine for the TEXT pass (it is what stops the "Thank you" fabrication,
#     E41/F44) but it only gates whisper's own decoding; it does not hand us speech regions.
#
# This runs Silero VAD directly under onnxruntime on CPU: no torch, no ROCm, ~2MB model, and it
# keeps the GPU free for llama-server. Silero is a streaming model - 512-sample frames at 16 kHz
# with a carried LSTM state - so frames MUST be fed in order and the state threaded through.

from __future__ import annotations

from pathlib import Path

import numpy as np

MODEL_PATH = Path("/opt/models/staging/silero-vad/silero-vad.onnx")
SAMPLE_RATE = 16000
FRAME = 512               # Silero's fixed frame size at 16 kHz - not a tunable
DEFAULT_THRESHOLD = 0.5   # Silero's own documented default; not fitted by us


class SileroVAD:
    """Speech regions from 16 kHz mono audio, via Silero VAD in ONNX."""

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Silero VAD ONNX not found at {model_path}. "
                "hint: fetch per manifests/MANIFEST.md (onnx-community/silero-vad, rev e71cae96, "
                "2,243,022 B, sha256 a4a068cd...) and verify size+sha BEFORE use."
            )
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise ImportError(
                "onnxruntime required. hint: use var/diar-venv/bin/python, not var/ft-venv."
            ) from exc
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 4
        self._sess = ort.InferenceSession(
            str(model_path), sess_options=opts, providers=["CPUExecutionProvider"]
        )

    def probabilities(self, audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Speech probability per 512-sample frame. Returns (frame centre times, probs)."""
        if audio.ndim != 1:
            raise ValueError(f"expected mono 1-D audio, got {audio.shape}. hint: average channels.")
        state = np.zeros((2, 1, 128), dtype=np.float32)
        sr = np.array(SAMPLE_RATE, dtype=np.int64)
        probs, times = [], []
        n = (len(audio) // FRAME) * FRAME
        for i in range(0, n, FRAME):
            chunk = audio[i : i + FRAME].astype(np.float32)[None, :]
            out, state = self._sess.run(
                ["output", "stateN"], {"input": chunk, "state": state, "sr": sr}
            )
            probs.append(float(out[0][0]))
            times.append((i + FRAME / 2) / SAMPLE_RATE)
        if not probs:
            raise ValueError(
                f"audio shorter than one {FRAME}-sample frame. hint: need at least 32ms."
            )
        return np.array(times), np.array(probs)

    def speech_regions(
        self,
        audio: np.ndarray,
        threshold: float = DEFAULT_THRESHOLD,
        min_speech_s: float = 0.25,
        min_silence_s: float = 0.10,
        pad_s: float = 0.03,
    ) -> list[tuple[float, float]]:
        """Merge frame probabilities into (start, end) speech regions.

        Defaults mirror whisper.cpp's own VAD settings (min speech 250ms, min silence 100ms,
        pad 30ms) so the two passes agree about what speech is, rather than each inventing its own.
        """
        times, probs = self.probabilities(audio)
        speech = probs >= threshold
        regions: list[list[float]] = []
        start = None
        for t, s in zip(times, speech):
            if s and start is None:
                start = t
            elif not s and start is not None:
                regions.append([start, t])
                start = None
        if start is not None:
            regions.append([start, times[-1]])

        # bridge short silences, then drop short blips - order matters: bridging first lets a
        # real utterance broken by a breath survive the min_speech filter as one region.
        merged: list[list[float]] = []
        for r in regions:
            if merged and r[0] - merged[-1][1] < min_silence_s:
                merged[-1][1] = r[1]
            else:
                merged.append(r)
        out = [(max(0.0, a - pad_s), b + pad_s) for a, b in merged if (b - a) >= min_speech_s]
        return out


def speech_fraction(regions: list[tuple[float, float]], duration: float) -> float:
    """Fraction of the recording marked as speech - the sanity check for a VAD."""
    if duration <= 0:
        raise ValueError(f"duration must be positive, got {duration}. hint: check the audio loaded.")
    return sum(b - a for a, b in regions) / duration
