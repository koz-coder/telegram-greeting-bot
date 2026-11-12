import os
import requests
import feedparser

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape


BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

GOOGLE_NEWS_URL = "https://news.google.com/rss/search"

SOURCES = [
    {
        "name": "🇺🇿 Kun.uz",
        "query": "site:kun.uz",
    },
    {
        "name": "🌍 Reuters",
        "query": "site:reuters.com",
    },
    {
        "name": "🌐 BBC",
        "query": "site:bbc.com",
    },
]

MAX_NEWS = 7
NEWS_AGE_HOURS = 24


def get_news():
    all_news = []
    seen_titles = set()

    for source in SOURCES:
        params = {
            "q": source["query"],
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

                if not title or not link:
                    continue

                published = entry.get("published")

                if not published:
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

                now = datetime.now(timezone.utc)

                if now - published_date > timedelta(
                    hours=NEWS_AGE_HOURS
                ):
                    continue

                if published_date > now + timedelta(hours=1):
                    continue

                normalized_title = title.lower()

                if normalized_title in seen_titles:
                    continue

                seen_titles.add(normalized_title)

                all_news.append({
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

    return all_news[:MAX_NEWS]


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
            f"Telegram error: {result}"
        )


def main():
    if not BOT_TOKEN or not GROUP_CHAT_ID:
        raise RuntimeError(
            "Не найдены BOT_TOKEN или GROUP_CHAT_ID"
        )

    news = get_news()

    if not news:
        send_telegram_message(
            "📰 <b>Новости дня</b>\n\n"
            "Сегодня не удалось найти свежие новости "
            "за последние 24 часа."
        )
        return

    message = "📰 <b>ГЛАВНЫЕ НОВОСТИ</b>\n"
    message += "━━━━━━━━━━━━━━━━━━\n\n"

    for index, item in enumerate(news, start=1):
        title = escape(item["title"])
        source = escape(item["source"])
        link = escape(item["link"], quote=True)

        message += (
            f"<b>{index}. {title}</b>\n"
            f"{source}\n"
            f'<a href="{link}">Читать новость</a>\n\n'
        )

    message += "━━━━━━━━━━━━━━━━━━\n"
    message += "Новости за последние 24 часа."

    send_telegram_message(message)

    print(f"Успешно отправлено новостей: {len(news)}")


if __name__ == "__main__":
    main()
