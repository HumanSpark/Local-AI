| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| cohere2moe ?B Q3_K - Medium    |  95.52 GiB |   218.25 B | Vulkan     |  -1 |   pp512 @ d8192 |         54.06 ± 0.65 |
| cohere2moe ?B Q3_K - Medium    |  95.52 GiB |   218.25 B | Vulkan     |  -1 |   tg128 @ d8192 |         13.20 ± 0.04 |

build: 067de93 (200)
