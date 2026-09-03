"""Breathe Bishkek — сбор данных о качестве воздуха и погоде."""

import os
import csv
import time
import requests
from datetime import datetime, timezone

LAT, LON = 42.8746, 74.5698
FILE = "data/bishkek_air.csv"
BISHKEK_TZ = timezone(timedelta(hours=6))


def get_with_retry(url, params, tries=3, timeout=60):
    last_error = None
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_error = e
            print(f"Попытка {attempt + 1} не удалась: {e}")
            time.sleep(5)
    raise last_error


def collect():
        air = get_with_retry(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params={"latitude": LAT, "longitude": LON,
                "current": "pm2_5,pm10,carbon_monoxide",
                "timezone": "Asia/Bishkek"},
    )["current"]

        weather = get_with_retry(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": LAT, "longitude": LON,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,pressure_msl",
                "timezone": "Asia/Bishkek"},
    )["current"]

    return {
        "time": air["time"],
        "collected_at": datetime.now(BISHKEK_TZ).isoformat(timespec="seconds"),
        "pm2_5": air["pm2_5"],
        "pm10": air["pm10"],
        "co": air["carbon_monoxide"],
        "temp": weather["temperature_2m"],
        "humidity": weather["relative_humidity_2m"],
        "wind": weather["wind_speed_10m"],
        "pressure": weather["pressure_msl"],
    }


def main():
    row = collect()
    os.makedirs("data", exist_ok=True)
    exists = os.path.exists(FILE)

    with open(FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not exists:
            writer.writeheader()
        writer.writerow(row)

    print("OK:", row)


if __name__ == "__main__":
    main()
