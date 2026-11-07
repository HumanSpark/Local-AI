| model                          |       size |     params | backend    | ngl | type_k | type_v |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | -----: | -----: | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |   pp512 @ d8192 |        486.34 ± 2.29 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |   q8_0 |   q8_0 |   1 |   tg128 @ d8192 |         68.87 ± 0.10 |

build: 067de93 (200)
