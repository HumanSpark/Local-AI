| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| minimax-m2 230B.A10B Q3_K - Medium |  94.93 GiB |   228.69 B | Vulkan     |  -1 |   pp512 @ d4096 |        134.57 ± 1.84 |
| minimax-m2 230B.A10B Q3_K - Medium |  94.93 GiB |   228.69 B | Vulkan     |  -1 |   tg128 @ d4096 |         25.20 ± 0.08 |

build: 067de93 (200)
