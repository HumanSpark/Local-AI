| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |           pp512 |       1089.93 ± 2.11 |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |           tg128 |         44.21 ± 0.21 |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |   pp512 @ d8192 |       538.54 ± 10.40 |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |   tg128 @ d8192 |         35.96 ± 0.29 |

build: 067de93 (200)
