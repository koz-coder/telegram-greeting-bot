import os
import re
import json
import hashlib
import requests
import feedparser

from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape, unescape
from urllib.parse import urlparse, urljoin


BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID")

GOOGLE_NEWS_URL = "https://news.google.com/rss/search"

HISTORY_FILE = "sent_news.json"

MAX_NEWS = 7
NEWS_AGE_HOURS = 24
HISTORY_DAYS = 60

REQUEST_TIMEOUT = 25

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
    )
}

# Только узбекские СМИ

SOURCES = [
    {
        "name": "Kun.uz",
        "query": "site:kun.uz",
    },
    {
        "name": "Gazeta.uz",
        "query": "site:gazeta.uz",
    },
    {
        "name": "Daryo.uz",
        "query": "site:daryo.uz",
    },
    {
        "name": "Spot.uz",
        "query": "site:spot.uz",
    },
    {
        "name": "UzA",
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
        print("История новостей не найдена.")
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


def clean_html(text):
    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_entry_date(entry):
    published = entry.get("published")

    if not published:
        published = entry.get("updated")

    if not published:
        return None

    try:
        date = parsedate_to_datetime(published)

        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)

        return date.astimezone(timezone.utc)

    except (TypeError, ValueError):
        try:
            date = datetime.fromisoformat(
                published.replace("Z", "+00:00")
            )

            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)

            return date.astimezone(timezone.utc)

        except (ValueError, TypeError):
            return None


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
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
            )

            response.raise_for_status()

            feed = feedparser.parse(response.content)

            for entry in feed.entries:

                title = entry.get("title", "").strip()
                link = entry.get("link", "").strip()

                if not title or not link:
                    continue

                published_date = get_entry_date(entry)

                if not published_date:
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

                description = clean_html(
                    entry.get("summary", "")
                )

                news_id = hashlib.sha256(
                    normalized_title.encode("utf-8")
                ).hexdigest()

                all_news.append({
                    "id": news_id,
                    "title": title,
                    "description": description,
                    "link": link,
                    "source": source["name"],
                    "date": published_date,
                    "image": None,
                    "video": None,
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


def get_article_media(url):
    """
    Пытается получить фотографию и прямое видео
    из метаданных оригинальной публикации.
    """

    image_url = None
    video_url = None

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        response.raise_for_status()

        page = response.text

        # Open Graph image

        image_patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
        ]

        for pattern in image_patterns:

            match = re.search(
                pattern,
                page,
                re.IGNORECASE,
            )

            if match:
                image_url = urljoin(
                    response.url,
                    unescape(match.group(1)),
                )
                break

        # Прямые видеофайлы MP4

        video_patterns = [
            r'<meta[^>]+property=["\']og:video:url["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+property=["\']og:video["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+\.mp4[^"\']*)["\']',
        ]

        for pattern in video_patterns:

            match = re.search(
                pattern,
                page,
                re.IGNORECASE,
            )

            if match:

                candidate = urljoin(
                    response.url,
                    unescape(match.group(1)),
                )

                if candidate.lower().split("?")[0].endswith(".mp4"):
                    video_url = candidate
                    break

    except requests.RequestException as error:
        print(f"Не удалось получить медиа: {error}")

    return image_url, video_url


def telegram_request(method, data=None, files=None):
    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/{method}"
    )

    response = requests.post(
        url,
        data=data,
        files=files,
        timeout=60,
    )

    response.raise_for_status()

    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(
            f"Ошибка Telegram: {result}"
        )

    return result


def send_text(message):
    telegram_request(
        "sendMessage",
        data={
            "chat_id": GROUP_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
    )


def send_photo(image_url, caption):
    response = requests.get(
        image_url,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
    )

    response.raise_for_status()

    content_type = response.headers.get(
        "Content-Type", ""
    )

    if not content_type.startswith("image/"):
        raise RuntimeError(
            "Ссылка не вернула изображение."
        )

    telegram_request(
        "sendPhoto",
        data={
            "chat_id": GROUP_CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML",
        },
        files={
            "photo": (
                "news.jpg",
                response.content,
            )
        },
    )


def send_video(video_url, caption):
    response = requests.get(
        video_url,
        headers=HEADERS,
        timeout=60,
        stream=True,
    )

    response.raise_for_status()

    content = response.content

    telegram_request(
        "sendVideo",
        data={
            "chat_id": GROUP_CHAT_ID,
            "caption": caption,
            "parse_mode": "HTML",
        },
        files={
            "video": (
                "news.mp4",
                content,
                "video/mp4",
            )
        },
    )


def format_news(item, index):
    title = escape(item["title"])

    description = item["description"]

    if description:
        description = escape(description[:700])
    else:
        description = (
            "Подробности доступны в оригинальной публикации."
        )

    source = escape(item["source"])

    date = item["date"].astimezone(
        timezone(timedelta(hours=5))
    ).strftime("%d.%m.%Y, %H:%M")

    link = escape(
        item["link"],
        quote=True,
    )

    return (
        f"🇺🇿 <b>{index}. {title}</b>\n\n"
        f"{description}\n\n"
        f"📰 Источник: {source}\n"
        f"🕒 {date}\n"
        f'<a href="{link}">Читать полностью</a>'
    )


def send_news_item(item, index):
    caption = format_news(item, index)

    image_url, video_url = get_article_media(
        item["link"]
    )

    # Если доступно видео — отправляем видео

    if video_url:
        try:
            send_video(
                video_url,
                caption,
            )

            print(
                f"Видео отправлено: {item['title']}"
            )

            return

        except Exception as error:
            print(
                f"Не удалось отправить видео: {error}"
            )

    # Если видео нет — пробуем фотографию

    if image_url:
        try:
            send_photo(
                image_url,
                caption,
            )

            print(
                f"Фото отправлено: {item['title']}"
            )

            return

        except Exception as error:
            print(
                f"Не удалось отправить фото: {error}"
            )

    # Если медиа нет — отправляем текст

    send_text(caption)

    print(
        f"Текстовая новость отправлена: {item['title']}"
    )


def main():

    if not BOT_TOKEN or not GROUP_CHAT_ID:
        raise RuntimeError(
            "Не найдены BOT_TOKEN или GROUP_CHAT_ID"
        )

    print("Получаем новости Узбекистана...")

    history = load_history()

    all_news = get_news()

    new_news = [
        item
        for item in all_news
        if item["id"] not in history
    ]

    new_news = new_news[:MAX_NEWS]

    if not new_news:

        print("Новых новостей нет.")

        send_text(
            "🇺🇿 <b>Новости Узбекистана</b>\n\n"
            "За последние 24 часа новых публикаций "
            "для нашей новостной ленты не найдено."
        )

        save_history(history)

        return

    send_text(
        "🇺🇿 <b>ГЛАВНЫЕ НОВОСТИ УЗБЕКИСТАНА</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Самые свежие события страны"
    )

    now = datetime.now(timezone.utc).isoformat()

    for index, item in enumerate(new_news, start=1):

        try:
            send_news_item(
                item,
                index,
            )

            history[item["id"]] = now

        except Exception as error:

            print(
                f"Ошибка отправки новости "
                f"{item['title']}: {error}"
            )

    save_history(history)

    print(
        f"Обработано новостей: {len(new_news)}"
    )


if __name__ == "__main__":
    main()
