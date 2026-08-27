# Breathe Bishkek

Bishkek is one of the most polluted cities in the world during
the winter heating season. Public sensors show current values,
but there is no open, structured record of how air quality moves
together with weather over time.

This repository collects that record.

## What it does

Every hour, a GitHub Action pulls current air quality and weather
for Bishkek and appends one row to `data/bishkek_air.csv`.

| Column | Meaning |
|---|---|
| `time` | Timestamp of the reading (Asia/Bishkek) |
| `collected_at` | When the script ran |
| `pm2_5`, `pm10`, `co` | Pollutant concentrations, µg/m³ |
| `temp`, `humidity`, `wind`, `pressure` | Weather conditions |

## Data source

[Open-Meteo](https://open-meteo.com) air quality and forecast APIs.

## Status

Collecting data since August 2026. Analysis to follow once enough
of the heating season is covered.

---

Built by Ibrahim, Bishkek.
