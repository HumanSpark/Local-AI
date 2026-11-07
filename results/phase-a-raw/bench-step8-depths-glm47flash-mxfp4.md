| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |           pp512 |        968.27 ± 4.06 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |           tg128 |         63.44 ± 0.23 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d2048 |        628.99 ± 2.23 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d2048 |         56.44 ± 0.31 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d4096 |        479.14 ± 2.39 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d4096 |         52.72 ± 0.08 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d8192 |        321.82 ± 2.81 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d8192 |         45.43 ± 0.24 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |  pp512 @ d16384 |        199.57 ± 1.66 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |  tg128 @ d16384 |         36.47 ± 0.16 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |  pp512 @ d32768 |        113.48 ± 0.78 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |  tg128 @ d32768 |         26.29 ± 0.09 |

build: 067de93 (200)
