| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |           pp512 |        972.60 ± 7.29 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |           tg128 |         60.05 ± 0.41 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   pp512 @ d4096 |        821.82 ± 7.53 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   tg128 @ d4096 |         57.63 ± 0.18 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   pp512 @ d8192 |        771.37 ± 5.15 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   tg128 @ d8192 |         56.06 ± 0.13 |

build: 067de93 (200)
