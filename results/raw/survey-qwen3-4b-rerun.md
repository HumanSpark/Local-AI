| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |           pp512 |      1940.34 ± 16.71 |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |           tg128 |         77.42 ± 0.29 |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |   pp512 @ d4096 |       996.49 ± 19.01 |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |   tg128 @ d4096 |         63.15 ± 0.13 |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |   pp512 @ d8192 |       636.69 ± 13.30 |
| qwen3 4B Q4_K - Medium         |   2.32 GiB |     4.02 B | Vulkan     |  -1 |   tg128 @ d8192 |         53.63 ± 0.10 |

build: 067de93 (200)
