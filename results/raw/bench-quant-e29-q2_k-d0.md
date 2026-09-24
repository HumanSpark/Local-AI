| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q2_K - Medium |  10.48 GiB |    30.53 B | Vulkan     |  -1 |           pp512 |      1091.25 ± 12.98 |
| qwen3moe 30B.A3B Q2_K - Medium |  10.48 GiB |    30.53 B | Vulkan     |  -1 |           tg128 |        105.68 ± 0.20 |

build: 067de93 (200)
