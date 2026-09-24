| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |           pp512 |      1321.83 ± 15.42 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |           tg128 |         75.22 ± 0.65 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   pp512 @ d2048 |      1141.74 ± 31.82 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   tg128 @ d2048 |         71.97 ± 0.64 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   pp512 @ d4096 |      1084.99 ± 35.46 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   tg128 @ d4096 |         71.24 ± 0.16 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   pp512 @ d8192 |       964.48 ± 28.26 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   tg128 @ d8192 |         67.51 ± 0.14 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |  pp512 @ d16384 |        727.08 ± 7.24 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |  tg128 @ d16384 |         63.57 ± 0.49 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |  pp512 @ d32768 |        457.86 ± 6.95 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |  tg128 @ d32768 |         56.08 ± 0.27 |

build: 067de93 (200)
