| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |           pp512 |        283.00 ± 4.80 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |           tg128 |         12.64 ± 0.00 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |   pp512 @ d4096 |       235.96 ± 10.95 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |   tg128 @ d4096 |         12.38 ± 0.00 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |   pp512 @ d8192 |        222.49 ± 9.95 |
| qwen35 27B Q4_K - Medium       |  15.65 GiB |    27.32 B | Vulkan     |  -1 |   tg128 @ d8192 |         12.19 ± 0.00 |

build: 9e40df63b (770)
