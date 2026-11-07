| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |           pp512 |        198.20 ± 9.57 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |           tg128 |         10.89 ± 0.00 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d4096 |        124.69 ± 1.51 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d4096 |         10.30 ± 0.00 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d8192 |         86.00 ± 0.47 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d8192 |          9.76 ± 0.02 |

build: 067de93 (200)
