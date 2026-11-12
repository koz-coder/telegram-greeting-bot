import os
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

TIMEZONE = ZoneInfo("Asia/Tashkent")

CITY = "Ташкент"

LATITUDE = 41.2995
LONGITUDE = 69.2401

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


WEATHER_CODES = {
    0: "☀️ Ясно",
    1: "🌤 Преимущественно ясно",
    2: "⛅ Переменная облачность",
    3: "☁️ Пасмурно",
    45: "🌫 Туман",
    48: "🌫 Туман с изморозью",
    51: "🌦 Лёгкая морось",
    53: "🌦 Морось",
    55: "🌧 Сильная морось",
    56: "🌧 Ледяная морось",
    57: "🌧 Сильная ледяная морось",
    61: "🌧 Небольшой дождь",
    63: "🌧 Дождь",
    65: "🌧 Сильный дождь",
    66: "🌧 Ледяной дождь",
    67: "🌧 Сильный ледяной дождь",
    71: "❄️ Небольшой снег",
    73: "❄️ Снег",
    75: "❄️ Сильный снег",
    77: "🌨 Снежная крупа",
    80: "🌦 Ливневый дождь",
    81: "🌧 Сильные ливни",
    82: "⛈ Очень сильные ливни",
    85: "🌨 Снегопад",
    86: "❄️ Сильный снегопад",
    95: "⛈ Гроза",
    96: "⛈ Гроза с градом",
    99: "⛈ Сильная гроза с градом",
}


def get_weather():
    tomorrow = datetime.now(TIMEZONE).date() + timedelta(days=1)

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max,"
            "precipitation_sum,"
            "wind_speed_10m_max"
        ),
        "timezone": "Asia/Tashkent",
        "forecast_days": 2,
    }

    response = requests.get(
        WEATHER_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    daily = data["daily"]

    dates = daily["time"]
    index = dates.index(tomorrow.isoformat())

    weather_code = daily["weather_code"][index]

    description = WEATHER_CODES.get(
        weather_code,
        "🌤 Переменная погода",
    )

    temperature_min = daily["temperature_2m_min"][index]
    temperature_max = daily["temperature_2m_max"][index]

    rain_probability = daily[
        "precipitation_probability_max"
    ][index]

    precipitation = daily["precipitation_sum"][index]

    wind_speed = daily["wind_speed_10m_max"][index]

    return {
        "date": tomorrow.strftime("%d.%m.%Y"),
        "description": description,
        "min": temperature_min,
        "max": temperature_max,
        "rain_probability": rain_probability,
        "precipitation": precipitation,
        "wind": wind_speed,
    }


def get_recommendation(weather):
    if weather["rain_probability"] >= 60:
        return "☂️ Не забудьте взять зонт."

    if weather["min"] <= 5:
        return "🧥 Завтра лучше одеться потеплее."

    if weather["max"] >= 30:
        return "🧢 Не забудьте головной убор и воду."

    if weather["wind"] >= 30:
        return "💨 Ожидается сильный ветер."

    return "👕 Одевайтесь по погоде."


def send_message(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": GROUP_CHAT_ID,
            "text": message,
        },
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Ошибка Telegram: {result}"
        )


def main():
    if not BOT_TOKEN or not GROUP_CHAT_ID:
        raise RuntimeError(
            "Не найдены BOT_TOKEN или GROUP_CHAT_ID"
        )

    weather = get_weather()

    message = (
        f"🌤 <b>ПОГОДА НА ЗАВТРА</b>\n"
        f"📍 {CITY}\n"
        f"📅 {weather['date']}\n\n"
        f"{weather['description']}\n\n"
        f"🌡 Температура:\n"
        f"Минимум: {weather['min']}°C\n"
        f"Максимум: {weather['max']}°C\n\n"
        f"🌧 Вероятность осадков: "
        f"{weather['rain_probability']}%\n"
        f"💧 Количество осадков: "
        f"{weather['precipitation']} мм\n"
        f"💨 Максимальный ветер: "
        f"{weather['wind']} км/ч\n\n"
        f"{get_recommendation(weather)}\n\n"
        f"❤️ Хорошего вечера!"
    )

    send_message(message)

    print("Прогноз погоды успешно отправлен.")


if __name__ == "__main__":
    main()
