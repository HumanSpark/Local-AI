| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |           pp512 |        611.88 ± 1.15 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |           tg128 |         24.40 ± 0.03 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |   pp512 @ d4096 |        469.74 ± 5.97 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |   tg128 @ d4096 |         22.36 ± 0.03 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |   pp512 @ d8192 |       372.66 ± 16.24 |
| llama 13B Q4_K - Medium        |   8.28 GiB |    14.66 B | Vulkan     |  -1 |   tg128 @ d8192 |         20.62 ± 0.02 |

build: 067de93 (200)
