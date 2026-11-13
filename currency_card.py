import requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from zoneinfo import ZoneInfo
import os

# Настройки изображения
WIDTH = 1200
HEIGHT = 675

BACKGROUND = "#101827"
CARD_COLOR = "#1C293B"
WHITE = "#FFFFFF"
GRAY = "#AAB7C8"
GREEN = "#35D49A"
ACCENT = "#6C8EFF"

CURRENCIES = {
    "USD": ("🇺🇸", "Доллар США"),
    "EUR": ("🇪🇺", "Евро"),
    "RUB": ("🇷🇺", "Российский рубль"),
    "TRY": ("🇹🇷", "Турецкая лира"),
}


def get_font(size, bold=False):
    if bold:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    else:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    return ImageFont.truetype(path, size)


def get_currency_rates():
    url = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    data = response.json()

    rates = {}

    for item in data:
        code = item.get("Ccy")

        if code in CURRENCIES:
            rates[code] = float(item["Rate"])

    return rates


def create_currency_card():
    rates = get_currency_rates()

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND
    )

    draw = ImageDraw.Draw(image)

    # Заголовок
    draw.text(
        (65, 45),
        "KU ZYA  |  ФИНАНСЫ",
        font=get_font(23, True),
        fill=ACCENT
    )

    draw.text(
        (65, 100),
        "Курсы валют",
        font=get_font(55, True),
        fill=WHITE
    )

    draw.text(
        (68, 175),
        "Официальные курсы Центрального банка Узбекистана",
        font=get_font(20),
        fill=GRAY
    )

    # Дата
    today = datetime.now(
        ZoneInfo("Asia/Tashkent")
    ).strftime("%d.%m.%Y")

    draw.text(
        (950, 65),
        today,
        font=get_font(22, True),
        fill=GRAY
    )

    # Карточки валют
    positions = [
        (65, 250),
        (625, 250),
        (65, 430),
        (625, 430)
    ]

    for (code, (flag, name)), position in zip(
        CURRENCIES.items(),
        positions
    ):
        x, y = position

        draw.rounded_rectangle(
            (x, y, x + 510, y + 145),
            radius=22,
            fill=CARD_COLOR
        )

        draw.text(
            (x + 28, y + 22),
            code,
            font=get_font(32, True),
            fill=WHITE
        )

        draw.text(
            (x + 28, y + 72),
            name,
            font=get_font(19),
            fill=GRAY
        )

        rate = rates.get(code)

        if rate is not None:
            rate_text = f"{rate:,.2f}".replace(",", " ")

            draw.text(
                (x + 275, y + 43),
                rate_text,
                font=get_font(35, True),
                fill=GREEN
            )

            draw.text(
                (x + 400, y + 95),
                "UZS",
                font=get_font(17, True),
                fill=GRAY
            )

    # Нижняя подпись
    draw.text(
        (65, 625),
        "KU ZYA • Ваш семейный помощник",
        font=get_font(18),
        fill=GRAY
    )

    output_path = "currency_card.png"

    image.save(output_path, quality=95)

    print(f"Карточка создана: {output_path}")

    return output_path


if __name__ == "__main__":
    create_currency_card()
