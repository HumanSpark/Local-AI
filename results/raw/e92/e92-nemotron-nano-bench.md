ggml_vulkan: Found 1 Vulkan devices:
ggml_vulkan: 0 = AMD Radeon Graphics (RADV GFX1151) (radv) | uma: 1 | fp16: 1 | bf16: 0 | fp4: 0 | warp size: 64 | shared memory: 65536 | int dot: 0 | matrix cores: KHR_coopmat
| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |           pp512 |       1006.26 ± 5.50 |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |           tg128 |         64.52 ± 0.81 |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |   pp512 @ d4096 |       890.83 ± 18.74 |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |   tg128 @ d4096 |         63.56 ± 0.12 |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |   pp512 @ d8192 |       847.54 ± 11.91 |
| nemotron_h_moe 31B.A3.5B Q4_K - Medium |  22.96 GiB |    31.58 B | Vulkan     |  -1 |   tg128 @ d8192 |         63.19 ± 0.16 |

build: daef7b687 (1047)
