| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |           pp512 |        996.40 ± 5.90 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |           tg128 |         59.30 ± 0.36 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   pp512 @ d8192 |       803.78 ± 12.62 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |   tg128 @ d8192 |         55.29 ± 0.42 |

build: 067de93 (200)
