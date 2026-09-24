| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3moe 235B.A22B Q3_K - Medium |  96.59 GiB |   235.09 B | Vulkan     |  -1 |   pp512 @ d8192 |         79.79 ± 0.26 |
| qwen3moe 235B.A22B Q3_K - Medium |  96.59 GiB |   235.09 B | Vulkan     |  -1 |   tg128 @ d8192 |         15.10 ± 0.02 |

build: 067de93 (200)
