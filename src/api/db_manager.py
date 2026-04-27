import psycopg


class DBManager:
    """
    Класс для работы с базой данных PostgreSQL.
    """

    def __init__(self, config: dict):
        """Подключение к базе данных."""
        self.conn = psycopg.connect(**config)
        self.conn.autocommit = True
        self._create_tables()

    def _create_tables(self):
        """ Создаёт таблицы countries и aeroplanes,
        если они ещё не существуют."""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS countries (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100),
                    south FLOAT,
                    north FLOAT,
                    west FLOAT,
                    east FLOAT
                );
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS aeroplanes (
                    id SERIAL PRIMARY KEY,
                    icao24 VARCHAR(10) UNIQUE,
                    callsign VARCHAR(20),
                    origin_country VARCHAR(100),
                    longitude FLOAT,
                    latitude FLOAT,
                    velocity FLOAT,
                    country_id INT REFERENCES countries(id)
                );
            """)

    def insert_country(self, name, bbox):
        """Сохраняет информацию о стране в базу данных."""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO countries (name, south, north, west, east)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (name, *bbox))

            return cur.fetchone()[0]

    def insert_plane(self, plane, country_id):
        """Сохраняет информацию о самолёте в базу данных."""
        icao24 = plane[0]
        callsign = (plane[1] or "UNKNOWN").strip()
        origin_country = plane[2] or "UNKNOWN"
        longitude = plane[5]
        latitude = plane[6]
        velocity = plane[9] or 0

        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO aeroplanes (
                    icao24, callsign, origin_country,
                    longitude, latitude, velocity, country_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (icao24) DO NOTHING;
            """, (
                icao24,
                callsign,
                origin_country,
                longitude,
                latitude,
                velocity,
                country_id
            ))

    def get_countries_and_aeroplanes_count(self):
        """Получает список стран и количество самолётов
        в их воздушном пространстве."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT c.name, COUNT(a.id)
                FROM countries c
                LEFT JOIN aeroplanes a ON c.id = a.country_id
                GROUP BY c.name
            """)
            return cur.fetchall()

    def get_all_aeroplanes(self):
        """Получает полный список всех самолётов из базы данных."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT * FROM aeroplanes")
            return cur.fetchall()

    def get_avg_speed(self):
        """Вычисляет среднюю скорость всех самолётов."""
        with self.conn.cursor() as cur:
            cur.execute("SELECT AVG(velocity) FROM aeroplanes")
            return cur.fetchone()[0]

    def get_aeroplanes_with_higher_speed(self):
        """Получает список самолётов, скорость которых выше средней."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM aeroplanes
                WHERE velocity > (SELECT AVG(velocity) FROM aeroplanes)
            """)
            return cur.fetchall()

    def get_aeroplanes_with_keyword(self, keyword):
        """Получает список самолётов, в позывном которых
        содержится ключевое слово."""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT * FROM aeroplanes
                WHERE callsign ILIKE %s
            """, (f"%{keyword}%",))
            return cur.fetchall()

    def clear_tables(self):
        """Очищает таблицы перед загрузкой новых данных."""
        with self.conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE aeroplanes RESTART IDENTITY CASCADE;")
            cur.execute("TRUNCATE TABLE countries RESTART IDENTITY CASCADE;")