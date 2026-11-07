| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |           pp512 |       247.93 ± 13.39 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |           tg128 |         12.59 ± 0.00 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |   pp512 @ d4096 |        231.11 ± 2.66 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |   tg128 @ d4096 |         11.93 ± 0.00 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |   pp512 @ d8192 |        219.36 ± 2.44 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |   tg128 @ d8192 |         11.67 ± 0.00 |

build: 067de93 (200)
