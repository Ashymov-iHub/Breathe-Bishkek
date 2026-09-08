"""Breathe Bishkek — сбор данных о качестве воздуха и погоде.

Источники:
  1. Open-Meteo — модельные данные (CAMS)
  2. sensor.community — реальные датчики SDS011 в Бишкеке
"""

import requests
import csv
import os
import statistics
from datetime import datetime, timezone, timedelta

LAT, LON = 42.8746, 74.5698
FILE = "data/bishkek_air.csv"
BISHKEK_TZ = timezone(timedelta(hours=6))


def get_model_data():
    """Модельные данные Open-Meteo."""
    air = requests.get(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params={"latitude": LAT, "longitude": LON,
                "current": "pm2_5,pm10,carbon_monoxide",
                "timezone": "Asia/Bishkek"},
        timeout=30,
    ).json()["current"]

    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": LAT, "longitude": LON,
                "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,pressure_msl",
                "timezone": "Asia/Bishkek"},
        timeout=30,
    ).json()["current"]

    return air, weather


def get_sensors():
    """Реальные датчики sensor.community в радиусе 10 км от центра."""
    try:
        data = requests.get(
            f"https://data.sensor.community/airrohr/v1/filter/area={LAT},{LON},10",
            timeout=30,
        ).json()
    except Exception as e:
        print("WARNING: sensor.community недоступен:", e)
        return {}

    readings = {}
    for item in data:
        sid = item["sensor"]["id"]
        if sid in readings:
            continue
        values = {v["value_type"]: v["value"] for v in item["sensordatavalues"]}
        if "P2" in values:
            try:
                readings[sid] = {
                    "pm2_5": float(values["P2"]),
                    "pm10": float(values.get("P1", 0)) or None,
                    "timestamp": item["timestamp"],
                }
            except (ValueError, TypeError):
                continue

    return readings


def main():
    air, weather = get_model_data()
    sensors = get_sensors()

    pm25_values = [s["pm2_5"] for s in sensors.values()]
    pm10_values = [s["pm10"] for s in sensors.values() if s["pm10"]]

    row = {
        "time": air["time"],
        "collected_at": datetime.now(BISHKEK_TZ).isoformat(timespec="seconds"),
        # --- модель Open-Meteo ---
        "model_pm2_5": air["pm2_5"],
        "model_pm10": air["pm10"],
        "model_co": air["carbon_monoxide"],
        # --- реальные датчики (агрегаты) ---
        "sensor_count": len(pm25_values),
        "sensor_pm2_5_median": round(statistics.median(pm25_values), 2) if pm25_values else None,
        "sensor_pm2_5_min": min(pm25_values) if pm25_values else None,
        "sensor_pm2_5_max": max(pm25_values) if pm25_values else None,
        "sensor_pm10_median": round(statistics.median(pm10_values), 2) if pm10_values else None,
        # --- сырые значения по каждому датчику ---
        "sensor_raw": ";".join(f"{sid}={s['pm2_5']}" for sid, s in sorted(sensors.items())),
        # --- погода ---
        "temp": weather["temperature_2m"],
        "humidity": weather["relative_humidity_2m"],
        "wind": weather["wind_speed_10m"],
        "pressure": weather["pressure_msl"],
    }

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
