| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |           pp512 |        939.52 ± 1.46 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |           tg128 |         71.32 ± 0.76 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d4096 |       493.85 ± 17.84 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d4096 |         58.67 ± 0.20 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d8192 |        321.49 ± 2.25 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d8192 |         50.87 ± 0.32 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |  pp512 @ d16384 |        198.35 ± 1.68 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |  tg128 @ d16384 |         39.40 ± 0.14 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |  pp512 @ d32768 |        113.87 ± 4.11 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |  tg128 @ d32768 |         27.84 ± 0.07 |

build: 067de93 (200)
