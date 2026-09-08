"""Breathe Bishkek — сбор данных о качестве воздуха и погоде.

Два источника:
  1. Open-Meteo — модельные данные (CAMS)
  2. WAQI/aqicn — реальный датчик в Бишкеке
"""

import requests
import csv
import os
from datetime import datetime, timezone, timedelta

LAT, LON = 42.8746, 74.5698
FILE = "data/bishkek_air.csv"
BISHKEK_TZ = timezone(timedelta(hours=6))

AQICN_TOKEN = os.environ.get("AQICN_TOKEN")
STATION = "@93670"  # UN House, Bishkek


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


def get_sensor_data():
    """Реальный датчик через WAQI. Возвращает None при любой проблеме."""
    if not AQICN_TOKEN:
        print("WARNING: AQICN_TOKEN не задан")
        return None, None, None

    try:
        r = requests.get(
            f"https://api.waqi.info/feed/{STATION}/",
            params={"token": AQICN_TOKEN},
            timeout=30,
        ).json()

        if r.get("status") != "ok":
            print("WARNING: WAQI вернул", r.get("status"), r.get("data"))
            return None, None, None

        iaqi = r["data"].get("iaqi", {})
        pm25 = iaqi.get("pm25", {}).get("v")
        pm10 = iaqi.get("pm10", {}).get("v")
        obs_time = r["data"].get("time", {}).get("s")
        return pm25, pm10, obs_time

    except Exception as e:
        print("WARNING: ошибка WAQI:", e)
        return None, None, None


def main():
    air, weather = get_model_data()
    sensor_pm25, sensor_pm10, sensor_time = get_sensor_data()

    row = {
        "time": air["time"],
        "collected_at": datetime.now(BISHKEK_TZ).isoformat(timespec="seconds"),
        # --- модель Open-Meteo ---
        "model_pm2_5": air["pm2_5"],
        "model_pm10": air["pm10"],
        "model_co": air["carbon_monoxide"],
        # --- реальный датчик WAQI ---
        "sensor_pm2_5": sensor_pm25,
        "sensor_pm10": sensor_pm10,
        "sensor_time": sensor_time,
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
