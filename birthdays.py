import json
from datetime import date, datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

BIRTHDAYS_FILE = BASE_DIR / "birthdays.json"


def load_birthdays():
    """Загружает семейный календарь."""
    with open(BIRTHDAYS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def calculate_age(birth_date, current_date=None):
    """Точно рассчитывает возраст человека."""
    birthday = datetime.strptime(birth_date, "%Y-%m-%d").date()
    today = current_date or date.today()

    age = today.year - birthday.year

    if (today.month, today.day) < (birthday.month, birthday.day):
        age -= 1

    return age


def get_today_birthdays(current_date=None):
    """Находит именинников сегодняшнего дня."""
    today = current_date or date.today()
    birthdays = load_birthdays()

    result = []

    for person in birthdays:
        birthday = datetime.strptime(
            person["birth_date"], "%Y-%m-%d"
        ).date()

        if (birthday.month, birthday.day) == (today.month, today.day):
            person_data = person.copy()
            person_data["age"] = calculate_age(
                person["birth_date"], today
            )
            result.append(person_data)

    return result


def main():
    today = date.today()

    print("=" * 40)
    print("СЕМЕЙНЫЙ КАЛЕНДАРЬ ДНЕЙ РОЖДЕНИЯ")
    print("=" * 40)

    print(f"Сегодня: {today.strftime('%d.%m.%Y')}")

    birthdays = get_today_birthdays(today)

    if not birthdays:
        print("Сегодня именинников нет.")
        return

    for person in birthdays:
        print()
        print(f"🎂 Именинник: {person['name']}")
        print(f"Возраст: {person['age']}")
        print(f"Обращение: {person['address']}")
        print(f"Родство: {person['relation']}")

    print()
    print("Проверка завершена.")


if __name__ == "__main__":
    main()
