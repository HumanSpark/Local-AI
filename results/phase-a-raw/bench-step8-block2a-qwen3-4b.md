| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |           pp512 |       2051.57 ± 8.40 |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |           tg128 |         78.38 ± 0.64 |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |   pp512 @ d8192 |       665.94 ± 12.71 |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |   tg128 @ d8192 |         54.12 ± 0.22 |

build: 067de93 (200)
