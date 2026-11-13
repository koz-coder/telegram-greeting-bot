import os
import math
import random
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============================================================
# TASHKENT WEATHER — premium animated Telegram card
# Canvas: 1080x1350. Data: Open-Meteo. Output: animated GIF.
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")
TZ = ZoneInfo("Asia/Tashkent")

LATITUDE = 41.2995
LONGITUDE = 69.2401
WIDTH, HEIGHT = 1080, 1350
FRAME_COUNT = 24
FRAME_DURATION_MS = 100
OUTPUT_FILE = "weather_animation.gif"
API_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_NAMES = {
    0: "Ясно", 1: "Преимущественно ясно",
    2: "Переменная облачность", 3: "Облачно",
    45: "Туман", 48: "Изморозевый туман",
    51: "Небольшая морось", 53: "Морось", 55: "Сильная морось",
    56: "Ледяная морось", 57: "Сильная ледяная морось",
    61: "Небольшой дождь", 63: "Дождь", 65: "Сильный дождь",
    66: "Ледяной дождь", 67: "Сильный ледяной дождь",
    71: "Небольшой снег", 73: "Снег", 75: "Сильный снег",
    77: "Снежная крупа", 80: "Ливень", 81: "Сильный ливень",
    82: "Очень сильный ливень", 85: "Снегопад", 86: "Сильный снегопад",
    95: "Гроза", 96: "Гроза с градом", 99: "Сильная гроза"
}

def load_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    ]
    for path in paths:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def get_weather():
    tomorrow = datetime.now(TZ).date() + timedelta(days=1)
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m",
        "hourly": "temperature_2m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum,wind_speed_10m_max,sunrise,sunset",
        "timezone": "Asia/Tashkent",
        "forecast_days": 2
    }
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()

    daily = data["daily"]
    day_index = daily["time"].index(tomorrow.isoformat())
    hourly = data["hourly"]

    hours = []
    for hour in (9, 12, 15, 18):
        stamp = f"{tomorrow.isoformat()}T{hour:02d}:00"
        try:
            i = hourly["time"].index(stamp)
            temp = hourly["temperature_2m"][i]
            code = hourly["weather_code"][i]
        except (ValueError, IndexError):
            temp, code = None, None
        hours.append({"hour": hour, "temp": temp, "code": code})

    current = data["current"]
    return {
        "date": tomorrow,
        "current_temp": current["temperature_2m"],
        "feels_like": current["apparent_temperature"],
        "humidity": current["relative_humidity_2m"],
        "current_code": current["weather_code"],
        "wind": current["wind_speed_10m"],
        "max": daily["temperature_2m_max"][day_index],
        "min": daily["temperature_2m_min"][day_index],
        "code": daily["weather_code"][day_index],
        "rain": daily["precipitation_probability_max"][day_index] or 0,
        "precipitation": daily["precipitation_sum"][day_index] or 0,
        "max_wind": daily["wind_speed_10m_max"][day_index],
        "sunrise": daily["sunrise"][day_index][-5:],
        "sunset": daily["sunset"][day_index][-5:],
        "hours": hours
    }

def weather_effect(code):
    if code in (95, 96, 99):
        return "storm"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82):
        return "rain"
    if code in (2, 3, 45, 48):
        return "cloud"
    return "sun"

def gradient_background(effect):
    palettes = {
        "sun": ((25, 67, 119), (31, 48, 91)),
        "cloud": ((44, 77, 119), (25, 47, 91)),
        "rain": ((17, 43, 79), (13, 31, 69)),
        "storm": ((12, 28, 58), (9, 20, 49)),
        "snow": ((70, 101, 142), (29, 53, 94))
    }
    top, bottom = palettes[effect]
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pix = image.load()
    for y in range(HEIGHT):
        t = y / (HEIGHT - 1)
        row = tuple(round(top[c] * (1 - t) + bottom[c] * t) for c in range(3))
        for x in range(WIDTH):
            pix[x, y] = row
    return image.convert("RGBA")

def add_atmosphere(image, effect):
    # Soft atmospheric glow behind the skyline.
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    if effect == "sun":
        gd.ellipse((460, 80, 1160, 760), fill=(255, 163, 91, 100))
    elif effect == "snow":
        gd.ellipse((360, 100, 1100, 760), fill=(188, 215, 245, 65))
    else:
        gd.ellipse((480, 100, 1160, 760), fill=(113, 159, 213, 58))
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(125)))

    # Soft cloud banks.
    cloud_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    cd = ImageDraw.Draw(cloud_layer)
    random.seed(31)
    for band in range(3):
        y0 = 280 + band * 90
        for i in range(8):
            x = i * 160 - 80 + random.randint(-35, 35)
            y = y0 + random.randint(-25, 25)
            alpha = 24 + band * 9
            color = (178, 202, 232, alpha)
            cd.ellipse((x, y, x + 230, y + 82), fill=color)
            cd.ellipse((x + 40, y - 42, x + 165, y + 95), fill=color)
    image.alpha_composite(cloud_layer.filter(ImageFilter.GaussianBlur(32)))

def add_tashkent_skyline(image):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    random.seed(10)

    # Distant buildings and warm windows.
    for x in range(-15, WIDTH + 25, 43):
        bw = random.randint(25, 43)
        bh = random.randint(38, 102)
        y = 575 - bh
        d.rectangle((x, y, x + bw, 590), fill=(9, 25, 48, 190))
        for wy in range(y + 12, 580, 18):
            for wx in range(x + 7, x + bw - 4, 12):
                d.rectangle((wx, wy, wx + 4, wy + 6), fill=(255, 205, 126, 95))

    # Tree silhouettes along the horizon.
    for x in range(-20, WIDTH + 30, 31):
        crown_y = random.randint(525, 575)
        d.line((x + 12, 600, x + 12, crown_y + 20), fill=(12, 38, 39, 240), width=8)
        d.ellipse((x - 10, crown_y - 12, x + 34, crown_y + 38), fill=(13, 48, 43, 240))

    # Stylized Tashkent TV tower on the right.
    tx = 925
    d.line((tx, 565, tx, 75), fill=(16, 30, 51, 255), width=9)
    d.polygon([(tx - 25, 565), (tx + 25, 565), (tx + 10, 270), (tx - 10, 270)],
              fill=(31, 48, 70, 255))
    d.rectangle((tx - 30, 250, tx + 30, 283), fill=(42, 59, 81, 255))
    d.rectangle((tx - 22, 207, tx + 22, 227), fill=(42, 59, 81, 255))
    d.line((tx, 207, tx, 16), fill=(20, 34, 56, 255), width=5)
    d.ellipse((tx - 5, 9, tx + 5, 19), fill=(225, 235, 248, 255))
    image.alpha_composite(layer)

    shade = Image.new("RGBA", image.size, (0, 0, 0, 0))
    ImageDraw.Draw(shade).rectangle((0, 500, WIDTH, HEIGHT), fill=(7, 22, 49, 65))
    image.alpha_composite(shade)

def draw_cloud(image, x, y, scale=1.0, alpha=245):
    layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # Soft shadow and layered cloud lobes.
    d.ellipse((x, y + 48*scale, x + 220*scale, y + 135*scale),
              fill=(10, 26, 53, 75))
    col = (232, 241, 252, alpha)
    d.ellipse((x + 5*scale, y + 35*scale, x + 125*scale, y + 135*scale), fill=col)
    d.ellipse((x + 55*scale, y, x + 170*scale, y + 135*scale), fill=col)
    d.ellipse((x + 120*scale, y + 35*scale, x + 245*scale, y + 140*scale), fill=col)
    image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.4)))

def draw_sun(image, cx, cy, radius=55):
    glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((cx-radius-38, cy-radius-38, cx+radius+38, cy+radius+38),
               fill=(255, 194, 76, 120))
    image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(35)))
    d = ImageDraw.Draw(image)
    d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius),
              fill=(255, 207, 91, 255), outline=(255, 244, 198, 235), width=4)

def draw_icon(image, code, x, y, scale=1.0):
    effect = weather_effect(code if code is not None else 2)
    if effect == "sun":
        draw_sun(image, int(x + 55*scale), int(y + 55*scale), int(34*scale))
    elif effect == "cloud":
        draw_cloud(image, x, y + 10*scale, 0.78*scale)
    elif effect in ("rain", "storm"):
        draw_cloud(image, x, y, 0.78*scale)
        d = ImageDraw.Draw(image, "RGBA")
        for i in range(4):
            xx = x + (40 + i*38)*scale
            d.line((xx, y+104*scale, xx-11*scale, y+136*scale),
                   fill=(153, 211, 255, 235), width=max(3, int(5*scale)))
    elif effect == "snow":
        draw_cloud(image, x, y, 0.78*scale)
        d = ImageDraw.Draw(image, "RGBA")
        for i in range(4):
            xx = x + (40 + i*38)*scale
            yy = y + 133*scale
            r = 5*scale
            d.ellipse((xx-r, yy-r, xx+r, yy+r), fill=(255, 255, 255, 245))

def panel(image, box, radius=32):
    # True translucent glass: draw on RGBA overlay, then composite once.
    x1, y1, x2, y2 = box
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle((x1+2, y1+9, x2+2, y2+12), radius=radius,
                         fill=(0, 0, 0, 58))
    image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))

    glass = Image.new("RGBA", image.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glass)
    gd.rounded_rectangle(box, radius=radius,
                         fill=(33, 70, 119, 155),
                         outline=(226, 239, 255, 190), width=3)
    # Subtle top sheen.
    gd.line((x1+35, y1+3, x2-35, y1+3), fill=(255, 255, 255, 70), width=2)
    image.alpha_composite(glass)

def draw_card(weather):
    effect = weather_effect(weather["code"])
    image = gradient_background(effect)
    add_atmosphere(image, effect)
    add_tashkent_skyline(image)

    white = (255, 255, 255, 255)
    muted = (216, 230, 250, 255)
    d = ImageDraw.Draw(image, "RGBA")
    title = load_font(47, True)
    body = load_font(31)
    section = load_font(38, True)
    small = load_font(25)
    big = load_font(190)

    # Header.
    d.ellipse((64, 54, 96, 86), outline=white, width=5)
    d.ellipse((75, 65, 85, 75), fill=white)
    d.text((120, 42), "Погода в Ташкенте", font=title, fill=white)
    d.rounded_rectangle((65, 113, 96, 144), radius=5, outline=muted, width=4)
    d.text((120, 107), f"Прогноз на {weather['date'].strftime('%d.%m.%Y')}",
           font=body, fill=white)

    # Hero temperature and weather art.
    draw_icon(image, weather["current_code"], 600, 190, 1.55)
    d = ImageDraw.Draw(image, "RGBA")
    d.text((65, 165), f"{weather['current_temp']:.0f}°", font=big, fill=white)
    d.text((80, 370), "Сейчас в Ташкенте", font=load_font(39), fill=white)
    d.text((80, 427), f"Ощущается как {weather['feels_like']:.0f}°",
           font=body, fill=muted)

    # Tomorrow summary.
    panel(image, (50, 510, 1030, 665))
    d = ImageDraw.Draw(image, "RGBA")
    d.text((95, 535), "Завтра", font=section, fill=white)
    draw_icon(image, weather["code"], 210, 565, 0.72)
    d = ImageDraw.Draw(image, "RGBA")
    d.line((395, 535, 395, 640), fill=(235, 244, 255, 180), width=2)
    description = WEATHER_NAMES.get(weather["code"], "Переменная облачность")
    # Fit long weather description into the center column.
    desc_font = load_font(34 if len(description) < 20 else 29, True)
    d.text((430, 555), description, font=desc_font, fill=white)
    d.line((795, 535, 795, 640), fill=(235, 244, 255, 180), width=2)
    d.text((830, 540), f"↑ {weather['max']:+.0f}°", font=section, fill=white)
    d.text((830, 590), f"↓ {weather['min']:+.0f}°", font=section, fill=white)

    # Humidity / wind / precipitation.
    panel(image, (50, 690, 1030, 840))
    d = ImageDraw.Draw(image, "RGBA")
    d.line((382, 715, 382, 815), fill=(235, 244, 255, 160), width=2)
    d.line((710, 715, 710, 815), fill=(235, 244, 255, 160), width=2)
    # Droplet icon.
    d.ellipse((103, 727, 137, 775), outline=white, width=4)
    d.polygon([(120, 715), (106, 744), (134, 744)], fill=white)
    d.text((153, 720), "Влажность", font=body, fill=white)
    d.text((153, 770), f"{weather['humidity']}%", font=section, fill=white)
    # Wind icon.
    for yy, length in ((730, 62), (750, 48), (770, 60)):
        d.arc((418, yy, 418+length, yy+22), 190, 345, fill=white, width=4)
    d.text((500, 720), "Ветер", font=body, fill=white)
    d.text((500, 770), f"{weather['wind']:.0f} км/ч", font=section, fill=white)
    # Rain cloud icon.
    d.ellipse((748, 735, 785, 770), outline=white, width=4)
    d.ellipse((770, 722, 810, 770), outline=white, width=4)
    d.ellipse((795, 738, 826, 770), outline=white, width=4)
    d.line((765, 770, 760, 785), fill=(170, 220, 255, 255), width=4)
    d.line((790, 770, 785, 785), fill=(170, 220, 255, 255), width=4)
    d.text((845, 720), "Осадки", font=body, fill=white)
    d.text((845, 770), f"{weather['rain']}%", font=section, fill=white)

    # Hourly forecast.
    d.text((80, 870), "◷  Прогноз по часам", font=section, fill=white)
    panel(image, (50, 925, 1030, 1175))
    d = ImageDraw.Draw(image, "RGBA")
    columns = [175, 420, 665, 910]
    for index, (x, item) in enumerate(zip(columns, weather["hours"])):
        if index:
            divider_x = 297 + (index-1)*245
            d.line((divider_x, 955, divider_x, 1145),
                   fill=(235, 244, 255, 155), width=2)
        d.text((x-55, 950), f"{item['hour']:02d}:00",
               font=body, fill=white)
        draw_icon(image, item["code"], x-62, 1000, 0.55)
        d = ImageDraw.Draw(image, "RGBA")
        temp_text = "—" if item["temp"] is None else f"{item['temp']:.0f}°"
        d.text((x-35, 1090), temp_text, font=section, fill=white)

    # Sunrise and sunset.
    panel(image, (50, 1200, 1030, 1315), radius=28)
    d = ImageDraw.Draw(image, "RGBA")
    # Sunrise icon.
    d.arc((112, 1230, 178, 1290), 180, 360, fill=(255, 205, 105, 255), width=5)
    d.line((105, 1270, 185, 1270), fill=(255, 205, 105, 255), width=5)
    d.text((210, 1235), "Восход", font=body, fill=white)
    d.text((355, 1230), weather["sunrise"], font=section, fill=white)
    d.line((540, 1220, 540, 1295), fill=(235, 244, 255, 160), width=2)
    # Sunset icon.
    d.arc((610, 1230, 676, 1290), 180, 360, fill=(255, 205, 105, 255), width=5)
    d.line((603, 1270, 683, 1270), fill=(255, 205, 105, 255), width=5)
    d.text((710, 1235), "Закат", font=body, fill=white)
    d.text((835, 1230), weather["sunset"], font=section, fill=white)

    return image

def animate_weather(base, weather):
    effect = weather_effect(weather["code"])
    frames = []
    random.seed(2026)

    # Fixed particle paths keep the animation smooth and looping.
    rain_particles = [
        (random.randint(0, WIDTH), random.randint(0, HEIGHT),
         random.randint(22, 42), random.randint(18, 34))
        for _ in range(260 if effect in ("rain", "storm") else 1)
    ]
    snow_particles = [
        (random.randint(0, WIDTH), random.randint(0, HEIGHT),
         random.randint(5, 15), random.randint(2, 6), random.random()*6.28)
        for _ in range(170 if effect == "snow" else 1)
    ]

    for frame_no in range(FRAME_COUNT):
        frame = base.copy()
        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay, "RGBA")

        if effect in ("rain", "storm"):
            count = len(rain_particles)
            for x, y0, length, speed in rain_particles:
                y = (y0 + frame_no*speed) % (HEIGHT + 80) - 40
                x2 = x - int(length*0.28)
                d.line((x, y, x2, y+length),
                       fill=(190, 222, 255, 125), width=3)
            if effect == "storm" and frame_no in (2, 3, 14):
                d.rectangle((0, 0, WIDTH, HEIGHT), fill=(255, 255, 255, 35))

        elif effect == "snow":
            for x, y0, speed, radius, phase in snow_particles:
                y = (y0 + frame_no*speed) % HEIGHT
                drift = int(math.sin(phase + frame_no*0.22)*24)
                d.ellipse((x+drift-radius, y-radius, x+drift+radius, y+radius),
                          fill=(255, 255, 255, 220))

        elif effect == "cloud":
            # Fine, translucent cloud wisps drift across the whole sky.
            for i in range(8):
                x = ((i*190 + frame_no*8) % (WIDTH+240)) - 120
                y = 180 + (i % 3)*95
                d.ellipse((x, y, x+210, y+48), fill=(224, 236, 250, 24))

        elif effect == "sun":
            pulse = int(8 + 7*math.sin(frame_no*math.pi/12))
            d.ellipse((730-pulse, 150-pulse, 930+pulse, 350+pulse),
                      fill=(255, 205, 105, 13))

        frame.alpha_composite(overlay)
        frames.append(frame.convert("RGB").quantize(
            colors=256, method=Image.Quantize.MEDIANCUT
        ))

    frames[0].save(
        OUTPUT_FILE,
        save_all=True,
        append_images=frames[1:],
        duration=FRAME_DURATION_MS,
        loop=0,
        optimize=True,
        disposal=2
    )
    return OUTPUT_FILE

def send_animation(path):
    if not BOT_TOKEN or not GROUP_CHAT_ID:
        raise RuntimeError("Не заданы GitHub Secrets BOT_TOKEN и GROUP_CHAT_ID")
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAnimation"
    with open(path, "rb") as animation:
        response = requests.post(
            url,
            data={"chat_id": GROUP_CHAT_ID},
            files={"animation": ("weather.gif", animation, "image/gif")},
            timeout=120
        )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API: {result}")
    print("Анимированная погодная карточка отправлена.")

def main():
    print("Получаем прогноз Open-Meteo...")
    weather = get_weather()
    print("Рисуем карточку...")
    base = draw_card(weather)
    print("Создаём GIF...")
    gif_path = animate_weather(base, weather)
    print("Отправляем GIF в Telegram...")
    send_animation(gif_path)

if __name__ == "__main__":
    main()
