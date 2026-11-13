import os
import math
import random
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ==============================
# НАСТРОЙКИ
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

TIMEZONE = ZoneInfo("Asia/Tashkent")

LAT = 41.2995
LON = 69.2401

WIDTH = 540
HEIGHT = 675
FRAMES = 24
DURATION = 100

OUTPUT_FILE = "weather_animation.gif"

API_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Ясно",
    1: "Преимущественно ясно",
    2: "Переменная облачность",
    3: "Облачно",
    45: "Туман",
    48: "Туман",
    51: "Небольшая морось",
    53: "Морось",
    55: "Сильная морось",
    56: "Ледяная морось",
    57: "Сильная ледяная морось",
    61: "Небольшой дождь",
    63: "Дождь",
    65: "Сильный дождь",
    66: "Ледяной дождь",
    67: "Сильный ледяной дождь",
    71: "Небольшой снег",
    73: "Снег",
    75: "Сильный снег",
    77: "Снежная крупа",
    80: "Ливень",
    81: "Сильный ливень",
    82: "Очень сильный ливень",
    85: "Снегопад",
    86: "Сильный снегопад",
    95: "Гроза",
    96: "Гроза с градом",
    99: "Сильная гроза"
}


# ==============================
# ШРИФТЫ
# ==============================

def get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"
    ]

    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


# ==============================
# ПОЛУЧЕНИЕ ПОГОДЫ
# ==============================

def get_weather():
    tomorrow = datetime.now(TIMEZONE).date() + timedelta(days=1)

    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": (
            "temperature_2m,apparent_temperature,"
            "relative_humidity_2m,weather_code,"
            "wind_speed_10m,is_day"
        ),
        "hourly": (
            "temperature_2m,weather_code"
        ),
        "daily": (
            "weather_code,temperature_2m_max,"
            "temperature_2m_min,precipitation_probability_max,"
            "precipitation_sum,wind_speed_10m_max,"
            "sunrise,sunset"
        ),
        "timezone": "Asia/Tashkent",
        "forecast_days": 2
    }

    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    daily = data["daily"]

    index = daily["time"].index(tomorrow.isoformat())

    hourly = data["hourly"]

    hours = []

    for target_hour in [9, 12, 15, 18]:
        target = f"{tomorrow.isoformat()}T{target_hour:02d}:00"

        try:
            hour_index = hourly["time"].index(target)
            temperature = hourly["temperature_2m"][hour_index]
        except (ValueError, IndexError):
            temperature = None

        hours.append({
            "hour": target_hour,
            "temperature": temperature
        })

    current = data["current"]

    return {
        "date": tomorrow,
        "current_temp": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "wind": current["wind_speed_10m"],
        "current_code": current["weather_code"],
        "max": daily["temperature_2m_max"][index],
        "min": daily["temperature_2m_min"][index],
        "code": daily["weather_code"][index],
        "rain": daily["precipitation_probability_max"][index] or 0,
        "precipitation": daily["precipitation_sum"][index] or 0,
        "max_wind": daily["wind_speed_10m_max"][index],
        "sunrise": daily["sunrise"][index][-5:],
        "sunset": daily["sunset"][index][-5:],
        "hours": hours
    }


# ==============================
# ОПРЕДЕЛЕНИЕ АНИМАЦИИ
# ==============================

def get_effect(code):
    if code in [95, 96, 99]:
        return "storm"

    if code in [71, 73, 75, 77, 85, 86]:
        return "snow"

    if code in [51, 53, 55, 56, 57, 61, 63, 65,
                66, 67, 80, 81, 82]:
        return "rain"

    if code in [2, 3, 45, 48]:
        return "cloud"

    return "sun"


# ==============================
# ФОН КАРТОЧКИ
# ==============================

def create_background():
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()

    for y in range(HEIGHT):
        for x in range(WIDTH):
            ratio = y / HEIGHT

            r = int(15 + ratio * 12)
            g = int(25 + ratio * 8)
            b = int(65 + ratio * 40)

            pixels[x, y] = (r, g, b)

    return image


# ==============================
# РИСОВАНИЕ КАРТОЧКИ
# ==============================

def create_static_card(weather):
    image = create_background().convert("RGBA")

    draw = ImageDraw.Draw(image)

    title_font = get_font(25, True)
    big_font = get_font(66, True)
    medium_font = get_font(25, True)
    normal_font = get_font(19)
    small_font = get_font(16)

    tomorrow = weather["date"]

    date_text = tomorrow.strftime("%d.%m.%Y")

    draw.text(
        (35, 28),
        "ПОГОДА В ТАШКЕНТЕ",
        font=title_font,
        fill="white"
    )

    draw.text(
        (37, 65),
        f"Прогноз на завтра • {date_text}",
        font=small_font,
        fill=(190, 205, 235)
    )

    # Текущая температура

    draw.text(
        (35, 120),
        f"{weather['current_temp']:.0f}°",
        font=big_font,
        fill="white"
    )

    draw.text(
        (38, 205),
        "Сейчас",
        font=normal_font,
        fill=(200, 215, 240)
    )

    draw.text(
        (38, 245),
        f"Ощущается как {weather['feels_like']:.0f}°",
        font=normal_font,
        fill="white"
    )

    # Карточка прогноза

    draw.rounded_rectangle(
        (25, 300, 515, 445),
        radius=22,
        fill=(255, 255, 255, 28),
        outline=(255, 255, 255, 65),
        width=2
    )

    description = WEATHER_CODES.get(
        weather["code"], "Переменная погода"
    )

    draw.text(
        (45, 318),
        "ЗАВТРА",
        font=medium_font,
        fill=(200, 215, 245)
    )

    draw.text(
        (45, 355),
        description,
        font=medium_font,
        fill="white"
    )

    draw.text(
        (45, 400),
        f"Максимум {weather['max']:.0f}°"
        f"     Минимум {weather['min']:.0f}°",
        font=normal_font,
        fill="white"
    )

    # Показатели

    draw.rounded_rectangle(
        (25, 460, 515, 535),
        radius=18,
        fill=(255, 255, 255, 25)
    )

    draw.text(
        (45, 480),
        f"💧 {weather['humidity']}%",
        font=normal_font,
        fill="white"
    )

    draw.text(
        (210, 480),
        f"Ветер {weather['wind']:.0f} км/ч",
        font=normal_font,
        fill="white"
    )

    draw.text(
        (45, 515),
        f"Вероятность осадков: {weather['rain']}%",
        font=small_font,
        fill=(220, 230, 250)
    )

    # Почасовой прогноз

    draw.text(
        (30, 555),
        "ПО ЧАСАМ",
        font=small_font,
        fill=(190, 205, 235)
    )

    x_positions = [45, 165, 285, 405]

    for position, item in zip(x_positions, weather["hours"]):
        temperature = item["temperature"]

        if temperature is None:
            temperature_text = "—"
        else:
            temperature_text = f"{temperature:.0f}°"

        draw.text(
            (position, 585),
            f"{item['hour']:02d}:00",
            font=small_font,
            fill=(190, 205, 235)
        )

        draw.text(
            (position, 615),
            temperature_text,
            font=medium_font,
            fill="white"
        )

    draw.text(
        (35, 650),
        f"Восход {weather['sunrise']}  •  Закат {weather['sunset']}",
        font=get_font(14),
        fill=(185, 200, 225)
    )

    return image


# ==============================
# АНИМАЦИЯ ДОЖДЯ
# ==============================

def add_rain(frame, phase, intensity=1):
    draw = ImageDraw.Draw(frame, "RGBA")

    random.seed(100)

    count = 100 if intensity == 1 else 180

    for i in range(count):
        x = random.randint(0, WIDTH)
        start_y = random.randint(-HEIGHT, HEIGHT)

        y = (start_y + phase * random.randint(15, 28)) % HEIGHT

        length = random.randint(12, 25)

        draw.line(
            (x, y, x - 5, y + length),
            fill=(180, 220, 255, 155),
            width=2
        )

    return frame


# ==============================
# АНИМАЦИЯ СНЕГА
# ==============================

def add_snow(frame, phase):
    draw = ImageDraw.Draw(frame, "RGBA")

    random.seed(200)

    for i in range(100):
        x = random.randint(0, WIDTH)
        start_y = random.randint(-HEIGHT, HEIGHT)

        speed = random.randint(5, 12)

        y = (start_y + phase * speed) % HEIGHT

        drift = int(math.sin((phase + i) / 3) * 8)

        radius = random.randint(2, 5)

        draw.ellipse(
            (
                x + drift - radius,
                y - radius,
                x + drift + radius,
                y + radius
            ),
            fill=(255, 255, 255, 210)
        )

    return frame


# ==============================
# ДВИЖУЩИЕСЯ ОБЛАКА
# ==============================

def add_clouds(frame, phase):
    draw = ImageDraw.Draw(frame, "RGBA")

    for i in range(5):
        x = ((i * 150 + phase * 5) % (WIDTH + 180)) - 90
        y = 110 + i * 35

        draw.ellipse(
            (x, y, x + 100, y + 35),
            fill=(210, 220, 240, 65)
        )

        draw.ellipse(
            (x + 20, y - 15, x + 75, y + 35),
            fill=(210, 220, 240, 65)
        )

    return frame


# ==============================
# СОЛНЦЕ
# ==============================

def add_sun(frame, phase):
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    pulse = int(15 + 8 * math.sin(phase / 3))

    draw.ellipse(
        (350 - pulse, 105 - pulse,
         440 + pulse, 195 + pulse),
        fill=(255, 210, 90, 45)
    )

    overlay = overlay.filter(ImageFilter.GaussianBlur(18))

    frame.alpha_composite(overlay)

    draw = ImageDraw.Draw(frame, "RGBA")

    draw.ellipse(
        (370, 125, 420, 175),
        fill=(255, 220, 120, 230)
    )

    return frame


# ==============================
# СОЗДАНИЕ GIF
# ==============================

def create_animation(weather):
    base = create_static_card(weather)

    effect = get_effect(weather["code"])

    frames = []

    intensity = 2 if weather["code"] in [
        65, 67, 75, 82, 86, 95, 96, 99
    ] else 1

    for phase in range(FRAMES):
        frame = base.copy()

        if effect in ["rain", "storm"]:
            add_rain(frame, phase, intensity)

        elif effect == "snow":
            add_snow(frame, phase)

        elif effect == "cloud":
            add_clouds(frame, phase)

        elif effect == "sun":
            add_sun(frame, phase)

        if effect == "storm" and phase % 8 in [0, 1]:
            draw = ImageDraw.Draw(frame, "RGBA")
            draw.rectangle(
                (0, 0, WIDTH, HEIGHT),
                fill=(255, 255, 255, 35)
            )

        frames.append(
            frame.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE)
        )

    frames[0].save(
        OUTPUT_FILE,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION,
        loop=0,
        optimize=True
    )

    print(f"Анимация создана: {OUTPUT_FILE}")

    return OUTPUT_FILE


# ==============================
# ОТПРАВКА В TELEGRAM
# ==============================

def send_weather_animation(path):
    if not BOT_TOKEN or not GROUP_CHAT_ID:
        raise ValueError("Не найдены BOT_TOKEN или GROUP_CHAT_ID")

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAnimation"

    with open(path, "rb") as animation:
        response = requests.post(
            url,
            data={"chat_id": GROUP_CHAT_ID},
            files={"animation": animation},
            timeout=60
        )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")

    print("Анимированная погода успешно отправлена!")


# ==============================
# ЗАПУСК
# ==============================

def main():
    print("Получаем прогноз погоды...")

    weather = get_weather()

    print("Создаём анимацию...")

    animation = create_animation(weather)

    print("Отправляем в Telegram...")

    send_weather_animation(animation)


if __name__ == "__main__":
    main()
