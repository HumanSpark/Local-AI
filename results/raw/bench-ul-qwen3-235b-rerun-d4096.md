| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3moe 235B.A22B Q3_K - Medium |  96.59 GiB |   235.09 B | Vulkan     |  -1 |   pp512 @ d4096 |         99.29 ± 0.86 |
| qwen3moe 235B.A22B Q3_K - Medium |  96.59 GiB |   235.09 B | Vulkan     |  -1 |   tg128 @ d4096 |         15.91 ± 0.02 |

build: 067de93 (200)
