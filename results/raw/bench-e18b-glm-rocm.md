| model                          |       size |     params | backend    | ngl | mmap |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | ---: | --------------: | -------------------: |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |           pp512 |       924.50 ± 25.20 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |           tg128 |         52.98 ± 0.12 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |   pp512 @ d4096 |        451.73 ± 2.82 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |   tg128 @ d4096 |         47.06 ± 0.14 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |   pp512 @ d8192 |        300.10 ± 2.22 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |   tg128 @ d8192 |         42.43 ± 0.17 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |  pp512 @ d16384 |        174.47 ± 1.40 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |  tg128 @ d16384 |         35.20 ± 0.11 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |  pp512 @ d32768 |         95.38 ± 0.72 |
| deepseek2 30B.A3B Q4_K - Medium |  17.05 GiB |    29.94 B | ROCm       |  -1 |    0 |  tg128 @ d32768 |         26.20 ± 0.04 |

build: 067de93 (200)
