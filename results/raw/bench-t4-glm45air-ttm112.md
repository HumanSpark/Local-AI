| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | Vulkan     |  -1 |           pp512 |        230.59 ± 8.41 |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | Vulkan     |  -1 |           tg128 |         24.24 ± 0.12 |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | Vulkan     |  -1 |   pp512 @ d8192 |         41.28 ± 1.60 |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | Vulkan     |  -1 |   tg128 @ d8192 |         21.06 ± 0.09 |

build: 067de93 (200)
