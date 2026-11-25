import os
import json
import base64
import random
import logging
import argparse
import requests

from pathlib import Path
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from PIL import Image, ImageDraw, ImageFont, ImageFilter


# ============================================================
# НАСТРОЙКИ
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

BIRTHDAYS_FILE = BASE_DIR / "birthdays.json"
CACHE_DIR = BASE_DIR / "birthday_cache"

TZ = ZoneInfo("Asia/Tashkent")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()

TEXT_MODEL = "gpt-4.1-mini"
IMAGE_MODEL = "gpt-image-1"

WIDTH = 1080
HEIGHT = 1350

OPENAI_URL = "https://api.openai.com/v1"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# ============================================================
# ЦВЕТОВЫЕ ПАЛИТРЫ
# ============================================================

PALETTES = [
    {
        "top": (24, 52, 91),
        "bottom": (76, 40, 102),
        "accent": (235, 190, 116)
    },
    {
        "top": (35, 82, 91),
        "bottom": (23, 48, 76),
        "accent": (220, 190, 135)
    },
    {
        "top": (83, 49, 82),
        "bottom": (35, 39, 76),
        "accent": (245, 194, 133)
    },
    {
        "top": (32, 64, 112),
        "bottom": (20, 35, 68),
        "accent": (218, 210, 157)
    },
    {
        "top": (91, 55, 54),
        "bottom": (40, 35, 64),
        "accent": (247, 202, 126)
    },
    {
        "top": (32, 83, 75),
        "bottom": (22, 43, 62),
        "accent": (230, 201, 145)
    }
]


# ============================================================
# ШРИФТЫ
# ============================================================

def get_font(size, bold=False):

    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

        "C:/Windows/Fonts/arialbd.ttf"
        if bold else
        "C:/Windows/Fonts/arial.ttf"
    ]

    for path in paths:

        try:
            return ImageFont.truetype(path, size)

        except OSError:
            continue

    return ImageFont.load_default()


# ============================================================
# СЕМЕЙНЫЙ КАЛЕНДАРЬ
# ============================================================

def load_birthdays():

    with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as file:

        return json.load(file)


def calculate_age(birth_date, current_date):

    birthday = datetime.strptime(
        birth_date,
        "%Y-%m-%d"
    ).date()

    age = current_date.year - birthday.year

    if (
        current_date.month,
        current_date.day
    ) < (
        birthday.month,
        birthday.day
    ):

        age -= 1

    return age


def get_birthday(person, target_date):

    birthday = datetime.strptime(
        person["birth_date"],
        "%Y-%m-%d"
    ).date()

    if (
        birthday.month,
        birthday.day
    ) != (
        target_date.month,
        target_date.day
    ):

        return None

    result = person.copy()

    result["age"] = calculate_age(
        person["birth_date"],
        target_date
    )

    return result


# ============================================================
# OPENAI — ГЕНЕРАЦИЯ ПОЗДРАВЛЕНИЯ
# ============================================================

def generate_greeting(person, year):

    if not OPENAI_API_KEY:

        raise RuntimeError(
            "Не найден OPENAI_API_KEY."
        )

    name = person["name"]
    age = person["age"]
    relation = person["relation"]
    address = person["address"]

    if relation == "mother":

        role = (
            "Это любимая жена и мама детей. "
            "Обращайся к ней тепло, как к любимой женщине."
        )

    elif relation == "daughter":

        role = (
            "Это дочь. "
            "Обращайся к ней нежно и по-отцовски."
        )

    else:

        role = (
            "Это сын. "
            "Обращайся к нему тепло и по-отцовски."
        )

    prompt = f"""
Ты пишешь семейное поздравление от имени любящего отца
своему родному человеку.

Контекст:
Имя: {name}
Возраст: {age}
Обращение: {address}
Родство: {relation}
Год: {year}

{role}

Требования:

1. Поздравление должно быть искренним и душевным.
2. Пиши от первого лица, как отец.
3. Используй естественный русский язык.
4. Не используй слишком литературные и искусственные выражения.
5. Не делай текст похожим на официальную открытку.
6. Добавь личную отцовскую теплоту.
7. Упомяни день рождения и пожелания здоровья, счастья.
8. Не повторяй банальные шаблоны.
9. Не добавляй выдуманные события из жизни человека.
10. Не упоминай искусственный интеллект.

Объём: примерно 120–180 слов.

Верни только готовый текст поздравления.
"""

    response = requests.post(
        f"{OPENAI_URL}/chat/completions",

        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },

        json={
            "model": TEXT_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.9
        },

        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    message = data["choices"][0]["message"]["content"]

    return message.strip()


# ============================================================
# OPENAI — ГЕНЕРАЦИЯ ФОНОВОГО ИЗОБРАЖЕНИЯ
# ============================================================

def generate_background(person, year):

    if not OPENAI_API_KEY:

        raise RuntimeError(
            "Не найден OPENAI_API_KEY."
        )

    relation = person["relation"]

    if relation == "mother":

        style = (
            "elegant, warm, sophisticated, "
            "beautiful flowers and soft golden light"
        )

    elif relation == "daughter":

        style = (
            "elegant, delicate, beautiful flowers, "
            "warm sunlight and refined details"
        )

    else:

        style = (
            "elegant masculine design, "
            "beautiful architecture, cinematic light"
        )

    prompt = f"""
Create a premium birthday greeting card background.

Visual direction:
{style}

Composition:
- Vertical portrait 2:3 format.
- Cinematic professional photography.
- Beautiful atmospheric lighting.
- Rich details and premium design.
- Harmonious colors.
- Tasteful decorative elements.
- Sophisticated visual composition.
- Suitable for a heartfelt family birthday greeting.

IMPORTANT:
Leave the central upper area relatively clean.
Leave the lower central area clean for text overlay.

Do not include any text.
Do not include letters.
Do not include numbers.
Do not include logos.
Do not include watermarks.

Create a completely original composition.
"""

    response = requests.post(
        f"{OPENAI_URL}/images/generations",

        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },

        json={
            "model": IMAGE_MODEL,
            "prompt": prompt,
            "size": "1024x1536",
            "quality": "high"
        },

        timeout=300
    )

    response.raise_for_status()

    data = response.json()

    image_data = base64.b64decode(
        data["data"][0]["b64_json"]
    )

    return Image.open(
        __import__("io").BytesIO(image_data)
    ).convert("RGB")


# ============================================================
# СОЗДАНИЕ ДИЗАЙНА ОТКРЫТКИ
# ============================================================

def create_fallback_background(seed):

    random.seed(seed)

    palette = random.choice(PALETTES)

    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT)
    )

    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):

        t = y / HEIGHT

        color = tuple(
            int(
                palette["top"][i] * (1 - t)
                + palette["bottom"][i] * t
            )

            for i in range(3)
        )

        draw.line(
            (0, y, WIDTH, y),
            fill=color
        )

    return image, palette


def create_card_background(person, year):

    try:

        logging.info(
            "Генерируем фон открытки для %s",
            person["name"]
        )

        image = generate_background(
            person,
            year
        )

        image = image.resize(
            (WIDTH, HEIGHT),
            Image.Resampling.LANCZOS
        )

        palette = random.choice(PALETTES)

        return image, palette

    except Exception:

        logging.exception(
            "Не удалось создать AI-фон. Используем резервный дизайн."
        )

        return create_fallback_background(
            f"{person['name']}-{year}"
        )


# ============================================================
# ТЕКСТ НА ОТКРЫТКЕ
# ============================================================

def draw_centered_text(
    draw,
    text,
    y,
    font,
    fill,
    stroke_width=0
):

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font,
        stroke_width=stroke_width
    )

    width = bbox[2] - bbox[0]

    x = (WIDTH - width) // 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=fill,
        stroke_width=stroke_width,
        stroke_fill=(0, 0, 0, 180)
    )


def create_card(person, year, output_path):

    image, palette = create_card_background(
        person,
        year
    )

    image = image.convert("RGBA")

    # Затемнение для читаемости текста

    overlay = Image.new(
        "RGBA",
        image.size,
        (0, 0, 0, 0)
    )

    overlay_draw = ImageDraw.Draw(overlay)

    overlay_draw.rectangle(
        (0, 0, WIDTH, HEIGHT),
        fill=(0, 0, 0, 65)
    )

    image = Image.alpha_composite(
        image,
        overlay
    )

    draw = ImageDraw.Draw(image)

    # Декоративная рамка

    accent = palette["accent"]

    draw.rounded_rectangle(
        (45, 45, WIDTH - 45, HEIGHT - 45),
        radius=35,
        outline=accent,
        width=3
    )

    # Верхняя надпись

    draw_centered_text(
        draw,
        "С ДНЁМ РОЖДЕНИЯ",
        120,
        get_font(36, True),
        accent
    )

    # Имя

    name = person["name"]

    name_font_size = 76

    name_font = get_font(
        name_font_size,
        True
    )

    while (
        draw.textbbox(
            (0, 0),
            name,
            font=name_font
        )[2] > WIDTH - 130
        and name_font_size > 42
    ):

        name_font_size -= 2

        name_font = get_font(
            name_font_size,
            True
        )

    draw_centered_text(
        draw,
        name,
        830,
        name_font,
        "white",
        2
    )

    # Возраст

    age_text = f"{person['age']} лет"

    draw_centered_text(
        draw,
        age_text,
        930,
        get_font(55, True),
        accent
    )

    # Нижняя подпись

    draw_centered_text(
        draw,
        "С любовью, папа ❤️",
        1110,
        get_font(38),
        "white"
    )

    image.convert("RGB").save(
        output_path,
        quality=95
    )

    logging.info(
        "Открытка сохранена: %s",
        output_path
    )


# ============================================================
# ПОДГОТОВКА ПОЗДРАВЛЕНИЯ
# ============================================================

def prepare_birthday(person, target_date):

    year = target_date.year

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        f"{person['name']}_{year}"
    )

    image_path = CACHE_DIR / f"{filename}.jpg"

    message_path = CACHE_DIR / f"{filename}.json"

    logging.info(
        "Подготавливаем поздравление: %s",
        person["name"]
    )

    # Если поздравление уже подготовлено,
    # повторно не генерируем.

    if image_path.exists() and message_path.exists():

        logging.info(
            "Готовое поздравление уже существует."
        )

        return

    message = generate_greeting(
        person,
        year
    )

    create_card(
        person,
        year,
        image_path
    )

    data = {
        "name": person["name"],
        "age": person["age"],
        "date": target_date.isoformat(),
        "message": message,
        "image": image_path.name
    }

    with open(
        message_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    logging.info(
        "Поздравление подготовлено: %s",
        person["name"]
    )


# ============================================================
# ПОДГОТОВКА ЗАВТРАШНИХ ИМЕНИННИКОВ
# ============================================================

def prepare_tomorrow():

    tomorrow = datetime.now(TZ).date() + timedelta(days=1)

    birthdays = load_birthdays()

    found = 0

    for person in birthdays:

        birthday_person = get_birthday(
            person,
            tomorrow
        )

        if birthday_person:

            prepare_birthday(
                birthday_person,
                tomorrow
            )

            found += 1

    if found == 0:

        logging.info(
            "Завтра дней рождения нет."
        )

    else:

        logging.info(
            "Подготовлено поздравлений: %s",
            found
        )


# ============================================================
# ОТПРАВКА ПОЗДРАВЛЕНИЯ В TELEGRAM
# ============================================================

def send_telegram_photo(image_path, caption):

    if not BOT_TOKEN or not GROUP_CHAT_ID:

        raise RuntimeError(
            "Не заданы BOT_TOKEN или GROUP_CHAT_ID."
        )

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendPhoto"
    )

    with open(image_path, "rb") as photo:

        response = requests.post(
            url,

            data={
                "chat_id": GROUP_CHAT_ID,
                "caption": caption
            },

            files={
                "photo": photo
            },

            timeout=120
        )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):

        raise RuntimeError(
            f"Ошибка Telegram: {result}"
        )


def send_today():

    today = datetime.now(TZ).date()

    birthdays = load_birthdays()

    found = 0

    for person in birthdays:

        birthday_person = get_birthday(
            person,
            today
        )

        if not birthday_person:

            continue

        found += 1

        filename = (
            f"{person['name']}_{today.year}"
        )

        image_path = CACHE_DIR / f"{filename}.jpg"

        message_path = CACHE_DIR / f"{filename}.json"

        if not image_path.exists() or not message_path.exists():

            raise FileNotFoundError(
                f"Не найдено заранее подготовленное поздравление: {filename}"
            )

        with open(
            message_path,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        caption = (
            f"🎂 С днём рождения, {person['name']}!\n\n"
            f"{data['message']}"
        )

        send_telegram_photo(
            image_path,
            caption
        )

        logging.info(
            "Поздравление отправлено: %s",
            person["name"]
        )

    if found == 0:

        logging.info(
            "Сегодня дней рождения нет."
        )


# ============================================================
# ПРЕДВАРИТЕЛЬНЫЙ ПРОСМОТР
# ============================================================

def preview_birthday(name):

    people = load_birthdays()

    person = next(
        (
            p for p in people
            if p["name"].lower() == name.lower()
        ),
        None
    )

    if not person:

        raise ValueError(
            f"Человек не найден: {name}"
        )

    today = datetime.now(TZ).date()

    birth_date = datetime.strptime(
        person["birth_date"],
        "%Y-%m-%d"
    ).date()

    target_date = date(
        today.year,
        birth_date.month,
        birth_date.day
    )

    if target_date < today:

        target_date = date(
            today.year + 1,
            birth_date.month,
            birth_date.day
        )

    person["age"] = calculate_age(
        person["birth_date"],
        target_date
    )

    prepare_birthday(
        person,
        target_date
    )

    print(
        f"Предпросмотр подготовлен для {name}"
    )


# ============================================================
# ЗАПУСК
# ============================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=[
            "prepare",
            "send",
            "preview"
        ]
    )

    parser.add_argument(
        "--name",
        default=None
    )

    args = parser.parse_args()

    if args.action == "prepare":

        prepare_tomorrow()

    elif args.action == "send":

        send_today()

    elif args.action == "preview":

        if not args.name:

            raise ValueError(
                "Для preview укажи --name"
            )

        preview_birthday(
            args.name
        )


if __name__ == "__main__":

    main()
