| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |           pp512 |       214.02 ± 13.03 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |           tg128 |         11.09 ± 0.00 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d4096 |        163.21 ± 2.98 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d4096 |         10.54 ± 0.00 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   pp512 @ d8192 |        128.08 ± 3.38 |
| qwen2 32B Q4_K - Medium        |  18.48 GiB |    32.76 B | Vulkan     |  -1 |   tg128 @ d8192 |         10.04 ± 0.00 |

build: 067de93 (200)
