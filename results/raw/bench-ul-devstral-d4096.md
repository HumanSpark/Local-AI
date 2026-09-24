ggml_vulkan: Found 1 Vulkan devices:
ggml_vulkan: 0 = AMD Radeon Graphics (RADV GFX1151) (radv) | uma: 1 | fp16: 1 | bf16: 0 | warp size: 64 | shared memory: 65536 | int dot: 0 | matrix cores: KHR_coopmat
| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama ?B Q5_K - Medium         |  82.18 GiB |   125.03 B | Vulkan     |  -1 |   pp512 @ d4096 |         26.24 ± 0.08 |
| llama ?B Q5_K - Medium         |  82.18 GiB |   125.03 B | Vulkan     |  -1 |   tg128 @ d4096 |          2.45 ± 0.00 |

build: 067de93 (200)
