| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |           pp512 |        943.49 ± 1.24 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |           tg128 |         71.93 ± 0.69 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d8192 |       340.01 ± 16.91 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d8192 |         50.74 ± 0.29 |

build: 067de93 (200)
