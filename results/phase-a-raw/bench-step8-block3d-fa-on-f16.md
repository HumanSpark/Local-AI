| model                          |       size |     params | backend    | ngl |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |           pp512 |       1124.64 ± 9.74 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |           tg128 |         92.12 ± 0.41 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |   pp512 @ d2048 |       894.86 ± 31.51 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |   tg128 @ d2048 |         81.60 ± 0.32 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |   pp512 @ d4096 |        734.15 ± 6.88 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |   tg128 @ d4096 |         75.78 ± 0.73 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |   pp512 @ d8192 |        555.65 ± 9.45 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |   tg128 @ d8192 |         66.66 ± 0.34 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |  pp512 @ d16384 |        343.86 ± 3.98 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |  tg128 @ d16384 |         53.09 ± 0.39 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |  pp512 @ d32768 |        181.64 ± 3.75 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   1 |  tg128 @ d32768 |         38.15 ± 0.15 |

build: 067de93 (200)
