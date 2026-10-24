"""Очистка датасета Яндекс Недвижимости с помощью Apache Airflow 3."""

from datetime import datetime

from airflow.sdk import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from sqlalchemy import BigInteger, Numeric, text


CONN_ID = "real_estate_db"
SOURCE_TABLE = "real_estate_dataset"
TARGET_TABLE = "real_estate_dataset_clean"


@dag(
    dag_id="real_estate_cleaning",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["real_estate", "cleaning"],
)
def real_estate_cleaning():
    @task
    def check_source():
        hook = PostgresHook(postgres_conn_id=CONN_ID)
        source_count = hook.get_first(
            f"SELECT COUNT(*) FROM {SOURCE_TABLE}"
        )[0]

        if source_count == 0:
            raise ValueError("Исходная таблица пуста")

        print(f"Исходных квартир: {source_count}")

    @task
    def clean_and_load():
        import pandas as pd
        from src.cleaning import clean_data

        hook = PostgresHook(postgres_conn_id=CONN_ID)
        engine = hook.get_sqlalchemy_engine()

        try:
            df = pd.read_sql_query(
                text(f"SELECT * FROM {SOURCE_TABLE}"),
                engine,
            )
            print(f"Исходный размер: {df.shape}")

            df_clean = clean_data(df)
            print(f"После очистки: {df_clean.shape}")

            if df_clean.empty:
                raise ValueError("После очистки не осталось записей")
            if df_clean.isna().any().any():
                raise ValueError("После очистки остались пропуски")
            if df_clean["flat_id"].duplicated().any():
                raise ValueError("Обнаружены повторяющиеся flat_id")
            if df_clean.drop(columns=["flat_id"]).duplicated().any():
                raise ValueError("Обнаружены дубликаты по характеристикам")
            if (
                (df_clean["kitchen_area"] <= 0)
                | (df_clean["living_area"] <= 0)
                | (df_clean["kitchen_area"] + df_clean["living_area"]
                   > df_clean["total_area"] + 0.01)
            ).any():
                raise ValueError("После очистки остались ошибки площадей")

            price_per_sqm = df_clean["price"] / df_clean["total_area"]
            if ((price_per_sqm < 20_000) | (price_per_sqm > 5_000_000)).any():
                raise ValueError("После очистки остались ценовые выбросы")

            # Транзакция сохраняет старую версию таблицы при ошибке записи.
            with engine.begin() as connection:
                df_clean.to_sql(
                    TARGET_TABLE,
                    con=connection,
                    if_exists="replace",
                    index=False,
                    chunksize=1000,
                    dtype={
                        "flat_id": BigInteger(),
                        "building_id": BigInteger(),
                        "price": Numeric(18, 2),
                    },
                )
                connection.execute(
                    text(f"ALTER TABLE {TARGET_TABLE} "
                         "ADD PRIMARY KEY (flat_id)")
                )

            print(f"Записано строк: {len(df_clean)}")
            return len(df_clean)
        finally:
            engine.dispose()

    @task
    def check_result(expected_count: int):
        hook = PostgresHook(postgres_conn_id=CONN_ID)
        result = hook.get_first(
            f"""
            SELECT COUNT(*), COUNT(DISTINCT flat_id),
                   COUNT(*) FILTER (WHERE price IS NULL)
            FROM {TARGET_TABLE}
            """
        )
        actual_count, unique_flats, missing_prices = result

        if (actual_count != expected_count or
                unique_flats != actual_count or
                missing_prices != 0):
            raise ValueError(f"Ошибка проверки результата: {result}")

        print(f"Датасет сохранён успешно: {actual_count} квартир")

    source_task = check_source()
    cleaned_count = clean_and_load()
    checked = check_result(cleaned_count)

    source_task >> cleaned_count >> checked


real_estate_cleaning()
