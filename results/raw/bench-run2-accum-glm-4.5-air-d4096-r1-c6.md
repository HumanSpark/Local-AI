| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | Vulkan     |  -1 |   pp512 @ d4096 |         95.94 ± 3.03 |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | Vulkan     |  -1 |   tg128 @ d4096 |         22.58 ± 0.09 |

build: 067de93 (200)
