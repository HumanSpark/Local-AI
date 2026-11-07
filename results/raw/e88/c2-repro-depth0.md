| model                          |       size |     params | backend    | ngl | type_k | type_v |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | -----: | -----: | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |           pp512 |       1075.72 ± 2.64 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |           tg128 |         90.90 ± 0.05 |

build: 067de93 (200)
