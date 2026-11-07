| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama4 17Bx16E (Scout) Q4_K - Medium |  60.86 GiB |   107.77 B | Vulkan     |  -1 |   pp512 @ d4096 |        158.68 ± 1.27 |
| llama4 17Bx16E (Scout) Q4_K - Medium |  60.86 GiB |   107.77 B | Vulkan     |  -1 |   tg128 @ d4096 |         17.58 ± 0.04 |

build: 067de93 (200)
