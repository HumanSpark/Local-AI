| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |           pp512 |        633.72 ± 1.39 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |           tg128 |         24.39 ± 0.04 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   pp512 @ d8192 |        282.30 ± 7.35 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   tg128 @ d8192 |         21.23 ± 0.01 |

build: 067de93 (200)
