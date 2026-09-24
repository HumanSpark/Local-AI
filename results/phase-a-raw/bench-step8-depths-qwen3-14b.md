| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |           pp512 |        621.66 ± 2.10 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |           tg128 |         24.34 ± 0.03 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   pp512 @ d2048 |       453.03 ± 20.53 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   tg128 @ d2048 |         23.39 ± 0.02 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   pp512 @ d4096 |        386.27 ± 4.66 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   tg128 @ d4096 |         22.65 ± 0.03 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   pp512 @ d8192 |        271.79 ± 7.42 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |   tg128 @ d8192 |         21.19 ± 0.02 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |  pp512 @ d16384 |        156.47 ± 3.01 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |  tg128 @ d16384 |         18.85 ± 0.02 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |  pp512 @ d32768 |         39.54 ± 4.22 |
| qwen3 14B Q4_K - Medium        |   8.38 GiB |    14.77 B | Vulkan     |  -1 |  tg128 @ d32768 |         15.47 ± 0.02 |

build: 067de93 (200)
