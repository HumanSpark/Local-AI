| model                          |       size |     params | backend    | ngl |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --: | --------------: | -------------------: |
| bailingmoe3 124B.A5.1B Q3_K - Medium |  57.27 GiB |   127.49 B | Vulkan     | 999 |   1 |   pp512 @ d8192 |        354.32 ± 5.63 |
| bailingmoe3 124B.A5.1B Q3_K - Medium |  57.27 GiB |   127.49 B | Vulkan     | 999 |   1 |   tg128 @ d8192 |         34.71 ± 0.15 |

build: 94f3af3d0 (2979)
