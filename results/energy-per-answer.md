<!--
# File: results/energy-per-answer.md
# Purpose: Energy per coding task and per correct answer on this machine, compared with a fridge-freezer.
# Project: sparkbench | Date: 2026-11-25
#
# Overview: Owner 2026-11-25: add energy per answer, and "compare it with a typical fridge". Computed by
# tools/energy_per_answer.py from existing task records and measured chip power; no new runs.
-->

# Energy per answer, and what a fridge uses

## In plain English

While it works, this machine draws about as much power as nearly three fridge-freezers running at once: 121 W at the
wall, against a fridge-freezer's 44.5 W average. An everyday coding fix took a median 9.9 min, about 20 Wh, the
electricity a fridge-freezer uses in about 27 minutes. On the ten large changes, where production solved half, each
correct answer cost about 70 Wh at the wall, roughly what a fridge-freezer uses in an hour and a half.

## Figures (production: Qwen3.8-Flash-Next on Halogen)

| Run | Solved | Energy per task (wall) | Fridge-freezer equivalent per task | Energy per correct answer (wall) |
|---|---|---|---|---|
| 15 everyday fixes, 5 Nov | 15/15 | 20.1 Wh | 27 min | 21 Wh |
| 10 large changes, 18 Nov | 5/10 | 23.1 Wh | 31 min | 70 Wh (94 min) |

## How it is worked out

- **Wall power: 121.4 W, measured.** A Tapo P304M strip on lanhost feeds benchhost from socket 4; the fleet's
  read-only power log recorded 102 one-minute readings on 22 Nov, 12:47-15:10 UTC, while benchhost ran a sustained
  coding job (Hy4-Flash on the Strata engine, E171): median 121.4 W, range 119.2-125.1 W, 10-minute means 120.1-122.7 W.
  The strip's own energy counter agrees (0.288 kWh in 2.37 h = 121.5 W). Production's engine was not on the meter that
  day; its chip power on code is 87.0 W (E153), so the same box under production load is expected near this figure,
  not measured.
- **Energy per task** = task time x 121.4 W. This counts the whole task at working power, though the GPU idles while
  tests run; with the box drawing about 120 W either way during a coding run, the difference is small.
- **Energy per correct answer** = all energy used on the bank / tasks solved, so failed attempts count against it.
- **Fridge-freezer:** 390 kWh a year on average, from the UK government's Cold Appliances Field Trial (Building
  Research Establishment for the Department of Business, Energy & Industrial Strategy, 2017, Table 6, page 25;
  998 appliances in 766 homes). That is 44.5 W around the clock; a fridge-freezer cycles on and off, so 44.5 W is its
  average over a year.
- The earlier estimate (chip power plus 10-25 W) understated the wall draw: measured overhead is nearer 30 W.

## Whole months, from the Tapo app (socket 4 is benchhost, owner confirmed 2026-11-25)

Screenshots of the Tapo app's Energy Monitoring screen, taken 2026-11-25 07:45-07:46, cropped to the totals and
charts: `results/energy/tapo-app-2026-11-25/`. The figures below are copied from them exactly.

| Period | Energy used | What it means |
|---|---|---|
| 25 Nov, midnight to 07:45 | 0.863 kWh in 7.8h | 111 W average: the overnight benchmark run |
| November to date | 21.088 kWh (runtime 583.6h) | the busiest month; about two-thirds of a fridge-freezer's month (32.5 kWh) |
| October | 6.681 kWh | a quiet month; about a fifth of a fridge-freezer's month |
| September | 18.584 kWh | |
| 2026 since the plug was fitted (August on) | 50.84 kWh | |

Busiest single day in November: 2.724 kWh (113 W averaged over 24h, a full day of coding benchmarks). Quiet days run
about 0.15-0.25 kWh, roughly 6-10 W: the box idle with the everyday model ready to answer. The app's November bill,
EUR 7.791, implies EUR 0.369/kWh, the rate set in the app; the cost model still uses the July tariff of EUR 0.298/kWh.

## The Tapo export (email from TP-Link, 2026-11-25 07:46, two attachments)

Kept unchanged in `results/energy/tapo-export-2026-11-25/` (`energy-usage.xls`, `power.xls`) with a CSV of every sheet
beside them: power every 5 minutes for the last 24 hours, hourly power and energy for 19-25 Nov, daily energy from
1 Sep, monthly for the year. Figures:

- **Idle: about 7 W** (median of 66 five-minute readings under 30 W in the last 24h): the box waiting, everyday model ready.
- **Working: about 120 W** (median of 209 readings over 90 W; range 91-165 W), matching the 121.4 W from the fleet log.
- **19-25 Nov: 6.25 kWh, costing EUR 1.82** on the actual tariff, with 38% of it used at the night rate.
- **November to date: 21.09 kWh**, busiest day 2.72 kWh.

## What it costs on the actual tariff

SSE Airtricity, 1 Year Smart Day/Night/Peak 30% (rates from 5 Oct 2026, as listed): night 20.56c (23:00-08:00), day
33.81c, peak 37.88c (17:00-19:00).

| Item | Energy (wall) | At night rate | At day rate |
|---|---|---|---|
| One everyday coding fix | 20.1 Wh | 0.41c | 0.68c |
| One correct large change | 70 Wh | 1.4c | 2.4c |
| An hour of work | 121 Wh | 2.5c | 4.1c |
| A day idle | 0.17 kWh (7 W) | | about 5c |

For comparison, Claude Sonnet 5.5 solved the same 15 everyday fixes for USD 1.23 in API fees, about 8 US cents a fix
(E154). Electricity only: the machine's purchase price, standing charges and a person's time are not included.

## Limits

Wall power was metered for one 2.4-hour coding window on 22 Nov, on another engine; the power log has been stopped
since (the strip is not to be rebooted). Hourly history for other days exists only in the Tapo app. Cloud models' energy is not known and not compared.

Source: Cold appliances field trial report, BRE for BEIS, January 2017,
https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/585520/Cold_appliances_field_trial_report_FINAL_230117__2_.pdf
