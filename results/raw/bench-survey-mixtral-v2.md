| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama 8x7B Q4_K - Medium       |  26.49 GiB |    46.70 B | Vulkan     |  -1 |           pp512 |        216.13 ± 6.30 |
| llama 8x7B Q4_K - Medium       |  26.49 GiB |    46.70 B | Vulkan     |  -1 |           tg128 |         26.45 ± 0.05 |
| llama 8x7B Q4_K - Medium       |  26.49 GiB |    46.70 B | Vulkan     |  -1 |   pp512 @ d4096 |        196.44 ± 0.90 |
| llama 8x7B Q4_K - Medium       |  26.49 GiB |    46.70 B | Vulkan     |  -1 |   tg128 @ d4096 |         24.60 ± 0.13 |
| llama 8x7B Q4_K - Medium       |  26.49 GiB |    46.70 B | Vulkan     |  -1 |   pp512 @ d8192 |        178.96 ± 2.50 |
| llama 8x7B Q4_K - Medium       |  26.49 GiB |    46.70 B | Vulkan     |  -1 |   tg128 @ d8192 |         23.46 ± 0.08 |

build: 067de93 (200)
