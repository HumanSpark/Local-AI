# T8 vLLM-Omni route - BLOCKED on gfx1151 (W3, 2026-07-25)

**Outcome:** the shared vLLM-Omni route is recorded **route-blocked** on sparkmax (gfx1151 /
Radeon 8060S, RDNA3.5 APU, ROCm 7.2.4). This is the plan's accepted T8 done-when ("three result
sets, OR one clearly-evidenced route blockage"). One bounded investigation, not fought serially.

## The plan's premise was wrong (real-data-first at task time)

The WORKPLAN framed T8 as "one env cost for three": stand up vLLM-Omni once, run Qwen3-TTS 0.6B,
VoxCPM2, CosyVoice3 through it. Verified live at each repo (2026-07-25), the three engines do NOT
share a serving stack:

| Engine | Actual serving stack (from its own README) |
|---|---|
| Qwen3-TTS | vLLM-Omni ("day-0 support ... use vLLM-Omni for deployment") |
| VoxCPM2 | **Nano-vLLM** (`nanovllm-voxcpm`) - a different project |
| CosyVoice3 | **standard vLLM 0.11.x+ (V1 engine)** - a different path with strict version pins |

So there was never one shared vLLM-Omni env to amortise across three engines. All three are
vLLM-*family*, though, so they share the deeper blocker below.

## The blocker: no vLLM (any variant) runs on gfx1151 without a doomed source build

Layered evidence, all verified live 2026-07-25:

1. **No prebuilt vLLM ROCm image targets this GPU.** Every `docker.io/rocm/vllm` tag is
   **MI300 / Instinct** (CDNA datacenter, gfx942) on **ROCm 6.x**
   (e.g. `rocm6.2_mi300_...`, `rocm6.3.1_instinct_vllm0.8.3_...`). None is RDNA / gfx1151 / ROCm 7.x.
2. **ROCm 6.x is incompatible with gfx1151.** F5-TTS's own README (and the ROCm 6.2 vs 7.2
   compatibility matrices it links) states gfx1151/gfx1201 are **not in ROCm 6.x**; using ROCm 6.x
   on these GPUs throws `HIP error: invalid device function`. The prebuilt vLLM images are all
   ROCm 6.x, so they cannot run here.
3. **A vLLM source build would NOT produce gfx1151 kernels anyway.** vLLM's own
   `docker/Dockerfile.rocm_base` lists gfx1151 in `PYTORCH_ROCM_ARCH` (so torch builds) but then
   builds vLLM's custom kernels with `GPU_ARCHS=$(... sed 's/;gfx1[0-9]{3}//g')` - i.e. it
   **strips every gfx1xxx arch** from the kernel build. AITER (AMD's optimised kernels) is
   `gfx942;gfx950` only. So vLLM's paged-attention / custom kernels have no gfx1151 build; a
   from-source attempt is a multi-hour "heroic port" the timebox rule explicitly says to avoid
   ("R&D breadth beats one heroic port").

## Disposition for the T10 gate (per the plan's route-dependency rule)

These three are NOT dead - they are blocked **on the vLLM route specifically**, and each has a
documented **native (non-vLLM) PyTorch alternate route** that the T10 gate may admit to Stage 2:

| Engine | Licence (T1) | Documented alternate route (native, no vLLM) |
|---|---|---|
| Qwen3-TTS 0.6B/1.7B | Apache-2.0 (PASS) | the `qwen-tts` package's own PyTorch loader |
| VoxCPM2 | Apache-2.0 (PASS) | plain PyTorch inference / `llama.cpp-omni` on-device path |
| CosyVoice3/2 | Apache-2.0 (PASS) | CosyVoice's own FastAPI server + PyTorch inference |

Fish (s2-pro) and F5-TTS already PROVED the "container FROM the cached `rocm/pytorch:rocm7.2.3`
base + native PyTorch inference" path works on gfx1151. So the alternate routes are credible, not
speculative - they are per-engine standups (Stage-2 shaped), which is why they belong at the T10
gate, not inside T8's shared-route timebox.

**Recommendation to carry into T9/T10:** admit CosyVoice3 and Qwen3-TTS to Stage 2 via their
native PyTorch routes (both Apache-2.0, both could WIN, unlike research-only F5). VoxCPM2 likewise
if its native path is as clean. The vLLM *throughput* path is only relevant once/if an engine is
selected and needs production serving - not for the benchmark.
