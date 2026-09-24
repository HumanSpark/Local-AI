| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3moe 235B.A22B Q3_K - Medium |  96.59 GiB |   235.09 B | Vulkan     |  -1 |   pp512 @ d8192 |         80.12 ± 0.44 |
| qwen3moe 235B.A22B Q3_K - Medium |  96.59 GiB |   235.09 B | Vulkan     |  -1 |   tg128 @ d8192 |         15.11 ± 0.05 |

build: 067de93 (200)
