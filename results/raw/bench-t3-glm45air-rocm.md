| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | ROCm       |  -1 |           pp512 |        295.30 ± 6.26 |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | ROCm       |  -1 |           tg128 |         21.89 ± 0.16 |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | ROCm       |  -1 |   pp512 @ d8192 |        182.62 ± 1.98 |
| glm4moe 106B.A12B Q4_K - Medium |  67.96 GiB |   110.47 B | ROCm       |  -1 |   tg128 @ d8192 |         15.87 ± 0.51 |

build: 067de93 (200)
