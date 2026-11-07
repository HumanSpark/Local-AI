| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |           pp512 |       333.97 ± 15.35 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |           tg128 |         15.07 ± 0.01 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |   pp512 @ d4096 |       248.21 ± 11.92 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |   tg128 @ d4096 |         14.42 ± 0.01 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |   pp512 @ d8192 |        237.98 ± 8.39 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |   tg128 @ d8192 |         13.81 ± 0.01 |

build: 067de93 (200)
