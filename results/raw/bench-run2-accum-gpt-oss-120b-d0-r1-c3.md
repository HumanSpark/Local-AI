| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| gpt-oss 120B MXFP4 MoE         |  59.02 GiB |   116.83 B | Vulkan     |  -1 |           pp512 |        478.99 ± 5.32 |
| gpt-oss 120B MXFP4 MoE         |  59.02 GiB |   116.83 B | Vulkan     |  -1 |           tg128 |         53.39 ± 0.09 |

build: 067de93 (200)
