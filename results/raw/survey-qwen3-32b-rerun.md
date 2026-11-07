| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |           pp512 |       216.97 ± 13.10 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |           tg128 |         10.98 ± 0.00 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d4096 |        130.96 ± 1.81 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d4096 |         10.42 ± 0.00 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d8192 |         63.04 ± 1.93 |
| qwen3 32B Q4_K - Medium        |  18.40 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d8192 |          9.92 ± 0.00 |

build: 067de93 (200)
