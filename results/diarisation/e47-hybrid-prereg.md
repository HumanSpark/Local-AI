# PRE-REGISTRATION: pyannote-VAD + our embeddings - can we close the false-alarm gap at our speed? (2026-07-17)

# File: results/diarisation/e47-hybrid-prereg.md
# Purpose: Predictions BEFORE running the hybrid (pyannote segmentation-3.0 as VAD, our clustering).
# Project: sparkbench | Date: 2026-07-17
#
# Overview: E46 showed pyannote beats our stack on IHM (6.5% vs 20.3%), and online calls - Alastair's
# actual use case - map to IHM (close mics mixed to one stream, like AMI Mix-Headset). The gap is
# false alarm (~7 pts, our Silero VAD) + close-talk confusion (~7 pts, our clustering). This tests
# whether swapping ONLY the VAD - pyannote/segmentation-3.0 in place of Silero, keeping our fast
# WeSpeaker embeddings + complete-linkage clustering - closes the false-alarm half while keeping
# most of our speed. Speed matters: ours ~60x real time GPU-free vs pyannote ~real time on CPU.

Why: online calls are the deployment, they map to IHM (pyannote's biggest lead), and speed is a
stated priority - so the winning config is "pyannote accuracy at our speed" IF the VAD swap delivers.
Trigger: Alastair, 2026-07-17 - "most are going to be online calls, but the speed is a major bonus".

## Setup

Same 6 held-out AMI IHM meetings, same pyannote.metrics DER, same collar/overlap policies, same
supplied k. Only change from our stack: speech regions come from pyannote/segmentation-3.0 instead
of Silero VAD. Everything downstream (3s/1s windows, WeSpeaker ONNX embeddings, complete-linkage AHC)
is unchanged.

## Reference points (from E46, same 6 IHM meetings, collar 0.25 overlap-skipped)

| system | DER | miss | FA | conf |
|---|---|---|---|---|
| ours (Silero VAD) | 20.3% | 1.1% | 10.6% | 8.6% |
| pyannote 3.1 (full) | 6.5% | 2.3% | 3.2% | 1.1% |

## Predictions (registered BEFORE the run)

| ID | Prediction | Rationale |
|---|---|---|
| **H1** | Hybrid FALSE ALARM drops to <= 5% (from our 10.6%, toward pyannote's 3.2%) | The VAD is the direct cause of false alarm; swapping in the better one should transfer most of the improvement. |
| **H2** | Hybrid CONFUSION stays near ours (7-9%), NOT near pyannote's 1.1% | We keep OUR embeddings+clustering. Confusion is a clustering property, not a VAD one, so it should barely move. If it drops a lot, cleaner speech regions also helped clustering (a bonus). |
| **H3** | Hybrid DER lands 11-15% - between ours (20.3%) and pyannote (6.5%), closer to the middle | H1 removes ~5-7 FA points; H2 leaves confusion roughly put. 20.3 - ~6 = ~14. |
| **H4** | Hybrid is SLOWER than ours but still >> pyannote-full speed | segmentation-3.0 is one torch model on CPU vs our Silero; but we skip pyannote's embedding+clustering. Expect maybe 5-15x real time vs our ~60x and pyannote's ~1x. |

## Disposition

- **H3 true (11-15%)** -> the VAD swap is worth adopting: most of pyannote's accuracy advantage on
  online-call audio, at a fraction of its compute, keeping our ONNX/no-torch embedding path.
- **Confusion is then the ONLY remaining gap** -> the decision becomes "is 11-15% good enough, or do
  we also need pyannote's clustering?" - a clean, well-scoped question.
- **H1 false (FA barely moves)** -> segmentation-3.0's advantage does not transfer through our
  windowing, and the honest conclusion is "adopt pyannote wholesale or stay as we are".

## Limit

segmentation-3.0 used as a binary VAD (speech / non-speech), collapsing its overlap-aware output.
That forfeits its overlap handling - a deliberate scope cut to isolate the false-alarm question. The
torch dependency it reintroduces is the cost to weigh against the accuracy gain.
