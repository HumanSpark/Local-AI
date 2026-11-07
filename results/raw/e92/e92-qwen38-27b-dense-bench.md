ggml_vulkan: Found 1 Vulkan devices:
ggml_vulkan: 0 = AMD Radeon Graphics (RADV GFX1151) (radv) | uma: 1 | fp16: 1 | bf16: 0 | fp4: 0 | warp size: 64 | shared memory: 65536 | int dot: 0 | matrix cores: KHR_coopmat
| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |           pp512 |       294.57 ± 13.63 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |           tg128 |         12.59 ± 0.00 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |   pp512 @ d4096 |       235.48 ± 10.49 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |   tg128 @ d4096 |         12.32 ± 0.00 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |   pp512 @ d8192 |       221.19 ± 10.00 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |   tg128 @ d8192 |         12.12 ± 0.00 |

build: daef7b687 (1047)
