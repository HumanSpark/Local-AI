| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3moe 235B.A22B Q3_K - Medium |  96.59 GiB |   235.09 B | Vulkan     |  -1 |           pp512 |        116.64 ± 1.82 |
| qwen3moe 235B.A22B Q3_K - Medium |  96.59 GiB |   235.09 B | Vulkan     |  -1 |           tg128 |         16.94 ± 0.07 |

build: 067de93 (200)
