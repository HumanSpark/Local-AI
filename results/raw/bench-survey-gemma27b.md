| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |           pp512 |       248.43 ± 13.14 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |           tg128 |         12.56 ± 0.00 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |   pp512 @ d4096 |        224.17 ± 2.68 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |   tg128 @ d4096 |         11.91 ± 0.01 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |   pp512 @ d8192 |        219.77 ± 3.17 |
| gemma3 27B Q4_K - Medium       |  15.40 GiB |    27.01 B | Vulkan     |  -1 |   tg128 @ d8192 |         11.65 ± 0.00 |

build: 067de93 (200)
