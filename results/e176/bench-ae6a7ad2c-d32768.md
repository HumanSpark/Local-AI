| model                          |       size |     params | backend    | ngl |  fa |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --: | --------------: | -------------------: |
| bailingmoe3 124B.A5.1B Q3_K - Medium |  57.27 GiB |   127.49 B | Vulkan     | 999 |   1 |  pp512 @ d32768 |        205.42 ± 0.44 |
| bailingmoe3 124B.A5.1B Q3_K - Medium |  57.27 GiB |   127.49 B | Vulkan     | 999 |   1 |  tg128 @ d32768 |         30.33 ± 0.07 |

build: ae6a7ad2c (3023)
