import os
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "").strip()

TZ = ZoneInfo("Asia/Tashkent")

HOLIDAYS = {
    (1, 1): "🎄 С Новым годом! / Yangi yilingiz bilan!",
    (3, 8): "🌷 С Международным женским днём! / Xalqaro xotin-qizlar kuni muborak!",
    (3, 21): "🌸 С праздником Навруз! / Navro‘z bayrami muborak!",
    (5, 9): "🕊 С Днём памяти и почестей! / Xotira va qadrlash kuni muborak!",
    (9, 1): "🇺🇿 С Днём независимости Узбекистана! / O‘zbekiston Mustaqilligi kuni muborak!",
    (10, 1): "📚 С Днём учителей и наставников! / O‘qituvchi va murabbiylar kuni muborak!",
    (12, 8): "🇺🇿 С Днём Конституции Узбекистана! / O‘zbekiston Konstitutsiyasi kuni muborak!",
}


def get_message():
    now = datetime.now(TZ)
    holiday = HOLIDAYS.get((now.month, now.day))

    if holiday:
        return (
            f"{holiday}\n\n"
            "Желаем всем здоровья и успехов! 🌟\n"
            "Barchangizga sog‘lik va muvaffaqiyat tilaymiz! 🌟"
        )

    return (
        "☀️ Доброе утро, команда!\n"
        "Желаем всем продуктивного дня и успехов! 💪\n\n"
        "☀️ Xayrli tong, jamoa!\n"
        "Barchangizga samarali kun va muvaffaqiyat tilaymiz! 💪"
    )


async def main():
    if not BOT_TOKEN or not GROUP_CHAT_ID:
        raise ValueError(
            "Не заданы BOT_TOKEN и GROUP_CHAT_ID в переменных окружения."
        )

    bot = Bot(token=BOT_TOKEN)

    try:
        await bot.initialize()
        await bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=get_message()
        )
        print("Сообщение успешно отправлено!")
    finally:
        await bot.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
