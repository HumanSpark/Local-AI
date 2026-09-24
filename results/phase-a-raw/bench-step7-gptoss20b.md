| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |           pp512 |      1366.71 ± 12.31 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |           tg128 |         77.76 ± 0.81 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   pp512 @ d8192 |      1005.33 ± 41.22 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   tg128 @ d8192 |         70.65 ± 0.58 |

build: 067de93 (200)
