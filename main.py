
import os
import random
import logging
from datetime import time, datetime
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "").strip()
TZ = ZoneInfo("Asia/Tashkent")

GREETINGS = [
    "Доброе утро! ☀️ Пусть день будет продуктивным и принесёт хорошие новости!\n\nXayrli tong! ☀️ Kuningiz samarali va xushxabarlarga boy bo‘lsin!",
    "Всем отличного дня, хорошего настроения и успехов во всех делах! 💪\n\nBarchaga ajoyib kun, yaxshi kayfiyat va ishlaringizga omad tilaymiz! 💪",
    "Пусть сегодня всё получается легко, а поводов для улыбки будет больше! 😊\n\nBugun barcha ishlaringiz oson bitsin, tabassum uchun sabablar ko‘p bo‘lsin! 😊",
    "Новая возможность, новый день! Желаю всем успехов и энергии! 🚀\n\nYangi imkoniyatlar, yangi kun! Barchaga omad va kuch-g‘ayrat tilayman! 🚀",
]

HOLIDAYS = {
    (1, 1): (
        "С Новым годом! 🎄 Желаю мира, здоровья и больших успехов!\n\n"
        "Yangi yil muborak! 🎄 Sizga tinchlik, sog‘liq va katta muvaffaqiyatlar tilayman!"
    ),
    (3, 8): (
        "С Международным женским днём! 💐 Счастья, любви и благополучия!\n\n"
        "Xalqaro xotin-qizlar kuni muborak! 💐 Baxt, mehr va farovonlik tilayman!"
    ),
    (3, 21): (
        "С праздником Навруз! 🌷 Пусть в каждом доме будут мир и достаток!\n\n"
        "Navro‘z bayrami muborak! 🌷 Har bir xonadonda tinchlik va baraka bo‘lsin!"
    ),
    (5, 9): (
        "С Днём памяти и почестей! Желаем мира и благополучия. 🕊️\n\n"
        "Xotira va qadrlash kuni muborak! Tinchlik va farovonlik tilaymiz. 🕊️"
    ),
    (9, 1): (
        "С Днём независимости Узбекистана! 🇺🇿 Мира и процветания нашей стране!\n\n"
        "O‘zbekiston Mustaqilligi kuni muborak! 🇺🇿 Yurtimiz tinch va obod bo‘lsin!"
    ),
    (10, 1): (
        "С Днём учителей и наставников! 📚 Спасибо за ваш труд!\n\n"
        "O‘qituvchi va murabbiylar kuni muborak! 📚 Mehnatingiz uchun rahmat!"
    ),
    (12, 8): (
        "С Днём Конституции Узбекистана! 🇺🇿 Мира, единства и благополучия!\n\n"
        "O‘zbekiston Konstitutsiyasi kuni muborak! 🇺🇿 Tinchlik, birlik va farovonlik tilaymiz!"
    ),
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот ежедневных приветствий. 🇺🇿\n"
        "Salom! Men kundalik tabriklar botiman.\n\n"
        "Команды:\n"
        "/chatid — узнать ID чата\n"
        "/test — проверить сообщение\n"
        "/help — помощь"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/chatid — показать ID текущего чата\n"
        "/test — отправить тестовое приветствие\n"
        "/start — начать работу"
    )

async def chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Chat ID: {update.effective_chat.id}"
    )

async def test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Тест! Бот работает. ✅\n\n"
        "Sinov! Bot ishlayapti. ✅"
    )

async def send_daily_message(context: ContextTypes.DEFAULT_TYPE):
    if not GROUP_CHAT_ID:
        logging.error("Не задан GROUP_CHAT_ID.")
        return

    today = datetime.now(TZ)
    message = HOLIDAYS.get(
        (today.month, today.day),
        random.choice(GREETINGS),
    )

    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=message,
    )

def main():
    if not BOT_TOKEN:
        raise RuntimeError("Не задан BOT_TOKEN.")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("chatid", chatid))
    app.add_handler(CommandHandler("test", test))

    app.job_queue.run_daily(
        send_daily_message,
        time=time(hour=10, minute=0, tzinfo=TZ),
        name="daily_greeting",
    )

    logging.info("Бот запущен. Ежедневное сообщение — в 10:00.")
    app.run_polling()

if __name__ == "__main__":
    main()