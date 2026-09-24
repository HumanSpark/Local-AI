| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| minimax-m2 230B.A10B Q3_K - Medium |  94.93 GiB |   228.69 B | Vulkan     |  -1 |   pp512 @ d8192 |        102.57 ± 1.75 |
| minimax-m2 230B.A10B Q3_K - Medium |  94.93 GiB |   228.69 B | Vulkan     |  -1 |   tg128 @ d8192 |         22.67 ± 0.07 |

build: 067de93 (200)
