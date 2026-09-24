| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| nemotron_h_moe 120B.A12B Q5_K - Medium |  99.95 GiB |   120.67 B | Vulkan     |  -1 |   pp512 @ d8192 |        136.39 ± 0.83 |
| nemotron_h_moe 120B.A12B Q5_K - Medium |  99.95 GiB |   120.67 B | Vulkan     |  -1 |   tg128 @ d8192 |         16.06 ± 0.02 |

build: 067de93 (200)
