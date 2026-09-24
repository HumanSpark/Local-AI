| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B IQ2_XXS - 2.0625 bpw |   9.63 GiB |    30.53 B | Vulkan     |  -1 |           pp512 |      1099.27 ± 12.57 |
| qwen3moe 30B.A3B IQ2_XXS - 2.0625 bpw |   9.63 GiB |    30.53 B | Vulkan     |  -1 |           tg128 |        105.35 ± 0.22 |

build: 067de93 (200)
