import os
import json
import hashlib
import requests
import feedparser

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape


BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

GOOGLE_NEWS_URL = "https://news.google.com/rss/search"

HISTORY_FILE = "sent_news.json"

MAX_NEWS = 7
NEWS_AGE_HOURS = 24
HISTORY_DAYS = 60

# Только узбекские СМИ

SOURCES = [
    {
        "name": "🇺🇿 Kun.uz",
        "query": "site:kun.uz",
    },
    {
        "name": "🇺🇿 Gazeta.uz",
        "query": "site:gazeta.uz",
    },
    {
        "name": "🇺🇿 Daryo.uz",
        "query": "site:daryo.uz",
    },
    {
        "name": "🇺🇿 Spot.uz",
        "query": "site:spot.uz",
    },
    {
        "name": "🇺🇿 UzA",
        "query": "site:uza.uz",
    },
]


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        print("История новостей не найдена. Создаём новую.")
        return {}


def save_history(history):
    cutoff = datetime.now(timezone.utc) - timedelta(
        days=HISTORY_DAYS
    )

    cleaned_history = {}

    for key, value in history.items():
        try:
            sent_date = datetime.fromisoformat(value)

            if sent_date >= cutoff:
                cleaned_history[key] = value

        except (ValueError, TypeError):
            continue

    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        json.dump(
            cleaned_history,
            file,
            ensure_ascii=False,
            indent=2,
        )


def get_news():
    all_news = []
    seen_titles = set()

    now = datetime.now(timezone.utc)

    for source in SOURCES:

        params = {
            "q": f"{source['query']} when:1d",
            "hl": "ru",
            "gl": "UZ",
            "ceid": "UZ:ru",
        }

        try:
            response = requests.get(
                GOOGLE_NEWS_URL,
                params=params,
                timeout=20,
                headers={
                    "User-Agent": "Mozilla/5.0"
                },
            )

            response.raise_for_status()

            feed = feedparser.parse(response.content)

            for entry in feed.entries:

                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()
                published = entry.get("published")

                if not title or not link or not published:
                    continue

                try:
                    published_date = parsedate_to_datetime(
                        published
                    )

                    if published_date.tzinfo is None:
                        published_date = published_date.replace(
                            tzinfo=timezone.utc
                        )

                except (TypeError, ValueError):
                    continue

                if now - published_date > timedelta(
                    hours=NEWS_AGE_HOURS
                ):
                    continue

                if published_date > now + timedelta(hours=1):
                    continue

                normalized_title = " ".join(
                    title.lower().split()
                )

                if normalized_title in seen_titles:
                    continue

                seen_titles.add(normalized_title)

                news_id = hashlib.sha256(
                    normalized_title.encode("utf-8")
                ).hexdigest()

                all_news.append({
                    "id": news_id,
                    "title": title,
                    "link": link,
                    "source": source["name"],
                    "date": published_date,
                })

        except requests.RequestException as error:
            print(
                f"Ошибка получения новостей "
                f"{source['name']}: {error}"
            )

    all_news.sort(
        key=lambda item: item["date"],
        reverse=True,
    )

    return all_news


def send_telegram_message(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

    response = requests.post(
        url,
        data={
            "chat_id": GROUP_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=30,
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Ошибка Telegram: {result}"
        )


def main():

    if not BOT_TOKEN or not GROUP_CHAT_ID:
        raise RuntimeError(
            "Не найдены BOT_TOKEN или GROUP_CHAT_ID"
        )

    history = load_history()

    all_news = get_news()

    new_news = [
        item for item in all_news
        if item["id"] not in history
    ]

    new_news = new_news[:MAX_NEWS]

    if not new_news:

        print("Новых новостей нет.")

        send_telegram_message(
            "🇺🇿 <b>НОВОСТИ УЗБЕКИСТАНА</b>\n\n"
            "За последние 24 часа новых публикаций "
            "не найдено."
        )

        save_history(history)
        return

    message = (
        "🇺🇿 <b>ГЛАВНЫЕ НОВОСТИ УЗБЕКИСТАНА</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
    )

    for index, item in enumerate(new_news, start=1):

        title = escape(item["title"])
        source = escape(item["source"])
        link = escape(item["link"], quote=True)

        message += (
            f"<b>{index}. {title}</b>\n"
            f"{source}\n"
            f'<a href="{link}">📖 Читать подробнее</a>\n\n'
        )

    message += (
        "━━━━━━━━━━━━━━━━━━\n"
        "📰 Свежие новости за последние 24 часа."
    )

    # Telegram ограничивает сообщение 4096 символами.
    if len(message) > 4000:
        print("Сообщение слишком длинное. Уменьшаем количество новостей.")

        while len(message) > 4000 and len(new_news) > 1:
            new_news.pop()

            message = (
                "🇺🇿 <b>ГЛАВНЫЕ НОВОСТИ УЗБЕКИСТАНА</b>\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
            )

            for index, item in enumerate(new_news, start=1):
                title = escape(item["title"])
                source = escape(item["source"])
                link = escape(item["link"], quote=True)

                message += (
                    f"<b>{index}. {title}</b>\n"
                    f"{source}\n"
                    f'<a href="{link}">📖 Читать подробнее</a>\n\n'
                )

            message += (
                "━━━━━━━━━━━━━━━━━━\n"
                "📰 Свежие новости за последние 24 часа."
            )

    send_telegram_message(message)

    now = datetime.now(timezone.utc).isoformat()

    for item in new_news:
        history[item["id"]] = now

    save_history(history)

    print(
        f"Успешно отправлено новостей: {len(new_news)}"
    )


if __name__ == "__main__":
    main()
