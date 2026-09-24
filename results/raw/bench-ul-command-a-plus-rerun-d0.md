| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| cohere2moe ?B Q3_K - Medium    |  95.52 GiB |   218.25 B | Vulkan     |  -1 |           pp512 |         97.13 ± 0.80 |
| cohere2moe ?B Q3_K - Medium    |  95.52 GiB |   218.25 B | Vulkan     |  -1 |           tg128 |         13.52 ± 0.02 |

build: 067de93 (200)
