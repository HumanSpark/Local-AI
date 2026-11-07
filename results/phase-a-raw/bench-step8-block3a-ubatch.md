| model                          |       size |     params | backend    | ngl | n_ubatch |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | -------: | --------------: | -------------------: |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |      128 |           pp512 |       555.86 ± 11.41 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |      256 |           pp512 |        700.39 ± 9.18 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |      512 |           pp512 |       899.00 ± 11.39 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |     1024 |           pp512 |        896.11 ± 8.25 |
| qwen35moe 35B.A3B Q4_K - Medium |  20.81 GiB |    34.66 B | Vulkan     |  -1 |     2048 |           pp512 |        893.21 ± 6.30 |

build: 067de93 (200)
