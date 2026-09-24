| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| llama4 17Bx16E (Scout) Q4_K - Medium |  60.86 GiB |   107.77 B | Vulkan     |  -1 |   pp512 @ d8192 |        165.48 ± 1.88 |
| llama4 17Bx16E (Scout) Q4_K - Medium |  60.86 GiB |   107.77 B | Vulkan     |  -1 |   tg128 @ d8192 |         18.19 ± 0.01 |

build: 067de93 (200)
