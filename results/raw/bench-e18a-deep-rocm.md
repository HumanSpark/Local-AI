| model                          |       size |     params | backend    | ngl | mmap |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | ---: | --------------: | -------------------: |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |  pp512 @ d65536 |        189.53 ± 3.52 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |  tg128 @ d65536 |         23.50 ± 0.14 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |  pp512 @ d98304 |        133.86 ± 2.34 |
| qwen3moe 30B.A3B Q4_K - Medium |  17.28 GiB |    30.53 B | ROCm       |  -1 |    0 |  tg128 @ d98304 |         17.83 ± 0.01 |

build: 067de93 (200)
