| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |           pp512 |      2149.96 ± 14.29 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |           tg128 |         77.44 ± 0.65 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |   pp512 @ d4096 |      1339.56 ± 21.64 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |   tg128 @ d4096 |         63.13 ± 0.41 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |   pp512 @ d8192 |       917.48 ± 16.95 |
| phi3 3B Q4_K - Medium          |   2.31 GiB |     3.84 B | Vulkan     |  -1 |   tg128 @ d8192 |         54.87 ± 0.37 |

build: 067de93 (200)
