| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |           pp512 |       223.16 ± 13.78 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |           tg128 |         11.09 ± 0.01 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d4096 |        169.02 ± 3.96 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d4096 |         10.53 ± 0.00 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d8192 |        133.65 ± 3.08 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d8192 |         10.03 ± 0.01 |

build: 067de93 (200)
