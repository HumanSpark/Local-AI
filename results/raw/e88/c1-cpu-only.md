| model                          |       size |     params | backend    | ngl | type_k | type_v |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | -----: | -----: | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |   0 |   q8_0 |   q8_0 |   1 |           pp512 |        344.38 ± 1.48 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |   0 |   q8_0 |   q8_0 |   1 |           tg128 |         33.39 ± 0.91 |

build: 067de93 (200)
