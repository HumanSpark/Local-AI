| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama ?B Q5_K - Medium         |  82.18 GiB |   125.03 B | Vulkan     |  -1 |   pp512 @ d8192 |         15.06 ± 0.50 |
| llama ?B Q5_K - Medium         |  82.18 GiB |   125.03 B | Vulkan     |  -1 |   tg128 @ d8192 |          2.40 ± 0.00 |

build: 067de93 (200)
