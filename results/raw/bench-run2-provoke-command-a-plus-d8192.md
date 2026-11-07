| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| cohere2moe ?B Q3_K - Medium    |  95.52 GiB |   218.25 B | Vulkan     |  -1 |   pp512 @ d8192 |         53.89 ± 0.51 |
| cohere2moe ?B Q3_K - Medium    |  95.52 GiB |   218.25 B | Vulkan     |  -1 |   tg128 @ d8192 |         13.32 ± 0.01 |

build: 067de93 (200)
