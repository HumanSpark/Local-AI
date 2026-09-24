| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |           pp512 |      1977.58 ± 40.58 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |           tg128 |         78.26 ± 0.17 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |   pp512 @ d4096 |      1274.54 ± 25.31 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |   tg128 @ d4096 |         65.12 ± 0.06 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |   pp512 @ d8192 |       891.35 ± 14.54 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |   tg128 @ d8192 |         56.17 ± 0.08 |

build: 067de93 (200)
