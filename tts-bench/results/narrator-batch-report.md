# W3 narrator batch - re-render + intelligibility audit

**Project:** sparkbench | **Date:** 2026-07-26 | **Run:** unattended via `stage2-sweep/run_batch.sh`

Written because three garbled narrator renders were delivered as candidates after passing every
duration/level/flat-factor screen. Those screens answer *does audio exist at a sane level*, not
*is this speech*. This audit gates renders on ASR-vs-requested-text word error rate.

**Filename note (2026-07-27):** every `stage2-sweep/out/refvoice/*.wav` file named below by its bare
name (`cb_tra_a.wav`, `narr_cosy_p233.wav`, etc.) was renamed the same day to carry its verdict in the
filename - see `docs/w3-audio-rename-log.csv` for the old->new mapping and
`docs/w3-audio-audit-report.md` for the narrative. The log output below is left verbatim as the
original captured evidence; it is not stale, the files it refers to just have a longer name now.

```
step 1 render  exit=0
step 2 control exit=0   (human reference vs its own transcript - MUST be 0)
step 3 audit   exit=1   (non-zero = at least one render rejected)
```

## Render metrics

| file | duration | words/sec | mean dB |
|---|---|---|---|
| narr_cosy_p233.wav | 9.80s | 2.65 | -23.5 |
| narr_cosy_p239dn.wav | 5.28s | 4.92 | -26.2 |
| narr_cosy_p239.wav | 9.60s | 2.71 | -25.8 |

## Gate verdicts

```
expected (22 words): these take the shape of a long round arch with its path high above and its two ends apparently beyond the horizon
p233_008.flac                      WER  0.00  ok
    heard: these take the shape of a long round arch with its path high above and its two ends apparently beyond the horizon
all 1 render(s) intelligible (WER <= 0.5)
expected (26 words): the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cb_ac_c50_slow.wav                 WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cb_ac_c50.wav                      WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cb_ac_c70_slow.wav                 WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cb_ac_c70.wav                      WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cb_tra_a.wav                       WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cb_tra_b.wav                       WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cb_uk_asis.wav                     WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cb_uk_slower.wav                   WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cb_uk_slowest.wav                  WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
cosy_copyacc.wav                   WER  0.96  GARBLED
    heard: the eodleanppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp
cosy_irish.wav                     WER  6.85  GARBLED
    heard: desi oh beep oh yeah beep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh jeep oh j
cosy_tra_s10.wav                   WER  0.96  GARBLED
    heard: up that g and each to that pew but
cosy_zs.wav                        WER  0.96  GARBLED
    heard: i'll blow that up oh dear and uh i'll reach that out pew but
f5_tra_s088.wav                    WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
f5_tra_s10.wav                     WER  0.04  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool and
narr_cosy_p233.wav                 WER  8.54  GARBLED
    heard: yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes yes ye
narr_cosy_p239dn.wav               WER  0.96  GARBLED
    heard: what's that what's that what's that what's that what's that
narr_cosy_p239.wav                 WER  2.50  GARBLED
    heard: or we it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's it's
vox_tra_clone.wav                  WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
vox_uk_clone.wav                   WER  0.00  ok
    heard: the businesses that win with ai won't be the ones with the biggest budgets they'll be the ones who understood the problem before buying the tool
7 render(s) rejected as not intelligible: ['cosy_copyacc.wav', 'cosy_irish.wav', 'cosy_tra_s10.wav', 'cosy_zs.wav', 'narr_cosy_p233.wav', 'narr_cosy_p239dn.wav', 'narr_cosy_p239.wav']
[16:15:40] STEP 3 exit=1 (non-zero simply means at least one render was rejected)
```

Full log: `stage2-sweep/out/batch.log` (gitignored). Audio is gitignored and regenerable.

## What a fresh session should do with this

1. If the control failed, fix the gate before believing anything else here.
2. Ship ONLY renders marked `ok` to the owner. A `GARBLED` render must never be presented as
   an engine's work, and must not be used to explain anything about voice quality or accent.
3. Check whether the renders the owner already judged on ACCENT are `ok`. Any that are
   `GARBLED` invalidate the feedback given on them, including parts of F54.
4. Compare `n2_*_zs` against `n2_*_xl` - that isolates whether zero-shot or cross-lingual is
   the reliable mode on this box, which the first attempt could not distinguish.
