import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
from zoneinfo import ZoneInfo

WIDTH, HEIGHT = 1080, 1350

CBU_URL = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"

CURRENCIES = {
    "USD": ("Доллар США", "#2878E8", "US"),
    "EUR": ("Евро", "#7655D9", "EU"),
    "RUB": ("Российский рубль", "#E64F78", "RU"),
    "TRY": ("Турецкая лира", "#12A88A", "TR"),
}


def get_font(size, bold=False):
    path = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    )
    return ImageFont.truetype(path, size)


def get_rates():
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
        raise ValueError(f"Не найдены валюты: {missing}")

    return rates, actual_date


def create_background():
    image = Image.new("RGB", (WIDTH, HEIGHT))
    pixels = image.load()

    top = (27, 111, 221)
    bottom = (103, 72, 197)

    for y in range(HEIGHT):
        t = y / HEIGHT
        color = tuple(
            int(top[i] * (1 - t) + bottom[i] * t)
            for i in range(3)
        )

        for x in range(WIDTH):
            pixels[x, y] = color

    return image


def draw_flag(draw, x, y, code):
    r = 37

    draw.ellipse(
        (x-r, y-r, x+r, y+r),
        fill="#F0F3FA"
    )

    if code == "US":
        draw.ellipse(
            (x-29, y-29, x+29, y+29),
            fill="#D94352"
        )
        for offset in [-18, -6, 6, 18]:
            draw.rectangle(
                (x-28, y+offset-3, x+28, y+offset+3),
                fill="white"
            )
        draw.rectangle(
            (x-28, y-28, x-2, y+4),
            fill="#2452A4"
        )

    elif code == "EU":
        draw.ellipse(
            (x-29, y-29, x+29, y+29),
            fill="#244BAA"
        )
        import math
        for angle in range(0, 360, 45):
            px = x + int(17 * math.cos(math.radians(angle)))
            py = y + int(17 * math.sin(math.radians(angle)))
            draw.ellipse(
                (px-3, py-3, px+3, py+3),
                fill="#FFD447"
            )

    elif code == "RU":
        draw.ellipse(
            (x-29, y-29, x+29, y+29),
            fill="#E94A54"
        )
        draw.rectangle(
            (x-29, y-29, x+29, y-10),
            fill="white"
        )
        draw.rectangle(
            (x-29, y-10, x+29, y+10),
            fill="#3977D8"
        )

    elif code == "TR":
        draw.ellipse(
            (x-29, y-29, x+29, y+29),
            fill="#E84152"
        )
        draw.ellipse(
            (x-12, y-12, x+17, y+17),
            fill="white"
        )
        draw.ellipse(
            (x-4, y-12, x+25, y+17),
            fill="#E84152"
        )


def draw_currency_card(image, code, rate, y):
    name, accent, flag = CURRENCIES[code]

    x = 75
    card_width = 930
    card_height = 205

    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)

    sd.rounded_rectangle(
        (x+5, y+12, x+card_width+5, y+card_height+12),
        radius=32,
        fill=(10, 20, 55, 95)
    )

    shadow = shadow.filter(ImageFilter.GaussianBlur(17))
    image.paste(shadow, (0, 0), shadow)

    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (x, y, x+card_width, y+card_height),
        radius=32,
        fill="white"
    )

    draw.rounded_rectangle(
        (x, y, x+17, y+card_height),
        radius=8,
        fill=accent
    )

    draw_flag(draw, x+100, y+100, flag)

    draw.text(
        (x+170, y+42),
        code,
        font=get_font(43, True),
        fill="#192B4A"
    )

    draw.text(
        (x+170, y+105),
        name,
        font=get_font(25),
        fill="#77839A"
    )

    rate_text = f"{rate:,.2f}".replace(",", " ")

    draw.text(
        (x+450, y+72),
        rate_text,
        font=get_font(45, True),
        fill=accent
    )

    draw.text(
        (x+450, y+132),
        "UZBEKISTAN SUM",
        font=get_font(17, True),
        fill="#8B95A8"
    )


def create_currency_card():
    rates, actual_date = get_rates()

    image = create_background()
    draw = ImageDraw.Draw(image)

    # Заголовок
    draw.text(
        (75, 85),
        "ФИНАНСЫ УЗБЕКИСТАНА",
        font=get_font(25, True),
        fill="#DCEBFF"
    )

    draw.text(
        (75, 140),
        "Курсы валют",
        font=get_font(72, True),
        fill="white"
    )

    draw.text(
        (80, 235),
        "Официальные курсы Центрального банка",
        font=get_font(25),
        fill="#E4EDFF"
    )

    # Дата
    date_text = actual_date or datetime.now(
        ZoneInfo("Asia/Tashkent")
    ).strftime("%d.%m.%Y")

    draw.rounded_rectangle(
        (730, 85, 1005, 145),
        radius=25,
        fill="white"
    )

    draw.text(
        (765, 103),
        date_text,
        font=get_font(23, True),
        fill="#34466B"
    )

    # Карточки
    positions = [350, 585, 820, 1055]

    for code, y in zip(CURRENCIES, positions):
        draw_currency_card(image, code, rates[code], y)

    draw = ImageDraw.Draw(image)

    draw.text(
        (75, 1290),
        "Источник: Центральный банк Республики Узбекистан",
        font=get_font(19),
        fill="white"
    )

    image.save("currency_card.png", quality=95)

    print("Вертикальная карточка успешно создана!")

    return "currency_card.png"


if __name__ == "__main__":
    create_currency_card()
