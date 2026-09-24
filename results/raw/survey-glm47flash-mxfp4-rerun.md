| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |           pp512 |        966.53 ± 1.39 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |           tg128 |         64.08 ± 0.35 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d4096 |        474.75 ± 1.87 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d4096 |         53.52 ± 0.10 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d8192 |        318.38 ± 2.45 |
| deepseek2 30B.A3B MXFP4 MoE    |  15.79 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d8192 |         46.50 ± 0.05 |

build: 067de93 (200)
