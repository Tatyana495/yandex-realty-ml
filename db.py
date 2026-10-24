from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Читаем пароль из файла .env
env_path = Path(__file__).parent / ".env"

password = None

for line in env_path.read_text(encoding="utf-8-sig").splitlines():
    if line.startswith("POSTGRES_PASSWORD="):
        password = line.split("=", 1)[1].strip()
        break

if not password:
    raise ValueError("POSTGRES_PASSWORD не найден в .env")


# Параметры подключения к PostgreSQL
url = URL.create(
    drivername="postgresql+psycopg",
    username="real_estate_user",
    password=password,
    host="127.0.0.1",
    port=55432,
    database="real_estate",
)

engine = create_engine(url, pool_pre_ping=True)


# Проверяем подключение и количество записей
with engine.connect() as connection:
    version = connection.execute(
        text("SELECT current_database()")
    ).scalar_one()

    buildings_count = connection.execute(
        text("SELECT COUNT(*) FROM buildings")
    ).scalar_one()

    flats_count = connection.execute(
        text("SELECT COUNT(*) FROM flats")
    ).scalar_one()

    print("Подключение к PostgreSQL успешно!")
    print(f"База данных: {version}")
    print(f"Домов: {buildings_count}")
    print(f"Квартир: {flats_count}")