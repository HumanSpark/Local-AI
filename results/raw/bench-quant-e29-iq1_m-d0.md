| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen3moe 30B.A3B IQ1_M - 1.75 bpw |   9.01 GiB |    30.53 B | Vulkan     |  -1 |           pp512 |       1111.67 ± 3.94 |
| qwen3moe 30B.A3B IQ1_M - 1.75 bpw |   9.01 GiB |    30.53 B | Vulkan     |  -1 |           tg128 |        105.57 ± 0.63 |

build: 067de93 (200)
