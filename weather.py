import os
import math
import requests

from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# =====================================================
# НАСТРОЙКИ
# =====================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "").strip()

TIMEZONE = ZoneInfo("Asia/Tashkent")

CITY = "Ташкент"

LATITUDE = 41.2995
LONGITUDE = 69.2401

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WIDTH = 1080
HEIGHT = 1350
SCALE = 2

W = WIDTH * SCALE
H = HEIGHT * SCALE

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "weather_card.png"


# =====================================================
# ПОГОДНЫЕ ОПИСАНИЯ
# =====================================================

WEATHER_CODES = {
    0: "Ясно",
    1: "Преимущественно ясно",
    2: "Переменная облачность",
    3: "Пасмурно",
    45: "Туман",
    48: "Туман с изморозью",
    51: "Лёгкая морось",
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
    80: "Ливневый дождь",
    81: "Сильные ливни",
    82: "Очень сильные ливни",
    85: "Снегопад",
    86: "Сильный снегопад",
    95: "Гроза",
    96: "Гроза с градом",
    99: "Сильная гроза с градом",
}


# =====================================================
# ШРИФТЫ И МАСШТАБ
# =====================================================

def s(value):
    return int(value * SCALE)


def get_font(size, bold=False):
    paths = [
        (
            "/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans-Bold.ttf"
            if bold else
            "/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans.ttf"
        ),
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
    ]

    for path in paths:
        try:
            return ImageFont.truetype(path, s(size))
        except OSError:
            continue

    return ImageFont.load_default()


# =====================================================
# ПОЛУЧЕНИЕ ПОГОДЫ
# =====================================================

def get_weather():

    tomorrow = (
        datetime.now(TIMEZONE).date()
        + timedelta(days=1)
    )

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,

        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "is_day,"
            "weather_code,"
            "wind_speed_10m"
        ),

        "hourly": (
            "temperature_2m,"
            "precipitation_probability,"
            "weather_code"
        ),

        "daily": (
            "weather_code,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_probability_max,"
            "precipitation_sum,"
            "wind_speed_10m_max,"
            "sunrise,"
            "sunset"
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

    current = data["current"]
    daily = data["daily"]
    hourly = data["hourly"]

    tomorrow_string = tomorrow.isoformat()

    try:
        index = daily["time"].index(tomorrow_string)
    except ValueError:
        raise ValueError(
            "Не удалось получить прогноз на завтра."
        )

    hourly_forecast = []

    target_hours = [9, 12, 15, 18]

    for hour in target_hours:

        target_time = (
            f"{tomorrow_string}T"
            f"{hour:02d}:00"
        )

        if target_time not in hourly["time"]:
            continue

        hour_index = hourly["time"].index(
            target_time
        )

        hourly_forecast.append({
            "time": f"{hour:02d}:00",

            "temperature": hourly[
                "temperature_2m"
            ][hour_index],

            "code": hourly[
                "weather_code"
            ][hour_index],

            "rain": hourly[
                "precipitation_probability"
            ][hour_index],
        })

    return {
        "city": CITY,

        "current_temp": current[
            "temperature_2m"
        ],

        "feels_like": current[
            "apparent_temperature"
        ],

        "humidity": current[
            "relative_humidity_2m"
        ],

        "current_wind": current[
            "wind_speed_10m"
        ],

        "current_code": current[
            "weather_code"
        ],

        "current_is_day": current[
            "is_day"
        ],

        "date": tomorrow.strftime("%d.%m.%Y"),

        "weekday": tomorrow.strftime("%A"),

        "description": WEATHER_CODES.get(
            daily["weather_code"][index],
            "Переменная погода"
        ),

        "code": daily["weather_code"][index],

        "min": daily[
            "temperature_2m_min"
        ][index],

        "max": daily[
            "temperature_2m_max"
        ][index],

        "rain_probability": daily[
            "precipitation_probability_max"
        ][index],

        "precipitation": daily[
            "precipitation_sum"
        ][index],

        "wind": daily[
            "wind_speed_10m_max"
        ][index],

        "sunrise": daily[
            "sunrise"
        ][index][-5:],

        "sunset": daily[
            "sunset"
        ][index][-5:],

        "hourly": hourly_forecast,
    }


# =====================================================
# РЕКОМЕНДАЦИЯ
# =====================================================

def get_recommendation(weather):

    if weather["rain_probability"] >= 60:
        return "Возьмите с собой зонт."

    if weather["min"] <= 5:
        return "Завтра лучше одеться потеплее."

    if weather["max"] >= 30:
        return "Не забудьте головной убор и воду."

    if weather["wind"] >= 30:
        return "Ожидается сильный ветер."

    if weather["min"] <= 12:
        return "Утром будет прохладно. Возьмите куртку."

    return "Хороший день для прогулок!"


# =====================================================
# ФОН
# =====================================================

def create_background():

    image = Image.new(
        "RGB",
        (W, H)
    )

    pixels = image.load()

    top = (20, 105, 190)
    bottom = (65, 59, 145)

    for y in range(H):

        t = y / H
        t = t * t * (3 - 2 * t)

        color = tuple(
            int(
                top[i] * (1 - t)
                + bottom[i] * t
            )
            for i in range(3)
        )

        for x in range(W):
            pixels[x, y] = color

    glow = Image.new(
        "RGBA",
        (W, H),
        (0, 0, 0, 0)
    )

    gd = ImageDraw.Draw(glow)

    gd.ellipse(
        (
            s(650),
            s(-200),
            s(1250),
            s(400)
        ),
        fill=(110, 190, 255, 65)
    )

    glow = glow.filter(
        ImageFilter.GaussianBlur(s(100))
    )

    return Image.alpha_composite(
        image.convert("RGBA"),
        glow
    )


# =====================================================
# ПОГОДНЫЕ ИКОНКИ
# =====================================================

def draw_weather_icon(image, x, y, code, size=70):

    draw = ImageDraw.Draw(image)

    cx = s(x)
    cy = s(y)
    r = s(size)

    # Солнце
    if code in [0, 1]:

        draw.ellipse(
            (
                cx-r//2,
                cy-r//2,
                cx+r//2,
                cy+r//2
            ),
            fill="#FFD76A"
        )

        for angle in range(0, 360, 45):

            rad = math.radians(angle)

            x1 = cx + int(r * 0.65 * math.cos(rad))
            y1 = cy + int(r * 0.65 * math.sin(rad))

            x2 = cx + int(r * 0.9 * math.cos(rad))
            y2 = cy + int(r * 0.9 * math.sin(rad))

            draw.line(
                (x1, y1, x2, y2),
                fill="#FFD76A",
                width=s(5)
            )

    # Облака
    elif code in [2, 3, 45, 48]:

        draw.ellipse(
            (
                cx-r//2,
                cy-r//2,
                cx,
                cy+r//3
            ),
            fill="#E5F1FF"
        )

        draw.ellipse(
            (
                cx-r//5,
                cy-r*0.7,
                cx+r//2,
                cy+r//3
            ),
            fill="#FFFFFF"
        )

        draw.rounded_rectangle(
            (
                cx-r//2,
                cy,
                cx+r//2,
                cy+r//2
            ),
            radius=s(15),
            fill="#FFFFFF"
        )

    # Дождь
    elif code in range(51, 68) or code in range(80, 83):

        draw.ellipse(
            (
                cx-r//2,
                cy-r//2,
                cx,
                cy+r//3
            ),
            fill="#E5F1FF"
        )

        draw.ellipse(
            (
                cx-r//5,
                cy-r//2,
                cx+r//2,
                cy+r//3
            ),
            fill="#FFFFFF"
        )

        draw.rounded_rectangle(
            (
                cx-r//2,
                cy,
                cx+r//2,
                cy+r//2
            ),
            radius=s(15),
            fill="#FFFFFF"
        )

        for offset in [-25, 0, 25]:

            draw.line(
                (
                    cx+s(offset),
                    cy+s(30),
                    cx+s(offset-10),
                    cy+s(50)
                ),
                fill="#68C5FF",
                width=s(5)
            )

    # Снег
    elif code in range(71, 78) or code in [85, 86]:

        draw.ellipse(
            (
                cx-r//2,
                cy-r//2,
                cx,
                cy+r//3
            ),
            fill="#FFFFFF"
        )

        draw.ellipse(
            (
                cx-r//5,
                cy-r//2,
                cx+r//2,
                cy+r//3
            ),
            fill="#FFFFFF"
        )

        for offset in [-25, 0, 25]:

            draw.ellipse(
                (
                    cx+s(offset)-s(5),
                    cy+s(32),
                    cx+s(offset)+s(5),
                    cy+s(42)
                ),
                fill="#BDE8FF"
            )

    # Гроза
    else:

        draw.ellipse(
            (
                cx-r//2,
                cy-r//2,
                cx,
                cy+r//3
            ),
            fill="#D9E6F8"
        )

        draw.ellipse(
            (
                cx-r//5,
                cy-r//2,
                cx+r//2,
                cy+r//3
            ),
            fill="#FFFFFF"
        )

        points = [
            (cx, cy+s(20)),
            (cx-s(15), cy+s(48)),
            (cx+s(3), cy+s(48)),
            (cx-s(5), cy+s(75)),
            (cx+s(23), cy+s(40)),
            (cx+s(7), cy+s(40)),
        ]

        draw.polygon(
            points,
            fill="#FFD34F"
        )


# =====================================================
# БЕЛАЯ КАРТОЧКА
# =====================================================

def draw_card(image, x, y, width, height):

    shadow = Image.new(
        "RGBA",
        (W, H),
        (0, 0, 0, 0)
    )

    sd = ImageDraw.Draw(shadow)

    sd.rounded_rectangle(
        (
            s(x+4),
            s(y+8),
            s(x+width+4),
            s(y+height+8)
        ),
        radius=s(28),
        fill=(0, 0, 0, 55)
    )

    shadow = shadow.filter(
        ImageFilter.GaussianBlur(s(12))
    )

    image.alpha_composite(shadow)

    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (
            s(x),
            s(y),
            s(x+width),
            s(y+height)
        ),
        radius=s(28),
        fill="#FFFFFF"
    )


# =====================================================
# СОЗДАНИЕ КАРТОЧКИ
# =====================================================

def create_weather_card(weather):

    image = create_background()

    draw = ImageDraw.Draw(image)

    # Заголовок
    draw.text(
        (s(70), s(65)),
        "ПОГОДА УЗБЕКИСТАНА",
        font=get_font(22, True),
        fill="#CBE4FF"
    )

    draw.text(
        (s(70), s(110)),
        "Ташкент",
        font=get_font(65, True),
        fill="#FFFFFF"
    )

    draw.text(
        (s(75), s(195)),
        f"Прогноз на {weather['date']}",
        font=get_font(23),
        fill="#DFEBFF"
    )

    # Основная карточка
    draw_card(image, 55, 260, 970, 320)

    draw = ImageDraw.Draw(image)

    draw.text(
        (s(95), s(290)),
        "СЕЙЧАС В ГОРОДЕ",
        font=get_font(20, True),
        fill="#8997AB"
    )

    draw_weather_icon(
        image,
        820,
        415,
        weather["current_code"],
        80
    )

    draw = ImageDraw.Draw(image)

    draw.text(
        (s(100), s(335)),
        f"{weather['current_temp']:+.0f}°",
        font=get_font(100, True),
        fill="#1B3152"
    )

    draw.text(
        (s(105), s(465)),
        WEATHER_CODES.get(
            weather["current_code"],
            "Переменная погода"
        ),
        font=get_font(24),
        fill="#66758C"
    )

    # Ощущается как
    draw.text(
        (s(650), s(485)),
        f"Ощущается как {weather['feels_like']:+.0f}°",
        font=get_font(20, True),
        fill="#52647E"
    )

    # Показатели
    draw_card(image, 55, 610, 970, 125)

    draw = ImageDraw.Draw(image)

    indicators = [
        (
            "ВЛАЖНОСТЬ",
            f"{weather['humidity']}%"
        ),
        (
            "ВЕТЕР",
            f"{weather['current_wind']} км/ч"
        ),
        (
            "ОСАДКИ",
            f"{weather['rain_probability']}%"
        ),
    ]

    indicator_x = [115, 425, 730]

    for (title, value), x in zip(
        indicators,
        indicator_x
    ):

        draw.text(
            (s(x), s(635)),
            title,
            font=get_font(16, True),
            fill="#8C9AAF"
        )

        draw.text(
            (s(x), s(675)),
            value,
            font=get_font(27, True),
            fill="#203654"
        )

    # Прогноз на завтра
    draw_card(image, 55, 765, 970, 205)

    draw = ImageDraw.Draw(image)

    draw.text(
        (s(90), s(790)),
        "ПРОГНОЗ НА ЗАВТРА",
        font=get_font(20, True),
        fill="#8997AB"
    )

    draw_weather_icon(
        image,
        175,
        885,
        weather["code"],
        55
    )

    draw = ImageDraw.Draw(image)

    draw.text(
        (s(250), s(840)),
        weather["description"],
        font=get_font(24, True),
        fill="#243957"
    )

    draw.text(
        (s(250), s(890)),
        f"Минимум {weather['min']:+.0f}°",
        font=get_font(21),
        fill="#718097"
    )

    draw.text(
        (s(580), s(875)),
        f"{weather['max']:+.0f}°",
        font=get_font(50, True),
        fill="#2878E8"
    )

    draw.text(
        (s(790), s(895)),
        f"{weather['min']:+.0f}°",
        font=get_font(27, True),
        fill="#8D9AAD"
    )

    # Почасовой прогноз
    draw_card(image, 55, 1000, 970, 180)

    draw = ImageDraw.Draw(image)

    draw.text(
        (s(90), s(1020)),
        "ПОЧАСОВОЙ ПРОГНОЗ",
        font=get_font(19, True),
        fill="#8997AB"
    )

    if weather["hourly"]:

        positions = [180, 405, 630, 855]

        for item, x in zip(
            weather["hourly"],
            positions
        ):

            draw.text(
                (s(x-30), s(1060)),
                item["time"],
                font=get_font(20, True),
                fill="#52647E"
            )

            draw_weather_icon(
                image,
                x,
                1120,
                item["code"],
                28
            )

            draw = ImageDraw.Draw(image)

            draw.text(
                (s(x-35), s(1150)),
                f"{item['temperature']:+.0f}°",
                font=get_font(25, True),
                fill="#243957"
            )

    # Восход и закат
    draw = ImageDraw.Draw(image)

    draw.text(
        (s(80), s(1205)),
        f"Восход  {weather['sunrise']}",
        font=get_font(20, True),
        fill="#FFFFFF"
    )

    draw.text(
        (s(570), s(1205)),
        f"Закат  {weather['sunset']}",
        font=get_font(20, True),
        fill="#FFFFFF"
    )

    # Рекомендация
    recommendation = get_recommendation(weather)

    draw.text(
        (s(80), s(1260)),
        recommendation,
        font=get_font(19, True),
        fill="#E6F1FF"
    )

    # Финальное изображение
    image = image.convert("RGB")

    image = image.resize(
        (WIDTH, HEIGHT),
        Image.Resampling.LANCZOS
    )

    image.save(
        OUTPUT_PATH,
        format="PNG",
        optimize=True
    )

    print("Погодная карточка успешно создана!")

    return str(OUTPUT_PATH)


# =====================================================
# ОТПРАВКА В TELEGRAM
# =====================================================

def send_weather_photo(image_path):

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendPhoto"
    )

    with open(image_path, "rb") as photo:

        response = requests.post(
            url,
            data={
                "chat_id": GROUP_CHAT_ID
            },
            files={
                "photo": photo
            },
            timeout=60
        )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Ошибка Telegram: {result}"
        )


# =====================================================
# ЗАПУСК
# =====================================================

def main():

    if not BOT_TOKEN or not GROUP_CHAT_ID:
        raise RuntimeError(
            "Не найдены BOT_TOKEN или GROUP_CHAT_ID"
        )

    weather = get_weather()

    image_path = create_weather_card(weather)

    send_weather_photo(image_path)

    print(
        "Погодная карточка успешно отправлена!"
    )


if __name__ == "__main__":
    main()
