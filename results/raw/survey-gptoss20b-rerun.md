| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |           pp512 |      1308.99 ± 15.11 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |           tg128 |         77.10 ± 0.85 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   pp512 @ d4096 |      1061.91 ± 40.38 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   tg128 @ d4096 |         72.80 ± 0.08 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   pp512 @ d8192 |       954.84 ± 30.59 |
| gpt-oss 20B MXFP4 MoE          |  11.27 GiB |    20.91 B | Vulkan     |  -1 |   tg128 @ d8192 |         70.06 ± 0.07 |

build: 067de93 (200)
