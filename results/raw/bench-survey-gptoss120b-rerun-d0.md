| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| gpt-oss 120B MXFP4 MoE         |  59.02 GiB |   116.83 B | Vulkan     |  -1 |           pp512 |        479.00 ± 1.69 |
| gpt-oss 120B MXFP4 MoE         |  59.02 GiB |   116.83 B | Vulkan     |  -1 |           tg128 |         53.79 ± 0.06 |

build: 067de93 (200)
