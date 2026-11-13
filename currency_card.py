import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from zoneinfo import ZoneInfo

WIDTH = 1200
HEIGHT = 675

CBU_URL = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"

CURRENCIES = {
    "USD": ("Доллар США", "#2588F5", "US"),
    "EUR": ("Евро", "#7858EA", "EU"),
    "RUB": ("Российский рубль", "#E94B72", "RU"),
    "TRY": ("Турецкая лира", "#12A985", "TR"),
}


def get_font(size, bold=False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]

    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass

    return ImageFont.load_default()


def gradient_background():
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()

    top = (24, 117, 235)
    bottom = (117, 67, 220)

    for y in range(HEIGHT):
        ratio = y / HEIGHT

        color = tuple(
            int(top[i] * (1 - ratio) + bottom[i] * ratio)
            for i in range(3)
        )

        for x in range(WIDTH):
            pixels[x, y] = color

    return image


def draw_flag(draw, x, y, code):
    radius = 27

    draw.ellipse(
        (x - radius, y - radius, x + radius, y + radius),
        fill="white"
    )

    if code == "US":
        draw.ellipse(
            (x - 21, y - 21, x + 21, y + 21),
            fill="#E74C3C"
        )

        for offset in [-13, -3, 7, 17]:
            draw.rectangle(
                (x - 20, y + offset - 2, x + 20, y + offset + 2),
                fill="white"
            )

        draw.rectangle(
            (x - 20, y - 20, x - 1, y + 2),
            fill="#2453A6"
        )

    elif code == "EU":
        draw.ellipse(
            (x - 21, y - 21, x + 21, y + 21),
            fill="#2352B5"
        )

        for angle in range(0, 360, 45):
            import math

            px = x + int(12 * math.cos(math.radians(angle)))
            py = y + int(12 * math.sin(math.radians(angle)))

            draw.ellipse(
                (px - 2, py - 2, px + 2, py + 2),
                fill="#FFD447"
            )

    elif code == "RU":
        draw.ellipse(
            (x - 21, y - 21, x + 21, y + 21),
            fill="#E74C3C"
        )

        draw.rectangle(
            (x - 21, y - 21, x + 21, y - 7),
            fill="white"
        )

        draw.rectangle(
            (x - 21, y - 7, x + 21, y + 7),
            fill="#3978DB"
        )

    elif code == "TR":
        draw.ellipse(
            (x - 21, y - 21, x + 21, y + 21),
            fill="#E84152"
        )

        draw.ellipse(
            (x - 8, y - 9, x + 12, y + 11),
            fill="white"
        )

        draw.ellipse(
            (x - 3, y - 9, x + 17, y + 11),
            fill="#E84152"
        )


def draw_card(image, position, currency, rate):
    x, y = position

    name, accent, flag = CURRENCIES[currency]

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)

    shadow_draw.rounded_rectangle(
        (x + 5, y + 9, x + 525, y + 184),
        radius=28,
        fill=(15, 25, 65, 90)
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    image.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(image)

    # Белая карточка
    draw.rounded_rectangle(
        (x, y, x + 520, y + 175),
        radius=27,
        fill="#FFFFFF"
    )

    # Цветная боковая полоса
    draw.rounded_rectangle(
        (x, y, x + 13, y + 175),
        radius=6,
        fill=accent
    )

    # Флаг
    draw_flag(draw, x + 65, y + 65, flag)

    # Код валюты
    draw.text(
        (x + 110, y + 32),
        currency,
        font=get_font(34, True),
        fill="#182B50"
    )

    # Название
    draw.text(
        (x + 110, y + 82),
        name,
        font=get_font(19),
        fill="#71809A"
    )

    # Курс
    rate_text = f"{rate:,.2f}".replace(",", " ")

    draw.text(
        (x + 110, y + 125),
        rate_text + " UZS",
        font=get_font(29, True),
        fill=accent
    )

    # Декоративный круг
    draw.ellipse(
        (x + 455, y + 28, x + 495, y + 68),
        fill=accent
    )

    draw.text(
        (x + 466, y + 34),
        "✓",
        font=get_font(24, True),
        fill="white"
    )


def get_currency_rates():
    response = requests.get(CBU_URL, timeout=20)
    response.raise_for_status()

    data = response.json()

    rates = {}
    actual_date = None

    for item in data:
        code = item.get("Ccy")

        if code in CURRENCIES:
            rates[code] = float(item["Rate"])
            actual_date = item.get("Date")

    missing = set(CURRENCIES) - set(rates)

    if missing:
        raise ValueError(
            f"Не найдены валюты: {', '.join(sorted(missing))}"
        )

    return rates, actual_date


def create_currency_card():
    rates, actual_date = get_currency_rates()

    image = gradient_background()
    draw = ImageDraw.Draw(image)

    # Декоративные элементы
    draw.ellipse(
        (930, -170, 1320, 220),
        fill="#3B9CF7"
    )

    draw.ellipse(
        (-160, 430, 240, 830),
        fill="#5C53DD"
    )

    draw.text(
        (65, 35),
        "ФИНАНСЫ УЗБЕКИСТАНА",
        font=get_font(23, True),
        fill="#D9EEFF"
    )

    draw.text(
        (65, 78),
        "Курсы валют",
        font=get_font(58, True),
        fill="white"
    )

    draw.text(
        (70, 150),
        "Актуальные официальные курсы",
        font=get_font(22),
        fill="#E0E9FF"
    )

    # Дата курса
    date_text = actual_date or datetime.now(
        ZoneInfo("Asia/Tashkent")
    ).strftime("%d.%m.%Y")

    draw.rounded_rectangle(
        (880, 65, 1135, 125),
        radius=25,
        fill="#FFFFFF"
    )

    draw.text(
        (915, 82),
        f"Дата: {date_text}",
        font=get_font(20, True),
        fill="#34466B"
    )

    # Карточки валют
    positions = [
        (65, 225),
        (615, 225),
        (65, 425),
        (615, 425)
    ]

    for (currency, rate), position in zip(
        rates.items(),
        positions
    ):
        draw_card(image, position, currency, rate)

    # Нижняя подпись
    draw = ImageDraw.Draw(image)

    draw.text(
        (65, 635),
        "Официальный источник: Центральный банк Республики Узбекистан",
        font=get_font(17),
        fill="#FFFFFF"
    )

    output_path = "currency_card.png"

    image.save(output_path, quality=95)

    print("Яркая карточка курсов валют создана!")

    return output_path


if __name__ == "__main__":
    create_currency_card()
