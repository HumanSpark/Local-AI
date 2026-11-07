| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |           pp512 |      1107.62 ± 10.71 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | Vulkan     |  -1 |           tg128 |         92.30 ± 0.32 |

build: 067de93 (200)
