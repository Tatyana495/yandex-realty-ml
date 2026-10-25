# Улучшение модели: CatBoost вместо одной Ridge

**Вносите эти файлы в существующий проект.** Архив содержит изменённые
`src/ml/train.py`, `src/ml/evaluate.py`, `dvc.yaml`, `params.yaml`,
`requirements-stage3.txt` и новый `src/ml/features.py`.

## Что меняется

- Ridge и DummyRegressor остаются для честного сравнения.
- Добавляем CatBoost с функцией потерь MAE и признаками, описывающими
  отношение площадей и положение этажа.
- Для выбора числа деревьев используется дополнительная групповая валидация
  **только внутри train**. Затем CatBoost переобучается на всей обучающей выборке.
- Файлы `data/ml/train.csv` и `data/ml/test.csv` сохраняются: этапы `export`
  и `split` не меняются.
- Сохраняем три модели в `models/price_model.joblib`.

## Windows PowerShell

```powershell
cd C:\Users\demya\yandex_realty
.\.venv\Scripts\Activate.ps1
python -m pip install "catboost>=1.2.8,<2"
python -m pip check
python -m dvc repro
python -m dvc metrics show
python -m dvc status
```

`dvc repro` повторно запустит только `train` и `evaluate`, если исходные
`data/ml/train.csv` и `data/ml/test.csv` не менялись.

Проверьте по `reports/metrics.json`, улучшилась ли MAE. Пока не знаем:
фактические метрики CatBoost появятся только после запуска на вашей базе.

Когда новая модель устроит по качеству и не содержит утечек данных,
выполните `python -m dvc push`, `python -m dvc status -c`,
затем зафиксируйте изменения в Git.

**Безопасность:** не добавляйте `.env`, `.dvc/config.local`, `AWS_*` ключи
и файл `models/price_model.joblib` вручную в GitHub.
