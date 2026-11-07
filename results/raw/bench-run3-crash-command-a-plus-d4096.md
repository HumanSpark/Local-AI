| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| cohere2moe ?B Q3_K - Medium    |  95.52 GiB |   218.25 B | Vulkan     |  -1 |   pp512 @ d4096 |         66.97 ± 2.47 |
| cohere2moe ?B Q3_K - Medium    |  95.52 GiB |   218.25 B | Vulkan     |  -1 |   tg128 @ d4096 |         13.34 ± 0.01 |

build: 067de93 (200)
