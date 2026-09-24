| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |           pp512 |       598.49 ± 23.81 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |           tg128 |         24.45 ± 0.00 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |   pp512 @ d4096 |        467.99 ± 6.79 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |   tg128 @ d4096 |         22.46 ± 0.00 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |   pp512 @ d8192 |       390.47 ± 15.75 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |   tg128 @ d8192 |         20.72 ± 0.00 |

build: 067de93 (200)
