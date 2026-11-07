| model                          |       size |     params | backend    | ngl | mmap |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | ---: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |           pp512 |      1205.15 ± 16.53 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |           tg128 |         71.58 ± 0.24 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |   pp512 @ d4096 |       912.27 ± 13.24 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |   tg128 @ d4096 |         62.85 ± 0.28 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |   pp512 @ d8192 |       752.09 ± 11.60 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |   tg128 @ d8192 |         56.40 ± 0.17 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |  pp512 @ d16384 |        528.11 ± 9.05 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |  tg128 @ d16384 |         46.81 ± 0.13 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |  pp512 @ d32768 |        323.68 ± 8.30 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |  tg128 @ d32768 |         35.32 ± 0.05 |

build: 067de93 (200)
