| model                          |       size |     params | backend    | ngl | type_k | type_v |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | -----: | -----: | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |           pp512 |      1089.75 ± 11.40 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |           tg128 |         88.66 ± 0.64 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |   pp512 @ d2048 |       803.62 ± 19.14 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |   tg128 @ d2048 |         79.64 ± 0.40 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |   pp512 @ d4096 |       679.00 ± 21.48 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |   tg128 @ d4096 |         75.34 ± 0.13 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |   pp512 @ d8192 |        491.20 ± 5.36 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |   tg128 @ d8192 |         67.98 ± 0.29 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |  pp512 @ d16384 |        312.33 ± 5.76 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |  tg128 @ d16384 |         57.61 ± 0.38 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |  pp512 @ d32768 |        192.21 ± 2.75 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |  tg128 @ d32768 |         43.75 ± 0.47 |

build: 067de93 (200)
