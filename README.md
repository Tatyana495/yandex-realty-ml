# Yandex Realty — прогнозирование стоимости квартир

## писание проекта

Проект посвящён разработке MVP модели машинного обучения
для прогнозирования стоимости квартир по их характеристикам.

На первом этапе реализован ETL-процесс с использованием
Apache Airflow и PostgreSQL.

## Используемые технологии

- Python 3.12
- PostgreSQL 17
- Apache Airflow 3.3.2
- Docker Compose
- SQL
- pandas
- scikit-learn

## Исходные данные

Данные представлены двумя таблицами:

- buildings — характеристики домов.
- flats — характеристики квартир и их стоимость.

Связь таблиц:
flats.building_id = buildings.id

## ETL-процесс

DAG: real_estate_etl

Процесс состоит из четырёх задач:

1. create_table — создание итоговой таблицы.
2. extract — извлечение данных из исходных таблиц.
3. transform — объединение данных о квартирах и домах.
4. load — загрузка результата в PostgreSQL.

Для промежуточной обработки используются таблицы PostgreSQL.

## Результаты первого этапа

Исходные данные:
- 24 620 домов.
- 141 362 квартиры.

Итоговая таблица: real_estate_dataset

Результаты проверки:
- 141 362 строки.
- 141 362 уникальные квартиры.
- 24 620 уникальных домов.
- 0 пропусков в целевой переменной price.

DAG успешно выполнен в Apache Airflow.

## Запуск проекта

1. Установить Docker и Docker Compose.
2. Создать файл .env с переменной POSTGRES_PASSWORD.
3. Запустить PostgreSQL:

   docker compose up -d

4. Создать исходные таблицы с помощью create_tables.sql.
5. Загрузить исходные CSV-файлы в PostgreSQL.
6. Запустить Apache Airflow:

   docker compose -f compose.yaml -f compose.airflow.yaml up -d

7. Открыть Airflow:

   http://localhost:8081

8. Создать подключение real_estate_db:
   - Host: postgres
   - Port: 5432
   - Database: real_estate
   - User: real_estate_user
   - Password: из файла .env

9. Запустить DAG real_estate_etl.

## Структура проекта

- dags/real_estate_etl.py — DAG для ETL.
- compose.yaml — PostgreSQL.
- compose.airflow.yaml — Apache Airflow.
- create_tables.sql — создание исходных таблиц.
- db.py — подключение Python к PostgreSQL.
- requirements.txt — зависимости Python.

## Примечания

Исходные CSV-файлы и пароли не публикуются в репозитории.

Данные PostgreSQL хранятся в Docker volume.
При развёртывании на другом компьютере необходимо
отдельно загрузить исходные данные.
