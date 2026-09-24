ggml_vulkan: Found 1 Vulkan devices:
ggml_vulkan: 0 = AMD Radeon Graphics (RADV GFX1151) (radv) | uma: 1 | fp16: 1 | bf16: 0 | fp4: 0 | warp size: 64 | shared memory: 65536 | int dot: 0 | matrix cores: KHR_coopmat
| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen35moe 35B.A3B Q4_K - Medium |  19.91 GiB |    34.66 B | Vulkan     |  -1 |           pp512 |        984.04 ± 9.13 |
| qwen35moe 35B.A3B Q4_K - Medium |  19.91 GiB |    34.66 B | Vulkan     |  -1 |           tg128 |         70.00 ± 0.04 |
| qwen35moe 35B.A3B Q4_K - Medium |  19.91 GiB |    34.66 B | Vulkan     |  -1 |   pp512 @ d4096 |        836.91 ± 4.40 |
| qwen35moe 35B.A3B Q4_K - Medium |  19.91 GiB |    34.66 B | Vulkan     |  -1 |   tg128 @ d4096 |         66.23 ± 0.41 |
| qwen35moe 35B.A3B Q4_K - Medium |  19.91 GiB |    34.66 B | Vulkan     |  -1 |   pp512 @ d8192 |        793.63 ± 5.03 |
| qwen35moe 35B.A3B Q4_K - Medium |  19.91 GiB |    34.66 B | Vulkan     |  -1 |   tg128 @ d8192 |         64.45 ± 0.17 |

build: daef7b687 (1047)
