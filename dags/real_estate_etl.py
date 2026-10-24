
from datetime import datetime

from airflow.sdk import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook


CONN_ID = "real_estate_db"


def get_hook():
    return PostgresHook(postgres_conn_id=CONN_ID)


@dag(
    dag_id="real_estate_etl",
    start_date=datetime(2026, 1, 1),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["real_estate", "etl"],
)
def real_estate_etl():

    @task
    def create_table():
        hook = get_hook()

        hook.run("""
            CREATE TABLE IF NOT EXISTS real_estate_dataset (
                flat_id BIGINT PRIMARY KEY,
                building_id BIGINT,
                floor INTEGER,
                kitchen_area DOUBLE PRECISION,
                living_area DOUBLE PRECISION,
                rooms INTEGER,
                is_apartment BOOLEAN,
                studio BOOLEAN,
                total_area DOUBLE PRECISION,
                price NUMERIC(18, 2),
                build_year INTEGER,
                building_type_int INTEGER,
                latitude DOUBLE PRECISION,
                longitude DOUBLE PRECISION,
                ceiling_height DOUBLE PRECISION,
                flats_count INTEGER,
                floors_total INTEGER,
                has_elevator BOOLEAN
            )
        """)

    @task
    def extract():
        hook = get_hook()

        hook.run([
            "DROP TABLE IF EXISTS etl_flats_stage",
            """
            CREATE TABLE etl_flats_stage AS
            SELECT * FROM flats
            """,
            "DROP TABLE IF EXISTS etl_buildings_stage",
            """
            CREATE TABLE etl_buildings_stage AS
            SELECT * FROM buildings
            """,
        ])

    @task
    def transform():
        hook = get_hook()

        hook.run([
            "DROP TABLE IF EXISTS etl_joined_stage",
            """
            CREATE TABLE etl_joined_stage AS
            SELECT
                f.id AS flat_id,
                f.building_id,
                f.floor,
                f.kitchen_area,
                f.living_area,
                f.rooms,
                f.is_apartment,
                f.studio,
                f.total_area,
                f.price,
                b.build_year,
                b.building_type_int,
                b.latitude,
                b.longitude,
                b.ceiling_height,
                b.flats_count,
                b.floors_total,
                b.has_elevator
            FROM etl_flats_stage AS f
            INNER JOIN etl_buildings_stage AS b
                ON f.building_id = b.id
            """,
        ])

    @task
    def load():
        hook = get_hook()

        source_count = hook.get_first(
            "SELECT COUNT(*) FROM etl_flats_stage"
        )[0]

        result_count = hook.get_first(
            "SELECT COUNT(*) FROM etl_joined_stage"
        )[0]

        if source_count != result_count:
            raise ValueError(
                "Some flats have no matching building"
            )

        hook.run([
            "TRUNCATE TABLE real_estate_dataset",
            """
            INSERT INTO real_estate_dataset
            SELECT * FROM etl_joined_stage
            """,
        ])

        loaded_count = hook.get_first(
            "SELECT COUNT(*) FROM real_estate_dataset"
        )[0]

        if loaded_count != source_count:
            raise ValueError("Incorrect number of loaded rows")

        print(f"Loaded rows: {loaded_count}")

    create_task = create_table()
    extract_task = extract()
    transform_task = transform()
    load_task = load()

    create_task >> extract_task >> transform_task >> load_task


real_estate_etl()
