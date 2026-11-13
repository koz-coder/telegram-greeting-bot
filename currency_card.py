import math
import requests

from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# =====================================================
# НАСТРОЙКИ
# =====================================================

WIDTH = 1080
HEIGHT = 1350

SCALE = 2

W = WIDTH * SCALE
H = HEIGHT * SCALE

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "currency_card.png"

CBU_URL = "https://cbu.uz/ru/arkhiv-kursov-valyut/json/"

TZ = ZoneInfo("Asia/Tashkent")


CURRENCIES = {
    "USD": ("Доллар США", "#2878E8", "US"),
    "EUR": ("Евро", "#7655D9", "EU"),
    "RUB": ("Российский рубль", "#E64F78", "RU"),
    "TRY": ("Турецкая лира", "#12A88A", "TR"),
}


def s(value):
    """Масштабирование координат для высокого разрешения."""
    return int(value * SCALE)


def get_font(size, bold=False):
    """Загрузка шрифтов."""
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
# ПОЛУЧЕНИЕ КУРСОВ ЦБ
# =====================================================

def get_rates():
    response = requests.get(
        CBU_URL,
        timeout=25,
        headers={"User-Agent": "Mozilla/5.0"}
    )

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


# =====================================================
# ФОНОВЫЙ ДИЗАЙН
# =====================================================

def create_background():
    image = Image.new("RGB", (W, H))

    pixels = image.load()

    top = (19, 91, 190)
    bottom = (76, 55, 157)

    for y in range(H):
        t = y / H

        t = t * t * (3 - 2 * t)

        color = tuple(
            int(top[i] * (1 - t) + bottom[i] * t)
            for i in range(3)
        )

        for x in range(W):
            pixels[x, y] = color

    # Мягкое голубое свечение
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    glow_draw.ellipse(
        (s(650), s(-250), s(1250), s(350)),
        fill=(91, 176, 255, 65)
    )

    glow_draw.ellipse(
        (s(-300), s(850), s(450), s(1550)),
        fill=(120, 100, 255, 35)
    )

    glow = glow.filter(
        ImageFilter.GaussianBlur(s(100))
    )

    image = Image.alpha_composite(
        image.convert("RGBA"),
        glow
    )

    return image


# =====================================================
# КРУГЛЫЕ ФЛАГИ
# =====================================================

def draw_flag(image, center_x, center_y, code):
    size = s(76)

    flag = Image.new(
        "RGBA",
        (size, size),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(flag)

    cx = size // 2
    cy = size // 2
    radius = size // 2

    if code == "US":

        stripe_height = size / 13

        for i in range(13):
            color = (
                "#D83D4D"
                if i % 2 == 0
                else "#FFFFFF"
            )

            y1 = int(i * stripe_height)

            y2 = int((i + 1) * stripe_height)

            draw.rectangle(
                (0, y1, size, y2),
                fill=color
            )

        draw.rectangle(
            (0, 0, int(size * 0.48), int(size * 0.54)),
            fill="#234A91"
        )

        for row in range(5):
            for col in range(5):
                px = int(size * 0.07 + col * size * 0.075)
                py = int(size * 0.06 + row * size * 0.095)

                draw.ellipse(
                    (px, py, px + s(2), py + s(2)),
                    fill="white"
                )

    elif code == "EU":

        draw.ellipse(
            (0, 0, size, size),
            fill="#244BAA"
        )

        for angle in range(0, 360, 30):
            rad = math.radians(angle)

            px = cx + int(size * 0.29 * math.cos(rad))
            py = cy + int(size * 0.29 * math.sin(rad))

            draw.ellipse(
                (
                    px - s(2),
                    py - s(2),
                    px + s(2),
                    py + s(2)
                ),
                fill="#FFD447"
            )

    elif code == "RU":

        draw.rectangle(
            (0, 0, size, size // 3),
            fill="#FFFFFF"
        )

        draw.rectangle(
            (0, size // 3, size, 2 * size // 3),
            fill="#3977D8"
        )

        draw.rectangle(
            (0, 2 * size // 3, size, size),
            fill="#E94A54"
        )

    elif code == "TR":

        draw.ellipse(
            (0, 0, size, size),
            fill="#E84152"
        )

        draw.ellipse(
            (
                cx - s(16),
                cy - s(19),
                cx + s(18),
                cy + s(15)
            ),
            fill="white"
        )

        draw.ellipse(
            (
                cx - s(5),
                cy - s(19),
                cx + s(29),
                cy + s(15)
            ),
            fill="#E84152"
        )

        # Звезда
        points = []

        for i in range(10):
            angle = math.radians(-90 + i * 36)

            r = s(10) if i % 2 == 0 else s(4)

            points.append(
                (
                    cx + s(17) + r * math.cos(angle),
                    cy - s(2) + r * math.sin(angle)
                )
            )

        draw.polygon(points, fill="white")

    # Маска круга
    mask = Image.new("L", (size, size), 0)

    mask_draw = ImageDraw.Draw(mask)

    mask_draw.ellipse(
        (0, 0, size - 1, size - 1),
        fill=255
    )

    flag.putalpha(mask)

    # Мягкая белая подложка
    shadow = Image.new(
        "RGBA",
        (size + s(12), size + s(12)),
        (0, 0, 0, 0)
    )

    shadow_draw = ImageDraw.Draw(shadow)

    shadow_draw.ellipse(
        (s(3), s(3), size + s(9), size + s(9)),
        fill=(0, 0, 0, 35)
    )

    shadow = shadow.filter(
        ImageFilter.GaussianBlur(s(5))
    )

    image.alpha_composite(
        shadow,
        (
            s(center_x) - size // 2 - s(6),
            s(center_y) - size // 2 - s(6)
        )
    )

    image.alpha_composite(
        flag,
        (
            s(center_x) - size // 2,
            s(center_y) - size // 2
        )
    )


# =====================================================
# КАРТОЧКА ОДНОЙ ВАЛЮТЫ
# =====================================================

def draw_currency_card(image, code, rate, y):
    name, accent, flag = CURRENCIES[code]

    x = 65
    card_width = 950
    card_height = 190

    # Тень
    shadow = Image.new(
        "RGBA",
        (W, H),
        (0, 0, 0, 0)
    )

    shadow_draw = ImageDraw.Draw(shadow)

    shadow_draw.rounded_rectangle(
        (
            s(x + 5),
            s(y + 12),
            s(x + card_width + 5),
            s(y + card_height + 12)
        ),
        radius=s(30),
        fill=(5, 15, 40, 95)
    )

    shadow = shadow.filter(
        ImageFilter.GaussianBlur(s(17))
    )

    image.alpha_composite(shadow)

    draw = ImageDraw.Draw(image)

    # Основная карточка
    draw.rounded_rectangle(
        (
            s(x),
            s(y),
            s(x + card_width),
            s(y + card_height)
        ),
        radius=s(30),
        fill="#FFFFFF"
    )

    # Цветная боковая полоса
    draw.rounded_rectangle(
        (
            s(x),
            s(y + 25),
            s(x + 9),
            s(y + card_height - 25)
        ),
        radius=s(5),
        fill=accent
    )

    # Флаг
    draw_flag(
        image,
        x + 105,
        y + 95,
        flag
    )

    draw = ImageDraw.Draw(image)

    # Код валюты
    draw.text(
        (s(x + 175), s(y + 48)),
        code,
        font=get_font(42, True),
        fill="#172B4D"
    )

    # Название валюты
    draw.text(
        (s(x + 175), s(y + 112)),
        name,
        font=get_font(24),
        fill="#78859A"
    )

    # Курс
    rate_text = f"{rate:,.2f}".replace(",", " ")

    rate_font = get_font(43, True)

    draw.text(
        (s(x + 475), s(y + 57)),
        rate_text,
        font=rate_font,
        fill=accent
    )

    draw.text(
        (s(x + 478), s(y + 120)),
        "Узбекский сум",
        font=get_font(15, True),
        fill="#9AA5B5"
    )


# =====================================================
# ГЛАВНАЯ КАРТОЧКА
# =====================================================

def create_currency_card():
    rates, actual_date = get_rates()

    image = create_background()

    draw = ImageDraw.Draw(image)

    # Верхний заголовок
    draw.text(
        (s(75), s(72)),
        "ФИНАНСЫ УЗБЕКИСТАНА",
        font=get_font(23, True),
        fill="#C9E1FF"
    )

    draw.text(
        (s(75), s(120)),
        "Курсы валют",
        font=get_font(76, True),
        fill="#FFFFFF"
    )

    draw.text(
        (s(80), s(220)),
        "Официальные курсы Центрального банка",
        font=get_font(24),
        fill="#DCE9FF"
    )

    # Дата
    date_text = actual_date or datetime.now(
        TZ
    ).strftime("%d.%m.%Y")

    draw.rounded_rectangle(
        (
            s(755),
            s(72),
            s(1005),
            s(132)
        ),
        radius=s(25),
        fill="#FFFFFF"
    )

    date_font = get_font(21, True)

    bbox = draw.textbbox(
        (0, 0),
        date_text,
        font=date_font
    )

    date_width = bbox[2] - bbox[0]

    draw.text(
        (
            s(880) - date_width // 2,
            s(91)
        ),
        date_text,
        font=date_font,
        fill="#34466B"
    )

    # Карточки валют
    positions = [335, 555, 775, 995]

    for code, y in zip(CURRENCIES, positions):
        draw_currency_card(
            image,
            code,
            rates[code],
            y
        )

    draw = ImageDraw.Draw(image)

    # Нижний разделитель
    draw.line(
        (
            s(75),
            s(1240),
            s(1005),
            s(1240)
        ),
        fill=(255, 255, 255, 85),
        width=s(1)
    )

    # Источник
    draw.text(
        (s(75), s(1270)),
        "Источник: Центральный банк Республики Узбекистан",
        font=get_font(18),
        fill="#E4EDFF"
    )

    # Уменьшение с сохранением качества
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

    print("Премиальная карточка курсов валют создана!")

    return str(OUTPUT_PATH)


if __name__ == "__main__":
    create_currency_card()
