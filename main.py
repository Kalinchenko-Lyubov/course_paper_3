import time

from src.api.nominatim import get_country_bbox
from src.api.opensky import get_planes
from src.api.db_manager import DBManager
from src.config import DB_CONFIG

import psycopg


def create_database_if_not_exists(config):
    """
    Создаёт базу данных, если она не существует.
    """
    conn = psycopg.connect(
        dbname="postgres",
        user=config["user"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
    )
    conn.autocommit = True

    dbname = config["dbname"]

    with conn.cursor() as cur:
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s;",
            (dbname,)
        )
        exists = cur.fetchone()

        if not exists:
            cur.execute(f"CREATE DATABASE {dbname};")

    conn.close()


def load_data(db, countries):
    """
    Загружает данные по странам и самолётам в базу данных.
    """
    for country in countries:
        print(f"Обработка: {country}")

        bbox = get_country_bbox(country)
        if not bbox:
            continue

        country_id = db.insert_country(country, bbox)
        planes = get_planes(bbox)

        for plane in planes:
            if not plane:
                continue

            if plane[5] is None or plane[6] is None:
                continue

            try:
                db.insert_plane(plane, country_id)
            except Exception as e:
                print(f"Ошибка вставки: {e}")

        time.sleep(1)


def main():
    """
    Основная функция программы:
    - создаёт базу данных (если её нет)
    - очищает таблицы
    - загружает данные по странам и самолётам
    - выводит аналитическую информацию
    """
    countries = [
        "Germany", "France", "Italy", "Spain", "Poland",
        "Sweden", "Norway", "Finland", "Netherlands", "Belgium"
    ]

    create_database_if_not_exists(DB_CONFIG)

    db = DBManager(DB_CONFIG)
    db.clear_tables()
    load_data(db, countries)

    print("\nДанные загружены\n")

    print("Страны и количество самолётов:")
    for country, count in db.get_countries_and_aeroplanes_count():
        print(f"{country:<12} — {count}")

    print("\nСредняя скорость самолётов:")
    avg_speed = db.get_avg_speed()

    if avg_speed:
        print(f"{avg_speed:.2f} м/с")
    else:
        print("Нет данных")

    print("\nСамолёты со скоростью выше средней:")
    fast_planes = db.get_aeroplanes_with_higher_speed()
    for plane in fast_planes[:10]:
        print(f"{plane[1]} | {plane[2]} | {plane[6]} м/с")

    print("\nСамолёты с 'ACA' в callsign:")
    aca_planes = db.get_aeroplanes_with_keyword("ACA")
    for plane in aca_planes[:10]:
        print(f"{plane[1]} | {plane[2]} | {plane[6]} м/с")


if __name__ == "__main__":
    main()