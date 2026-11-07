| model                          |       size |     params | backend    | ngl | type_k | type_v |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | -----: | -----: | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q4_1 |   q4_1 |   1 |           pp512 |       1075.66 ± 5.27 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q4_1 |   q4_1 |   1 |           tg128 |         90.12 ± 0.93 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q4_1 |   q4_1 |   1 |  pp512 @ d16384 |        309.67 ± 2.48 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q4_1 |   q4_1 |   1 |  tg128 @ d16384 |         59.86 ± 0.27 |

build: 067de93 (200)
