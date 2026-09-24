| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |           pp512 |       1042.41 ± 8.77 |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |           tg128 |         43.38 ± 0.14 |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |   pp512 @ d4096 |        671.93 ± 7.66 |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |   tg128 @ d4096 |         38.62 ± 0.01 |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |   pp512 @ d8192 |        482.89 ± 8.92 |
| qwen3 8B Q4_K - Medium         |   4.68 GiB |     8.19 B | Vulkan     |  -1 |   tg128 @ d8192 |         34.95 ± 0.02 |

build: 067de93 (200)
