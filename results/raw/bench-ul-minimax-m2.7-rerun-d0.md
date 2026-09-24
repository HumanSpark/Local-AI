| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| minimax-m2 230B.A10B Q3_K - Medium |  94.93 GiB |   228.69 B | Vulkan     |  -1 |           pp512 |        170.02 ± 5.59 |
| minimax-m2 230B.A10B Q3_K - Medium |  94.93 GiB |   228.69 B | Vulkan     |  -1 |           tg128 |         28.88 ± 0.04 |

build: 067de93 (200)
