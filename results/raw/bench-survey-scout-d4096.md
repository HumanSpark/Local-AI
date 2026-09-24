| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama4 17Bx16E (Scout) Q4_K - Medium |  60.86 GiB |   107.77 B | Vulkan     |  -1 |   pp512 @ d4096 |        146.03 ± 2.81 |
| llama4 17Bx16E (Scout) Q4_K - Medium |  60.86 GiB |   107.77 B | Vulkan     |  -1 |   tg128 @ d4096 |         16.64 ± 0.19 |

build: 067de93 (200)
