| model                          |       size |     params | backend    | ngl | type_k | type_v |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | -----: | -----: | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |           pp512 |       1075.17 ± 7.57 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |           tg128 |         89.89 ± 0.86 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |  pp512 @ d16384 |        309.86 ± 3.54 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |  tg128 @ d16384 |         58.95 ± 0.08 |

build: 067de93 (200)
