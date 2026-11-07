| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| minimax-m2 230B.A10B Q3_K - Medium |  94.93 GiB |   228.69 B | Vulkan     |  -1 |   pp512 @ d8192 |         99.96 ± 1.22 |
| minimax-m2 230B.A10B Q3_K - Medium |  94.93 GiB |   228.69 B | Vulkan     |  -1 |   tg128 @ d8192 |         22.76 ± 0.08 |

build: 067de93 (200)
