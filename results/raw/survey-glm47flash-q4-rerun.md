| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |           pp512 |        914.75 ± 1.51 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |           tg128 |         71.40 ± 0.93 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d4096 |       474.99 ± 11.63 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d4096 |         58.77 ± 0.11 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d8192 |        310.51 ± 2.18 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d8192 |         51.43 ± 0.08 |

build: 067de93 (200)
