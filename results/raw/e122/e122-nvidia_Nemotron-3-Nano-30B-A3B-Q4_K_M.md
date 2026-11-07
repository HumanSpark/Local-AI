| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |           pp512 |       992.85 ± 25.50 |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |           tg128 |         64.11 ± 0.13 |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |   pp512 @ d4096 |       891.11 ± 21.44 |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |   tg128 @ d4096 |         63.67 ± 0.17 |

build: daef7b687 (1047)
