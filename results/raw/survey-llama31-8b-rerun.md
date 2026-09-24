| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |           pp512 |       1057.32 ± 6.45 |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |           tg128 |         44.04 ± 0.03 |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |   pp512 @ d4096 |       701.06 ± 11.09 |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |   tg128 @ d4096 |         39.63 ± 0.02 |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |   pp512 @ d8192 |       525.60 ± 10.51 |
| llama 8B Q4_K - Medium         |   4.58 GiB |     8.03 B | Vulkan     |  -1 |   tg128 @ d8192 |         36.37 ± 0.15 |

build: 067de93 (200)
