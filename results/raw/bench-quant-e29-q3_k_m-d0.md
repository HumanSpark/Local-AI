| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q3_K - Medium |  13.70 GiB |    30.53 B | Vulkan     |  -1 |           pp512 |       1030.96 ± 8.35 |
| qwen3moe 30B.A3B Q3_K - Medium |  13.70 GiB |    30.53 B | Vulkan     |  -1 |           tg128 |        101.45 ± 0.18 |

build: 067de93 (200)
