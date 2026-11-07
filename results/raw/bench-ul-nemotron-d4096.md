| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| nemotron_h_moe 120B.A12B Q5_K - Medium |  99.95 GiB |   120.67 B | Vulkan     |  -1 |   pp512 @ d4096 |        136.33 ± 0.44 |
| nemotron_h_moe 120B.A12B Q5_K - Medium |  99.95 GiB |   120.67 B | Vulkan     |  -1 |   tg128 @ d4096 |         16.12 ± 0.04 |

build: 067de93 (200)
