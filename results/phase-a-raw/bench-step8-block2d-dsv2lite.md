| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |           pp512 |      1640.63 ± 13.15 |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |           tg128 |        110.80 ± 0.55 |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |   pp512 @ d8192 |      1181.76 ± 29.65 |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |   tg128 @ d8192 |         44.52 ± 0.21 |

build: 067de93 (200)
