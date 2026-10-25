## Этап 3. DVC-пайплайн обучения модели

Цель: прогнозировать цену квартиры в рублях на основе характеристик объекта и дома.
Данные загружаются из `real_estate_dataset_clean` в PostgreSQL (этап 2).

Пайплайн DVC содержит четыре этапа:

1. `export` — экспорт очищенной таблицы PostgreSQL в `data/ml/clean.csv`.
2. `split` — разбиение на train/test по `building_id` в соотношении примерно 80/20 **по домам**.
3. `train` — обучение Ridge-регрессии и медианной базовой модели. Пропуски заполняются,
   числовые признаки стандартизируются, `building_type_int` кодируется one-hot.
   Предобработка обучается только на тренировочной части.
4. `evaluate` — оценка обеих моделей на отложенной тестовой выборке:
   MAE (руб.), RMSE (руб.), R².

Параметры модели и разделения хранятся в `params.yaml`, описание стадий — в `dvc.yaml`.
Модель находится в `models/price_model.joblib` и версионируется DVC.

### Запуск на Windows (PowerShell)

Из корня проекта с активированной `.venv`:

```powershell
python -m pip install "dvc[s3]" pyyaml joblib
python -m dvc init
python -m dvc repro
python -m dvc metrics show
python -m dvc dag
```

**Важно:** запуск DVC выполняется в папке проекта, где лежит `.env` с
`POSTGRES_PASSWORD`; служба PostgreSQL должна быть запущена на `127.0.0.1:55432`.

### S3

Вначале нужно создать корзину (bucket) в AWS S3 или совместимом облаке.
Затем настроить DVC remote:

```powershell
python -m dvc remote add -d storage s3://ИМЯ_ВАШЕГО_BUCKET/yandex-realty-dvc
```

Для S3-совместимого сервиса дополнительно:

```powershell
python -m dvc remote modify storage endpointurl https://АДРЕС_ВАШЕГО_S3_ENDPOINT
```

Ключи доступа записывать только в локальную (исключенную из Git) конфигурацию:

```powershell
python -m dvc remote modify --local storage access_key_id "ВАШ_ACCESS_KEY"
python -m dvc remote modify --local storage secret_access_key "ВАШ_SECRET_KEY"
```

Отправка результатов в облако:

```powershell
python -m dvc push
python -m dvc status -c
```

Для повторного экспорта данных из PostgreSQL после изменений в БД можно
выполнить `python -m dvc repro -f export`, затем `python -m dvc repro`.
Без принудительного экспорта DVC не узнает об изменениях внешней базы данных,
так как отслеживает файлы, код и параметры, а не состояние PostgreSQL.

Не отправляйте `.env`, `.dvc/config.local`, `.dvc/cache`, CSV и модель в Git;
в Git должны попасть `dvc.yaml`, `params.yaml`, `dvc.lock`, исходники и метрики.
