| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama4 17Bx16E (Scout) Q4_K - Medium |  60.86 GiB |   107.77 B | Vulkan     |  -1 |   pp512 @ d4096 |        154.07 ± 1.03 |
| llama4 17Bx16E (Scout) Q4_K - Medium |  60.86 GiB |   107.77 B | Vulkan     |  -1 |   tg128 @ d4096 |         17.57 ± 0.03 |

build: 067de93 (200)
