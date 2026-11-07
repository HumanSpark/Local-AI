| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |           pp512 |        922.24 ± 2.73 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |           tg128 |         70.93 ± 0.52 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d2048 |       613.14 ± 16.24 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d2048 |         62.75 ± 0.43 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d4096 |       484.49 ± 14.40 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d4096 |         57.12 ± 0.41 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   pp512 @ d8192 |        315.59 ± 2.57 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |   tg128 @ d8192 |         50.50 ± 0.27 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |  pp512 @ d16384 |        197.01 ± 1.56 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |  tg128 @ d16384 |         39.21 ± 0.33 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |  pp512 @ d32768 |        113.85 ± 4.18 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | Vulkan     |  -1 |  tg128 @ d32768 |         27.91 ± 0.09 |

build: 067de93 (200)
