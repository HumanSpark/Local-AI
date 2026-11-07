| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama ?B Q5_K - Medium         |  82.18 GiB |   125.03 B | Vulkan     |  -1 |   pp512 @ d4096 |         29.03 ± 0.11 |
| llama ?B Q5_K - Medium         |  82.18 GiB |   125.03 B | Vulkan     |  -1 |   tg128 @ d4096 |          2.45 ± 0.00 |

build: 067de93 (200)
