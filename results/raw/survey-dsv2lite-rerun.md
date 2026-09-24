| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |           pp512 |      1606.82 ± 23.37 |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |           tg128 |        111.92 ± 1.78 |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |   pp512 @ d4096 |      1301.37 ± 40.99 |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |   tg128 @ d4096 |         64.40 ± 0.08 |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |   pp512 @ d8192 |      1141.63 ± 33.46 |
| deepseek2 16B Q4_K - Medium    |   9.65 GiB |    15.71 B | Vulkan     |  -1 |   tg128 @ d8192 |         45.31 ± 0.04 |

build: 067de93 (200)
