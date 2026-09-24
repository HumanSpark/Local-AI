| model                          |       size |     params | backend    | ngl | n_ubatch | type_k | type_v |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | -------: | -----: | -----: | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |      512 |   q8_0 |   q8_0 |   1 |           pp512 |       1033.13 ± 4.85 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |      512 |   q8_0 |   q8_0 |   1 |          pp4096 |        805.05 ± 0.22 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |     1024 |   q8_0 |   q8_0 |   1 |           pp512 |        960.85 ± 5.89 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |     1024 |   q8_0 |   q8_0 |   1 |          pp4096 |        933.09 ± 2.10 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |     2048 |   q8_0 |   q8_0 |   1 |           pp512 |        961.02 ± 8.66 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |     2048 |   q8_0 |   q8_0 |   1 |          pp4096 |        989.49 ± 0.64 |

build: 067de93 (200)
