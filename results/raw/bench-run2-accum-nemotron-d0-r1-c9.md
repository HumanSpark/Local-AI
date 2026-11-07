| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| nemotron_h_moe 120B.A12B Q5_K - Medium |  99.95 GiB |   120.67 B | Vulkan     |  -1 |           pp512 |        139.52 ± 1.80 |
| nemotron_h_moe 120B.A12B Q5_K - Medium |  99.95 GiB |   120.67 B | Vulkan     |  -1 |           tg128 |         15.96 ± 0.02 |

build: 067de93 (200)
