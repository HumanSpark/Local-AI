| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |           pp512 |        985.57 ± 2.46 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |           tg128 |         62.94 ± 0.16 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d8192 |        327.42 ± 2.89 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d8192 |         46.22 ± 0.28 |

build: 067de93 (200)
