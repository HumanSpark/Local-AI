| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |           pp512 |       298.07 ± 21.35 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |           tg128 |         15.12 ± 0.00 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |   pp512 @ d4096 |        248.28 ± 1.50 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |   tg128 @ d4096 |         14.46 ± 0.00 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |   pp512 @ d8192 |        219.67 ± 3.83 |
| llama 13B Q4_K - Medium        |  13.34 GiB |    23.57 B | Vulkan     |  -1 |   tg128 @ d8192 |         13.86 ± 0.00 |

build: 067de93 (200)
