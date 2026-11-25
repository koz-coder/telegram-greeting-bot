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
        "top": (13, 22, 38),
        "bottom": (25, 39, 59),
        "accent": (198, 169, 119),
        "text": (245, 243, 237)
    },
    {
        "top": (18, 25, 35),
        "bottom": (34, 43, 54),
        "accent": (184, 190, 190),
        "text": (246, 246, 242)
    },
    {
        "top": (24, 22, 31),
        "bottom": (48, 38, 48),
        "accent": (205, 174, 145),
        "text": (248, 242, 237)
    },
    {
        "top": (13, 29, 35),
        "bottom": (24, 48, 53),
        "accent": (174, 190, 171),
        "text": (243, 246, 239)
    }
]


# =====================================================
# ТЕКСТЫ ПОЗДРАВЛЕНИЙ
# =====================================================

SON_MESSAGES = [
    "Сынок, с днём рождения! Желаю тебе крепкого здоровья, уверенности в себе и сил для достижения всех целей. Пусть рядом будут верные люди, а в доме всегда царят мир и благополучие. Береги себя, родной!",

    "Мой дорогой сын, пусть каждый год приносит тебе мудрость, опыт и новые возможности. Желаю достойной жизни, крепкой семьи, душевного спокойствия и успехов во всех начинаниях. Никогда не теряй доброту своего сердца.",

    "Сынок, желаю тебе здоровья, счастья и достатка. Пусть любые трудности делают тебя сильнее, а каждый новый день открывает хорошие перспективы. Цени родных, уважай близких и всегда верь в свои силы.",

    "С днём рождения, родной! Пусть твоя дорога будет светлой, решения — мудрыми, а рядом всегда будут те, кто искренне желает тебе добра. Желаю тебе семейного тепла и много счастливых лет.",

    "Мой сынок, желаю тебе никогда не терять веру в себя. Пусть труд приносит достойные результаты, мечты становятся реальностью, а сердце всегда остаётся спокойным. Будь здоров и счастлив!",

    "Родной мой, поздравляю тебя с днём рождения! Желаю крепкого здоровья, терпения, сил и благополучия. Пусть в твоей семье всегда будут любовь, уважение и взаимопонимание.",

    "Сынок, пусть в жизни будет больше поводов для радости, хороших новостей и добрых встреч. Желаю тебе уверенно идти вперёд, не забывая о семье и тех, кто тебя любит.",

    "Дорогой сын, желаю тебе долгих лет жизни, крепкого здоровья и спокойствия в душе. Пусть Всевышний оберегает тебя, помогает в добрых делах и хранит твою семью.",

    "Сынок, пусть каждый прожитый год делает тебя мудрее и сильнее. Желаю тебе достатка, уважения окружающих, настоящей дружбы и счастья в семейной жизни.",

    "Мой родной, с днём рождения! Желаю, чтобы в твоём доме всегда звучал смех, дети радовали своими успехами, а близкие были здоровы. Береги себя и цени каждый день."
]


DAUGHTER_MESSAGES = [
    "Доченька, с днём рождения! Желаю тебе крепкого здоровья, настоящего счастья и душевного тепла. Пусть рядом всегда будут любящие люди, а все твои добрые мечты находят дорогу к исполнению.",

    "Моя дорогая доченька, пусть судьба будет к тебе добра. Желаю семейного благополучия, любви, спокойствия и много счастливых моментов. Береги себя, родная!",

    "Родная моя, желаю тебе здоровья, женского счастья и уверенности в завтрашнем дне. Пусть твой дом будет наполнен любовью, улыбками и взаимопониманием.",

    "Доченька, пусть каждый новый день приносит тебе радость, приятные встречи и хорошие новости. Оставайся такой же доброй, искренней и заботливой. Будь счастлива!",

    "Моя любимая доченька, желаю тебе долгих и счастливых лет, крепкого здоровья и душевного спокойствия. Пусть близкие всегда окружают тебя заботой, а жизнь радует приятными событиями.",

    "С днём рождения, родная! Пусть в твоей жизни будет больше света, любви и добрых людей. Желаю, чтобы все трудности оставались позади, а впереди ждали только хорошие перемены.",

    "Доченька, желаю тебе благополучия, здоровья и исполнения желаний. Пусть твоя семья будет крепкой, дети здоровыми, а сердце всегда наполнено теплом.",

    "Моя родная, никогда не забывай, как ты дорога своей семье. Желаю тебе радости, терпения, мудрости и много счастливых лет. Пусть Всевышний хранит тебя."
]


MOTHER_MESSAGES = [
    "Любимая, с днём рождения! Желаю тебе крепкого здоровья, спокойствия и долгих счастливых лет. Спасибо за твою заботу, терпение и любовь к нашей семье. Пусть дети всегда радуют тебя, а каждый день приносит тепло и радость.",

    "Моя дорогая, пусть Всевышний дарует тебе здоровье, силы и душевный покой. Желаю, чтобы рядом всегда были любящие дети, чтобы в доме царили уют и благополучие. Береги себя, родная.",

    "Любимая, поздравляю тебя! Желаю тебе много светлых дней, хорошего настроения и крепкого здоровья. Пусть все переживания сменяются радостью, а близкие окружают тебя заботой и вниманием.",

    "Родная моя, ты — сердце нашей семьи. Желаю тебе долгих лет жизни, спокойствия в душе и благополучия. Пусть дети будут здоровы и счастливы, а дом всегда наполнен добром.",

    "Моя любимая, желаю тебе здоровья, терпения и душевного тепла. Пусть каждый новый день приносит хорошие новости, улыбки детей и уверенность в том, что рядом есть родные люди.",

    "С днём рождения, родная! Пусть в твоей жизни будет больше спокойных дней, приятных событий и искренней радости. Спасибо тебе за всё, что ты делаешь для нашей семьи.",

    "Любимая, желаю тебе крепкого здоровья и долгих лет. Пусть Всевышний оберегает тебя, дарит силы и наполняет сердце спокойствием. Будь счастлива, родная.",

    "Моя дорогая жена, пусть дети всегда будут твоей радостью и гордостью. Желаю тебе благополучия, заботы близких, домашнего уюта и много счастливых мгновений."
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



def age_suffix(age):
    last_two = age % 100
    last = age % 10

    if 11 <= last_two <= 14:
        return "лет"
    if last == 1:
        return "год"
    if 2 <= last <= 4:
        return "года"
    return "лет"

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

    # Сдержанная палитра: разные оттенки, без случайных украшений.
    rng = random.Random(f"{person['name']}-{year}-premium")
    design = rng.choice(DESIGNS)

    image = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)

    for y in range(HEIGHT):
        t = y / max(HEIGHT - 1, 1)
        color = tuple(
            int(
                design["top"][i] * (1 - t)
                + design["bottom"][i] * t
            )
            for i in range(3)
        )
        draw.line((0, y, WIDTH, y), fill=color)

    # Едва заметное центральное свечение, без блёсток и фигур.
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        (170, 230, 910, 1030),
        fill=(*design["accent"], 20)
    )
    glow = glow.filter(ImageFilter.GaussianBlur(190))
    image = Image.alpha_composite(image.convert("RGBA"), glow)

    draw = ImageDraw.Draw(image)

    # Тонкая рамка и короткий разделитель — минималистичное оформление.
    draw.rounded_rectangle(
        (42, 42, WIDTH - 42, HEIGHT - 42),
        radius=22,
        outline=(*design["accent"], 150),
        width=2
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

def get_card_wish(person):

    relation = person.get("relation", "son")

    if relation == "mother":
        return (
            "Пусть рядом всегда будут любовь близких, "
            "душевный покой и поводы для улыбки."
        )

    if relation == "daughter":
        return (
            "Пусть в жизни будет больше счастливых дней, "
            "любви и тепла. Береги себя, родная."
        )

    return (
        "Желаю здоровья, внутренней силы и уверенности "
        "в каждом шаге. Береги себя и своих близких."
    )


def create_card(person, target_date, output_path):

    image, design = create_background(
        person,
        target_date.year
    )

    draw = ImageDraw.Draw(image)
    accent = design["accent"]
    main_text = design["text"]

    # Верхняя подпись
    heading_font = load_font(30, True)
    centered_text(
        draw,
        "С ДНЁМ РОЖДЕНИЯ",
        155,
        heading_font,
        accent
    )

    # Тонкий разделитель под заголовком
    draw.line(
        (390, 225, 690, 225),
        fill=(*accent, 180),
        width=2
    )

    # Имя — главный акцент композиции
    name = person["name"]
    name_font = load_font(76, True)

    # Уменьшаем шрифт для длинных имён, чтобы они не выходили за поля.
    while draw.textlength(name, font=name_font) > 900:
        name_font = load_font(name_font.size - 4, True)

    centered_text(
        draw,
        name,
        440,
        name_font,
        main_text
    )

    age = calculate_age(
        person["birth_date"],
        target_date
    )
    age_text = f"{age} {age_suffix(age)}"

    centered_text(
        draw,
        age_text,
        555,
        load_font(38),
        accent
    )

    # Короткое пожелание, без шаблонных лозунгов и лишних украшений.
    wish = get_card_wish(person)
    wish_font = load_font(30)
    lines = wrap_text(draw, wish, wish_font, 760)

    line_height = 52
    start_y = 770 - ((len(lines) - 1) * line_height) // 2

    for index, line in enumerate(lines):
        centered_text(
            draw,
            line,
            start_y + index * line_height,
            wish_font,
            main_text
        )

    # Подпись отделена большим свободным пространством.
    centered_text(
        draw,
        "С любовью, папа",
        1135,
        load_font(30),
        accent
    )

    image.convert("RGB").save(
        output_path,
        quality=95
    )


# =====================================================
# ПОДГОТОВКА ПОЗДРАВЛЕНИЯ
# =====================================================

def prepare_person(person, target_date, force=False):

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = f"{person['name']}_{target_date.year}"

    image_path = CACHE_DIR / f"{filename}.jpg"
    text_path = CACHE_DIR / f"{filename}.json"

    if image_path.exists() and text_path.exists() and not force:
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
        target_date,
        force=True
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
