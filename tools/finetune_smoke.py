#!/usr/bin/env python3
# File: finetune_smoke.py
# Purpose: DEFINITIVE proof that gfx1151 (Ryzen AI Max+ 395) can TRAIN, not just infer -
#          the check that settles whether F35/Q6's "no ROCm training stack" wall is real.
#          Runs the full training loop (forward -> loss -> backward -> optimizer step) with
#          a PEFT LoRA adapter on the GPU, using a TINY model built from config (no download,
#          no memory-edge risk). If loss goes down over a few steps, on-box training works.
# Project: sparkbench | Date: 2026-07-13
# Usage: var/ft-venv/bin/python tools/finetune_smoke.py   (run with the ROCm-torch venv)

from __future__ import annotations

import os

# The two env flags the Strix Halo fine-tuning guide requires, set BEFORE importing torch.
os.environ.setdefault("TORCH_ROCM_AOTRITON_ENABLE_EXPERIMENTAL", "1")
os.environ.setdefault("HSA_ENABLE_SDMA", "0")  # also sidesteps the F24 SDMA-suballocator path

import torch  # noqa: E402


def main() -> None:
    print(f"torch {torch.__version__} | hip {getattr(torch.version, 'hip', None)}")
    avail = torch.cuda.is_available()
    print(f"GPU available: {avail}")
    if not avail:
        print("RESULT: GPU NOT available - the wall stands (or env/setup issue). Investigate.")
        return
    dev = torch.device("cuda")
    print(f"device 0: {torch.cuda.get_device_name(0)}")

    # 1) raw GPU op
    a = torch.randn(512, 512, device=dev)
    b = torch.randn(512, 512, device=dev)
    _ = (a @ b).sum().item()
    print("matmul on GPU: OK")

    # 2) full LoRA training loop on a tiny model built from config (no download)
    from transformers import LlamaConfig, LlamaForCausalLM
    from peft import LoraConfig, get_peft_model

    cfg = LlamaConfig(vocab_size=512, hidden_size=128, intermediate_size=256,
                      num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=4,
                      max_position_embeddings=128)
    model = LlamaForCausalLM(cfg)
    lora = LoraConfig(r=8, lora_alpha=16, target_modules=["q_proj", "v_proj"],
                      task_type="CAUSAL_LM")
    model = get_peft_model(model, lora).to(dev)
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"LoRA model on GPU: {trainable:,} trainable params")

    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-3)
    torch.manual_seed(0)
    x = torch.randint(0, 512, (4, 32), device=dev)  # fixed batch -> loss must fall
    losses = []
    for step in range(8):
        out = model(input_ids=x, labels=x)
        out.loss.backward()
        opt.step(); opt.zero_grad()
        losses.append(out.loss.item())
        print(f"  step {step}: loss {out.loss.item():.4f}")

    fell = losses[-1] < losses[0]
    print(f"\nloss {losses[0]:.4f} -> {losses[-1]:.4f}  ({'DOWN' if fell else 'not down'})")
    print("RESULT: on-box LoRA training WORKS on gfx1151." if fell else
          "RESULT: ran but loss did not fall - inspect (autograd/optimizer issue).")


if __name__ == "__main__":
    main()
