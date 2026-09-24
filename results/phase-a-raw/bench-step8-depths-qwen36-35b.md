| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |           pp512 |        982.86 ± 6.80 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |           tg128 |         58.71 ± 0.23 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   pp512 @ d2048 |       870.38 ± 14.50 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   tg128 @ d2048 |         57.08 ± 0.28 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   pp512 @ d4096 |        844.46 ± 8.03 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   tg128 @ d4096 |         56.53 ± 0.30 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   pp512 @ d8192 |        799.36 ± 1.33 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   tg128 @ d8192 |         55.14 ± 0.24 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |  pp512 @ d16384 |       702.46 ± 12.65 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |  tg128 @ d16384 |         52.47 ± 0.28 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |  pp512 @ d32768 |       587.42 ± 12.98 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |  tg128 @ d32768 |         47.87 ± 0.26 |

build: 067de93 (200)
