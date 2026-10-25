"""Выгрузка очищенных данных из PostgreSQL в CSV для DVC."""

import os
import re
from pathlib import Path

import pandas as pd
import yaml
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


ROOT = Path(__file__).resolve().parents[2]


def read_password() -> str:
    """Читаем пароль из окружения или локального .env (не из Git)."""
    password = os.getenv("POSTGRES_PASSWORD")
    if password:
        return password

    env_file = ROOT / ".env"
    if not env_file.exists():
        raise FileNotFoundError("Нет .env с POSTGRES_PASSWORD")

    for line in env_file.read_text(encoding="utf-8-sig").splitlines():
        if line.strip().startswith("POSTGRES_PASSWORD="):
            password = line.split("=", 1)[1].strip().strip('"').strip("'")
            if password:
                return password
    raise ValueError("POSTGRES_PASSWORD не найден в .env")


def main():
    with (ROOT / "params.yaml").open(encoding="utf-8") as file:
        config = yaml.safe_load(file)["database"]

    table = config["table"]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", table):
        raise ValueError("Некорректное название таблицы")

    url = URL.create(
        "postgresql+psycopg",
        username=config["user"],
        password=read_password(),
        host=config["host"],
        port=int(config["port"]),
        database=config["name"],
    )
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            data = pd.read_sql_query(
                text(f'SELECT * FROM "{table}" ORDER BY flat_id'),
                connection,
            )
    finally:
        engine.dispose()

    if data.empty:
        raise ValueError("Таблица с очищенными данными пуста")
    if "price" not in data.columns or "building_id" not in data.columns:
        raise ValueError("Не найдены обязательные столбцы price / building_id")

    output = ROOT / "data" / "ml" / "clean.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output, index=False, encoding="utf-8", lineterminator="\n")
    print(f"Выгружено квартир: {len(data)}. Файл: {output}")


if __name__ == "__main__":
    main()
