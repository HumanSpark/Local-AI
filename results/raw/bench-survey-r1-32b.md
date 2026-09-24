| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |           pp512 |       223.96 ± 14.31 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |           tg128 |         11.05 ± 0.00 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d4096 |        171.02 ± 3.45 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d4096 |         10.50 ± 0.00 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d8192 |        133.84 ± 3.94 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d8192 |         10.00 ± 0.01 |

build: 067de93 (200)
