import json
import random
import argparse
import logging

from pathlib import Path
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from PIL import Image, ImageDraw, ImageFont, ImageFilter


# =====================================================
# НАСТРОЙКИ
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

BIRTHDAYS_FILE = BASE_DIR / "birthdays.json"
CACHE_DIR = BASE_DIR / "birthday_cache"

TZ = ZoneInfo("Asia/Tashkent")

WIDTH = 1080
HEIGHT = 1350

logging.basicConfig(level=logging.INFO)


# =====================================================
# ДИЗАЙНЫ
# =====================================================

DESIGNS = [
    {
        "top": (24, 43, 78),
        "bottom": (83, 45, 91),
        "accent": (238, 194, 123),
        "decoration": "stars"
    },
    {
        "top": (27, 76, 79),
        "bottom": (19, 43, 66),
        "accent": (229, 203, 151),
        "decoration": "circles"
    },
    {
        "top": (91, 48, 58),
        "bottom": (36, 36, 70),
        "accent": (247, 202, 133),
        "decoration": "flowers"
    },
    {
        "top": (38, 65, 112),
        "bottom": (20, 34, 66),
        "accent": (226, 211, 161),
        "decoration": "stars"
    },
    {
        "top": (72, 58, 91),
        "bottom": (31, 39, 72),
        "accent": (240, 194, 137),
        "decoration": "circles"
    },
    {
        "top": (34, 83, 69),
        "bottom": (20, 42, 58),
        "accent": (231, 205, 151),
        "decoration": "flowers"
    }
]


# =====================================================
# ТЕКСТЫ ПОЗДРАВЛЕНИЙ
# =====================================================

SON_MESSAGES = [
    (
        "Сынок, с днём рождения! Желаю тебе крепкого "
        "здоровья, уверенности в себе и сил для достижения "
        "всех твоих целей. Пусть в жизни будет больше "
        "радостных событий, достойных людей и хороших "
        "возможностей. Помни, что самое главное — оставаться "
        "честным, добрым и уважать своих близких. "
        "Я всегда желаю тебе только добра. Береги себя, "
        "мой родной. Пусть у тебя всё будет хорошо!"
    ),
    (
        "Мой родной сынок, поздравляю тебя с днём рождения! "
        "Пусть каждый новый год жизни приносит тебе мудрость, "
        "опыт и новые победы. Желаю здоровья, семейного "
        "благополучия, душевного спокойствия и удачи. "
        "Не бойся идти вперёд, верь в свои силы и цени "
        "людей, которые искренне рядом с тобой. "
        "Пусть твоя дорога будет светлой, а сердце всегда "
        "остаётся добрым."
    ),
    (
        "С днём рождения, сынок! Хочу пожелать тебе "
        "крепкого здоровья, счастья и спокойствия. "
        "Пусть всё, к чему ты стремишься, постепенно "
        "становится реальностью. Цени свою семью, "
        "уважай старших, поддерживай родных и никогда "
        "не теряй доброту. Желаю тебе достойной жизни, "
        "верных друзей и много поводов для улыбки. "
        "Береги себя, родной!"
    )
]

DAUGHTER_MESSAGES = [
    (
        "Доченька, с днём рождения! Желаю тебе здоровья, "
        "счастья, любви и душевного тепла. Пусть в твоей "
        "жизни будет как можно больше светлых дней, "
        "искренних улыбок и добрых людей. Оставайся такой "
        "же доброй и заботливой. Пусть все твои мечты "
        "находят дорогу к исполнению. Береги себя, "
        "моя родная!"
    ),
    (
        "Моя дорогая доченька, поздравляю тебя! "
        "Пусть судьба будет к тебе добра, пусть рядом "
        "всегда будут любящие люди, а в душе царит "
        "спокойствие. Желаю тебе крепкого здоровья, "
        "женского счастья, радости и благополучия. "
        "Никогда не забывай, насколько ты дорога "
        "своей семье. Будь счастлива, родная!"
    )
]

MOTHER_MESSAGES = [
    (
        "Любимая, с днём рождения! Желаю тебе крепкого "
        "здоровья, спокойствия, душевного тепла и долгих "
        "счастливых лет. Спасибо тебе за заботу о нашей "
        "семье, за твоё терпение и любовь к детям. "
        "Пусть каждый день приносит тебе радость, "
        "внимание близких и хорошие новости. "
        "Береги себя, родная. Ты заслуживаешь самого "
        "доброго и светлого."
    ),
    (
        "Моя любимая, поздравляю тебя с днём рождения! "
        "От всего сердца желаю тебе здоровья, счастья "
        "и душевного покоя. Пусть дети радуют тебя "
        "своими успехами, в доме всегда будет тепло, "
        "а рядом будут люди, которые ценят и любят тебя. "
        "Спасибо за всё, что ты делаешь для нашей семьи. "
        "Будь здорова и счастлива, родная!"
    )
]


# =====================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# =====================================================

def load_font(size, bold=False):

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


def load_birthdays():

    with open(BIRTHDAYS_FILE, encoding="utf-8") as file:
        return json.load(file)


def calculate_age(birth_date, target_date):

    birthday = datetime.strptime(
        birth_date, "%Y-%m-%d"
    ).date()

    age = target_date.year - birthday.year

    if (target_date.month, target_date.day) < (
        birthday.month, birthday.day
    ):
        age -= 1

    return age


def get_message(person, year):

    seed = f"{person['name']}-{year}"

    rng = random.Random(seed)

    if person["relation"] == "mother":
        messages = MOTHER_MESSAGES

    elif person["relation"] == "daughter":
        messages = DAUGHTER_MESSAGES

    else:
        messages = SON_MESSAGES

    return rng.choice(messages)


# =====================================================
# СОЗДАНИЕ ФОНА
# =====================================================

def create_background(person, year):

    rng = random.Random(
        f"{person['name']}-{year}-design"
    )

    design = rng.choice(DESIGNS)

    image = Image.new("RGB", (WIDTH, HEIGHT))

    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):

        t = y / HEIGHT

        color = tuple(
            int(
                design["top"][i] * (1 - t)
                + design["bottom"][i] * t
            )
            for i in range(3)
        )

        draw.line(
            (0, y, WIDTH, y),
            fill=color
        )

    # Мягкое свечение

    glow = Image.new(
        "RGBA",
        (WIDTH, HEIGHT),
        (0, 0, 0, 0)
    )

    gd = ImageDraw.Draw(glow)

    gd.ellipse(
        (250, 100, 850, 700),
        fill=(*design["accent"], 55)
    )

    glow = glow.filter(
        ImageFilter.GaussianBlur(130)
    )

    image = Image.alpha_composite(
        image.convert("RGBA"),
        glow
    )

    draw = ImageDraw.Draw(image)

    # Декоративные элементы

    accent = design["accent"]

    for i in range(18):

        x = rng.randint(65, WIDTH - 65)
        y = rng.randint(100, HEIGHT - 100)
        radius = rng.randint(3, 12)

        draw.ellipse(
            (
                x - radius,
                y - radius,
                x + radius,
                y + radius
            ),
            fill=(*accent, rng.randint(45, 130))
        )

    draw.rounded_rectangle(
        (35, 35, WIDTH - 35, HEIGHT - 35),
        radius=35,
        outline=accent,
        width=3
    )

    return image, design


# =====================================================
# РИСУЕМ ТЕКСТ
# =====================================================

def centered_text(draw, text, y, font, color):

    bbox = draw.textbbox(
        (0, 0),
        text,
        font=font
    )

    width = bbox[2] - bbox[0]

    x = (WIDTH - width) // 2

    draw.text(
        (x, y),
        text,
        font=font,
        fill=color
    )


def wrap_text(draw, text, font, max_width):

    words = text.split()

    lines = []
    current = ""

    for word in words:

        test = f"{current} {word}".strip()

        if draw.textlength(test, font=font) <= max_width:
            current = test

        else:
            if current:
                lines.append(current)

            current = word

    if current:
        lines.append(current)

    return lines


# =====================================================
# СОЗДАЁМ ОТКРЫТКУ
# =====================================================

def create_card(person, target_date, output_path):

    image, design = create_background(
        person,
        target_date.year
    )

    draw = ImageDraw.Draw(image)

    accent = design["accent"]

    centered_text(
        draw,
        "С ДНЁМ РОЖДЕНИЯ",
        120,
        load_font(43, True),
        accent
    )

    centered_text(
        draw,
        person["name"],
        810,
        load_font(76, True),
        "white"
    )

    age = calculate_age(
        person["birth_date"],
        target_date
    )

    centered_text(
        draw,
        f"{age} лет",
        915,
        load_font(55, True),
        accent
    )

    centered_text(
        draw,
        "С любовью, папа ❤️",
        1120,
        load_font(39, True),
        "white"
    )

    image.convert("RGB").save(
        output_path,
        quality=95
    )


# =====================================================
# ПОДГОТОВКА ПОЗДРАВЛЕНИЯ
# =====================================================

def prepare_person(person, target_date):

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = f"{person['name']}_{target_date.year}"

    image_path = CACHE_DIR / f"{filename}.jpg"
    text_path = CACHE_DIR / f"{filename}.json"

    if image_path.exists() and text_path.exists():
        logging.info("Уже подготовлено: %s", person["name"])
        return

    age = calculate_age(
        person["birth_date"],
        target_date
    )

    message = get_message(
        person,
        target_date.year
    )

    create_card(
        person,
        target_date,
        image_path
    )

    data = {
        "name": person["name"],
        "age": age,
        "date": target_date.isoformat(),
        "message": message
    }

    with open(text_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    logging.info(
        "Подготовлено: %s, возраст %s",
        person["name"],
        age
    )


# =====================================================
# ПРЕДПРОСМОТР
# =====================================================

def preview(name):

    today = datetime.now(TZ).date()

    people = load_birthdays()

    person = next(
        (
            p for p in people
            if p["name"].lower() == name.lower()
        ),
        None
    )

    if not person:
        raise ValueError("Человек не найден.")

    birthday = datetime.strptime(
        person["birth_date"],
        "%Y-%m-%d"
    ).date()

    target_date = date(
        today.year,
        birthday.month,
        birthday.day
    )

    if target_date < today:
        target_date = date(
            today.year + 1,
            birthday.month,
            birthday.day
        )

    prepare_person(
        person,
        target_date
    )

    print("Предпросмотр создан.")
    print("Имя:", person["name"])
    print(
        "Возраст:",
        calculate_age(person["birth_date"], target_date)
    )


# =====================================================
# ПОДГОТОВКА ЗАВТРАШНИХ ИМЕНИННИКОВ
# =====================================================

def prepare_tomorrow():

    tomorrow = (
        datetime.now(TZ).date()
        + timedelta(days=1)
    )

    for person in load_birthdays():

        birthday = datetime.strptime(
            person["birth_date"],
            "%Y-%m-%d"
        ).date()

        if (
            birthday.month == tomorrow.month
            and birthday.day == tomorrow.day
        ):
            prepare_person(
                person,
                tomorrow
            )


# =====================================================
# ОТПРАВКА В TELEGRAM
# =====================================================

def send_today():

    import os
    import requests

    token = os.getenv("BOT_TOKEN")
    chat_id = os.getenv("GROUP_CHAT_ID")

    if not token or not chat_id:
        raise RuntimeError("Не заданы Telegram Secrets.")

    today = datetime.now(TZ).date()

    for person in load_birthdays():

        birthday = datetime.strptime(
            person["birth_date"],
            "%Y-%m-%d"
        ).date()

        if (
            birthday.month != today.month
            or birthday.day != today.day
        ):
            continue

        filename = f"{person['name']}_{today.year}"

        image_path = CACHE_DIR / f"{filename}.jpg"
        text_path = CACHE_DIR / f"{filename}.json"

        if not image_path.exists() or not text_path.exists():
            raise FileNotFoundError(
                f"Нет подготовленной открытки: {filename}"
            )

        with open(text_path, encoding="utf-8") as file:
            data = json.load(file)

        caption = (
            f"🎂 С днём рождения, {person['name']}!\n\n"
            f"{data['message']}"
        )

        with open(image_path, "rb") as photo:

            response = requests.post(
                f"https://api.telegram.org/bot{token}/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "caption": caption
                },
                files={
                    "photo": photo
                },
                timeout=60
            )

        response.raise_for_status()

        logging.info(
            "Отправлено поздравление: %s",
            person["name"]
        )


# =====================================================
# ЗАПУСК
# =====================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=["preview", "prepare", "send"]
    )

    parser.add_argument(
        "--name",
        default=None
    )

    args = parser.parse_args()

    if args.action == "preview":

        if not args.name:
            raise ValueError("Укажи имя через --name")

        preview(args.name)

    elif args.action == "prepare":

        prepare_tomorrow()

    elif args.action == "send":

        send_today()


if __name__ == "__main__":
    main()
