"""Сравнение Ridge, медианного прогноза и CatBoost на ОДНОМ тесте."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from src.ml.features import prepare_catboost_features


ROOT = Path(__file__).resolve().parents[2]


def metrics(y_true, y_pred):
    return {
        "mae_rub": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "rmse_rub": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 2),
        "r2": round(float(r2_score(y_true, y_pred)), 4),
    }


def main():
    saved = joblib.load(ROOT / "models" / "price_model.joblib")
    data = pd.read_csv(ROOT / "data" / "ml" / "test.csv")
    features = saved["features"]
    x = data[features].copy()
    categorical = ["building_type_int"]
    numeric = [col for col in features if col not in categorical]
    x[numeric] = x[numeric].apply(pd.to_numeric, errors="coerce")
    x[categorical] = x[categorical].fillna("unknown").astype(str)
    y = pd.to_numeric(data["price"], errors="raise")

    boosted_x = prepare_catboost_features(x)[saved["catboost_features"]]
    results = {
        "ridge": metrics(y, saved["model"].predict(x)),
        "dummy_median": metrics(y, saved["baseline"].predict(x)),
        "catboost": metrics(y, saved["catboost"].predict(boosted_x)),
        "test_rows": int(len(data)),
        "catboost_trees": int(saved["catboost_trees"]),
    }
    path = ROOT / "reports" / "metrics.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))

    delta = (1 - results["catboost"]["mae_rub"] / results["ridge"]["mae_rub"]) * 100
    print(f"Изменение MAE относительно Ridge: {delta:+.2f}% (положительное = лучше)")


if __name__ == "__main__":
    main()
