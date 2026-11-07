| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |           pp512 |        621.61 ± 2.29 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |           tg128 |         24.61 ± 0.01 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   pp512 @ d4096 |        387.22 ± 4.04 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   tg128 @ d4096 |         22.90 ± 0.01 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   pp512 @ d8192 |        269.38 ± 4.90 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   tg128 @ d8192 |         21.42 ± 0.00 |

build: 067de93 (200)
