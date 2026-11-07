| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| nemotron_h_moe 120B.A12B Q5_K - Medium |  99.95 GiB |   120.67 B | Vulkan     |  -1 |           pp512 |        136.91 ± 1.62 |
| nemotron_h_moe 120B.A12B Q5_K - Medium |  99.95 GiB |   120.67 B | Vulkan     |  -1 |           tg128 |         16.01 ± 0.03 |

build: 067de93 (200)
