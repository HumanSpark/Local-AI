| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |           pp512 |       1078.08 ± 1.70 |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |           tg128 |         43.56 ± 0.24 |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |   pp512 @ d8192 |       499.97 ± 10.38 |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |   tg128 @ d8192 |         35.23 ± 0.15 |

build: 067de93 (200)
