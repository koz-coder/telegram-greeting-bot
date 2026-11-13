import os
import math
import random
import requests

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ==================================================
# НАСТРОЙКИ
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

TIMEZONE = ZoneInfo("Asia/Tashkent")

LAT = 41.2995
LON = 69.2401

W = 1080
H = 1350

SCALE = 2
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
    57: "Ледяная морось",
    61: "Небольшой дождь",
    63: "Дождь",
    65: "Сильный дождь",
    66: "Ледяной дождь",
    67: "Ледяной дождь",
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


# ==================================================
# ШРИФТЫ
# ==================================================

def font(size, bold=False):
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


# ==================================================
# ПОЛУЧЕНИЕ ПРОГНОЗА
# ==================================================

def get_weather():

    tomorrow = datetime.now(TIMEZONE).date() + timedelta(days=1)

    params = {
        "latitude": LAT,
        "longitude": LON,
        "current": (
            "temperature_2m,apparent_temperature,"
            "relative_humidity_2m,weather_code,"
            "wind_speed_10m"
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

    response = requests.get(
        API_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    daily = data["daily"]

    index = daily["time"].index(tomorrow.isoformat())

    hourly = data["hourly"]

    hours = []

    for hour in [9, 12, 15, 18]:

        target = f"{tomorrow.isoformat()}T{hour:02d}:00"

        try:
            i = hourly["time"].index(target)
            temp = hourly["temperature_2m"][i]
            code = hourly["weather_code"][i]
        except (ValueError, IndexError):
            temp = None
            code = None

        hours.append({
            "hour": hour,
            "temp": temp,
            "code": code
        })

    current = data["current"]

    return {
        "date": tomorrow,
        "current_temp": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "wind": current["wind_speed_10m"],
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


# ==================================================
# ОПРЕДЕЛЕНИЕ ТИПА ПОГОДЫ
# ==================================================

def get_effect(code):

    if code in [95, 96, 99]:
        return "storm"

    if code in [71, 73, 75, 77, 85, 86]:
        return "snow"

    if code in [
        51, 53, 55, 56, 57,
        61, 63, 65, 66, 67,
        80, 81, 82
    ]:
        return "rain"

    if code in [2, 3, 45, 48]:
        return "cloud"

    return "sun"


# ==================================================
# ФОН
# ==================================================

def create_background():

    image = Image.new("RGB", (W, H))
    pixels = image.load()

    for y in range(H):

        t = y / H

        r = int(12 + t * 25)
        g = int(24 + t * 25)
        b = int(67 + t * 48)

        for x in range(W):
            pixels[x, y] = (r, g, b)

    return image.convert("RGBA")


# ==================================================
# СТЕКЛЯННЫЕ БЛОКИ
# ==================================================

def glass_card(draw, box, radius=30):

    draw.rounded_rectangle(
        box,
        radius=radius,
        fill=(255, 255, 255, 25),
        outline=(255, 255, 255, 55),
        width=2
    )


# ==================================================
# ИКОНКИ ПОГОДЫ
# ==================================================

def draw_sun(draw, x, y, radius):

    draw.ellipse(
        (
            x-radius-18,
            y-radius-18,
            x+radius+18,
            y+radius+18
        ),
        fill=(255, 205, 105, 35)
    )

    draw.ellipse(
        (
            x-radius,
            y-radius,
            x+radius,
            y+radius
        ),
        fill=(255, 211, 112, 255)
    )

    for angle in range(0, 360, 45):

        rad = math.radians(angle)

        x1 = x + math.cos(rad) * (radius + 20)
        y1 = y + math.sin(rad) * (radius + 20)

        x2 = x + math.cos(rad) * (radius + 42)
        y2 = y + math.sin(rad) * (radius + 42)

        draw.line(
            (x1, y1, x2, y2),
            fill=(255, 220, 150, 230),
            width=7
        )


def draw_cloud(draw, x, y, scale=1):

    color = (220, 231, 247, 220)

    draw.ellipse(
        (x, y+35*scale, x+150*scale, y+115*scale),
        fill=color
    )

    draw.ellipse(
        (x+45*scale, y, x+135*scale, y+100*scale),
        fill=color
    )

    draw.ellipse(
        (x+95*scale, y+25*scale, x+190*scale, y+110*scale),
        fill=color
    )


# ==================================================
# ОСНОВНОЙ ДИЗАЙН
# ==================================================

def create_card(weather):

    image = create_background()

    draw = ImageDraw.Draw(image, "RGBA")

    title = font(42, True)
    big = font(150)
    medium = font(38, True)
    normal = font(29)
    small = font(24)

    effect = get_effect(weather["code"])

    # Заголовок

    draw.text(
        (65, 55),
        "ПОГОДА В ТАШКЕНТЕ",
        font=title,
        fill="white"
    )

    draw.text(
        (68, 115),
        f"Прогноз на {weather['date'].strftime('%d.%m.%Y')}",
        font=small,
        fill=(190, 207, 235)
    )

    # Главная погодная иконка

    if effect == "sun":
        draw_sun(draw, 820, 310, 65)

    elif effect == "cloud":
        draw_cloud(draw, 740, 230, 1.3)

    elif effect in ["rain", "storm"]:
        draw_cloud(draw, 740, 230, 1.3)

    elif effect == "snow":
        draw_cloud(draw, 740, 230, 1.3)

    # Температура

    draw.text(
        (65, 205),
        f"{weather['current_temp']:.0f}°",
        font=big,
        fill="white"
    )

    draw.text(
        (75, 390),
        "Сейчас в Ташкенте",
        font=normal,
        fill=(210, 222, 242)
    )

    draw.text(
        (75, 445),
        f"Ощущается как {weather['feels_like']:.0f}°",
        font=small,
        fill=(190, 207, 235)
    )

    # Прогноз на завтра

    glass_card(draw, (50, 545, 1030, 795))

    description = WEATHER_CODES.get(
        weather["code"],
        "Переменная погода"
    )

    draw.text(
        (90, 580),
        "ЗАВТРА",
        font=small,
        fill=(190, 210, 240)
    )

    draw.text(
        (90, 635),
        description,
        font=medium,
        fill="white"
    )

    draw.text(
        (90, 710),
        f"Максимум  {weather['max']:.0f}°",
        font=normal,
        fill="white"
    )

    draw.text(
        (570, 710),
        f"Минимум  {weather['min']:.0f}°",
        font=normal,
        fill="white"
    )

    # Показатели

    glass_card(draw, (50, 825, 1030, 1035))

    draw.text(
        (90, 865),
        "ВЛАЖНОСТЬ",
        font=small,
        fill=(185, 205, 235)
    )

    draw.text(
        (90, 920),
        f"{weather['humidity']}%",
        font=medium,
        fill="white"
    )

    draw.text(
        (390, 865),
        "ВЕТЕР",
        font=small,
        fill=(185, 205, 235)
    )

    draw.text(
        (390, 920),
        f"{weather['wind']:.0f} км/ч",
        font=medium,
        fill="white"
    )

    draw.text(
        (710, 865),
        "ОСАДКИ",
        font=small,
        fill=(185, 205, 235)
    )

    draw.text(
        (710, 920),
        f"{weather['rain']}%",
        font=medium,
        fill="white"
    )

    # Почасовой прогноз

    draw.text(
        (65, 1065),
        "ПРОГНОЗ ПО ЧАСАМ",
        font=small,
        fill=(190, 210, 240)
    )

    positions = [90, 330, 570, 810]

    for x, item in zip(positions, weather["hours"]):

        draw.text(
            (x, 1115),
            f"{item['hour']:02d}:00",
            font=small,
            fill=(190, 210, 240)
        )

        temp = (
            "—"
            if item["temp"] is None
            else f"{item['temp']:.0f}°"
        )

        draw.text(
            (x, 1165),
            temp,
            font=medium,
            fill="white"
        )

    # Восход и закат

    draw.text(
        (65, 1260),
        f"ВОСХОД  {weather['sunrise']}",
        font=small,
        fill=(190, 210, 240)
    )

    draw.text(
        (580, 1260),
        f"ЗАКАТ  {weather['sunset']}",
        font=small,
        fill=(190, 210, 240)
    )

    return image


# ==================================================
# АНИМАЦИЯ ДОЖДЯ
# ==================================================

def add_rain(frame, phase, intensity=1):

    draw = ImageDraw.Draw(frame, "RGBA")

    random.seed(123)

    count = 180 if intensity == 1 else 300

    for i in range(count):

        x = random.randint(0, W)
        start_y = random.randint(-H, H)

        speed = random.randint(25, 42)

        y = (start_y + phase * speed) % H

        length = random.randint(22, 42)

        draw.line(
            (x, y, x-12, y+length),
            fill=(185, 220, 255, 135),
            width=3
        )

    return frame


# ==================================================
# АНИМАЦИЯ СНЕГА
# ==================================================

def add_snow(frame, phase):

    draw = ImageDraw.Draw(frame, "RGBA")

    random.seed(456)

    for i in range(150):

        x = random.randint(0, W)
        start_y = random.randint(-H, H)

        speed = random.randint(8, 18)

        y = (start_y + phase * speed) % H

        drift = int(math.sin((phase+i)/4) * 18)

        radius = random.randint(3, 7)

        draw.ellipse(
            (
                x+drift-radius,
                y-radius,
                x+drift+radius,
                y+radius
            ),
            fill=(255, 255, 255, 210)
        )

    return frame


# ==================================================
# АНИМАЦИЯ ОБЛАКОВ
# ==================================================

def add_moving_clouds(frame, phase):

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay, "RGBA")

    for i in range(5):

        x = ((i*260 + phase*12) % (W+300)) - 150
        y = 170 + i*65

        draw_cloud(draw, x, y, 0.9)

    frame.alpha_composite(overlay)

    return frame


# ==================================================
# СОЛНЦЕ
# ==================================================

def add_sun_animation(frame, phase):

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    draw = ImageDraw.Draw(overlay)

    pulse = int(15 + 12*math.sin(phase/3))

    draw.ellipse(
        (
            750-pulse,
            240-pulse,
            900+pulse,
            390+pulse
        ),
        fill=(255, 205, 100, 40)
    )

    overlay = overlay.filter(
        ImageFilter.GaussianBlur(35)
    )

    frame.alpha_composite(overlay)

    return frame


# ==================================================
# СОЗДАНИЕ GIF
# ==================================================

def create_animation(weather):

    base = create_card(weather)

    effect = get_effect(weather["code"])

    frames = []

    strong = weather["code"] in [
        65, 67, 75, 82, 86, 95, 96, 99
    ]

    for phase in range(FRAMES):

        frame = base.copy()

        if effect in ["rain", "storm"]:

            add_rain(
                frame,
                phase,
                2 if strong else 1
            )

        elif effect == "snow":

            add_snow(frame, phase)

        elif effect == "cloud":

            add_moving_clouds(frame, phase)

        elif effect == "sun":

            add_sun_animation(frame, phase)

        if effect == "storm" and phase % 8 in [0, 1]:

            flash = Image.new(
                "RGBA",
                (W, H),
                (255, 255, 255, 35)
            )

            frame.alpha_composite(flash)

        frames.append(
            frame.convert("RGB").quantize(
                colors=256,
                method=Image.Quantize.MEDIANCUT
            )
        )

    frames[0].save(
        OUTPUT_FILE,
        save_all=True,
        append_images=frames[1:],
        duration=DURATION,
        loop=0,
        optimize=True
    )

    print("GIF успешно создан:", OUTPUT_FILE)

    return OUTPUT_FILE


# ==================================================
# ОТПРАВКА В TELEGRAM
# ==================================================

def send_weather_animation(path):

    if not BOT_TOKEN or not GROUP_CHAT_ID:
        raise ValueError(
            "Не найдены BOT_TOKEN или GROUP_CHAT_ID"
        )

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendAnimation"
    )

    with open(path, "rb") as animation:

        response = requests.post(
            url,
            data={"chat_id": GROUP_CHAT_ID},
            files={"animation": animation},
            timeout=120
        )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(result)

    print("Погодная GIF успешно отправлена!")


# ==================================================
# ЗАПУСК
# ==================================================

def main():

    print("Получаем прогноз...")

    weather = get_weather()

    print("Создаём качественную анимацию...")

    animation = create_animation(weather)

    print("Отправляем в Telegram...")

    send_weather_animation(animation)


if __name__ == "__main__":
    main()
