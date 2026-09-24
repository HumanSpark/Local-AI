| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | Vulkan     |  -1 |           pp512 |        225.98 ± 7.51 |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | Vulkan     |  -1 |           tg128 |         24.71 ± 0.02 |

build: 067de93 (200)
