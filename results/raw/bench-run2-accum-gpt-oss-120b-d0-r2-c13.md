| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| gpt-oss 120B MXFP4 MoE         |  59.02 GiB |   116.83 B | Vulkan     |  -1 |           pp512 |        486.00 ± 5.44 |
| gpt-oss 120B MXFP4 MoE         |  59.02 GiB |   116.83 B | Vulkan     |  -1 |           tg128 |         53.32 ± 0.27 |

build: 067de93 (200)
